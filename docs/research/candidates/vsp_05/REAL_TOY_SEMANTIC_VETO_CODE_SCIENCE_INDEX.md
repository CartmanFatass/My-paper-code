# VSP-05 B1 real toy semantic veto: code/science index

This package implements `VSP05-B1-REAL-TOY-SEMANTIC-VETO`, a small exploratory
algorithm experiment for `CAND-VSP-05@adversarial-revision-v7`. It is distinct
from the earlier finite census: the runner advances the real clean-process
dynamic-roster environment, event core and supplied executor, trains a logistic
learner, and evaluates frozen arms on fresh episodes.

## Ownership and dependency direction

- `experiments/candidates/vsp_05/semantic_veto_policy.py` owns the eight-field
  current-time feature, frozen receipt/truth predicates, logistic learner,
  deterministic SHAM permutation and pure veto selection rule.
- `experiments/candidates/vsp_05/real_toy_semantic_veto.py` owns the isolated
  experiment configuration, candidate-local runtime adapter, training and
  evaluation loops, metrics, JSON result schema and CLI.
- `tests/experiments/candidates/vsp_05/test_real_toy_semantic_veto.py` proves
  the feature/action contracts, deterministic SHAM, exact registered budget,
  real runtime calls and reloadable smoke result.

Dependencies point from the isolated candidate into the existing
`CleanProcessDynamicRosterEventEnv`, `VariableRosterEventCore`,
`SuppliedExecutorVectorRuntime` and `SuppliedSkillExecutor`. Production modules
do not import this candidate package, and the stable default execution route is
unchanged.

## Frozen mechanism

The candidate-independent proposed successor is a deterministic current-state
rule. A genuine join starts at skill 2. Thereafter the rule identifies the
coarse target indicated by process position/velocity; if that target is already
incumbent, or no coarse target is present, it proposes the cyclic successor.
The same rule is used in every arm and does not read identity, clock, age,
reward, future state, terminal state, history or RNG.

The semantic gate uses exact symmetric constants fixed before the outcome run:

- directional hard position `|p| >= 1/8`, strict truth `|p| >= 1/4`, with
  skill 0 negative and skill 2 positive;
- hold hard velocity `|v| <= 1/4`, strict truth `|v| <= 1/16` for skill 1.

Only an incumbent with a different proposed successor and a true hard gate can
be handed off. `DET_GATE_ONLY` follows the proposal. The learned arms use a
zero-initialized `Linear(8,1)`, full-batch BCE plus explicit `1e-3` L2, Adam at
`0.05`, and reject at `p_alias >= 0.80`. TARGET uses current receipt labels;
SHAM deterministically permutes the same labels within each training seed.
A support-poor seed remains a valid fixed-budget run: the trainer performs the
registered update count on the L2-only zero-record objective and records zero
support rather than inventing rows or extending the budget.

## Registered execution

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.vsp_05.real_toy_semantic_veto `
  --config registered `
  --code-revision <exact-source-commit> `
  --output <explicit-result.json>
```

The registered budget is exactly 7,680 real training transitions, 23,040 real
evaluation transitions, 30,720 total transitions, 768 optimizer updates, 96
training episodes and 288 evaluated episodes. It uses task seeds
`67057,67058,67059` and fresh evaluation seeds `97057,97058,97059`. There is no
hypothetical rollout, candidate search, recurrence, rescue arm, adaptive tuning
or budget extension.

For proof-sized interface validation, use `--config smoke`. The JSON reports
declared and actual counts, real component call evidence, training diagnostics,
per-seed/per-arm episode rows, arm aggregates and explicit `null` values for
zero-denominator rates. The primary premature-handoff rate is false-strict-
truth adopted successors divided by every incumbent/different-successor/
`G_SEM=1` opportunity; `alias_support` remains a separate diagnostic only.
Handoff delay is the event-rank distance from each lifecycle's first strict-
true hard-positive to adoption of that same proposed successor; unresolved
first truths are reported as censored rather than treated as one-step delays.

## Claim boundary

The artifact is descriptive, fixed-budget B-level toy evidence. Mechanical
completion is not scientific acceptance and does not establish promotion,
retirement, utility, generalization, deployment value, production coverage or
any broader semantic-veto claim. The result must be interpreted only within
the exact registered environment, mechanism, arms, seeds and budget above.

## Registered B1 execution receipt

The one authorized fresh run `vsp05_b1_e50b43e3_r1` used source commit
`e50b43e30b2010c5320f0e23d0f2ba5c28804b1e`. TRAIN, EVALUATE and ANALYZE all
exited zero. The declared and actual counts matched exactly: 7,680 training
transitions, 23,040 evaluation transitions, 30,720 total transitions, 768
optimizer updates, 96 training episodes and 288 evaluated episodes. All seven
real environment/policy/learner/trainer/evaluation/executor/core call flags
were true.

The fixed host instance produced alias-only support: training seeds yielded
9, 6 and 6 alias records and zero strict-truth records; every evaluation arm
had 23 gated alias opportunities and zero strict-truth opportunities. TARGET
and SHAM therefore both vetoed all 23 gated opportunities, while DET adopted
all 23. Their primary premature-handoff rates were respectively `0/23`,
`0/23` and `23/23`; TARGET-minus-SHAM was exactly zero. Miss and event-rank
delay remained undefined because strict-truth support was zero. These are
mechanical observations, not a scientific direction decision.

The tracked public evidence is
[`REAL_TOY_SEMANTIC_VETO_RESULT.json`](REAL_TOY_SEMANTIC_VETO_RESULT.json).
It preserves exact per-training-seed records, per-evaluation-seed/arm
aggregates, total aggregates, configuration, call counts and the source-bound
run locator. The full 288 episode rows remain in the run-owned raw artifact
`logs/vsp05_b1_real_toy_semantic_veto_e50b43e3_r1/raw_result.json`.
