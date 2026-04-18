"""
ProfitSpot MCP — DeFiLlama API Client
100% free, no API key required.

Endpoints:
  https://yields.llama.fi/pools          — All yield pools (6,500+)
  https://yields.llama.fi/chart/{pool}   — Historical APY/TVL for a pool
  https://api.llama.fi/protocols          — All DeFi protocols
  https://api.llama.fi/protocol/{name}   — Protocol detail + TVL by chain
  https://api.llama.fi/v2/chains          — All chains with TVL
  https://stablecoins.llama.fi/stablecoins — Stablecoin market caps
"""
import httpx
import logging
from typing import Optional, Any

from .cache import cache

logger = logging.getLogger(__name__)

YIELDS_BASE = "https://yields.llama.fi"
API_BASE = "https://api.llama.fi"
STABLECOINS_BASE = "https://stablecoins.llama.fi"


class DeFiLlamaClient:
    """Async DeFiLlama API client with in-memory caching."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def _get(self, url: str, cache_key: str, ttl: int = 300) -> Optional[Any]:
        """Generic GET with caching."""
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    cache.set(cache_key, data, ttl=ttl)
                    return data
                logger.error("DeFiLlama %s returned %d", url, resp.status_code)
        except Exception as e:
            logger.error("DeFiLlama fetch failed %s: %s", url, e)
        return None

    # ── Pool Endpoints ────────────────────────────────────────

    async def fetch_pools(self) -> list[dict]:
        """Fetch all yield pools (~6,500+)."""
        data = await self._get(f"{YIELDS_BASE}/pools", "all_pools", ttl=300)
        return data.get("data", []) if isinstance(data, dict) else []

    async def fetch_pool_chart(self, pool_id: str) -> list[dict]:
        """Fetch historical APY/TVL for a specific pool."""
        data = await self._get(
            f"{YIELDS_BASE}/chart/{pool_id}", f"chart:{pool_id}", ttl=600
        )
        return data.get("data", []) if isinstance(data, dict) else []

    # ── Protocol Endpoints ────────────────────────────────────

    async def fetch_protocols(self) -> list[dict]:
        """Fetch all DeFi protocols."""
        data = await self._get(f"{API_BASE}/protocols", "all_protocols", ttl=600)
        return data if isinstance(data, list) else []

    async def fetch_protocol(self, name: str) -> Optional[dict]:
        """Fetch protocol detail + TVL by chain."""
        return await self._get(
            f"{API_BASE}/protocol/{name}", f"protocol:{name}", ttl=600
        )

    # ── Chain Endpoints ───────────────────────────────────────

    async def fetch_chains(self) -> list[dict]:
        """Fetch all chains with TVL."""
        data = await self._get(f"{API_BASE}/v2/chains", "all_chains", ttl=600)
        return data if isinstance(data, list) else []

    # ── Stablecoin Endpoints ──────────────────────────────────

    async def fetch_stablecoins(self) -> Optional[dict]:
        """Fetch stablecoin market caps + flows."""
        return await self._get(
            f"{STABLECOINS_BASE}/stablecoins", "stablecoins", ttl=600
        )

    # ── Convenience ───────────────────────────────────────────

    async def find_pool_by_id(self, pool_id: str) -> Optional[dict]:
        """Find a single pool by its ID from the full pool list."""
        pools = await self.fetch_pools()
        for p in pools:
            if p.get("pool") == pool_id:
                return p
        return None


# ── Singleton ─────────────────────────────────────────────────
_client: Optional[DeFiLlamaClient] = None


def get_client() -> DeFiLlamaClient:
    """Get or create the DeFiLlama client singleton."""
    global _client
    if _client is None:
        _client = DeFiLlamaClient()
    return _client
