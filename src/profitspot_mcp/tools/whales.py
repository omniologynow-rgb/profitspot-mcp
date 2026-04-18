"""
Tool 6: track_whales
Detect large capital movements across DeFi pools.

Strategy:
  - Compare current TVL snapshots to cached previous snapshots.
  - Also use APY change signals as proxy (large APY drop = capital inflow).
  - First call establishes baseline; subsequent calls detect changes.
"""
from ..defillama import get_client
from ..cache import cache
from datetime import datetime, timezone

SNAPSHOT_CACHE_KEY = "whale_tvl_snapshot"
SNAPSHOT_TTL = 3600  # 1 hour


async def track_whales_impl(
    chain: str | None = None,
    min_tvl_change: float = 500_000,
    timeframe: str = "24h",
) -> dict:
    """
    Detect large capital movements.

    Finds pools with TVL changes > threshold since last snapshot.
    Also flags pools with dramatic APY changes (capital flow proxy).
    """
    client = get_client()
    current_pools = await client.fetch_pools()
    if not current_pools:
        return {"movements": [], "error": "DeFiLlama API unavailable"}

    # Filter by chain if specified
    if chain:
        current_pools = [
            p for p in current_pools
            if (p.get("chain", "") or "").lower() == chain.lower()
        ]

    # Build current TVL map
    current_map: dict[str, dict] = {}
    for p in current_pools:
        pid = p.get("pool", "")
        tvl = p.get("tvlUsd", 0) or 0
        if pid and tvl > 100_000:  # Only track pools with meaningful TVL
            current_map[pid] = {
                "tvl": tvl,
                "symbol": p.get("symbol", "?"),
                "protocol": p.get("project", "?"),
                "chain": p.get("chain", "?"),
                "apy": p.get("apy", 0) or 0,
                "apyPct1D": p.get("apyPct1D") or 0,
                "apyPct7D": p.get("apyPct7D") or 0,
            }

    # Load previous snapshot
    prev_snapshot = cache.get(SNAPSHOT_CACHE_KEY)
    snapshot_age = cache.get_age(SNAPSHOT_CACHE_KEY)

    # Save current as new snapshot
    cache.set(SNAPSHOT_CACHE_KEY, {
        "map": {pid: d["tvl"] for pid, d in current_map.items()},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, ttl=SNAPSHOT_TTL)

    movements: list[dict] = []

    if prev_snapshot and isinstance(prev_snapshot, dict):
        prev_map = prev_snapshot.get("map", {})
        prev_ts = prev_snapshot.get("timestamp", "")

        for pid, current_data in current_map.items():
            prev_tvl = prev_map.get(pid)
            if prev_tvl is None:
                continue

            tvl_change = current_data["tvl"] - prev_tvl
            abs_change = abs(tvl_change)

            if abs_change >= min_tvl_change:
                pct_change = (tvl_change / prev_tvl * 100) if prev_tvl > 0 else 0
                direction = "inflow" if tvl_change > 0 else "outflow"

                # Correlate with APY changes
                apy_1d = current_data["apyPct1D"]
                apy_signal = ""
                if direction == "inflow" and apy_1d < -5:
                    apy_signal = "APY declining (diluted by new capital)"
                elif direction == "outflow" and apy_1d > 10:
                    apy_signal = "APY spiking (less capital, same rewards)"

                movements.append({
                    "pool_id": pid,
                    "symbol": current_data["symbol"],
                    "protocol": current_data["protocol"],
                    "chain": current_data["chain"],
                    "direction": direction,
                    "tvl_change_usd": round(tvl_change, 0),
                    "tvl_change_pct": round(pct_change, 2),
                    "current_tvl": round(current_data["tvl"], 0),
                    "previous_tvl": round(prev_tvl, 0),
                    "current_apy": round(current_data["apy"], 2),
                    "apy_correlation": apy_signal or "No strong APY correlation",
                })
    else:
        # No previous snapshot — use APY change heuristics
        for pid, data in current_map.items():
            apy_1d_change = abs(data["apyPct1D"])
            apy_7d_change = abs(data["apyPct7D"])

            # Large APY changes in high-TVL pools suggest whale movement
            if data["tvl"] >= 5_000_000 and (apy_1d_change > 20 or apy_7d_change > 40):
                direction = "likely_inflow" if data["apyPct1D"] < 0 else "likely_outflow"
                movements.append({
                    "pool_id": pid,
                    "symbol": data["symbol"],
                    "protocol": data["protocol"],
                    "chain": data["chain"],
                    "direction": direction,
                    "tvl_change_usd": None,
                    "tvl_change_pct": None,
                    "current_tvl": round(data["tvl"], 0),
                    "previous_tvl": None,
                    "current_apy": round(data["apy"], 2),
                    "apy_correlation": f"APY changed {data['apyPct1D']:.1f}% in 24h (whale signal)",
                    "detection_method": "apy_heuristic",
                })

    # Sort by absolute change
    movements.sort(
        key=lambda x: abs(x.get("tvl_change_usd") or 0),
        reverse=True,
    )

    is_baseline = prev_snapshot is None
    return {
        "movements": movements[:50],
        "total_detected": len(movements),
        "tracking_status": "baseline_established" if is_baseline else "comparing_snapshots",
        "snapshot_age_seconds": round(snapshot_age, 0) if snapshot_age else None,
        "filters": {
            "chain": chain,
            "min_tvl_change": min_tvl_change,
            "timeframe": timeframe,
        },
        "note": (
            "First call — baseline established. Subsequent calls will detect actual TVL changes. "
            "Current results use APY-change heuristics as a proxy for whale activity."
        ) if is_baseline else f"Comparing to snapshot from {round(snapshot_age, 0) if snapshot_age else '?'}s ago.",
    }
