"""
Tool 4: simulate_profit
Project returns for a specific pool using Monte Carlo.
"""
from ..defillama import get_client
from ..calculations import run_monte_carlo


async def simulate_profit_impl(
    pool_id: str,
    investment: float = 10_000,
    days: int = 365,
    compound: bool = True,
) -> dict:
    """
    Run Monte Carlo profit simulation for a specific pool.

    Uses Ornstein-Uhlenbeck APY model with:
    - APY mean reversion + crash events
    - Impermanent loss via GBM
    - Pool failure probability
    - 1,000 simulation iterations

    Returns:
      Scenarios (bearish/base/optimistic), percentiles,
      probability profitable, risk factors.
    """
    client = get_client()
    pool = await client.find_pool_by_id(pool_id)
    if not pool:
        return {"error": f"Pool '{pool_id}' not found. Use discover_yields to find valid pool IDs."}

    apy = pool.get("apy", 0) or 0
    tvl = pool.get("tvlUsd", 0) or 0
    il_risk_raw = (pool.get("ilRisk", "") or "").lower() or "medium"
    is_stable = pool.get("stablecoin", False)

    # Stablecoin pools have low IL
    il_risk = "low" if is_stable else il_risk_raw
    if il_risk in ("no", "none", ""):
        il_risk = "low"

    # Validate days
    if days < 1:
        days = 30
    elif days > 730:
        days = 730

    simulation = run_monte_carlo(
        current_apy=apy,
        tvl=tvl,
        il_risk=il_risk,
        days=days,
        investment=investment,
        compound=compound,
    )

    return {
        "pool": {
            "pool_id": pool.get("pool", ""),
            "symbol": pool.get("symbol", "?"),
            "protocol": pool.get("project", "?"),
            "chain": pool.get("chain", "?"),
            "current_apy": round(apy, 2),
            "tvl_usd": round(tvl, 0),
            "stablecoin": bool(is_stable),
        },
        "simulation": simulation,
    }
