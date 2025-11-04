# 3-Tier Model Distribution Strategy

## Overview

The 12 specialized subagents now use a 3-tier model distribution system to optimize for speed, quality, and resource usage. Each tier uses a different Z.ai model running locally via Ollama.

## Model Tiers

### TIER 1: KIMI (Fastest) ⚡
**Model**: `kimi-k2:1t-cloud`
**Use case**: Simple data fetching, quick lookups
**Characteristics**: Fastest response time, minimal reasoning needed

**Agents using KIMI (1 total):**
- **price-quote-fetcher** - Just fetches current stock prices from API

**Why KIMI?** Price lookups are simple HTTP requests with minimal processing. Speed is more important than deep analysis.

---

### TIER 2: MINIMAX (Medium Speed) 🎯
**Model**: `minimax-m2:cloud`
**Use case**: Analysis, research, aggregation
**Characteristics**: Good balance of speed and analytical capability

**Agents using MINIMAX (7 total):**
1. **fundamentals-analyst** - Analyzes financial statements and ratios
2. **technical-analyst** - Interprets chart patterns and trends
3. **company-intelligence** - Researches business profiles and competitors
4. **market-sentiment-analyst** - Aggregates analyst ratings and insider trades
5. **news-research-analyst** - Summarizes news, SEC filings, ESG data
6. **cashflow-analyzer** - Analyzes income and expense patterns
7. **debt-manager** - Calculates debt payoff strategies

**Why MINIMAX?** These tasks require understanding and synthesis but not complex mathematical reasoning. MINIMAX provides good analytical quality at medium speed.

---

### TIER 3: GLM-4.6 (Most Powerful) 🚀
**Model**: `glm-4.6:cloud`
**Use case**: Complex calculations, optimization, simulations
**Characteristics**: Strongest reasoning, best for math-heavy tasks

**Agents using GLM-4.6 (4 total):**
1. **portfolio-analyzer** - Portfolio optimization, Sharpe ratio, rebalancing calculations
2. **goal-planner** - Monte Carlo simulations (1000+ iterations), retirement projections
3. **tax-optimizer** - Tax optimization strategies, loss harvesting analysis
4. **risk-assessor** - Value at Risk (VaR), stress testing, volatility calculations

**Why GLM-4.6?** These agents perform complex mathematical operations, probabilistic simulations, and multi-variable optimization that benefit from the most powerful model.

---

## Performance Impact

### Speed Comparison
- **KIMI**: ~1-2 seconds per query
- **MINIMAX**: ~3-5 seconds per analysis
- **GLM-4.6**: ~5-10 seconds for complex calculations

### Example: "Analyze AAPL comprehensively"
**With 3-tier distribution:**
```
price-quote-fetcher (KIMI):         2 seconds  ⚡
fundamentals-analyst (MINIMAX):     4 seconds  🎯
technical-analyst (MINIMAX):        4 seconds  🎯
company-intelligence (MINIMAX):     4 seconds  🎯
market-sentiment-analyst (MINIMAX): 4 seconds  🎯
news-research-analyst (MINIMAX):    4 seconds  🎯
────────────────────────────────────────────────
Total (parallel execution):         4 seconds  ✅
(All MINIMAX agents run concurrently, KIMI finishes instantly)
```

**If all used GLM-4.6:**
```
All 6 agents @ 8 seconds each:     ~8 seconds  ⏱️
(Slower, but unnecessary for simple tasks)
```

**Savings**: ~50% faster for multi-agent queries!

---

## Configuration

### File: `src/subagents_config.py`

```python
# Z.ai API configuration (local Ollama)
OLLAMA_API_KEY = "6ddb812c07914107ba7c0e504fdcf9f1.gkld5OFtD8NRbDZvMiYtHG6P"
OLLAMA_BASE_URL = "http://localhost:11434/v1/"

# Create model instances
KIMI_MODEL = ChatOpenAI(
    temperature=0,
    model="kimi-k2:1t-cloud",
    openai_api_key=OLLAMA_API_KEY,
    openai_api_base=OLLAMA_BASE_URL,
    max_retries=10,
    timeout=300,
)

MINIMAX_MODEL = ChatOpenAI(
    temperature=0,
    model="minimax-m2:cloud",
    openai_api_key=OLLAMA_API_KEY,
    openai_api_base=OLLAMA_BASE_URL,
    max_retries=10,
    timeout=300,
)

GLM_MODEL = ChatOpenAI(
    temperature=0,
    model="glm-4.6:cloud",
    openai_api_key=OLLAMA_API_KEY,
    openai_api_base=OLLAMA_BASE_URL,
    max_retries=10,
    timeout=300,
)

# Distribute models to subagents
SUBAGENT_MODELS = {
    "price-quote-fetcher": KIMI_MODEL,
    "fundamentals-analyst": MINIMAX_MODEL,
    # ... etc
}
```

---

## Rate Limiting

All models include:
- **Max retries**: 10 attempts with exponential backoff
- **Timeout**: 300 seconds (5 minutes) for complex tasks
- **Connection limits**: Max 10 concurrent connections

See `RATE_LIMITING.md` for details on retry logic.

---

## Testing

Test the model distribution:

```bash
python3 -c "
from src.subagents_config import SUBAGENT_MODELS
for agent, model in SUBAGENT_MODELS.items():
    print(f'{agent}: {model.model_name}')
"
```

Expected output:
```
price-quote-fetcher: kimi-k2:1t-cloud
fundamentals-analyst: minimax-m2:cloud
technical-analyst: minimax-m2:cloud
company-intelligence: minimax-m2:cloud
market-sentiment-analyst: minimax-m2:cloud
news-research-analyst: minimax-m2:cloud
cashflow-analyzer: minimax-m2:cloud
debt-manager: minimax-m2:cloud
portfolio-analyzer: glm-4.6:cloud
goal-planner: glm-4.6:cloud
tax-optimizer: glm-4.6:cloud
risk-assessor: glm-4.6:cloud
```

---

## Changing Models

To change a model for a specific agent, edit `SUBAGENT_MODELS` in `src/subagents_config.py`:

```python
# Example: Use GLM-4.6 for fundamentals instead of MINIMAX
SUBAGENT_MODELS = {
    "fundamentals-analyst": GLM_MODEL,  # Changed from MINIMAX_MODEL
    # ... rest unchanged
}
```

---

## Benefits Summary

✅ **Faster simple queries** - Price lookups use fastest model
✅ **Balanced medium tasks** - Most agents use optimal speed/quality model
✅ **Accurate complex work** - Math-heavy tasks use most powerful model
✅ **Resource efficient** - Don't waste powerful model on simple tasks
✅ **Parallel friendly** - Fast agents don't slow down the group
✅ **Cost optimized** - Use expensive compute only when needed

---

## Future Improvements

Potential enhancements:
1. **Dynamic model selection** - Agent chooses model based on query complexity
2. **Model caching** - Cache results from expensive GLM-4.6 calculations
3. **Adaptive thresholds** - Automatically adjust tier based on performance metrics
4. **Custom models** - Allow users to specify their own model preferences
