# VSP02 teammate-policy-change B01 — P15 scientific intake

**VALID_COMPLETE / WITHIN_MEI, B/EXPLORE.** On the one seed1103 prefix/pair, full Adam RESET
delivered 7.4873046875 native services per adaptation episode versus CARRY's 7.46875. The primary
RESET minus CARRY difference is **+0.0185546875**, or 19 deliveries over 1,024 episodes, inside the
predeclared absolute MEI of 0.5. This is a valid local observation, not equivalence or stable
superiority. The P15 allocation is complete; this intake adds no scientific invocation.

Binding structure: other-agent non-stationarity and partial observability, with fixed N=2 and
persistent entity identities/roles. The accepted recast remains `recasts: 1`; member recovery is
unresolved. No direction or Portfolio disposition, C consumption or UAV entry follows.

## 1. Assignment, authority and evidence checked

P15 at main `25b1a88b162ae137b5071ca2d9acb87007fb3ea9` allocated exactly one complete pair.
Root's return route supplies CM's technical PASS at `12a419e8e05a8ea8270dc71a4605746d5c779b4c`,
integrated on main `a2470e7f8959c5f336b88339e7c9b2b858d22ebc`, for scientific intake only.
Authoring checkout `C:/Projects/HMASD-worktrees/dm-vsp02`, branch `codex/vsp02`, was clean at that
CM evidence commit. The current Portfolio row is ACTIVE/LOW; only Portfolio controls that row.

The scientific binding is the [science card](VSP02_TEAMMATE_POLICY_CHANGE_B01_SCIENCE_CARD_20260907.md)
§§1–8 at launch `19be5ee18393913ff92693cdf037213ec1777510`, the
[code specification](VSP02_TEAMMATE_POLICY_CHANGE_B01_CODE_SPEC_20260907.md) §§2–5, and
[P15 readiness](VSP02_TEAMMATE_POLICY_CHANGE_B01_P15_READINESS_20260907.md) §§1–5.
Evidence-spec §§4, 5.2, 11.4 and 11.8 control the interpretation; the card's reading rule is
unchanged. No new Pro round is needed for ordinary object-tier intake inside the accepted family.

DM checked the complete [E0 evidence](VSP02_TEAMMATE_POLICY_CHANGE_B01_RESULT_EVIDENCE_20260907.md)
and its [JSON](VSP02_TEAMMATE_POLICY_CHANGE_B01_RESULT_EVIDENCE_20260907.json) against those bindings:
actual primary windows, counts, fork/movement measurements, runtime, admission and dispatch
receipts. DM read the original summary and raw training/evaluation/curve data, independently
computed the full-window comparison and descriptive curves with stdlib Python, and viewed the
published PNG. The existing scientific-tools `summarize_runs.py --paired --baseline CARRY` was
applied to a two-row table containing exactly one full-window score per arm for seed1103.
[Intake analysis](VSP02_TEAMMATE_POLICY_CHANGE_B01_INTAKE_ANALYSIS_20260907.json) preserves its
output, all 64 native bins, all sampled checkpoints and the declared independent unit.

CM's focused raw-row/update/RNG/fork checks and the prior accepted implementation review supply
technical evidence; DM did not repeat the implementation suite, run a fixture, import the trainer
or replay the experiment. Technical PASS is separate from the bounded scientific reading below.
This is existing result collection/intake, excluded from new CM engineering comparison enrollment.

## 2. Rule applied verbatim and primary observation

Card §1:

> Primary per-arm AUC is the sum of the **1024 actual post-change training-episode native returns divided by1024**; Delta is RESET minus CARRY.

Card §6, the applicable branch:

> Inside the MEI, report the actual sign and absence of a difference at this scale, not equivalence.

The independence limit in evidence-spec §11.8.3 is also applied verbatim:

> One training seed cannot estimate training-seed population uncertainty;
> resampling units must respect shared data, folds and actual independence.

| Native training window | Complete episodes | Return sum | Mean deliveries/episode |
| --- | ---: | ---: | ---: |
| Prefix | 4096 | 28126 | 6.86669921875 |
| CARRY adaptation | 1024 | 7648 | 7.46875 |
| RESET adaptation | 1024 | 7667 | 7.4873046875 |

Delta is 19/1024 = +0.0185546875, **3.7109375% of the absolute MEI**, and descriptively about
0.2484% of CARRY's mean. The relative value is not a new decision threshold. Both full native
windows, all training updates and required evaluations are complete; both completion flags are
true and no required output is missing. No selected checkpoint, evaluation interpolation or
post-hoc window replaces the full adaptation-service primary.

The independent unit is **one learned prefix and its whole CARRY/RESET pair**. There is n=1,
not two independent arms, 2,048 independent trained policies or 16 independent checkpoints.
The run-summary tool reports sample SD as null and supplies no confidence interval. No
episode-level bootstrap or bin-level significance claim is made.

## 3. Complete curves, learner movement and scientific meaning

The old-prefix sampled endpoint is 8.125; shared post-switch q0 is 3.953125. This is a descriptive
change across different evaluation streams, teammate regimes and the notification bit, not an
isolated estimate of the causal policy-switch effect. The prefix's last 256 native episodes average
7.9296875. Both descendants subsequently return to roughly the same sampled service level.

| Adaptation episodes completed | Sampled CARRY | Sampled RESET | RESET minus CARRY |
| --- | ---: | ---: | ---: |
| 16 | 4.5625 | 4.671875 | +0.109375 |
| 32 | 4.6875 | 4.734375 | +0.046875 |
| 64 | 6.53125 | 6.4375 | -0.09375 |
| 128 | 7.265625 | 7.171875 | -0.09375 |
| 256 | 8.1875 | 8.234375 | +0.046875 |
| 512 | 7.671875 | 7.75 | +0.078125 |
| 768 | 7.859375 | 7.859375 | 0 |
| 1024 | 8.234375 | 8.234375 | 0 |

All intermediate losses are retained. Among the 64 non-overlapping native 16-episode bins,
RESET minus CARRY is positive in 18, negative in 6 and zero in 40; bins share learner history and
are not independent replications. Outcome-informed descriptive slices give first-128 Delta
+0.0703125 and remaining-896 Delta +0.0111607143. They describe where this already observed total
arose; they were not predeclared alternative primaries or selected as evidence of superiority.

At the fork, both models have maximum parameter difference zero from the prefix and identical
global progress 4096. CARRY keeps ten Adam state entries at step4096 with prefix moments; RESET
has zero entries/moments/steps. Both finish at global progress5120, with Adam step5120 versus1024.
The first16 prefix updates move parameters by RMS0.0023259019944816828 from initial RMS
0.07666852325201035. Prefix-end displacement is0.06980965286493301; post-fork displacement is
0.019422367215156555 CARRY and0.02313823625445366 RESET. These numeric measurements support real
learning and the intended intervention. Greater RESET movement did not produce an MEI-sized
service difference. The CSVs do not reconstruct tensors; these readings rely on the accepted
instrumentation and prior focused checks, as disclosed by E0.

The event-to-consequence chain is intact: the persistent courier changes its actual endpoint
actions; the receiver owns movement/receipt using only its local history and the public change
bit; complete native trajectories train recurrent PPO; only retained Adam state differs at the
common fork; adaptation service supplies the primary consequence. There is no roster change,
join/leave/rejoin, replacement, slot reassignment, survivor transfer or variable-duration claim.

**Strongest support:** a complete real-learning matched comparison with nonzero optimizer
exposure, equal starting parameters/information and directly observed native service. It supports
the local tiny positive RESET sign and feasibility of this bounded CPU invocation.
**Strongest contradiction to a useful RESET benefit here:** the difference is only19 of the512
deliveries defining MEI, terminal sampled values coincide, and intermediate RESET losses occur.
The result supplies no MEI-sized advantage on this pair.

Generic warm-start optimizer transience remains the strongest explanation class: the scripted
teammate can be absorbed into a changing environment. Recurrent inference, critic adaptation,
step-counter effects and single-prefix variability also survive. The observed service and
parameter movement do not qualify a tuned competent comparator or prove the policy exploits the
available light/history effectively. No-change or component controls would answer separate
attribution questions; none is retrospectively required to accept this B performance fact.

New-host tuned-baseline headroom remains absent. The declared reward range0–16 is not a newly
measured upper-minus-tuned-baseline record. Historical matched terminal greedy headroom0 and B5R1's
equal exact-success sets C=R={U03} remain unchanged; B5R1's descriptive CARRY minus RESET about
+0.003792 with one negative pair uses the opposite subtraction convention and transfers no sign
to this host. No historical quarantine or evidence boundary is lifted.

Reuse of P11's verified local-library evidence is sufficient: MARL-0495, Zhai et al., IJCAI2023,
DOI10.24963/ijcai.2023/39, page2 paragraphs120–121 and125, supports the legal recent-action-history
design. This expected within-MEI result requires no new comparator, mechanism recast or retrieval
sweep. The evidence continues to support the information choice, not Adam-reset benefit or novelty.

Claim ceiling: one fixed-host, fixed-budget B training pair. No equivalence, stable population
superiority, isolated event-specific or unique Adam mechanism, competent-baseline dominance,
member recovery, partner co-adaptation, transfer, UAV entry or deployment conclusion.

## 4. Exposure, receipts, cost and engineering boundary

The machine-generated analysis line records:

`environment_transitions=350208; optimizer_steps=6144; evaluation_episodes=1152; model_selection_trials=0; result_bearing_invocations=1; independent_training_pairs=1`.

This comprises6144 complete training episodes /294912 joint steps /384 rollout batches /6144
actual Adam steps, plus1152 complete evaluation episodes /55296 joint steps. The shared q0 is64
episodes once; each of eight later checkpoints has64 episodes per arm. Four PPO passes give
1179648 transition-passes, not extra interaction. The five earlier engineering implementations
are not scientific arms or replications; their retained exposure is separate in the preparation
and readiness records. DM intake adds zero transitions, updates, evaluations and invocations.

The accepted source is `19be5ee18393913ff92693cdf037213ec1777510`, remote node `wsl_4070`, handle
`vsp02-tpc-b01-p15-s1103-a1`, detached cwd
`/home/wu/hmasd-worktrees/vsp02-tpc-b01-p15-s1103-a1`. CPython3.10.21 / torch2.7.0+cu118 executed
CPU FP32 with one intra-op and one inter-op thread. Runner wall, including imports through
publication, is36.69615292199887s; the supervisor admission/runner chain is38s, within the complete
1800s cap. Peak RSS is520306688 bytes (496.203125MiB); `resources_unmeasured=false`. Aggregate CPU
time and full historical direction cost are unmeasured, not zero. This result's cost is36.696s
runner /38s chain for one valid pair; it is not a retroactive pre-launch affordability projection.

Fresh on-node admission at2026-09-08T00:45:27.993526Z passed with physical/effective available
memory each15634575360 bytes, above4294967296. The archived command joins admission immediately
to the runner. Original raw outputs remain under
`temp/directions/vsp_02/exp/teammate_policy_change_b01_p15_s1103_a1/` in the direction checkout;
admission is under `exp/admission/tpc_b01_p15_s1103_a1.json` and supervisor records under
`exp/supervisor/vsp02-tpc-b01-p15-s1103-a1/`, relative to the same direction temp root.
E0 JSON embeds the summary, admission, inventories and source of the checks; raw CSV and PNG
bytes are retained locally and remotely. PID2754886 is finished, exit0, tmux inactive.

There were **two supervisor starts and one scientific invocation**. The earlier08:44:43 +08:00
start exited0 in0s without preflight or runner text. Root attributed it to a PowerShell quoting
error sending an empty/truncated chain and observed no admission, model, output root or scientific
exposure. DM read the archived log/runner/status and Root's recorded clarification: the zero-second
empty segment is directly visible; the no-exposure observation remains explicitly attributed to
Root. The corrected identical payload ran08:45:27–08:46:05 +08:00. No failed scientific attempt,
retry result, quarantine or negative polarity is manufactured from the wrapper no-op.

Engineering-scope §4 machinery needed by this intake: **none**. The card requested none; no
unrequested machinery or section5 source/runner budget breach is present in the accepted delivery.
This intake changes documents only and starts no CM assignment, test, admission, experiment or
resource sweep. Learner-side instrumentation and the primary are complete; §11.8.7 introduces no
dependent limitation here beyond the disclosed inability to recover tensors from CSV.

## 5. Prediction, owner flags and reviews

The prospective Pro working prediction Delta in[-0.5,+0.5], adopted on the card before launch,
contains the observed +0.0185546875. Score: **inside the predicted interval on this one pair**;
one covered value does not establish forecast calibration. Owner prediction: **not taken
(unattended)**. Owner-console reviews on main and the direction checkout returned[] at intake;
the VSP02 audit owner cells contain no new override, so no review needs marking answered.

Owner flags: none. Material limitations are the single prefix, absent new-host tuned headroom,
generic-transient alternative and tiny primary with retained intermediate losses. No critic
dissent, close-call, second recast, new card or direction/Portfolio decision is produced. Ordinary
valid-result and object decisions stay in this intake/audit; no separate owner item is created.
The [Chinese owner brief](../../portfolio/owner/briefs/vsp_02/2026-09-07_VSP02_TEAMMATE_POLICY_CHANGE_B01.md)
reports the result and next-task boundary without requiring an owner reply.

## 6. Decisions this intake produces

### Object tier — scientific acceptance

Options: (a) accept the complete B result as a within-MEI local comparison; (b) return a concrete
comparison-threatening defect to the existing CM; (c) treat the tiny positive sign as superiority
or the small difference as equivalence. Recommendation and executed choice: **(a)**. All primary
counts and receipts match the card; no defect requiring(b) was found, and(c) exceeds n=1 and the
unchanged MEI rule. **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
This records B evidence; A/B have no consumption state and no C object is consumed.

### Object tier — next discriminator recommendation and clean return

Options: (a) finish P15 and return one fresh independent prefix with the same comparison as the
specific next-task recommendation; (b) finish P15 without a follow-up recommendation; (c) spend
work on repeated evaluations of seed1103 or an exact causal/search diagnostic first.
Recommendation and executed choice: **(a), recommendation only; no allocation or launch**.
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Evidence-spec §11.8.3
favors another training unit for this learning question. The observed complete36.7s pair makes
one such measurement proportionate to the remaining uncertainty; it does not guarantee its cost
or make positive results a prerequisite. Option(c) leaves training-seed variability unmeasured
and has no separately justified algorithmic or attribution purpose here.

Exact out-of-scope next-task recommendation to Portfolio through Root: allocate **one fresh
prefix/pair at master seed1117**, with the accepted source/host, P4096, CARRY/RESET Q1024 each,
all existing E64 checkpoints, CPU FP32 one thread, and one complete1800s cap. Prospectively amend
the seed/allocation on the B card before any such launch. Preserve seed1103 and every1117 outcome;
do not run until positive or substitute a selected checkpoint. The next observation asks whether
this tiny within-MEI sign and endpoint agreement persist under a fresh learned prefix, not whether
an exact mechanism or stable population advantage has been proved.

Dominant work is again one prefix plus two descendant arms: `(4096+2*1024)*48` training joint
steps, four PPO passes, and `(64+64+2*8*64)*48` evaluation joint steps:350208 combined steps and
6144 Adam calls. No new validation, no-change control, exact optimizer diagnosis, search or tuning
is added. The current observed36.696s is one unchanged-count planning reference; a new invocation
still needs its own named allocation and fresh on-node admission. P15's unused wall allowance
does not authorize it. Root is asked to return this concrete task need to Portfolio, not to choose
the scientific question. No priority, lifecycle, capacity or investment disposition is made here.

Audit: `docs/research/portfolio/audit/2026-09-07.md#L92` (technical acceptance) and `#L93`
(next-question recommendation), at this authoring revision. Root integrates this intake's named
commit; the direction checkout remains recoverable with no live scientific process or pending Pro
response. The only outstanding next-task dependency is Portfolio's explicit allocation and card
amendment for the specified new prefix.
