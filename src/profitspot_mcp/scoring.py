"""
ProfitSpot MCP — Risk Grading Algorithm

Enhanced A/B/C/D/F composite scoring.
Base: 5-factor weighted system from ProfitSpot SaaS.
Enhanced: APY volatility (stdev), protocol age tiers,
          stablecoin pair detection, audit proxy.

Scoring (100 points max):
  TVL Stability          25 pts
  APY Sustainability     20 pts  (includes volatility stdev)
  Protocol Reputation    20 pts  (includes age tier)
  IL Exposure            15 pts
  Pair Stability         10 pts  (stablecoin detection)
  Security/Audit Proxy   10 pts

Grade: A=85-100, B=70-84, C=55-69, D=40-54, F=0-39
"""
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Protocol Tier Lists ───────────────────────────────────────

TIER_1_PROTOCOLS: set[str] = {
    "aave", "uniswap", "curve", "compound", "lido", "maker", "convex",
    "aave-v3", "aave-v2", "uniswap-v3", "uniswap-v2", "curve-dex",
    "makerdao", "convex-finance", "lido",
}

TIER_2_PROTOCOLS: set[str] = {
    "morpho", "maple", "rocket-pool", "balancer", "sushi", "sushiswap",
    "yearn", "pendle", "gmx", "aerodrome", "velodrome", "pancakeswap",
    "trader-joe", "camelot", "radiant", "benqi", "stargate",
    "frax", "spark", "sky", "fluid", "euler",
    "balancer-v2", "yearn-finance", "gmx-v2",
}

# Estimated protocol age (months) — Tier 1 are battle-tested
PROTOCOL_AGE_MONTHS: dict[str, int] = {
    **{p: 48 for p in TIER_1_PROTOCOLS},
    **{p: 18 for p in TIER_2_PROTOCOLS},
}


def _get_protocol_key(protocol: str) -> str:
    """Normalize protocol name for tier lookup."""
    return protocol.lower().strip().replace(" ", "-").replace("_", "-")


def _protocol_tier(protocol: str) -> tuple[int, str, int]:
    """Returns (tier_number, label, estimated_age_months)."""
    key = _get_protocol_key(protocol)
    if key in TIER_1_PROTOCOLS or any(t in key for t in TIER_1_PROTOCOLS):
        return 1, "Tier 1 Blue Chip", PROTOCOL_AGE_MONTHS.get(key, 48)
    if key in TIER_2_PROTOCOLS or any(t in key for t in TIER_2_PROTOCOLS):
        return 2, "Tier 2 Established", PROTOCOL_AGE_MONTHS.get(key, 18)
    return 3, "Unranked", 3


def calculate_risk_grade(
    pool_data: dict,
    historical_apy: Optional[list[dict]] = None,
) -> dict:
    """
    Calculate composite risk grade A-F for a pool.

    Args:
        pool_data: Raw pool dict from DeFiLlama /pools endpoint
        historical_apy: Optional list from /chart/{pool_id} for volatility calc

    Returns:
        {grade, score, summary, factors: {name: {score, max, detail}}}
    """
    tvl = pool_data.get("tvlUsd", 0) or pool_data.get("tvl_usd", 0) or 0
    apy = pool_data.get("apy", 0) or pool_data.get("apy_total", 0) or 0
    il_risk_raw = pool_data.get("ilRisk", "") or pool_data.get("il_risk", "")
    il_risk = il_risk_raw.lower() if il_risk_raw else "medium"
    protocol = pool_data.get("project", "") or pool_data.get("protocol", "") or ""
    is_stablecoin = bool(pool_data.get("stablecoin", False) or pool_data.get("stable_coin", False))
    exposure = pool_data.get("exposure", "single")
    apy_pct_7d = pool_data.get("apyPct7D") or 0

    factors: dict[str, dict] = {}

    # ── 1. TVL Stability (25 pts) ─────────────────────────────
    if tvl >= 100_000_000:
        tvl_score, tvl_detail = 25, f"${tvl/1e6:.0f}M TVL — excellent depth"
    elif tvl >= 10_000_000:
        tvl_score, tvl_detail = 20, f"${tvl/1e6:.1f}M TVL — strong"
    elif tvl >= 1_000_000:
        tvl_score, tvl_detail = 15, f"${tvl/1e6:.2f}M TVL — moderate"
    elif tvl >= 100_000:
        tvl_score, tvl_detail = 10, f"${tvl/1e3:.0f}K TVL — thin liquidity"
    else:
        tvl_score, tvl_detail = 5, f"${tvl/1e3:.0f}K TVL — very thin, elevated rug risk"
    factors["tvl_stability"] = {"score": tvl_score, "max": 25, "detail": tvl_detail}

    # ── 2. APY Sustainability + Volatility (20 pts) ───────────
    #   Base: 14 pts from APY level
    #   Bonus: 6 pts from volatility (stdev)
    if apy <= 20:
        apy_base, apy_d = 14, f"{apy:.1f}% APY — sustainable"
    elif apy <= 50:
        apy_base, apy_d = 10, f"{apy:.1f}% APY — moderate"
    elif apy <= 100:
        apy_base, apy_d = 7, f"{apy:.1f}% APY — elevated, likely incentivised"
    elif apy <= 500:
        apy_base, apy_d = 3, f"{apy:.1f}% APY — high risk, unsustainable"
    else:
        apy_base, apy_d = 0, f"{apy:.1f}% APY — extreme, almost certainly collapses"

    # Volatility from historical data or 7d change heuristic
    if historical_apy and len(historical_apy) >= 5:
        apy_vals = [h.get("apy", 0) for h in historical_apy if h.get("apy") is not None]
        if len(apy_vals) >= 5:
            stdev = float(np.std(apy_vals))
            mean_apy = float(np.mean(apy_vals))
            cv = stdev / mean_apy if mean_apy > 0 else 1.0
            if cv < 0.10:
                vol_score, vol_label = 6, f"very stable (CV={cv:.2f})"
            elif cv < 0.30:
                vol_score, vol_label = 4, f"moderate (CV={cv:.2f})"
            elif cv < 0.60:
                vol_score, vol_label = 2, f"high (CV={cv:.2f})"
            else:
                vol_score, vol_label = 0, f"extreme (CV={cv:.2f})"
            apy_d += f" | Volatility: {vol_label}"
        else:
            vol_score = 3
    else:
        # Heuristic from 7d change
        abs_7d = abs(apy_pct_7d)
        if abs_7d < 10:
            vol_score = 5
        elif abs_7d < 30:
            vol_score = 3
        else:
            vol_score = 1

    apy_score = apy_base + vol_score
    factors["apy_sustainability"] = {"score": apy_score, "max": 20, "detail": apy_d}

    # ── 3. Protocol Reputation + Age (20 pts) ─────────────────
    tier_num, tier_label, est_age = _protocol_tier(protocol)
    if tier_num == 1:
        proto_base = 12
    elif tier_num == 2:
        proto_base = 9
    else:
        proto_base = 4

    if est_age >= 24:
        age_bonus = 8
    elif est_age >= 12:
        age_bonus = 6
    elif est_age >= 6:
        age_bonus = 4
    elif est_age >= 3:
        age_bonus = 2
    else:
        age_bonus = 0

    proto_score = proto_base + age_bonus
    proto_detail = f"{protocol or 'Unknown'} — {tier_label} (est. {est_age}+ months)"
    factors["protocol_reputation"] = {"score": proto_score, "max": 20, "detail": proto_detail}

    # ── 4. IL Exposure (15 pts) ───────────────────────────────
    if il_risk in ("no", "none", "") and exposure == "single":
        il_score, il_detail = 15, "No IL risk (single-asset)"
    elif il_risk in ("no", "none") or is_stablecoin:
        il_score, il_detail = 13, "Minimal IL (stablecoin or correlated pair)"
    elif il_risk == "low":
        il_score, il_detail = 12, "Low IL risk"
    elif il_risk == "medium" or il_risk == "yes":
        il_score, il_detail = 8, "Medium IL — monitor price divergence"
    elif il_risk == "high":
        il_score, il_detail = 4, "High IL — significant price divergence exposure"
    else:
        il_score, il_detail = 6, f"IL risk: {il_risk}"
    factors["il_exposure"] = {"score": il_score, "max": 15, "detail": il_detail}

    # ── 5. Pair Stability (10 pts) ────────────────────────────
    if is_stablecoin:
        pair_score, pair_detail = 10, "Stablecoin pool — minimal price risk"
    elif exposure == "single":
        pair_score, pair_detail = 7, "Single-asset — no pair risk"
    else:
        pair_score, pair_detail = 3, "Non-stable pair — volatile"
    factors["pair_stability"] = {"score": pair_score, "max": 10, "detail": pair_detail}

    # ── 6. Security/Audit Proxy (10 pts) ──────────────────────
    pkey = _get_protocol_key(protocol)
    if pkey in TIER_1_PROTOCOLS and tvl >= 10_000_000:
        sec_score, sec_detail = 10, "Blue chip + deep TVL — high confidence"
    elif pkey in TIER_2_PROTOCOLS and tvl >= 1_000_000:
        sec_score, sec_detail = 7, "Established protocol + reasonable TVL"
    elif tvl >= 100_000:
        sec_score, sec_detail = 4, "Moderate — verify audits independently"
    else:
        sec_score, sec_detail = 2, "Low confidence — unverified security"
    factors["security_audit"] = {"score": sec_score, "max": 10, "detail": sec_detail}

    # ── Total Score & Grade ───────────────────────────────────
    total = sum(f["score"] for f in factors.values())
    total = max(0, min(100, total))

    if total >= 85:
        grade, summary = "A", "Low Risk — Strong TVL, sustainable yield, battle-tested protocol. Suitable for conservative allocation."
    elif total >= 70:
        grade, summary = "B", "Moderate Risk — Solid fundamentals, minor concerns. Good for diversified portfolios."
    elif total >= 55:
        grade, summary = "C", "Medium Risk — Mixed signals. Research thoroughly before committing."
    elif total >= 40:
        grade, summary = "D", "High Risk — Multiple red flags. Small allocations only."
    else:
        grade, summary = "F", "Extreme Risk — Significant red flags. High probability of capital loss."

    return {
        "grade": grade,
        "score": total,
        "summary": summary,
        "factors": factors,
    }
