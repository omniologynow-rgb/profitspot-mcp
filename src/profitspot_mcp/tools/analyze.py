"""
Tool 2: analyze_pool
Deep analysis of a specific pool.
"""
from ..defillama import get_client
from ..scoring import calculate_risk_grade
from ..calculations import project_returns_multi, calculate_impermanent_loss
import numpy as np


async def analyze_pool_impl(pool_id: str) -> dict:
    """
    Deep-dive analysis of a single pool.

    Returns:
      Pool data, APY trends (7d/30d/90d), TVL history,
      risk grade breakdown, IL estimate, projected returns.
    """
    client = get_client()

    # Fetch pool data
    pool = await client.find_pool_by_id(pool_id)
    if not pool:
        return {"error": f"Pool '{pool_id}' not found. Use discover_yields to find valid pool IDs."}

    # Fetch historical data
    history = await client.fetch_pool_chart(pool_id)

    apy = pool.get("apy", 0) or 0
    tvl = pool.get("tvlUsd", 0) or 0
    il_risk_raw = (pool.get("ilRisk", "") or "").lower() or "medium"

    # ── APY Trend Analysis ────────────────────────────────────
    apy_trend = {"current": round(apy, 2)}
    if history:
        recent = history[-90:] if len(history) >= 90 else history
        apy_vals = [h.get("apy", 0) or 0 for h in recent]
        tvl_vals = [h.get("tvlUsd", 0) or 0 for h in recent]

        if len(apy_vals) >= 7:
            apy_trend["avg_7d"] = round(float(np.mean(apy_vals[-7:])), 2)
        if len(apy_vals) >= 30:
            apy_trend["avg_30d"] = round(float(np.mean(apy_vals[-30:])), 2)
        if len(apy_vals) >= 90:
            apy_trend["avg_90d"] = round(float(np.mean(apy_vals)), 2)

        if len(apy_vals) >= 7:
            recent_avg = float(np.mean(apy_vals[-7:]))
            older_avg = float(np.mean(apy_vals[:-7])) if len(apy_vals) > 7 else recent_avg
            if recent_avg > older_avg * 1.1:
                apy_trend["direction"] = "increasing"
            elif recent_avg < older_avg * 0.9:
                apy_trend["direction"] = "decreasing"
            else:
                apy_trend["direction"] = "stable"

        apy_trend["volatility_stdev"] = round(float(np.std(apy_vals)), 2) if apy_vals else 0

        # TVL trend
        if len(tvl_vals) >= 2:
            tvl_start = tvl_vals[0] if tvl_vals[0] > 0 else 1
            tvl_change_pct = ((tvl_vals[-1] - tvl_start) / tvl_start) * 100
            apy_trend["tvl_change_pct"] = round(tvl_change_pct, 2)
    else:
        apy_trend["direction"] = "unknown"
        apy_trend["note"] = "No historical data available"

    # ── Risk Grade Breakdown ──────────────────────────────────
    risk = calculate_risk_grade(pool, historical_apy=history if history else None)

    # ── IL Estimate ───────────────────────────────────────────
    il_estimate = None
    exposure = pool.get("exposure", "single")
    if exposure == "multi" and il_risk_raw not in ("no", "none"):
        # Estimate IL for typical price divergence scenarios
        scenarios = [
            {"label": "Minor divergence (+10%/-5%)", "a": 10, "b": -5},
            {"label": "Moderate divergence (+30%/-10%)", "a": 30, "b": -10},
            {"label": "Major divergence (+80%/-30%)", "a": 80, "b": -30},
        ]
        il_estimate = []
        for s in scenarios:
            il = calculate_impermanent_loss(s["a"], s["b"], 10_000)
            il_estimate.append({
                "scenario": s["label"],
                "il_percent": il["il_percent"],
                "il_usd_per_10k": il["il_usd"],
            })

    # ── Projected Returns ─────────────────────────────────────
    projections = project_returns_multi(apy, days_list=[30, 90, 365])

    # ── Pool Summary ──────────────────────────────────────────
    prediction_raw = pool.get("predictions") or {}
    prediction_class = prediction_raw.get("predictedClass", "stable") if isinstance(prediction_raw, dict) else "stable"

    return {
        "pool": {
            "pool_id": pool.get("pool", ""),
            "symbol": pool.get("symbol", "?"),
            "protocol": pool.get("project", "?"),
            "chain": pool.get("chain", "?"),
            "apy": round(apy, 2),
            "apy_base": round(pool.get("apyBase", 0) or 0, 2),
            "apy_reward": round(pool.get("apyReward", 0) or 0, 2),
            "tvl_usd": round(tvl, 0),
            "stablecoin": bool(pool.get("stablecoin", False)),
            "il_risk": il_risk_raw,
            "exposure": exposure,
            "prediction": prediction_class,
            "reward_tokens": pool.get("rewardTokens") or [],
            "underlying_tokens": pool.get("underlyingTokens") or [],
        },
        "apy_trend": apy_trend,
        "risk_grade": risk,
        "il_estimate": il_estimate,
        "projected_returns": projections,
        "data_points": len(history) if history else 0,
    }
