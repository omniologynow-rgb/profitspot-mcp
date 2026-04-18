"""
ProfitSpot MCP Server — Cross-Chain DeFi Intelligence for AI Agents

The "Bloomberg Terminal for AI agents."
Risk-scored yields, profit simulation, whale tracking
across 86 chains and 6,500+ pools.

https://profitspot.live

Usage:
  fastmcp dev  src/profitspot_mcp/server.py         # Dev mode with inspector
  fastmcp run  src/profitspot_mcp/server.py          # Production (stdio)
  python -m profitspot_mcp.server                    # Direct run (http)

Environment:
  PROFITSPOT_API_KEY  — Set for Pro tier (all 7 tools, full params)
                        Leave unset for Free tier (3 tools, limited)
"""
from fastmcp import FastMCP

from .auth import get_tier, Tier, pro_gate, rate_gate, get_discover_limit, can_filter_risk
from .models import build_response
from .cache import cache

# Tool implementations
from .tools.discover import discover_yields_impl
from .tools.analyze import analyze_pool_impl
from .tools.impermanent_loss import calculate_il_impl
from .tools.simulate import simulate_profit_impl
from .tools.risk import risk_score_impl
from .tools.whales import track_whales_impl
from .tools.overview import defi_overview_impl

# ── FastMCP Server ────────────────────────────────────────────────
mcp = FastMCP(
    "ProfitSpot MCP",
    instructions=(
        "Cross-chain DeFi intelligence for AI agents. "
        "Risk-scored yields, profit simulation, whale tracking "
        "across 86 chains and 6,500+ pools. "
        "By profitspot.live — the Bloomberg Terminal for AI."
    ),
)


# ══════════════════════════════════════════════════════════════════
# TOOL 1: discover_yields (FREE — limited to 10 results, no risk filter)
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def discover_yields(
    chain: str | None = None,
    min_tvl: float = 1_000_000,
    min_apy: float = 0,
    max_risk: str = "F",
    limit: int = 20,
) -> dict:
    """Discover top DeFi yield opportunities across 86 chains and 6,500+ pools.

    Filter by chain, minimum TVL, minimum APY, and maximum risk grade (A-F).
    Returns sorted list with pool name, protocol, chain, APY, TVL, risk grade,
    prediction (stable/up/down), and stablecoin flag.

    FREE tier: limited to 10 results, no risk filtering.
    PRO tier: up to 50 results with full risk grade filtering.
    """
    # Rate limit check
    if err := rate_gate():
        return err

    tier = get_tier()

    # Enforce free tier limits
    effective_limit = min(limit, get_discover_limit())
    risk_filter_on = can_filter_risk()

    data = await discover_yields_impl(
        chain=chain,
        min_tvl=min_tvl,
        min_apy=min_apy,
        max_risk=max_risk if risk_filter_on else "F",
        limit=effective_limit,
        risk_filter_enabled=risk_filter_on,
    )

    confidence = 0.92 if data.get("pools") else 0.3
    if not risk_filter_on and max_risk != "F":
        data["tier_note"] = (
            "Risk grade filtering requires Pro tier. "
            "Showing all grades. Set PROFITSPOT_API_KEY for full access."
        )

    return build_response(data, confidence=confidence, tool="discover_yields", tier=tier.value)


# ══════════════════════════════════════════════════════════════════
# TOOL 2: analyze_pool (PRO ONLY)
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def analyze_pool(pool_id: str) -> dict:
    """Deep analysis of a specific DeFi pool.

    Returns: full pool data, historical APY trends (7d/30d/90d),
    TVL history, risk grade with full breakdown (why it got that grade),
    IL estimate scenarios for LP pools, and projected returns at
    current APY for $1K/$10K/$100K over 30/90/365 days.

    PRO ONLY — requires PROFITSPOT_API_KEY.
    """
    # Rate limit check
    if err := rate_gate():
        return err

    gate = pro_gate("analyze_pool")
    if gate:
        return gate

    data = await analyze_pool_impl(pool_id)

    if "error" in data:
        return build_response(data, confidence=0.0, tool="analyze_pool", tier="pro")

    confidence = 0.90 if data.get("data_points", 0) > 30 else 0.75
    return build_response(data, confidence=confidence, tool="analyze_pool", tier="pro")


# ══════════════════════════════════════════════════════════════════
# TOOL 3: calculate_impermanent_loss (ALWAYS FREE)
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def calculate_impermanent_loss(
    token_a_price_change: float,
    token_b_price_change: float,
    investment_amount: float = 10_000,
) -> dict:
    """Calculate exact impermanent loss for a 50/50 LP pair.

    Given price change percentages for both tokens, calculates exact IL
    in USD and percentage. Also returns: value if held vs value in LP,
    and net gain/loss including trading fees at various APY levels
    (5%, 10%, 20%, 50%).

    ALWAYS FREE — pure math, no API call needed.
    """
    # Rate limit check
    if err := rate_gate():
        return err

    data = await calculate_il_impl(
        token_a_price_change, token_b_price_change, investment_amount
    )
    tier = get_tier()
    return build_response(data, confidence=0.99, tool="calculate_impermanent_loss", tier=tier.value)


# ══════════════════════════════════════════════════════════════════
# TOOL 4: simulate_profit (PRO ONLY)
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def simulate_profit(
    pool_id: str,
    investment: float = 10_000,
    days: int = 365,
    compound: bool = True,
) -> dict:
    """Project returns for a specific pool using Monte Carlo simulation.

    Uses Ornstein-Uhlenbeck APY model that accounts for: APY mean reversion,
    APY crash events, impermanent loss via geometric Brownian motion,
    pool failure probability, and gas costs.
    Runs 1,000 simulations.

    Returns optimistic/base/bearish scenarios with dollar amounts,
    percentiles, probability of profit, and risk factors.

    PRO ONLY — requires PROFITSPOT_API_KEY.
    """
    # Rate limit check
    if err := rate_gate():
        return err

    gate = pro_gate("simulate_profit")
    if gate:
        return gate

    data = await simulate_profit_impl(pool_id, investment, days, compound)

    if "error" in data:
        return build_response(data, confidence=0.0, tool="simulate_profit", tier="pro")

    confidence = 0.80  # Monte Carlo model — inherently uncertain
    return build_response(data, confidence=confidence, tool="simulate_profit", tier="pro")


# ══════════════════════════════════════════════════════════════════
# TOOL 5: risk_score (PRO ONLY)
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def risk_score(
    pool_id: str | None = None,
    protocol: str | None = None,
) -> dict:
    """Get risk grade (A-F) for a specific pool or entire protocol.

    Returns overall grade, breakdown scores for: TVL stability,
    APY sustainability + volatility, protocol reputation + age,
    IL exposure, pair stability, and security/audit proxy.
    Each sub-score explained in plain English.

    For protocols: scores the top pools and returns an aggregate grade.

    PRO ONLY — requires PROFITSPOT_API_KEY.
    """
    # Rate limit check
    if err := rate_gate():
        return err

    gate = pro_gate("risk_score")
    if gate:
        return gate

    data = await risk_score_impl(pool_id, protocol)

    if "error" in data:
        return build_response(data, confidence=0.0, tool="risk_score", tier="pro")

    # Higher confidence if we have historical data
    has_factors = "factors" in data
    confidence = 0.88 if has_factors else 0.75
    return build_response(data, confidence=confidence, tool="risk_score", tier="pro")


# ══════════════════════════════════════════════════════════════════
# TOOL 6: track_whales (PRO ONLY)
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def track_whales(
    chain: str | None = None,
    min_tvl_change: float = 500_000,
    timeframe: str = "24h",
) -> dict:
    """Detect large capital movements (whale activity) across DeFi pools.

    Finds pools where TVL changed by >$500K since last snapshot.
    Reports: pool, direction (inflow/outflow), amount, percentage change,
    and whether this correlates with APY changes.

    First call establishes a baseline; subsequent calls detect actual changes.
    Also uses APY-change heuristics as a proxy for whale activity.

    PRO ONLY — requires PROFITSPOT_API_KEY.
    """
    # Rate limit check
    if err := rate_gate():
        return err

    gate = pro_gate("track_whales")
    if gate:
        return gate

    data = await track_whales_impl(chain, min_tvl_change, timeframe)

    if "error" in data:
        return build_response(data, confidence=0.3, tool="track_whales", tier="pro")

    is_baseline = data.get("tracking_status") == "baseline_established"
    confidence = 0.60 if is_baseline else 0.85
    return build_response(data, confidence=confidence, tool="track_whales", tier="pro")


# ══════════════════════════════════════════════════════════════════
# TOOL 7: defi_overview (FREE — basic stats / PRO — full stats)
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def defi_overview(chain: str | None = None) -> dict:
    """Big-picture DeFi dashboard.

    Returns: total DeFi TVL, TVL by top 10 chains, top 10 protocols
    by TVL, pool counts, and average yields.

    FREE tier: basic stats (TVL, chains, protocols).
    PRO tier: + average yields by risk grade, stablecoin market cap,
    hot opportunities (new pools with high APY + good risk grade).
    """
    # Rate limit check
    if err := rate_gate():
        return err

    tier = get_tier()
    full_stats = tier == Tier.PRO

    data = await defi_overview_impl(chain=chain, full_stats=full_stats)

    if "error" in data:
        return build_response(data, confidence=0.3, tool="defi_overview", tier=tier.value)

    confidence = 0.90 if data.get("total_pools", 0) > 100 else 0.70
    return build_response(data, confidence=confidence, tool="defi_overview", tier=tier.value)


# ── Entry Point ───────────────────────────────────────────────────

def main():
    """Run the MCP server (HTTP transport for production)."""
    mcp.run(transport="sse", host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
