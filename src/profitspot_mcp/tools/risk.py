"""
Tool 5: risk_score
Get risk grade (A-F) for a pool or entire protocol.
"""
from ..defillama import get_client
from ..scoring import calculate_risk_grade


async def risk_score_impl(
    pool_id: str | None = None,
    protocol: str | None = None,
) -> dict:
    """
    Get detailed risk grade for a pool or protocol.

    For a pool: returns A-F grade with full factor breakdown.
    For a protocol: scores the protocol's top pools and returns
    an aggregate assessment.

    At least one of pool_id or protocol must be provided.
    """
    if not pool_id and not protocol:
        return {"error": "Provide at least one of pool_id or protocol."}

    client = get_client()

    # ── Pool-level risk ───────────────────────────────────────
    if pool_id:
        pool = await client.find_pool_by_id(pool_id)
        if not pool:
            return {"error": f"Pool '{pool_id}' not found."}

        # Fetch historical for volatility scoring
        history = await client.fetch_pool_chart(pool_id)
        risk = calculate_risk_grade(pool, historical_apy=history if history else None)

        return {
            "type": "pool",
            "pool_id": pool_id,
            "symbol": pool.get("symbol", "?"),
            "protocol": pool.get("project", "?"),
            "chain": pool.get("chain", "?"),
            **risk,
        }

    # ── Protocol-level risk ───────────────────────────────────
    all_pools = await client.fetch_pools()
    protocol_pools = [
        p for p in all_pools
        if (p.get("project", "") or "").lower() == protocol.lower()
        and (p.get("tvlUsd", 0) or 0) > 10_000
    ]

    if not protocol_pools:
        return {"error": f"No pools found for protocol '{protocol}'."}

    # Score top pools by TVL
    protocol_pools.sort(key=lambda x: x.get("tvlUsd", 0) or 0, reverse=True)
    top_pools = protocol_pools[:10]

    grades = []
    scores = []
    pool_results = []

    for p in top_pools:
        risk = calculate_risk_grade(p)
        grades.append(risk["grade"])
        scores.append(risk["score"])
        pool_results.append({
            "pool_id": p.get("pool", ""),
            "symbol": p.get("symbol", "?"),
            "chain": p.get("chain", "?"),
            "tvl_usd": round(p.get("tvlUsd", 0) or 0, 0),
            "apy": round(p.get("apy", 0) or 0, 2),
            "grade": risk["grade"],
            "score": risk["score"],
        })

    avg_score = round(sum(scores) / len(scores)) if scores else 0
    if avg_score >= 85:
        agg_grade = "A"
    elif avg_score >= 70:
        agg_grade = "B"
    elif avg_score >= 55:
        agg_grade = "C"
    elif avg_score >= 40:
        agg_grade = "D"
    else:
        agg_grade = "F"

    total_tvl = sum(p.get("tvlUsd", 0) or 0 for p in protocol_pools)

    return {
        "type": "protocol",
        "protocol": protocol,
        "aggregate_grade": agg_grade,
        "aggregate_score": avg_score,
        "total_pools": len(protocol_pools),
        "total_tvl": round(total_tvl, 0),
        "top_pools_scored": pool_results,
        "summary": f"{protocol} has {len(protocol_pools)} pools with aggregate grade {agg_grade} (score {avg_score}/100). Total TVL: ${total_tvl/1e6:.1f}M.",
    }
