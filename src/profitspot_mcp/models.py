"""
ProfitSpot MCP — Pydantic Response Models
Every tool response includes:
  - confidence: float (0-1)
  - data_freshness: ISO timestamp
"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime, timezone


def now_iso() -> str:
    """Current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def build_response(
    data: dict | list,
    confidence: float,
    tool: str,
    tier: str = "free",
    meta: dict | None = None,
) -> dict:
    """
    Wrap any tool result in the standard ProfitSpot MCP envelope.
    Every response includes confidence (0-1) and data_freshness.
    """
    envelope = {
        "data": data,
        "confidence": round(min(max(confidence, 0.0), 1.0), 2),
        "data_freshness": now_iso(),
        "tool": tool,
        "tier": tier,
        "powered_by": "profitspot.live",
    }
    if meta:
        envelope["meta"] = meta
    return envelope


class PoolSummary(BaseModel):
    """Compact pool representation for list views."""
    pool_id: str
    symbol: str
    protocol: str
    chain: str
    apy: float
    apy_base: float = 0.0
    apy_reward: float = 0.0
    apy_mean_30d: float | None = None
    tvl_usd: float
    risk_grade: str = "?"
    risk_score: int = 0
    stablecoin: bool = False
    il_risk: str = "unknown"
    prediction: str = "stable"
    exposure: str = "single"
    volume_1d: float | None = None
    volume_7d: float | None = None


class RiskBreakdown(BaseModel):
    """Detailed risk scoring breakdown."""
    grade: str
    score: int
    summary: str
    factors: dict[str, Any]


class ILResult(BaseModel):
    """Impermanent loss calculation result."""
    il_percent: float
    il_usd: float
    value_if_held: float
    value_in_lp: float
    net_with_fees: dict[str, float]  # apy_level -> net_gain


class ProfitScenario(BaseModel):
    """Profit simulation scenario."""
    label: str
    projected_roi_pct: float
    projected_profit_usd: float
    final_value_usd: float
    apy_assumption: float
