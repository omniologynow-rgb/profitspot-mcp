<!-- mcp-name: io.github.omniologynow-rgb/profitspot-mcp -->
<p align="center">
  <h1 align="center">ProfitSpot MCP</h1>
  <p align="center">
    Cross-chain DeFi intelligence for AI agents.<br/>
    Risk-scored yields, Monte Carlo simulations, whale tracking<br/>
    across 86 chains and 6,500+ pools.
  </p>
</p>

<p align="center">
  <a href="https://pypi.org/project/profitspot-mcp/"><img src="https://img.shields.io/pypi/v/profitspot-mcp?color=%2334D058&label=pypi" alt="PyPI version"></a>
  <a href="https://github.com/profitspot/profitspot-mcp/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0-blue.svg" alt="License: AGPL-3.0"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-compatible-8A2BE2" alt="MCP Compatible"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-3776AB.svg" alt="Python 3.11+"></a>
  <a href="https://profitspot.live"><img src="https://img.shields.io/badge/built%20by-ProfitSpot-ff6b35" alt="Built by ProfitSpot"></a>
</p>

<p align="center">
  <a href="#-quick-install">Quick Install</a> •
  <a href="#-example-tool-calls">Examples</a> •
  <a href="#-tool-reference">Tool Reference</a> •
  <a href="#-pricing">Pricing</a> •
  <a href="#-self-hosting">Self-Hosting</a>
</p>

---

## What is this?

ProfitSpot MCP gives any AI agent — Claude, GPT, Gemini, or your custom agent — instant access to the same DeFi intelligence that powers [profitspot.live](https://profitspot.live). Think of it as the **Bloomberg Terminal for AI agents**.

Existing DeFi MCP servers are either basic DeFiLlama wrappers with 1 tool, or locked to a single chain. ProfitSpot MCP covers **86 chains**, **6,500+ pools**, and adds an **intelligence layer** — risk grades, Monte Carlo profit simulation, whale detection — that no competitor has.

**No API key required to get started.** Free tier gives you yield discovery, market overview, and IL calculations immediately.

---

## 🚀 Quick Install

### Claude Desktop

Add to your `claude_desktop_config.json`:

<table>
<tr><td><strong>macOS</strong></td><td><code>~/Library/Application Support/Claude/claude_desktop_config.json</code></td></tr>
<tr><td><strong>Windows</strong></td><td><code>%APPDATA%\Claude\claude_desktop_config.json</code></td></tr>
</table>

```json
{
  "mcpServers": {
    "profitspot": {
      "command": "uvx",
      "args": ["profitspot-mcp"],
      "env": {
        "PROFITSPOT_API_KEY": "your-pro-key-here"
      }
    }
  }
}
```

> **Free tier?** Just remove the `"env"` block entirely. No key needed.

### Cursor

Add to `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "profitspot": {
      "command": "uvx",
      "args": ["profitspot-mcp"],
      "env": {
        "PROFITSPOT_API_KEY": "your-pro-key-here"
      }
    }
  }
}
```

### VS Code (Copilot)

Add to your `.vscode/mcp.json`:

```json
{
  "servers": {
    "profitspot": {
      "type": "stdio",
      "command": "uvx",
      "args": ["profitspot-mcp"],
      "env": {
        "PROFITSPOT_API_KEY": "your-pro-key-here"
      }
    }
  }
}
```

### pip (manual install)

```bash
pip install profitspot-mcp
```

---

## 💡 Example Tool Calls

Real responses from live DeFiLlama data. Every response includes `confidence` (0–1) and `data_freshness` (ISO timestamp).

### 1. Discover Yields — Ethereum, grade B or better

```
discover_yields(chain="Ethereum", min_tvl=10000000, min_apy=3, max_risk="B", limit=5)
```

<details>
<summary><strong>Full JSON Response</strong> (click to expand)</summary>

```json
{
  "data": {
    "pools": [
      {
        "pool_id": "fc9f488e-8183-416f-a61e-4e5c571d4395",
        "symbol": "WETH-USDT",
        "protocol": "uniswap-v3",
        "chain": "Ethereum",
        "apy": 31.53,
        "apy_base": 31.53,
        "apy_reward": 0,
        "apy_mean_30d": 37.11,
        "tvl_usd": 73909084,
        "risk_grade": "B",
        "risk_score": 74,
        "prediction": "Down",
        "stablecoin": false,
        "il_risk": "yes",
        "exposure": "multi"
      },
      {
        "pool_id": "3dd2c646-c05a-4483-98f4-d7a924a6d6d3",
        "symbol": "WBTC-USDT",
        "protocol": "uniswap-v3",
        "chain": "Ethereum",
        "apy": 22.24,
        "apy_base": 22.24,
        "apy_reward": 0,
        "apy_mean_30d": 21.92,
        "tvl_usd": 16180215,
        "risk_grade": "B",
        "risk_score": 74,
        "prediction": "Down",
        "stablecoin": false,
        "il_risk": "yes",
        "exposure": "multi"
      },
      {
        "pool_id": "49717ee2-9808-4288-b76d-e658195b7979",
        "symbol": "USDC-WETH",
        "protocol": "uniswap-v3",
        "chain": "Ethereum",
        "apy": 18.24,
        "apy_base": 18.24,
        "apy_reward": 0,
        "apy_mean_30d": 20.65,
        "tvl_usd": 23656801,
        "risk_grade": "B",
        "risk_score": 78,
        "prediction": "Down",
        "stablecoin": false,
        "il_risk": "yes",
        "exposure": "multi"
      },
      {
        "pool_id": "0d9e7113-c9bc-4fb6-b138-5ca6f6944d6d",
        "symbol": "SDCRV",
        "protocol": "stake-dao",
        "chain": "Ethereum",
        "apy": 17.51,
        "apy_base": 0,
        "apy_reward": 17.51,
        "apy_mean_30d": 16.61,
        "tvl_usd": 26093458,
        "risk_grade": "B",
        "risk_score": 71,
        "prediction": "Down",
        "stablecoin": false,
        "il_risk": "no",
        "exposure": "single"
      }
    ],
    "total_matching": 146,
    "total_scanned": 16642,
    "filters_applied": {
      "chain": "Ethereum",
      "min_tvl": 10000000,
      "min_apy": 3,
      "max_risk": "B",
      "limit": 5
    }
  },
  "confidence": 0.92,
  "data_freshness": "2026-04-12T02:31:10.638795+00:00",
  "tool": "discover_yields",
  "tier": "pro",
  "powered_by": "profitspot.live"
}
```

</details>

**What you get:** 146 Ethereum pools matched from 16,642 scanned. Each pool comes risk-scored (A–F), with 30-day mean APY and APY prediction direction. Sorted by APY descending.

---

### 2. Risk Score — Deep breakdown for a Uniswap V3 pool

```
risk_score(pool_id="fc9f488e-8183-416f-a61e-4e5c571d4395")
```

<details>
<summary><strong>Full JSON Response</strong> (click to expand)</summary>

```json
{
  "data": {
    "type": "pool",
    "pool_id": "fc9f488e-8183-416f-a61e-4e5c571d4395",
    "symbol": "WETH-USDT",
    "protocol": "uniswap-v3",
    "chain": "Ethereum",
    "grade": "B",
    "score": 71,
    "summary": "Moderate Risk — Solid fundamentals, minor concerns. Good for diversified portfolios.",
    "factors": {
      "tvl_stability": {
        "score": 20,
        "max": 25,
        "detail": "$73.9M TVL — strong"
      },
      "apy_sustainability": {
        "score": 10,
        "max": 20,
        "detail": "31.5% APY — moderate | Volatility: extreme (CV=1.04)"
      },
      "protocol_reputation": {
        "score": 20,
        "max": 20,
        "detail": "uniswap-v3 — Tier 1 Blue Chip (est. 48+ months)"
      },
      "il_exposure": {
        "score": 8,
        "max": 15,
        "detail": "Medium IL — monitor price divergence"
      },
      "pair_stability": {
        "score": 3,
        "max": 10,
        "detail": "Non-stable pair — volatile"
      },
      "security_audit": {
        "score": 10,
        "max": 10,
        "detail": "Blue chip + deep TVL — high confidence"
      }
    }
  },
  "confidence": 0.88,
  "data_freshness": "2026-04-12T02:31:11.516026+00:00",
  "tool": "risk_score",
  "tier": "pro",
  "powered_by": "profitspot.live"
}
```

</details>

**What you get:** A composite **B grade (71/100)** with 6-factor breakdown. This pool scores perfectly on protocol reputation (Uniswap is Tier 1 Blue Chip, 48+ months) and security, but gets dinged on APY volatility (CV=1.04) and non-stablecoin pair risk. An AI agent can read this and explain *exactly why* a pool got its grade.

---

### 3. Impermanent Loss — ETH +50%, USDC −10%

```
calculate_impermanent_loss(token_a_price_change=50, token_b_price_change=-10, investment_amount=10000)
```

<details>
<summary><strong>Full JSON Response</strong> (click to expand)</summary>

```json
{
  "data": {
    "token_a_change_pct": 50.0,
    "token_b_change_pct": -10.0,
    "investment_amount": 10000.0,
    "il_percent": 3.1754,
    "il_usd": 381.05,
    "value_if_held": 12000.0,
    "value_in_lp": 11618.95,
    "net_with_fees": {
      "5%": {
        "fees_earned": 500.0,
        "net_gain_usd": 2118.95,
        "net_roi_pct": 21.19
      },
      "10%": {
        "fees_earned": 1000.0,
        "net_gain_usd": 2618.95,
        "net_roi_pct": 26.19
      },
      "20%": {
        "fees_earned": 2000.0,
        "net_gain_usd": 3618.95,
        "net_roi_pct": 36.19
      },
      "50%": {
        "fees_earned": 5000.0,
        "net_gain_usd": 6618.95,
        "net_roi_pct": 66.19
      }
    },
    "interpretation": "Moderate IL — needs decent APY to compensate."
  },
  "confidence": 0.99,
  "data_freshness": "2026-04-12T02:31:11.517000+00:00",
  "tool": "calculate_impermanent_loss",
  "tier": "pro",
  "powered_by": "profitspot.live"
}
```

</details>

**What you get:** Exact IL of **3.18% ($381)** on a $10K position. Your LP is worth $11,619 vs $12,000 if you just held. But here's the key insight — the `net_with_fees` table shows that even a modest 5% fee APY makes you net **+$2,119 (+21.2% ROI)**. The tool gives your AI agent the full picture to make an informed recommendation.

---

## 📖 Tool Reference

All 7 tools available through the MCP protocol:

### `discover_yields` 🟢 Free

> Find top yield opportunities across 86 chains. Filter, risk-score, and rank.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chain` | `string \| null` | `null` | Filter by chain name (e.g., `"Ethereum"`, `"Arbitrum"`) |
| `min_tvl` | `float` | `1000000` | Minimum TVL in USD |
| `min_apy` | `float` | `0` | Minimum APY percentage |
| `max_risk` | `string` | `"F"` | Maximum risk grade: `A`, `B`, `C`, `D`, or `F` *(Pro only)* |
| `limit` | `int` | `20` | Max results to return (Free: 10, Pro: 50) |

---

### `analyze_pool` 🔒 Pro

> Deep-dive analysis of a single pool: APY trends, risk breakdown, IL scenarios, projected returns.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pool_id` | `string` | *required* | Pool UUID from `discover_yields` results |

**Returns:** Historical APY (7d/30d/90d averages), trend direction, volatility stdev, full risk grade breakdown, IL estimate for 3 divergence scenarios, and projected returns for $1K/$10K/$100K at 30/90/365 days.

---

### `calculate_impermanent_loss` 🟢 Always Free

> Pure math — exact IL for any 50/50 LP pair. No API call needed.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `token_a_price_change` | `float` | *required* | % price change for token A (e.g., `50` for +50%) |
| `token_b_price_change` | `float` | *required* | % price change for token B (e.g., `-20` for −20%) |
| `investment_amount` | `float` | `10000` | Initial investment in USD |

**Returns:** IL in USD and %, value-if-held vs value-in-LP, net gain/loss at 5%/10%/20%/50% fee APY levels, and a human-readable interpretation.

---

### `simulate_profit` 🔒 Pro

> Monte Carlo profit projection using Ornstein-Uhlenbeck APY model. 1,000 simulations.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pool_id` | `string` | *required* | Pool UUID from `discover_yields` results |
| `investment` | `float` | `10000` | Investment amount in USD |
| `days` | `int` | `365` | Projection horizon (1–730 days) |
| `compound` | `bool` | `true` | Whether to compound returns daily |

**Returns:** Bearish/Base/Optimistic scenarios with dollar amounts, full percentile distribution (P5–P95), probability of profit, risk factors, and model parameters.

---

### `risk_score` 🔒 Pro

> A–F risk grade for any pool or entire protocol. 6-factor weighted breakdown.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pool_id` | `string \| null` | `null` | Score a specific pool |
| `protocol` | `string \| null` | `null` | Score an entire protocol (e.g., `"aave-v3"`) |

At least one parameter required. For protocols, scores the top 10 pools by TVL and returns an aggregate grade.

**6 Factors:** TVL Stability (25pts), APY Sustainability + Volatility (20pts), Protocol Reputation + Age (20pts), IL Exposure (15pts), Pair Stability (10pts), Security/Audit Proxy (10pts).

---

### `track_whales` 🔒 Pro

> Detect large capital movements — smart money entering or exiting pools.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chain` | `string \| null` | `null` | Filter by chain |
| `min_tvl_change` | `float` | `500000` | Minimum TVL change to flag (USD) |
| `timeframe` | `string` | `"24h"` | Detection window |

**Returns:** List of pools with large TVL changes, direction (inflow/outflow), dollar amount, percentage change, and whether this correlates with APY changes. First call establishes a baseline; subsequent calls detect actual movements.

---

### `defi_overview` 🟢 Free (basic) / Pro (full)

> Big-picture DeFi dashboard across all chains.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chain` | `string \| null` | `null` | Filter to a specific chain |

**Free:** Total TVL, top 10 chains, top 10 protocols, pool counts, average APY.
**Pro:** + Average yields by risk grade, stablecoin market cap, hot opportunities (new pools with rising APY + good risk grade).

---

## 💰 Pricing

<table>
<tr>
<td align="center" width="33%">

### 🆓 Free
**$0/mo**

3 tools, 50 calls/day

No API key needed

</td>
<td align="center" width="33%">

### ⚡ Pro
**$29/mo**

All 7 tools, 1K calls/day

[**→ Get Pro**](https://buy.stripe.com/3cIaEZ0Gf1DrgQodvh4wM00)

</td>
<td align="center" width="33%">

### 🏢 Enterprise
**$99/mo**

All 7 tools, 10K calls/day

[**→ Get Enterprise**](https://buy.stripe.com/7sY28t9cL81P8jS1Mz4wM01)

</td>
</tr>
</table>

|  | Free | Pro ($29/mo) | Enterprise ($99/mo) |
|:---|:---:|:---:|:---:|
| `discover_yields` | ✅ 10 results | ✅ 50 results + risk filter | ✅ 50 results + risk filter |
| `defi_overview` | ✅ Basic | ✅ Full + hot opportunities | ✅ Full + hot opportunities |
| `calculate_impermanent_loss` | ✅ | ✅ | ✅ |
| `analyze_pool` | ❌ | ✅ | ✅ |
| `simulate_profit` | ❌ | ✅ | ✅ |
| `risk_score` | ❌ | ✅ | ✅ |
| `track_whales` | ❌ | ✅ | ✅ |
| **Daily rate limit** | 50 | 1,000 | 10,000 |
| **Support** | Community | Email | Priority |

```bash
# Unlock Pro / Enterprise
export PROFITSPOT_API_KEY=ps_live_xxxxxxxxxxxxxxxx
```

<p align="center">
  <a href="https://buy.stripe.com/3cIaEZ0Gf1DrgQodvh4wM00"><strong>🚀 Get Pro — $29/mo</strong></a>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="https://buy.stripe.com/7sY28t9cL81P8jS1Mz4wM01"><strong>🏢 Get Enterprise — $99/mo</strong></a>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="https://profitspot.live/pricing"><strong>Compare Plans</strong></a>
</p>

---

## 🏠 Self-Hosting

### Option 1: uvx (recommended)

```bash
uvx profitspot-mcp
```

Zero install, runs directly. Requires [uv](https://docs.astral.sh/uv/).

### Option 2: pip + run

```bash
pip install profitspot-mcp
profitspot-mcp                          # stdio (for MCP clients)
python -m profitspot_mcp                # HTTP/SSE on :8080
```

### Option 3: Docker

```bash
docker build -t profitspot-mcp .
docker run -p 8080:8080 -e PROFITSPOT_API_KEY=your-key profitspot-mcp
```

### Option 4: From source

```bash
git clone https://github.com/profitspot/profitspot-mcp.git
cd profitspot-mcp
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Development with inspector UI
fastmcp dev run_server.py

# Production
fastmcp run run_server.py --transport sse --port 8080
```

---

## 🧠 Under the Hood

### Risk Grading — 6-Factor Composite Score

Every pool is scored on 100 points across 6 weighted factors:

| Factor | Weight | What It Measures |
|--------|:------:|------------------|
| TVL Stability | 25 pts | Liquidity depth, rug risk. $100M+ = full marks. |
| APY Sustainability | 20 pts | Yield level (is it realistic?) + volatility (stdev from historical data). |
| Protocol Reputation | 20 pts | Tier 1/2 classification (Aave, Uniswap, Curve = Tier 1) + estimated age. |
| IL Exposure | 15 pts | Single-asset, stablecoin pair, or volatile LP? |
| Pair Stability | 10 pts | Stablecoin pool detection for minimal price risk. |
| Security/Audit Proxy | 10 pts | Protocol trust signal derived from tier + TVL depth. |

**Grades:** A (85–100) · B (70–84) · C (55–69) · D (40–54) · F (0–39)

### Monte Carlo Engine — Not Just `APY × Days`

The `simulate_profit` tool runs **1,000 simulations** using:

- **Ornstein-Uhlenbeck process** — APY reverts toward a long-term mean (high APY pools decay faster)
- **Geometric Brownian Motion** — Simulates impermanent loss from price divergence
- **Pool failure events** — Probability of pool death based on TVL + APY level
- **APY crash events** — Random regime changes where APY drops 60–95%

Returns real dollar amounts across bearish/base/optimistic scenarios.

### Data Source

100% powered by [**DeFiLlama**](https://defillama.com/) APIs — free, no key, no rate limits. Covers 86+ chains, 6,500+ pools, all major protocols.

---

## 📄 License

[AGPL-3.0](LICENSE) — Free to use, modify, and distribute. Network use (running as a service) requires sharing your modifications under the same license.

---

<p align="center">
  <strong>Built by <a href="https://profitspot.live">ProfitSpot</a></strong><br/>
  <sub>The Bloomberg Terminal for DeFi — now available to every AI agent.</sub>
</p>
