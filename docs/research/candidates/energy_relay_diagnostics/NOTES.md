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

## 2026-09-27 — B02 prospective: direct PPO surrogate on fully shielded actions

### Question and adopted scope

Question: from the same published c03 learner state and with the same further PPO budget, does
zeroing only the direct actor-surrogate term for actions fully replaced by the production return
shield change complete closed-loop service or risk? This continues the unresolved training-to-use
question retained after B01; it does not reopen B01's path/saturation recipe. B01's useful
negative evidence remains: its restricted single-lane CPU collector/evaluator path agreed, the
declared horizontal mean-action saturation was absent, and sampled service changed little on
average while return cost and low-battery outcomes worsened. Those observations neither diagnose
the reward/credit path nor make the new intervention a correctness fix.

The selection reuses the complete independent ResearchCritic review and Root decision in
[`RESEARCH-two-successors.md`](../../archive/2026-09-27/RESEARCH-two-successors.md#two-successors-review),
published with main `2905e4f9e3ae74d25dbc01533d46230d0eb89fe9`. No material premise or comparator
changed, so no second scientific-review or Pro round is needed. This PPO question is distinct from
DM3's B02 supervised-label mask: that asks where behavior-cloning capacity is spent; this asks
how a finite reward-driven PPO continuation responds to its actor score terms. Neither result
substitutes for the other. Shared background used: RESEARCH §§1/2 require native team reward and
the full information/history path; §4 separates finite optimizer behavior from representability;
§6 keeps paired episode worlds distinct from training instances and requires controls for component
attribution; §7 says an ended recipe is not proof that the broader question is exhausted. No
claim of a representation ceiling, a general PPO defect, or a multi-seed result is planned.

### Verified c03 learner input

The new arms branch from Claude's published development c03 checkpoint, not from B01 outputs or
the old DM2 run directory. On configured node `wsl_4070`, the canonical input is
`/home/wu/hmasd-artifacts/energy_relay_benchmark/b02_s1_set_a01/checkpoints/c03/`.
Its `agent.pt` is 38,832,967 bytes with SHA256
`80b2bdadddb76a4c03fe9fea8ae9fb1317a136363d28dec0d8fae350745dcce4`; this exactly matches
`record.json`. The record names c03, rollout 100, 600,000 transitions, seed 925031, source launch
`759927b5e8caa0ba5bd8ba505ab5388985f6a2fa`, and policy fingerprint
`4667fdc9df9486167a9820ffc3433a5c6d4b8fe568b21e6fbc3c1326aca4ff3b`.

Before declaring the input, I loaded the checkpoint on that node through the production B02
configuration and `HMASDAgent.load_model`; the full learner fingerprint, coordinator and
discoverer state dicts, actor/critic optimizer state dicts, optimizer counts, ValueNorm mean/var/
count, and rollout-sampler RNG state/seed all matched the checkpoint. Actor and critic Adam steps
are each 225,000; the discoverer ValueNorm count is 4,800,000.0001 (including its 1e-4
RunningMeanStd pseudocount). This is the complete saved learner
state. As in Claude's documented c03 recovery, environment streams and Torch action RNG are
re-seeded at 925131; no environment trajectory state is claimed to be stored in the checkpoint.
The source boundary had both lanes truncated at H=3000, and the learner's inert schedule flags are
off. Each arm independently loads the same c03 input and starts its own reseeded continuation.

### Fixed comparison and estimand

Both arms retain the B02 S7-S2/H3000 recipe, 8 agents, two lanes, 3,000-step rollout/episode,
`k=10`, production shield (enter margin 0, exit margin .05), reward and return-cost coefficients,
network, action law, normalizers, learning rates, minibatch construction and 15 PPO epochs. Each
arm continues exactly 300,000 transitions: 50 rollouts × 6,000 transitions, ending at cumulative
900,000 transitions from the c00 initialization. The ordinary arm uses the existing PPO loss on
all valid actor samples. The intervention arm sets the direct PPO surrogate contribution to zero
only for an agent-step whose production shield mode fully replaces that agent's four submitted
action coordinates. Both are one started fit from the same c03 initialization: **2 fits, 600,000
new training transitions**, one shared-initialization block, not two independent seed replications.
The source c03 update count implies 2,250 optimizer steps per actor and critic per 6,000-transition
rollout; each arm therefore plans another 112,500 steps per optimizer, with actual counts checked
from the native agent.

The shield decision is computed from the current legal margin and previous shield mode. In an
active mode it replaces all four proposal coordinates before `env.step`; equality by chance between
a proposal and its replacement is not used to infer exposure. The intervention mask will be
recorded from the returned production mode and checked against the submitted-action contract.
All observations, sampled proposals, submissions, rewards, GAE rows, critic targets/updates,
ValueNorm updates, entropy, recurrence and recurrent reset behavior remain present. Advantages
are normalized over the original valid PPO rows before the intervention; the masked surrogate is
divided by that same original valid-row count, so filtering does not increase the effective step
size. All minibatches and optimizer steps remain scheduled.

This checks the internal path before execution. Shielding changes the environment action and thus
subsequent observations, rewards, GAE and critic targets in both arms. A fully covered row still
enters actor/critic recurrence and actor entropy; its inputs can affect hidden-state computation and
later unshielded decisions. The mask changes only the current direct policy-surrogate contribution
and then the learner's later parameters/behavior; it does not erase the transition or prevent
downstream state effects. A finite-sample or stale-batch score signal may be unhelpful, but the
surrogate is not pre-labelled erroneous. The strongest simpler explanation for an arm difference
is a different finite update path (including changed gradient scale/clipping) from a single shared
training instance, not a demonstrated general credit mechanism.

After both fixed endpoints, evaluate each endpoint on the same already-declared development
worlds 955001–955032, under deterministic mean action and stochastic draw 0 of the existing fixed
sample-seed rule, at H=3000: 4 cells × 32 episodes = **128 episodes / 384,000 evaluation steps**.
No c03 or intermediate checkpoint is rescored for selection. Read every native per-world J,
QoS/step, return cost, minimum battery, cutoff/depletion/failure and service tail, alongside all
PPO/value/entropy losses, action-surrogate exposure, gradient diagnostics and learner movement
from c03. Report both means and adverse worlds; world episodes/checkpoints do not raise the
training-instance n. These are development worlds, not a holdout or confirmation panel. No
957001–957032 outputs or sealed raw are opened or used for selection.

### Predicted readings and decision rule

The immediate implementation prediction is exact and mechanical: only fully replaced actor rows
lose their direct surrogate summands; critic, entropy, recurrent replay, advantage normalization,
ValueNorm, valid-row denominator and update counts match. Record the number of shield-mode action
rows and their PPO sample presentations, the initial matched minibatch's unmasked versus masked
surrogate gradient norms, per-rollout pre-clip combined actor-gradient RMS/maximum and clip rate,
and actor/critic parameter displacement from c03. These are exposure and scale diagnostics, not
the native outcome. Under either arm, an all-mode row may still affect recurrence, critic learning,
entropy and future policy behavior.

There is no promised positive sign for complete J/QoS. If the masked arm improves the native
service/risk package across the fixed panel without a material low-battery/failure-tail tradeoff,
that supports prospectively pricing an independent training replication. A loss or gradient change
alone, a one-mode mean gain, or a panel mean that hides important adverse tails does not support
"effective control learning improved." If native outcomes do not improve or show an unacceptable
service/risk trade, stop this exact mask scheme; do not add rollout length, change reward/shield,
select a checkpoint, or automatically extend/replicate after seeing scores. This finite comparison
can choose whether a new independent replication is worth its cost; it cannot confirm population
advantage.

### Cost, L0 implementation scope, and stops

Prospective cost: 2 started fits and 600,000 new training transitions, with 50 rollouts/arm and
112,500 expected actor plus 112,500 critic optimizer steps/arm; 128 H3000 evaluations / 384,000
steps. Adopt the independent review estimate of 4.7–5.7 hours total fit time plus 40–60 minutes
evaluation on the configured GPU. Engineering, review, node contention, checkpoint I/O, collection,
readback and publication are additional and must be measured or left unknown, not folded into that
fit estimate. Execute arms sequentially if admission/resource evidence calls for it.

L0 deliverable: a direction-owned B02 continuation/evaluation entry under
`experiments/candidates/energy_relay_diagnostics/b02/`, matching focused tests under
`tests/experiments/candidates/energy_relay_diagnostics/b02/`, and compact output under
`runs/energy_relay_diagnostics/b02_shield_surrogate_a01/` (ordinary, masked, and evaluation
subdirectories). A narrow optional shared learner/buffer
hook may transport the per-agent shield mask into PPO minibatches and zero only the selected
surrogate rows; default training remains off and unchanged. No edit to the accepted benchmark
training/evaluator/collector, prior run snapshots, other directions' owned source, shield, reward,
model, RNG streams or run horizon. Checks must cover sampler-mask ordering, default-off numerical
and RNG identity, exact surrogate denominator/gradient on known tensors, complete override
classification, c03 load verification, unchanged unmasked collector/learner behavior, actual update
counts, and B02 endpoint evaluation identity. A read-only independent `hmasd-reviewer` review is
required for shared learner/buffer numerical, RNG and checkpoint-path changes; acceptance remains
the DM's. Stop before launch if the mask reaches any path beyond the declared actor loss, changes
the default learner path, or the production checkpoint no longer passes its full-state identity
checks; resolve that finding and any needed science-premise change before execution.

### L0 implementation and independent engineering acceptance

The shared buffer sidecar is allocated only when the direction-owned collector enables it. The
collector records the production shield's returned mode and attaches the aligned per-agent row
after normal transition storage; it does not infer replacement from action equality. The learner
uses the original policy loss unchanged when the option is absent. When enabled, the direct
surrogate alone is masked and remains divided by the original count of valid rows; critic, entropy,
GAE, recurrence, ValueNorm, clipping, and optimizer schedule remain in the source path. The
collector and fixed endpoint evaluator are wrapped or called from the direction-owned entrypoint;
the benchmark collector, evaluator, checkpoint and frozen scripts were not edited.

The independent full-path engineering review found no mask, ordering, recurrence, loss-denominator,
default-off RNG/numerics, checkpoint-compatibility, or admission-order blocker. Its two integration
findings were repaired before review acceptance: endpoint ValueNorm validation now compares the
increment from the loaded c03 count (the expected increment is 2,400,000 rows, retaining the
1e-4 pseudocount), and paired summary paths use the evaluator's
`endpoint_deterministic-stochastic/summary.json` layout. Regressions require the expected count
transition 4,800,000.0001 → 7,200,000.0001 to pass, a wrong increment to fail, and both recorded
evaluation summaries to exist.

Post-repair focused checks: 31 passed in 38.93 seconds across the direction tests, discoverer-entry
mask tests, and B02 resume/evaluator tests (18 existing warnings). The tiny real-learner regression
also found bitwise-identical default and instrumented-unmasked update metrics, actor/critic weights,
and Torch/NumPy/Python/sampler RNG states; the masked update changed the actor while leaving critic
parameters and ValueNorm unchanged. `git diff --check` passed. No result-bearing run has started.

### B02 first accepted launch: technical failure before training (2026-09-27)

The first ordinary-arm operation was admitted on `wsl_4070` at source SHA
`d33cbc538509d6897a56c83f6621d40ab2978ae6`, with fresh effective-memory evidence of
13,233,786,880 bytes against the 4 GiB floor. Native admission ref:
`/home/wu/projects/HMASD/.git/hmasd-admission/e835202e976ee8bcde02856905bf3c924c31c65b2d63239221a234a7b130b00a.json`.
The output is retained at
`/home/wu/projects/HMASD/runs/energy_relay_diagnostics/b02_shield_surrogate_a01/ordinary/`.
The accepted process exited 1 before collection or an optimizer update; the native witness
records a valid process-exit termination and the expected summary is absent. Its traceback is
`TypeError: JSONEncoder.__init__() got an unexpected keyword argument 'parse_constant'` while
serializing the production active configuration. The option belongs to `json.loads`; moving it
to that call converts Python's encoded `Infinity` constants into JSON strings, allowing the
strict summary writer (`allow_nan=False`) to serialize the intended active-config record.
A focused regression checks both infinite interruption-cost fields and the production summary
writer. This is a runner defect, not evidence about either arm: 0 training transitions, 0
optimizer updates, and no scientific observation. The accepted operation is not replayed; the
corrected source will use a new published SHA and a fresh output root.

The two successful fits and paired panel therefore move to the fresh root
`runs/energy_relay_diagnostics/b02_shield_surrogate_a02/` (ordinary, masked, evaluation). The
preserved `a01/ordinary` failure remains technical execution evidence and is not counted as a
started result-bearing fit.

The correction was accepted by the independent engineering reviewer: `parse_constant` now
parses the encoded nonfinite config constants at the load boundary, and the strict writer still
receives JSON-safe strings. Focused validation after the repair: the config regression passed on
its own, then the B02 diagnostics, resume, and endpoint-evaluator suites passed **30 tests** with
18 existing warnings in 67.98 seconds. `git diff --check` passed. No training launch has used the
corrected source yet.

### B02 corrected ordinary attempt A02: partial training then technical failure (2026-09-27)

The corrected ordinary operation at source SHA `594fa3b0eaddb66786f5151772c969892b3ad67d` was
accepted on `wsl_4070` at 2026-09-27T10:44:24Z, after a fresh memory-floor pass (14,855,634,944
available bytes vs 4 GiB) and an idle GPU. Native manifest, operation ref, and retained output:

- Manifest: `/home/wu/projects/HMASD/runs/energy_relay_diagnostics/b02_shield_surrogate_a02/ordinary/launch-manifest.json`
- Operation ref: `/home/wu/projects/HMASD/.git/hmasd-admission/d4812de10031ef215d3a9ff116fab90be5c984163260dc8754f26186d470b59c.json`
- Output root: `/home/wu/projects/HMASD/runs/energy_relay_diagnostics/b02_shield_surrogate_a02/ordinary/`

It exited 1 with a valid `process_exit` witness at 2026-09-27T11:43:06Z; terminal status confirmed
consistent native records and absent supervisor/runner. The run summary is `INCOMPLETE` after 21
new 6,000-transition rollouts: 126,000 new transitions (726,000 cumulative), 42 completed H3000 training episodes,
and 47,250 new low-actor plus 47,250 new low-critic optimizer steps (272,250 cumulative each).
Wall time was 3,371.235 seconds. No endpoint checkpoint was written, so these partial rollout
readings do not supply the declared ordinary endpoint or a comparison result.

The traceback ended in shared `routed_core.py::_current_step_communication_cache` while
updating UAV connections: `TypeError: 'bool' object is not subscriptable` at the configuration
signature lookup. The accepted ordinary operation's mask remained disabled in all 21 recorded
rollouts. This is a technical failure during collection, not evidence for or against the
surrogate intervention. A01 and A02 are the two started ordinary-arm attempts so far; A01 failed
before collection, while A02 reached 126,000 new transitions. The masked arm and paired evaluation
remain unstarted. No automatic repeat is made; diagnose the cache failure and record the lead's
next costed decision before another result-bearing operation.

Key artifact SHA256s on the configured node: `summary.json`
`a362ee5968c779347fad2f7ffa188df0ddee8868b0324f34d09b2f9700458f5f`, `progress.jsonl`
`388f4f959fdd0305dfb1b98b0cb79c0ce513bd3383019471a8dbb78a8fdf2088`, `stderr.log`
`1da80a613783af635ed43a624d8ae3fbb96782f1f7fcc552c2a7f29324b8a539`, `process-exit.json`
`4fbc198cf98dd66bfb71a416ee56988c03eac31e12523c594a833f370f57eaa9`, and `launch-manifest.json`
`9ada417f49a3cdd7b3e0780ac4e28a72711a282c56a61c5b53ab9cefb7c83e98`.

### B02 A02 cache-failure engineering diagnosis (2026-09-27)

The independent engineering reviewer inspected the published source at `594fa3b0eaddb66786f5151772c969892b3ad67d`
and the traceback. It found no tracked boolean writer for `_step_communication_cache`: the reviewed
cache lifecycle resets it to `None`, leaves it `None` when caching is disabled, and stores a
dictionary after a successful refresh. The failing configuration lookup is a second cache read in
the UAV-to-UAV SINR path; the reviewed intervening operations do not replace the cache. The runtime
origin of the observed boolean therefore remains unresolved. Injecting `None`, `False`, and `True`
reproduced only the exception behavior, not how the production object acquired that value.

The reviewer also found that silently treating an invalid cache as `None` could select scalar
path-loss/SINR calculations instead of cached radio tensors and could alter threshold crossings,
topology, and later transitions. No fallback or core-cache code change is made. The current evidence
does not justify restarting either fit; the comparison remains incomplete with no masked arm or
paired endpoint. Before another result-bearing operation, require a targeted diagnostic/reproduction
proposal and record its incremental cost and lead decision. This is an execution decision, not a
scientific-negative result.

### L0: B02-local malformed-cache diagnostic probe

The accepted snapshot imports the exact `routed_core.py` bytes recorded above, and the launch
environment removes `PYTHONPATH`/user-site overrides; the manifest's control SHA is a descendant
of the accepted B02 SHA. Tracked cache assignments in that source produce only `None` or a dict.
The failure is on a second cache read in UAV-to-UAV SINR after the first read and path-loss lookup;
the runtime boolean writer remains unknown. Do not infer a shared root cause or edit the shared
environment file while another direction owns concurrent diagnosis.

Deliverable is a direction-owned, per-environment diagnostic wrapper in
`experiments/candidates/energy_relay_diagnostics/b02/training.py`. Before delegating to the original
cache getter, it records bounded recent reads and requires the value to be `None` or a dict. For any
other type, including `False` or `True`, it raises a specific invariant error before the original
getter can return an invalid value through the channel-update active branch or subscript it. The
error includes lane, lane seed, environment step, getter ordinal, cache type/value/identity, active
flag, environment class/source path, and recent read history. The wrapper is installed only on the
training environments created by this direction's B02 collector and restored with the factory in
`finally`. Valid `None` and dict paths delegate unchanged. No fallback, cache clear/rebuild, shared
environment edit, reward, observation, radio formula, RNG draw, or learner path change.

Checks: `False`/`True` injections with the channel-update active flag both off and on,
asserting the controlled error and its preceding-read evidence; valid `None`/dict delegation; the
existing communication-cache checks; and independent engineering review. Budget for this L0 is zero
result fits and zero result-node hours; use the configured local scientific runtime and report
measured test time. This is diagnostic-only, does not restart A02, and does not authorize another
training operation or the frozen pair. If the probe does not make the failure materially easier to
localize, stop and preserve the concrete unknowns; price any separate diagnostic run before
admission. A02 has no resumable endpoint.

### B02-local malformed-cache probe: diagnostic result and execution boundary (2026-09-27)

The new focused probe regression passed twice, most recently **2 passed in 10.34 seconds** on the
configured local scientific interpreter. It injects both booleans with the active-cache flag on and
off, verifies the preceding dictionary read and runtime identity fields, exercises valid `None` and
dictionary delegation, and checks factory, feedback, getter and agent-method restoration after a
collector exception. The initial combined run exposed a `NameError` in the new error builder; the
builder was corrected before the final passing run. The independent engineering reviewer found no
material issue and confirmed that the valid path delegates unchanged without RNG or transition-state
mutation.

The unchanged shared `tests/scenario7_channel_cache_test.py` had **six passes and two failures** in
the combined run; rerunning the two failures in isolation reproduced both. Cached-versus-uncached
reset observations fail exact equality, and the channel-cache test differs in 31 of 240 SINR cells
with maximum absolute difference `5.68434189e-14` (maximum relative difference
`3.77374346e-14`). No changed route or threshold crossing was measured. The shared environment file
was not edited. This evidence does not prove a deployment consequence, but it rejects claiming
bitwise cached/scalar equivalence and gives no basis for silently switching radio paths on a bool.

The probe diagnoses the first malformed getter read, not the assignment that wrote the bool. The
writer and why it appears after the first UAV-to-UAV cache read remain unknown; no safe recovery is
established. Do not run either frozen arm under a fallback or treat this as a negative result.

A possible next observation is one fresh, separately declared ordinary-only diagnostic from the
published c03 checkpoint with seed `925031`, using the probe and stopping after 22 rollouts / 132k
transitions. It would have no endpoint, masked arm or paired evaluation and would claim only whether
the invalid read recurs with lane/step/read-history evidence. A02 required 3,371.235 seconds for 21
completed rollouts / 126k recorded transitions; linear scaling gives about **58.8 minutes of runner
time** for 22 rollouts. Reserve 65–75 minutes of node wall for the operation; source preparation,
admission, review and other setup remain unmeasured. Any operation requires a fresh source SHA and
output root. This diagnostic has not been launched or admitted; its getter probe alone still cannot
name the writer, so add and review writer tracing first if that is the required decision-changing
evidence.

## 2026-09-27 — Owner-requested B02 re-audit: original evidence and corrections

This re-audit covers this replacement session's B02 implementation, A01/A02 interpretation,
cache probe at `7416b8e4e439454ed3c89679fd8664d5dcb4910d`, and proposed further investment.
It reads original outputs and the executed path rather than treating the preceding summaries as
proof. The owner's model correction motivates scrutiny; a model label neither invalidates data
nor validates this new reading. No new result-bearing operation is selected by this audit.
Current main was refreshed at `e8ddd930779bccf11101a0c981da73c0f545bb24`. Relevant background:
RESEARCH §§3/4/6 and the current UAV cooperative-planning plan require a useful same-information
comparison, distinguish finite optimization from a new planning mechanism, and retain training
instances as the inference units. The original two-arm protocol remains historical evidence.

### Original records independently reread

The configured node's A01/A02 manifest, exit witness, stderr, config, summary and all 21 recorded
A02 rollouts/progress rows were read directly. A02's summary/progress/stderr/exit/manifest hashes
still match the five hashes above. The source c03 `agent.pt` was rehashed directly: 38,832,967
bytes and `80b2bdadddb76a4c03fe9fea8ae9fb1317a136363d28dec0d8fae350745dcce4`; its original
record still identifies seed 925031, rollout 100, 600k transitions and 225,000 actor/critic
optimizer steps each. The collector, shield, learner, buffer and shared cache files inspected
on current main have no diff from their accepted A02 versions at `594fa3b0e`.

- A01 is a pre-training runner failure at `json.dumps(..., parse_constant=str)`. Moving
  `parse_constant` to `json.loads` is a real configuration-serialization repair. It supplies
  zero training fits/updates; count it as a separately retained launch failure.
- A02 is one failed started fit: at least 126,000 completed-rollout transitions, 42 completed
  H3000 training episodes and 47,250 new updates per actor/critic optimizer. A subsequent
  partial rollout is not accounted by those saved counts. Runner wall is 3,371.234690 s;
  acceptance-to-exit wall is 3,521.871189 s. `checkpoints` is empty and the output directory
  has no checkpoint directory. No masked fit or paired endpoint evaluation exists.
- All 21 records have `direct_surrogate_mask_enabled=false`. Fully overridden rows total
  277,992/1,008,000 = 27.5786%. Every recorded actor update clips at the configured norm .5.
  The direct-gradient ratio .7452307 is **one initial 320-row minibatch probe**, including
  74 overridden rows, copied into later rollout records; it is not 21 independent probes,
  a gradient-variance measurement, or a native-benefit result.
- Reaggregating B01's original development-panel JSON gives sampled-draw-0 c03-minus-c00
  QoS +.0978517013 and native J +290.7285980, with 6 QoS-loss and 8 J-loss worlds out of 32.
  Thus the ordinary learner demonstrably changed usefully in this one historical instance.
  B01's two-draw-averaged sampled-minus-deterministic J +1.218844 and return cost +7.745681
  remain intact. Neither observation identifies a shield-credit bottleneck, and neither is
  a substitute for the missing continuation pair. No sealed holdout was used in this audit.

### What the implementation actually estimates

The source path is `b02/training.py::collect_and_train` ->
`uav_service_auxiliary/b06/feedback.py::apply_feedback` -> `store_transition_batch` ->
`RolloutBuffer` recurrent sampler -> `HMASDAgent.update_discoverer_from_rollout`.
The actor samples a tanh-Gaussian proposal; the production shield reads current legal margin,
previous mode and station geometry. Its mode decision is independent of the current proposal,
and an active mode replaces all four proposal coordinates. The environment receives that
submitted command. Replay retains the sampled proposal and its original log probability,
alongside the actual resulting team reward. The actor uses current legal observations plus
the held central snapshot refreshed at k=10; the critic uses the existing state path. The mask
adds no actor input, future label, privileged planning query, reward or transition modification.
The inspected recurrent input does not feed this sampled proposal back as a previous-action input.

Writing M=1 for full override, the direct actor objective is
`-sum((1-M) * min(r*A_normalized, clip(r, .8, 1.2)*A_normalized)) / D`, where D counts all
original valid action rows. Modes, rows and proposal likelihoods remain aligned through the
same recurrent chunks. GAE, the critic, ValueNorm, entropy and recurrent processing are retained.
Those *procedures* match; after policies diverge, their future data, critic targets and parameters
need not remain numerically equal.

Condition on pre-action history (including the shield state) and the other proposals. With
complete, action-independent replacement and no separate proposal-dependent reward/memory,
the physical consequence is constant in this UAV's proposal u. Under the usual score-function
regularity, `E[Q * grad log pi(u|history)] = Q * grad integral pi(u|history) du = 0`.
This explains a possible variance-reduction opportunity. Ordinary proposal-based policy gradient
is still a legitimate estimator for the composed policy-plus-shield system. Multi-epoch clipped
PPO with sampled normalized advantages and a retained proposal-entropy term is a different finite
optimization object; the identity is not a proof of lower training variance, larger native return,
or correction of a generally erroneous gradient in this implementation.

The closest verified primary method is Eisenach et al.,
[Marginal Policy Gradients, §4.2, Lemma 4.5/Theorem 4.6](https://arxiv.org/html/1806.05134v3):
it marginalizes proposal distinctions erased by the execution map. The fully overridden
coordinate is a constant-map special case of that idea. Fujita and Maeda's
[CAPG, §3](https://proceedings.mlr.press/v80/fujita18a/fujita18a.pdf) is the neighboring bounded
clipping case; its tail probability correction is not this whole-action mask. The
[PPO clipped surrogate](https://arxiv.org/pdf/1707.06347) explains why an ideal policy-gradient
identity does not assert equality of the finite clipped objectives. These sources bound the
novelty claim; they provide no new UAV result.

### Targeted checks and explicit corrections

Configured local scientific Python, existing owned B02 tests plus the two disputed shared
cache tests, `--basetemp temp/directions/energy_relay_diagnostics/test/reaudit-20260927`:
**13 passed, 2 failed, 14 warnings in 21.68 s**. The passing scope includes stored-mask axis
order/RNG, the actual small learner update, default versus instrumented-unmasked identity,
actor-only masking on the matched batch, production-mode capture even when actions coincide,
config serialization, endpoint contract, and cache guard/restoration. This is local focused
verification, not production learning or universal numerical equivalence.

1. **Correct the denominator claim.** The earlier sentence “so filtering does not increase
   the effective step size” is too strong. D is unchanged, so there is no automatic retained-row
   renormalization. Removing cancelling terms can nevertheless increase the gradient, and Adam,
   clipping and the relative entropy contribution further change the update. Exact FP64 arithmetic
   with two row derivatives `(1, -.9)` and D=2 gives .05 unmasked versus .5 retaining only the first.
   Another four-row enumeration uses an own Bernoulli proposal independent of reward sign ±1,
   all proposals fully overridden, old p=.5 and PPO epsilon=.2. At new p=.5 the mean clipped
   objective and derivative are both zero; at p=.7 they are -.1 and -1, whereas the masked direct
   contribution is zero. These deterministic calculations explain the estimand boundary; they
   are not a performance experiment or a new empirical variance claim.
2. **Correct “reset observations differ.”** The first existing cache test compares the entire
   reset tuple and stops at its first assertion. A read-only pytest failure hook compared its
   actual captured locals: `OBS_ARRAY_EQUAL True`; the only differing leaves were all eight
   `reset/1/infos_dict/uav_i/reward_info/graph_potential` values, `.6712486810265368` versus
   `.6712486810265367`. Cache types were `dict` and `NoneType`. The follow-up ran the same
   existing test once in `reaudit-reset-20260927`, 4.86 s, preserving its expected failure.
   Its later five-step routing/RNG assertions were not reached. The earlier claim of unequal
   observation arrays is withdrawn; equality of the full returned structure still fails.
3. The second shared test again differs in 31/240 SINR cells, maximum absolute
   `5.68434189e-14`, maximum relative `3.77374346e-14`. Both tests are local **S7-S1** checks,
   not the failed S7-S2/CUDA continuation. No threshold/route consequence or bool-production
   mechanism follows from these tiny floating-point differences. A01's serializer bug, A02's
   malformed object and these cache numerics are three distinct findings.
4. The `7416b8e4e` guard raises before the original getter's active-cache shortcut on a
   non-None/non-dict value and restores its wrapper on exception. It records a bounded history
   of eight reads, lane/seed/step, type/value/id, class and getter module/file. It does **not**
   capture the assignment, prove live bytecode/native-library identity from a file path, or
   repair the runtime. The three recorded cache lifecycle assignments at A02's source produce
   None or a dictionary. The bool's origin remains unknown. Reproduction by injecting a bool
   establishes guard behavior only. No silent fallback is justified by this audit.

### Cost and the next-investment comparison

A successful mask package could supply a reusable training recommendation for controllers whose
commands are fully replaced by a fixed supervisor. It adds no joint path representation,
lookahead consequence model, allocation/hand-off decision, communication rule or new information.
Its current mathematical idea is already covered by action marginalization; a UAV planning
contribution has not been demonstrated. The internal same-information ordinary baseline is the
same c03 SET PPO plus the same shield, information cadence and training exposure. B01 supplies
conditional evidence of its learnability, not proof of optimal tuning. Ordinary gradient-scale,
entropy and clipping choices are stronger competing explanations for a finite package gain;
the frozen two-arm design does not separate them. A planning-level claim would additionally
need a competent planner at the same information/refresh contract; an unmatched historical
central teacher cannot supply that comparison. Other current leads already own concrete
cooperative-planning and from-scratch baseline questions.

The contemplated 22-rollout/132k getter-only repeat would be **one additional started fit**,
even if called diagnostic. Linear extrapolation of the uninstrumented failed prefix is about
58.9 runner minutes. The probe's per-read overhead is unmeasured, so the previous 65–75 minute
reserve is not a verified upper bound. The committed runner actually fixes 50 continuation
rollouts; a 22-rollout contract would require new implementation/checks/admission. It would
buy recurrence and read locality, with no endpoint comparison and no writer provenance.

A complete replacement pair would instead cost 2 new fits, 600k transitions, 225,000 actor and
225,000 critic updates in total, and 128 H3000 evaluation episodes/384k steps. The prior
4.7–5.7 training hours plus 40–60 evaluation minutes remain an estimate; repair/instrumentation,
startup, contention, storage, collection and reading are additional unknown costs. With A02,
cumulative started training would be 3 fits and at least 726k recorded new training transitions.
One shared c03 initialization and exposed development worlds would remain the scientific limit.
The investment disposition and the one fresh independent scientific review are recorded below.

### Independent scientific review and disposition

The fresh ResearchCritic `b02_direction_reaudit` used a separate context with no inherited
conversation. It reconstructed the raw B01/A01/A02 records, collector/shield/replay/learner
path and relevant primary methods before reading the current proponents' summaries. The
earlier partial-failure critique had a narrower scope and disclosed prior-context exposure;
it is retained as historical advice, not counted as this independent reconstruction. The
reset-local inspection above is a DM-observed follow-up supplied to the reviewer; the reviewer
did not claim an independent repeat of that runtime inspection. No additional Pro question
was needed for this decision, and none was sent.

The complete substantive recommendation was **REVISE**, with these reasons and boundaries:

- Preserve the narrow finite-PPO optimization question and the competent ordinary PPO + same
  shield comparator. The action-independent full-replacement premise is supported on the
  inspected path. The ideal score identity does not make ordinary proposal gradients wrong,
  prove the clipped update harmful, or establish a new cooperative planner. A02 supplies no
  scientific sign for or against masking. B01's ordinary learning and all adverse worlds stay.
- Reject the getter-only 22-rollout repeat as the next purchase. Recurrence would locate an
  invalid read; nonrecurrence would show only a successful prefix. Neither establishes the
  mutation source, a repair, or masking value. If engineering is later worth buying, a bounded
  observation should offer actionable mutation provenance, a narrow causal interval or a
  concrete repair. Exhaustive root-cause explanation is not a permanent scientific prerequisite;
  the actionability and cost of the presently available route are simply unestablished.
- A complete paired continuation could still be worthwhile modest exploration once there is
  an economical executable route and a concrete optimization use. One shared c03 and exposed
  development worlds bound the result. Gradient scale, entropy and clipping remain alternatives
  to a mechanism claim, but a third scalar-control arm is **not** a prerequisite for the modest
  original two-arm package comparison.
- If a future newly selected pair improves complete J/service in both declared modes with
  acceptable tails, first price fresh independent training replication. Loss, incomplete
  benefit or adverse tails ends the exact scheme according to its fixed rule; a technical
  failure still supplies no scientific sign. There is no automatic retry or follow-on fit.
- Under the current UAV cooperative-planning priority, this is supporting optimization.
  It does not earn an automatic debugging allocation or become the main planning contribution.

**MATERIAL_DISSENT: yes** — against purchasing the getter-only 22-rollout repeat and against
the claim that an unchanged denominator prevents a larger effective update. **DM disposition:
adopt both objections and the narrower interpretation.** No material disagreement remains.

**Current choice: materially revise; move `energy_relay_diagnostics` to `reserve` and end
the current B02/cache investment.** The question remains scientifically untested. Withdraw
the 22-rollout proposal and the effective-step-size guarantee; correct the reset-observation
claim as above. Do not select a replacement pair, repair project, new fit or diagnostic run.
The useful present result is the corrected estimator/implementation boundary, verified failure
account and investment judgment. Existing evidence does not identify a valuable, economical
next purchase for this question now. This is a present decision, not a pending approval or an
instruction to wait for a repair. A future prospective revision may use new executable evidence
and a concrete downstream need; no continuation is queued or automatically triggered.

The original lead and observer-interface ownership remain unchanged. The generic learner hook,
the owned B02 reference implementation and their focused checks remain available to interpret
the accepted source and the still-unanswered optimization question. The two failed operations
are reconciled; no live result operation or unread Pro answer remains. The audit added no
scientific fit or result-bearing rollout. Its focused checks and exact algebra are reported
above; the engineering/review time was not instrumented and is not claimed as zero cost.

### Compact publication and actual retirement

Copied and byte/hash-verified the exact original A01 manifest, acceptance status, process exit
and stderr, and A02 config, summary, manifest, acceptance status, process exit and stderr into
the matching local `runs/energy_relay_diagnostics/b02_shield_surrogate_a0{1,2}/ordinary/`
paths. These ten files contain 114,307 bytes and occupy 159,744 allocated bytes including their
directories. **`launch-status.json` is the original acceptance snapshot**, not a new terminal
query: its `accepted` field does not override the exit witnesses, A02 summary, or absent native
processes. The remote original progress/stdout and compact records remain at their declared
output roots; no checkpoint, full worktree or bulk retention package was copied.

Both exact launcher source snapshots initially refused retirement only because of four ignored
`scripts/__pycache__/*.pyc` files each. After checking the exact dirty list and absence of live
process references, removed those eight rebuildable files. Used the maintained node collector
`scripts/hmasd_snapshot_gc.py`, preview then exact-ID apply, with `--sudo-process-scan` for its
read-only inspection of protected same-user processes. Both previews and applies passed all
terminal identity, claim/source consistency, external-output and durable-source-ref checks.
No authoring worktree, claim, manifest, exit witness or run output was removed.

| Exact source snapshot | Allocated bytes before cache/source deletion | After | Directory / Git registration |
| --- | ---: | ---: | --- |
| `513b60e6c9fe41788e7990d1df24a66b` (A01, source `d33cbc5385`) | 797,786,112 | 0 | absent / absent |
| `4aa584ec81254e89a73defccfac2d923` (A02, source `594fa3b0ea`) | 797,855,744 | 0 | absent / absent |

The source targets therefore released **1,595,641,856 allocated bytes**. Subtracting the
159,744-byte local compact publication copy gives **1,595,482,112 bytes of net reduction across
these measured paths**; this is not a measurement of whole-host free capacity or Git object
storage. Concrete retained node outputs occupy 28,672 bytes (A01) and 229,376 bytes (A02).
After deletion, all ten compact source files and A02 `progress.jsonl` were rehashed unchanged;
the accepted c03 checkpoint remains in its original artifact store. There is no leftover
source snapshot from these two operations.

The final wait drain has generation 4, `events=[]`, `wake_id=null`, `delivery=null`, and only
the reconciled A02 job in terminal `failed` state with valid exit 1 and absent runner/supervisor.
No observations remain to rearm. This collection and retirement did not restart a worker,
resend a Pro question, or message another App task.
