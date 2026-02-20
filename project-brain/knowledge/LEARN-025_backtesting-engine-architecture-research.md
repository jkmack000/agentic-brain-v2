# LEARN-025: Backtesting Engine Architecture Research
<!-- type: LEARN -->
<!-- created: 2026-02-17 -->
<!-- tags: backtesting, architecture, event-driven, vectorized, data-pipeline, strategy-abstraction, optimization, overfitting, prover -->
<!-- links: SPEC-001, SPEC-000 -->

## Purpose

Research synthesis on production backtesting engine architectures. Focused on design decisions relevant to Prover — a multi-brain AI system where agents generate, modify, and evaluate trading strategies programmatically. Sourced from framework documentation (QuantConnect LEAN, Backtrader, Zipline, VectorBT, Freqtrade, NautilusTrader), blog posts, and research papers.

---

## 1. Core Architecture Patterns

### Event-Driven Backtesting

**How it works:** Simulates a live environment by processing discrete market events (ticks, bar closes, order fills) in a sequential event loop. Each event triggers callbacks in the strategy.

**Components:**
- **Event queue** — FIFO queue of market data events, signal events, order events, fill events
- **Data handler** — Reads historical data, emits market events one at a time
- **Strategy** — Receives market events, generates signal events
- **Portfolio** — Receives signals, manages position sizing, generates order events
- **Execution handler** — Receives orders, simulates fills with slippage/commission models, emits fill events
- **Event loop** — Orchestrates the cycle: data → strategy → portfolio → execution → repeat

**Pros:**
- High-fidelity simulation of live trading (tick-level, partial fills, dynamic risk)
- Same code runs backtest and live — no rewrite needed
- Models realistic order types, slippage, bid-ask spreads
- Prevents most forms of look-ahead bias by design (strategy only sees past data)

**Cons:**
- Slower (sequential iteration through every bar/tick)
- More complex to build and debug
- Harder to parallelize across parameter combinations

**Frameworks:** QuantConnect LEAN, Backtrader, Zipline, NautilusTrader, Freqtrade

### Vectorized Backtesting

**How it works:** Applies trading logic to entire arrays of historical data at once using NumPy/Pandas operations. Signals computed across all time steps simultaneously.

**Components:**
- **Data matrix** — Full OHLCV history loaded into DataFrame/array
- **Signal generator** — Vectorized indicator computation + boolean signal arrays
- **Position array** — Signal → position mapping (long=1, short=-1, flat=0)
- **Return computation** — Element-wise multiplication of position array * asset returns
- **Performance metrics** — Computed from return series

**Pros:**
- 100-1000x faster than event-driven (NumPy/Pandas vectorization)
- Simple to implement and reason about
- Ideal for screening thousands of parameter combinations
- Easy to parallelize

**Cons:**
- Assumes fills at next bar open/close — ignores intra-bar dynamics
- No realistic slippage, partial fills, or order book simulation
- Prone to look-ahead bias if not carefully implemented
- Cannot model stateful logic (dynamic position sizing, conditional exits)
- Code cannot run live without rewrite

**Frameworks:** VectorBT, custom Pandas/NumPy scripts

### Hybrid Approach (Industry Best Practice)

Production quant teams use a **two-phase pipeline:**

1. **Phase 1 — Vectorized screening:** Rapidly test thousands of parameter combinations, strategy variants, and universe filters. Eliminate non-performers. Cost: minutes.
2. **Phase 2 — Event-driven validation:** Migrate top candidates into event-driven framework for realistic simulation with slippage, transaction costs, and market impact. Cost: hours.

**Prover implication:** The Coder brain should generate strategies in both forms. Vectorized for the optimization agent's parameter sweeps, event-driven for final validation before any live deployment recommendation.

### Streaming vs Batch

| Aspect | Streaming | Batch |
|--------|-----------|-------|
| **Data delivery** | One bar/tick at a time | Full history at once |
| **Live parity** | High (same as live feed) | Low (requires rewrite) |
| **Speed** | Slower | Faster |
| **Memory** | Low (one bar in memory) | High (full history in memory) |
| **Frameworks** | LEAN, NautilusTrader | VectorBT, custom |

QuantConnect LEAN explicitly models backtesting as "streaming in fast-forward mode" — data points delivered one after another, identical to live trading but accelerated.

### NautilusTrader: Performance-First Event-Driven

NautilusTrader achieves event-driven correctness with near-vectorized speed:
- **Rust core** with Python bindings (Cython + PyO3)
- **Single-threaded deterministic** event loop (actor model pattern)
- **Nanosecond resolution** timestamps
- **5M+ rows/second** throughput
- Background services (network I/O, persistence, adapters) on separate threads/async runtimes
- Results communicated back to kernel via MessageBus
- Data stored/queried via Apache DataFusion + Parquet

**Prover implication:** If Prover needs high-frequency strategy testing, NautilusTrader's architecture is the gold standard. For daily/4h timeframes (likely Donchian use case), Backtrader or Freqtrade is sufficient.

---

## 2. Data Pipeline Design

### Raw → Strategy-Ready Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│ Raw Market   │────▸│ Clean &      │────▸│ Resample &    │────▸│ Strategy-    │
│ Data         │     │ Normalize    │     │ Align         │     │ Ready Data   │
└─────────────┘     └──────────────┘     └───────────────┘     └──────────────┘
  Sources:            Steps:               Steps:               Output:
  - Exchange APIs     - Fill gaps           - OHLCV resampling   - Aligned OHLCV
  - CSV/Parquet       - Handle splits       - Multi-TF align     - Indicator values
  - Data vendors      - Timezone normalize  - Forward-fill        - Signal arrays
  - Tick databases    - Deduplicate         - Calendar filter
                      - Validate OHLCV
```

### OHLCV Handling Patterns

**Storage format consensus:** Parquet is the industry standard for backtesting data.
- Columnar format enables reading only needed columns
- Compression (snappy/zstd) reduces disk 5-10x vs CSV
- Vectorized read operations
- Schema enforcement prevents data corruption
- Partitioning by symbol/date for large datasets

**Freqtrade** supports JSON, JSON gzip, Feather, and Parquet — recommends Parquet for production.

**Zipline** uses bcolz (columnar binary) + SQLite metadata for its data bundles. Bundles handle split/dividend adjustments on-the-fly.

**NautilusTrader** uses Apache DataFusion for Parquet catalog queries with nanosecond timestamps.

**Data organization patterns:**
- Daily data: single file per asset or single file for all assets
- Intraday data: partitioned by month (e.g., `BTC_1min_202602.parquet`)
- Tick data: partitioned by day

### Timeframe Alignment & Resampling

**Core rule:** Always store data in the *lowest* needed timeframe, resample up.

**Multi-timeframe pattern (all frameworks):**
1. Load base timeframe (e.g., 1-minute bars)
2. Resample to higher timeframes (5m, 1h, 4h, 1D) using OHLCV aggregation rules:
   - Open: first value in window
   - High: max of highs
   - Low: min of lows
   - Close: last value in window
   - Volume: sum
3. Align timestamps — higher timeframe values must only be available *after* the period closes (prevents look-ahead)
4. Forward-fill higher timeframe values into lower timeframe index

**Backtrader** provides built-in `resampledata()` and `replaydata()` methods. Data feeds auto-register as array members on the strategy.

**Freqtrade** uses "informative pairs" — strategy declares which additional timeframes/pairs it needs, framework handles fetching and alignment. Key config: `startup_candle_count` ensures enough history for indicators to stabilize.

**Prover implication:** The data pipeline should be a shared service, not embedded in each strategy. Donchian brain specifies what data it needs (symbol, timeframes), Coder brain implements the pipeline, Orchestrator ensures alignment.

---

## 3. Strategy Abstraction Patterns

### Pattern A: Class Inheritance (Backtrader, Zipline)

```python
class MyStrategy(bt.Strategy):
    params = (('period', 20),)     # Declarative parameter definition

    def __init__(self):
        self.sma = bt.indicators.SMA(period=self.params.period)

    def next(self):                  # Called every bar
        if self.data.close[0] > self.sma[0]:
            self.buy()
```

**Backtrader architecture:**
- `Cerebro` engine — central orchestrator: gathers Data Feeds, Strategies, Observers, Analyzers, Writers
- `Strategy` base class — users subclass and implement `__init__()` + `next()`
- `params` tuple — declarative parameter definition with inheritance support
- Data feeds auto-injected as `self.datas[0]`, `self.data1`, etc.
- Cerebro instantiates Strategy class (not instances) — enables re-instantiation for optimization
- Indicators auto-compute and align with data feeds

**Zipline architecture:**
- `TradingAlgorithm` class — operates on `BarData` aligned with trading calendar
- `Pipeline` API — declarative factor/filter computation across asset universe
- Data bundles (bcolz + SQLite) with on-the-fly corporate action adjustments
- `DataFrameLoader` and `BlazeLoader` for custom data sources

### Pattern B: DataFrame Method Override (Freqtrade)

```python
class MyStrategy(IStrategy):
    def populate_indicators(self, dataframe, metadata):
        dataframe['sma'] = ta.SMA(dataframe, timeperiod=20)
        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        dataframe.loc[dataframe['close'] > dataframe['sma'], 'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe, metadata):
        # exit conditions
        return dataframe
```

**Freqtrade architecture:**
- `IStrategy` abstract class — three mandatory methods (indicators, entry, exit)
- DataFrame-centric — all logic expressed as column operations
- `FreqtradeBot` orchestrator — runs main loop (~5s in live): refresh → analyze → manage → execute
- Exchange abstraction via CCXT library (100+ exchanges)
- **FreqAI** ML pipeline: `IFreqaiModel` (training/prediction), `FreqaiDataKitchen` (per-pair preprocessing, not persistent), `FreqaiDataDrawer` (persistent model/metadata storage)

### Pattern C: Vectorized Composition (VectorBT)

```python
entries = vbt.MA.run(price, window=20).ma_crossed_above(price)
exits = vbt.MA.run(price, window=50).ma_crossed_below(price)
portfolio = vbt.Portfolio.from_signals(price, entries, exits)
```

**VectorBT architecture:**
- Strategy as composition of vectorized signal generators
- Multi-dimensional array packing — multiple strategy instances in a single array
- Sequential row-by-row execution internally, but accepts array inputs and broadcasts
- Stateless order execution (no order queue — command in, result out)
- ~1000x faster than Backtrader for equivalent strategies

### Pattern D: Modular Handler Interfaces (LEAN)

```
Algorithm Engine
├── IDataFeed         → disk (backtest) or stream (live)
├── ITransactionHandler → fill model (backtest) or brokerage (live)
├── IResultHandler    → file/console (backtest) or web/API (live)
├── IRealtimeHandler  → simulated clock (backtest) or real clock (live)
└── ISetupHandler     → cash, portfolio, data initialization
```

**LEAN architecture:**
- Handler interfaces swap implementations between backtest and live
- `config.json` environments control which implementations load
- AlgorithmManager handles core execution loop with time slices
- C# core, Python/C# algorithm support
- 180+ contributors, powers 300+ hedge funds

### Prover Implications for Strategy Abstraction

For AI-generated strategies, **Pattern B (Freqtrade/DataFrame)** is most suitable because:
1. **LLM-friendly** — strategies are expressed as DataFrame column operations, which LLMs generate well
2. **Declarative parameters** — easy for optimization agents to enumerate and modify
3. **Separation of concerns** — indicators, entries, and exits are separate methods (AI can modify one without breaking others)
4. **Rich ecosystem** — Freqtrade has built-in optimization, live trading, and ML integration

For validation, **Pattern D (LEAN)** is ideal — handler interfaces make it easy to swap between backtest and live without changing strategy code.

---

## 4. Result Storage

### What Gets Stored

| Category | Contents | Format | Retention |
|----------|----------|--------|-----------|
| **Trade log** | Entry/exit timestamps, prices, size, PnL, fees, slippage | Parquet or JSON | Permanent |
| **Equity curve** | Timestamp + portfolio value series | Parquet or CSV | Permanent |
| **Performance metrics** | Sharpe, Sortino, max drawdown, win rate, profit factor, Calmar | JSON or YAML | Permanent |
| **Parameter set** | Strategy params that produced these results | JSON | Permanent |
| **Order book** | All orders (filled, cancelled, rejected) | Parquet | Optional |
| **Position history** | Position sizes over time | Parquet | Optional |
| **Indicator values** | Computed indicator series | Parquet | Ephemeral (recomputable) |

### Key Performance Metrics to Store

- **Sharpe ratio** — risk-adjusted return (annualized, using risk-free rate)
- **Sortino ratio** — like Sharpe but only penalizes downside volatility
- **Maximum drawdown** — largest peak-to-trough decline
- **Calmar ratio** — annualized return / max drawdown
- **Win rate** — percentage of profitable trades
- **Profit factor** — gross profit / gross loss
- **Average trade duration** — time in position
- **Number of trades** — total and per direction
- **Expectancy** — average PnL per trade
- **Recovery factor** — net profit / max drawdown
- **Annual return** — CAGR
- **Volatility** — annualized standard deviation of returns

### Storage Patterns

**Parquet for data, JSON for metadata** is the consensus pattern:
- Trade logs and equity curves: Parquet (columnar, compressed, fast queries)
- Strategy parameters and metrics summaries: JSON (human-readable, version-controllable)
- Optimization results: Parquet (thousands of parameter combinations with metrics)

**Directory structure pattern:**
```
results/
├── strategies/
│   └── donchian_breakout/
│       ├── params.json              # Strategy parameters
│       ├── trades.parquet           # Trade log
│       ├── equity.parquet           # Equity curve
│       ├── metrics.json             # Performance summary
│       └── optimization/
│           ├── grid_search_001.parquet  # All param combos + metrics
│           └── best_params.json
```

**Prover implication:** Raw results stay in the file system (too large for brain). The Donchian brain stores *insights* as LEARN files (e.g., "Donchian 20/10 outperforms 55/20 on BTC daily in trending markets"). This aligns with SPEC-001's decision.

---

## 5. Parameter Optimization

### Method Comparison

| Method | Strategy | Speed | Overfitting Risk | When to Use |
|--------|----------|-------|-------------------|-------------|
| **Grid search** | Exhaustive enumeration of all combinations | Slow (exponential) | High (tests everything) | Small param spaces (<1000 combos) |
| **Random search** | Random sampling from param distributions | Medium | Medium | Large spaces, early exploration |
| **Bayesian (Optuna/TPE)** | Probabilistic model guides search toward promising regions | Fast (sample-efficient) | Medium | Production optimization, >3 params |
| **Walk-forward** | Train on window, test on next, slide | Slow | Lower | Time series validation |
| **CPCV** | Combinatorial paths through purged k-folds | Slow | Lowest | Final validation, publication-grade |

### Bayesian Optimization with Optuna

**How it works:**
1. Define objective function (e.g., maximize Sharpe ratio from backtest)
2. Optuna suggests parameter combinations using Tree Parzen Estimator (TPE)
3. Run backtest with suggested params, return metric
4. TPE updates probability model, suggests next combination focusing on promising regions
5. Repeat until budget exhausted or convergence

**Why Optuna for trading:**
- Handles high-dimensional, mixed-type parameter spaces
- Pruning: kills unpromising trials early (saves compute)
- Native integration with Freqtrade
- Supports constraints (e.g., "only consider if max drawdown < 20%")
- Visualization of parameter importance and optimization history

**Freqtrade integration:** Uses Optuna as its hyperparameter optimization backend. Defines parameter spaces declaratively in the strategy class, runs backtests as Optuna trials.

### Walk-Forward Analysis

**How it works:**
1. Split data into segments: [Train1][Test1][Train2][Test2]...
2. Optimize on Train1, validate on Test1
3. Slide window forward: optimize on Train2, validate on Test2
4. Aggregate out-of-sample results

**Limitations:**
- Tests only a single path through time
- Susceptible to regime-specific overfitting
- Particular sequence of data points can bias results
- Higher temporal variability and weaker stationarity than CPCV

### Combinatorial Purged Cross-Validation (CPCV)

Developed by Marcos Lopez de Prado (2017). The most robust validation method for trading strategies.

**How it works:**
1. Split data into N groups (k-fold style)
2. Generate all combinatorial train/test splits
3. **Purge:** Remove observations near train/test boundaries to prevent information leakage
4. **Embargo:** Add buffer period after purge to account for serial correlation
5. Run strategy on each split
6. Aggregate performance across hundreds of historical paths

**Why CPCV is superior:**
- Produces a *distribution* of performance metrics (not a single number)
- Tests against many different market regime sequences
- Systematic elimination of look-ahead bias via purging + embargoing
- Computes Probability of Backtest Overfitting (PBO) — the probability that the best in-sample parameter set is mediocre out-of-sample
- Lower PBO and superior Deflated Sharpe Ratio vs walk-forward

**Prover implication:** The optimization pipeline should be:
1. **Vectorized grid/random** — screen universe rapidly (Coder brain generates)
2. **Bayesian (Optuna)** — refine top candidates efficiently
3. **CPCV validation** — final robustness check before any deployment recommendation
4. Results summarized as LEARN files in Donchian brain with PBO and Deflated Sharpe

---

## 6. Framework Reference

### Quick Comparison

| Framework | Language | Architecture | Speed | Live Trading | Best For |
|-----------|----------|-------------|-------|-------------|----------|
| **Backtrader** | Python | Event-driven, class inheritance | Moderate | Via brokers | Learning, prototyping, daily strategies |
| **Zipline** | Python | Event-driven, Pipeline API | Moderate | Limited | Research, factor models, equities |
| **VectorBT** | Python | Vectorized composition | Very fast | No | Parameter screening, rapid iteration |
| **QuantConnect LEAN** | C#/Python | Event-driven, handler interfaces | Fast | Yes (multi-broker) | Production, institutional, multi-asset |
| **Freqtrade** | Python | Event-driven, DataFrame methods | Moderate | Yes (crypto) | Crypto bots, ML integration, optimization |
| **NautilusTrader** | Rust/Python | Event-driven, actor model | Very fast | Yes | HFT, institutional, performance-critical |

### Framework Architecture Details

**Backtrader:**
- Cerebro engine (central orchestrator) + Strategy (user logic) + Data Feeds + Observers + Analyzers
- Strategy receives data feeds as auto-injected array members
- Cerebro takes Strategy *class* (not instance) — re-instantiates for optimization
- Built-in resampling and multi-timeframe support
- Mature but unmaintained (last commit 2020)

**Zipline:**
- TradingAlgorithm + Pipeline API + Data Bundles (bcolz + SQLite)
- Pipeline enables declarative cross-sectional factor computation
- Trading calendars handle exchange hours globally
- Originally built by Quantopian (defunct), maintained as zipline-reloaded

**VectorBT:**
- Strategy = composition of vectorized signal generators
- Multi-dimensional array broadcasting for parameter sweeps
- ~1000x faster than Backtrader
- Stateless execution (no order queue, no partial fills)
- PRO version adds more features

**QuantConnect LEAN:**
- Handler-based modularity (IDataFeed, ITransactionHandler, IResultHandler, IRealtimeHandler, ISetupHandler)
- Same code runs backtest and live via handler swap
- AlgorithmManager processes time slices
- 180+ contributors, 300+ hedge funds
- Config-driven environment switching (config.json)

**Freqtrade:**
- FreqtradeBot main loop (~5s cycle): refresh → analyze → manage → execute
- IStrategy: populate_indicators(), populate_entry_trend(), populate_exit_trend()
- Exchange abstraction via CCXT (100+ exchanges)
- FreqAI: IFreqaiModel + FreqaiDataKitchen + FreqaiDataDrawer for ML pipeline
- Built-in Optuna hyperparameter optimization
- Active development (2025.8 latest release)

**NautilusTrader:**
- Rust core + Python bindings (Cython/PyO3)
- Single-threaded deterministic event loop (actor model)
- Background services on separate threads (network, persistence, adapters)
- MessageBus for cross-component communication
- 5M+ rows/second, nanosecond resolution
- ParquetDataCatalog + DataFusion for data management

---

## 7. Common Pitfalls

### Look-Ahead Bias
**What:** Using information that wasn't available at the time a trading decision should have been made.
**Examples:** Using today's close to decide today's trade; computing indicators using future data points; using post-split prices without adjustment.
**Prevention:**
- Event-driven architecture prevents most cases by design
- Use point-in-time data (as-reported, not restated)
- Multi-timeframe alignment: higher TF values only available after period closes
- Apply indicators based only on past data
- Account for realistic execution delays

### Survivorship Bias
**What:** Testing only on assets that still exist, ignoring delisted/failed ones.
**Impact:** Overstates annual returns by 1-4%, skews Sharpe ratios and drawdowns.
**Prevention:**
- Use point-in-time databases that include delisted assets
- Use survivorship-bias-free data providers
- When building asset universes, reconstruct them as they existed at each historical date

### Overfitting (The Most Dangerous Pitfall)
**What:** Finding patterns that worked historically but fail forward. Modern computing can test billions of parameter combinations, virtually guaranteeing spurious patterns.
**Warning signs:**
- Sharpe ratio > 3 (extremely rare in practice)
- Strategy only works on one specific time window
- Too many parameters relative to number of trades
- Finding a pattern first, inventing the economic rationale second (storytelling bias)
**Prevention:**
- Test across multiple market regimes (trending, ranging, volatile, calm)
- Use CPCV for robust out-of-sample validation
- Limit parameter count (rules of thumb: >20 trades per parameter)
- Require economic rationale *before* parameter search
- Compute Probability of Backtest Overfitting (PBO)
- Use Deflated Sharpe Ratio to account for multiple testing

### Transaction Cost Modeling
**What:** Ignoring or underestimating real trading costs.
**Impact:** A backtest showing 15% annual returns can collapse to near-zero after realistic costs. High-turnover strategies especially affected — costs can slash returns by >50%.
**Components to model:**
- Commission/fees (fixed + percentage)
- Slippage (market impact, especially for large orders)
- Bid-ask spread (half-spread per side minimum)
- Funding costs (overnight, margin interest)
- Exchange-specific fee tiers

### Data Snooping Bias
**What:** Repeatedly testing hypotheses on the same dataset until something "works."
**Prevention:**
- Hold out a true out-of-sample set that is never touched during development
- Track how many strategy variants were tested (deflate Sharpe accordingly)
- CPCV provides PBO metric specifically for this

### Prover-Specific Pitfalls

Because AI agents will generate and test strategies programmatically:

1. **Infinite search risk** — AI can generate unlimited strategy variants. Without cost caps and stopping criteria, optimization can run forever.
   **Mitigation:** Budget caps per optimization run (`max_budget_usd` in Agent SDK), maximum trials per parameter sweep, convergence detection.

2. **Narrative fabrication** — LLMs are excellent at inventing plausible-sounding economic rationales for random patterns.
   **Mitigation:** Require the economic thesis *before* the parameter search. Donchian brain provides the thesis, Coder brain implements, not the other way around.

3. **Compounding bias across agents** — Each agent introduces small biases. Orchestrator → Donchian → Coder → Optimizer chain can amplify.
   **Mitigation:** CPCV validation as a hard gate. No strategy passes to "recommended" without PBO < 0.5.

4. **Hyperparameter meta-overfitting** — Optimizing the optimizer (which validation method, which metric, which data split) is itself a form of overfitting.
   **Mitigation:** Fix validation methodology in a RULE file. Do not let AI agents modify the validation pipeline.

---

## 8. Architecture Recommendations for Prover

### Recommended Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Phase 1 engine** | VectorBT | 1000x faster screening, parameter sweeps |
| **Phase 2 engine** | Freqtrade | DataFrame strategies (LLM-friendly), built-in Optuna, live trading path, active maintenance |
| **Data format** | Parquet | Industry standard, compressed, fast |
| **Optimization** | Optuna (Bayesian) | Sample-efficient, pruning, Freqtrade native |
| **Validation** | CPCV | Most robust, provides PBO metric |
| **Results storage** | Parquet (data) + JSON (metadata) | Queryable + human-readable |
| **Result insights** | LEARN files in Donchian brain | Per SPEC-001 decision |

### Data Flow Through Prover Brains

```
User → Orchestrator: "Backtest Donchian breakout on BTC daily"
                │
                ├──▸ Donchian Brain: Returns strategy spec (indicator params,
                │    entry/exit rules, economic thesis)
                │
                ├──▸ Coder Brain: Implements strategy as Freqtrade IStrategy
                │    class + VectorBT screening script
                │
                ├──▸ [Execute] Phase 1: VectorBT parameter sweep
                │    → Top 10 param sets by Sharpe
                │
                ├──▸ [Execute] Phase 2: Freqtrade backtest on top 10
                │    → Realistic fills, slippage, fees
                │
                ├──▸ [Execute] Phase 3: CPCV validation on top 3
                │    → PBO, Deflated Sharpe, equity curve distribution
                │
                └──▸ Orchestrator: Synthesize results → LEARN deposit
                     → Return to user with recommendation
```

### Open Design Questions for Prover

1. **Who runs the backtests?** Subagents can't execute long-running processes well. Need a execution service outside Claude Code (Agent SDK `query()` triggering a backtest process?).
2. **Data freshness** — How does OHLCV data get refreshed? Scheduled pipeline or on-demand fetch?
3. **Strategy versioning** — How to track which strategy version produced which results? Git tags? Dedicated VERSION file?
4. **Multi-asset** — Donchian on BTC first, but architecture should support multi-asset from day one.
5. **Timeframe for MVP** — Daily bars are simplest. Sub-hourly introduces alignment complexity.

---

## Sources

- [Interactive Brokers: Vector-Based vs Event-Based Backtesting](https://www.interactivebrokers.com/campus/ibkr-quant-news/a-practical-breakdown-of-vector-based-vs-event-based-backtesting/)
- [QuantConnect LEAN Algorithm Engine](https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/algorithm-engine)
- [QuantConnect LEAN Engine Architecture (DeepWiki)](https://deepwiki.com/QuantConnect/Lean/3-engine-and-execution)
- [VectorBT Documentation](https://vectorbt.dev/)
- [Backtrader Cerebro Documentation](https://www.backtrader.com/docu/cerebro/)
- [Backtrader Strategy Documentation](https://www.backtrader.com/docu/strategy/)
- [Freqtrade Architecture (DeepWiki)](https://deepwiki.com/freqtrade/freqtrade)
- [Freqtrade Strategy Customization](https://www.freqtrade.io/en/stable/strategy-customization/)
- [NautilusTrader Architecture](https://nautilustrader.io/docs/latest/concepts/architecture/)
- [Zipline Documentation](https://zipline.ml4trading.io/)
- [CPCV: Combinatorial Purged Cross-Validation (Medium)](https://medium.com/@alexdemachev/finding-optimal-hyperparameters-for-a-trading-strategy-with-combinatorial-cross-validation-3fd241d613fc)
- [Combinatorial Purged Cross-Validation (QuantBeckman)](https://www.quantbeckman.com/p/with-code-combinatorial-purged-cross)
- [Walk-Forward Optimization (QuantInsti)](https://blog.quantinsti.com/walk-forward-optimization-introduction/)
- [Seven Sins of Quantitative Investing](https://bookdown.org/palomar/portfoliooptimizationbook/8.2-seven-sins.html)
- [Common Pitfalls in Backtesting (Medium)](https://medium.com/funny-ai-quant/ai-algorithmic-trading-common-pitfalls-in-backtesting-a-comprehensive-guide-for-algorithmic-ce97e1b1f7f7)
- [Freqtrade Testing and Optimization (DeepWiki)](https://deepwiki.com/freqtrade/freqtrade/3-testing-and-optimization)
- [Backtrader Data Resampling](https://www.backtrader.com/docu/data-resampling/data-resampling/)
- [Market Data Storage for Backtesting (Medium)](https://medium.com/data-science/how-to-store-financial-market-data-for-backtesting-84b95fc016fc)

## Known Issues
- NautilusTrader analysis based on docs only — not hands-on tested
- VectorBT PRO (paid) features not evaluated — free version may lack some capabilities
- CPCV implementation details not fully explored — need to assess Python libraries (e.g., `mlfinlab`)
- Freqtrade is crypto-focused — equity/futures support may need different framework
- No hands-on benchmarking of framework speeds — numbers are from respective project claims
