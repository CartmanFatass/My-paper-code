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

## 2026-09-27 03:05 UTC — B01 accepted on wsl_4070

Exact inputs were committed and published on main at `ef5c35b77929fbf029d8e2eec9487c1371215bce`
before launch. The configured `agent-task` submitted the native snapshot launcher once; its
receipt is distinct from scientific admission. The native manifest records accepted operation
`4cb8c42b9e311d10759a059066a2808e4a3f599d59d4f39451a26b887921772f`, created
`2026-09-27T03:05:17.319992Z`, supervisor PID 745191 and runner PID 745192 with boot/start identities.
A subsequent native status read found both identities running, a consistent record, and no exit witness.

[Manifest](../../../../runs/energy_relay_diagnostics/b01_alignment_a01/launch-manifest.json),
[resource preflight](../../../../runs/energy_relay_diagnostics/b01_alignment_a01/admission-preflight.json),
and [fixed config](../../../../runs/energy_relay_diagnostics/b01_alignment_a01/config.json)
are copied as compact control evidence. The actual output remains
`/home/wu/projects/HMASD/runs/energy_relay_diagnostics/b01_alignment_a01`; retained source is
`/home/wu/projects/HMASD/.git/hmasd-launch-sources/d1edd10948b649f084a7d0f248791c99`.
The fresh admission measured 12,657,426,432 available bytes against a 4 GiB floor. Runtime config
confirms exactly 136 planned episodes, CPU, 4 workers × 1 Torch thread, 0 fits and 0 updates.
Bulk arrays are not duplicated locally. Final scientific completeness, measured cost and adverse
readings remain pending; admission and a running PID are not a result.

The deterministic local observer request uses the manifest's same `operation_ref` with read-only
remote native `status`, 30 s probes and a 1500 s observation window. It will be armed before
returning the turn. Checkpoint wakes drain and rearm that handle without relaunching anything.
The earlier unsuited noninteractive Git transport stalled before any scientific request; only
that session's Git transport helper was terminated, and synchronization then succeeded through
the configured `zsh -lic` network shell. Existing remote auto-GC warnings reported missing
historical tree `9e40125ee3e24973b69754649226d18847b45862`; no GC repair/deletion was attempted.
The current published tree synchronized and native source-snapshot admission succeeded.

### 2026-09-27 03:35 UTC — native observation checkpoint

Drained generation 1 / wake `9ef05798-7b58-4521-a21c-976a3e58ba34`, event
`ebe3f0c9d7397378618fb27c`. Native operation 4cb8c42b remains accepted and running with
matching supervisor/runner identities, no observer errors and no exit witness. The direction
and owner-pause controls remain unchanged. A counts-only read reports 93/136 completed
episodes, 279,000 transitions, 0 failed episodes, 0 fits and 0 optimizer updates at
1,663.22 s parent wall; raw logical bytes 313,869,673. These are incomplete progress/cost
facts, not scientific readings or final costs. No panel scores were opened or design changed.
Rearm the same observation with this drained event; no worker is restarted.

## 2026-09-27 — B01 complete: restricted path agreement, service–risk dissociation

### Native completion and verified evidence

Operation `4cb8c42b9e311d10759a059066a2808e4a3f599d59d4f39451a26b887921772f` exited 0
with a valid native witness at 03:47:03 UTC. Both recorded native process identities are absent;
records are consistent. Generation 2 / wake `5dbc24fc-91c7-4214-889e-79aef45a62d9`, event
`3890285c971bdbcd57f4bc66` delivered this terminal fact. The scientific runner separately reports
**COMPLETE: 136/136 episodes, 408,000 transitions, 0 failures, 0 fits, 0 new optimizer updates**.
All 136 native episodes ended by H3000 truncation; no early ending occurred in this batch.
No retry, extra checkpoint, additional draw, changed decoder or new fit was launched.

[Native summary](../../../../runs/energy_relay_diagnostics/b01_alignment_a01/summary.json),
[config](../../../../runs/energy_relay_diagnostics/b01_alignment_a01/config.json),
[terminal witness](../../../../runs/energy_relay_diagnostics/b01_alignment_a01/process-exit.json)
and the six `panels/*.json` preserve all world values and signed comparisons. All 136 remote
NPZ file SHA256/byte counts match their panel rows; all 136 individual JSON rows equal the
corresponding panel entries. Core native/head/action/position arrays are finite and length 3000;
all proposal/submitted components are bounded, and final `ends` is `[false,true]` everywhere.
All eight declared full-input archives are present and finite; recorded t, held source t and
held age exactly follow the registered k=10 cadence. Fifteen collected compact files also
matched the remote content hashes before duplicate local log/progress cleanup.

The canonical raw copy remains on `hmasd-wsl-node` at
`/home/wu/projects/HMASD/runs/energy_relay_diagnostics/b01_alignment_a01/raw/`:
**408,094,182 logical bytes**, 408,379,392 allocated bytes at completion. No raw archive was copied
locally. Ordered `(raw_path, raw_sha256)` pairs, serialized as sorted compact JSON, hash to
`953dcd9cb1a2aa6ece6c7ac1d8051614bf6772c0fe77f9840a520650ee54c41e`.
The original summary SHA256 is
`c908652a623f00cdfd4521285ffdded9d6c226670c83a5bcd4b7a4c60d535b57`.
Each raw locator/hash remains in the compact panels. The nonfatal stderr consists of 136 notices
about an absent discriminator buffer and eight warnings each for single-element skill-logit
standard deviations. The former buffer is unused here and there were no updates; the latter
are diagnostic statistics, while the collected numerical arrays passed the finite checks.
Original logs remain at the canonical output rather than being rewritten or hidden.

### Read by the fixed prospective comparisons

Every figure below is conditional on this one retained SET training instance, the 32 already
exposed development worlds, and this run's CPU/4-worker/1-thread realization. The collector
subset has four deliberately chosen worlds, not four independent training replications.

| Frozen panel | QoS/step | Native J | Return cost | Worst episode minimum battery | Normal-mode boundary share |
| --- | ---: | ---: | ---: | ---: | ---: |
| c00 sampled draw 0 | .242862 | 692.942 | 4.619 | .087044 | .011208 |
| c03 deterministic | .336776 | 979.529 | 1.657 | .082683 | .362775 |
| c03 sampled draw 0 | .340714 | 983.670 | 4.952 | .074577 | .093562 |
| c03 sampled draw 1 | .344618 | 977.825 | 13.853 | .069009 | .101978 |

**Path alignment prediction met.** All eight collector/evaluator pairs have identical action
and native array digests, identical recorded input/context/head streams and no first divergence.
All collector episodes stored 3000 transitions and counted one skipped update; weights,
normalizers and optimizer counts were checked unchanged. The tested single-lane CPU training
mode/storage path therefore does not supply the gap in these comparisons. Optimizer behavior,
live-lane bootstrap, two-lane CUDA, the changing historical policy and the original continuous
world/action streams remain untested. This is not a claim that the complete training pipeline
is globally equivalent to evaluation.

**Learning across the saved snapshots remains visible.** c03−c00 under sampled draw 0 is
+.097852 QoS/step (conditional paired-world SE .015858) and +290.729 J (SE 47.851); 24/32 worlds
improve in each. Six worlds lose QoS, eight lose J; the largest QoS/J loss is world 955025
(−.036114/−103.449). Return-cost mean changes by +.334, with 10 worlds worse; the largest cost
increase is 955001 (+34.440), which also has the largest battery loss (−.025395). The common
pre-entry QoS difference is +.083759, descriptively. Boundary residence increases in all 32
worlds while mean native service improves, another reason not to use boundary occupancy as
performance. None of this identifies a representation limit or an objective/credit defect.

**Changed deployment behavior does not justify a preferred mode.** Equal weighting
of draw 0/1 within each world versus deterministic gives QoS +.005890 (SE .014269), J +1.219
(SE 45.894), return cost +7.746 (SE 3.048; 30/32 worlds higher), and average episode minimum
battery −.010085 (24/32 lower). Boundary share falls by .265005 in every world. Mean charging
input increases by 97.313 Wh, waiting by 1715.563 ticks and F-mode occupancy by .086351.
Individual draws retain distinct consequences: draw 0 versus deterministic gives QoS +.003938,
J +4.141, cost +3.295; draw 1 gives +.007843, −1.704, +12.196. The draw-1 minus draw-0 QoS
mean is only +.003904, but per-world changes span −.214713 to +.354900 and the mean cost
increase is +8.901. Small means do not establish equivalence or action-stream insensitivity.
No canonical action mode is selected. There are zero cutoff/depletion events throughout;
this does not erase cost/battery losses or establish safety.

Important adverse worlds, all retained in the panel tables:

- **955011:** deterministic QoS .264 / J 764 / cost .54 becomes zero service / J −317 /
  cost 144.28 in draw 1. Its draw-1 minus draw-0 J is −925.836.
- **955016:** draw 0 gives zero service and draw 1 gives .354900 QoS; the failure is
  action-stream sensitive within this same execution configuration.
- **955021:** all three c03 runs give zero service, while return cost is 1.63 deterministic
  and 22.91/35.70 in the sampled draws.
- **955005:** deterministic QoS .259 exceeds draw 1's .087; an older zero-service label
  for this world does not describe this new execution configuration.

**Saturated mean actions do not explain these walls.** In every world, normal-mode horizontal
`tanh(mu)` never reaches the declared .95 threshold. Deterministic proposals agree with it
within 5.97e−8; no out-of-bounds proposal/submission is observed. Sampled horizontal saturation
is also rare (world means .000205/.000212 at c03). Nonetheless, deterministic boundary residence
is .362775 and outward submissions occur in approximately .905009 of normal-mode boundary
cases. Modest persistent outward commands are better supported than saturation. The average
stationarity share among outward normal-mode submissions is only .075227: boundary residence
must not be relabelled immobility. These records do not assign individual motion changes to
spatial clipping, guard action, docking or energy dynamics; aggregate guard counts cannot do so.
Common pre-entry sampled−deterministic QoS differences are −.005283/+ .016947 for draw 0/1;
they are descriptive matched windows, not estimates of the shield's causal contribution.

**Historical values stay separate.** The old c03 deterministic/sample-0 means are
.324896/.344789, while these are .336776/.340714. The prospective protocol explicitly changed
8 workers × 2 threads to 4 × 1 and disclaimed trajectory identity. A scoped source diff from
`759927b5e` to `ef5c35b77` shows no learner/environment changes; the evaluator change is the
optional observer, the collector adds default-preserving resume offsets, and native planning
adds excluded-world guards. Thread count is a plausible contributor, not an established cause.
Do not overwrite old readings, silently combine them, or label these a reproduction of the
original CUDA collection. The earlier accidental c04 commit-subject exposure remains recorded
above; it was not used for this interpretation, and no excluded result artifact was read.

### Independent scientific review and investment decision

ResearchCritic `/root/alignment_design_review` retained its original separate context
(`fork_turns=none` at creation), reconstructed the six native panels before reading prospective
predictions, and received no proposed DM explanation. It read no excluded output or other
new direction's scores. Its full substantive diagnosis is adopted: restricted CPU path agreement
met the prediction; mean-action saturation is directly weakened; service–risk dissociation and
adverse action-stream outcomes are the strongest new evidence; historical causes remain
unidentified. The review explicitly rejects treating wall residence as immobility, small
mean differences as equivalence, or thread count as a proven explanation.

Its recommendation is to **close further investment in this path/saturation diagnostic**, retain
both evaluation modes and all adverse draw/world readings, and launch no follow-up from B01
alone. More collector parity coverage or additional wall/action panels would not isolate the
historical mismatch. A decoder or reward change lacks a supported intervening failure link.
Independent fits concern reproducibility and imitation concerns finite learnability, neither
of which these extra evaluation episodes can establish. A fresh-world or CPU/CUDA study would
need a consequential estimand: fresh worlds test another sample, not reconstruction of the
old continuous training stream. At the observed rate another 32-episode panel is about ten
minutes plus overhead; its low marginal action-changing value, rather than absolute cost,
motivates no further batch. **MATERIAL_DISSENT: no.** No Pro round adds distinct value to this
resolved in-scope decision.

DM disposition: adopt the no-run recommendation and end this diagnostic investment now, while
retaining ownership of the broader unresolved comparability/execution question and the reusable
trajectory interface. The batch ending alone is not the reason for closure: the predicted
path equality occurred, saturation did not, and deployment sampling changed service/risk
with little mean J change and worse cost/battery components. More of the same evidence cannot distinguish the remaining
historical world/snapshot/action/device contributors. No fixed waiting condition, automatic
fit, reward rescue or repeated diagnostic ladder is created.

Current shared context was refreshed to published main `dee7ae639de6f9f4691e3d477d30989e27ead88e`.
The S7 service/risk background (RESEARCH section 6, especially B09–B11) already requires reading
local behavior alongside complete service, cost and battery consequences; B01 strengthens this
with a matched-mode example rather than treating fewer walls as a repair. The updated allocation
keeps independent RL repetitions with DM1 `energy_relay_baselines` and places imitation with
DM3 `energy_relay_imitation` (a routing correction to the review's older baseline-DM shorthand).
Both remain separate owners. The same published trace interface can serve their declared work;
no App notification, takeover or additional experiment is needed.

### Reusable interface, retention and cost

Keep `experiments/candidates/energy_relay_diagnostics/b01/instrumentation.py`, its focused
regression file, and the optional shared evaluator hook. They expose decision-time legal
observations/current central state, actual head parameters, proposal/submission and post-step
facts, without another actor call or RNG draw. Full-input shapes in the eight archived episodes
are `(3000,8,365)` for legal current/next/held joint observations and `(3000,306)` for current/next/
held central states; the held source/age remain separate. These are **learned-policy trajectories,
not teacher demonstrations**. Future teacher use still declares its information rights and targets.

The fixed batch runner, collector adapter and reading implementation plus their batch-specific
checks have no remaining code consumer after the source scan. Their exact executable versions
remain at [the accepted source commit](https://github.com/CartmanFatass/My-paper-code/tree/ef5c35b77929fbf029d8e2eec9487c1371215bce/experiments/candidates/energy_relay_diagnostics);
[metric definitions](https://github.com/CartmanFatass/My-paper-code/blob/ef5c35b77929fbf029d8e2eec9487c1371215bce/experiments/candidates/energy_relay_diagnostics/b01/readout.py)
remain tied to the immutable result. Remove those unused live files at closure rather than
keeping an unselected executable batch. Preserve all 136 raw archives as the evidence for the
reported identities and native/action findings; intermediate per-world JSON may be removed
only after its exact equality with the retained panel rows is checked. Cleanup measurements
and actual leftovers follow after execution, not as an assumed saving.

Measured cost: 0 new fits/updates, 408,000 native transitions. The internal batch timer is
2444.266127 s (40.74 min); native manifest creation to OS exit is
2506.589619 s (41.78 min), retaining startup/teardown outside that timer.
Parent plus exited-child CPU user/system totals are 9977.904010 s (2.7716 CPU-hours),
with scopes recorded separately in the summary. Maximum observed worker RSS is 1,224,932 KiB;
parent high-water RSS is 468,588 KiB, not a summed concurrent-memory estimate. The original
output allocation is 410,533,888 bytes. Preparation, source synchronization, engineering, review,
readback and publication are additional work not separately metered; they are not zero.

### Closure cleanup and final interface check

The snapshot collector first refused a same-user `/proc/660/cwd` permission gap. The documented
passwordless `--sudo-process-scan` performed only the read-only process probe; a second preview
found the exact snapshot eligible, with terminal witness, no process references and durable
`refs/heads/main` reachability. Apply then removed and unregistered only
`d1edd10948b649f084a7d0f248791c99`. Its allocated bytes fell **794,984,448 → 0**.
The 136 redundant individual JSON rows were compared exactly against retained native panel rows
again before deletion; `per_world/` fell **1,142,784 → 0**. Thus remote deletion targets released
**796,127,232 allocated bytes**, without a backup/archive/copy or relocation of raw evidence.
The complete canonical output now occupies 409,849,856 allocated bytes; its 136 NPZ files remain.
`du` includes directory allocation (raw subtree 408,408,064 bytes), whereas the runner's raw
allocation statistic counts files only (408,379,392 bytes). These scopes are not contradictory.
Claims, manifest, exit witness, config, original summary, six native panels and logs remain.

In local main, explicit `git rm` removed the four finished-batch Python files (`run_b01.py`,
`collector.py`, `study.py`, `readout.py`) and their three batch-specific test files, after the
consumer scan found no outside imports. The recorder, its tests and shared optional hook remain.
Owned bytecode caches, the three obsolete launch/observer scratch files, and redundant local
log/progress copies were also removed; each exact target was checked absent. These local targets
released **258,048 allocated bytes**. Twelve compact result/control files are retained locally
(1,388,544 allocated bytes total); the nine newly collected compact files account for 1,339,392
bytes. Even charging that new collection allocation against cleanup, these measured targets
and copies yield **795,045,888 bytes net decrease**. This is scoped allocation accounting, not a
claim about concurrent whole-host free-space changes or Git object-store shrinkage. No full
worktree backup, tarball, duplicate raw retention or backup chain was created.

After removing the batch-only implementation, the retained instrumentation regression passed
**4 tests in 13.87 s** with bytecode disabled and normal pytest-owned scratch teardown. This
checks the still-live reusable import/observer path; no scientific episode or new fit was bought.
The four observer checks and optional evaluator hook remain supported; historical batch checks
are recoverable at the accepted source SHA. There is no remaining scientific worker, pending
Pro request, unused source snapshot or uncollected result for B01. Consume the terminal native
observer event before returning; there are no remaining running observations to resume.

### Publication and post-sync native-record reconciliation

Scientific result, shared standing and code retirement were published on main at
`27b796888f4c5464bd7ed888fdc6fdce2cdaa747`; the remote branch was verified at that SHA.
The final canonical-node fast-forward was initially deferred for another direction's live
tracked summary. A path-only comparison then established that incoming changes did not touch
those live edits, so the fast-forward completed without clearing them. No excluded result
content was opened, and no other operation was stopped or restarted.

That sparse checkout omitted the three previously tracked B01 control files (manifest, config,
preflight) outside its selected cone. The same native status therefore temporarily reported
unknown/invalid binding, rather than a new scientific exit. Following the documented recovery,
`git sparse-checkout add runs/energy_relay_diagnostics/b01_alignment_a01` restored the exact
published originals and retains this path for future updates. All twelve compact JSON files
were byte-hash matched to the published result commit; the terminal native read again reports
exit 0, valid exit witness, absent recorded processes and consistent records. All 136 raw
archives remain, the snapshot is absent, and the retired entry is absent from the canonical
source checkout. Both then-current unrelated dirty paths were preserved. No witness was
synthesized or edited and no scientific worker was relaunched. Existing unrelated Git auto-GC
warnings and foreign untracked output directories were left untouched.
