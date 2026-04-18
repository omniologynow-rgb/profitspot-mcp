"""
Tool 7: defi_overview
Big-picture DeFi dashboard.
"""
from ..defillama import get_client
from ..scoring import calculate_risk_grade


async def defi_overview_impl(
    chain: str | None = None,
    full_stats: bool = True,
) -> dict:
    """
    Big-picture DeFi dashboard.

    Returns:
      Total TVL, TVL by top chains, top protocols, average yields
      by risk grade, stablecoin data, hot opportunities.

    Args:
        chain: Optional chain filter
        full_stats: True for pro (all data), False for free (basic)
    """
    client = get_client()

    # Fetch core data
    pools = await client.fetch_pools()
    chains_data = await client.fetch_chains()
    stablecoins_data = await client.fetch_stablecoins()

    if not pools:
        return {"error": "DeFiLlama API unavailable"}

    # Filter by chain if specified
    if chain:
        pools = [p for p in pools if (p.get("chain", "") or "").lower() == chain.lower()]

    # Quality filter
    quality = [
        p for p in pools
        if (p.get("tvlUsd", 0) or 0) > 100_000
        and 0 < (p.get("apy", 0) or 0) < 1000
    ]

    # ── Aggregate Stats ───────────────────────────────────────
    total_tvl = sum(p.get("tvlUsd", 0) or 0 for p in quality)
    avg_apy = (
        sum(p.get("apy", 0) or 0 for p in quality) / len(quality)
        if quality else 0
    )

    # Chain distribution
    chain_tvl: dict[str, float] = {}
    chain_pools_count: dict[str, int] = {}
    for p in quality:
        c = p.get("chain", "Unknown")
        chain_tvl[c] = chain_tvl.get(c, 0) + (p.get("tvlUsd", 0) or 0)
        chain_pools_count[c] = chain_pools_count.get(c, 0) + 1

    top_chains = sorted(chain_tvl.items(), key=lambda x: x[1], reverse=True)[:10]

    # Protocol distribution
    protocol_tvl: dict[str, float] = {}
    for p in quality:
        proto = p.get("project", "Unknown")
        protocol_tvl[proto] = protocol_tvl.get(proto, 0) + (p.get("tvlUsd", 0) or 0)

    top_protocols = sorted(protocol_tvl.items(), key=lambda x: x[1], reverse=True)[:10]

    result: dict = {
        "total_pools": len(quality),
        "total_pools_all": len(pools),
        "total_tvl_usd": round(total_tvl, 0),
        "total_tvl_formatted": f"${total_tvl / 1e9:.2f}B" if total_tvl >= 1e9 else f"${total_tvl / 1e6:.1f}M",
        "average_apy": round(avg_apy, 2),
        "chains_covered": len(chain_tvl),
        "top_chains": [
            {"chain": c, "tvl_usd": round(t, 0), "pool_count": chain_pools_count.get(c, 0)}
            for c, t in top_chains
        ],
        "top_protocols": [
            {"protocol": p, "tvl_usd": round(t, 0)}
            for p, t in top_protocols
        ],
    }

    if not full_stats:
        result["note"] = "Upgrade to Pro for risk-graded yields, hot opportunities, and stablecoin flows."
        return result

    # ── Pro: Average Yields by Risk Grade ─────────────────────
    grade_yields: dict[str, list[float]] = {"A": [], "B": [], "C": [], "D": [], "F": []}
    sample_pools = quality[:500]  # Score a sample for performance
    for p in sample_pools:
        risk = calculate_risk_grade(p)
        g = risk["grade"]
        if g in grade_yields:
            grade_yields[g].append(p.get("apy", 0) or 0)

    result["avg_yield_by_grade"] = {
        g: round(sum(v) / len(v), 2) if v else 0
        for g, v in grade_yields.items()
    }

    # ── Pro: Stablecoin Data ──────────────────────────────────
    if stablecoins_data and isinstance(stablecoins_data, dict):
        stables = stablecoins_data.get("peggedAssets", [])
        top_stables = sorted(
            stables, key=lambda s: s.get("circulating", {}).get("peggedUSD", 0) or 0, reverse=True
        )[:5]
        result["stablecoin_overview"] = [
            {
                "name": s.get("name", "?"),
                "symbol": s.get("symbol", "?"),
                "market_cap": round(s.get("circulating", {}).get("peggedUSD", 0) or 0, 0),
            }
            for s in top_stables
        ]

    # ── Pro: Hot Opportunities ────────────────────────────────
    # New high-APY pools with good risk in last 7 days
    hot: list[dict] = []
    for p in quality:
        apy = p.get("apy", 0) or 0
        tvl = p.get("tvlUsd", 0) or 0
        apy_7d = p.get("apyPct7D") or 0

        if apy >= 15 and tvl >= 1_000_000 and apy_7d > 5:
            risk = calculate_risk_grade(p)
            if risk["grade"] in ("A", "B", "C"):
                hot.append({
                    "pool_id": p.get("pool", ""),
                    "symbol": p.get("symbol", "?"),
                    "protocol": p.get("project", "?"),
                    "chain": p.get("chain", "?"),
                    "apy": round(apy, 2),
                    "tvl_usd": round(tvl, 0),
                    "risk_grade": risk["grade"],
                    "apy_7d_change": round(apy_7d, 2),
                    "why_hot": f"APY up {apy_7d:.0f}% this week, grade {risk['grade']}, ${tvl/1e6:.1f}M TVL",
                })

    hot.sort(key=lambda x: x["apy"], reverse=True)
    result["hot_opportunities"] = hot[:10]

    # ── Pro: Chain TVL from /chains ───────────────────────────
    if chains_data:
        total_defi_tvl = sum(c.get("tvl", 0) or 0 for c in chains_data)
        result["total_defi_tvl_all_chains"] = round(total_defi_tvl, 0)
        result["total_defi_tvl_formatted"] = (
            f"${total_defi_tvl / 1e9:.2f}B" if total_defi_tvl >= 1e9
            else f"${total_defi_tvl / 1e6:.1f}M"
        )

    return result
