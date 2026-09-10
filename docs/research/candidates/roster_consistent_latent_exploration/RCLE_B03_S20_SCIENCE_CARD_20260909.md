Claim to test: on one fresh independent training seed, claim-score weight 100 again reduces post-event unmet demand relative to weight 1 after the same 200 FLEX updates, with every native tradeoff retained.
Binding MARL structure: multi-agent credit assignment.

# RCLE B03 actor100 fresh-pair S20 science card — 2026-09-09

**B/EXPLORE; complete S20 batch explicitly allocated by Root on 2026-09-09.**
The scientific freeze remains `2da8ec66be12da255e69721d0bdc672ce07edc33`, with accepted
read-only feasibility `17aa7f01533887750b74a6ca62465e67b41a4580`.
Reporting object `RCLE-TBCFV-B03-ACTOR100-S20`. Root's allocation is main
`fb4f3e0ae9058675162bcb183f34182a969a935f`, final RCLE section of
`docs/research/portfolio/decisions/2026-09-09-synthesis-execution.md`.
Sections 2–6 retain the frozen law/counts/caps; §7 records the subsequent allocation.
No scientific invocation has occurred at this allocation binding.

## 1. Question, reason to spend and claim ceiling

The next observation asks whether the small native benefit and fragmentation tradeoff
recur in a genuinely new matched training pair under the same learning laws and budget.
This is one new training seed with two fresh fits, not additional evaluation of the old
policies. It is outcome-informed B exploration, not prospective confirmation of a
population claim. The old seed-19 pair was selected for recovery after its W1 and failure
were observed; the new pair is chosen after seeing its completed positive result.

The [recovery intake](RCLE_B03_RECOVERY_RESULT_INTAKE_20260909.md) at
`2299d09d30f3ed63d333ca17a02a067aa5cbae15`, §§2–7, reports Delta_U +0.0132242839,
below the fixed 0.05 MEI, with both primary paths and all eight U/Y means favorable.
Every learned recovery score was 40; fragmentation worsened in all four final-roster-12
cells. The simple reference was much stronger. These facts make one bounded pair worth
considering, while deferral remains a close runner-up; preserve owner item
`20260909-rcle-004`. The previous card's “end this spend” branch has been applied. This
newly selected pair has its own count and cap, not an extension or unspent old allowance.

Evidence spec §§5.2 and 11.8.1–3 permit this small follow-up without a diagnostic, exact
upper, causal proof or prior positive replication. Another training seed directly
observes a different learning instance; an exact gradient census would not answer that
question. The [selection intake](RCLE_B03_S20_SELECTION_INTAKE_20260909.md) records the
options and delegated choice. No family, lifecycle, priority, recast or Pro decision is
made. Neither two favorable seeds nor significance would establish stable superiority,
a pure actor-credit cause, general roster robustness or a C conclusion.

## 2. Fixed host, learning laws and comparator

Reuse [original B03 card](RCLE_TBCFV_B03_ACTOR100_SCIENCE_CARD_20260909.md) §§2–5 at
`9c729fb7b675c3d21b35815fa7e46cf6444fa3af`. Only the selected independent seed/root changes;
the same actual native host, legal information, model, loss, return, update and panels
remain. Implementation base is the accepted recovery source
`4e89f24197a79d0b4fc724018f0223ca2c1e4289`; subsequent result/docs commits change no law.

The native chain remains: tick-24 roster event → physical entities and survivor state
→ public set summaries and own features → FLEX plan update and six-way claim sampling
→ complete-episode score-gradient training → movement and normalized unmet demand.
Membership is an unordered physical-agent set, without persistent policy slots. Current
rank is recomputed; survivors retain physical state, newcomers receive only prescribed
event pulses. This is one event, not leave/rejoin, replacement or censoring research.
The four-tick claim clock and 64-tick undiscounted complete return remain. Shared-policy
partner co-adaptation is endogenous to each arm; no future or private clue is added.

Both arms use the same 26,161-parameter FP64 FLEX-REKEY model, fresh Xavier/zero-bias
initialization, and initially zero cell baselines. Current deterministic FLEX-head
derivatives remain live. For each balanced 64-episode block, retain
`L_lambda = -mean_e stop(Y_e-b_cell(e))*(s_M,e + lambda*s_A,e)`, with the original
separate episode-mean manager/claim scores. W1 uses lambda 1; W100 uses lambda 100.
One backward computes the joint gradient; a nonzero gradient takes one full-vector
norm-0.02 step, then the 0.95/0.05 cell-baseline update occurs. A zero gradient is recorded,
not replaced or retried. Reward remains complete-return Y, not post-event U.

Two hundred blocks × 64 episodes per arm use the unchanged eight training cells:
`6→6, 10→10, 6→10, 10→6` × ACTIVE_CONTINUATION/NEW_EPOCH, eight episodes per cell/block.
Keep all 200 curves per fit. No altered weight, baseline, optimizer, normalization,
entropy, schedule, architecture, group step, batching, gradient decomposition or grid.
Weight 100 changes the normalized joint direction, not parameter motion by a factor of
100; shared encoders, manager/FLEX heads, baselines and visitation can all mediate it.

## 3. Fresh seed, actual random addresses and old-contract preservation

Select master **20**, block **0**, in the existing scientific RNG namespace
`RCLE-TBCFV-B03-ACTOR100`. Reporting suffix `S20` is outside random addresses. The new
root is SHA256 of ASCII `RCLE-TBCFV-B03-ACTOR100/seed/20`:
`065798a1a4115ac244accada16fc267f814deb622cfd05b9657418892c656e3b`.
The original seed-19 root remains
`4b17629c25d71afceed93bbe657c0b5799d468d1f5673d90a7ceee644ec474c5`.
These values are computed from the actual source convention in the
[machine-generated plan](b03_actor100_s20_20260909/EXPOSURE_PLAN.json), without model calls.

Both new arms use the same fresh root and semantic coordinates, with true RNG package
FLEX-REKEY. Keep distinct training/evaluation purpose domains and the existing initializer,
cell/scenario, manager and actor derivations. W1/W100, lambda, source SHA, execution order,
output path and S20 reporting label never enter random addresses. The new root changes
initialization and native/policy random inputs relative to seed 19; matching within the
pair is justified by actual generating conditions, not the number 20 alone. Different
policies may produce different trajectories, baselines and visited states.

The current CLI parses only seed 19 and does not pass it into `run`; the study root and
metadata also use a module constant. Merely changing the CLI label is insufficient.
The allowed future source change is the smallest explicit seed propagation through
`run`/`make_rng`, actual root derivation and emitted metadata, retaining seed 19 as the
existing default and unchanged old-wrapper inputs. The implemented CLI must accept
19/20 and pass its parsed seed into the real computation. Add a separate `--reporting-object` argument
(default original OBJECT_ID) for summary `object`; S20 commands supply the S20 label.
That argument cannot enter root or semantic address construction. Do not globally
monkeypatch constants or create a new RNG framework. CM's [accepted read-only feasibility](RCLE_B03_S20_FEASIBILITY_20260909.md)
§§1–3 traces these exact consumers through initialization, scenario, manager and actor
inputs and final metadata; no missing native seed argument or shared-host change was found.

Both S20 fits start at update 0 with the same newly generated initial tensors and zero
baselines. No old initial/final tensor, fitted control, baseline or unknown failed prefix
is loaded. W100's `--control-summary` must point only to this new S20 W1 summary, whose
shared initialization/final panels supply G_U and Delta_U. No historical W1 summary is
staged. Preserve the original seed-19 cards, source bindings, output roots and failed
attempt. Summary `object` reports S20 while `seed=20`, actual root and authority block digest
identify its generating inputs. The RNG namespace remains the original B03 constant.
The existing control loader and index matcher do not themselves verify seed identity;
the fixed fresh-W1 path, one supplied-fixture primary-input check and actual result
identity inspection cover that concrete risk. No runtime provenance validator is added.

## 4. Panels, primary, reading rules and predictions

Run one shared new-initialization FLEX panel, one new W1-final panel, one new W100-final
panel and one unchanged INDEPENDENT-NEAREST reference panel. Each uses the fresh seed-20
held-out domains: `8→8, 12→12, 8→12, 12→8` × both conditions, 256 episodes per cell.
W1 owns initialization once. Evaluate learned endpoints only after update 200. The
reference keeps the nearest-beacon/smaller-index tie rule; its unavailable Y stays null
with the existing reason. No extra panel, intermediate checkpoint or old evaluation reuse.

Primary: the equally weighted ACTIVE_CONTINUATION 8→12 and 12→8 means of paired-scenario
`U_W1−U_W100`, positive for W100. Preserve all assigned indices, both arm/path levels,
each arm's init gain G_U, 40U, tau/fraction tau=40, all eight U/tau/Y/F cells and the
secondary eight-cell mean. U is mean unmet demand over ticks 24–63; tau is failure-coded
at 40. F is allocation fragmentation, not a reward. NEW_EPOCH is not a pure memory erasure.

The new primary is read on seed 20 alone. Show the old recovered seed-19 result alongside
it, including every old failure/cost and the four F losses; do not pool evaluation rows
across seeds or select a favorable seed/cell. Per-path SE and its equal-path combination
follow original §5's actual independent cell domains. These intervals are conditional
scenario uncertainty. If both pairs complete, there are two paired training units;
per-seed outcomes can show recurrence or instability but do not establish stable
training-population uncertainty. No all-seeds-positive or significance continuation gate.

**MEI remains absolute U=0.05**, two normalized unmet-demand ticks in the 40-tick window,
for the original reason. Tau 4 is only a descriptive tradeoff scale. **Headroom H_A1 is
still unidentified.** The recovered reference U 0.2860636 versus W100 U 0.6911112 leaves
a 0.4050476 diagnostic gap, not an upper-minus-tuned-generic record. Observation, action,
information and budget match the existing host/reference set, so reuse it on the fresh
scenarios; no baseline tuning or new headroom prerequisite is included.

How the result will be interpreted: an effect above MEI would add a larger local native
signal, with all losses and the old small result retained; a smaller positive result
would support recurrence at a small scale only. Zero/adverse sign would expose variation
or a counterexample to the forecast. Native learning without a law advantage, recovery
saturation and F losses remain separate. After this finite pair, recommend the next
question from the actual outcomes/cost; none of these readings automatically allocates it.
Apply all nine original §5 branches verbatim; overlapping rows remain simultaneous:

| Complete observation | Reading and possible recommendation |
| --- | --- |
| Delta_U≥0.05 without a same-scale reverse native tradeoff | W100 service signal on this seed/budget; consider a separately selected fresh pair, without stable or causal claims. |
| 0<Delta_U<0.05 | Small local positive signal; judge another named comparison using path outcomes, G_U and actual cost. |
| Delta_U=0 or -0.05<Delta_U<0 | No positive W100 signal; retain the exact zero/adverse value and Monte Carlo ambiguity. |
| Delta_U≤-0.05 or a material service/recovery loss | Counterexample to this fixed weight at this budget; a justified independent replication may test recurrence. |
| abs(Delta_U)<0.05 and either arm G_U≥0.05 | Native learning without a same-scale law advantage; name the improving arm. |
| abs(Delta_U)<0.05, both G_U small and tau saturated | No useful benefit shown by this 200-update comparison; end this spend and return to object selection. |
| Favorable primary with W100 G_U≤0 | Report relative benefit and absolute deterioration together; do not call it improvement from initialization. |
| Opposite paths, U/tau tradeoff or intervals crossing interest scales | Mixed/undecided; retain all paths and companions, with U=0.05/tau=4 as descriptive scales. |
| Damaged training, information or primary readout | Report the actual failure and counts; only independent narrower facts survive. No algorithmic polarity. |

**New DM predictions before implementation/execution:** low confidence that
`0<Delta_U<0.05`; strongest alternative is Delta_U≤0 from training-instance variation or
amplified/displaced credit. Delta_U≤0 refutes the positive forecast; Delta_U≥0.05 supports
its sign but refutes the small-size forecast. Predict tau=40 in a majority of assigned
scenarios for each learned arm. Separately, with low confidence, predict positive mean
W100−W1 F across the four final-roster-12 cells, using the already required cell outputs;
this is a companion prediction, not a new primary or a gate. Preserve all four signs.
No new Pro prediction is invented. Earlier forecasts retain their original scores.
Owner prediction: not taken (unattended) unless an actual reply arrives before execution.

## 5. Selected topology, exposure and prospective complete cost

The selected fixed list has **three separate scientific interpreter invocations**:
W1 (fresh init + 200 blocks + init/final panels) → W100 (fresh init + 200 blocks + final,
paired to new W1) → reference. A single detached supervisor may own this sequential list;
there is no parallel arm team, nested search or automatic retry. Each actual invocation
has its own fresh same-node admission joined to its runner by `&&`; any failure stops
the list. Poor finite returns or tau saturation do not stop training or skip W100.

| New work if explicitly allocated | Episodes | Primitive ticks | Backward/step calls |
| --- | ---: | ---: | ---: |
| Two arms × 200 × 64 training | 25,600 | 1,638,400 | 400 |
| Two final panels, each 8 × 256 | 4,096 | 262,144 | 0 |
| One shared initialization panel | 2,048 | 131,072 | 0 |
| One reference panel | 2,048 | 131,072 | 0 |
| Total | **33,792** | **2,162,688** | **400** |

W1 owns 16,896 episodes/1,081,344 ticks; W100 owns 14,848/950,272; reference owns
2,048/131,072. The unchanged initializer allocates six model objects per learned
invocation: 12 total, comprising two fits and ten untrained helpers; reference has none.
Dominant work is 2 arms × 1 fresh seed × 200 × 64, plus four fixed panels. Six legal
claim candidates are scored, with no joint-action/trajectory/beam/coefficient search.
The source uses two 32-episode batches per update (800 across both arms), and eight
32-episode batches per cell/panel (256 across four panels). These are episode-batch
evaluations, not a count of underlying native kernel calls. A future changed-seed check
is added validation, not part of those scientific counts.

Machine-generated exposure line: **26,161 parameters per fit; 200 joint step calls;
each nonzero step has norm 0.02; summed path-length opportunity ≤4 per fit**. Actual
nonzero/zero counts, initial norm and final displacement are measured in the charged
invocations; path length is not net displacement. Fresh initialization norm is not yet
measured, and no extra probe is required to obtain it. Scientific exposure now is zero.

Known B03 history remains 33,792 episodes/2,162,688 ticks/400 calls plus the old failed
W100 prefix, unknown within 12,800 episodes/819,200 ticks/200 calls. If S20 completes,
known cumulative work is 67,584/4,325,376/800 plus that same unknown prefix; nominal maxima
80,384/5,144,576/1,000 are bounds, not observed totals. Scientific allocations then total
30: five started fits (one old failed, four complete) plus 25 helpers; the four complete
endpoints form two paired seeds. Earlier objects' exposure is not erased or folded into
this named B03 accounting window.

Selected prospective caps, validated against the read-only topology: **600s per complete learned
invocation, 30s reference, 1,500s complete new object**, including startup/build,
initialization, training, evaluation, preparation, at most one ≤30s focused seed-wiring
check, collection/merge and publication. If each sublimit is used, 240s remains for other
support; no cap resets across scripts or source revisions. Record sum of complete
invocation walls and study critical path separately, charge shared work once, and report
unmeasured overall/CPU windows honestly. No calibration run or profiler is allocated.

Prior complete W1 79.24s + recovered W100 70.95s + reference 2.59s = 152.78s is a planning
reference only; roughly 150–200s plus necessary support is plausible, not a future bound.
The failed 53.20s prefix is not a throughput estimate. The named previous conservative
CM/DM window remains 261.3980053s; adding this prospective cap gives 1,761.3980053s for that
named window, not full-history wall/CPU cost or new authority to spend an old remainder.

## 6. Route, observation, stops and engineering scope

Retain remote-first **wsl_4070, CPU FP64, one compute thread**, configured interpreter
and native ABI. No device/node/fallback or interpreter change is selected. After actual
allocation and source acceptance, commit/push before detached exact-SHA execution under
configured `agent-task`. Each invocation requires physical/effective available memory
≥4 GiB immediately before its runner. No remote worktree or input stage is created now.

CM sends `MONITOR_ADD` directly after the accepted shared supervisor handle, resolving
Monitor from live `C:/Projects/HMASD/.codex/hmasd-monitor.toml`; name W1→W100→reference,
three fresh admissions, 600/600/30 limits and the whole-object cap. CM stops routine
polling and returns pending collection. Root confirms actual adoption; a message alone
is not adoption. Monitor observes the whole handle and sends terminal facts to Root,
which resumes the original CM for collection/technical acceptance. A failed adoption
returns to Root without a duplicate observer or launch. DM then performs scientific intake.

Normal completion is both 200-block fits, all four panels and publication. Stop for
actual cap/admission failure, fatal/nonfinite output or a concrete reward/information/
RNG/training/readout defect. Preserve every partial count and completed block; within-
block progress may remain unknown. A failed W1 cannot supply the pair, so stop the list.
Missing initialization limits G_U; missing reference limits that comparison and whole-
card completion; independently trustworthy final Delta_U remains reportable under §11.8.7.
Optional resource telemetry alone is `resources_unmeasured`. No automatic recovery,
replacement, additional pair or mechanism diagnosis follows any outcome.

**Engineering scope §4 needs:** reuse the existing standard-library fatal-stack capture
in each of the three interpreter logs, because signal 11 remains unresolved. The existing
completed-block JSONL publishes the already required 400 curves (200 per fit), one flush
per completed block; it adds no new metric, checkpoint/resume or logging framework.
No historical-input byte manifest is needed because no old fitted control is reused.
No other §4 machinery is selected. Existing seed/root fields describe actual algorithm
inputs, not tamper evidence or an extra runtime gate. No native/ctypes/GC repair is selected.

Future implementation scope is the existing B03 study/runner's seed/reporting propagation,
one fixed S20 command list, and one focused changed-boundary check plus independent
semantic review. The check uses supplied fixtures/fakes to exercise default/explicit 19,
actual 20 propagation and post-learner primary publication with distinguishable old/new
W1 inputs; no scientific model/native smoke is required. Inspect actual producer consumers
and the fresh-W1 path in review, then both new initial tensors and root metadata in result
acceptance. Reuse the same available CM/reviewer; no extra role or check layer is introduced.
Preserve source ≤2,000 added lines, runner ≤600 lines and the directory's ≤300s test budget;
the selected focused check ceiling is ≤30s within the complete object cap. Reuse accepted
loss, step order and native evidence; a new launch does not justify repeating them.
A necessary semantic change or an unaccounted invocation returns as a concrete conflict.
All work stays in `C:/Projects/HMASD-worktrees/dm-rcle-a02-20260906`, branch `codex/rcle`.
CM owns implementation/technical acceptance only after Root's concrete allocation; DM
owns the card and scientific intake. No additional owner approval is requested.

## 7. Explicit allocation and handoff — 2026-09-09

Root accepted feasibility/card/intake into main `bb3854c61`/`7296b485d` and allocated
the complete batch at `fb4f3e0ae9058675162bcb183f34182a969a935f`: minimal study/CLI
seed and reporting wiring, fixed fresh-W1 command list, one supplied-fixture focused
check ≤30s within the remaining directory allowance, independent semantic review,
then exactly the three sequential remote invocations and full technical/scientific
intake. Main audit rows 177–178 map the preceding selection rows 135–136; Root's later
allocation/owner-item trace remains in main and is not overwritten from this checkout.
There is no extra Root source gate after CM acceptance and exact committed/pushed source.

The same CM owns this complete batch in the existing `codex/rcle` authoring checkout.
Before transfer, DM synchronized only the committed applicable operating instructions
from the allocation SHA; this input-only commit does not introduce governance changes.
CM resolves the Monitor from the live primary path in §6, directly registers the accepted
shared handle, records dispatch separately from adoption, and returns pending collection.
Root confirms adoption and later resumes that same CM at terminal. No DM parallel polling.
Source SHA, command, handle, receipts and actual cost will be published in the CM/launch/E0
records; they cannot be filled from this allocation alone.

At handoff, no S20 source edit, check/model/native call, preflight or experiment has run.
Carry a conservative **15s DM preparation charge inside the 1,500s cap** for the short
allocation-input reads, synchronization and document/Git publication commands. Actual
known prior B03-directory focused checks total 14.3754106s + 5.0949401s = 19.4703507s;
CM reconciles any further recorded spend before using the selected ≤30s S20 check, without
resetting the 300s directory allowance. This arithmetic and existing receipts are enough;
no new cost probe is selected. Subsequent support is charged once and the chain is bounded
by the remaining allowance with collection/publication reserved. The same 600/600/30s
invocation caps, zero retry/replacement/extra panel or successor, and dependency-based stops
remain. A failed invocation does not regain its allowance through a new source SHA.
