# Energy relay diagnostics

## 2026-09-27 — Question adoption and bounded source reconstruction

Lead: **Codex DM (independent session)**, authoring on shared main. The owner assigned
the joint D2/D3 question: on frozen S7-S2/H3000, which training/evaluation differences
come from worlds, policy snapshots, action mode, aggregation or the proposal → shield →
environment path, and what remains to justify a learning intervention? No new fit is
authorized by a flat training curve alone. This is exploratory work on one retained SET
training instance, not a learning-population claim.

Sources read before design: current main `d81fc8622`, the corrected
[Claude report](../../../inbox/2026-09-27-energy-relay-benchmark-report-and-directions-for-codex.md),
[benchmark NOTES](../energy_relay_benchmark/NOTES.md) B01/Stage 0/c00–c03 and the recovery
declaration, and [RESEARCH](../../RESEARCH.md) native service/risk, information structure,
and cost of diagnostic comparisons. The existing S7 feedback and recovery studies require
complete J/QoS/return-cost/risk readings: fewer overrides, more charging, less wall contact,
or a better proxy alone do not establish useful control. H_local is a planner pooling all
eight legal observations, not an independently decentralized actor. SET reads a current
local observation plus a held central state/joint-observation/ego snapshot, refreshed at k=10,
with a recurrent low-level network.

Adverse constraints retained: N sampled service .308/.318 versus .328 deterministic, despite
roughly halving boundary residence, weakens a pure action-mode account of the service deficit.
c00→c03 service rises .209→.325 deterministic and .243→.345 sampled on the fixed development
panel; this does not identify why collection-time summaries stay lower. The original report's
reward/credit explanation is a hypothesis. A same-weight squashed decode changes the policy
and is not an evaluation correction. The earlier fit's failure and recovery remain Claude's
evidence and operation; this direction neither restores nor takes over them.

Exposure boundary: only public 955001–955032 development evidence and c00/c03 inputs are
eligible here. No reading, reevaluation or use of 957001–957032 or the sealed
`b02_holdout_refs_a01` outputs; later publication cannot turn these into our unseen test set.
No c04–c06 collection or observation of Claude's accepted operations. Zero new optimizer updates.

Applicable independent scientific review already supplied by Root: `/root/dm_allocation_review`
in a context without conversation inheritance supported merging D2/D3, narrowed the first
observation to c00/c03, rejected mechanical reevaluation of every checkpoint and an automatic
post-diagnostic fit. Its proposed 128–160 episodes/0 fit and comparable collector/evaluator
readings are adopted as the starting scope. Exact path/stream feasibility is being reconstructed;
any necessary materially different design will receive a focused review, not a repeat allocation
review. Pro adds no distinct question at this point.

Historical limitations already verified in source: B01 stores rewards/metrics, poses, shield
modes and energy/station facts but no proposal/submitted actions or full observations. B02
stores lane/episode J and QoS, override/mode counts and update summaries; it drops the original
step traces. Its first lane resets use seed 925031+lane, later `reset(seed=None)` continues the
environment RNG. Independent resets with those integers cannot be labelled a replay of that
continuous stream. Recovery explicitly reseeds environment/action streams and is not exact
episode-stream continuation. New observations must record the absent fields prospectively.

### L0: optional action/input instrumentation, 0 fits

Deliverable: a reusable, opt-in trace observer for the unchanged B01 world evaluator, implemented
in `experiments/candidates/energy_relay_diagnostics/b01/instrumentation.py`, with tests under
`tests/experiments/candidates/energy_relay_diagnostics/b01/`. The owner permits a narrow shared
exception in `experiments/candidates/energy_relay_benchmark/b01/evaluation.py` only to expose
optional observation hooks. The shared file has no pending edit at the initial check. No change
to runner interfaces, default traces, host/reward/shield, checkpoint loading, sampling, resets,
recurrent/snapshot cadence or holdout guards. No edits to Claude's NOTES or training collector.

Interface intent: `evaluate_world(..., observer=None)` and `evaluate_task(..., observer_factory=None)`
may accept the optional direction-owned recorder; normal calls remain unchanged. The observer
receives decision-time legal observations and current central state, controller proposal before
shield, submitted command after shield, and post-step observations/state. For learned policies
record the actual actor distribution mean/effective scale from the forward pass that produced
the action, plus held snapshot identity/age. Hooks must not call the actor a second time or draw
RNG. Full legal observations, central state and held snapshots are separately opt-in; action
diagnostics may be collected without bulk inputs. Teacher use must keep pooled legal information
and privileged/current state separately labelled. Fields must never mix t and t+1.

Checks: existing evaluator default-contract tests; instrumented versus uninstrumented equality
for native trajectory/actions/RNG/fingerprint/normalizers on deterministic and sampled learned
paths; correct proposal/submitted distinction under active shield; snapshot hold/refresh timing;
heuristic without actor fields; copy ownership and hook teardown on success/failure. Use pytest
scratch ownership. Independent engineering review is required before result execution because
these hooks touch the evaluator and numerical/RNG path. Implementer returns diff/checks only;
DM accepts and publishes under the shared Git writer lock. No subagent edits this notebook.

Cost: zero fits and no result-bearing probe during implementation. Focused synthetic/short-native
correctness tests only. Full planned observation remains bounded at 128–160 H3000 episodes
(384k–480k transitions; roughly 30–40 minutes at prior throughput before contention/instrumentation).
Engineering, review, storage and actual node wall are additional costs, not zero. Full input
traces will use a small prospectively fixed subset; all-world action traces and compact native
per-world summaries suffice for the principal reading. Stop implementation for an unavailable
actual actor hook or semantic change, returning the concrete limitation instead of changing
the policy. Exact runnable protocol follows after source reconstruction.

### L0 continuation: frozen collector adapter and admitted study entry

DM owns `b01/collector.py`, `b01/study.py`, `b01/readout.py`, the direction-local
`run_b01.py`, and their matching tests; these are disjoint from the instrumentation Implementer.
Reuse the actual B02 `collect_and_train` with one lane/one complete episode, an agent facade
that forwards real step/storage/bootstrap/reset/clear calls while replacing the optimizer update
with an explicit counted no-op. Seed immediately before the first policy step using the evaluator's
sample seed, and use the same frozen checkpoint/world/config. A process-local, try/finally-scoped
environment-factory wrapper records transitions without modifying the original collector file.
No two calls run concurrently in one process. Refuse a policy/optimizer/normalizer mutation,
incomplete episode or mismatch of actual submitted actions and the independently decoded production
shield. The adapter is a one-lane CPU path check, not a reproduction of two-lane CUDA training.

Reuse B01 metric and phase aggregation. Compact JSON carries per-world results, all adverse worlds,
checkpoint/config identity, 0 updates, costs and raw file hash/size; large arrays stay at the declared
node output. The entry calls admission before candidate imports/scientific effects, pins c00/c03
external checkpoint hashes and refuses any world outside the prospectively fixed development panel.
Tests compare the adapter with the real evaluator on short native fixtures and verify unchanged
parameters/normalizers/optimizer counts, all native summaries, missing/malformed inputs and holdout
refusal. Engineering review covers the adapter, runner and readout together with instrumentation.

New source fact: the retained B02 config specifies `tanh_gaussian`, and the actual head returns
`tanh(mu)` deterministically or `tanh(rsample())` stochastically (`hmasd/r_mappo_utils.py`). Thus
the deterministic action is not the expectation of the bounded stochastic action. A raw-normal
clipping-only account is inapplicable to this SET instance; spatial boundary truncation can still
occur with bounded persistent velocities. This fact narrows the action reading before any new
outcome. A focused independent critic is reviewing the marginal value and allocation of the exact
comparability observations, reusing Root's question-selection review rather than repeating it.

## 2026-09-27 — B01 fixed prospective comparison after focused independent review

The initial registration is now published at `ce3947efb`; Root's complete allocation review is
[preserved here](../../archive/2026-09-27/RESEARCH.md#two-dm-allocation-review). Its narrower
c00/c03 proposal is retained. The focused ResearchCritic `/root/alignment_design_review` ran with
`fork_turns=none`, reconstructed source/outputs before opening this notebook, and did not inspect
holdout or c04–c06. **Recommendation adopted: 136 complete native episodes, 0 fits, 0 updates.**
The critic initially questioned 64 collector episodes: the saved tanh actor has no dropout/BatchNorm,
input normalization is disabled, and terminal H3000 bootstrap is zero. Most additional collector
episodes would broaden code coverage without identifying the unmatched historical comparison.
Eight complete collector episodes plus a second c03 sampled draw have more decision value.
The revised design received **MATERIAL_DISSENT: no**. No added Pro consultation is useful now.

The critic's consequential evidence and constraints are retained: the c03 draw-0 service mean
improves over deterministic while return cost worsens; only 17/32 worlds improve service and
25/32 pay more return cost. World 955016 loses service completely and incurs much greater return
cost, while 955005 escapes zero service. Wall occupancy cannot select an evaluation mode or prove
control benefit. All 200 original training episodes through rollout 100 are H3000 truncations,
so simple episode-versus-step weighting cannot explain the historical gap. Different worlds,
changing policies, CPU/CUDA, batched sampling and continuous RNG remain unmatched. This review
supports neither a reward/credit diagnosis nor a learning-population claim.

### Fixed exposure and inputs

Same S7-S2/H3000, 8 UAVs, production shield (0,.05), original reward/return coefficient 2,
and existing native evaluator/loader/metrics. Frozen retained SET c00 (initialization) and c03
(600k transitions), both from `759927b5e8caa0ba5bd8ba505ab5388985f6a2fa`, training seed 925031.
The runner pins full checkpoint SHA256, fingerprints and the recorded config digest; these are
source identities, not fresh training replications. Checkpoints are read from their existing
node artifact copies, with no new checkpoint duplication. Exact command/config live in the run.

| Panel | Worlds | Episodes |
| --- | --- | ---: |
| c00/c03 evaluator, sampled draw 0 | 955001–955032, separately per checkpoint | 64 |
| c03 evaluator, deterministic `tanh(mu)` | same 32 | 32 |
| c03 evaluator, sampled draw 1 | same 32 | 32 |
| c00/c03 actual collector, sampled draw 0, no update | 955001, 955005, 955016, 955021, per checkpoint | 8 |

The four-world subset deliberately covers the first development world and published adverse
cases; it is not a random sample for inference. Complete native endings count as observations,
including an early termination. The collector stores the terminal transition then stops before
resetting into a second episode; an early ending need not reach H3000 or the skipped-update call.
Full H3000 endings retain the real zero terminal bootstrap and one counted no-op update. No live-lane
bootstrap claim is made. No retry, extension, extra checkpoint, altered decode or fit follows a score.

Every episode records actual head parameters, proposal/submitted actions, t/t+1 legal positions,
held-snapshot age and per-step input/context identities plus original native metrics. Full t/t+1
legal observations, current privileged central states and held SET snapshots are retained only
for c03 evaluator deterministic/draw-0 on the four subset worlds: 8 episodes. Their distinct field
names/timings support later teacher collection without conflating legal information, central
state, proposal, submission or snapshot refresh. World raw arrays remain in one durable node copy.

CPU FP32 throughout, initially 4 workers × 1 Torch thread, same numerical settings on paired
paths. This is deliberately a single-lane CPU comparison of train-mode/storage versus evaluation;
it does not replay original two-lane CUDA training. Original published evaluator timing used
8 workers × 2 threads, so old wall rates and exact historical trajectory identity are not assumed.
The existing sampled seed rule is used with explicit draw 0/1, immediately before the first action.

### Predictions, falsifiers and reading

1. **Path alignment.** Prediction from source: identical single-lane inputs, head outputs,
   proposals, submissions and transitions for each collector/evaluator pair, unchanged weights,
   optimizer states/counts and normalizers. Record exact array identities and any first divergence,
   not only a mean. Agreement weakens suspicion of this tested train-mode/storage path; it does
   not identify the historical gap as exclusively a world or measurement effect. A divergence
   is located in input/context, head, proposal, submission or native transition; same head but
   different sampled actions can reflect RNG consumption and is not itself a biased learner.
2. **Mode and action stream.** Preserve c00→c03 sampled draw-0 change; c03 draw 0 versus
   deterministic, draw 1 versus deterministic and draw 1 versus draw 0. For the new diagnostic
   summary, average the two draws equally within each world, then average worlds, while keeping
   each draw and every adverse world. The historical draw-0 result is unchanged. Similar native
   consequences across draws strengthen a conditional deployment description; reversal or large
   changes weaken reliance on one draw. Neither outcome selects a canonical mode or increases
   the number of independent training instances.
3. **Execution description.** Report proposal/head saturation (horizontal component magnitude
   ≥ .95), outward proposals/submissions at a spatial wall (within 1 m), and observed horizontal
   stationarity (< .05 m displacement) alongside normal/F modes. Persistent modest outward
   commands weaken saturation as the wall explanation. Saturation supports only that behavior
   description; aggregate guard counters cannot attribute a particular UAV's motion difference
   to guard, docking, energy dynamics or position clipping. No changed decoder is tested.
4. **Native use.** Read complete J, QoS, return cost, cutoffs/depletions, minimum battery, charging,
   waiting and losses per world. Common pre-entry windows are descriptive matched windows, not
   estimates of the shield's causal contribution. The .03 QoS scale is inherited context, not
   a new joint-service/risk pass rule. A flatter curve, fewer wall steps or higher sampled mean
   does not justify a new learning intervention without a separate worthwhile prediction.

Cost: at most **408,000 environment transitions**, 0 fits/optimizer updates. **40–80 min** is a
provisional planning range for four workers, including unknown collector/instrumentation effects;
contention, engineering, review, readback and storage are additional measured costs. Raw output
is provisionally expected below 2 GiB compressed; report actual bytes, not a storage guarantee.
Fresh wsl_4070 admission remains required; no interference with Claude's fit/evaluations.

Engineering so far: optional interface implemented; four new observer checks passed, four existing
evaluator contract selections passed (176.21 s), three initial real-collector checks passed
(14.82 s), then eight observer/collector checks passed (19.25 s) after adding compact per-step
input identities and preserving early native endings. These are synthetic short-native checks,
not new scored benchmark episodes. Independent engineering review and exact-input publication
precede the result launch.

### Engineering acceptance and publication boundary

DM read and accepted the Implementer's optional observer and the fixed batch entry. Independent
`hmasd-reviewer` `/root/engineering_review` found no material issue after checking the actual
head hooks, RNG/snapshot timing, real collector storage and native ending, zero-update contract,
paired/equal-draw reading, checkpoint pins, raw retention, admission order and failed exit status.
The reviewer ran 16 then-current tests plus the new CLI regression. Its generic disappearing-log
telemetry concern was withdrawn after confirming the current actor creates no such files; the DM
nevertheless made optional disk telemetry tolerate OS errors as `resources_unmeasured` instead
of interrupting collection. This changes only cost reporting. Full H3000/multiprocess execution
and actual checkpoint loading remain runtime checks, not claims from the synthetic test pool.

Final focused evidence: 17 combined direction tests passed in 19.57 s; after the telemetry-only
change, all 7 study tests passed in 3.72 s (18 distinct direction tests in total). Existing default
evaluator checks above remain applicable; no repeated broad suite was purchased. Read-only
SHA256 on the actual wsl_4070 c00/c03 artifact files exactly matched the prospective pins.
Preparation/review wall was not separately metered; it is not reported as zero.

The original public training summary was also checked directly through rollout 100: 200 H3000
episodes, mean sampled collection QoS .1775678717; first/last ten-rollout means .1914571869 /
.1944008227. Lane and completed-episode QoS summaries are numerically identical (maximum
difference 0). This eliminates a simple lane/episode weighting discrepancy in those records,
while leaving world/snapshot/device/action-stream differences unresolved. It does not restore
missing historical per-step reward components or action/input traces.

### Exposure audit at shared-main publication

During the shared-main refresh, a broad `git log -4 --oneline` unintentionally displayed
another author's c04 result summary in a commit subject. No c04–c06 result artifact was opened
or used. The 136-episode protocol, predictions, code and independent reviews were already
fixed before this exposure and are unchanged. Subsequent synchronization reads commit identities
and owned paths only. This session cannot claim complete blindness to c04; the source-subject
exposure is preserved rather than silently omitted. No sealed holdout result was opened.
