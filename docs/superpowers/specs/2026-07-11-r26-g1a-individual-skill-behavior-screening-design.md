# R26-G1a Individual-Skill Behavior Screening Design

Date: 2026-07-11

Status: user-approved design; implementation and experiment launch are still
pending.

## 1. Purpose

R26-G1a asks the smallest unresolved question on the traditional HA-CTSE line:

```text
Do naturally assigned individual skills z_i leave a stable, held-out local
behavior signature after controlling for assignment context and recent history?
```

This is a reward-off screening gate. It does not claim causal skill semantics.
A pass authorizes only the later R26-G1b forced-`z_i` intervention. It does not
authorize `q_d`, `q_D`, `q_A`, team-discriminator, or any new intrinsic reward.

The IMOD workspace is a separate research line. This design applies only to the
traditional HA-CTSE R24/R25 continuation in this repository.

## 2. Evidence And Motivation

R24's team-conditioned `q_d` gate failed under the tested policies and current
diagnostic setup. The real classifier did not consistently beat behavior-only
or matched nulls, and the forced audit produced a between/within ratio of
approximately `0.308`, far below the prior `1.2` gate. Those results block
`q_d/q_D` rewards but leave a more basic question open: whether individual
skill labels are behaviorally differentiated at all.

R25 provides mature frozen policies at update 25, update 30, and final for two
conditions:

- `arm0_arch_only`: primary diagnostic substrate;
- `arm2_qA_reward`: contrast condition for assignment legibility versus task
  behavior, not a preferred policy.

## 3. Scope

### In scope

- Load an existing R25 checkpoint without optimizer state.
- Run the frozen policy in evaluation mode while preserving its natural
  stochastic skill assignments and primitive actions.
- Collect fixed post-assignment local behavior windows for each renewing agent.
- Train fresh diagnostic classifiers on detached data only.
- Compare real labels against context/history baselines and matched nulls.
- Produce machine-readable JSON and a compact Markdown gate report.
- Provide a sequential CUDA runner covering the six mature R25 checkpoints.

### Out of scope

- No policy, critic, optimizer, PPO, SMDP, collector, or environment changes.
- No training continuation from the checkpoint.
- No forced skill assignment in G1a.
- No reward injection or reward coefficient.
- No communication-specific fields in classifier inputs.
- No graph, world model, q_D target, or IMOD implementation.
- No scientific pass claim from the arm2 contrast alone.

## 4. Selected Approach

Use an offline natural-policy collector plus a frozen diagnostic analyzer.

Rejected alternatives:

1. Resume checkpoint training and reuse the R24 exporter. This changes the
   policy while collecting evidence and confounds checkpoint semantics with
   additional learning.
2. Run forced-`z_i` intervention first. This is the causal G1b gate and is
   premature until basic observational behavior separation passes.

## 5. Data Collection Contract

### 5.1 Frozen policy

The collector must:

- reconstruct checkpoint structure using the existing checkpoint metadata;
- load model weights with `load_optimizers=False`;
- set all modules to evaluation mode;
- execute under `torch.no_grad()`;
- never call an update, backward, optimizer, or checkpoint-save path;
- reject a non-CUDA experiment request instead of silently falling back to CPU.

CPU remains allowed only for focused unit tests with synthetic fixtures.

### 5.2 Assignment anchor and horizon

A sample begins when an individual agent receives a natural new assignment at
one of its own renewal boundaries. Re-selecting the same label still counts as
a new assignment event because the policy made a fresh decision.

The post window is exactly one global skill interval:

```text
H_screen = skill_interval = 10 primitive steps for the R25 checkpoints.
```

All R25 duration candidates are at least one interval, so this window does not
cross the next legal renewal boundary for the focal assignment. Samples cut
short by episode termination or truncation are discarded. The collector must
not pad incomplete windows.

The pre window is the immediately preceding `H_screen` primitive steps for the
same agent. It is marked invalid when the episode or available history is too
short.

### 5.3 Feature groups

All arrays are detached `float32` or `int64` values.

`post_action` contains generic summaries of the executed primitive-action
sequence. `post_effect` contains generic summaries of the focal agent's local
observation trajectory. The first implementation uses the same summary family
for post and pre windows: first-to-last delta, mean delta, standard deviation,
and span. It does not read task reward, coverage, throughput, QoS, backhaul,
recovery, or topology-specific labels.

`prior_context` is a strong non-outcome baseline containing only information
available at assignment time:

- focal agent identity;
- selected duration index;
- previous focal skill label and prior skill age/phase;
- team code, when present;
- teammate assignment roster with the focal current `z_i` removed;
- assignment-time local/high-level observation;
- detached OPT compact/omega context when present;
- pre-window action/effect summaries and validity bit.

The current focal label `z_i` must not appear directly or through a focal slot
inside the teammate roster. Environment reward and communication diagnostics
must not enter `prior_context`.

### 5.4 Dataset identity and grouping

Each row stores:

```text
label, post_action, post_effect, pre_action, pre_effect, pre_valid,
prior_context, reset_id, reset_seed, episode_id, env_id, agent_id,
duration_idx, segment_length, checkpoint_id, checkpoint_update
```

The collector writes compressed NPZ shards under the assigned run root. It
must never write loose runtime files into the repository root.

The analyzer skill cardinality is the checkpoint's actual `n_skills`, not the
number of agents. The collector manifest records this value from checkpoint
metadata, and the runner must pass the same value to the analyzer and reject a
mismatch. The six registered R25 checkpoints were inspected before Task 2
review and all use `n_skills=4` with `n_agents=6`; using `num_skills=6` would
change normalized entropy and invalidate the scientific gate.

## 6. Held-Out Split And Probe Training

### 6.1 Grouped split

The analyzer uses one deterministic split shared by every model and null:

- 60% train resets;
- 20% validation resets;
- 20% test resets.

Grouping is by `reset_id`; rows from the same reset/episode may not cross split
boundaries. The split seed is pre-registered in the runner. The analyzer must
not retry splits until a favorable result appears. If an active label is absent
from a required split, the checkpoint is reported as `UNDERPOWERED`.

### 6.2 Equal-capacity heads

Three fresh classifiers use the same hidden width, depth, optimizer, learning
rate, batch schedule, and early-stopping rule:

```text
q_behavior(z_i | post_action, post_effect)
q_prior(z_i | prior_context)
q_full(z_i | post_action, post_effect, prior_context)
```

Action and effect use separate encoders before fusion. Inputs and labels are
detached. Early stopping monitors validation cross-entropy with a fixed maximum
of 1000 steps and patience of 20 validation checks. The best validation state
is evaluated once on the test split. Test metrics never affect stopping.

Every variant uses the same device class, split, initialization seeds, model
capacity, and stopping rule.

## 7. Null Controls

The analyzer reports every variant, including failures:

- `real`: unchanged post behavior and labels;
- `shuffled`: global label permutation;
- `fake_marginal`: labels sampled from the empirical marginal;
- `agent_matched`: labels shuffled within focal-agent groups;
- `duration_matched`: labels shuffled within duration groups;
- `agent_duration_matched`: labels shuffled within joint agent-duration groups;
- `pre_only`: replace post behavior with the valid pre window;
- `action_only`: zero the post-effect stream;
- `effect_only`: zero the post-action stream;
- `context_only`: the `q_prior` baseline.

Grouped shuffles must never fall back to a global shuffle when a group has one
row. Singleton groups retain their original label and the unchanged fraction is
reported.

Every label null is constructed only after the reset-grouped split is fixed.
Train, validation, and test labels are transformed independently with
deterministic `(variant, split)` seeds; held-out labels must never determine a
training or validation permutation or fake-marginal distribution.

`acc_behavior(post) - acc_behavior(pre)` is evaluated on identical rows with a
valid pre window. Within each already-fixed reset split, both the post and pre
behavior probes are trained, validated, and tested on the same `pre_valid`
subset. If filtering removes required label support from any split, this
comparison is `UNDERPOWERED`; invalid pre windows must not be replaced with a
one-sided zero feature vector for the gate.

## 8. Metrics And Pre-Registered G1a Gate

Per checkpoint, report:

- label count, normalized label entropy, and maximum label fraction;
- train/validation/test row and reset counts;
- test accuracy, macro-F1, cross-entropy, and majority accuracy;
- `acc_full - acc_prior`;
- `acc_behavior - acc_prior`;
- `acc_behavior(post) - acc_behavior(pre)`;
- per-row `log q_full(z_i) - log q_prior(z_i)` mean and positive fraction;
- real-minus-null differences for every matched null;
- reset-cluster bootstrap 95% confidence intervals for primary differences;
- early-stop step and train-versus-test gaps.

An arm0 checkpoint passes G1a only when all conditions hold:

1. normalized label entropy is at least `0.8`;
2. `acc_full - acc_prior >= 0.05`;
3. `acc_behavior(post) - acc_behavior(pre) >= 0.05`;
4. real beats every label-matched null, and the reset-cluster bootstrap 95%
   lower confidence bound for real versus the strongest matched null is above
   zero;
5. no train/test overfit warning invalidates the read.

The overfit warning is pre-registered as a strict train-minus-test accuracy gap
greater than `0.20` for any fitted probe whose result participates in the gate
or a required matched-null comparison. A gap equal to `0.20` does not trigger
the warning. This threshold is emitted in result metadata and must not be tuned
after observing R26 data.

Validation-only early stopping uses a minimum validation-loss improvement of
`1e-4`; this is a numerical tolerance, not a scientific gate. The tolerance is
also emitted in result metadata.

The arm0 screening family passes only if at least two of update 25, update 30,
and final pass in the same direction. Arm2 is reported as a contrast and cannot
rescue an arm0 failure. Because R25 has one seed, a family pass remains a
screening result and not a publication-level causal claim.

## 9. Decision Tree

### PASS

Implement and pre-register R26-G1b forced-`z_i` intervention with between/within
trajectory separation and horizon persistence. Keep all rewards off.

### FAIL

Conclude that the current low-level actor does not exhibit verified individual
skill modes under the tested mature policies. The next design question becomes
actor-conditioning/discoverer capacity, such as whether the existing skill
embedding is too weak. Do not tune a discriminator or inject reward.

### MIXED

If one checkpoint passes, null ordering is unstable, or confidence intervals
cross zero, classify the family as inconclusive. Inspect sample support,
overfitting, and checkpoint/update sufficiency. Do not change the pass gate or
launch a reward arm.

### UNDERPOWERED OR INVALID

If label support, grouped splitting, checkpoint loading, feature exclusion, or
device consistency fails, repair the instrument and repeat the same
pre-registered analysis. Instrument repair does not change algorithm status.

## 10. File And Interface Boundaries

Create:

- `ha_ctse_process/r26_g1_dataset.py`: immutable dataset schema, validation,
  sharded NPZ I/O, grouped split metadata, and deterministic row sampling.
- `scripts/collect_r26_g1_windows.py`: frozen-checkpoint natural-policy
  collector.
- `scripts/analyze_r26_g1_behavior.py`: equal-capacity probes, early stopping,
  null variants, cluster bootstrap, JSON/Markdown reports.
- `scripts/run_r26_g1_screening_local_cuda.ps1`: dry-run capable sequential
  runner for arm0 and arm2 update25/update30/final checkpoints.
- `tests/r26_g1_dataset_test.py` and `tests/r26_g1_behavior_test.py`.

Do not modify `ha_ctse_process/standalone_agent.py`, the training loop, reward
composition, policy/critic architecture, or checkpoint format for G1a. Generic
window encoding belongs in the new R26 module and may reuse formulas, not R24's
scientific labels or reward path.

Both Python entrypoints must be directly executable by absolute or relative
file path from a run/worktree without requiring callers to set `PYTHONPATH`;
each entrypoint establishes the repository root before importing
`ha_ctse_process`.

## 11. Error Handling And Auditability

- Missing checkpoint or structural mismatch: fail before collection.
- CUDA unavailable for a real run: fail with an explicit message; no CPU
  fallback.
- Incomplete post window: discard and count.
- Missing labels in a split: report `UNDERPOWERED`; do not silently resplit.
- Non-finite feature or loss: fail the checkpoint analysis and preserve the
  offending row/checkpoint identifiers in the report.
- Analyzer failures after an output directory is known write structured JSON
  and Markdown with gate status `INVALID`, error type/message, checkpoint or
  shard identity, and offending row identifiers when available before the CLI
  returns a non-zero status.
- The compact Markdown report includes split identities/counts, entropy and
  majority baselines, primary gate differences and intervals, all matched-null
  differences and intervals, thresholds, and gate reasons; JSON remains the
  complete machine-readable artifact.
- Every runner arm writes `command.txt`, `runner_status.txt`, stdout/stderr,
  dataset shards, analyzer JSON, analyzer Markdown, and a manifest below its
  assigned run directory.

## 12. Verification

Focused tests must prove:

- focal `z_i` is absent from `prior_context` and teammate roster slots;
- reset-grouped splits have no leakage;
- grouped nulls preserve group membership and do not globally fall back;
- pre and post windows remain distinct;
- synthetic behavior-coded labels pass while context-only/noise labels fail;
- validation early stopping never reads test metrics;
- all production inputs are detached and no policy parameter receives a
  gradient;
- a collector smoke loads a checkpoint, produces shards, and leaves the
  checkpoint unchanged;
- dry-run commands cover exactly six checkpoints and contain no reward flags.

Before any experiment launch, `memory/ExpRecord.md` must receive a new R26-G1a
row with measured time cost, CUDA device, exact run root, checkpoint inventory,
and this gate. The launch itself is a separate user decision.
