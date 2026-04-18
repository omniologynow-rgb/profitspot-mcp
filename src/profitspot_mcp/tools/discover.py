"""
Tool 1: discover_yields
Discover top yield opportunities across all chains.
"""
from ..defillama import get_client
from ..scoring import calculate_risk_grade

GRADE_ORDER = {"A": 1, "B": 2, "C": 3, "D": 4, "F": 5}


async def discover_yields_impl(
    chain: str | None = None,
    min_tvl: float = 1_000_000,
    min_apy: float = 0,
    max_risk: str = "F",
    limit: int = 20,
    risk_filter_enabled: bool = True,
) -> dict:
    """
    Fetch, filter, risk-score, and rank yield pools.

    Returns:
        {pools: [...], total_scanned, filters_applied}
    """
    client = get_client()
    raw_pools = await client.fetch_pools()

    if not raw_pools:
        return {"pools": [], "total_scanned": 0, "error": "DeFiLlama API unavailable"}

    max_risk_val = GRADE_ORDER.get(max_risk.upper(), 5)
    scored: list[dict] = []

    for p in raw_pools:
        tvl = p.get("tvlUsd", 0) or 0
        apy = p.get("apy", 0) or 0
        pool_chain = (p.get("chain", "") or "").lower()

        # Basic filters
        if tvl < min_tvl:
            continue
        if apy < min_apy:
            continue
        if chain and pool_chain != chain.lower():
            continue

        # Risk grade
        risk = calculate_risk_grade(p)
        grade = risk["grade"]

        # Risk filter (pro only)
        if risk_filter_enabled and GRADE_ORDER.get(grade, 5) > max_risk_val:
            continue

        prediction_raw = p.get("predictions") or {}
        prediction_class = prediction_raw.get("predictedClass", "stable") if isinstance(prediction_raw, dict) else "stable"

        scored.append({
            "pool_id": p.get("pool", ""),
            "symbol": p.get("symbol", "?"),
            "protocol": p.get("project", "?"),
            "chain": p.get("chain", "?"),
            "apy": round(apy, 2),
            "apy_base": round(p.get("apyBase", 0) or 0, 2),
            "apy_reward": round(p.get("apyReward", 0) or 0, 2),
            "apy_mean_30d": round(p.get("apyMean30d", 0) or 0, 2),
            "tvl_usd": round(tvl, 0),
            "risk_grade": grade,
            "risk_score": risk["score"],
            "prediction": prediction_class,
            "stablecoin": bool(p.get("stablecoin", False)),
            "il_risk": (p.get("ilRisk", "unknown") or "unknown").lower(),
            "exposure": p.get("exposure", "single"),
        })

    # Sort by APY descending
    scored.sort(key=lambda x: x["apy"], reverse=True)
    result_pools = scored[:limit]

    return {
        "pools": result_pools,
        "total_matching": len(scored),
        "total_scanned": len(raw_pools),
        "filters_applied": {
            "chain": chain,
            "min_tvl": min_tvl,
            "min_apy": min_apy,
            "max_risk": max_risk if risk_filter_enabled else "disabled (free tier)",
            "limit": limit,
        },
    }
