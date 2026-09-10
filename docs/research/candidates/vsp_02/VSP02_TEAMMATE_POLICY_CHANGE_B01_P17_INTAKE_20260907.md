# VSP02 B01 P17 — scientific intake of seed1117 and both independent prefixes

**VALID_COMPLETE / WITHIN_MEI, B/EXPLORE.** Seed1117 gives CARRY7.8564453125 and
RESET7.84765625 native deliveries per adaptation episode: **Delta RESET minus CARRY
= -0.0087890625**, or nine fewer deliveries for RESET over1024 episodes. Seed1103 remains
+0.0185546875. Both are inside the unchanged absolute MEI0.5, with opposite signs. Their
descriptive mean is+0.0048828125; it does not replace either primary or establish equivalence.

P17 is complete. This intake adds no run, third seed, evaluation, source change or Pro request.
The accepted binding remains other-agent non-stationarity/partial observability with fixed N2,
identities and roles. Recasts remain1; member recovery, tuned new-host headroom and a unique
optimizer mechanism remain unresolved. No C object is consumed and no UAV claim follows.

## 1. Assignment and evidence checked

Root returned CM technical PASS at `02f0a2a2f3610919730006b3e988756e97a348b2` for full scientific
intake under P17, main `a787ff12cd0212b9fd23d9d861d5d192186028fe`. The authoring checkout
`C:/Projects/HMASD-worktrees/dm-vsp02`, branch `codex/vsp02`, was clean at the CM commit.
The current Portfolio row remains ACTIVE/LOW; this intake changes no lifecycle or priority.

The prospective contract is [card](VSP02_TEAMMATE_POLICY_CHANGE_B01_SCIENCE_CARD_20260907.md)
§§1–7,9 and [P17 amendment](VSP02_TEAMMATE_POLICY_CHANGE_B01_P17_AMENDMENT_INTAKE_20260907.md)
§§1–3 at `e69208359cf9914d6a7555e379c95b17f02afed1`. Exact execution source is separately
`19be5ee18393913ff92693cdf037213ec1777510`, with unchanged code-spec §§2–5. Evidence-spec
§§4,5.2,11.4,11.8.2–3,11.8.6–7 control. No C-class burden or retrospective card change is added.

DM read the full [P17 E0](VSP02_TEAMMATE_POLICY_CHANGE_B01_P17_RESULT_EVIDENCE_20260907.md)
and its [JSON](VSP02_TEAMMATE_POLICY_CHANGE_B01_P17_RESULT_EVIDENCE_20260907.json), including
primary/count/completeness, fork/movement, runtime, admission and supervisor records. DM checked
the original raw training/evaluation returns, independently computed the new full-window primary,
all native bins and sampled checkpoint readings, and visually inspected the published curves.
CM's retained row/order/update/finiteness/source checks supply engineering acceptance; DM did not
rerun those suites, import the trainer or replay either run.

Seed1103's already accepted [intake and analysis](VSP02_TEAMMATE_POLICY_CHANGE_B01_INTAKE_20260907.md)
are reused unchanged. The scientific-tools run summarizer received exactly four rows: one
full-window native score per arm for each of1103/1117, with `--paired --baseline CARRY`.
[P17 intake analysis](VSP02_TEAMMATE_POLICY_CHANGE_B01_P17_INTAKE_ANALYSIS_20260907.json)
retains the rows, tool output, all1117 bins/checkpoints, descriptive slices, actual exposure and
resource arithmetic. It generates no scientific trajectory. Technical conformance and scientific
effect are evaluated separately below.

## 2. Rules applied verbatim and both primaries

Card §1:

> Primary per-arm AUC is the sum of the **1024 actual post-change training-episode native returns divided by1024**; Delta is RESET minus CARRY.

Card §6, the applicable branch for both results:

> Inside the MEI, report the actual sign and absence of a difference at this scale, not equivalence.

Card §9, the prospective two-prefix summary rule:

> An unweighted mean of the two complete paired differences may be reported descriptively; it
> does not replace either per-prefix primary, establish stable superiority or make episodes into
> independent training samples.

| Independent prefix | CARRY sum /1024 | RESET sum /1024 | CARRY mean | RESET mean | Delta RESET minus CARRY |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1103 | 7648 | 7667 | 7.46875 | 7.4873046875 | +0.0185546875 |
| 1117 | 8045 | 8036 | 7.8564453125 | 7.84765625 | -0.0087890625 |

P17's negative primary is -9/1024, exactly matching the published result. Its magnitude is
1.7578125% of MEI. Seed1103's positive magnitude remains3.7109375% of MEI. Both windows are
complete; neither has an MEI-sized difference. A positive first seed is not retained as the sole
result, and a positive average does not erase the second seed's native loss.

The permitted unweighted mean paired Delta is **+0.0048828125** (0.9765625% of MEI).
Mean arm scores are CARRY7.66259765625 and RESET7.66748046875. Paired sample SD is
0.01933495104806966, with observed range[-0.0087890625,+0.0185546875]; these are descriptive
statistics from n=2, not a reliable population uncertainty estimate or a significance test.
No confidence interval, equivalence test, selected seed/checkpoint or pooled-episode inference
is used. One prefix and its whole pair are one independent training unit; evaluations and bins
are not additional seeds. B/EXPLORE has no consumption state.

## 3. Curves, adverse outcomes and bounded scientific meaning

Seed1117's old-prefix sampled endpoint is8.375, shared post-switch q0 is4.671875, and the
prefix's last256 native episodes average7.9609375. The visual record shows service returning
toward its previous level in both descendants. The endpoint/q0 contrast also changes regime,
notification bit and evaluation stream; it does not isolate the causal teammate-switch effect.

| Post-change episodes completed | Sampled CARRY | Sampled RESET | RESET minus CARRY |
| --- | ---: | ---: | ---: |
| 16 | 6.109375 | 6.171875 | +0.0625 |
| 32 | 7.546875 | 7.453125 | -0.09375 |
| 64 | 7.640625 | 7.5 | -0.140625 |
| 128 | 7.625 | 7.609375 | -0.015625 |
| 256 | 8.125 | 8.0625 | -0.0625 |
| 512 | 7.546875 | 7.546875 | 0 |
| 768 | 7.859375 | 7.84375 | -0.015625 |
| 1024 | 7.75 | 7.703125 | -0.046875 |

P17 has a small terminal RESET loss; the positive q16 evaluation is not substituted for that
endpoint or the native primary. Seed1103 retains its equal terminal means8.234375 and intermediate
RESET losses at q64/q128. Across1117's64 native16-episode bins,12 deltas are positive,13 negative
and39 zero. The first16 native means are equal5.1875; outcome-informed slices give first128
Delta-0.078125 and remaining896 Delta about+0.00111607. These slices describe the complete
observation and are not new primaries, independent samples or a selected late-window benefit.

Both1117 fork models match PREFIX exactly in the logged parameter comparison, at global
progress4096. CARRY keeps10 Adam entries at step4096 with prefix moments; RESET has zero
entries/moments/steps. Both finish at global5120; Adam steps are5120 CARRY and1024 RESET.
Initial parameter RMS is0.076406329870224. Actual RMS displacement is0.0019241179106757045
after the first16 updates,0.07071450352668762 at prefix end, and0.020302623510360718 CARRY /
0.02527695521712303 RESET from fork. First-rollout displacement is about2.5183% of initial RMS.
The accepted instrumentation supports real updates and the intended fork; CSVs do not
reconstruct tensors. RESET's greater parameter movement again does not imply useful service gain.

The causal path tested is unchanged: a persistent courier changes actual movement/delivery
actions; the receiver owns movement/receipt using equal legal local history and notification;
native trajectories train recurrent PPO; complete Adam history alone changes at a shared
learned start; actual post-switch service supplies the consequence. There is no join/leave,
replacement, slot reassignment, survivor transfer, variable duration or partner co-adaptation.

**Strongest support:** two complete independent-prefix comparisons with actual native windows,
nonzero learning and the intended equal-information/state fork. The second observation preserves
the within-MEI scale while showing that the small first-seed RESET sign does not persist.
**Strongest contradiction to useful RESET benefit on this tested configuration:** both effects
are tiny relative to the predeclared0.5 scale, the signs oppose, and1117 has native and terminal
sampled RESET losses. The data do not support an MEI-sized advantage on either observed prefix.

Across these prefixes, CARRY's means differ by0.3876953125 and RESET's by0.3603515625, much
larger than either within-prefix difference. This is a descriptive two-run contrast, not a
population variance conclusion. Generic warm-start optimizer transience, recurrent inference,
critic/step-count effects and learner-start variation remain live alternatives. The scripted
teammate can be absorbed into an ordinary changing environment; event-specific attribution and
a unique reset mechanism are not established. No-change or component controls are not added
retrospectively as conditions on these valid B observations.

New-host tuned-baseline headroom and competent-comparator qualification remain absent; service
near8 does not prove effective use of all available information. The declared0–16 reward range
is not a measured headroom record. Historical matched greedy headroom0, B5R1's equal exact-success
sets and its nonidentical continuous values remain unchanged. Neither old sign nor old quarantine
is reinterpreted. Prior verified local-library evidence, MARL-0495 / Zhai et al. IJCAI2023
DOI10.24963/ijcai.2023/39, page2 paragraphs120–121,125, continues to support legal recent-action
history, not Adam-reset benefit. The1117 outcome is inside its prospective range and changes no
comparator or mechanism design, so no new retrieval or novelty claim is made.

Claim ceiling: two observed independent prefixes on this fixed host/learner/P4096/Q1024 budget.
No stable superiority, equivalence, competent-baseline dominance, unique/event-specific Adam
effect, member recovery, transfer, UAV validation or whole-direction negative is established.

## 4. Actual exposure, receipts and resources

P17 contains6144 complete training episodes /294912 training joint steps /384 rollout batches /
6144 Adam calls and1152 complete evaluation episodes /55296 evaluation steps, totaling350208
joint steps. Both completeness flags are true; error, stopping reason and missing outputs are
empty. All E64 checkpoints and the single shared q0 are present. Four PPO passes reuse data
without adding interaction. P15 and P17 together contain12288 training episodes /589824 training
steps /12288 Adam calls, plus2304 evaluation episodes /110592 evaluation steps:700416 total
joint steps and2359296 PPO transition-passes. The machine-generated combined exposure line is:

`environment_transitions=700416; optimizer_steps=12288; evaluation_episodes=2304; model_selection_trials=0; result_bearing_invocations=2; independent_training_pairs=2`.

CM collection and DM intake each add zero scientific exposure. Prior engineering fixtures and
the five implementation-comparison arms remain separately recorded, not extra training seeds.

P17 source is19be5ee18393913ff92693cdf037213ec1777510, contracte69208359cf9914d6a7555e379c95b17f02afed1,
node `wsl_4070`, handle `vsp02-tpc-b01-p17-s1117-a1`, PID2755975. The exact detached cwd is
`/home/wu/hmasd-worktrees/vsp02-tpc-b01-p17-s1117-a1`; runtime remains CPU FP32, one intra-op/
inter-op thread, CPython3.10.21 and torch2.7.0+cu118. Fresh admission at
2026-09-08T02:53:03.394607Z passed with physical/effective available memory each15661023232 bytes,
above4294967296. The original runner shell places that receipt immediately before the runner.

The supervisor contains one start10:53:03 and exit10:53:40 +08:00,37s, finished/exit0/tmux inactive.
Whole runner wall, including imports through publication, is36.07172741298564s under the1800s
whole-pair cap. Peak RSS is518434816 bytes (494.41796875MiB), resources_unmeasured=false.
The six raw files remain under `temp/directions/vsp_02/exp/teammate_policy_change_b01_p17_s1117_a1/`
locally and in the remote exact-source checkout. Admission is under
`temp/directions/vsp_02/exp/admission/tpc_b01_p17_s1117_a1.json`; supervisor receipts are under
`temp/directions/vsp_02/exp/supervisor/vsp02-tpc-b01-p17-s1117-a1/`. E0 JSON embeds the original
summary, admission, supervisor and collection facts. No missing evidence or dependent primary
limitation under §11.8.7 was found.

The two valid pairs sum to72.76788033498451s runner wall and75s admission/runner chain wall;
runner wall per valid pair is descriptively36.383940167492256s. The7693s calendar span from
the first scientific start through the second completion includes allocation/control-plane gaps;
it is not continuous learner runtime or aggregate CPU work. Per-arm wall, aggregate CPU and full
historical direction cost remain unmeasured. The two whole-pair caps were separate; no unused
allowance grants another invocation. P15's earlier zero-second wrapper no-op remains attributed
and preserved only in P15; P17 has no such segment and no repeated accepted launch.

Engineering-scope §4 machinery needed: none. No source/test change, repeated fixture, runtime
guard, new telemetry or section5 budget breach is introduced or accepted as a price of this
result. Process exit and technical PASS alone are not mechanism value.

## 5. Predictions and owner surfaces

Seed1117's prospective DM interval[-0.5,+0.5] contains its negative primary. Seed1103's original
Pro-derived working interval also contained its own result. Score: both individual recorded
intervals cover their observation, but1117's forecast was informed by1103 and is not an
independent prediction. No sign forecast or forecast-calibration claim is added. Owner prediction:
**not taken (unattended)**. Current main/direction reviews returned[] and relevant audit owner
cells are empty; no owner instruction needs applying or marking answered.

The [Chinese result brief](../../portfolio/owner/briefs/vsp_02/2026-09-07_VSP02_TEAMMATE_POLICY_CHANGE_B01_P17_S1117.md)
preserves both signs and the terminal loss. Ordinary acceptance and prediction facts remain in
this intake/audit. The separate next-task recommendation below is published as a P1/P2 owner
proposal because it asks Portfolio to plan a direction-level question; it makes no scientific
disposition and does not wait for an owner reply. Owner flag for that proposal: portfolio.

## 6. Decisions this intake produces

### Object tier — accept both outcomes at the stated ceiling

Options: (a) accept1117 as valid within-MEI and retain the two-prefix descriptive result;
(b) return a concrete comparison-threatening defect to the same CM; (c) suppress the negative
seed or treat the small average as superiority/equivalence. Recommendation and executed choice:
**(a)**. All card-dependent evidence is complete and no defect requiring(b) was found; (c)
violates the predeclared all-outcome reading. **Owner-delegated decision (unattended, 2026-09-03
instruction): (a).** No B consumption or direction-family closure is recorded.

### Object tier — complete P17 and return the exact next-task need

Options: (a) complete P17 and return a bounded future Convergence task on the current fixed-member
family; (b) recommend more unchanged-seed expansion; (c) select a new mechanism/host, exact
diagnostic or C/UAV promotion locally. Recommendation and executed choice: **(a), return only**.
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** The observations provide
no MEI-sized RESET benefit on either prefix; further unchanged-seed expansion is not recommended
from this intake. Inexpensive execution alone is not an effect or a reason for indefinite repeats.
The existing B result remains valid without exact causal diagnosis or a tuned upper reference.

Exact next-task need through Root to Portfolio: a new, bounded question to
`em:vsp_02:convergence` on whether to continue or end the **accepted fixed-member
teammate-policy-change family**, using both complete outcomes and their claim ceiling. If it
continues, the node should name what new observation would change the decision; absence of a
stronger unrequested C claim must not be used as a negative. DM advises against further
unchanged-seed B01 expansion and against performance/UAV promotion on these data. It does not
declare the family closed, parked or recast; those direction-tier choices remain unmade.

This is an out-of-scope next-task recommendation, not a new Pro packet, Issue, Send, third seed,
new B card or Portfolio disposition. A prospective consultation can cite the existing exposure
line with zero new learning/evaluation; its external-model cost is unmeasured. It is required
only if a family disposition is requested, not as a universal gate on an independently authorized
B. P17 authorizes no further scientific or Pro invocation. Root returns the recommendation for
Portfolio's next concrete command; it is not asked to select or interpret the science.

Audit rows are `docs/research/portfolio/audit/2026-09-07.md#L95` (technical acceptance) and
`#L96` (next-task recommendation) at this authoring revision. Owner proposal: `docs/research/portfolio/owner/inbox/2026-09-07/20260907-vsp02-004.json`
(recommendation only; no auto-applied future review or family disposition). All results are retained and processes are terminal; no runtime
repair or unresolved technical gap remains. The unresolved direction-tier question and original
member-recovery agenda are separate from these two bounded B observations.
