"""
ProfitSpot MCP — Freemium Auth Layer

Tier enforcement:
  FREE  — No PROFITSPOT_API_KEY set
         discover_yields (limit 10, no risk filter)
         defi_overview (basic stats)
         calculate_impermanent_loss (always free)
         Rate limit: 50 queries/day

  PRO   — Valid PROFITSPOT_API_KEY in env
         All 7 tools, full parameters, higher limits
         Rate limit: 1,000/day ($29/mo) or 10K/day ($99/mo)
"""
import os
import time
from enum import Enum


class Tier(str, Enum):
    FREE = "free"
    PRO = "pro"


# Tools available at each tier
FREE_TOOLS = {"discover_yields", "defi_overview", "calculate_impermanent_loss"}
PRO_ONLY_TOOLS = {"analyze_pool", "simulate_profit", "risk_score", "track_whales"}

# Rate limits per tier (requests per day)
RATE_LIMITS = {
    Tier.FREE: 50,
    Tier.PRO: 1_000,   # $29/mo plan; $99/mo gets 10K (future key-level differentiation)
}

# Stripe payment links
UPGRADE_URLS = {
    "pro": "https://buy.stripe.com/3cIaEZ0Gf1DrgQodvh4wM00",
    "enterprise": "https://buy.stripe.com/7sY28t9cL81P8jS1Mz4wM01",
    "pricing": "https://profitspot.live/pricing",
}


class _RateLimiter:
    """Simple in-memory rate limiter using a sliding daily window."""

    def __init__(self):
        self._calls: list[float] = []

    def _prune(self):
        """Remove entries older than 24 hours."""
        cutoff = time.time() - 86_400
        self._calls = [t for t in self._calls if t > cutoff]

    def check(self, limit: int) -> tuple[bool, int]:
        """
        Check if a request is allowed under the given limit.
        Returns (allowed, remaining_calls).
        """
        self._prune()
        remaining = max(0, limit - len(self._calls))
        if len(self._calls) >= limit:
            return False, 0
        self._calls.append(time.time())
        return True, remaining - 1

    @property
    def usage_today(self) -> int:
        self._prune()
        return len(self._calls)


# Singleton rate limiter instance (per-process)
_limiter = _RateLimiter()


def get_tier() -> Tier:
    """Determine current tier based on PROFITSPOT_API_KEY env var."""
    key = os.environ.get("PROFITSPOT_API_KEY", "").strip()
    if key and len(key) >= 8:
        return Tier.PRO
    return Tier.FREE


def check_tool_access(tool_name: str) -> tuple[bool, str]:
    """
    Check if current tier has access to a tool.
    Returns (allowed, message).
    """
    tier = get_tier()
    if tool_name in FREE_TOOLS:
        return True, f"Access granted ({tier.value} tier)"
    if tier == Tier.PRO:
        return True, "Access granted (pro tier)"
    return False, (
        f"'{tool_name}' requires ProfitSpot Pro. "
        f"Set PROFITSPOT_API_KEY env var. Get your key → {UPGRADE_URLS['pro']}"
    )


def check_rate_limit() -> tuple[bool, dict]:
    """
    Check if the current request is within the daily rate limit.
    Returns (allowed, info_dict).

    Call this at the start of every tool invocation.
    """
    tier = get_tier()
    limit = RATE_LIMITS[tier]
    allowed, remaining = _limiter.check(limit)
    info = {
        "tier": tier.value,
        "daily_limit": limit,
        "remaining": remaining,
        "usage_today": _limiter.usage_today,
    }
    if not allowed:
        info["error"] = "rate_limit_exceeded"
        info["message"] = (
            f"Daily rate limit of {limit} requests exceeded ({tier.value} tier). "
            f"Upgrade for higher limits → {UPGRADE_URLS['pricing']}"
        )
        if tier == Tier.FREE:
            info["upgrade_url_pro"] = UPGRADE_URLS["pro"]
            info["upgrade_url_enterprise"] = UPGRADE_URLS["enterprise"]
    return allowed, info


def get_discover_limit() -> int:
    """Max results for discover_yields based on tier."""
    return 50 if get_tier() == Tier.PRO else 10


def can_filter_risk() -> bool:
    """Whether risk grade filtering is available."""
    return get_tier() == Tier.PRO


def pro_gate(tool_name: str) -> dict | None:
    """
    Returns a gated response dict if tool is blocked, None if allowed.
    Use at the top of pro-only tools.
    """
    allowed, message = check_tool_access(tool_name)
    if allowed:
        return None
    return {
        "error": "pro_required",
        "tool": tool_name,
        "message": message,
        "tier": "free",
        "upgrade_url_pro": UPGRADE_URLS["pro"],
        "upgrade_url_enterprise": UPGRADE_URLS["enterprise"],
        "pricing_page": UPGRADE_URLS["pricing"],
        "free_tools_available": sorted(FREE_TOOLS),
    }


def rate_gate() -> dict | None:
    """
    Returns a rate-limit error dict if limit exceeded, None if OK.
    Call at the top of every tool handler.
    """
    allowed, info = check_rate_limit()
    if allowed:
        return None
    return info
