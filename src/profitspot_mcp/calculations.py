"""
ProfitSpot MCP — Financial Calculations

Impermanent Loss:
  IL = 2*sqrt(r) / (1+r) - 1
  where r = price_ratio = new_price / old_price

Monte Carlo Profit Simulation:
  Ornstein-Uhlenbeck APY model from ProfitSpot SaaS.
  Includes IL via geometric Brownian motion, pool failure risk,
  APY crash events. 1,000 iterations.

Simple Projections:
  Compound / non-compound return calculation.
"""
import numpy as np
from typing import Optional


# ═══════════════════════════════════════════════════════════════
# IMPERMANENT LOSS CALCULATOR
# ═══════════════════════════════════════════════════════════════

def calculate_impermanent_loss(
    token_a_price_change: float,
    token_b_price_change: float,
    investment_amount: float = 10_000,
) -> dict:
    """
    Calculate exact impermanent loss for a 50/50 LP pair.

    Args:
        token_a_price_change: % change for token A (e.g., 50 for +50%)
        token_b_price_change: % change for token B (e.g., -20 for -20%)
        investment_amount: Initial investment in USD

    Returns:
        IL details including USD loss, percentage, hold vs LP comparison,
        and net results at various fee APY levels.
    """
    # Price ratios
    ratio_a = 1 + (token_a_price_change / 100)
    ratio_b = 1 + (token_b_price_change / 100)

    # Prevent invalid ratios
    ratio_a = max(ratio_a, 0.001)
    ratio_b = max(ratio_b, 0.001)

    # Value if simply held (no LP)
    half = investment_amount / 2
    value_if_held = half * ratio_a + half * ratio_b

    # Value in LP (constant product AMM formula for 50/50 pool)
    # Derivation: LP_value = V₀ * sqrt(ratio_a * ratio_b)
    # IL ratio  = 2*sqrt(a*b)/(a+b) - 1
    lp_value = investment_amount * np.sqrt(ratio_a * ratio_b)

    # IL (always negative or zero — a loss)
    il_usd = lp_value - value_if_held
    il_percent = (il_usd / value_if_held) * 100 if value_if_held > 0 else 0

    # Net returns at various APY fee levels (annual, applied to LP value)
    fee_levels = {"5%": 0.05, "10%": 0.10, "20%": 0.20, "50%": 0.50}
    net_with_fees = {}
    for label, rate in fee_levels.items():
        fees_earned = investment_amount * rate  # Approx 1-year fees
        net_gain = lp_value + fees_earned - investment_amount
        net_with_fees[label] = {
            "fees_earned": round(fees_earned, 2),
            "net_gain_usd": round(net_gain, 2),
            "net_roi_pct": round((net_gain / investment_amount) * 100, 2) if investment_amount > 0 else 0,
        }

    return {
        "token_a_change_pct": token_a_price_change,
        "token_b_change_pct": token_b_price_change,
        "investment_amount": investment_amount,
        "il_percent": round(abs(il_percent), 4),
        "il_usd": round(abs(il_usd), 2),
        "value_if_held": round(value_if_held, 2),
        "value_in_lp": round(lp_value, 2),
        "net_with_fees": net_with_fees,
        "interpretation": _il_interpretation(abs(il_percent)),
    }


def _il_interpretation(il_pct: float) -> str:
    """Human-readable IL interpretation."""
    if il_pct < 0.5:
        return "Negligible IL — price ratio barely changed."
    if il_pct < 2:
        return "Minor IL — easily offset by modest trading fees."
    if il_pct < 5:
        return "Moderate IL — needs decent APY to compensate."
    if il_pct < 15:
        return "Significant IL — high APY required to remain profitable."
    return "Severe IL — LP position likely unprofitable without exceptional fee income."


# ═══════════════════════════════════════════════════════════════
# MONTE CARLO PROFIT SIMULATION (Ornstein-Uhlenbeck)
# ═══════════════════════════════════════════════════════════════

def simulate_il_gbm(il_risk: str, days: int) -> float:
    """
    Simulate Impermanent Loss using Geometric Brownian Motion.
    Returns IL as positive percentage.
    """
    annual_vol = {"low": 0.30, "medium": 0.80, "high": 1.50}.get(il_risk.lower(), 0.80)
    daily_vol = annual_vol / np.sqrt(365)
    daily_returns = np.random.normal(0, daily_vol, days)
    log_return = np.sum(daily_returns)
    price_ratio = max(np.exp(log_return), 0.01)
    il_factor = 2 * np.sqrt(price_ratio) / (1 + price_ratio) - 1
    return abs(il_factor) * 100


def run_monte_carlo(
    current_apy: float,
    tvl: float,
    il_risk: str,
    days: int,
    investment: float = 10_000,
    num_simulations: int = 1_000,
    compound: bool = True,
) -> dict:
    """
    Run Monte Carlo simulation using Ornstein-Uhlenbeck APY process.

    APY Model: dAPY = theta*(mu - APY)*dt + sigma*dW
      - theta: mean reversion speed (scales with APY level)
      - mu: long-term mean (decays for high-APY pools)
      - sigma: volatility (scales with IL risk + TVL)

    Includes: APY crashes, pool failure probability, IL simulation.

    Returns:
      Percentiles, scenarios, probability profitable, risk factors.
    """
    np.random.seed(None)

    # ── APY Mean Reversion Target ─────────────────────────────
    if current_apy <= 10:
        mu, theta = current_apy * 0.90, 0.05
    elif current_apy <= 25:
        mu, theta = current_apy * 0.75, 0.08
    elif current_apy <= 50:
        mu, theta = current_apy * 0.55, 0.12
    elif current_apy <= 100:
        mu, theta = min(25.0, current_apy * 0.35), 0.20
    elif current_apy <= 300:
        mu, theta = min(18.0, current_apy * 0.15), 0.35
    else:
        mu, theta = min(12.0, current_apy * 0.05), 0.50

    # ── Volatility ────────────────────────────────────────────
    sigma = {"low": 0.15, "medium": 0.30, "high": 0.50}.get(il_risk.lower(), 0.30)
    if tvl < 100_000:
        sigma *= 2.0
    elif tvl < 1_000_000:
        sigma *= 1.5
    elif tvl < 5_000_000:
        sigma *= 1.2
    if current_apy > 300:
        sigma *= 1.6
    elif current_apy > 100:
        sigma *= 1.3

    # ── Pool Failure Probability ──────────────────────────────
    if tvl < 100_000:
        death_prob = 0.20
    elif tvl < 1_000_000:
        death_prob = 0.10
    elif tvl < 10_000_000:
        death_prob = 0.04
    elif tvl < 100_000_000:
        death_prob = 0.01
    else:
        death_prob = 0.005
    if current_apy > 200:
        death_prob += 0.15
    elif current_apy > 100:
        death_prob += 0.08
    elif current_apy > 50:
        death_prob += 0.03
    death_prob = min(death_prob * min(days / 365, 1.0), 0.40)

    # ── Daily APY Crash Probability ───────────────────────────
    crash_prob = 0.002 if current_apy <= 50 else (0.005 if current_apy <= 150 else 0.01)

    gas_fee_pct = 0.5
    final_rois: list[float] = []

    for _ in range(num_simulations):
        if np.random.random() < death_prob:
            final_rois.append(-np.random.uniform(60, 95))
            continue

        apy = current_apy
        cumulative = 0.0

        for day in range(days):
            if np.random.random() < crash_prob:
                apy *= np.random.uniform(0.05, 0.40)
            dW = np.random.normal(0, 1.0)
            apy = max(0.01, apy + theta * (mu - apy) + sigma * dW)
            daily_rate = apy / 365 / 100
            if compound:
                cumulative = (1 + cumulative) * (1 + daily_rate) - 1
            else:
                cumulative += daily_rate

        gross_pct = cumulative * 100
        il_loss = simulate_il_gbm(il_risk, days)
        net_roi = gross_pct - il_loss - gas_fee_pct
        final_rois.append(net_roi)

    arr = np.array(final_rois)

    # ── Results ───────────────────────────────────────────────
    percentiles = {
        f"p{p}": round(float(np.percentile(arr, p)), 2)
        for p in [5, 10, 25, 50, 75, 90, 95]
    }
    prob_profitable = round(float(np.mean(arr > 0) * 100), 1)
    mean_roi = round(float(np.mean(arr)), 2)
    median_roi = percentiles["p50"]

    # Scenarios
    bearish = round(float(np.percentile(arr, 10)), 2)
    base = median_roi
    optimistic = round(float(np.percentile(arr, 90)), 2)

    scenarios = [
        {
            "label": "Bearish (P10)",
            "roi_pct": bearish,
            "profit_usd": round(investment * bearish / 100, 2),
            "final_value": round(investment * (1 + bearish / 100), 2),
        },
        {
            "label": "Base (Median)",
            "roi_pct": base,
            "profit_usd": round(investment * base / 100, 2),
            "final_value": round(investment * (1 + base / 100), 2),
        },
        {
            "label": "Optimistic (P90)",
            "roi_pct": optimistic,
            "profit_usd": round(investment * optimistic / 100, 2),
            "final_value": round(investment * (1 + optimistic / 100), 2),
        },
    ]

    risk_factors = []
    if current_apy > 100:
        risk_factors.append("Very high APY — likely to decay significantly")
    if tvl < 1_000_000:
        risk_factors.append("Low TVL — higher slippage and rug risk")
    if il_risk == "high":
        risk_factors.append("High IL risk — volatile pair")
    if death_prob > 0.10:
        risk_factors.append(f"Pool failure probability: {death_prob*100:.0f}%")
    if not risk_factors:
        risk_factors.append("No major red flags detected")

    return {
        "percentiles": percentiles,
        "probability_profitable": prob_profitable,
        "mean_roi_pct": mean_roi,
        "median_roi_pct": median_roi,
        "scenarios": scenarios,
        "risk_factors": risk_factors,
        "parameters": {
            "current_apy": current_apy,
            "tvl": tvl,
            "il_risk": il_risk,
            "days": days,
            "investment": investment,
            "compound": compound,
            "simulations": num_simulations,
            "model": "Ornstein-Uhlenbeck + GBM-IL + Pool Failure",
        },
    }


# ═══════════════════════════════════════════════════════════════
# SIMPLE PROJECTION (for analyze_pool quick returns)
# ═══════════════════════════════════════════════════════════════

def project_returns(
    apy: float,
    investment: float,
    days: int,
    compound: bool = True,
) -> dict:
    """
    Simple deterministic projection at fixed APY.
    Returns projected values for given investment amounts.
    """
    daily_rate = apy / 365 / 100
    if compound:
        growth = (1 + daily_rate) ** days
    else:
        growth = 1 + daily_rate * days

    final = investment * growth
    profit = final - investment
    roi_pct = ((growth - 1) * 100)

    return {
        "investment": investment,
        "days": days,
        "apy_used": apy,
        "compound": compound,
        "final_value": round(final, 2),
        "profit": round(profit, 2),
        "roi_pct": round(roi_pct, 2),
    }


def project_returns_multi(apy: float, days_list: list[int] = None) -> list[dict]:
    """
    Project returns for $1K/$10K/$100K at various time horizons.
    """
    if days_list is None:
        days_list = [30, 90, 365]
    investments = [1_000, 10_000, 100_000]
    results = []
    for inv in investments:
        for d in days_list:
            r = project_returns(apy, inv, d)
            results.append(r)
    return results
