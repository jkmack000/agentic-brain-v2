# LEARN-022 — DSPy Optimizers (Teleprompters): Automatic Prompt & Weight Tuning
<!-- type: LEARN -->
<!-- tags: dspy, optimizers, teleprompters, prompt-tuning, bootstrapping, compilation, bayesian-optimization, few-shot, fine-tuning, MIPROv2 -->
<!-- created: 2026-02-15 -->
<!-- links: LEARN-020, SPEC-000, LEARN-002 -->

## What This Covers
Complete technical reference for DSPy's optimizer system — the mechanism that automatically tunes LLM prompts (instructions + few-shot demos) and model weights to maximize a user-defined metric. Formerly called "teleprompters" (renamed in DSPy 2.0, mid-2024). This is the novel DSPy subsystem not yet captured in any brain file; LEARN-020 covers the mem0-dspy project that uses DSPy but not the optimizer internals.

## Core Concept

A DSPy optimizer takes three inputs and returns an optimized program:
1. **Student program** — a `dspy.Module` subclass (single predictor or multi-module pipeline)
2. **Metric** — a function `metric(example, prediction, trace=None) → float|bool`
3. **Training set** — a list of `dspy.Example` objects (as few as 10)

```python
optimizer = dspy.MIPROv2(metric=my_metric, auto="light")
optimized = optimizer.compile(student_program, trainset=train_examples)
```

The `.compile()` call returns an **optimized copy** of the program with tuned parameters. The original is never mutated. The optimized program has `._compiled = True`.

## What Compilation Produces

Three types of artifacts, depending on the optimizer:
- **Demonstrations** — few-shot examples baked into each Predict module's prompt (`predictor.demos`)
- **Instructions** — rewritten natural-language task descriptions (`predictor.signature.instructions`)
- **Weights** — fine-tuned model weights (stored by the LM provider, not locally)

Save/load format is JSON:
```python
optimized.save("path.json")     # Saves demos + instructions per predictor
loaded = MyProgram()
loaded.load("path.json")        # Loads into an instance of the same class
```
The save file does NOT store the Python class definition, LM config, retriever indexes, or fine-tuned weights.

## Full Optimizer Catalog (15 Optimizers)

### A. Few-Shot Learning (5)
| Optimizer | What It Does | Min Data | Cost |
|-----------|-------------|----------|------|
| `LabeledFewShot` | Random sample of k labeled examples as demos | k examples | Minimal |
| `BootstrapFewShot` | Teacher generates demos, metric filters them | ~10 | Low |
| `BootstrapFewShotWithRandomSearch` | Multiple bootstrap runs, best-of-N selection | ~50 | Medium |
| `BootstrapFewShotWithOptuna` | Optuna-driven demo selection | ~50 | Medium |
| `KNNFewShot` | Dynamic per-input demo selection via nearest neighbors | ~100 | Low (at inference) |

### B. Instruction Optimization (5)
| Optimizer | What It Does | Min Data | Cost |
|-----------|-------------|----------|------|
| `COPRO` | Coordinate ascent over LLM-proposed instructions | ~50 | Medium-High |
| `MIPROv2` | Bayesian optimization over instructions + demos jointly | ~200 | High |
| `SIMBA` | Stochastic mini-batch introspective rules + demos | ~32 | Medium |
| `GEPA` | Evolutionary reflective prompt optimization | ~50 | High |
| `InferRules` | Induces natural-language rules from examples | ~50 | Medium |

### C. Weight Optimization (2)
| Optimizer | What It Does | Min Data | Cost |
|-----------|-------------|----------|------|
| `BootstrapFinetune` | Distills prompt-based program into fine-tuned weights | ~200 | Very High |
| `GRPO` | Group Relative Policy Optimization (RL-style) | ~100 | Very High |

### D. Combined & Utility (3)
| Optimizer | What It Does |
|-----------|-------------|
| `BetterTogether` | Chains prompt optimization + weight optimization in configurable strategy |
| `Ensemble` | Combines multiple programs into a single ensemble |
| `AvatarOptimizer` | Feedback-based instruction optimization for agent/tool-use programs |

## Key Optimizer Deep Dives

### BootstrapFewShot — The Foundation
The bootstrapping mechanism that underlies most other optimizers:

```python
optimizer = dspy.BootstrapFewShot(
    metric=my_metric,
    metric_threshold=None,          # Min score to accept a bootstrapped demo
    teacher_settings=dict(lm=gpt4), # Use a stronger teacher model
    max_bootstrapped_demos=4,       # Max teacher-generated demos
    max_labeled_demos=16,           # Max raw labeled examples from trainset
    max_rounds=1,                   # Retry rounds per example
)
compiled = optimizer.compile(student, trainset=train)
```

**Mechanical steps:**
1. Deep-copies teacher (defaults to student). If uncompiled, pre-compiles with `LabeledFewShot(k=max_labeled_demos)`.
2. For each training example (up to `max_rounds` attempts):
   - Runs teacher with `dspy.context(trace=[])` to capture execution trace
   - For rounds > 0: fresh LM copy at `temperature=1.0` with unique `rollout_id` to bypass cache
   - Temporarily removes current example from teacher's demos (prevents data leakage)
   - Evaluates metric; if passes, extracts each Predict module's I/O as `dspy.Example(augmented=True)`
   - Stores in `self.name2traces` keyed by predictor name
3. For each student predictor: assigns up to `max_bootstrapped_demos` augmented traces, fills remaining with raw labeled examples.

### MIPROv2 — The Recommended General-Purpose Optimizer
Jointly optimizes instructions AND few-shot examples using Bayesian Optimization (Optuna TPE sampler). This is the officially recommended optimizer for most tasks.

```python
optimizer = dspy.MIPROv2(
    metric=my_metric,
    auto="light",                   # "light" | "medium" | "heavy" | None
    # auto presets:
    #   light:  n=6,  val_size=100
    #   medium: n=12, val_size=300
    #   heavy:  n=18, val_size=1000
    prompt_model=None,              # Model for generating instruction candidates
    task_model=None,                # Model for running the actual program
    num_candidates=None,            # Required if auto=None
    max_bootstrapped_demos=4,
    max_labeled_demos=4,
    init_temperature=1.0,
    seed=9,
)
compiled = optimizer.compile(
    student, trainset=train,
    num_trials=None,                # Auto-calculated from candidates
    minibatch=True,
    minibatch_size=35,
    minibatch_full_eval_steps=5,
    program_aware_proposer=True,    # Sees program structure
    data_aware_proposer=True,       # Sees data properties
    tip_aware_proposer=True,        # Random prompting tips
    fewshot_aware_proposer=True,    # Sees bootstrapped examples
)
```

**Three-stage process:**
1. **Bootstrap few-shot examples** — Creates `num_fewshot_candidates` demo sets (teacher-generated, metric-filtered)
2. **Propose instruction candidates** — `GroundedProposer` generates instruction variants per predictor, informed by program code, dataset, demos, and prompting tips
3. **Bayesian optimization** — Optuna TPE sampler searches the joint space of (instruction variant, demo set) per predictor. Each trial evaluates a minibatch (35 examples). Every 5 trials, full-eval the best combo. Returns highest-scoring program.

`num_trials` auto-calculated as `max(2 * num_vars * log2(num_candidates), 1.5 * num_candidates)`.

**Zero-shot mode** (instruction-only optimization):
```python
compiled = optimizer.compile(program, trainset=trainset,
                             max_bootstrapped_demos=0, max_labeled_demos=0)
```

### SIMBA — Self-Reflective Introspection
Maintains a population of programs, alternates between two strategies per step:
1. **append_a_demo** — adds a successful example as a demonstration
2. **append_a_rule** — LLM introspects on failures and generates a natural-language rule appended to instructions

Uses softmax-weighted selection from top-K programs per mini-batch. 8 steps default. Returns best program with `candidate_programs` and `trial_logs`.

### GEPA — Evolutionary Reflective Optimization
Extended metric protocol: `(gold, pred, trace, pred_name, pred_trace) → {"score": float, "feedback": str}`. Uses Pareto-based candidate selection, program variant merging, and LLM reflection. Requires a strong `reflection_lm`. Supports checkpointing (resume from `log_dir`). Can serve as batch inference-time search.

### InferRules — Rule Induction
Extends BootstrapFewShot: first bootstraps demos, then uses an LLM to extract `num_rules` natural-language rules from examples, appends them to predictor instructions: `"Please adhere to the following rules: {rules}"`. Evaluates `num_candidates` rule sets, returns best.

### BetterTogether — Combined Optimization
Chains prompt and weight optimization via a strategy string:
```python
optimizer = dspy.BetterTogether(metric=my_metric)
compiled = optimizer.compile(student, trainset=train, strategy="p -> w -> p")
# "p" = prompt optimization, "w" = weight optimization
# Any chain supported: "p -> w", "w -> p", "p -> w -> p -> w", etc.
```
Currently restricted to `BootstrapFewShotWithRandomSearch` (prompt) + `BootstrapFinetune` (weight).

## Metrics System

```python
def my_metric(example, prediction, trace=None):
    """
    example:    dspy.Example — gold standard from dataset
    prediction: dspy.Prediction — model output
    trace:      None during evaluation, populated during bootstrapping
    Returns:    float (0.0-1.0) or bool
    """
    answer_correct = example.answer.lower() == prediction.answer.lower()

    # Stricter during optimization, lenient during eval
    if trace is not None:
        return answer_correct and len(prediction.rationale.split()) < 200
    return answer_correct
```

**The `trace` parameter is critical**: when non-None, the metric is being called during bootstrapping. Use this to apply stricter filters during optimization while being lenient during final evaluation.

**Built-in metrics**: `dspy.evaluate.answer_exact_match`, `dspy.evaluate.answer_passage_match`, `dspy.SemanticF1()`.

**LM-as-judge metrics**: Use a DSPy module as a metric function — define a `Judge` signature and call it inside the metric.

**`dspy.Evaluate` utility**:
```python
evaluator = dspy.Evaluate(devset=dev, metric=metric, num_threads=4, display_table=5)
score = evaluator(compiled_program)  # Returns float (percentage passing)
```

## Assertions and Constraints

```python
dspy.Assert(condition, "Error message")   # Hard — retries on failure, discards trace if all retries fail
dspy.Suggest(condition, "Suggestion")     # Soft — logs but doesn't retry or fail
```

- `dspy.Assert` retries up to `max_backtracking_attempts` (2-3), injecting error message as feedback
- During bootstrapping, failed assertions discard the trace (not used as a demo)
- Enable via `program.activate_assertions()` or `assert_transform_module(program, backtrack_handler)`

## Teacher-Student Paradigm

Use a stronger model to bootstrap demos for a weaker model:
```python
dspy.configure(lm=student_lm)  # Student is default
optimizer = dspy.BootstrapFewShot(
    metric=my_metric,
    teacher_settings=dict(lm=teacher_lm)  # Teacher generates demos
)
compiled_student = optimizer.compile(MyProgram(), trainset=train)
# Student runs on gpt-4o-mini with demos generated by gpt-4o
```

## Practical Guidance

### When to Use Which
| Scenario | Optimizer | Min Data |
|----------|-----------|----------|
| Quick start, few examples | `BootstrapFewShot` | ~10 |
| More data, want reliability | `BootstrapFewShotWithRandomSearch` | ~50 |
| Instruction-only (zero-shot) | `MIPROv2` with demos=0 | ~50 |
| General-purpose, best quality | `MIPROv2` (official recommendation) | ~200 |
| Self-reflective improvement | `SIMBA` | ~32 |
| Rule-based improvement | `InferRules` | ~50 |
| Dynamic per-input demos | `KNNFewShot` | ~100 |
| Maximum performance | `BootstrapFinetune` | ~200 |
| RL-style weight training | `GRPO` | ~100 |
| Combined prompt + weight | `BetterTogether` | ~500 |

### Cost Estimates
- `BootstrapFewShot`: ~len(trainset) teacher calls. Cheapest.
- `MIPROv2 light`: ~$2, ~10min for simple tasks
- `MIPROv2 heavy`: most expensive prompt optimization
- Fine-tuning (`BootstrapFinetune`, `GRPO`): additional compute costs for actual training
- `GEPA`: requires strong reflection model on top of task model (~2x per-step cost)

### Common Pitfalls
1. **Metric must return `float` or `bool`** — returning string/None silently breaks optimization
2. **Always include `trace=None` parameter** in metric signature
3. **Overfitting with <20 examples** — bootstrapped demos perfectly solve training but generalize poorly. Use separate val set.
4. **Demo token overflow** — `max_bootstrapped_demos=8` with long CoT can blow context limits
5. **Non-deterministic results** — optimization involves randomness. Use RandomSearch or multiple MIPROv2 trials.
6. **Teacher must match program structure** — same retrievers, same external state
7. **Overly strict `dspy.Assert`** — most traces discarded, too few demos. Check assertion pass rate first.
8. **Changing signatures after compilation** — saved demos no longer align. Re-optimize after changes.
9. **Module naming stability** — `predictor.demos` keyed by Python attribute name. Renaming breaks save/load.

## Brain-Relevant Takeaways

1. **Orthogonal to brain system** — brains store knowledge, DSPy optimizes prompts. But brain content could serve as training data for optimizing brain operations (e.g., optimize `/brain-search` prompts with labeled search examples).
2. **SIMBA's self-reflective rules** are the closest pattern to brain RULE files — LLM introspects on failures and generates explicit rules. Could automate RULE file creation from operational data.
3. **Teacher-student distillation** could optimize brain search: use expensive model to generate high-quality search strategies, distill to Haiku for cheap lookups.
4. **MIPROv2's auto presets (light/medium/heavy)** are a good UX pattern — brain operations could offer similar quick/thorough modes.
5. **Metric-driven optimization parallels brain quality gates** — the metric function pattern maps to our Stop hook quality check and `/brain-deposit` dedup validation.
6. **Compilation artifacts (JSON demos + instructions)** are compatible with brain file format — could store optimized prompts as brain CODE files for reuse across sessions.
7. **InferRules' rule induction** could mine accumulated LOG files for explicit rules to deposit as RULE files.

## Known Issues
- DSPy API evolves rapidly; parameter names and defaults may shift. This analysis is point-in-time Feb 2026.
- SIMBA, GEPA, InferRules, GRPO appear newer (post-May 2025 additions or major rewrites) — less battle-tested.
- `BetterTogether` requires `dspy.settings.experimental = True` and is restricted to specific optimizer combinations.
- GRPO requires `exclude_demos=True` and `multitask=True` (demos and per-predictor training not yet supported).
- GEPA marked as experimental, based on external `gepa` package.
