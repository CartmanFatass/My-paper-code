Claim: On B03's four development conditions of the A03 ground-terminal host, each recorded update-16 controller (CONTROL, FORECAST_PACKAGE) serves lower, about the same, or higher than its own-interface zero-update initialization view; the measurement is conditional on these fixed controllers, the recorded exogenous inputs and this panel.
Binding MARL structure: other-agent partial observability and state ownership during handover; physical vehicles, current owner/standby roles and active/shadow recurrent copies remain distinct.

# DISH zero-update controller witness A01 — science card

Date 2026-09-06; object `DISH-INIT-WITNESS-A01`; **A / RECON** (bounded comparison of fixed
controllers against existing records). Selected by the complete post-B03 Convergence response
(`pro_packets/20260906_post_b03_convergence/archive/RESPONSE.md` at commit `f85016d76`,
**PRO_FINAL**, intake `DISH_POST_B03_CONVERGENCE_INTAKE_20260906.md`). The Claude research hub
(Root and DM) freezes this card under the owner's standing unattended delegation, after a
read-only code map of the B03 initializer and evaluation path (§2 records what it found). No
empirical outcome has been observed. The joint forecast-package branch is ended by the same
decision; this object neither reopens it nor trains anything.

## 1. Question and ceiling

With `J_a,0,r` the service of the zero-update initialization in interface view `a` on condition
`r`, and `J_a,16,r` the accepted B03 update-16 row value of arm `a`: is
`D_a = (1/4) Σ_r (J_a,16,r − J_a,0,r)` clearly negative, inside the descriptive band, or clearly
positive, for `a ∈ {CONTROL, FORECAST_PACKAGE}`?

Ceiling: a conditional measurement on two fixed initial views and two recorded final
controllers, the recorded exogenous randomness of seed 73 and the four B03 conditions. It is
not a learning experiment; it provides no independent training replicate; it does not
attribute an initial-to-final change to PPO, learning rate, NLL, normalization or any
component; it establishes no general "learning harms", stability or relay capability; the
initial-to-final contrast includes every controller-state difference formed by training, not
only parameters. It does not re-read B01/B02/B03 or A01–A05, and it is not a prerequisite for
any learner-side B (the response's explicit reading). No outcome automatically buys a learner
B, restores package investment or changes Portfolio.

## 2. Inputs (fixed) and what the code map established

**Initialization.** The zero-update state is obtained from
`build_master_addressed_initial_state(master=<B03 master bytes>, block=0, arm="STRUCTURED")`
(`experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_recurrent_trainer.py:170-231`),
master `b938a93e7b41bec6c1b0df8761649fda2e0779f05d6610de5ed5ba71f780543a`
(sha256 of ASCII `DISH-FORECAST-PACKAGE-B03/seed/73`). The function overwrites every parameter
of the 25 linear layers from the master-addressed `INIT` stream, sets `log_std` to the constant
−0.5, returns `torch.save` bytes of `{model, optimizer (fresh AdamW, no step), welford (three
empty states, count 0), update: 0, evaluation_checkpoint: False, initialization}` and consumes no
other RNG; both B03 arms called it with these same arguments (`initial_model_norm`
38.24996300787587 identical in both summaries). **No code path saved this state to disk**; B03
persisted only `checkpoint_update16.pt`. The response's input rule therefore resolves to the
second branch: the witness **generates the zero-update state once** from the recorded master and
the existing initializer and labels it `reconstructed_from_master` in its publication; it
records the initializer call count, the model/optimizer objects the helper constructs, and the
parameter L2 norm, which must equal 38.24996300787587 as a check quantity (a check, not proof of
identity with the B03 start; that identity rests on the initializer's determinism, which the
focused check pins). No inference of the initialization from final parameters, no seed 61, no
training reconstruction, no initialization search.

**Zero-update normalization state.** The empty Welford states from the same bytes (count 0):
`WelfordState.normalized` then uses variance 1 without mean-centering and clamps to ±10
(`production_training_engine.py:197-199`). Evaluation never updates Welford state
(`BatchedRecurrentPolicy.normalized_actor` only reads it). Neither final Welford state is
loaded; nothing is refit on evaluation data.

**Two interface views on the same bytes.**
`BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=initial, state=RecurrentRolloutState.fresh("STRUCTURED", width=1), forecast_package=<view>)`
with `forecast_package=False` for the CONTROL view (raw service logits to the native
probability input) and `True` for the FORECAST_PACKAGE view (sigmoid on the same head,
`production_recurrent_trainer.py:347`). The two views share every parameter (`service_q` and
`prediction_cholesky` always exist); no weight is drawn; the NLL head has no consumer at
inference. One policy object per view; fresh recurrent state per episode.

**Conditions and exogenous inputs.** The four B03 coordinates in B03's order
(TARGET_VISUAL_MASK / K8, TARGET_VISUAL_MASK / K4_TO_K12, TERRAIN_RELAY_MASK / K8,
TERRAIN_RELAY_MASK / K4_TO_K12; speed 4, slot 0, block 0; recorded phases 4, 2, 1, 1). Each new
episode is reset from the **recorded** `evaluation_rows[].reset` dictionary of
`b03_forecast_package_20260906/control/summary.json` (byte-identical to the package summary's,
verified) fed to `native_batch_from_rows((row,), library=library)`; the rows are pure scalars
derived from (master, coordinate) and reproduce the same phase, route, switch tick and
degradation tick. No new phase, route or noise draw. The focused check pins that each recorded
reset equals the coordinate's recomputed `_reset_row`.

**Reused final rows (read-only).** CONTROL 452 / 458 / 449 / 483 and FORECAST_PACKAGE
92 / 222 / 129 / 311 with their energy, hard events, terminal facts and transfer fields are
read from the two B03 summaries by coordinate and copied into the publication with
`source = "reused:b03/<arm>/summary.json"`; the update-16 checkpoints are neither loaded nor
executed.

## 3. Host and path

`GROUND-TERMINAL-LINEAR-CLEARANCE-A03` unchanged; corrected ordinary renewal boundary
(`3f4d447f6`); native float64, policy FP32, `torch.set_num_threads(1)`; reward, information,
action space, projection, prepare/certificate/transfer rules unchanged; no fitting, optimization
or threshold tuning. The initialization controllers are not held-only: they may propose motion
and protocol actions. Path per episode: recorded route and degradation events → role-conditioned
causal observation and real messages → recurrent state under frozen weights → ordinary motion and
prepare/commit/forecast outputs under the current permission → unchanged native behaviour and
service → fixed-range reduction, then subtraction from the reused final row. `evaluate_episode`
(`forecast_package_b02/study.py:124-155`) unchanged, horizon 1,200; native early termination stops
stepping, unexecuted ticks count zero service, completed ticks / termination reason / events
are reported; after a legal transfer the ordinary evaluation continues; no row is filtered by
trigger, service sign or phase. No credit assignment, learning step, passive-label promotion,
source fork or scripted transfer.

## 4. Measurement and reading

Primary: `D_a` per arm as in §1, with each view mean, all eight per-row differences, the eight
new row values and the eight reused values in one table whose `source` column separates
`new:zero_update:<view>` from `reused:b03/<arm>/summary.json`; the reused −272 pair's provenance
stated. Companion fields per new row exactly as `evaluate_episode` records them (service ticks,
completed ticks, energy, the seven hard-event classes, terminal facts, legal transfers, service
before / at-or-after transfer, unstepped ticks); zero training transitions, backward passes,
optimizer steps and label calls (asserted zero in the publication); parameter norm before and
after the eight episodes (must be equal); counts of initializer calls, policy constructions and
checkpoint loads.

Descriptive scale **24 mean service ticks, symmetric** (0.02 of the range); not a per-row
tolerance and not a redefinition of B03's rule. Reading (from the response; applied per arm, not
as a joint gate):

| Pattern | Reading and the successor it motivates |
| --- | --- |
| `D_C ≤ −24` | the final CONTROL serves below its own-interface zero-update view on this panel: concrete motivation for a *named* stability B (no proof that the learning rate is too large or PPO wrong); if the package also drops, report a shared conditional before/after loss, not two seeds |
| CONTROL holds or improves (`D_C > −24`) while `D_P ≤ −24` | do not adopt "common learner degradation"; the package stop stands; any successor targets a still-grounded specific learning/control question rather than generally lowering update strength |
| both `D_a ≥ +24` | the panel does not support "sixteen updates made both arms worse"; B03's package-adverse conclusion still holds (absolute improvement and incremental disadvantage coexist) |
| inside band, heterogeneous across rows, or with adverse companion costs | keep every row; state no clear large change; no equivalence claim; no sample-adding until signs agree |
| inputs, path or measurement insufficient or incomplete | keep only trustworthy measured rows; no complete `D_a`; B03 is not quarantined; return the specific comparison gap |

Bad native behaviour of a zero-update view is a valid observation (no initialization swap, no
row filtering). Companion energy and events are reported, never used to offset service.

## 5. Predictions on record

- **DM (hub), prospective.** The two zero-update views will differ materially from each other
  because the raw-logit interface feeds near-zero untransformed values into the native
  probability input while the sigmoid view feeds values near 0.5: the zero-update
  FORECAST_PACKAGE view is predicted to serve more than the zero-update CONTROL view. Pattern
  predicted: row 2 of the table, `D_C > −24` (the final CONTROL at 460.5 is not below its raw-logit
  initial view) and `D_P ≤ −24` (the package's 188.5 is below its sigmoid initial view).
  Confidence: moderate on `D_P ≤ −24`, low on `D_C`.
- **Node (Pro), prospective**: none stated numerically; the response treats every row of the
  table as a serious outcome.
- **Owner**: not taken (unattended).

## 6. Work, cost and stop boundary

Work: one initializer call; two policy constructions; 2 views × 4 conditions × ≤ 1,200 ticks =
**at most 9,600 actual native ticks**; zero training / replay / backward / optimizer steps /
next-label / delay / consequence work; no passive-label interface; final checkpoints not loaded;
no search, source fork, held-only rows or B02 checkpoints. Publication of one `summary.json`.

**Cap: 120 s whole-item compute wall** on `wsl_4070`, covering the one focused check the object
needs, native build or cache load, initialization, the eight episodes, comparison and
publication; shared preparation charged once (not "120 s plus build"); splitting into check and
formal invocation does not reset the cap. The runner's allowance is `120 − C` seconds where `C`
is the measured wall of the focused check on the node; the formal invocation is bounded by that
allowance. This is a spend choice, not a projection: no per-episode evaluation wall exists in
any B02/B03 record; B03's `C = 4.94 s` indicates a warm native cache on the node; the A02 window
and the B03 arm walls are not extrapolated.

Execution: exact committed and pushed source, detached `agent-task`, single CPU thread, FP32
policy / float64 native, fresh memory admission (≥ 4 GiB physical and effective) immediately
before the formal invocation; full wall and scoped peak RSS reported; no profiler, registry,
validator, worker pool, ABI or resource threshold added; 2,000 / 600-line budgets. Stop at the
eight episodes and complete publication, or when the allowance is exhausted, an input fails, or
an actual failure threatens the primary measurement; terminations are kept, not rerun; no
replacement seed, extra phases or conditions, automatic retry, or ad-hoc final-policy rerun; no
second object allotment this round. An incomplete run publishes its actual rows and counts and
is taken in under the last row of §4.

## 7. Acceptance (bounded)

Prove that the stated inputs and the ordinary path ran: the reconstructed initialization label
and norm; `count == 0` Welford at load; both views built from the same bytes; the eight recorded
resets consumed verbatim; eight rows or legal terminations complete; zero training counters;
the reused rows joined by coordinate with correct values; fixed-range service and events
readable. Reuse B03's accepted primary reduction and corrected-boundary coverage. One targeted
focused check (new test file, fast, no learner, no development panel) for: initializer
determinism across two calls; recorded-reset round trip against `_reset_row`; a policy built
from the initializer bytes exposes the raw and sigmoid views of one head with Welford count 0;
the publication arithmetic (`D_a`, means, source column, zero-training assertions) on synthetic
rows. No rerun of A01/A02, the r06 suite, the final eight rows, training history, every hidden
array, or cross-platform bit identity. If the same host, information, termination or evaluation
semantics cannot be established, the reused comparison is what is damaged; no unselected final
rerun or new implementation fills it in.

## 8. Records

Card (this file); CM objective `DISH_INIT_WITNESS_A01_CM_OBJECTIVE_20260906.md`; CM record; launch
and result under `docs/research/candidates/degraded_incumbent_shadow_handover/init_witness_a01_20260906/`;
result intake `DISH_INIT_WITNESS_A01_RESULT_INTAKE_20260906.md`, then the same Convergence node.
