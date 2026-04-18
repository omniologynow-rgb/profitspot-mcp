"""
ProfitSpot MCP — Tool Integration Tests

Tests all 7 tools against live DeFiLlama API.
Run: cd /app/profitspot-mcp && .venv/bin/python -m pytest tests/ -v
"""
import asyncio
import sys
import os

# Add source to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from profitspot_mcp.tools.discover import discover_yields_impl
from profitspot_mcp.tools.overview import defi_overview_impl
from profitspot_mcp.tools.impermanent_loss import calculate_il_impl
from profitspot_mcp.tools.risk import risk_score_impl
from profitspot_mcp.tools.analyze import analyze_pool_impl
from profitspot_mcp.tools.simulate import simulate_profit_impl
from profitspot_mcp.tools.whales import track_whales_impl
from profitspot_mcp.calculations import calculate_impermanent_loss, run_monte_carlo, project_returns
from profitspot_mcp.scoring import calculate_risk_grade


def run(coro):
    """Run async function."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ────────────────────────────────────────────────────────────
# UNIT TESTS — No API calls
# ────────────────────────────────────────────────────────────

def test_impermanent_loss_math():
    """Test IL calculation with known values."""
    # No price change = no IL
    result = calculate_impermanent_loss(0, 0, 10_000)
    assert result["il_percent"] < 0.01, f"Expected ~0 IL, got {result['il_percent']}%"
    assert abs(result["value_if_held"] - 10_000) < 1

    # ETH doubles, USDC stays: ~5.7% IL
    result = calculate_impermanent_loss(100, 0, 10_000)
    assert 5.0 < result["il_percent"] < 6.5, f"Expected ~5.7% IL, got {result['il_percent']}%"
    assert result["value_if_held"] == 15_000  # half doubled, half stayed

    # Both tokens double: no IL
    result = calculate_impermanent_loss(100, 100, 10_000)
    assert result["il_percent"] < 0.01
    print("\u2705 IL math tests passed")


def test_risk_scoring():
    """Test risk grading with synthetic pool data."""
    # Grade A: High TVL, low APY, Tier 1 protocol, stablecoin
    pool_a = {
        "tvlUsd": 500_000_000, "apy": 5.0, "project": "aave-v3",
        "stablecoin": True, "ilRisk": "no", "exposure": "single",
    }
    result = calculate_risk_grade(pool_a)
    assert result["grade"] == "A", f"Expected A, got {result['grade']} (score {result['score']})"

    # Grade F: Low TVL, extreme APY, unknown protocol
    pool_f = {
        "tvlUsd": 50_000, "apy": 800, "project": "scamcoin-yield",
        "stablecoin": False, "ilRisk": "high", "exposure": "multi",
    }
    result = calculate_risk_grade(pool_f)
    assert result["grade"] in ("D", "F"), f"Expected D/F, got {result['grade']} (score {result['score']})"
    print("\u2705 Risk scoring tests passed")


def test_monte_carlo():
    """Test Monte Carlo simulation produces valid output."""
    result = run_monte_carlo(
        current_apy=10.0, tvl=50_000_000, il_risk="low",
        days=90, investment=10_000, num_simulations=100,
    )
    assert "percentiles" in result
    assert "scenarios" in result
    assert len(result["scenarios"]) == 3
    assert 0 <= result["probability_profitable"] <= 100
    print("\u2705 Monte Carlo tests passed")


def test_project_returns():
    """Test simple projection math."""
    result = project_returns(apy=10.0, investment=10_000, days=365, compound=True)
    # ~10% return compounded
    assert 10_900 < result["final_value"] < 11_100
    print("\u2705 Projection tests passed")


# ────────────────────────────────────────────────────────────
# INTEGRATION TESTS — Hit live DeFiLlama
# ────────────────────────────────────────────────────────────

def test_discover_yields_live():
    """Integration: discover_yields with live DeFiLlama data."""
    result = run(discover_yields_impl(min_tvl=10_000_000, limit=5))
    assert "pools" in result
    assert len(result["pools"]) > 0, "No pools returned"
    pool = result["pools"][0]
    assert "pool_id" in pool
    assert "risk_grade" in pool
    assert pool["tvl_usd"] >= 10_000_000
    print(f"\u2705 discover_yields: {len(result['pools'])} pools, "
          f"top: {pool['symbol']} {pool['apy']}% APY, grade {pool['risk_grade']}")
    return pool["pool_id"]


def test_defi_overview_live():
    """Integration: defi_overview with live data."""
    result = run(defi_overview_impl(full_stats=False))
    assert "total_pools" in result
    assert result["total_pools"] > 100, f"Only {result['total_pools']} pools"
    assert result["chains_covered"] > 10
    print(f"\u2705 defi_overview: {result['total_pools']} pools, "
          f"{result['chains_covered']} chains, TVL {result['total_tvl_formatted']}")


def test_analyze_pool_live(pool_id: str):
    """Integration: analyze_pool with live data."""
    result = run(analyze_pool_impl(pool_id))
    assert "error" not in result, f"Error: {result.get('error')}"
    assert "pool" in result
    assert "risk_grade" in result
    assert "projected_returns" in result
    print(f"\u2705 analyze_pool: {result['pool']['symbol']} — "
          f"grade {result['risk_grade']['grade']}, "
          f"{result['data_points']} data points")


def test_risk_score_live(pool_id: str):
    """Integration: risk_score for a pool."""
    result = run(risk_score_impl(pool_id=pool_id))
    assert "error" not in result
    assert "grade" in result
    assert "factors" in result
    print(f"\u2705 risk_score (pool): grade {result['grade']}, score {result['score']}")


def test_risk_score_protocol_live():
    """Integration: risk_score for a protocol."""
    result = run(risk_score_impl(protocol="aave-v3"))
    assert "error" not in result
    assert "aggregate_grade" in result
    print(f"\u2705 risk_score (protocol): aave-v3 — "
          f"grade {result['aggregate_grade']}, {result['total_pools']} pools")


def test_simulate_profit_live(pool_id: str):
    """Integration: simulate_profit with Monte Carlo."""
    result = run(simulate_profit_impl(pool_id, investment=10_000, days=90))
    assert "error" not in result
    assert "simulation" in result
    sim = result["simulation"]
    assert "scenarios" in sim
    assert len(sim["scenarios"]) == 3
    print(f"\u2705 simulate_profit: {result['pool']['symbol']} — "
          f"P(profit)={sim['probability_profitable']}%, "
          f"median ROI={sim['median_roi_pct']}%")


def test_track_whales_live():
    """Integration: track_whales (baseline establishment)."""
    result = run(track_whales_impl(min_tvl_change=1_000_000))
    assert "movements" in result
    assert "tracking_status" in result
    print(f"\u2705 track_whales: status={result['tracking_status']}, "
          f"{result['total_detected']} movements detected")


# ────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("ProfitSpot MCP — Tool Test Suite")
    print("=" * 60)

    print("\n── Unit Tests (no API) ──")
    test_impermanent_loss_math()
    test_risk_scoring()
    test_monte_carlo()
    test_project_returns()

    print("\n── Integration Tests (live DeFiLlama) ──")
    pool_id = test_discover_yields_live()
    test_defi_overview_live()

    if pool_id:
        test_analyze_pool_live(pool_id)
        test_risk_score_live(pool_id)
        test_simulate_profit_live(pool_id)

    test_risk_score_protocol_live()
    test_track_whales_live()

    print("\n" + "=" * 60)
    print("\u2705 ALL TESTS PASSED")
    print("=" * 60)
