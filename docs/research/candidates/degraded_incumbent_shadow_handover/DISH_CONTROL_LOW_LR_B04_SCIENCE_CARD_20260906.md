Claim: On the corrected ordinary renewal boundary of the A03 ground-terminal host, from matched initialization and identical sixteen-update exposure on one new paired seed, the inherited CONTROL learner with a tenfold smaller constant AdamW learning rate (3e-5) may serve more complete-episode native service than the same learner at 3e-4, and may or may not retain the service of its own zero-update initialization.
Binding MARL structure: other-agent partial observability and state ownership during handover; physical vehicles, current owner/standby roles and active/shadow recurrent copies remain distinct.

# DISH control low-learning-rate B04 — science card

Date 2026-09-06; object `DISH-CONTROL-LOW-LR-B04`; **B / EXPLORE**. Selected by the complete
post-witness Convergence response (`pro_packets/20260906_post_witness_convergence/archive/RESPONSE.md`
at commit `27730bf75`, **PRO_FINAL**, intake `DISH_POST_WITNESS_CONVERGENCE_INTAKE_20260906.md`).
The Claude research hub (Root and DM) freezes this card under the owner's standing unattended
delegation, after a read-only code map of the r06 optimizer construction and restore path (§2
records what it found and the objective fixes the plumbing). No empirical outcome has been
observed. The joint forecast-package branch stays ended; this object neither reopens it nor
changes any interface, objective or normalization rule. B04 is a new object with its own card,
predictions and acceptance; seeds 73 and 61, their checkpoints and rows are not its inputs.

## 1. Question and ceiling

On the corrected boundary and the A03 host, does the inherited CONTROL learner at the same
sixteen-update exposure with a constant AdamW learning rate of 3e-5 instead of 3e-4 raise final
whole-episode native service, and is any improvement only a smaller loss against CONTROL, or also
a retention or gain relative to this seed's own zero-update initialization?

Ceiling: an exploratory performance signal on **one paired training replicate** (seed 89) and four
development conditions. The witness fact that motivates it (the seed-73 final CONTROL serves
245.75 fewer mean ticks than its own zero-update view) is a motivation, **not a diagnosis of an
over-large learning rate**; this object is a performance hypothesis, not a localized repair. It
establishes no cause of the historical loss, no general stability claim, no generic relay or
legal-handover competence, no SHADOW-COPY value, no calibration, no variable-N claim, and no
statement that normalization, parameter movement or PPO is the source of any loss. AdamW's
learning rate also scales its decoupled weight decay, so the object measures the total effect of
the learning-rate hyperparameter; it promises neither a tenfold smaller displacement nor a pure
actor-step effect. B03's −272, its hard events, CONTROL's one training legal transfer, the finite
gradient extremes, the staged curves and the witness's eight differences stand as narrowed; B02,
B01, A01–A05 stand; R02 stays closed. No outcome automatically authorizes another learning
rate, a frozen normalization, reopening the package branch or a Portfolio change.

## 2. Host, arms, treatment and control

Both arms use **GROUND-TERMINAL-LINEAR-CLEARANCE-A03** exactly as B03 card §2, on the corrected
ordinary renewal boundary (`observation["renew"]` is the current-countdown permission; raw flag
`renew_completed`; commit `3f4d447f6`, validated by A01/A02). Both arms are the **inherited B03
CONTROL learner**: `STRUCTURED` algorithm/RNG role, `forecast_package=False`, raw service logits
to the native probability input, mean-only coordinate MSE, BCE-with-logits service objective, PPO,
link and missingness auxiliaries, mask laws, recurrent replay, clipping, and Welford normalization
updated by the original rule in both arms (no freezing, no borrowing, no refit). No NLL, no
sigmoid, no epoch reduction.

Output arm names `CONTROL` and `LOW_LR`. The only differential treatment:

- `CONTROL`: the inherited AdamW with its constant learning rate **3e-4**;
- `LOW_LR`: the same AdamW with the learning rate **3e-5 on every original parameter group**,
  constant over all sixteen updates and all 512 optimizer steps.

All other optimizer coefficients (betas, eps, weight-decay coefficient), gradient clipping, loss
weights, sampling, PPO/replay laws, label and mask laws, termination rules, threshold, action
space, actor information, reward, ABI and ordinary ownership transitions are unchanged and
identical between arms. No compensation of other coefficients for the changed learning rate.
Certificate checks stay nondifferentiable; privileged next-state and passive-clone labels stay
training labels.

**What the code map established (engineering fact, binds the objective).** The r06 production
modules construct AdamW with a literal `lr=3e-4` at three sites: the master-addressed initializer
payload (`production_recurrent_trainer.py:221-223`) and the training engine's construction and
restore paths (`production_training_engine.py:239-241`, `527-529`); the B02/B03 study literal
`configuration()["learning_rate"] = 3e-4` records, but does not set, the rate. The optimizer
that actually steps is a local of the engine's update function, rebuilt at every one of the
sixteen updates with `lr=3e-4` and then **overwritten by `optimizer.load_state_dict` from the
previous checkpoint's optimizer state** (`production_training_engine.py:527-536`; the persistent
trainer always passes its current checkpoint bytes, `production_training.py:71-81`); the two
parameter groups (matrix weights with weight decay 1e-4; biases, `log_std` and the `flex_*`
layers with 0.0) are built identically at both sites, and `checkpoint["optimizer"]` is written
right after the step (`:640`). No live optimizer object is reachable from a study. The thin B04
entry therefore realizes `LOW_LR` without editing r06 by **rewriting `lr` in every parameter
group of the initializer payload's saved optimizer state before training** (the only site that
seeds the chain), and by **recording the rate read back from every parameter group of the
trainer's checkpoint after every update** in the published curves; the focused check pins that
the recorded rate equals the arm's rate at all sixteen updates for both arms and that the
engine's construct-then-restore path carries it across chained updates rather than returning to
3e-4. The exact
mechanism is fixed in `DISH_CONTROL_LOW_LR_B04_CM_OBJECTIVE_20260906.md`; a dependency that
prevents the comparison from running with this meaning is returned as that specific gap, not
patched around and not reconstructed from history.

## 3. Seed, initialization, pairing and exposure

One fresh paired seed **89**. Its 256-bit master is SHA256 of the ASCII string
`DISH-CONTROL-LOW-LR-B04/seed/89`, hex
`665c8d879ef9d289d4ad6d4d3bf051643d9f17bb05c97521566dc48a77071c9d`. This binding is prospective
and lives in B04's own namespace; it is a new stream, generated by no consultation; seeds 73 and 61
are not reused.

Both arms start from the same master-addressed `STRUCTURED` initial parameters at block 0
(`build_master_addressed_initial_state(master, block=0, arm="STRUCTURED")`), the same three empty
Welford states (count 0) and the same semantic-address exogenous law; the arm name selects no RNG
substream. Optimizer, recurrent, native and normalization states evolve independently per arm;
nothing is copied between arms; realized eligible-label counts may differ and are not forced
equal. The initial state may be generated once and saved under the run root so the zero-update
reference and both arms consume the same bytes (a plain file, no resume, registry or identity
guard); the initializer call count, constructed objects and the parameter L2 norm are recorded.

Each arm trains **16 complete updates**, **32 lanes × 128 ticks per update**, 4 epochs × 8
minibatches: **65,536 ordinary training transitions and 512 optimizer steps per arm** (131,072 and
1,024 in total). Update-16 checkpoint only; no earlier or best checkpoint, no within-pair search.
Record actual ordinary transitions, completed updates, optimizer steps, per-update service and
learning curves, per-update loss and gradient statistics with their scope and finiteness,
`next_mask` and service-label eligible counts, **the learning rate read back from each parameter
group at each update**, initial and final model norm and parameter displacement. Nominal counts
never replace observations. The inherited 32-lane training distribution is kept; the four
evaluation conditions are not made the training distribution.

## 4. Zero-update reference, evaluation and primary measurement

**Zero-update reference (inside the object, ancillary).** The seed-89 initialization, evaluated
once per condition with the inherited raw CONTROL interface (`forecast_package=False`,
count-0 Welford, fresh recurrent state per row), gives four rows `J_0,r`. It is a normal
zero-update policy with motion and protocol outputs, not held-only. No `LOW_LR` initial view is
needed (the learning rate is not an interface at inference). It is not a prerequisite A and not
an admission condition: no skipping training, seed change, condition change or arm stop follows
from these rows. Seed 73's 706.25 is a historical reference only and enters no seed-89 arithmetic.

**Evaluation.** For each final checkpoint and for the reference, the four combinations of
`TARGET_VISUAL_MASK` and `TERRAIN_RELAY_MASK` with `K8` and `K4_TO_K12` at speed 4, slot 0,
block 0, with the four complete resets **derived for seed 89 by the inherited coordinate law**
(`_reset_row`) and **recorded verbatim in the publication**; they are not seed 73's phases
4/2/1/1. Each row's reset is shared between the two arms and the reference; fresh native and
recurrent state per row; no state borrowed across rows or arms. Deterministic policy evaluation;
fixed 1,200-tick range with native terminal semantics (stop stepping at a terminal, count zero
service for the unexecuted remainder, report completed ticks, terminal cause and events); no
early stop at first-valid; all four rows enter the primary. At most 4,800 evaluation ticks per
arm and 4,800 for the reference.

**Primary.** `J_a,16,r` is the fixed-range sum of native service indicators of arm `a` on row
`r`:

`Delta_LR = (1/4) Σ_r (J_LOW_LR,16,r − J_CONTROL,16,r)`.

Ancillary absolute readings: `D_CONTROL,new = (1/4) Σ_r (J_CONTROL,16,r − J_0,r)` and
`D_LOW_LR,new = (1/4) Σ_r (J_LOW_LR,16,r − J_0,r)`. Publish the reference mean, both final means,
all twelve row values and all per-row differences in one table whose `source` column separates
`new:zero_update:raw`, `new:CONTROL:update16` and `new:LOW_LR:update16`; nothing from the seed-73
tables is joined into it. Companions per row: energy, the seven hard-event classes
(`invalid_commit`, `token_gap`, `dual_owner`, `dual_payload`, `buffer_clear`,
`command_slew_breach`, `separation_breach`), completed and unexecuted ticks, termination reason,
ordinary legal transfers with service before and at-or-after the transfer (a time decomposition
only). Training events and transfers are listed separately from evaluation. Lower training loss
or lower energy never counts as service gain; temporal post-transfer service is not service
carried by the promoted owner.

## 5. Interpretation and predictions on record

Useful-effect scale **+24 mean service ticks** (0.02 of the range) for `Delta_LR`; ±24 for the
two before/after descriptions. It is a descriptive scale for this card, not a per-row tolerance,
not a launch gate, not a repository-wide threshold. No significance test, no per-row or per-seed
sign requirement, no per-row bootstrap as a seed interval (four rows are four conditions, not
four seeds). Reading table (from the response):

| Pattern | Reading |
| --- | --- |
| `Delta_LR ≥ +24` without an adverse companion trade-off | an incremental low-learning-rate signal on this training instance and four conditions; one or two later independent seeds of the same comparison may be considered from the full record (not pre-bought) |
| relative signal and `D_LOW_LR,new ≤ −24` | only a smaller loss against CONTROL, not recovery of the initialization; the reference's advantage is listed alongside |
| relative signal and `D_LOW_LR,new` inside ±24, or ≥ +24 | "near its initial performance", or "also a positive before/after change"; neither equivalence nor general stability nor cause |
| `Delta_LR` inside ±24, or mixed row signs | no useful learning-rate advantage established at this exposure; keep every row and the condition differences; no automatic further reduction, longer training, better checkpoint or seed-adding; no equivalence |
| `LOW_LR` with a clear service loss, more hard events, or an adverse energy/service trade-off | the adverse fact prevails over any proxy; this `LOW_LR` configuration is not extended (one seed closes only this trial, not all CONTROL learning laws or source mechanisms) |
| no evaluation legal transfer | the CONTROL comparison stands as incumbent-only; the source question stays unestimated |
| an input, training chain or primary measurement incomplete | keep trustworthy rows and counts; no complete paired conclusion; name the damaged dependency; no fabricated rows; B03 not quarantined |

If the new CONTROL arm does not fall below its initialization, the shared before/after loss
seen on seed 73 simply did not repeat on this instance by the same description; the paired
result stays readable and the witness is not overturned.

Predictions:

- **DM (hub), prospective.** `D_CONTROL,new ≤ −24` (the seed-73 pattern of a CONTROL final
  below its zero-update raw view repeats on seed 89, moderate confidence), and `Delta_LR` inside
  ±24 or mixed across rows (row 4 of the table), because a tenfold smaller step over 512
  optimizer steps from the same initialization leaves the controller nearer its start but the
  witness showed the initial raw view itself already serving well, so the two arms' finals are
  predicted to straddle rather than separate cleanly; low confidence. Competing prediction:
  `Delta_LR ≥ +24` with `D_LOW_LR,new` inside ±24 (row 3): the smaller step preserves most of
  the initialization's service while CONTROL again drops.
- **Node (Pro), prospective:** none stated numerically; every row of the table is a serious
  outcome and no outcome is treated as expected.
- **Owner:** not taken (unattended).

## 6. Whole cost, route and stop

Work: one initializer call; one raw-interface initial view × 4 rows (≤ 4,800 native ticks,
zero backward, optimizer and label calls); two learner runs (65,536 ordinary transitions, 512
optimizer steps, full recurrent replay and backward each); final evaluation 2 arms × 4 rows ×
≤ 1,200 ticks (≤ 9,600); twelve evaluation episodes and at most 14,400 evaluation ticks in
total; update-16 checkpoints only. Native training work law per arm `2N + 2E + H`, `0 ≤ H ≤ 20E`,
at most 1,572,864 native training step calls; `E` changes with the new seed and rate (B03's
18,775 and 7,972 are not reused); `H` unmeasured if no direct reading exists, no ABI extension.
No best checkpoint, learning-rate grid, old seeds, old final controllers or calibration
experiment.

**Cap: complete charge ≤ 1,800 s per arm and ≤ 3,600 s for both arms**, a new limit not
inherited from B02/B03/witness balances. The item's charge includes the shared initialization,
the four-row reference, the one focused check, actually paid build or cache load, and the
shared reduction and publication; there is no extra 120 s and no "plus build". Shared work `S`
(focused check, initialization, reference rows, shared publication) is charged once and
allocated `S/2` to each arm in advance; each arm's complete wall plus its share stays within
1,800 s and the total including `S` within 3,600 s; publication is left room inside the cap;
splitting into segments does not reset it. Study elapsed, summed invocation wall and CPU are
kept separate; no new resource evaluation, CPU cap or profiler. B03's 196.83 / 185.55 s
prepublication arm walls, 4.94 s shared check and 412.16 s chain, and the witness's 16.23 s, are
references for work types only, not projections (a tenfold learning-rate cut is not a tenfold
time cut); the DM's earlier ~410 s figure is not adopted. The CM lists the cost range from the
chosen path and existing timings, and returns a specific range problem if the complete plan
exceeds the cap rather than dropping labels, training or raising the limit.

Execution: remote-first on `wsl_4070` per `.codex/hmasd-compute.toml` from exact committed and
pushed source in a detached `agent-task` worktree at the launch sha; single Torch thread, FP32
learner, float64 native; a fresh physical and effective memory admission ≥ 4 GiB joined by `&&`
immediately before each result-bearing invocation; full wall and scoped peak RSS reported; 2,000 /
600-line budgets; no A05 exception, scheduler, registry, validator, extra guard, worker pool or
cross-platform bit contract. Agent editing, Git, queue delay and SSH latency are not experimental
compute.

Stop after both arms' sixteen updates, the twelve rows or their legal terminations, and
publication; or at budget exhaustion, an actual non-finite training state, or a failure
threatening the primary measurement, keeping actual exposure. No efficacy early stop, ad-hoc
early checkpoint, outcome-driven seed or row replacement, automatic continuation, resume, cap
enlargement or scientific retry; pre-launch failures keep their records, spend and zero exposure.
A damaged arm keeps the other arm and every trustworthy part without a fabricated paired
difference.

## 7. Acceptance (bounded) and engineering handoff

Prove that the stated inputs and the ordinary path ran, reusing B03's accepted primary reduction,
the corrected-boundary coverage of A01/A02 and the witness's initializer and reset coverage:

- **Learning rate in effect.** The selected rate acts on all original optimizer parameter groups
  at every update, in both arms; a checkpoint or state restore or a trainer rebuild does not
  reset `LOW_LR` to 3e-4. Pinned by the per-update read-back in the curves (all sixteen entries,
  every group, equal to the arm's rate) and by one targeted focused check that rewrites the
  initializer payload for each arm, chains two synthetic engine updates
  (`run_full_4096_dry_update` with its built-in fixture, the second resumed from the first's
  checkpoint) and reads every parameter group's rate from each checkpoint; the published
  `configuration["learning_rate"]` must equal the rate actually baked into the payload (B03's
  literal recorded, but did not set, the rate).
- **No hidden change.** Objectives, masks, clipping, normalization rule, interface and host carry
  no other difference between arms (configuration dictionaries differ only in `learning_rate`
  and `arm`).
- **Same initialization and reference.** Both arms and the reference consume the same initial
  bytes (norm equality; count-0 Welford at load); the four seed-89 resets are recorded and each
  equals the coordinate's recomputed `_reset_row`; the same reset serves all three uses of a row.
- **Primary.** Fixed-range service reduction, terminals, events and the `source` column readable;
  `Delta_LR`, `D_CONTROL,new`, `D_LOW_LR,new` computed by the published arithmetic (checked on
  synthetic rows); the before/after differences' sources stated.

No rerun of seed 61 or 73, A01/A02, the r06 suite, all schedules, historical fragments, all
gradient connections, or B03's eight final rows.

**Engineering-scope §4 declaration: none of its default-prohibited machinery is needed.** CM
owns a thin B04 entry only: `experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04/`,
`scripts/run_dish_control_low_lr_b04.py`, focused tests under
`tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04/`, and the
B04 CM record; it reuses `forecast_package_b02/study.py`, `forecast_package_b03/study.py`,
`init_witness_a01/study.py` and the r06 production sources by import, unchanged. Objective:
`DISH_CONTROL_LOW_LR_B04_CM_OBJECTIVE_20260906.md`. Implementation by Grok Build under the
CLAUDE.md Grok Build route with hub review; `hmasd-reviewer` if a shared surface changes. Output
root `temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b04_20260906/{shared,control,low_lr}`
with adjacent admission receipts; preserve compact curves, the final checkpoints, the saved
initial state, configuration, per-row native outcomes and recorded resets, event and owner
summaries, actual exposure and wall/RSS/CPU witnesses. CM freezes argv/cwd/node/launch sha
before launch; the operator launches; DM interprets; Root integrates.

The complete Pro decision selects this comparison, not source acceptance; the four §11.4
conditions remain the only launch gate. No additional Pro round, owner vote or exact main-commit
identity is a prerequisite.

## 8. Records

Card (this file); CM objective `DISH_CONTROL_LOW_LR_B04_CM_OBJECTIVE_20260906.md`; CM record
`DISH_CONTROL_LOW_LR_B04_CM_RECORD_20260906.md`; launch and result under
`docs/research/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04_20260906/`;
result intake `DISH_CONTROL_LOW_LR_B04_RESULT_INTAKE_20260906.md`, then the same Convergence node.

scope: none
