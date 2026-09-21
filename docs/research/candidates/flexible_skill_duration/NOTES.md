# flexible_skill_duration — notebook

Append-only (constitution section 4). Lead: Claude session. The last section is the handover.
Frozen object: [FSD_MATCHED_INFORMATION_BASELINE_B01](FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md);
the card stands in for the claim note and is read by its own section 6. History before this
file lives in `DIRECTION.md` and the dated cards beside it (evidence, not maintained).

## 2026-09-18 17:55 PDT — resumption; L0 for the CF comparator and the B01 runner

**Resumption.** The owner resumed research in the Claude session on the WSL host
(`/home/fires/hmasd-wsl`) with "我们继续研究". By the constitution the first execution batch is
B01 exactly as frozen. Work branch `claude/fsd-b01` from main `c7df86504`. No producer, no live
handle and no open Pro request were inherited (handoff of 2026-09-16).

**Source state checked before scoping.**
- The handoff's code map still matches main: `R_Actor` `hmasd/networks.py:1401`,
  `SkillDiscoverer` :1575, `_apply_compact_context` :1664; `hmasd/agent.py` `reset_env_state`
  :1559, `select_action` :1732, `_batched_assign_skills` :1917, `_should_close_high_level_sample`
  :3382, `store_transition_batch` :3862, `_compute_low_level_compact_context` :4059,
  `update_discoverer_from_rollout` :6088.
- The truncation/termination GAE fixes of 2026-09-18 (`5a7c31c45`, `d60c5f439`) touch only
  `ha_ctse_process/`. The FSD path (`hmasd/agent.py`) is unchanged, so D1280 is still the
  standing recipe the card names, and both arms share whatever boundary arithmetic that path
  has. Not altered for this object (card section 1, "kept unchanged").
- The superseded `scripts/run_fsd_host_headroom_b01.py`, its launch script and tests are still
  on main and are replaced in the same change, never launched.

**L0 scope.**
- *Deliverable.* (1) A CF ("central-input flat") actor input pathway behind a new config flag,
  default False in `configs/config_1.py` and `configs/config_test.py`, never set by
  `apply_algorithm_config("mappo")`, set only by the CF branch of the new runner's `make_config`.
  Per-lane central snapshot = normalised global state + six normalised joint observations in
  fixed UAV order, taken at the step after a lane reset and at every `skill_timer == 0` step
  with k = 10, held for the intervening steps, cleared at `reset_env_state`; actor input =
  private observation + held snapshot + six-dimensional ego one-hot (never normalised) +
  constant skill + own GRU state. The snapshot actually used at collection is stored per step
  and replayed byte-for-byte in the recurrent update; the evaluator builds it by the same code.
  (2) `scripts/run_fsd_matched_information_baseline_b01.py`: thin entry over the baseline
  interruption B01 runner, arms `D1280` and `CF`, 45 rollouts, panels after 5, 10, …, 45,
  `--stage {0,1}`, `--lr-multiplier` (CF only; every actor and critic optimizer group that
  trains, once, on the schedule output if any), `select-stage0` (card section 3 verbatim: max
  mean J45, tie order 1, 0.5, 2 within the maximal set, `SELECTION_INCOMPLETE`) and `reduce`
  (card sections 5 and 6 verbatim, including `PRIMARY_INCOMPLETE_OR_INVALID`). Launch script
  under `experiments/candidates/flexible_skill_duration/matched_information_baseline_b01/`;
  new result entry goes through `scripts/hmasd_launch.py` with the admission guard.
  (3) Tests of card section 8. Delete the superseded host-headroom runner, launch script and
  tests in the same change.
- *Owned paths.* `hmasd/networks.py`, `hmasd/agent.py`, `hmasd/utils.py` (flag-gated additions
  only), `configs/config_1.py`, `configs/config_test.py`, `scripts/run_flexible_skill_duration_e0.py`
  (`CONFIG_DUMP_FIELDS`), the new runner, launch directory and tests.
- *Must not change.* With the flag off every existing arm is bit-identical: no new RNG draw, no
  parameter, buffer field or module constructed, no change in initialisation order. D1280's
  inputs, recipe and optimizer rates. Actor hidden width, action head, critic input, PPO loss,
  discount/GAE/termination arithmetic. Seeds, blocks, panel law, MEI, labels and the reading
  rule of the card. Training normalisers, buffers and RNG are untouched by evaluation panels.
- *Checks.* Card section 8 tests; the existing FSD guards
  (`tests/flexible_skill_duration_d2_test.py`, the baseline interruption B01 tests) still pass
  with the flag off; real-tiny CF run (2 lanes, 20-step horizon) through collection, replay and
  evaluator. Scratch under `temp/`, removed. No result-bearing smoke.
- *Review.* Independent `hmasd-reviewer` on the agent/networks/utils diff before any launch.
- *Budget and stop.* No fit is consumed by this step. Stop and return on any conflict between
  the card's interface and the code that would need a scientific choice.

**Plan after acceptance.** Commit and push; publish the lifted pause and this direction row on
`main` (the launcher compares the local `RESEARCH.md` with `origin/main`); stage 0 = six CF
fits on `wsl_4070` with fresh admission per fit, `SELECTION.json` before any stage-1 read,
then ten stage-1 fits. CF wall and RSS are unmeasured: the first stage-0 fits are watched for
RSS before filling four concurrent slots.

## 2026-09-18 evening — CF comparator and B01 runner accepted; independent review; plan for stage 0

**Accepted work (DM).** Implementer commits `f8532f99e` (flag-gated CF pathway in
`hmasd/networks.py`, `hmasd/agent.py`, `hmasd/utils.py`, flag default False in both configs,
`CONFIG_DUMP_FIELDS`) and `f3d082f81` (runner
`scripts/run_fsd_matched_information_baseline_b01.py`, launch entry, 57 tests; the superseded
host-headroom runner, launch script and test deleted). I read the core diff and the card
transcriptions myself. Checks: new object tests 57 passed; the whole FSD test tree 201 passed
(`--import-mode=importlib`; duplicate test basenames across frozen directories predate this);
D2 guard 13 passed. Known failures that predate this change and were reproduced at the parent
commit: `tests/ha_ctse_test.py::test_process_mode_clear_buffers_invalidates_old_policy_state`
(stub agent lacks `d2_enabled`) and the host-dependent P4 tape digest in
`tests/update_phase_equivalence_test.py` — the tape rebuilt from the parent and from this
change is identical on this host, which is the flag-off identity evidence.

**How the card's interface was realised.** CF runs the `off` route. The held snapshot refreshes
exactly where that route re-decides skills, `(env_steps % k == 0) | done | invalid skill`, with
k = 10, i.e. steps 0, 10, 20, … of an episode and the first step after a lane reset, from that
step's state and joint observations, before the actor forward. Raw values are held and stored
per step; normalisation is applied at use by the same code in collection, replay and evaluator.
Both arms instantiate `use_obsnorm = use_statenorm = False`, so the normalisers are the identity
and replay of the actor input is bit-exact; with them forced on, the snapshot would share the
private observation's existing end-of-rollout-statistics mismatch, no new one. Actor input
104 → 853 (state 119 + 6 × 104 + ego 6); only the actor's input projection widens. The frozen
B01 runner gained a `FLAT_ARM` constant (same value) so an arm named CF is validated as the flat.

**Independent review (`hmasd-reviewer`).** One material finding, operational: stage-1 CF could
not launch as documented, because the kernel's snapshot rebinds an absolute author path and
refuses one absent from the published snapshot, and `runs/` outputs are never in it. Repair
chosen: after stage 0, `SELECTION.json` is committed and stage 1 launches from that sha with
the repository-relative path; this also pins λ in Git before any stage-1 fit (card section 3).
Launch-script comment corrected. No leak, cadence, pairing, isolation or D1280-perturbation
finding; config differences CF versus D1280 are all inside the planned set. Nits repaired in
the same follow-up commit: the single-environment `select_action` route now refuses the flag
(it never advances the timer and would have read the centre every step; unreachable for this
object); dead `_central_snapshot_source_step` removed; `stage_guard` runs before the single-use
admission; `fit_endpoint` checks the flag in the evaluation config too. Left as is, on purpose:
`interval_inside_mei` uses the closed interval the card words ("entirely inside [−.05, +.05]");
the inherited descriptive `cost_law` string; the evaluator's unused snapshot buffer (≈48 MB).
After the repairs: object + frozen B01 + D2 guard + buffer/RNN suites 105 passed.

**Cost facts (timing probe by the Implementer, one rollout at full training shape, outside
`runs/`, no endpoint, no admission; not a fit).** CF 70.4 s per rollout and peak RSS 870 MiB;
flag-off flat 66.0 s and 845 MiB on this host. Collection and update alone extrapolate to about
3,200 s per CF fit; the nine 32-world panels are not included, so the card's 12,000 s ordinary
plan is kept as the watchdog basis until the first fit reports.

**Stage 0 plan.** Six CF fits (λ ∈ {0.5, 1, 2} × blocks 772603, 772703) on `wsl_4070`, each
through `launch_fit.sh` and the admission kernel from the published sha. Two first, RSS and
per-rollout wall read from their progress, then up to four concurrent. No stage-1 fit or panel
is read before `SELECTION.json` is committed.

## 2026-09-18 19:35 PDT — stage 0, first launch attempt: pre-training refusal on the node (no fit consumed)

Node preparation: the canonical checkout on `wsl_4070` (`/home/wu/projects/HMASD`) was 953
commits behind and its sparse cone lacked `.codex` and `docs/research`, which the admission
kernel reads there. Fetched `main` through the node's network shell (`zsh -lic`; a plain
`bash` fetch times out on SSL), fast-forwarded to `1e3a0b981`, added the two declared paths.
Untracked bundles and the existing worktrees were not touched.

Attempt `b01_s0_cf_l1_772603_a01` (CF, λ = 1, block 772603, sha `1e3a0b981`): the kernel
refused with "runner did not request admission before the deadline; claim is blocked". The
child exited 1 at import, before admission and before any output, environment or learner:
`ModuleNotFoundError: No module named 'configs'` — the node's sparse list in
`.codex/hmasd-compute.toml` predates the `configs/` package. Launch-to-exit wall under one
minute. Records kept on the node under `runs/flexible_skill_duration/b01_s0_cf_l1_772603_a01/`
(manifest, status, `process-exit.json`, `stderr.log`). A pre-training launch failure consumes
no fit (constitution section 3). Repair: `configs` added to the declared sparse list; the next
attempt runs from the new sha under a fresh tag, so it is a new claim, not a replay of this one.
The runner imports repository code only from `configs`, `envs`, `hmasd` and `scripts`.

## 2026-09-18 19:45 PDT — stage 0 running on `wsl_4070` (four of six CF fits admitted)

All from published sha `dd53e8d51112f4eb6128cd91ec797fa85329890a`, node `wsl_4070`
(`ssh hmasd-wsl-node`, canonical checkout `/home/wu/projects/HMASD`), through
`launch_fit.sh` and the admission kernel, detached. Output roots are
`runs/flexible_skill_duration/<tag>/` on the node; each holds the native manifest,
`admission-preflight.json`, `launch-status.json`, stdout/stderr and, at exit, `process-exit.json`.
Observe from either host with
`ssh hmasd-wsl-node 'cd /home/wu/projects/HMASD && python3 scripts/hmasd_launch.py status <operation_ref>'`.

| tag | λ | block | operation ref (under `/home/wu/projects/HMASD/.git/hmasd-admission/`) |
| --- | --- | --- | --- |
| `b01_s0_cf_l1_772603_a02` | 1 | 772603 | `0e3efb4589922c3341043d9b3bac2806ac8a054f0ca96f4967ae84c0b0190d7f.json` |
| `b01_s0_cf_l1_772703_a01` | 1 | 772703 | `a1bb803c36bebf9ce9e6181c859edb684003ef8814c32019a170a5ad9174a639.json` |
| `b01_s0_cf_l05_772603_a01` | 0.5 | 772603 | `61893241fc7cf32315ac827db11f9106989d2401bc9f98240b001f49256e6ba4.json` |
| `b01_s0_cf_l05_772703_a01` | 0.5 | 772703 | `213868c1ebbeb9457bc039bcac95e9d9abdcc01e60c18d4d89b8d93a608e69d3.json` |

Still to launch when a slot frees: λ = 2 on 772603 and 772703 (tags `b01_s0_cf_l2_<block>_a01`).
Node operating facts for whoever continues: network commands on the node need `zsh -lic`
(proxy); the node has no control-plane venv, so the launch script is called with
`HMASD_CONTROL_PLANE_PYTHON=/usr/bin/python3` (3.12, the kernel is standard-library only).

Resource reading, first fit after three rollouts with two fits side by side: about 50 s per
rollout (collection plus update, no panel yet), runner RSS 1.13 GB and flat, node 13 GB
available, load 7 on 20 cores. Basis for the expected end: about 45 × 50–70 s plus nine
32-world panels per fit at four concurrent, i.e. roughly one to one and a half hours per fit;
to be corrected from the first completed fit. No score has been read; selection reads only
the six J45 after all six complete.

## 2026-09-18 21:35 PDT — stage 0: all six CF fits admitted; first two terminal

The two λ = 1 fits exited on their own with code 0, 45 training rows and an empty `stderr.log`:
`b01_s0_cf_l1_772603_a02` after 6650 s and `b01_s0_cf_l1_772703_a01` after 6820 s (admission
preflight to `process-exit.json`). That corrects the earlier guess: at four concurrent fits the
node gives about 140 s per rollout including panels, about 1.85 h per CF fit; each runner used
about 3.9 cores and 1.0–1.25 GB RSS, load 15 on 20 cores, so four concurrent is the ceiling.

Each freed slot took one of the remaining λ = 2 fits, same sha `dd53e8d51112f4eb6128cd91ec797fa85329890a`,
same launch path:

| tag | λ | block | operation ref (under `/home/wu/projects/HMASD/.git/hmasd-admission/`) |
| --- | --- | --- | --- |
| `b01_s0_cf_l2_772603_a01` | 2 | 772603 | `77b25c84f310deb24c7732026a6da4976b23e85a6df5bf0551c8ee5f8e9a11f1.json` |
| `b01_s0_cf_l2_772703_a01` | 2 | 772703 | `1437db79508cc73a5f26b751736fab5b04c5b8e2b94e78fb59a6d526ce206de2.json` |

The two λ = 0.5 fits are past rollout 41 and still running. No score has been read. Stage-1
planning from the measured wall: ten fits at four concurrent is about three waves, roughly
five to six hours on this node.

## 2026-09-18 23:15 PDT — stage 0 complete: λ* = 0.5, `SELECTION.json` committed before stage 1

All six CF tuning fits exited on their own with code 0, 45 training rows, empty `stderr.log`.
The two λ = 2 fits ran two-concurrent: 3873 s and 3751 s (about 75–85 s per rollout with panels),
against 6650–6820 s at four concurrent. Outputs were collected into
`runs/flexible_skill_duration/<tag>/` on the WSL host and all 59 files match the node by sha256;
node originals untouched. The refused first attempt `b01_s0_cf_l1_772603_a01` is kept beside them.

Selection by the card's rule, from `select-stage0` over the six `summary.json` (no other quantity
was read before it): `runs/flexible_skill_duration/b01_s0_selection/SELECTION.json`.

| λ | J45 block 772603 | J45 block 772703 | mean |
| --- | --- | --- | --- |
| 0.5 | 0.2233 | 0.0908 | **0.1571** |
| 1 | 0.1162 | 0.0743 | 0.0952 |
| 2 | 0.1321 | 0.0683 | 0.1002 |

Maximal set {0.5}, no tie, status `complete`. λ* = 0.5 is the edge of the grid; the card fixes
the grid at {0.5, 1, 2} and gives no extension, so none is made. Block-to-block spread inside one
λ (0.13 J at λ = 0.5) is larger than the MEI, a reminder that the stage-1 reading rests on the
five paired blocks, not on any single fit. Tuning blocks are not reused in stage 1.

Stage 1 launches from the commit that contains this `SELECTION.json`, CF with the
repository-relative `--selection runs/flexible_skill_duration/b01_s0_selection/SELECTION.json`,
ten fits at no more than four concurrent on `wsl_4070`, D1280 and CF of the same block side by
side where the slots allow.

## 2026-09-18 23:40 PDT — stage 1, first wave admitted on `wsl_4070`

Launch sha `887563f4713177d76999ef5832ce2dfa946d8505`, the commit that contains
`SELECTION.json`. The node checkout was fast-forwarded to it and
`runs/flexible_skill_duration/b01_s0_selection` was added to the node's sparse list, because
the launch snapshot inherits the sparse patterns and CF reads the selection from the snapshot
(sha256 of the file equal on both sides, `468a5fa7…cad26a`). CF manifests record stage 1,
`lr_multiplier` 0.5. All four alive, `stderr.log` empty.

| tag | arm | block | operation ref (under `/home/wu/projects/HMASD/.git/hmasd-admission/`) |
| --- | --- | --- | --- |
| `b01_s1_cf_772803_a01` | CF λ 0.5 | 772803 | `5e0151193e2d1d28a8a004194a8c4bb409a25ddec2e14e1e40c7e023643ac9ce.json` |
| `b01_s1_d1280_772803_a01` | D1280 | 772803 | `57213538a0804bb844713338ec6e820c44d17aaf713701330295501e540733dc.json` |
| `b01_s1_cf_772903_a01` | CF λ 0.5 | 772903 | `e4e665436835072d171273ce772ed7211aaf3529c90483e4b8100a31806e5c62.json` |
| `b01_s1_d1280_772903_a01` | D1280 | 772903 | `0bf4b0c7a8ed388c46882a36101c4b4b6060d02efca0d79af675b4bd032aa88e.json` |

Still to launch as slots free, same sha and path: blocks 773003, 773103, 773203, one D1280 and
one CF each (tags `b01_s1_<arm>_<block>_a01`). No stage-1 panel or score is read before all ten
are terminal; the reading is `reduce` and card section 6 only.

## Pro question 2026-09-19 b01-after-stage0-next-step
Conversation: new (WSL Jev route; the address stays in the local operation file, named here by question key)
Question: Before the ten stage-1 fits of B01 are read, what is the strongest objection to the DM's plan for what each of the card's three importance labels would justify next, and what is the smallest discriminating comparison that should follow each label? The answer changes the DM's next idea after B01, not the frozen batch or its reading.
Standing:
  B01 is frozen and running exactly as carded: D1280 (standing recipe, D2 fixed-clock path) versus CF, a flat MAPPO-style actor that receives the same central snapshot the coordinator sees, refreshed on the same k = 10 clock. Stage 0 is complete: six CF tuning fits, `runs/flexible_skill_duration/b01_s0_selection/SELECTION.json` selects learning-rate multiplier 0.5 (mean J45 0.1571 against 0.0952 at 1 and 0.1002 at 2). Two facts from stage 0 bear on interpretation: the selected multiplier is the lower edge of the carded grid {0.5, 1, 2}, and the two tuning blocks differ by 0.13 J at the selected multiplier (0.2233 and 0.0908), more than twice the MEI of 0.05 J. Stage 1 (five fresh blocks, one D1280 and one CF fit each) is running; nothing of it has been read.
  DM's plan, the thing to attack: D_REFERENCE_ABOVE -> treat the hierarchy's advantage over a matched-information flat learner as worth one mechanism question (is it the skill clock or the coordinator's larger batch); SMALL_SIGNED -> treat the UAV host as offering no established headroom for duration ideas at this budget and move the direction to a cheaper host or idle; CF_REFERENCE_ABOVE -> make CF the working baseline for any later duration idea and ask whether D1280's deficit is optimisation (45 rollouts) rather than structure.
Context:
  Governance: `docs/project/OPERATING_CONSTITUTION.md` sections 1, 3, 5, 7, 8 (source_sha). The owner lifted the pause on 2026-09-18 for B01 exactly as frozen (`docs/research/RESEARCH.md`, pause line and the `flexible_skill_duration` row, source_sha). Advice grants no fits and adds no gate.
  Method: `.agents/skills/hmasd-scientific-tools/SKILL.md` sections "Confirm a claim", "Comparators and MARL information", "Statistics", "Cost and exposure" (source_sha): they govern what a five-pair paired comparison with a declared MEI can and cannot support, and what a matched-information comparator must hold equal.
  Evidence: this notebook, entries "2026-09-18 23:15 PDT — stage 0 complete" and "2026-09-18 evening — CF comparator and B01 runner accepted" (source_sha); `runs/flexible_skill_duration/b01_s0_selection/SELECTION.json` and the six `runs/flexible_skill_duration/b01_s0_cf_*/summary.json` (source_sha) for the per-block J45 and the panel trajectories; `scripts/run_fsd_matched_information_baseline_b01.py` functions `make_config`, `paired_statistics`, `read_primary` (source_sha) for what is actually held equal and how the labels are computed.
  Frozen contract: `docs/research/candidates/flexible_skill_duration/FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md` sections 1, 3, 4, 6, 9, 10 (source_sha). Its seeds, grid, endpoint J45, MEI, labels and the rule that covered outcomes get no result review stay unchanged; do not propose extending the grid, adding blocks or re-reading stage 0 inside B01.
Allowance: none is requested. B01 consumes its carded sixteen fits; whatever follows is a new prospective notebook entry under the default per-idea allowance of constitution section 3.
Constraints: seeds and matched baseline per constitution section 8; no training, no edits
  outside the empty "### Answer" subsection; write only there on branch claude/fsd-b01.
  Read the question at the pinned source, but fetch the latest target file before editing
  and use its actual blob SHA. Preserve all other bytes; stop on overlapping edits.
  On successful write, report the actual commit. On write failure return the complete
  answer in chat, not just a SHA, status message or link.
Return: a critic pass. (1) For each of the three labels, the strongest objection to the DM's planned next step, with the evidence or source it rests on. (2) What the grid-edge selection and the 0.13 J block spread do and do not license saying about CF being "competently tuned", and whether that limits any of the three readings. (3) For each label, the smallest discriminating comparison that would follow, with its prediction, strongest simpler explanation and fit cost. (4) Any decision-critical source you could not read. (5) MATERIAL_DISSENT yes/no on the plan as a whole, one paragraph.
### Answer

**Critic pass, before the stage-1 read.** Reasoning is pinned to `71223276833abeec641d3b51bc1bb645517b743a`; no stage-1 score is used below. These are alternative next-idea recommendations, not modifications of B01, fit grants, baseline-default changes, or requests for another result review. The current constitution and lifted pause govern; the card's scientific contract remains intact. ([G], sections 1, 3, 5, 7, 8; [I]; [C], section 6.)

#### 1. Strongest objection to each planned next step

**D_REFERENCE_ABOVE — a reason to investigate a package advantage, not an identified hierarchy mechanism.** I support retaining D1280 as the locally supported reference and considering one mechanism question. The objection is to making “skill clock or larger coordinator batch” an exhaustive fork. Both arms already receive central information on the same k = 10 clock, and both primitive recurrent actors react every step. What differs includes discrete-skill representation versus a much wider raw input, communication/bandwidth use, discriminator/intrinsic-reward and credit semantics, coordinator learning, and optimization exposure. The accepted implementation note reports the actor input widening from 104 to 853 while the hidden width stays fixed. Matching the exogenous information does not match the difficulty of learning to use it. The limited CF tuning discussed below leaves that simpler explanation live. ([C], section 1; [N], “CF comparator and B01 runner accepted”; [R], `make_config`; [M], “Comparators and MARL information”.)

Furthermore, this label means only mean(G) > .05, not that the interval excludes zero, nor that its lower bound exceeds .05. A large, imprecise package difference may be worth an exploratory intervention without becoming strong component evidence. There is no I1280 arm here and no duration benefit to inherit. Even a successful batch control would not, by elimination, establish a clock mechanism. ([C], sections 5, 6, 9; [R], `paired_statistics`, `read_primary`.)

**SMALL_SIGNED — the literal “no established headroom” statement is defensible; making it a label-triggered host verdict is not.** B01 does not contain an upper reference, so strict headroom is unestablished under *all three* labels. Its small D1280-minus-CF point difference neither measures the gain from changing duration nor establishes that the UAV host cannot support one. In particular, `SMALL_SIGNED + INTERVAL_INCLUDES_ZERO + not inside MEI` explicitly means that magnitude and direction remain unresolved. An interval wholly inside the MEI supports the card's narrower small-magnitude reading under its working model, still not equivalence or absence of duration opportunity. A small estimate with a sign-resolving interval is also not the same evidence state as a wide interval spanning consequential effects. ([C], opening, sections 1, 6, 9; [R], `read_primary`.)

Moving to a cheaper host or leaving the direction idle can nevertheless be a sensible cost/opportunity decision when there is no worthwhile discriminating idea. My dissent is against deriving that choice automatically from this label, not against allowing the DM to stop. Missing tuned headroom is explicitly not a prerequisite to exploration; conversely, no follow-up fit is owed. A cheap-host result would remain exploration on that host, not an unmeasured UAV claim. ([G], sections 1, 3, 7; [M], “Comparators and MARL information”, “Cost and exposure”.)

**CF_REFERENCE_ABOVE — use CF as a provisional working comparator at this budget, not as a universal baseline or a diagnosis of D1280.** I support taking a CF advantage seriously rather than defending D1280 by default. But “optimization rather than structure” is a false dichotomy: architecture, representation, credit, and optimization can interact. Forty-five rollouts are a resource condition, not a convergence guarantee. A deficit at that endpoint does not establish undertraining, an asymptotic structural limit, or a defect. Longer training of D alone against CF's old J45 would confound the proposed explanation with unequal exposure. ([C], sections 1, 2, 6, 9; [M], “Comparators and MARL information”, “Cost and exposure”.)

“Any later duration idea” also needs qualification. A later candidate that changes central refresh opportunities or information access needs a correspondingly matched comparator; the name CF does not by itself preserve that match. Retain CF at lambda = .5 as the working *45-rollout, k = 10 central-input* reference for the applicable condition, carry the independent uncertainty label, and retain D1280 as the fixed-clock attribution reference where useful. This is neither a D0 code-default change nor a withdrawal of historical FSD evidence. ([C], sections 1, 6, 9; [M], “Comparators and MARL information”.)

#### 2. What the grid edge and block spread license

**The supported description is “CF selected by the completed, prospectively limited learning-rate procedure,” not “CF is optimally or robustly tuned.”** `SELECTION.json` records all six candidates as available, no missing/invalid inputs, a unique maximum at .5, and no tie. The choice is not driven by opposite within-block rankings: .5 beats both alternatives on *each* block. Its increments over 1 are .1071 and .0166 J, and over 2 are .0913 and .0226 J. The corresponding two-block mean increments are .0618 and .0569 J. Those are descriptive selection contrasts, not fresh confirmation or MEI verdicts. ([S]; [C], section 3.)

The lower-edge optimum does **not** show that a value below .5 would win, quantify any remaining improvement, or invalidate the frozen comparator. Nor does it establish that the optimum has been bracketed. The response is not even monotone over the observed grid on both blocks: at 772603, 2 beats 1. “Competent” must therefore be qualified by the declared information interface, implemented learner, and limited tuning exposure, rather than used as a certificate of best attainable flat performance. This limits broad interpretations of *every* label without changing any of their numerical readings. ([S]; [C], sections 1, 3; [M], “Comparators and MARL information”.)

The .1325 J spread at .5 is a difference between two CF training/evaluation-block outcomes, about 2.65 times the MEI; it is **not** s_G, not a confidence interval, and not evidence that the stage-1 paired difference must be noisy by that amount. Shared exogenous block difficulty can cancel in a within-block contrast, while other variation will not. Stage 1 must use its five independent G_b values and the specified df = 4 interval. Neither the 32 worlds, the nine panels, nor the six tuning fits enlarge that inference n. The interval is conditional on the selected multiplier and excludes variability from repeating selection. Five blocks do not validate the iid-normal working model. ([C], sections 2, 4, 5; [R], `paired_statistics`; [M], “Statistics”.)

A specific trajectory caution is available without selecting a replacement endpoint. Averaging the 32 recorded native scores for the selected recipe gives:

| Tuning block | J5 | J40 | J45 |
| --- | ---: | ---: | ---: |
| 772603 | .2642 | .0886 | .2233 |
| 772703 | .3418 | .1152 | .0908 |

These are descriptive panels from [T05a] and [T05b], with J45 also recorded in [S]. Both J45 values are below J5, but the last five-rollout change is strongly positive on one block and negative on the other. Thus neither “uniformly still improving” nor “uniformly deteriorating” follows. The other four summaries also record actual training exposure and distinct early-panel outcomes; none is an untrained placeholder. This makes stability/optimization a live alternative, **not** a diagnosed cause or permission to pick an earlier checkpoint. ([T1a]; [T1b]; [T2a]; [T2b].)

Consequently, a D-above result does not defeat all competently optimized flat designs; a small result does not exhaust host opportunity; and a CF-above result remains an adverse observation for this D1280 recipe even though better CF tuning might exist. No label is vetoed because .5 lies at the edge. Do not extend the grid, add blocks, substitute an earlier panel, pool stage 0 into stage 1, or reopen selection inside B01. ([C], sections 2–6.)

#### 3. Smallest discriminating next comparisons

The following are **alternatives, one next idea for the realized branch**, to be specified prospectively in the existing notebook if the DM chooses to pursue one. Each uses two arms and three fresh independent training blocks per arm: six fits, including all arms and with no additional tuning. Three pairs are the smallest version here meeting the constitution's minimum for an empirical learning claim; they do not guarantee precision or turn an exploration into confirmation. A two-fit, single-pair screen could only be exploratory. Pairing must come from a declared shared exogenous design, not merely equal seed numbers; use fresh training and evaluation addresses disjoint from B01. Neither B01 arms nor panels become additional replicates. All arms retain the native endpoint and matched evaluation conditions for their declared comparison. ([G], sections 3, 8; [M], “Explore an idea”, “Statistics”.)

**After D_REFERENCE_ABOVE: D1280 versus the same fixed-clock D recipe with coordinator batch 128.** At 45 rollouts, change only the coordinator batch setting/law; retain k = 10, central input rights, skill representation, discriminators, reward/credit semantics, primitive actor/critic learning rates, recurrent chunk length, and evaluation law. This is a direct intervention on the proposed batch explanation, not another D-versus-CF package rerun. The inherited construction already exposes `coordinator_batch_size` independently of the fixed-clock arm. ([B], `make_config`; [C], section 1.)

*Prediction and discriminator.* If the larger-batch *training law* is materially responsible for D1280's performance, J45(D1280) should exceed J45(D128) on fresh paired blocks. Little change would weaken that particular explanation and motivate looking elsewhere; it would not prove the skill clock. A loss when lowering the batch supports sensitivity to the batch law, not the claim that it explains all of B01's D–CF gap. Without a contemporaneous CF arm, that mediation question remains unanswered; historical CF levels are context, not a third randomized arm.

*Strongest simpler explanation.* The batch parameter also changes the number/composition of optimizer updates under the existing ceil-based law. Therefore this tests a batch/optimization package, not pure gradient-variance reduction at equal optimizer work. Record actual coordinator examples and calls; do not describe equal team steps as equal compute. CF's raw-input optimization difficulty remains an independent alternative if both D recipes do well. A naive change to `config.k` would be less discriminating: the inherited runner explicitly documents that k also controls recurrent truncated-BPTT chunks. ([B], `make_config`; [C], section 7; [M], “Cost and exposure”.)

*Fit cost.* 2 arms × 3 blocks × 45 rollouts = **6 fits**, 2,160,000 training team steps. With the nine 32-world panels retained, evaluation is 864,000 team steps. Wall cost is 3 × W(D1280,45) + 3 × W(D128,45); the new smaller-batch arm's wall is unknown. No CF retuning or clock arm is silently included.

**After SMALL_SIGNED: state-dependent duration placement versus a state-blind, duration-histogram-matched control.** The smallest useful question is about *timing*, not a more precise repeat of D1280–CF and not host saturation. One concrete new UAV exploration would give both arms the same D-family learner and an identical feasible episode duration budget: for H500, forty synchronized team/individual skill segments comprising thirty lengths of 10 and ten lengths of 20, including the initial segment. In the candidate, one fixed, declared state-dependent renewal rule chooses which eligible segments continue to 20, subject to the remaining quota; in the control, an arm-local state-blind random permutation places the identical multiset. Fix the candidate rule before the batch; do not search thresholds in these six fits. This is a proposed new treatment, **not** a claim that this quota-based runner already exists.

Keep central snapshots available to *both* arms on the same primitive k = 10 observation clock even across a 20-step skill hold; keep recurrent training chunks at 10, the same duration-aware credit/termination semantics, coordinator batch and optimizer exposure, and identical actor/critic inputs and native reward. Both arms make the same number of skill assignments and use the same duration histogram. Neither arm may obtain another arm's trajectories or an extra off-clock central read. These are the identifying controls for this proposed comparison, not changes to B01. ([C], section 1, for the information boundary; [B], `make_config`, for the k/chunk confound; [M], “Comparators and MARL information”.)

*Prediction and discriminator.* Useful state-aligned duration should improve final native J over state-blind placement under that same duration budget. The strongest simpler explanation—more renewals, a different average duration, more communication, or more training work—is controlled rather than credited to timing. Also inspect the native reward components and realized counts; a quota violation destroys that attribution. A positive observation concerns this timing rule and control, not superiority to CF or a paper-grade UAV claim. A negative or imprecise observation weakens only this rule, not all duration ideas or the host. The control is an attribution comparator; B01's CF result does not supply a contemporaneous generic-baseline comparison for the new treatment.

*Fit cost.* At the same 45-rollout training horizon and nine-panel schedule: **6 fits**, 2,160,000 training and 864,000 evaluation team steps. Wall cost of this new duration pathway is unknown; fewer assignments do not establish a speed benefit. A cheaper-host version would answer a cheap-host question only. If this is not worth its cost or no concrete timing rule is worth testing, **idle costs zero fits and is legitimate**—no compulsory headroom search, continuation, or approval loop follows SMALL_SIGNED. ([G], sections 1, 3, 7; [M], “Cost and exposure”.)

**After CF_REFERENCE_ABOVE: a balanced, prospectively longer-horizon D1280–CF comparison.** Train fresh D1280 and CF at the already fixed .5 multiplier to **90 rollouts**, with evaluations at both 45 and 90 fixed before starting. Both arms receive the same additional training opportunity. This is a new horizon-sensitivity question, not continuation of B01 checkpoints, rescue fits on B01's blocks, or retrospective selection of an endpoint. Freeze the recipes and information interface; do not combine a D learning-rate change with the horizon change. Only two 32-world panels per fit are needed for this question.

Use the paired within-fit changes, then the paired between-method contrast:

```text
H_b = [J90(D1280,b) - J45(D1280,b)]
      - [J90(CF,b) - J45(CF,b)] = G90_b - G45_b.
```

*Prediction and discriminator.* The specific “D needs more learning exposure” account predicts positive absolute D improvement and positive H, with the CF advantage shrinking at J90. Carry G90 and both arms' absolute changes beside H. A closing gap caused only by CF deterioration is **not** D catching up. If both improve similarly while CF retains its advantage, the simple 45-rollout undertraining account is weakened. Persistent disadvantage at 90 still cannot establish asymptotic inferiority, structural impossibility, or a code defect. The 45/90 observations are nested in three independent training pairs, not six independent pairs or twelve fits. ([C], section 2; [M], “Statistics”, “Cost and exposure”.)

*Strongest simpler explanation.* More resources can help any learner; this is why CF must also receive 90 rollouts. Instability, credit assignment, and recipe-specific optimization remain possible explanations of the pattern. This test is about these recipes' response to added exposure, not a separation of “structure” from all “optimization.”

*Fit cost.* 2 arms × 3 blocks × 90 rollouts = **6 longer fits**, 4,320,000 training team steps—twice the training exposure of six B01-sized fits. Two fixed 32-world panels per fit add 192,000 evaluation team steps. Wall cost is 3 × W(D1280,90) + 3 × W(CF,.5,90), presently unknown. The stage-0 wall observations vary with concurrency, so neither a universal fit time nor doubling an old wall number is a measured cost. ([N], “stage 0 complete”; [G], section 3.)

#### 4. Decision-critical source access and scope

**No named decision-critical source was inaccessible through the GitHub connector.** I read the pinned question and named notebook entries, the specified governance/method/card passages, `SELECTION.json`, relevant exposure and panel fields in all six named stage-0 summaries, and the requested runner functions. I also followed the runner's inherited `make_config` and evaluation/validation implementation in [B] to check the batch and recurrent-chunk confounds. The trajectory calculation quoted above uses the selected recipe's J5/J40 panels and its recorded J45; it is not a re-reduction or reselection of stage 0.

I have not independently re-audited every training-row field, replay cache, node-side original, or test assertion. The implementation acceptance and review findings are reported evidence from [N], not a claim that I reran those checks. Stage-1 outcomes were intentionally not inspected for this advice. There is no measured result for any proposed follow-up and no measured wall cost for the new arms/horizons. Those are limits on diagnosis and cost precision, not additional gates.

#### 5. MATERIAL_DISSENT

**MATERIAL_DISSENT: yes.** I accept the DM's broad instincts—investigate a worthwhile D advantage, allow idle or cheaper exploration when no good idea remains, and use a successful CF comparator rather than protect D1280. I dissent from making the three point-importance labels sufficient routing evidence: D-above does not narrow mechanism to clock versus batch; SMALL_SIGNED is not an empirical host-exit verdict; CF-above neither proves undertraining nor supplies a universally matched future baseline. Keep the card's importance and uncertainty readings intact, qualify CF's tuning as the completed limited procedure, and choose at most one new discriminating question with its actual exposure visible. No grid extension, extra B01 block, altered endpoint, automatic follow-up, default change, new allowance, or result-review requirement follows this advice. ([C], sections 1, 3–6, 9; [G], sections 3, 5, 7, 8; [M].)

[G]: https://github.com/CartmanFatass/My-paper-code/blob/71223276833abeec641d3b51bc1bb645517b743a/docs/project/OPERATING_CONSTITUTION.md
[I]: https://github.com/CartmanFatass/My-paper-code/blob/71223276833abeec641d3b51bc1bb645517b743a/docs/research/RESEARCH.md
[M]: https://github.com/CartmanFatass/My-paper-code/blob/71223276833abeec641d3b51bc1bb645517b743a/.agents/skills/hmasd-scientific-tools/SKILL.md
[C]: https://github.com/CartmanFatass/My-paper-code/blob/71223276833abeec641d3b51bc1bb645517b743a/docs/research/candidates/flexible_skill_duration/FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md
[N]: https://github.com/CartmanFatass/My-paper-code/blob/71223276833abeec641d3b51bc1bb645517b743a/docs/research/candidates/flexible_skill_duration/NOTES.md
[S]: https://github.com/CartmanFatass/My-paper-code/blob/71223276833abeec641d3b51bc1bb645517b743a/runs/flexible_skill_duration/b01_s0_selection/SELECTION.json
[R]: https://github.com/CartmanFatass/My-paper-code/blob/71223276833abeec641d3b51bc1bb645517b743a/scripts/run_fsd_matched_information_baseline_b01.py
[B]: https://github.com/CartmanFatass/My-paper-code/blob/71223276833abeec641d3b51bc1bb645517b743a/scripts/run_fsd_baseline_interruption_b01.py
[T05a]: https://github.com/CartmanFatass/My-paper-code/blob/71223276833abeec641d3b51bc1bb645517b743a/runs/flexible_skill_duration/b01_s0_cf_l05_772603_a01/summary.json
[T05b]: https://github.com/CartmanFatass/My-paper-code/blob/71223276833abeec641d3b51bc1bb645517b743a/runs/flexible_skill_duration/b01_s0_cf_l05_772703_a01/summary.json
[T1a]: https://github.com/CartmanFatass/My-paper-code/blob/71223276833abeec641d3b51bc1bb645517b743a/runs/flexible_skill_duration/b01_s0_cf_l1_772603_a02/summary.json
[T1b]: https://github.com/CartmanFatass/My-paper-code/blob/71223276833abeec641d3b51bc1bb645517b743a/runs/flexible_skill_duration/b01_s0_cf_l1_772703_a01/summary.json
[T2a]: https://github.com/CartmanFatass/My-paper-code/blob/71223276833abeec641d3b51bc1bb645517b743a/runs/flexible_skill_duration/b01_s0_cf_l2_772603_a01/summary.json
[T2b]: https://github.com/CartmanFatass/My-paper-code/blob/71223276833abeec641d3b51bc1bb645517b743a/runs/flexible_skill_duration/b01_s0_cf_l2_772703_a01/summary.json

## 2026-09-19 03:15 PDT — DM response to the Pro critic pass (b01-after-stage0-next-step)

Delivery: Pro wrote the answer itself, commit `18e1543d8f0b7bdda20ebf30d2aefcb40fbacaa4` on
`claude/fsd-b01`, parent the pinned source `712232768`, 95 added lines inside `### Answer`,
nothing removed, no other file; merged to main. Sent over the WSL Jev route as a short message
plus the full message as a document; Pro reported the document hash as matching. Source use:
it read the pinned card, method sections, `SELECTION.json`, all six stage-0 summaries and the
runner, and followed the inherited `make_config`; I checked its two code claims
(`config.k` is also the truncated-BPTT chunk length; the ceil-based coordinator batch law) in
`scripts/run_fsd_baseline_interruption_b01.py` and its stage-0 contrasts against
`SELECTION.json`: correct. It did not read stage 1, and neither have I.

MATERIAL_DISSENT: yes, on routing, not on B01. What I take from it:

- **Adopted.** The three importance labels are not sufficient routing evidence by themselves;
  the uncertainty label and the interval go with them into whatever I decide next.
  "CF selected by the completed, prospectively limited learning-rate procedure" replaces
  "competently tuned" in anything I write about B01. The 0.13 J spread between tuning blocks is
  a between-block CF difference, not s_G; stage 1 stands on its five G_b.
- **Adopted, D_REFERENCE_ABOVE.** "Skill clock or batch" was a false fork: the arms also differ
  in input width against a fixed hidden size (104 to 853), discrete-skill representation,
  discriminators and intrinsic reward, and coordinator learning. If I ask a mechanism question
  it is Pro's D1280 versus D128 (coordinator batch only, k and chunk length fixed), read as a
  batch-and-optimiser-calls package, not as a clock test by elimination.
- **Adopted, CF_REFERENCE_ABOVE.** No D-only longer training against CF's old J45. If pursued,
  both arms to 90 rollouts with panels at 45 and 90 fixed in advance, read through H_b and both
  arms' absolute changes. CF at 0.5 becomes the working 45-rollout, k = 10 central-input
  comparator for that condition only.
- **Modified, SMALL_SIGNED.** I keep idle or a cheaper host as a legitimate cost decision, and
  drop the wording that the label shows the UAV host has no room for duration ideas: B01 has no
  upper reference under any label. Pro's quota-matched placement test (thirty segments of 10 and
  ten of 20, state-dependent placement against a state-blind permutation of the same multiset)
  is the cleanest timing question I have seen for this direction, but it needs a new runner
  pathway and a candidate rule fixed beforehand; it is recorded as an idea, not scheduled.
- **Noted, not acted on.** Both selected-recipe tuning fits sit below their own J5 at J45, with
  opposite last-step directions. That keeps optimisation stability live as an explanation of
  whatever stage 1 shows; it changes no endpoint and selects no checkpoint.

Nothing here touches B01: no grid extension, no extra block, no altered endpoint. At most one of
the three six-fit follow-ups will be written as a prospective entry, after stage 1 is read by
card section 6, under the default per-idea allowance.

## 2026-09-19 05:10 PDT — stage 1: all ten fits admitted; six terminal

All from launch sha `887563f4713177d76999ef5832ce2dfa946d8505`, same path as the first wave, each
taking a slot as one freed (never more than four concurrent). Terminal so far, each on its own
with exit code 0, 45 training rows and an empty `stderr.log`: CF and D1280 on 772803, CF and
D1280 on 772903, CF on 773003, CF on 773103. Running: D1280 773003, D1280 773103, CF 773203,
D1280 773203. No stage-1 panel or score has been read.

| tag | arm | block | operation ref (under `/home/wu/projects/HMASD/.git/hmasd-admission/`) |
| --- | --- | --- | --- |
| `b01_s1_cf_773003_a01` | CF λ 0.5 | 773003 | `381823497e8b2fdd9314bdf4cc9ea11319b20884fa0f8e5720ee03dfa26bcbc9.json` |
| `b01_s1_d1280_773003_a01` | D1280 | 773003 | `d8e9ce1dbb390045f847791896a59458114e83f583380bf45e42f9d3212f29e3.json` |
| `b01_s1_cf_773103_a01` | CF λ 0.5 | 773103 | `724c339a89c227058ec981ef8c875a5d56fe2ed0ac89d20ed5e2b5b772994119.json` |
| `b01_s1_d1280_773103_a01` | D1280 | 773103 | `2ba4fa2ded43173eedf4868a085da19d1d69f38695b198bfbfa875dce318e666.json` |
| `b01_s1_cf_773203_a01` | CF λ 0.5 | 773203 | `76cbcd238f93b3fc79294db8ff0c514bae766f78538c05d2a332538c26588779.json` |
| `b01_s1_d1280_773203_a01` | D1280 | 773203 | `f278de05e9a32acd95687ade79a40fb1e6276f5e6b78aa03d21153f635c852dc.json` |

One pre-training refusal, no fit consumed: the first request for `b01_s1_cf_773003_a01` was
refused with "canonical control checkout has not fetched the published control head", because
main had moved (transport work) since the node was synced. The node checkout was fast-forwarded
and the same request admitted. Operating fact: fast-forward the node's canonical checkout to
published main before each launch; the launch sha stays the one that holds `SELECTION.json`.

Observed cost at four concurrent: CF about 1.85 h per fit as in stage 0; D1280 somewhat slower
than CF on this node (in the first wave the two D1280 fits finished about 35 minutes after
their CF partners), the opposite of the card's wall plan ordering. Plans, not caps.

## 2026-09-19 05:05 PDT — stage 1 complete; B01 read by card section 6: D_REFERENCE_ABOVE, INTERVAL_POSITIVE

Clock correction first. The heading times of four earlier entries were my estimates and run
ahead of the clock: "23:15" and "23:40" (2026-09-18) were committed at 22:38 and 22:42, "03:15"
and "05:10" (2026-09-19) at 02:55 and 03:18. The commit times are the facts; the entries stay as
written. This heading is from `date`.

**Completion.** All ten stage-1 fits are terminal, each with its own `process-exit.json`
(exit code 0), 45 training rows, nine panels and an empty `stderr.log`; the last,
`b01_s1_d1280_773203_a01`, finished 04:59 PDT. Every fit reports launch sha `887563f47`, CF at
multiplier 0.5, D1280 at 1.0, 360,000 training transitions, 45 update stages, 144,000 evaluation
steps, two model constructions, no checkpoint load; optimizer calls 101,250 actor and critic in
both arms, coordinator 675 in D1280 and 0 in CF, as the card planned. No stage-1 score was read
before the tenth exit. The ten folders were copied from the node in one pull (90 files,
sha256-identical to the node's; node originals untouched) into `runs/flexible_skill_duration/`.
`reduce` over the ten summaries and the committed `SELECTION.json` wrote
`runs/flexible_skill_duration/b01_s1_reduce/summary.json`
(sha256 `c8d16765ac258ef15602f56c375780dfc92de008dbdb77889a436531b685c22d`), status `complete`,
no missing or invalid arm.

**Primary.** G_b = J45(D1280) − J45(CF, λ 0.5), five paired blocks.

| block | J45 D1280 | J45 CF | G_b | world-difference SD / SE (32 worlds) |
| --- | ---: | ---: | ---: | ---: |
| 772803 | 0.4559 | 0.0747 | +0.3812 | 0.048 / 0.0085 |
| 772903 | 0.3547 | 0.1587 | +0.1960 | 0.061 / 0.0107 |
| 773003 | 0.4994 | 0.0802 | +0.4192 | 0.039 / 0.0069 |
| 773103 | 0.4004 | 0.1894 | +0.2110 | 0.054 / 0.0096 |
| 773203 | 0.4282 | 0.1880 | +0.2402 | 0.077 / 0.0136 |

mean(G) = **+0.2895 J**, s_G = 0.1032, SE_G = 0.0461, t(.975, 4) = 2.7764, working-model interval
**[+0.1614, +0.4176]**; blocks 5 positive, 0 negative, 0 zero (listed, not a gate). Levels,
descriptive only: D1280 0.4277 (SD 0.055), CF 0.1382 (SD 0.057).

**Labels by the card's sole numeric conditions.** mean(G) > +.05: `D_REFERENCE_ABOVE`. Interval
lower end > 0: `INTERVAL_POSITIVE`. The interval is not inside [−.05, +.05]; its lower end is
about three MEI. Fixed reading: the fixed D1280 recipe has a development-scale positive point
difference on these five blocks over the central-input flat learner selected by the completed,
prospectively limited learning-rate procedure; D1280 is retained as a locally supported
comparison reference. A record for later use: no interruption object follows automatically, no
default changes. The outcome is covered by the rule, so no result review. The interval is the
declared iid-normal df = 4 working model, conditional on λ* = 0.5 and excluding the variation
of rerunning the tuning; five blocks do not validate its coverage.

**Curves G_r (reported, never selected among).** Mean G_r by rollout 5…40: .124, .094, .095,
.158, .199, .144, .260, .292; four of five blocks positive through rollout 20, five of five from
25 on. Arm means by panel, rollout 5…45:

| arm | 5 | 10 | 15 | 20 | 25 | 30 | 35 | 40 | 45 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| D1280 | .341 | .319 | .358 | .368 | .438 | .422 | .434 | .449 | .428 |
| CF | .217 | .225 | .264 | .210 | .239 | .278 | .173 | .157 | .138 |

**What the gap is made of (descriptive; changes no label).** From rollout 5 to 45 the D1280
mean rises by .087 and the CF mean falls by .079. CF ends below its own J5 in four of five
blocks (773103 is the exception) and its mean drops after rollout 30; D1280 ends above its J5
in four of five (773003: −.003). So about .12 of the .29 is there at the first panel, and the
rest is half D1280 improving and half CF deteriorating. This is what the Pro pass flagged from
the two stage-0 fits at 0.5 (both below their J5 at J45), now seen on five fresh blocks: the
selected flat learner is not stable over 45 rollouts at the smallest multiplier of the fixed
grid, and 0.5 was the grid edge. The card's reading stands as written, and it claims nothing
about hierarchy necessity, an upper reference or headroom (section 9). What I will not write
from B01: "skills are needed on this host" or "D1280 beats a well-trained flat policy". What it
does support: at this budget and under this limited tuning, the standing D1280 recipe is the
better and the more stable of the two learners, by a margin far outside the MEI, on every block.

**Predictions scored (card section 10).** I gave D_REFERENCE_ABOVE .25 (SMALL_SIGNED .50,
CF_REFERENCE_ABOVE .25) and INTERVAL_INCLUDES_ZERO .80. Both missed: log score −1.39 on the
label, −1.61 on the interval. I expected a central-input flat learner with the same information
to be roughly level with D1280 and did not price in that it would degrade with training. The
lesson I take is about my model of the flat learner on this host, not about the rule.

**Cost, measured.** Native wall before publication, summed: CF 33,882 s (5 fits, mean 6,776 s),
D1280 41,241 s (mean 8,248 s; the last ran partly alone, 5,814 s). Stage 1 total 75,123 s
against the card's plan of 111,500 s for these ten; the plan had CF as the slower arm and the
node shows the opposite. Peak RSS: D1280 2.75–2.79 GiB, CF 1.26–1.33 GiB. Makespan at no more
than four concurrent fits on `wsl_4070`: first admission 22:42 PDT, last exit 04:59 PDT.

**The object ends here.** B01 used its 16 fits (plus one pre-training refusal in each stage, no
fit consumed). No extra block, no grid extension, no longer training under this object.

**Next, not scheduled.** Under `D_REFERENCE_ABOVE` the routing I adopted after the Pro pass
applies: if I ask a mechanism question it is D1280 versus D128 (coordinator batch only, k and
chunk length fixed), read as a batch-and-optimiser-calls package. The CF decline adds a second
candidate I had not listed: whether the flat learner's deterioration is a step-size effect
(it would be a new object with its own prospective entry, not a repair of B01's comparator, and
B01's reading would not be re-judged by it). At most one six-fit entry, written prospectively,
under the default per-idea allowance; neither is started.

## 2026-09-19 05:20 PDT — prospective: coordinator batch, D1280 versus D128 at 45 rollouts (explore, six fits)

Written before any code for it exists and before any of its fits. Exploration under section 3
(one idea, up to six fits): no claim note, no MEI verdict, no label with a consequence.

**The idea in one sentence.** The standing D recipe trains its coordinator on batches of 1280;
if that batch law is part of why D1280 learns and stays stable over 45 rollouts, the same
recipe with `coordinator_batch_size = 128` should end lower, or be less stable, on the same
blocks.

**Structure it touches.** Learning of the high-level (coordinator) policy only: how the 800
coordinator rows a rollout produces (16 lanes, H500, k = 10) are cut into optimizer chunks and
normalisation groups. D1280 takes them in one chunk, 15 coordinator calls per rollout, 675 per
fit; D128 takes ceil(800 / 128) = 7 chunks, 105 calls per rollout, 4,725 per fit. The treatment
is therefore a package of three things that cannot be separated here: smaller batches, seven
times as many coordinator optimizer steps, smaller advantage-normalisation groups. Nothing
else changes: k = 10 and the skill clock, information rights, skill representation,
discriminators and intrinsic reward, the primitive actor and critic with their learning rates
and 10-step recurrent chunks, the 45-rollout horizon, the nine 32-world panels, the evaluator.
`scripts/run_fsd_uav_individual_renewal_b01.py make_config` already takes the batch size as an
argument independent of the renewal arm; `hmasd/agent.py` reads it in the coordinator update.

**What is already known.** `FSD_INTERRUPTION_BATCH_B01` (2026-09-15) ran D128 and D1280 side by
side at **five** rollouts on two blocks: D1280 − D128 = +.028 and +.006 J (its MB contrast, the
average over the D and I rows, was −.003 J, SD .023). At that short horizon the batch law did
not visibly matter. Nobody has run D128 at 45 rollouts. B01 now shows D1280 rising from .341 at
rollout 5 to .428 at rollout 45 with a J45 block SD of .055, so the question is about rollouts
5 to 45, where the older object says nothing. It is context and is not pooled with this one.

**Strongest simpler explanation.** The batch law is irrelevant at this scale, as it looked at
five rollouts: D1280's level and stability come from the rest of the recipe, and D128 lands
within block noise of D1280. A second one: D128 is better, because 7× the coordinator updates
is more learning per rollout, and 1280 was chosen for the interruption arm's row counts, not
because the fixed-clock arm needed it.

**The observation that distinguishes them.** Per block b, M_b = J45(D1280, b) − J45(D128, b),
and the two nine-panel curves side by side. Batch law matters in the proposed direction: M_b
positive on most blocks and the D128 curve flat or falling after the early panels, the way
CF's did. Irrelevant: M_b of both signs, mean small against its own spread, curves overlapping.
D128 better: M_b mostly negative. I will report the five M_b, their mean, sample SD, SE and the
t(.975, 4) working-model interval (same caveats as B01), the panel curves and the per-arm
levels; mixed signs or a wide interval are reported as such. Whatever the result, this does
**not** say how much of B01's D − CF gap the batch law carries: there is no CF arm here, and
B01's CF levels are context, not a third arm. It also says nothing about the skill clock.

**Arms, blocks, fits: 6 fits, 45 rollouts each.**

| fits | arm | blocks (training / evaluation seed) |
| ---: | --- | --- |
| 5 | D128 | the five B01 confirmation blocks, 772803/782803 … 773203/783203 |
| 1 | D1280 | 772803/782803 again, at the new launch sha |

The D1280 side of M_b is B01's five stage-1 D1280 fits, already complete at sha `887563f47`.
This departs from Pro's 2 arms × 3 fresh blocks, and the reason is precision per fit: three
pairs give df = 2 (t = 4.30), five pairs give df = 4 (t = 2.78) for the same six fits, and
pairing on the same training and evaluation seeds removes the block component exactly as in
B01. The price is that the D1280 arm is not contemporaneous and its scores are known to me
while D128's are not; all five blocks are used, none chosen, so knowing them selects nothing.
The sixth fit pays for the non-contemporaneity: D1280 rerun on block 772803 at the new sha, on
the same node and interpreter. If its nine panel means reproduce B01's fit exactly, the old
D1280 fits stand as the arm without qualification. If they differ, the difference is the
measured size of rerun variation at fixed seed (thread scheduling, not the seed), it is
reported next to the M_b, and M_b still uses the five B01 fits as declared here; the rerun
never replaces one. This is fixed now so that the choice cannot follow the numbers.

Exposure: 6 × 360,000 = 2,160,000 training team steps, 864,000 evaluation team steps, 54
panels. Wall: D1280 measured 8,200–9,300 s per fit at four concurrent on `wsl_4070`; D128 at
45 rollouts unmeasured (seven times the coordinator steps, smaller each). Plan, not a cap:
two waves, about five hours of node time. Budget: the default per-idea allowance, no more
fits whatever the scores show; a failed training attempt counts, a pre-training refusal does
not.

**Expected sign (DM, before any output).** P(mean M > +.05) = .25, P(|mean M| ≤ .05) = .55,
P(mean M < −.05) = .20; P(interval includes zero) = .75; P(the D1280 rerun reproduces the nine
panel means exactly) = .5. I lean to "irrelevant" because of the five-rollout record; B01 has
just shown me that my model of what degrades over 45 rollouts on this host is poor, which is
why the tails are not thinner.

**What I would do with it (no automatic step).** Irrelevant or D128 better: drop the batch law
as an explanation of D1280's standing and note D128's wall, since a cheaper reference is worth
having. D1280 clearly better with D128 decaying like CF: coordinator-side optimisation
stability becomes the live account of both the D128 and the CF curves, and the step-size
question about the flat learner noted at the end of the B01 reading becomes the natural next
entry. Either way one new entry, written prospectively.

**Code needed (L0 scope, not yet written).** A thin entry
`scripts/run_fsd_coordinator_batch_b02.py` over the B01 runner's loop, panel law and fit
validation, exactly as the matched-information runner does it: arms `D128` = ("D0", 128) and
`D1280` = ("D0", 1280), blocks restricted to the five above, no stage or multiplier argument,
no CF code path touched; a `reduce` that takes the five new D128 summaries, the five B01 D1280
summaries by path with their recorded sha, and the rerun, and writes the quantities above; a
launch script on the admission kernel; tests for the arm table, the block restriction, the
pairing, a missing pair, and the rerun comparison (exact equality reported as a boolean plus
the maximum absolute panel difference). No learner, environment or evaluator change, so no
shared-core review; the D1280 config produced by the new entry must equal B01's field for
field, and a test asserts it.

## 2026-09-19 05:26 PDT — coordinator batch B02: entry code written and accepted; design confirmed by the owner

The owner preferred my design (five D128 fits paired with B01's completed D1280 fits, plus one
D1280 rerun) over Pro's two arms on three fresh blocks, because it was written after reading the
new result. No change to the prospective entry above.

Code, written by me and accepted by me; no learner, environment, evaluator or shared-runner file
is touched, so no independent review:

- `scripts/run_fsd_coordinator_batch_b02.py`: thin entry over the frozen B01 loop, as the
  matched-information runner is. Arms `D128` and `D1280`, both the ordinary D0 construction;
  `plan_guard` admits exactly the six planned fits (D128 on the five blocks, D1280 on 772803
  only) before an admission is spent. `reduce` reads this object's fits with its own validator
  and the five reference fits with the matched-information validator, refuses a pair whose
  host, precision, seeds or configuration differ in anything but `coordinator_batch_size` (the
  launch sha differs by design and is reported), and reports the rerun as exact-or-not plus the
  maximum panel-mean and world-score differences; the rerun never enters M_b.
- `experiments/candidates/flexible_skill_duration/coordinator_batch_b02/launch_fit.sh`: one
  kernel invocation per fit.
- Tests (six, fake learner and host, 45 rollouts and nine panels through the frozen loop): the
  plan guard; the **real** config of the new D1280 equals the matched-information D1280 field for
  field and D128 differs from it in `coordinator_batch_size` only; identity and cross-object
  refusal; the paired readout end to end with exact dyadic values; a differing rerun measured
  and not substituted; missing, invalid, unplanned-difference and duplicate inputs. Run with
  the matched-information (57) and baseline x interruption (18) folders: all pass, and the two
  thin entries pass in one process.
- Checked against the real records: the real D1280 config built by this entry equals the
  `learner_config` recorded in `b01_s1_d1280_772803_a01/summary.json` with no differing field,
  and `reduce` validates all five real B01 D1280 summaries (level mean 0.4277, as B01 reported).

Launch next, at the commit that holds this code: four first (D128 on 772803, 772903, 773003
and the D1280 rerun on 772803), the remaining two D128 as slots free. Tags `b02_d128_<block>_a01`
and `b02_d1280_772803_a01`. No B02 score is read before all six are terminal.

## 2026-09-19 05:28 PDT — coordinator batch B02: first wave admitted on `wsl_4070`

Launch sha `0cb5093578d16f9baaa2bd96cb3b395ad4e14012`, node checkout fast-forwarded to it first,
each through `coordinator_batch_b02/launch_fit.sh` and the admission kernel, all admitted at the
first request. Alive with an empty `stderr.log` after the fourth admission.

| tag | arm | block | operation ref (under `/home/wu/projects/HMASD/.git/hmasd-admission/`) |
| --- | --- | --- | --- |
| `b02_d128_772803_a01` | D128 | 772803 | `cf275abaca1b0cfef5c347e3c1e441bc0a337fef0f6388d87865dd757b8893cb.json` |
| `b02_d1280_772803_a01` | D1280 rerun | 772803 | `dba478b1d80feccde0892410e490aa7fcaa5e6121311a61becb5412770804c00.json` |
| `b02_d128_772903_a01` | D128 | 772903 | `2f90f77197c2d097e94e803c199e768ee3262323aa28493ff06e4bb48b192a24.json` |
| `b02_d128_773003_a01` | D128 | 773003 | `b06453dea598bfa64b4f4eac5818c1cefa06936e7d324cfdd756de91cb6eee92.json` |

Still to launch as slots free, same sha: D128 on 773103 and 773203.

## 2026-09-19 06:45 PDT — control revision `fb3d225fb` (cumulative research understanding): read and adopted for future work

The owner pointed this session at the merged control revision (PR #26, `fb3d225fb`). Read at a
safe boundary while the B02 first wave runs: the constitution sections 1, 2, 4 and 5, `AGENTS.md`,
`hmasd-research-hub`, `hmasd-scientific-tools` with `references/cumulative-research.md`,
`hmasd-pro-research-prompt-author`, `hmasd-portfolio-task`, and the Scout and ResearchCritic
bodies. `tools/publish_claude_control.py --check` reports `drift: 0`, so the generated Claude
bodies on disk are the revised ones. The subagent descriptions this session loaded at start
are the earlier ones; a subagent started from now on reads the revised body from disk.

What does not change: B02 is in flight and is not touched. Same launch sha, same six planned
fits, same fixed rule for the rerun, no relaunch, no re-read of the design. The B01 reading by
card section 6 stands as written.

What changes in how this session works from here:

- The B02 reading will separate execution facts, observations and interpretation, and will say
  what it strengthens, weakens and leaves untouched in the current explanation (the B01 entry's
  "What the gap is made of"). "No useful discrimination" is an allowed outcome.
- B02 is a package screen. D128 changes the batch, the number of optimizer steps (seven times
  as many) and the normalisation group size together; the prospective entry already says so.
  The reading therefore forgoes attributing a difference to any one of the three.
- The numeric probabilities in the B02 prospective entry were written before this revision.
  They will be scored as written, as uncalibrated guesses. Later prospective entries give the
  expected sign and, for a targeted change, one intermediate and one native prediction, not
  invented probabilities.
- A boundary return is one paragraph: state, evidence and commit, what the evidence does and
  does not establish, the judgment changed or unresolved, the next step or real dependency.
- No Pro round is owed after B02; one is written only if a focused question needs it.

Operating fact: a Codex session drives `vap_folr_core` as DM from its own worktree of this same
repository on this host (`~/.codex/worktrees/folr-predictive-aux/hmasd-wsl`, branch
`codex/folr-predictive-aux-a01`), and its planned fits use node `local_linux`, whose
`project_root` is this checkout. This checkout may therefore be fast-forwarded and may receive
`runs/vap_folr_core/` outputs that are not this session's. This session stages explicit FSD
paths only, fetches before each commit, never cleans or stages files it did not write, and
edits only the FSD row of `RESEARCH.md`. That branch states that FSD stays with the Claude
session and that there is no Root dispatch layer, so this session keeps integrating its own
FSD commits on `main`.

## 2026-09-19 08:21 PDT — coordinator batch B02: all six fits admitted; three terminal

Execution facts only; no B02 score has been read. `b02_d128_772803_a01`, `b02_d1280_772803_a01`
and `b02_d128_772903_a01` ended with exit 0 and 45 rows each; `b02_d128_773003_a01` was at 44
rows. Two slots were free, so the last two planned fits were launched at the same launch sha
`0cb5093578d16f9baaa2bd96cb3b395ad4e14012`, after fast-forwarding the node checkout to the
published `main` (`ff0725db5`). Both admitted at the first request, alive with an empty
`stderr.log`. Never more than four fits ran at once.

| tag | arm | block | operation ref (under `/home/wu/projects/HMASD/.git/hmasd-admission/`) |
| --- | --- | --- | --- |
| `b02_d128_773103_a01` | D128 | 773103 | `af2f9072c8a2eb8b53eeda01352d5dd976f656856a6faf649c57110113ad3a84.json` |
| `b02_d128_773203_a01` | D128 | 773203 | `519d27ad0032b08745c520758c06a61ba4774d9b62e425ae8a5eed1bdfaaca26.json` |

The plan is now fully launched: six of six. Collection and the reduction wait for all six exits.

## 2026-09-19 10:00 PDT — coordinator batch B02 read: no detectable difference between D1280 and D128 at 45 rollouts; the D1280 rerun is bit-exact

Prior explanation this reads against: the B01 reading (entry "stage 1 complete", section "What
the gap is made of") and the prospective entry "coordinator batch, D1280 versus D128". The
written rule there is followed; nothing was added after seeing scores. Exploration: no MEI
verdict, no effect claim.

**Execution facts.** Six of six planned fits admitted at the first request on `wsl_4070`, launch
sha `0cb5093578d16f9baaa2bd96cb3b395ad4e14012`, never more than four at once, all exit 0 with 45
training rows, `summary.json` status complete, empty `stderr.log`. Collected in one rsync, 54
files sha256-identical to the node; node originals untouched. `reduce` status complete, no
invalid input, every pair differing only in `coordinator_batch_size`;
`runs/flexible_skill_duration/b02_reduce/summary.json`, sha256
`fe5178b2cea1175c3bd675f6bb0836ebf606be1fb58571b5efc944909b873940`. Wall before publication:
first wave (four concurrent) D128 9,852 / 9,839 / 10,047 s and the D1280 rerun 9,885 s; second
wave (two concurrent) D128 5,619 / 5,554 s. Peak RSS: D128 about 1.9 GiB, D1280 2.75 GiB.
Exposure as declared: 2,160,000 training team steps.

**Observations.** M_b = J45(D1280, b) − J45(D128, b), D1280 from the five completed B01 fits.

| block | J45 D1280 | J45 D128 | M_b | D1280 J45 − J5 | D128 J45 − J5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 772803 | .4559 | .4362 | +.0197 | +.228 | +.136 |
| 772903 | .3547 | .4540 | −.0993 | +.051 | +.223 |
| 773003 | .4994 | .4216 | +.0778 | −.003 | +.048 |
| 773103 | .4004 | .4876 | −.0872 | +.079 | +.073 |
| 773203 | .4282 | .4646 | −.0364 | +.077 | +.204 |

Mean M = −0.0251, s = 0.0743, SE = 0.0332, t(.975, 4) interval [−0.1173, +0.0671], two blocks
positive and three negative. Levels, descriptive: D1280 0.4277 (SD .055), D128 0.4528 (SD .025).
Arm-mean curves over rollouts 5…45: D1280 .341 .319 .358 .368 .438 .422 .434 .449 .428; D128
.316 .357 .363 .377 .420 .424 .458 .436 .453. The mean paired difference stays within ±.04 at
every panel and changes sign five times. D128 rises from rollout 5 to 45 in five of five
blocks; nothing in it resembles the CF decline seen in B01.

D1280 rerun on 772803: all nine panel means and every world score equal the B01 fit exactly
(maximum absolute difference 0.0) across the two launch shas.

**Interpretation.** Separated from the above; qualitative.

- Weakened: the account that D1280's standing in B01 owes something to its batch law (one large
  coordinator batch, 675 optimizer calls per fit). Replacing it with 4,725 smaller calls and
  smaller normalisation groups moved J45 by an amount not distinguishable from zero, with the
  point estimate on D128's side. This is a package screen: it does not say that batch size,
  step count and normalisation group size are each irrelevant, only that their sum was not
  seen to matter here.
- Not established: equivalence. The interval admits a difference of either sign as large as
  the .05 J used as B01's MEI. "No detectable difference with five blocks" is the statement.
- Weakened as well: "many small coordinator updates destabilise training on this host over 45
  rollouts". The skill learner took seven times the updates and rose in every block. B02 has no
  CF arm, so this does not explain the CF decline; it only removes one candidate account of it
  that would have worked through the coordinator update count.
- Strengthened: run-to-run variation at a fixed seed is nil for D1280 on this node and
  interpreter, across launch shas. The non-contemporaneous reference arm cost nothing, and
  block-to-block variation is seed variation, not scheduling noise. Shown on one block.
- Untouched: why the selected flat learner declines; whether skills are needed; whether the
  B01 gap would survive a flat learner that does not decline; anything about unfixed k.
- Suggested by the result, not predicted: D128's endpoints are less dispersed across blocks
  (SD .025 against .055) and the blocks where D128 wins are those where D1280 ended low. With
  five blocks this is a conjecture and I am not acting on it.

**Predictions, scored as written** (pre-revision probabilities, uncalibrated guesses): mean M in
|M| ≤ .05, assigned .55, log score −0.60; interval includes zero, assigned .75, −0.29; rerun
exact, assigned .5, −0.69. The lean to "irrelevant" held; the rerun was a coin flip I had no
basis for, and it is now a known fact about this node.

**Decision, as written beforehand.** The batch law is dropped as an explanation of D1280's
standing. The hoped-for by-product does not exist in wall time: at four concurrent, D128 cost
the same as D1280 (about 9,850–10,050 s); it is cheaper only in memory (about 0.85 GiB less).
D1280 stays the reference; no reason to switch. The idea is ended with its six fits used; no
extension.

**Next.** The follow-up I had named (the flat learner's step size) was conditioned on D128
decaying like CF, and it did not. The question survives on B01's own evidence (CF declines in
four of five blocks at the grid-edge multiplier 0.5), and it bears on the constitution's
"competent matched-information baseline": as long as the comparator deteriorates with
training, the +0.29 J gap overstates what a well-trained flat policy would concede. That would
be a new prospective entry with its own allowance, not scheduled by this one. Re-entry
condition: I write that entry, or the owner points the direction elsewhere. No Pro round is
owed for this result.

## 2026-09-19 14:55 PDT — inspection of existing fits (no new fit): the flat learner's evaluation decline coincides with an action-noise blow-up, not with a training-return decline

The owner asked for the next step. Before spending fits on "the flat learner's step size" I read
what the sixteen completed B01 fits and the five B02 D128 fits already record per training
rollout (`training_rows[*].losses`, `episode_returns_U`, `relative_initialization_displacement`).
Prior explanation: B01 reading, "What the gap is made of" (CF evaluation J falls .217 → .138
while D1280 rises), and its open question whether a lower learning rate would stop the decline.

**Observations** (arm means over the five stage-1 blocks, rollouts 1 / 15 / 30 / 45).

| quantity | CF (selected, ×0.5) | D1280 | D128 |
| --- | --- | --- | --- |
| training episode return U (stochastic policy) | 19.7 / 22.1 / 22.9 / 22.7 | 19.5 / 27.5 / 30.2 / 28.7 | 19.5 / 23.5 / 30.4 / 29.5 |
| evaluation J (deterministic policy), rollouts 5 / 15 / 30 / 45 | .217 / .264 / .278 / .138 | .341 / .358 / .422 / .428 | .316 / .363 / .424 / .453 |
| low-level action entropy | 4.32 / 5.69 / 7.27 / 8.92 | 4.33 / 5.51 / 6.57 / 7.46 | 4.33 / 5.51 / 6.58 / 7.48 |
| actor displacement from initialisation (relative) | .027 / .063 / .079 / .094 | .158 / .710 / .973 / 1.148 | .158 / .708 / .976 / 1.149 |
| low-level value loss (normalised) | .087 / .097 / .141 / .175 | .136 / .033 / .010 / .008 | .136 / .045 / .012 / .006 |

- CF's training return does not decline; it rises a little and plateaus. Only the deterministic
  evaluation declines. Training acts by sampling, evaluation by the mean action
  (`deterministic=True` in the B01 panel loop), and the environment clamps a motion request to
  the unit ball.
- The action entropy rises in every fit of every arm, almost identically across blocks (CF
  8.84–9.01 at rollout 45). The policy is a 3-dimensional Gaussian per agent with a learned
  log-std initialised at 0 and capped at 2.0 (`hmasd/networks.py`); entropy 4.32 is std 1.0,
  8.92 is std about 4.7, 7.46 is about 2.9. The entropy term is `-lambda_l * entropy` with
  `lambda_l = 0.05`, fixed (no entropy targets, no annealing in these configs).
- In the six stage-0 CF fits the entropy at rollout 45 orders with the learning-rate multiplier:
  8.95 (×0.5), 9.82 (×1), 10.12 (×2; the cap is 10.26). The stage-0 selection of ×0.5 picked the
  multiplier under which the noise grew slowest.
- CF's actor has moved about a twelfth as far from initialisation as D's, at half D's learning
  rate; its recorded policy loss is near zero (order 1e-4 against D's order 5e-3).

**Interpretation (working, conditional).** The strongest account I can now give of the CF
decline is not a step-size problem of the usual kind. With std several times the action range,
the sampled actions are mostly clamped, the policy-gradient signal on the mean is weak, the
entropy bonus keeps pushing the log-std up, and the mean action (the only thing evaluation
uses) is barely trained and drifts. Training return cannot show this because it is measured
under the noise. The learning-rate grid could only slow it. This weakens "CF needs a smaller
learning rate" as the repair, and it strengthens the B01 caveat: the +0.29 J gap is measured
against a flat learner whose evaluated policy is partly untrained.

What it does not settle: D's entropy rises too (std about 2.9) and D still improves, so noise
growth alone is not sufficient for decline; D's low-level learner optimises a short-horizon
intrinsic reward with a critic that fits (value loss falls to .008) and its actor moves. The
difference between "noise blow-up with a usable gradient" and "noise blow-up with none" is my
inference, not an observation. The CF critic's rising value loss is compatible with the same
account (returns get noisier) and with an independent critic problem; the inspection cannot
separate them.

## 2026-09-19 15:00 PDT — prospective: flat learner with a smaller entropy coefficient (explore, six fits)

**Question.** Is the central-input flat learner's evaluation decline caused by the entropy
bonus inflating its action noise, and how much of the B01 gap remains when it is removed?
This continues the matched-information question of B01, with new information value: B01 tuned
only the learning rate, and the inspection above says the learning rate was not the lever.

**Structure touched.** None of roster, duration, credit or information flow. This is
comparator competence (constitution section 1: "a competent matched-information baseline").

**Simpler explanations it must be told from.** (a) The decline is a central-input or recurrent
evaluation artefact unrelated to noise: then entropy stays low under the change and J still
falls. (b) The flat learner is simply poor on this host: then entropy stays low, the actor
moves, and J stays flat near .2 without decline or gain. (c) The entropy account: entropy stays
low, the actor moves further, J45 ≥ J5 and J45 above the B01 CF fit on the same block.

**Arms.** `CF` exactly as selected in B01 (learning-rate multiplier 0.5, everything else equal)
with one field changed: `lambda_l` = 0.005 (`CF_E005`) or 0.0005 (`CF_E0005`), against B01's
0.05. Exactly zero is not used because the learner records the entropy as 0 when the
coefficient is 0 (`hmasd/agent.py`, `action_entropy_val`), which would blind the intermediate
observable. Two values because a tenfold cut may not be enough to stop the growth and a
hundredfold cut may collapse exploration; which of the two happens is itself informative.

**Blocks and count.** Both values on B01 stage-1 blocks 772803, 772903, 773003 (the first three
in order, none chosen by score): six fits, the whole default allowance, 45 rollouts, panels at
5…45, same evaluation seeds, node `wsl_4070`. References are the completed B01 fits on the same
blocks: CF (`lambda_l` .05) and D1280, not contemporaneous. B02 showed a D1280 rerun to be
bit-exact across launch shas on this node; the same is assumed, not shown, for CF. No rerun fit
is spent on it.

**Predictions (signs; targeted change, so one intermediate and one native).**
- Intermediate: action entropy at rollout 45 stays below 5.5 for both values (B01 CF: 8.9), and
  the actor's displacement at rollout 45 is at least twice B01 CF's .094.
- Native: J45 ≥ J5 in at least four of the six fits, and J45 above the B01 CF fit on the same
  block in at least five of six.
- Gap: D1280 − CF_E stays positive on most blocks and is smaller than B01's on the same block.
  I expect a gap to remain because D's training return is also far above CF's; I do not put a
  number on it.
If the intermediate holds and the native fails, the entropy account of the decline is weakened
and (a) or (b) gains; if J improves without the entropy staying low, the gain is kept and the
story reconsidered.

**Reading.** Per fit: entropy, displacement, training return and J by rollout. Per value, three
paired differences against CF and against D1280 on J45 with mean and range; with three pairs a
t interval has df = 2 and is reported only as a description. Exploration: no MEI verdict, no
claim about the size of a matched-information gap. Selecting the better of two values on these
blocks and then comparing to D1280 on the same blocks is selection on the evaluation blocks;
any number quoted for the remaining gap carries that caveat, and a gap claim would need fresh
blocks and a claim note.

**Exposure.** 6 × 360,000 = 2,160,000 training team steps; CF measured about 6,800 s per fit at
four concurrent; two waves (four, then two). No extension whatever the scores show.

**What I would do with it.** Entropy account holds: the B01 comparator was not competent, the
RESEARCH row says so, and the next entry is a fresh-block comparison against the repaired flat
learner (and the question whether D's own entropy growth costs it anything). Account fails:
record which of (a), (b) the curves favour and stop tuning CF blind.

**Code (L0).** A thin entry `scripts/run_fsd_flat_entropy_b03.py` over the matched-information
runner: arms `CF_E005`, `CF_E0005`, the three blocks, stage-1 CF construction at the selected
multiplier with `lambda_l` overridden, a plan guard, a `reduce` that pairs with the B01 CF and
D1280 summaries and refuses any config difference other than `lambda_l` (against CF), and
reports the per-rollout diagnostics above; launch script on the admission kernel; tests for the
arm table, the single-field difference against the recorded B01 CF config, the plan guard and
the reduce. No learner, environment or evaluator change, so no shared-core review.

## 2026-09-19 14:59 PDT — flat entropy B03: entry code written and accepted

`scripts/run_fsd_flat_entropy_b03.py` (thin entry over the frozen B01 loop),
`experiments/candidates/flexible_skill_duration/flat_entropy_b03/launch_fit.sh`, six tests under
`tests/experiments/candidates/flexible_skill_duration/flat_entropy_b03/`. No learner, environment
or evaluator change, so accepted by the DM without an independent review.

The frozen runner knows one flat arm by name, so both arms run as its `CF` arm and carry
`entropy_arm` (`CF_E005`, `CF_E0005`) and `entropy_coefficient` in the summary. The plan guard
refuses anything but the six planned fits before the admission is spent. `reduce` reads the new
fits with this object's validator (recorded `lambda_l` must be the arm's, central input on) and
the B01 CF and D1280 fits with B01's own; a new fit whose configuration differs from the CF fit
of its block in any field other than `lambda_l` is refused. It reports, per fit, J by rollout
and the entropy, actor displacement, value loss and training return at rollouts 1, 5, …, 45,
and per arm the three differences against CF and against D1280.

Checks: 6 new tests pass; with the B02 tests in one process 12 pass; matched-information 57 and
baseline-interruption 18 pass. On the real configuration: the construction without an entropy
arm equals the `learner_config` recorded in `b01_s1_cf_772803_a01/summary.json` with no
differing field; each arm differs from it in `lambda_l` only; entropy targets and annealing are
off, and the learner reads `config.lambda_l` at every low-level update (`hmasd/agent.py`). The
six real reference summaries pass validation. One thing found while testing and fixed: the
summary wrapper is now installed for the duration of a fit only, so a fit of another object in
the same process is not marked as this one's (production runs one fit per process).

Launch order: both arms on 772803 and 772903 first (four concurrent), then both on 773003.

## 2026-09-19 15:02 PDT — flat entropy B03: first wave admitted on `wsl_4070`

Launch sha `051e8c7ab955a348fe868e6271eb72c77bbf50e3`, node idle beforehand (14 GiB free), node
checkout fast-forwarded to the published `main` first, each fit through
`flat_entropy_b03/launch_fit.sh` and the admission kernel, all admitted at the first request.
Alive with an empty `stderr.log` after the fourth admission; each manifest carries the declared
`entropy_arm`.

| tag | arm | block | operation ref (under `/home/wu/projects/HMASD/.git/hmasd-admission/`) |
| --- | --- | --- | --- |
| `b03_e005_772803_a01` | CF_E005 | 772803 | `01b1b6860d5d81d3cffca352fdd225807a42d9dd8ddb0ab0df8c0fec8187e19e.json` |
| `b03_e0005_772803_a01` | CF_E0005 | 772803 | `390679e9cb8ac4f0a047bd023aa4e2ed65557e004696e0b162ccfea3c6449ed1.json` |
| `b03_e005_772903_a01` | CF_E005 | 772903 | `7e2f391f470fff839905c8f3acac252e337915b771fe12025f2e794466c60225.json` |
| `b03_e0005_772903_a01` | CF_E0005 | 772903 | `6151fe9d6ced143f2125372ac5e4e0f231c00ff7ae9537f82ed34c3d563de7f7.json` |

Still to launch as slots free, same sha: both arms on 773003. No B03 score or diagnostic is read
before all six are terminal.

## 2026-09-19 17:00 PDT — flat entropy B03: all six fits admitted; two terminal

Execution facts only; no B03 score or diagnostic has been read. `b03_e005_772803_a01` and
`b03_e0005_772803_a01` ended with exit 0 and 45 rows; the two fits on 772903 were at 43 and 44
rows. Two slots were free, so the last two planned fits were launched at the same launch sha
`051e8c7ab955a348fe868e6271eb72c77bbf50e3`, after fast-forwarding the node checkout to the
published `main`. Both admitted at the first request, alive with an empty `stderr.log`. Never
more than four fits ran at once.

| tag | arm | block | operation ref (under `/home/wu/projects/HMASD/.git/hmasd-admission/`) |
| --- | --- | --- | --- |
| `b03_e005_773003_a01` | CF_E005 | 773003 | `52b55e115c94de5979881d30b8fde16b1975840be84923548ba05787306fa60d.json` |
| `b03_e0005_773003_a01` | CF_E0005 | 773003 | `d3890de28dc218231c0f9a8d0931ca8e06e34d6c69eaf89c7b1dda0a77bb0335.json` |

The plan is fully launched: six of six. Collection and the reduction wait for all six exits.

## 2026-09-19 18:05 PDT — flat entropy B03 read: the decline goes away, the flat learner still does not learn

Reads against the inspection entry and the prospective entry of 2026-09-19 (14:55 and 15:00 PDT).
Nothing was added to the plan after seeing scores. Exploration: no MEI verdict, no claim about
the size of a matched-information gap.

**Execution facts.** Six of six planned fits admitted at the first request on `wsl_4070`, launch
sha `051e8c7ab955a348fe868e6271eb72c77bbf50e3`, never more than four at once, all exit 0 with 45
rows, status complete, empty `stderr.log`; recorded `lambda_l` is the arm's in every learner and
evaluation config. One rsync, 54 files sha256-identical to the node. `reduce` complete, no
invalid input, every new fit differing from the CF fit of its block in `lambda_l` only;
`runs/flexible_skill_duration/b03_reduce/summary.json`, sha256
`73eb2fd72f298e0255e4288a7b5edf62c5492d722932639306ab85dde8d39ab2`. Wall 7,000–7,260 s per fit at
four concurrent, about 3,600 s at two; peak RSS 1.3 GiB.

**Observations.** J45 by block, with the completed B01 fits of the same block.

| block | CF (.05) | CF_E005 | CF_E0005 | D1280 | D1280 − CF | D1280 − E005 | D1280 − E0005 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 772803 | .075 | .267 | .329 | .456 | .381 | .189 | .127 |
| 772903 | .159 | .290 | .307 | .355 | .196 | .065 | .047 |
| 773003 | .080 | .290 | .235 | .499 | .419 | .209 | .265 |
| mean | .105 | .282 | .290 | .437 | .332 | .154 | .146 |

Both arms end above CF on all three blocks (+.13 to +.25) and below D1280 on all three. With
three pairs the t interval (df = 2) for D1280 − new is [−.04, +.35] and [−.13, +.42]: description
only.

Diagnostics at rollout 45, mean of three blocks (rollout 1 in brackets):

| | CF (.05) | CF_E005 | CF_E0005 | D1280 |
| --- | ---: | ---: | ---: | ---: |
| action entropy (4.3) | 8.91 | 4.45 | 3.96 | 7.46 |
| actor displacement (.027; D .153) | .093 | .071 | .071 | 1.156 |
| low-level value loss | .172 | .111 | .085 | .009 |
| training return U, rollouts 35–45 | 22.5 | 22.9 | 23.8 | 29.3 |

J within a fit moves a great deal from panel to panel (SD over the nine panels about .07–.08
for every flat fit, .06 for D1280), so J45 alone is a noisy reading of a fit. Window means,
computed after seeing the curves and therefore descriptive only:

| | CF (.05) | CF_E005 | CF_E0005 | D1280 |
| --- | ---: | ---: | ---: | ---: |
| early, panels 5–20 | .241 | .225 | .214 | .356 |
| late, panels 30–45 | .167 | .223 | .262 | .426 |

**Predictions, scored.**
- Intermediate, entropy at rollout 45 below 5.5: held in six of six (3.87–4.46).
- Intermediate, actor displacement at least twice CF's .094: failed in six of six. It is lower
  than CF's (.069–.073); CF's extra displacement is plausibly its own log-std parameter growing.
- Native, J45 ≥ J5 in at least four of six: five of six, but two of the five by less than .005.
  On window means: CF falls, E005 is flat, E0005 rises a little.
- Native, J45 above the CF fit of the block in at least five of six: six of six.
- Gap positive and smaller than B01's on the same block: six of six for both parts.

**Interpretation.**
- Strengthened: the entropy bonus is what made the selected flat learner's evaluated policy
  deteriorate. Cutting the coefficient stops the noise growth and removes the decline, ordered
  by dose in the window means (.05 falls, .005 flat, .0005 slightly up). On J45 this accounts for
  roughly half of the B01 gap on these blocks (.33 → about .15); on the late-window means for
  less (.26 → .16–.20), because CF's J45 happened to be low points and the new arms' high points.
- Weakened: my mechanism for it. I predicted that with less noise the actor would move further;
  it moved no further. The flat actor's displacement from initialisation is about .07–.09 under
  every entropy coefficient and about .15–.22 at the larger learning rates of stage 0, against
  1.15 for D's low-level actor. So "noise swamps the gradient on the mean" is not the reason the
  flat actor barely trains; something else keeps its updates small or incoherent.
- New, and the main thing this batch shows: with the decline removed, the flat learner does not
  learn in 45 rollouts. Its J stays in the .2–.3 band it occupies at rollout 5 (D1280 is in the
  same band at rollout 5 on two of three blocks and then climbs), its training return stays
  near 23 against D's 29, and its policy loss is of order 1e-4. What B01 measured as +.29 J is
  therefore one part comparator deterioration (removed here by one hyperparameter) and one
  part a flat learner that stands still while D learns.
- Not established: that a flat learner cannot learn on this host, that skills are why D
  learns, or any size for a matched-information gap. D's low-level actor optimises an intrinsic
  reward that includes the discriminator terms; whether its large displacement and its gain
  come from the skill structure or from having a denser learning signal is untouched. The two
  entropy values were tried on the blocks the gap is read on; three blocks.
- Simpler explanation (b) of the prospective entry ("the flat learner is simply poor on this
  host") gains, in the modified form "its actor is hardly being trained"; (a), an evaluation
  artefact unrelated to noise, loses.

**Decision.** The idea is ended with its six fits used; no extension. `lambda_l` = 0.0005 is the
better of the two flat settings seen so far and is recorded as such, not adopted as "the"
baseline: a baseline whose actor does not train is not the competent comparator the
constitution asks for.

**Next (not scheduled, no fit needed to start).** Read why the flat actor's updates are so
small: the `mappo` route's advantage computation and normalisation, the clip and minibatch
settings it actually runs with, the recorded policy loss, KL and clip fraction if present, and
what reward D's low-level learner is given, against the same quantities for D. That is code
reading and existing `training_rows`, zero fits. A fit-bearing entry follows only if that
reading names a modifiable link with a prediction of its own. Re-entry condition: that
inspection is written up, or the owner redirects.

## 2026-09-19 18:10 PDT — inspection (no new fit): the flat actor's updates are small because they are incoherent; the low-level minibatch is 320 samples

Follows the "Next" of the B03 reading. Code read: `hmasd/agent.py`
`update_discoverer_from_rollout`, `hmasd/utils.py` `get_discoverer_sampler`,
`hmasd/baselines.py` `apply_algorithm_config("mappo")`; data: `training_rows` of the completed
B01, B02 and B03 fits on blocks 772803–773003 (stage-0 blocks for the ×2 learning rate).

**Facts.**
- Flat and D low-level learners run the same update: GAE on the buffer, PPO clip, advantage
  normalisation *per minibatch*, recurrent chunks of k = 10 steps, 15 epochs. The minibatch is
  `sequence_batch_size` sequences, which no FSD config sets, so the default 32 applies: 32 × 10 =
  320 agent-steps per minibatch, 150 minibatches per epoch, 2,250 optimizer steps per rollout
  (matches the recorded `optimizer_calls_delta`). The config fields `num_mini_batch = 4` and
  `batch_size = 12000` exist but this sampler does not read them.
- Both learners receive the environment reward with weight 1. D's low-level reward adds the
  team and individual discriminator terms (weights .05 and .02), whose recorded per-step
  magnitude (−.038, −.017) is comparable to the environment component (+.034).
- Recorded low-level policy loss (the clipped surrogate after the epochs; 0 means the update did
  not improve the surrogate), and actor displacement per unit of learning rate × steps:

| arm | fits | policy loss, mean | last ten rollouts | displacement at 45 | displacement / (lr × steps) |
| --- | ---: | ---: | ---: | ---: | ---: |
| CF `lambda_l` .05 | 3 | +0.0002 | +0.0003 | .093 | .018 |
| CF .005 | 3 | −0.0006 | −0.0004 | .071 | .014 |
| CF .0005 | 3 | −0.0005 | −0.0003 | .071 | .014 |
| CF .05, learning rate ×2 (stage 0) | 2 | +0.0017 | +0.0020 | .219 | .011 |
| D1280 | 3 | −0.0258 | −0.0483 | 1.156 | .114 |
| D128 | 3 | −0.0259 | −0.0494 | 1.148 | .113 |

**Interpretation (working).** The flat actor takes as many steps as D's and moves an eighth as
far per unit of learning rate, and its surrogate does not improve: its steps largely cancel.
That is what gradient noise looks like, and the update law invites it: a team-shared,
long-horizon reward estimated on 320 samples with the advantages re-normalised inside each of
those minibatches. D's low-level learner runs the same law but also optimises discriminator
terms that each agent controls directly and immediately, which would give it a coherent
gradient whatever the minibatch. Conventional MAPPO practice is the opposite corner: one to a
few minibatches over the whole buffer, a handful of steps per rollout, learning rate around
5e-4. The flat comparator here has never been run that way.

Not established: that minibatch size is the cause (clip, the central-input actor, or credit
among six agents could each matter), or that D's gain comes from the discriminator signal. No
gradient statistics are recorded, and a probe that trains is a fit under section 3, so the
cheaper route is a direct learner test.

## 2026-09-19 18:15 PDT — prospective: flat learner with a conventional large-minibatch update (explore, six fits, package screen)

**Question.** Does the central-input flat learner learn on this host within 45 rollouts when its
low-level update uses whole-buffer-scale minibatches and a learning rate suited to the smaller
number of steps? This continues the comparator-competence question; B03 removed the decline and
left a learner that stands still.

**Package, declared.** Two things change together against the best flat setting so far
(`CF_E0005`: selected CF, `lambda_l` .0005): `sequence_batch_size` 32 → 1200 (four minibatches of
12,000 agent-steps per epoch, 60 optimizer steps per rollout instead of 2,250) and the
actor/critic learning rate. This screen forgoes attributing a change to either one.

**Arms.** `CF_M1`: learning rate 1e-4 (the standing base rate, multiplier 1.0). `CF_M5`: 5e-4 (the
usual MAPPO rate). Two rates because 37 times fewer steps at an unchanged small rate may simply
not move, and I have no measurement to pick one.

**Blocks and count.** Both arms on 772803, 772903, 773003: six fits, the whole default
allowance, 45 rollouts, panels 5…45, node `wsl_4070`. References on the same blocks, not
contemporaneous: the three B03 `CF_E0005` fits and the three B01 D1280 fits.

**Simpler explanations it must be told from.** (a) The flat learner cannot extract a usable
gradient from this reward at any batch size in 45 rollouts (credit among six agents, horizon):
then the surrogate improves (large batches make that easy) but training return and J do not.
(b) Steps too few: nothing moves, policy loss and displacement stay near zero.

**Predictions (signs).**
- Intermediate: mean policy loss at least five times more negative than CF_E0005's −0.0005 in
  both arms; actor displacement at 45 above .2 for `CF_M5`.
- Native: training return over rollouts 35–45 above 25 (CF_E0005: 23.8; D1280: 29.3) and the
  late-window J (panels 30–45) above CF_E0005's on the same block in at least two of three
  blocks, for at least one arm. I expect `CF_M5` to be that arm.
- Gap: D1280 stays above on most blocks. I hold this loosely; a flat learner that overtakes
  D1280 would be the most consequential outcome for the direction and is not excluded.

**Reading.** Per fit: J by rollout, window means (5–20, 30–45; declared now), policy loss,
displacement, value loss, entropy, training return. Differences against CF_E0005 and D1280 on the
same block, three pairs, description only. Exploration: no MEI verdict, no gap-size claim; the
settings are being tried on the blocks the gap is read on.

**Exposure.** 6 × 360,000 training team steps; wall unmeasured for this update law (fewer,
larger steps), planned as CF's 7,000 s. No extension whatever the scores show.

**What I would do with it.** Learns: this becomes the flat construction, and the next entry is
a fresh-block D1280 comparison against it with a claim note if the owner wants a confirmation.
Does not learn with a clearly improving surrogate: explanation (a) gains, and the question
moves from the optimiser to credit and information. Nothing moves: (b), record and stop
tuning blind.

**Code (L0).** Thin entry `scripts/run_fsd_flat_update_b04.py` as B03's: arms, three blocks,
CF_E0005 construction with `sequence_batch_size` and the two learning rates overridden, plan
guard, `reduce` pairing with the B03 CF_E0005 and B01 D1280 summaries. `sequence_batch_size` is
not among the snapshot fields, so the fit validator checks the behaviour instead: 60 low-level
optimizer steps per rollout, 2,700 per fit. Launch script, tests. No learner, environment or
evaluator change.

## 2026-09-19 18:14 PDT — flat update B04: entry code written and accepted

`scripts/run_fsd_flat_update_b04.py` (thin entry, same pattern as B03),
`experiments/candidates/flexible_skill_duration/flat_update_b04/launch_fit.sh`, six tests under
`tests/experiments/candidates/flexible_skill_duration/flat_update_b04/`. No learner, environment or
evaluator change (`sequence_batch_size` is an existing learner setting read by
`update_discoverer_from_rollout`), so accepted by the DM without an independent review.

Checks: 6 new tests pass, one of them a real tiny execution (real environment and agent, two
lanes, twenty-step episodes) in which a minibatch of 8 sequences gives exactly
epochs × 3 × rollouts low-level optimizer steps where the default would give epochs × 1: the
setting reaches the sampler. With the B03 and B02 tests in one process 18 pass;
matched-information 57 pass. On the real configuration: the construction without an update arm
equals the `learner_config` recorded in `b03_e0005_772803_a01/summary.json` with no differing
field; each arm differs from it in the two learning-rate fields only (1e-4, 5e-4), carries
`sequence_batch_size` 1200, and is expected to take 15 × 4 × 45 = 2,700 low-level steps, which the
fit validator requires of both low-level optimizers. The six real reference summaries (three
CF_E0005, three D1280) pass their own objects' validators through this entry.

Launch order: both arms on 772803 and 772903 first (four concurrent), then both on 773003.

## 2026-09-19 18:16 PDT — flat update B04: first wave admitted on `wsl_4070`

Launch sha `af66e79141f518be22c997d704e137bfd23419c2`, node idle beforehand (13 GiB free, no other
runner), node checkout fast-forwarded to the published `main` first, each fit through
`flat_update_b04/launch_fit.sh` and the admission kernel, all admitted at the first request.
Alive with an empty `stderr.log` after the fourth admission; each manifest carries the declared
`update_arm`.

| tag | arm | block | operation ref (under `/home/wu/projects/HMASD/.git/hmasd-admission/`) |
| --- | --- | --- | --- |
| `b04_m1_772803_a01` | CF_M1 | 772803 | `c361870b0978eb660bd3401d248ff89d8e61c644601e03b4df6fbe38442fb31d.json` |
| `b04_m5_772803_a01` | CF_M5 | 772803 | `bc7ba2e1a40c2661f2c33aa0ba177d099b0ff37ef8223f04fd051b8c60cfc9b2.json` |
| `b04_m1_772903_a01` | CF_M1 | 772903 | `a8213e81cf56f5c767b1863055382e0e53b0ec8fc64049557bab2f1351a0c7b5.json` |
| `b04_m5_772903_a01` | CF_M5 | 772903 | `38e599ade237554f247b396a76ab89bb86fed3aa7f79dbee621760ca8c344b31.json` |

Still to launch as slots free, same sha: both arms on 773003. No B04 score or diagnostic is read
before all six are terminal.

## 2026-09-19 19:05 PDT — flat update B04: all six fits admitted; two terminal; shared write with UCOPE

Execution facts only. `b04_m5_772803_a01` and `b04_m5_772903_a01` exited with code 0 and 45
training rows, empty `stderr.log`, about 50 minutes after admission at four concurrent (the
60-step-per-rollout update is much faster than the 2,250-step one; observed 60 low-level steps per
rollout in every fit). The last two fits were launched into the freed slots at the same sha, both
admitted at the first request, alive with an empty `stderr.log`; never more than four concurrent.

| tag | arm | block | operation ref (under `/home/wu/projects/HMASD/.git/hmasd-admission/`) |
| --- | --- | --- | --- |
| `b04_m1_773003_a01` | CF_M1 | 773003 | `e3f4c34c2463e0bc2fd5eb490eb634d9793ad03b499ddb8d2783b731897fd1e9.json` |
| `b04_m5_773003_a01` | CF_M5 | 773003 | `fbd3faaa8247a341dde470a04522d725d3f5b4f6e51e5dc5bd5308009407e21d.json` |

No B04 score or diagnostic is read before all six are terminal.

Shared write: by the owner's choice of 2026-09-19 a Codex session owns the reopened `ucope`
feedback-renewal branch in parallel with FSD, FOLR idle; Codex integrated PR #27 into `main`
(`801184245`). This session held its FSD writes to `main` until that merge (coordination note left
on the PR), then fast-forwarded its checkout and the `wsl_4070` checkout. The merge touches no FSD
path and not the FSD row of `RESEARCH.md`. UCOPE's first batch is planned on `local_linux` from a
separate worktree; this session touches no UCOPE file or `runs/ucope/` output.

## 2026-09-19 19:50 PDT — flat update B04 read: a conventional large-minibatch update changes nothing; the noise explanation is weakened

Reads against the inspection and prospective entries of 2026-09-19 (18:10 and 18:15 PDT). Nothing
was added to the plan after seeing scores. Exploration and a package screen: no MEI verdict, no
mechanism attribution between minibatch size, step count and learning rate, no gap-size claim.

**Execution facts.** Six of six planned fits admitted at the first request on `wsl_4070`, launch
sha `af66e79141f518be22c997d704e137bfd23419c2`, never more than four at once, all exit 0 with 45
rows, status complete, empty `stderr.log`; every fit took exactly 2,700 low-level optimizer steps
(60 per rollout) on both low-level optimizers, which the fit validator requires. One rsync, 54
files, the six `summary.json` sha256-identical to the node. `reduce` complete, no invalid input,
each new fit differing from the CF_E0005 fit of its block in the two learning-rate fields only
(the minibatch size is carried outside the config snapshot and proved by the step count);
`runs/flexible_skill_duration/b04_reduce/summary.json`, sha256
`67e2150cc287a2115397abe00d08073a300a3aed08b8ca4850e03d4ba39a2ae1`. Wall 2,640–3,720 s per fit at
four concurrent (CF_E0005: about 7,000 s), peak RSS 2.1 GiB.

**Observations.** Late-window J (panels 30–45, declared beforehand) and J45, with the completed
fits of the same block.

| block | CF_E0005 late | CF_M1 late | CF_M5 late | D1280 late | CF_E0005 J45 | CF_M1 J45 | CF_M5 J45 | D1280 J45 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 772803 | .290 | .254 | .321 | .432 | .329 | .282 | .353 | .456 |
| 772903 | .214 | .202 | .188 | .395 | .307 | .183 | .162 | .355 |
| 773003 | .283 | .222 | .257 | .452 | .235 | .181 | .230 | .499 |
| mean | .262 | .226 | .255 | .426 | .290 | .215 | .248 | .437 |

New minus CF_E0005, late window: CF_M1 −.036 (three of three below), CF_M5 −.007 (one above, two
below); both inside the panel-to-panel noise of a fit (SD about .07). D1280 minus new, late
window: +.201 and +.171, three of three positive for both arms.

Diagnostics at rollout 45, mean of three blocks (policy loss: mean over the fit):

| | CF_E0005 | CF_M1 | CF_M5 | D1280 |
| --- | ---: | ---: | ---: | ---: |
| optimizer steps per rollout | 2,250 | 60 | 60 | 2,250 |
| mean policy loss | −.0005 | −.0016 | −.0006 | −.026 |
| actor displacement | .071 | .062 | .085 | 1.156 |
| action entropy | 3.96 | 4.14 | 3.84 | 7.46 |
| low-level value loss | .086 | .212 | .269 | .009 |
| training return U, rollouts 35–45 | 23.3 | 23.1 | 24.9 | 29.2 |

Displacement does not scale with learning rate × steps: after rollout 1 CF_M5 has moved 4.5
times as far as CF_M1 (.042 against .009, the ratio of the rates), and by rollout 45 both sit
where CF_E0005 sat after 37 times as many steps at half of CF_M1's rate (.06–.10). The flat
actor goes a short, similar distance under every update tried and then stops; D's actor keeps
moving for 45 rollouts.

**Predictions, scored.**
- Intermediate, mean policy loss at least five times more negative than −.0005 in both arms:
  failed in both (CF_M1 about three times, CF_M5 unchanged).
- Intermediate, CF_M5 actor displacement above .2: failed in three of three (.075, .080, .100).
- Native, for at least one arm: training return over rollouts 35–45 above 25 and late-window J
  above CF_E0005 on at least two of three blocks: failed. CF_M5 passes 25 on one block (26.2)
  and is above CF_E0005 on one block; CF_M1 on none.
- D1280 stays above on most blocks (loosely held): three of three for both arms.

**Interpretation.**
- Weakened: my explanation that the flat actor stands still because 320-sample minibatches with
  per-minibatch advantage normalisation make its gradient mostly noise. A 37-fold larger
  minibatch, at the old and at the conventional MAPPO rate, leaves the surrogate no better and
  the policy no better. As a package screen this does not exonerate every component (a larger
  minibatch with many more steps was not run), but the result I said would follow from the
  noise account did not appear in either arm, and I will not rescue it with a third setting.
- Strengthened: the flat learner's failure is not an optimiser-setting matter. Four different
  update regimes (entropy .05/.005/.0005, 2,250 or 60 steps, rates .5e-4 to 5e-4) give the same
  picture: surrogate about zero, displacement saturating below .1, training return 22–25.
- Not predicted, seen in the diagnostics, so descriptive only: the flat critic does not fit. Its
  value loss stays at .07–.30 in every flat fit of B01, B03 and B04 while D's low-level value
  loss falls from .10–.18 to .02 or less by rollout 25 and about .01 by rollout 45. A critic that explains little of the return gives
  advantages that are mostly return noise whatever the minibatch. Whether the two critics are
  even fitting comparable targets (horizon, bootstrapping at skill boundaries, reward scale) I
  have not checked.
- Untouched: D1280's standing as the reference and B02's reading; the B03 reading that the
  entropy bonus caused the evaluation decline; whether an unfixed k helps (nothing here tests it).
- Contrary evidence I keep in view: D128 and D1280 learn with this same low-level code and the
  same 320-sample minibatches, so whatever stops the flat learner is something the flat
  construction lacks or has, not the update law by itself.

**Standing.** CF_E0005 remains the best flat setting seen; the B04 construction is not adopted
(no better, and a worse critic fit). The flat comparator is still not a learning baseline, so
B01's `D_REFERENCE_ABOVE` remains a statement about a comparator that does not learn. Fits used:
6 of 6; the batch is closed.

**Next.** As written beforehand for this outcome: stop tuning blind. Zero-fit inspection of what
the two low-level critics are asked to fit: how low-level returns and GAE are built for D and for
the flat arm (episode horizon against skill segment, bootstrap at skill boundaries, reward terms
and scale), and what explained variance each critic reaches in the recorded logs. A new
prospective entry only if that inspection yields a change with a predicted intermediate effect.

## 2026-09-19 19:55 PDT — inspection (no new fit): D's discriminator reward is a near-constant offset; both critics fit the same kind of target

Follows the "Next" of the B04 reading. Code read: `hmasd/agent.py`
`update_discoverer_from_rollout` (advantage and value-loss sections), `hmasd/utils.py`
`compute_gae`, the matched-information entry's CF description; data: `training_rows[].losses` of
the ten completed D fits (B01 D1280, B02 D128) and of the flat fits.

**Facts.**
- One code path builds the low-level targets for D and for the flat arm: GAE over the whole
  rollout buffer, gamma .99, lambda .95, no cut or bootstrap at skill boundaries, episode `dones`
  only. `use_valuenorm` is on in both, so the recorded low-level value loss is an MSE on a
  running-normalised return: roughly one minus the explained variance. Flat critics therefore
  explain about 70–93 % of return variance, D's about 99 %.
- The recorded reward components of D, per agent-step: environment .038 at rollout 1 rising to
  .056–.063; team discriminator term −.040 to −.044; individual term −.017 to −.018, in every
  one of ten fits at rollouts 1, 25 and 45. The discriminator terms are as large as the
  environment reward, not small as I wrote at 18:10, and they do not change over training.
  Discriminator losses stay at 1.72–1.76 (ln 6 = 1.79) and accuracies fall from .31–.37 to
  .24–.35 (chance .167): the skills do not become more distinguishable.
- The flat arm's per-step environment reward rises from .038 to about .05 (CF_E0005), D's to
  about .057, consistent with the training returns already recorded.
- D's action entropy climbs to 7.4 under the same `lambda_l` .05 that inflated CF's noise to
  8.9; D's evaluation does not decline with it.

**Interpretation.**
- Weakened: my 18:10 account that D's low-level learner moves because the discriminator terms
  give each agent an immediate signal it controls. In the recorded means those terms are an
  offset of about −.06 per step that training does not improve; a constant offset leaves GAE
  advantages unchanged after the critic absorbs it. Their per-sample variation is not logged, so
  this is weakened, not excluded.
- What remains different between the two low-level learners, all untested: the skill input (a
  one-hot held for k = 10 steps and chosen by a learning coordinator, which gives temporally
  extended, state-dependent variation in behaviour); the actor's input (D: own observation plus
  skill; CF: own observation plus the central snapshot, a much wider input); D's better critic
  fit, which may be cause or consequence.
- Three of my mechanism predictions have now failed in a row (B03 displacement, B04 surrogate and
  displacement, and this account of the discriminator terms). The observations are solid; my
  explanations of why the flat learner stands still are not. Before another fit I want the
  explanation challenged rather than extended.

**Next.** One critic pass on the working explanation and on which single observation would most
discriminate between the remaining differences. No fit is scheduled.

## Pro question 2026-09-19 flat-learner-stands-still-critic
Conversation: new (WSL Jev route; the address stays in the local operation file, named here by question key)
Question: Why does the matched-information flat learner (CF) not train on the UAV host while the hierarchical learner (D1280) trains with the same low-level update code, and which single next observation would most discriminate between the remaining explanations? The answer changes the DM's next prospective entry (or the decision to write none); it does not change any completed batch or its reading. This is a critic pass on the DM's belief update: the owner asked that this key criticism come from Pro. A local read-only critic runs in parallel as a comparison and its text is deliberately not in this notebook at the pinned revision.
Standing:
  Observations (completed, committed). B01: D1280 above CF by +0.290 J over five blocks, read `D_REFERENCE_ABOVE`; the selected CF declines over training. B02: D128 versus D1280 coordinator batch, no detectable difference, the batch law is dropped. B03: CF's evaluation decline was its entropy bonus (`lambda_l` .05) inflating the action noise; at .005 and .0005 the decline is gone, J45 rises from .105 to .28–.29 on three blocks, D1280 still above on all three; the flat actor barely moves from initialisation. B04 (package screen): CF at `lambda_l` .0005 with 1,200-sequence minibatches (60 optimizer steps per rollout instead of 2,250) at rates 1e-4 and 5e-4 changes nothing. In every flat fit of B01, B03 and B04: mean low-level policy loss (the PPO surrogate) about 0 (−.0005 to −.0016) against −.026 for D; actor displacement from initialisation saturates at .06–.10 whatever the learning rate × steps (D: 1.15 and still rising at rollout 45); normalised low-level value loss .07–.30 (D: about .01); training return over rollouts 35–45 of 22–25 (D: 29); late-window J .19–.32 (D: .40–.45).
  The DM's explanations so far, and their fate. (1) B03 prediction that removing the entropy bonus would at least double actor displacement: failed six of six. (2) 18:10 inspection account that 320-sample minibatches with per-minibatch advantage normalisation make the flat gradient mostly noise: B04's three predictions (surrogate five times more negative, CF_M5 displacement above .2, late-window J above CF_E0005 on two of three blocks) all failed. (3) 18:10 account that D's low-level actor moves because the discriminator terms give each agent an immediate controllable signal: the 19:55 inspection finds those terms are a near-constant offset of about −.06 per agent-step in all ten D fits, with discriminators near chance and not improving. Three mechanism predictions failed in a row; the observations stand, the explanations do not.
  What the DM currently believes remains different between the two low-level learners, all untested: (a) the skill input, a one-hot held for k = 10 steps and chosen by a learning coordinator (temporally extended, state-dependent behavioural variation); (b) the actor input, D: own observation (104) plus skill, CF: own observation plus the held central snapshot, reported as 853 wide at the same hidden width in the accepted implementation note, a point the earlier Pro answer in this notebook ("Pro question 2026-09-19 b01-after-stage0-next-step", section 1) already raised as a live simpler explanation; (c) D's better critic fit, cause or consequence unknown. Not yet excluded at zero fits: a construction detail or defect specific to the CF path (central snapshot at acting time versus in the replayed update, PPO ratio against mismatched log-probabilities, clip fraction saturating, gradient clipping at `max_grad_norm` .5 with the wide input, log-std handling, the `n_z = 1` path). Clip fraction, approximate KL, gradient norms and explained variance are not logged; that telemetry is missing, not diagnosed.
  Contrary evidence kept in view: D128 and D1280 learn with the same low-level code and the same 320-sample minibatches; D's action entropy climbs to 7.4 under the same `lambda_l` .05 without an evaluation decline; CF's training return does rise a little (19 to 22–25), so the flat learner is not strictly inert; every flat setting since B01 was tried on the blocks the D1280 comparison is read on, so no gap size is claimed.
Context:
  Governance: `docs/project/OPERATING_CONSTITUTION.md` sections 1, 3, 5, 7, 8 (source_sha). The owner's pause is lifted; FSD is active and led by the Claude session (`docs/research/RESEARCH.md`, pause line, the 2026-09-19 parallel-work paragraph and the `flexible_skill_duration` row, source_sha). Advice grants no fits and adds no gate. One fit is one started training attempt, so an instrumented training probe counts as a fit; an exploratory idea may use up to six.
  Method: `.agents/skills/hmasd-scientific-tools/SKILL.md` sections "Update the working explanation", "Explore an idea", "Comparators and MARL information", "Statistics", "Cost and exposure", and `.agents/skills/hmasd-scientific-tools/references/cumulative-research.md` (source_sha): they govern how a belief update separates observation from interpretation, what a targeted change must predict (an intermediate effect and a native consequence) and what a matched-information comparator must hold equal.
  Evidence: this notebook (source_sha), entries "2026-09-19 14:55 PDT — inspection of existing fits", "15:00 PDT — prospective: flat learner with a smaller entropy coefficient", "18:05 PDT — flat entropy B03 read", "18:10 PDT — inspection (no new fit): the flat actor's updates are small because they are incoherent", "18:15 PDT — prospective: flat learner with a conventional large-minibatch update", "19:50 PDT — flat update B04 read", "19:55 PDT — inspection (no new fit): D's discriminator reward is a near-constant offset", and the entry "2026-09-18 evening — CF comparator and B01 runner accepted". Reduced outputs `runs/flexible_skill_duration/b01_s1_reduce/summary.json`, `b02_reduce/summary.json`, `b03_reduce/summary.json`, `b04_reduce/summary.json`; per-fit `runs/flexible_skill_duration/{b01_s1_cf_*,b01_s1_d1280_*,b02_d128_*,b03_*,b04_*}_a01/summary.json`, field `training_rows[].losses` (policy loss, value loss, entropy, reward components, discriminator accuracy) and `relative_initialization_displacement` (source_sha).
  Code, actual learning path (source_sha): `hmasd/agent.py` `update_discoverer_from_rollout` (advantage computation, sampler call, central input in the replayed update near `_central_actor_input_from_replay`, ratio, clipping, value loss with ValueNorm, entropy term) and the acting-time central input near `central_input_flat`; `hmasd/utils.py` `get_discoverer_sampler` and `compute_gae`; `hmasd/networks.py` the skill discoverer's `central_input_dim` and `_apply_central_input`; `scripts/run_fsd_matched_information_baseline_b01.py` `make_config` (CF construction) and `scripts/run_fsd_baseline_interruption_b01.py` `make_config` (flat reduction, D arms); thin entries `scripts/run_fsd_flat_entropy_b03.py`, `scripts/run_fsd_flat_update_b04.py`.
  Frozen contract: `docs/research/candidates/flexible_skill_duration/FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md` sections 1, 3, 6 (source_sha) for what CF is required to be and how B01 was read. B01 is ended; nothing here reopens it or its labels.
Allowance: none is requested. Whatever follows is a new prospective notebook entry under the default per-idea allowance of constitution section 3 (up to six fits); zero-fit inspection of code and recorded logs is free.
Constraints: seeds and matched baseline per constitution section 8; no training, no edits
  outside the empty "### Answer" subsection; write only there on branch claude/fsd-pro-critic.
  Read the question at the pinned source, but fetch the latest target file before editing
  and use its actual blob SHA. Preserve all other bytes; stop on overlapping edits.
  On successful write, report the actual commit. On write failure return the complete
  answer in chat, not just a SHA, status message or link.
Return: a critic pass with diagnosis. (1) Is the DM's belief update sound: what the recorded evidence strengthens, weakens and leaves unresolved, including anything misread (does displacement really saturate regardless of learning rate × steps; is a near-constant discriminator mean enough to weaken the immediate-signal account; are the normalised value losses comparable across arms). (2) Any more mundane explanation that the code or the recorded logs can confirm or exclude at zero fits, in particular a construction detail or defect specific to the CF/flat path; for each concrete suspect give the file and function, and what it predicts in the recorded diagnostics. (3) The competing explanations that remain, each with its prediction for an intermediate quantity and for native J, and the strongest simpler alternative. (4) Among candidate next observations, which single one discriminates most per fit and what each outcome would imply: (i) D with both discriminator reward weights at 0; (ii) a plain flat learner without the central snapshot (own observation only); (iii) D with skills but a frozen or uniform-random coordinator; (iv) an instrumented probe of one CF and one D fit logging clip fraction, approximate KL, pre-clip gradient norm and explained variance; or a better one you propose, with fit and non-fit cost. Replication, a targeted repair or "no useful new fit yet" are legitimate answers. (5) What none of this can say about the direction's actual question (does an unfixed skill duration k help against a matched-information baseline), and whether the direction should keep spending fits on making CF competent. (6) Any decision-critical source you could not read. (7) MATERIAL_DISSENT yes/no on the DM's current belief update, one paragraph.
### Answer

*Saved from chat by the DM (2026-09-19): Pro read the repository at the pinned sha but its GitHub connector exposed no file-write action, so nothing was written on `claude/fsd-pro-critic`; `deliver` returned NOT_DELIVERED with no commit on that branch and the question unchanged. Chat text sha256 `146aed298e983c8a8dcce15ca3d133e1c9a639c909b6989e9669a05b6949e8ca` (26,672 characters). Wording unchanged; the three displayed formulas, which the chat rendered one symbol per line, are re-typeset on one line each, the two tab-separated tables are set as Markdown tables, and section titles are set as headings.*

Reasoning source: a41dbb31e5806d0b7c3e8958b6e74396406aa5cd. This critique leaves completed batches and their frozen readings intact.

#### 1. The DM’s belief update is partly sound, but several diagnostic inferences are not

The supported conclusion is narrower than “the flat learner’s failure is not an optimiser-setting matter.” B03 demonstrated a useful entropy-coefficient intervention: the selected CF’s evaluation deterioration disappeared, while the predicted increase in actor displacement did not occur. B04 failed to produce its specified rescue under the larger-minibatch/fewer-update packages at either learning rate. Those are reasons to abandon the particular predictions, not to exonerate optimization, input conditioning, or CF construction generally. Every intervention retained the same CF input-processing path. CF also is not literally inert: its training return rises somewhat, its parameters change, and B04’s learning rate affects early displacement. The descriptive diagnosis is limited learning under the tested constructions, not absence of training.

Displacement does not establish a learning-rate-independent stopping radius. The implemented statistic is

`d_t = ||θ_t − θ_0||_2 / ||θ_0||_2`,

over the actor parameter group, including its Gaussian scale parameters. It is neither cumulative update distance nor policy change on a fixed input distribution. Updates can reverse direction while this statistic barely changes; conversely, log-standard-deviation changes can increase it without improving the deterministic policy. CF and D also have different parameterizations and initialization norms.

The recorded B04 block 772803 illustrates the qualification. CF_M1 and CF_M5 move approximately .00907 and .04100 after rollout 1, but .05840 and .07513 after rollout 45. CF_M5 continues from .06917 at rollout 15 to .07513 at rollout 45: flattening, not an exact stop. The notebook also records larger displacements for higher-rate stage-0 CF fits, contradicting an unrestricted “every flat fit stays below .1.” That does not remove CF’s large descriptive contrast with D; it removes the claimed universal law. Learning rate multiplied by optimizer-call count is not a sufficient statistic for Adam trajectories with changing minibatches, advantages, clipping, and data distributions.

A near-zero PPO surrogate is not evidence of a near-zero gradient. This implementation centers and scales advantages within each minibatch. At the old policy, before any change in probabilities,

`L_policy = −mean(Â) = 0`,

yet

`∇_θ L_policy = −mean(Â ∇_θ log π_θ(a | x))`

need not vanish. The logged quantity averages losses across changing minibatches and update times; it is not fixed-batch improvement or a measurement of gradient coherence. Thus “surrogate about zero → gradient mostly noise → actor hardly trained” was not established. Clip fraction, probability-ratio consistency, gradient norms, and functional policy changes are needed to distinguish those possibilities.

The discriminator inspection is not a third intervention that falsified its mechanism. A stable rollout-average reward does not establish a nearly constant reward across transitions, states, agents, or actions. A zero-mean residual can still be the entire useful signal. The means weaken a story about increasing average discriminator reward; they do not, by themselves, appreciably weaken an immediate, controllable conditional signal. Likewise, the reported classification accuracies are not literally chance, and class frequencies matter when interpreting them. What is missing is the residual variation and its relation to actions, transitions, advantages, and subsequent native return. The notebook explicitly acknowledges that per-sample variation was not logged.

Even a genuinely constant per-step reward offset requires care. In a finite episode its value offset depends on remaining time. With the appropriately shifted, exact critic, the offset cancels in temporal-difference residuals. With an imperfect critic and a changing ValueNorm state, that cancellation need not hold during learning. Therefore “a constant offset is irrelevant after the critic absorbs it” is an idealized conditional argument, not evidence that absorption occurred here.

The ValueNorm losses cannot be converted into explained-variance percentages. The inspected low-level path does share primitive-time GAE, with episode termination rather than skill-boundary termination. However, D and CF have different rewards, policies, visited states, and skill-conditioned critic inputs. Their targets are GAE-derived returns, and each normalizer has its own history. The value loss is minibatch MSE against normalized—and potentially clipped—targets, averaged during optimization. It is not a final explained-variance measurement on a fixed dataset.

Ignoring target clipping for the moment,

`L_V = MSE(G, V) / σ²_running`, `EV = 1 − Var(G − V) / Var(G)`.

Equating `1 − L_V` with EV additionally requires matching variance denominators, zero residual bias, and matching prediction/target evaluation conditions. Those conditions were not shown. The estimates “CF explains 70–93%” and “D explains 99%” should therefore be withdrawn. D’s smaller logged loss remains an observation; superior native-relevant prediction, and whether it causes better actor learning, remain unresolved.

Finally, panel-to-panel variation is not the sampling uncertainty of a paired treatment effect. The B04 differences may be small and uncertain, but comparing them with within-fit panel SD does not establish equivalence. These corrections preserve B01’s frozen D_REFERENCE_ABOVE and B02’s bounded reading while substantially reducing confidence in the DM’s causal explanations.

#### 2. A concrete CF construction hazard is present: mixed physical units enter an unnormalized recurrent actor

The strongest mundane explanation found is not merely “853 inputs are harder than 104.” It is that CF adds metre-scale global coordinates to already scaled local features, without normalization before the GRU. The construction is confirmed; its proposed effect on learning is not yet measured.

The source chain is explicit:

MultiUAVEnv._get_state in envs/pettingzoo/uav_env.py concatenates raw UAV positions, raw user positions, and a normalized clock. For this host that is 18 UAV-coordinate entries, 100 user-coordinate entries, and one clock entry. The observation builders, by contrast, scale local positions and relative positions by area or height ranges and normalize SINR features. The actual runner constructs the Scenario 1 environment with its default 1,000-metre area and 50–150-metre height range; the generic configuration’s other environment defaults are not the bounds to use here.

ParallelToArrayAdapter._state_array casts and reshapes that state but does not scale it. The recorded CF learner and evaluator configurations have use_statenorm=false and use_obsnorm=false; accordingly, HMASDAgent._normalize_states returns the state unchanged. Calling the helper “normalize” does not make this input normalized.

_central_actor_input, its replay counterpart, and SkillDiscoverer._apply_central_input assemble and concatenate the held state, joint observations, and ego identity. The actor therefore receives 104+119+6(104)+6=853 entries with very different units. R_Actor sends these through MLPBase, then FiLM modulation, then the GRU. MLPBase contains two linear/ReLU layers, not an input normalization layer. RNNLayer applies LayerNorm after the GRU. SkillDiscoverer.Args explicitly disables feature normalization; moreover, the shown MLPBase.forward does not implement that option. Merely toggling a similarly named configuration flag is therefore not a demonstrated repair.

Mechanistic prediction: the appended coordinate block can dominate the actor’s pre-recurrent features, pushing GRU nonlinearities into saturated regions and reducing sensitivity to current private observations and ego identity. Post-GRU LayerNorm cannot undo a lost derivative through those gates. This predicts weak useful feature learning despite changes in the output head or log standard deviation, limited native learning, and little rescue from the entropy or minibatch interventions that leave this construction unchanged.

That prediction is compatible with the recorded symptoms, but the logs do not contain the required activations or layerwise gradients. I have confirmed an input-conditioning hazard, not demonstrated that CF’s gates saturate or that this explains the entire gap.

There is also important contrary evidence: both low-level critics ingest raw global state, and D still succeeds. Hence “raw coordinates make every network untrainable” is false as a general explanation. The CF-specific difference is that its primitive actor receives this heterogeneous input, while D’s primitive actor receives scaled local observations and skill conditioning. Different FiLM conditioning, target distributions, and learned parameters also prevent treating the critic comparison as a controlled saturation test.

Other concrete suspects have different evidential status:

| Suspect and location | What the source establishes, and its diagnostic prediction |
| --- | --- |
| Single-skill FiLM: networks.py::R_Actor, R_Critic; baselines.py::apply_algorithm_config | The flat switch makes both skill counts one; it does not remove FiLM. One-hot skill zero is [1], so the learned scale and offset are the linear layer’s column plus bias—not identity, but not an all-zero gate either. This leaves a parameterization/initialization interaction worth checking, especially with large inputs. It does not establish an n_z=1 dead-gradient defect. The prediction is a bottleneck localized to FiLM or its downstream activations, not necessarily a global zero gradient. |
| Acting/replay mismatch: agent.py central-input helpers, _batched_select_action, update_discoverer_from_rollout; utils.py::get_discoverer_sampler | The inspected layout, held-snapshot handling, environment/agent indexing, stored input hidden states, and shifted recurrent masks are structurally consistent. Disabled running input normalization also removes one possible source of changing normalization statistics in these fits. This is not a numerical equivalence test. A defect predicts nonzero replay log-probability error before the first optimizer step, at fixed weights and identical stored inputs/actions. |
| Missing optimizer coverage or clipped gradients: networks.py::actor_update_parameters; agent.py::update_discoverer_from_rollout | The widened actor’s parameters are included, actor and critic updates execute, and their gradient clipping is separate. This weakens “the new projection was omitted from Adam” and “the critic consumes the actor’s clipping allowance.” It does not exclude tiny feature gradients or excessive actor clipping. Those predict different layerwise norms and clipping multipliers; the existing total displacement and loss do not distinguish them. |
| Gaussian/action handling: r_mappo_utils.py::DiagGaussian; env_adapter.py::step; uav_env.py::step | The active Gaussian has no implemented log-standard-deviation clamp. Actions pass through the adapter; the environment clips resulting positions to spatial boundaries, not motion requests to a unit ball. The notebook’s cap/unit-ball account is therefore incorrect for this path. These are shared semantics, not a sufficient CF-specific explanation. They predict noise-dependent boundary occupancy and a stochastic-training/deterministic-evaluation difference. |

These conclusions come from the active implementations, rather than similarly named alternative distributions or configuration fields.

The strongest zero-fit numerical exclusion, given recoverable stored data, is a pre-update replay identity check: reconstruct the same policy inputs, hidden states, masks, and stored actions at unchanged weights, then inspect log-probability differences, ratios, approximate KL, and clip fraction. Ratios should be approximately one. A substantial discrepancy there is an implementation problem, not a finding about credit assignment. I did not execute that check.

#### 3. Competing explanations that remain

These are conditional predictions, not newly established mechanisms.

Input-scale/conditioning bottleneck — the leading simpler alternative. Intermediate prediction: scaling only the actor’s appended physical coordinates reduces their disproportionate contribution, reduces any observed gate saturation, and restores sensitivity and useful gradients from private/ego inputs to mean actions. Native prediction: CF shows greater within-fit improvement and higher late-window J than unchanged CF. The strongest simpler alternative is a better initial policy or changed feature weighting, rather than restored gradient flow specifically; an initialization panel and activation measurements distinguish that alternative.

A different CF implementation or parameterization bottleneck. Intermediate prediction: replay identity fails, clipping persistently suppresses otherwise useful actor gradients, or the constant-skill FiLM path accounts for the layerwise bottleneck after units are corrected. Native prediction: a repair of the identified link improves learning and J. The strongest simpler alternative is that these diagnostics are consequences of poor data or parameterization rather than the binding cause. No such defect has yet been demonstrated by the available telemetry.

Critic/advantage quality is the binding limitation. Intermediate prediction: after measuring actual target variance and residual bias, CF has poor predictive quality on a relevant fixed target, with noisy or uninformative advantages despite a functioning actor. A targeted critic improvement should improve those quantities before useful actor learning appears. Native prediction: subsequent training return and J increase. The strongest simpler alternative is that the apparent critic difference is a normalization/target-distribution artifact, or a consequence of D visiting more learnable states. Current normalized losses do not adjudicate this.

Skill conditioning and coordinated persistent behavior help learnability. Intermediate prediction: with implementation and conditioning problems removed, D still produces more useful state-dependent action variation or return-aligned policy gradients; removing learned coordination changes those quantities. Native prediction: an appropriately controlled frozen/random-coordinator D loses J if learned coordination is necessary in this package. The strongest simpler alternative is that persistent random context, easier parameterization, or a different training signal—not learned coordination—provides the benefit. This explanation concerns the fixed-k package, not flexible duration.

Discriminator reward supplies useful residual shaping. Intermediate prediction: transition-level discriminator residuals retain meaningful conditional variation and contribute to useful advantages despite stable overall means. Removing their actual contribution degrades useful policy learning if that shaping is necessary. Native prediction: D’s learning curve and J decline. The strongest simpler alternative is an optimization effect of changing target offsets, scale, and critic fitting, rather than useful skill-discrimination information.

These explanations can interact. In particular, good skill-conditioned behavior does not exclude a broken comparator, and a conditioning repair need not eliminate every remaining D–CF difference. The method guidance calls for separating such alternatives and predicting both an intermediate effect and a native consequence, rather than promoting whichever explanation remains after an unsuccessful batch.

#### 4. The most useful next observation is a targeted, same-information input-scaling contrast

My choice is a new CF construction that changes only the physical-unit scaling of the actor’s appended global-state block, with the relevant telemetry collected in that contrast. It addresses a concrete, verified construction hazard while retaining CF’s information, width, recurrence, and constant skill. It is more discriminating than another optimizer grid, less confounded than removing the snapshot, and more causally informative than merely observing two unmodified learners.

Use the stable CF_E0005 recipe as the comparator: entropy coefficient .0005, the original sequence-batch setting and selected actor/critic learning rates, k=10, and the same information interface. In the treatment, scale appended x/y coordinates by the actual environment’s area size and UAV altitude by its actual height range. Leave the already normalized clock unchanged. Leave own observations, joint observations, and ego identity unchanged. Apply the identical fixed transformation in collection, recurrent replay, and evaluation. A shared application point already exists in SkillDiscoverer._apply_central_input, which the low-level update also calls.

This transformation is information-preserving and changes neither width nor refresh opportunities. Do not simultaneously normalize the critic, enable global running-state normalization, remove FiLM, change reward weights, alter clipping, or increase width. Those would prevent attributing the result to this actor-input change. This is a new prospective construction, not a retroactive repair of the frozen B01 comparator.

The central observation is:

When CF keeps the same information and architecture but the appended coordinates no longer have a radically different scale, does useful policy learning recover?

The required intermediate measurement is not “total displacement exceeds .2.” Record input-block magnitudes and contributions, pre-GRU activation/gate behavior, and sensitivity of mean actions to private observations and ego identity on fixed probe inputs. Separate feature/FiLM/GRU/mean-head changes from log-standard-deviation changes. Add pre-update replay identity, clip fraction, approximate KL, pre-clip actor gradient norm and clipping multiplier. For the critic, record target variance, residual bias, and actual explained variance on clearly specified frozen samples, not 1 - value_loss.

Native assessment should include the pretraining level as well as within-fit improvement and the prospectively chosen late-window/final J quantities. Scaling changes the initialized policy’s function even with the same parameter draws. A higher final J caused entirely by a higher initial J would be useful comparator evidence, but not evidence that gradient flow recovered.

Interpret the outcomes separately.

Intermediate repair and improved native learning: strengthens the input-conditioning account and demonstrates a more competent flat construction on the tested conditions. It does not show that scaling explains the entire D–CF gap, or that skills are unnecessary.

Intermediate repair without native improvement: shows that the repaired feature was not sufficient; critic quality, reward/credit structure, and other representation limits remain. Do not rescue the account with an automatic second scaling setting.

Native improvement without the predicted intermediate change, or only a better initial policy: retain the practical gain, but revise the mechanism toward initialization or another representation effect.

Neither changes: weakens the specific scale-bottleneck explanation, provided the intended transformation actually reached all three paths. It does not establish that flat learning is impossible. A pre-update replay failure instead identifies an integrity problem whose dependent results require separate treatment.

Cost and scope. Source inspection and a forward-only check on recoverable stored tensors cost zero fits. An instrumented training attempt costs a fit even when called a probe or when unsuccessful. One paired treatment/control diagnostic costs two fits and remains exploratory. A seed-backed version of this single contrast can use three independent paired training blocks: six fits total, with no additional D fits or separate instrumentation batch. That is a possible prospective design within the existing allowance, not a grant or a requirement to consume all six. The constitution explicitly allows rough single-seed exploration while requiring at least three independent training seeds per arm for empirical learning claims.

At the existing 45-rollout law, six fits imply 2.16 million training team steps. The existing nine evaluation panels imply 864,000 evaluation team steps; one additional 32-world initialization panel per fit would add 96,000. Instrumentation adds measurement/storage overhead, not another training attempt; its wall overhead is unmeasured. Historical CF references could reduce new-fit cost for a localized exploratory observation, but do not remove the exposure and selection caveats or provide a fresh competence claim.

The alternatives in the question remain useful, but are lower priority for the present diagnosis:

| Candidate | What it discriminates, and what it would not establish |
| --- | --- |
| D with both discriminator reward contributions zero | Retained performance weakens necessity of those contributions in this package; lost performance supports their importance. Loss does not distinguish controllable residual shaping from target-offset/critic-conditioning effects. It leaves the concrete CF input hazard untouched. Verify the actual applied reward components, not just nominal fields. |
| Own-observation-only flat | Success implicates the appended-input construction, but simultaneously removes information and changes input width. It cannot distinguish scale from dimensionality or other representation effects and is not the matched-information primary comparator. Failure still does not establish hierarchy necessity. |
| D with frozen or uniform-random coordinator | Tests whether learned coordination is needed beyond skills/persistence and the remaining D machinery. A frozen initial network is still state-dependent and is not the same intervention as uniform random selection. Success weakens the need for learned coordination; failure does not demonstrate a flexible-duration benefit. |
| One instrumented CF and one instrumented D fit | Useful localization, but primarily observational and only one seed per arm. Large clipping or poor EV could be causes or consequences. Put these measurements into the targeted scaling contrast instead; include activation and per-module diagnostics that total norms alone miss. |

I would not start with a discriminator ablation merely because the most recent narrative concerned discriminator means. The next observation should address the strongest concrete competing explanation, not continue the order in which stories were proposed.

#### 5. Consequences for flexible skill duration and further comparator work

None of these observations establishes that an unfixed k helps. B01 compares complete methods with the declared central-information opportunities; it does not isolate hierarchy, and it does not estimate the interruption increment. B03/B04 modify flat learning. The proposed scaling contrast would establish, at most, something about the learnability of a fixed-information flat construction. Neither a recovered flat learner nor a remaining D advantage supplies the missing flexible-duration comparison. The frozen card explicitly maintains these limits.

Continue bounded comparator work, but stop blind tuning. A competent matched-information baseline is part of the direction’s actual scientific question, and the verified scale mismatch is a materially new reason for one targeted investigation. That is different from repeatedly choosing new hyperparameters until CF approaches D.

The stopping condition should concern information gained, not attainment of D’s score. A flat learner can be competent without winning. Conversely, larger parameter displacement or a more negative surrogate does not certify competence. If the targeted investigation fails to identify a useful learning improvement or a further specific causal link, record the unresolved comparator limitation and leave the next fit unscheduled. No new approval loop is needed, and no result automatically grants another batch.

#### 6. Source coverage and decision-critical gaps

I read the pinned question, the applicable governance and method sources, the relevant notebook entries, the frozen card, and the actual construction, acting, replay, loss, environment, and adapter code cited above. I used the named reductions and directly inspected representative CF and D per-fit configuration/loss records. I did not independently re-audit every row of every wildcard-matched fit; statements about all ten D fits’ reward means remain the notebook’s recorded inspection, not a newly reproduced all-fit reduction.

No governing source was inaccessible. The decisive empirical gaps are transition-level reward variation, saved replay equivalence, actor activations and layerwise gradients, and correctly defined critic prediction statistics. I did not load a checkpoint or execute a numerical replay/activation test. Consequently, the physical-unit mismatch and the active-code corrections are source-confirmed; GRU saturation, a PPO implementation failure, true critic EV, and the unique cause of the performance difference are not. Missing telemetry cannot be recovered by interpreting aggregate losses more confidently.

#### 7. MATERIAL_DISSENT: yes

The DM is right to stop blind tuning, retain the observed outcomes, and request criticism before another fit. I materially dissent from the stronger belief update: small relative displacement and a near-zero centered PPO surrogate do not show that the actor is untrained or its gradients incoherent; failed optimizer packages do not exonerate optimization and construction; stable discriminator means do not establish an uninformative immediate reward; and ValueNorm MSE does not justify the reported explained-variance percentages. Most importantly, the inspected CF actor concatenates raw physical coordinates with scaled local features without pre-GRU normalization—a concrete alternative untouched by B03/B04. The appropriate next step is a bounded, information-preserving test of that construction with intermediate and native measurements, not another hierarchy narrative. This dissent changes the proposed next observation, not any completed batch, frozen label, budget, or conclusion about unfixed skill duration.

## 2026-09-19 20:50 PDT — local critic (comparison to the Pro answer above), saved verbatim

The owner asked that the key critic pass come from Pro and that the local read-only critic
(`hmasd-research-critic`, launched before that instruction) finish as a comparison. Its report was
written without sight of the Pro question or answer, from `main` at `8f105a6bc`; it was kept out of
the notebook until the Pro answer was in, so neither text could lean on the other. The DM checked
its stage-0 displacement numbers, the rollout-1 displacements, D's skill entropies and coordinator
displacement, and the two `configs/config_1.py` fields against the recorded fits: they are as
reported.

> Critic pass on FSD, 2026-09-19 19:55 update. Read-only: no runs, no edits. All numbers below are from recorded `summary.json` files and source at current main (8f105a6bc).
> 
> ## Verdict in one line
> The update is mostly sound and the big conclusion ("the flat learner's failure is not an optimiser-setting matter") holds, but three of its supporting premises are contradicted by the record: displacement does scale with learning rate at matched update law; the normalised value loss is not comparable across arms; and D's coordinator is not learning, so hypothesis (a) as worded is false on the record. The discriminator-offset weakening, which I tried hardest to break, survives and is better supported than you stated.
> 
> ---
> 
> ## 1. Soundness of the belief update
> 
> **FACT — "displacement saturates at .06–.10 regardless of lr × steps" is wrong at matched update law.** At 2,250 steps/rollout the flat actor's relative displacement at rollout 45 is .091–.096 (lr 5e-5), .153/.158 (lr 1e-4, `b01_s0_cf_l1_772603_a02`, `b01_s0_cf_l1_772703_a01`), .217/.220 (lr 2e-4, `b01_s0_cf_l2_*`). Subtracting the log-std contribution (sqrt(3)·|H/3 − 1.4189| / ‖θ0‖, with ‖θ0‖ in `initial_parameter_norms.discoverer_actor` ≈ 46.1–46.3) the *network* part is .076 / .136 / .204 — i.e. essentially **linear in lr**. Your parenthetical at NOTES:1020 ("CF's extra displacement is plausibly its own log-std parameter growing") is exactly right and quantitative: B01 CF .0908 = .0592 log-std + .0688 network, and B03 E0005 .0687 = .0034 + .0686. The network moves the same distance under λ_l .05 and .0005; that is the clean statement. The true invariance is in *steps*, not lr: 37× fewer steps at the same lr costs only ~2.3× displacement (.136 → .058–.065). Neither a coherent-gradient law (∝ lr·steps) nor a diffusive one (∝ lr·√steps) reproduces B03 vs B04; both predict a large difference and none appeared. That is a stronger fact than "saturates", and it points at a near-stationary point rather than at noise accumulation.
> 
> **FACT — the surrogate and the displacement are not two independent observations.** `discoverer_policy_loss` is −E[min(rA, clip(r)A)] evaluated at the current parameters with advantages normalised per minibatch (`hmasd/agent.py:6485-6491`); at ratio ≡ 1 it is identically 0. So "surrogate ≈ 0" is a statement about how far the policy drifted from the behaviour policy inside the epochs — nearly the same quantity as displacement, not evidence about gradient quality. Two of your three "failed predictions" (B03 displacement, B04 surrogate + displacement) are therefore one failed prediction measured twice, on optimiser-side accounts that your own contrary evidence (D128/D1280 learn with the identical update law) already argued against. The run of failures is less damning than the notebook implies. What the surrogate *does* add is its **sign**: CF's mean is positive and grows with lr (+.0002 at 5e-5, +.0010 at 1e-4, +.0017 at 2e-4) — the pessimistic clip branch dominating, i.e. updates that do not improve the objective on re-sampled minibatches — while B04's large-batch arms turned it negative (−.0005 … −.0018) without producing movement or return. The stage-0 lr sweep, not B04, is where the "incoherent" account has support.
> 
> **FACT — the value loss is not comparable across arms.** `value_norm_discoverer` is an SB3 `RunningMeanStd` (`hmasd/agent.py:1036-1037`), full-history, no decay, updated once per rollout over all 48,000 returns (`:6319-6322`), and the loss is MSE against (R − m_hist)/s_hist (`:6496-6508`). It equals 1 − EV only if the return distribution is stationary. It is not: CF's mean predicted value rises 0.45 → 3.7–4.5 over the run while D's stays near zero (−0.86 → −0.15), because D's discriminator terms almost exactly cancel its environment reward (`avg_intrinsic_reward` −.022 → −.002 for D, +.038 → +.055 for CF). A current-rollout return SD that exceeds the history SD inflates the recorded loss by (σ_cur/σ_hist)² with no change in critic quality, and predicts exactly what CF shows: a loss that *rises* (.083 → .13–.25) while the critic keeps moving. So "flat critics explain 70–93 %, D's 99 %" (NOTES 19:55) is not established. Two further confounds in the same comparison: CF's critic displacement is .31–.35 at the selected lr and .49–.72 at lr 1e-4/2e-4, i.e. **equal to or larger than D's .48–.53** — the flat critic is not frozen; and the B04 arms had 2,700 total critic updates against B03's 101,250, so "the B04 construction has a worse critic fit" (NOTES 19:50 Standing) is confounded by step count and should not have counted against it.
> 
> **FACT — hypothesis (a) as worded is contradicted.** You describe D's skill input as "chosen by a learning coordinator (temporally extended, state-dependent behavioural variation)". In all ten D fits `agent_skill_entropy` is 1.74–1.78 against ln 6 = 1.7918 at rollouts 1, 5, 15, 25 and 45, `team_skill_entropy` 1.47–1.71, and the coordinator's relative displacement ends at .049 (r1 .008). The coordinator stays a near-uniform random assigner for the whole run. Whatever the skill channel does for D's low-level actor, it is **a near-uniform random 6-way FiLM modulation re-drawn every 10 steps**, not a learned state-dependent decomposition. This kills your candidate (iii) as an experiment (a frozen/uniform-random coordinator is what D already effectively has, so it predicts no difference) and it re-words (a): the live claim is "temporally extended random behavioural modulation + a 6-row FiLM channel", which is testable but is not the DIAYN story.
> 
> **FACT — no log-std cap on this path.** `DiagGaussian` (`hmasd/r_mappo_utils.py:73-95`) uses `AddBias(torch.zeros(num_outputs))` and ignores `continuous_logstd_min/max`; those are read only by `TanhDiagGaussian` (`:112-127`), selected by `continuous_action_distribution`, which `E0Config` never sets, so `networks.py:1608` falls back to "gaussian". Evidence: `b01_s0_cf_l2_772603_a01` ends at entropy 10.32, above the "cap" of 10.26 quoted at NOTES:818-819. This does not change the B03 conclusion (cutting λ_l stopped the growth); it removes the cap from the narrative.
> 
> **SURVIVES — the discriminator-offset weakening.** I tried to break it and could not. `legacy_mi_reward_coef = 0.5` (`configs/config_1.py:316`), so the effective weights are 0.025 and 0.01, not the .05/.02 written at NOTES:1080; and `use_prior_corrected_intrinsic = False` (`:288`) so the term is 0.025·log q with no +ln n_z (`hmasd/agent.py:1158-1166`, `:4826-4827`). Back-solving the recorded components gives mean log q_team = −1.67 and log q_ind = −1.75, matching both the recorded discriminator losses (1.72, 1.76) and the skill-marginal entropies (team 1.47–1.71, individual 1.75–1.78). A discriminator that has learned only the marginal skill frequency and ignores the state produces exactly these numbers *and* the observed accuracies (team .30–.38 ≈ max_Z p(Z) at entropy 1.47–1.71; individual .24–.28 against a near-uniform marginal). So the record is consistent with a **per-skill constant** the low-level actor cannot control, which is your conclusion. Two refinements: "discriminators near chance" understates it (they encode the marginal, which is why their accuracy beats 1/6 without any state information), and per-sample variance is still unlogged, so this is consistency, not proof.
> 
> ---
> 
> ## 2. Mundane explanations: what I checked and cleared, and the one suspect that survives
> 
> Cleared at zero fits:
> - **Central snapshot, acting vs replay.** Stored raw per step (`agent.py:4101` → `utils.py:418-447`), refusal if any row is missing (`utils.py:1285-1289`), env-major chunking (`:1290-1291`) with `env_sequence_indices = batch_indices // n_agents` and `ego = batch_indices % n_agents` (`:1353-1354`), which matches the acting layout `np.repeat(per_env, n_agents)` + `np.tile(np.eye(n_agents))` (`agent.py:1340-1341`). `use_obsnorm = use_statenorm = False` in every recorded `learner_config`, so `_normalize_*` are identity (`agent.py:1502`) on both sides and the replay is bit-exact, as NOTES:90-92 claims. No detach, no shape error, no staleness bug.
> - **Ratio / log-probs.** `old_log_probs` are the stored acting log-probs; valid-mask filtering is applied to policy and value (`:6472-6482`). One inert nit: the entropy term (`:6521`) is not masked and not `active_masks`-weighted, but with 500-step rollouts equal to the episode length every mask is 1, so it changes nothing here.
> - **max_grad_norm 0.5 with a wide input.** Clips both arms identically; with Adam the per-parameter step is ~lr regardless, so clipping cannot produce the 8.6× network-displacement gap at matched lr.
> - **Learning rate.** Excluded at zero fits: CF at D's own rate (1e-4, stage-0) and at 2e-4 also fails to learn — J goes .293→.116 and .171→.074 (lr 1e-4), −.043→.132 and .113→.068 (lr 2e-4). You can drop "CF ran at half D's rate" from the list of live differences and cite these two fits.
> - **Parameter-count artefact in the displacement metric.** ‖θ0‖ is 46.05–46.35 (CF) against 41.07–41.18 (D), so the denominators are comparable; and CF has ~190k *more* actor parameters (853×256 vs 104×256 first layer), which under any noise-driven motion would make ‖Δθ‖ larger, not smaller. The metric does not flatter D.
> 
> **The suspect that survives, and it is your (b): input dilution.** `_central_actor_input` (`agent.py:1316-1341`) builds 853 dims = own obs 104 + held state 119 + six held joint observations 624 + ego one-hot 6. Of those, **743 are byte-identical across the six agents of a lane and constant inside each 10-step chunk**; the agent's own *current* observation is 12 % of the input energy and its only private identifier is a 6-dim one-hot, in a trunk with `use_feature_normalization = False` (`networks.py:1606`) and orthogonal init. Conjecture (mine, not established): the six agents' gradients through the shared trunk are then nearly parallel while their advantages differ per agent, so the agent-distinguishing component of the update is a small fraction of the gradient and largely cancels. Prediction already visible in the record: the asymmetry must exist at the **first** update, before any learning difference can exist — and it does. At matched lr 1e-4, rollout-1 actor displacement is .0396/.0440 for CF and .151–.172 for D (3.7×). That single number is the most useful unused fact in the direction: it forbids any account of the form "D's actor moves because D is learning and CF is not".
> 
> Second-order construction asymmetry worth one line in the notebook: with n_z = 1 the FiLM generator is `nn.Linear(1, 512)` (`networks.py:1418`), so CF's feature modulation γ is drawn from a bound of 1/√1 while D's is 1/√6 — CF's trunk gain is ~2.5× D's at init, and CF's FiLM channel has 512 effective dof against D's 6 separate rows gated per sample. Nobody chose this; it rides along with the `mappo` switch (`hmasd/baselines.py:127-148` sets n_Z = n_z = 1, λ_D = λ_d = 0, discriminators and high-level training off).
> 
> ---
> 
> ## 3. The single most discriminating next observation
> 
> **Recommend (ii): a plain flat learner with the central snapshot off.** Reasons, in order of weight:
> 1. It is the only live difference that has never been varied: all twelve flat fits carry the 853-dim input.
> 2. It is a **single-field change against an exactly matched recorded reference**. Run it at D's low-level settings (lr 1e-4, λ_l .05, 2,250 steps, k = 10, 45 rollouts) on blocks 772603/772703 and the reference is `b01_s0_cf_l1_772603_a02` / `b01_s0_cf_l1_772703_a01`, which differ in the flag alone.
> 3. Both endpoints of the read are already calibrated, and the read arrives at **rollout 1** (~70–150 s of wall): CF .040/.044, D .151–.172.
> 4. Either outcome moves the direction. Learns → the "matched-information" comparator was crippled by how the information was delivered, B01's +.29 is a representation artefact, and the comparator question reopens as a representation question. Stalls → the central input is exonerated, the flat MAPPO learner genuinely does not learn here in 45 rollouts, and that is the honest caveat on any D-versus-flat statement.
> 5. Nearly no code: the frozen runner already has a validated FLAT arm at k = 10 (`scripts/run_fsd_baseline_interruption_b01.py:24, 49-66, 329-340`); a thin entry in the B03/B04 pattern suffices.
> 
> Design note, cheap: two fits, not one — one at (1e-4, λ_l .05) on 772603 for the clean *mechanism* read against the CF-l1 twin, one at (5e-5, λ_l .0005) on 772803 for the clean *outcome* read against `b03_e0005_772803_a01`, because at λ_l .05 the entropy blow-up will make J uninterpretable again. Each is a single-field change from its own reference. Declare: intermediate = network displacement (log-std part subtracted) ≥ .10 at rollout 1 and ≥ .4 at rollout 45; native = training return U over rollouts 35–45 ≥ 26 (flat fits 22–25, D 29.2) and late-window J above the matched reference. Intermediate passes with native failing would mean the wide input limited parameter movement but not the outcome.
> 
> **The designated follow-up, (i) D with λ_D = λ_d = 0**, is the arm that splits the remainder if the plain flat stalls: it is D minus the reward difference, so against recorded D1280 it tests the discriminator terms, and against the plain flat it tests the skill channel. Set the two weights only — do not set `disable_discriminator_rewards`, which also flips `use_discriminator_path` (`agent.py:531-534`) and changes construction and RNG. Note that it changes the coordinator's high-level reward too, which is tolerable only because the coordinator barely learns. Bonus: it tests my ValueNorm objection for free — with env-only reward D's return starts drifting like CF's, so if its recorded value loss climbs from .006 toward .1+ while its actor still moves and J still rises, the "critic fit" difference between the arms is an artefact of the full-history normaliser and can be struck from the list of live differences.
> 
> Against the others: **(iii) frozen/uniform-random coordinator is already what D runs** (skill entropy ≈ ln 6 throughout, coordinator displacement .049) and would spend a fit to reproduce D. **(iv) the instrumented probe** costs a fit to produce numbers that need a second D fit to interpret, and its main prize — pre-clip gradient norm, to tell "vanishing gradient" from "cancelling gradient" — is only weakly decision-relevant because Adam normalises the step anyway. If you judge that the precedent at NOTES:111-115 (one rollout, full training shape, outside `runs/`, no endpoint, no admission, recorded as not a fit) covers it, then instrumenting rollout 1 of CF and of D is much cheaper than a fit and targets exactly the place where the asymmetry is already visible — but that classification is your call, not mine, and I am not recommending you reclassify a training attempt to save budget.
> 
> ---
> 
> ## 4. Inherited contrary evidence, and limits
> 
> Keep in view: D128 ≡ D1280 on every low-level diagnostic (coordinator capacity is irrelevant, and the update law is not the obstacle); the coordinator does not learn and the discriminators do not separate skills, so D's gain cannot be attributed to skill discovery in any DIAYN sense; D's actor already moves 3.7× further than CF's after the *first* rollout at matched lr; CF's critic moves as much as D's; B01's D_REFERENCE_ABOVE remains a statement about a comparator that does not learn, and B03 showed roughly half of it was comparator deterioration; panel-to-panel J SD is .06–.09 for every flat fit, so no single-fit J difference below ~.1 is readable, and every setting since B01 was tried on the blocks the gap is read on.
> 
> Limits of this pass: I ran nothing and measured no gradients; the input-dilution mechanism is conjecture supported only by being the untested difference plus the rollout-1 asymmetry; the ValueNorm inflation factor is a mechanism argument with no measured σ_cur/σ_hist because return SDs are not logged; and the discriminator-variance question remains unlogged either way.
> 
> Limit on the direction: **none of B02–B04, and none of the fits I recommend, tests an unfixed skill duration k.** Twelve fits since B01 have gone into comparator repair and the next two would make fourteen. Worth recording as an option rather than a recommendation: the k-axis question (D0 versus the interruption arm I, both hierarchical, both learning) is answerable *within* the D family with D as its own control and needs no competent flat baseline; a flat baseline is needed for "hierarchy helps", not for "unfixed k beats fixed k". If the plain-flat fit stalls, that may be the cheaper road back to the direction's own question, with the flat comparator recorded as an open caveat rather than a prerequisite.
> 
> MATERIAL_DISSENT: yes — two premises the current explanation rests on (displacement is insensitive to lr; the normalised value losses are comparable as explained variance) are contradicted by the recorded runs, and the "learning coordinator" wording of hypothesis (a) is contradicted by the logged skill entropy, though the headline conclusion and the discriminator-offset weakening both survive.


## 2026-09-19 21:00 PDT — response to the Pro critic pass (and the local comparison): inferences withdrawn, one concrete construction hazard adopted as the next thing to test

Both critics return MATERIAL_DISSENT yes, on the belief update and not on any completed batch.
I read both in full. The owner's own note of the same evening makes the same three points about
the diagnostics (a near-zero centred PPO loss is not a near-zero gradient; a running-normalised
value loss is not explained variance; a stable mean discriminator reward says nothing about the
per-sample signal). What follows is what I adopt, modify and reject, and what changes.

**Delivery facts.** Question key `hmasd:aa7e79bf…b94ff`, sent once through the Jev route
(`send_effect` sent, effort `6 Pro`, document attached and seen), completed, answer kind "chat
answer": Pro's connector could read but not write, so the text above is saved from chat; the
branch `claude/fsd-pro-critic` carries no answer commit. No decision-critical source was
unreadable to Pro; it did not re-audit every fit and ran nothing.

**Withdrawn (both critics, and I agree after checking the record).**
- "Displacement saturates at .06–.10 whatever the learning rate × steps" (B04 read). At the
  original update law the flat actor's displacement at rollout 45 is .09, .155 and .22 at rates
  5e-5, 1e-4 and 2e-4 (stage-0 fits): about linear in the rate. What the record shows is a weak
  dependence on the number of steps (37 times fewer steps, about 2.3 times less displacement),
  and a statistic that mixes the network with the log-std parameter and is not policy change.
- "Surrogate about zero, so the gradient is mostly noise / updates cancel" (18:10 inspection).
  With advantages centred per minibatch the logged loss is 0 at ratio 1 whatever the gradient.
  Surrogate and displacement are close to one observation, so my "three failed predictions" were
  nearer two, both about quantities that did not measure what I took them to measure.
- "Flat critics explain 70–93 % of return variance, D's 99 %" (19:55) and "the B04 construction
  has a worse critic fit" (19:50 Standing). The normaliser is a full-history running statistic,
  targets may be clipped, CF's return level drifts while D's stays near zero, and B04's critic
  took 37 times fewer steps. D's smaller logged loss stays an observation; nothing about critic
  quality follows. The flat critic's own displacement (.31–.72) is as large as D's (.48–.53).
- "Log-std is capped at 2.0 and actions are clamped to the unit ball" (14:55 inspection). The
  active `DiagGaussian` has no clamp (one stage-0 fit ends at entropy 10.32, above that "cap") and
  the environment clips positions, not action requests. B03's reading does not depend on it.
- "Chosen by a learning coordinator" (19:55, difference (a)). In all D fits the agent-skill
  entropy stays at 1.74–1.78 against ln 6 = 1.79 and the coordinator's displacement ends at
  .049: D's skills are, in effect, drawn near-uniformly at random every ten steps for the whole
  run. Candidate (iii) of my question would re-run what D already is.
- B04's "inside the panel-to-panel noise of a fit" is not a statement about the uncertainty of a
  paired difference (Pro). The B04 differences are small and uncertain; no equivalence is read.

**Discriminator terms: the two critics differ; my position.** Pro: a stable mean hardly weakens
an immediate-signal account, and even a constant offset cancels only with an exact critic. The
local critic: the recorded components back-solve (effective weights .025 and .01, since
`legacy_mi_reward_coef` = .5) to log q equal to the skills' marginal entropy, which is what a
discriminator that ignores the state produces, i.e. a per-skill constant the primitive actor
cannot influence. I keep "weakened, not excluded", now resting on the second argument rather
than on the mean alone; per-sample variation remains unlogged.

**Adopted: a concrete construction hazard in CF that none of B03/B04 touched (Pro).** Checked at
source by me: `MultiUAVEnv._get_state` concatenates raw UAV and user positions in metres (area
1,000 m, heights 50–150 m) plus a normalised clock; `use_statenorm` and `use_obsnorm` are false
in every recorded config, so `_normalize_states` is the identity; the CF actor therefore reads
118 entries of order 10²–10³ next to 734 scaled entries of order 1, through two linear/ReLU
layers and FiLM into the GRU with no normalisation before it. By the environment's bounds the
raw block carries essentially all of the input's squared norm (order 10⁷ against 10²–10³); this
is arithmetic from the bounds, not a measured activation. D's primitive actor reads only scaled
local observations plus the skill. The local critic found the neighbouring fact (743 of 853
entries identical across a lane's agents and constant within a chunk) and the most useful
recorded number: at the same rate 1e-4 the actor's displacement after the *first* rollout is
.040/.044 for CF and .151–.172 for D, so the asymmetry exists before any learning difference
can. It missed the units: it treated "normalisation is the identity on both sides" as clearing
the input path. The two readings are compatible; Pro's is the sharper and keeps the information.
- Contrary evidence kept: both low-level critics read the same raw state and D still learns, so
  raw coordinates do not make every network untrainable (Pro).
- A conjecture of mine that this raises, untested: D's coordinator embeds the same raw state
  through one linear layer and barely moves (displacement .049, skill choice near uniform). If
  the same scale problem silences the coordinator, then B02's "coordinator batch makes no
  difference" is what a coordinator that does not learn would show, and it bears on this
  direction's own question, because any duration or interruption decision lives at that level.

**Rejected or deferred.**
- Own-observation-only flat first (local critic's recommendation): it removes information and
  width at once and leaves the matched-information comparator where it is; Pro's objection
  holds. Deferred, not dismissed: its rollout-1 read is cheap.
- D with discriminator weights at zero: deferred; it does not address the confirmed hazard.
- A separate instrumented CF/D probe: rejected as a separate batch; a training probe is a fit.
  Measurements belong inside the targeted contrast.
- The local critic's option of answering the k question inside the D family without a competent
  flat baseline: kept as an option for the next portfolio look, together with the coordinator
  conjecture above. Neither critic's advice, nor anything in B02–B04, tests an unfixed k.

**How the two critiques compare (the owner asked).** Agreement on every withdrawn inference
above. Pro alone: the unit mismatch, the conditional nature of the constant-offset argument, the
panel-noise point, the insistence on a pretraining level and on functional rather than
parameter-distance measurements. Local critic alone: the quantitative record (linear-in-rate
displacement with the log-std part separated, the rollout-1 asymmetry, the coordinator's
near-uniform skill choice, the effective discriminator weights, CF failing at D's own rate) and
the FiLM `nn.Linear(1, 512)` initialisation asymmetry. Pro was the better judge of what the
diagnostics can support and found the decisive construction fact; the local critic was the better
auditor of the recorded numbers. They are complements; the key pass goes to Pro from now on.

**What changes.** My working explanation is now: CF's limited learning is unexplained; the
leading concrete candidate is an input-conditioning bottleneck from raw-metre coordinates in the
actor's input, present from the first update; skill-channel, reward-residual and critic accounts
remain open and unranked behind it. B01's label and the B02/B03/B04 outcome readings stand.

**Next.** One prospective entry: CF_E0005 with the appended physical coordinates scaled by the
environment's own bounds, identical in acting, replay and evaluation, nothing else changed, paired
with the completed CF_E0005 fits on the same three blocks; intermediate reads that are functions
of the policy rather than parameter distance, and the initial-policy level so that a better
start is not mistaken for restored learning. The change touches the shared learner, so it goes
through the Implementer and an independent Reviewer before any fit.

## 2026-09-19 20:40 PDT — prospective: CF with the appended physical coordinates on the observations' own scale (explore; a zero-fit forward probe, then three fits)

(The two entries above carry heading times 20:50 and 21:00; they were written between 20:15 and
20:30 PDT. This entry's time is the clock's.)

**Idea, targeted (not a package).** The CF actor reads the held global state as raw metres (x, y
in 0–1,000; UAV height 50–150) beside 734 entries scaled to order 1, with no normalisation before
the GRU. The change: inside the actor's appended block only, map the state's coordinates with the
same affine convention the environment already uses for an agent's own position in its
observation (x and y divided by the area size; UAV height as (z − 50) / 100; the normalised clock
untouched). Nothing else: same information, same width, same held-snapshot clock, same FiLM,
GRU, critic (still raw state), rewards, update law. Construction otherwise exactly CF_E0005
(`lambda_l` .0005, rate multiplier .5, default 32-sequence minibatches, k = 10, 45 rollouts).
Identical in acting, replayed update and evaluation. Flag off: bit-identical to today.

**Step 1, zero fits: forward-only probe at initialisation**, per block (772803, 772903, 773003),
for the unscaled and the scaled construction from the same seed: one evaluation panel of the
untrained policy (32 worlds, the block's evaluation seeds) giving J_init; and on the inputs met
in that panel, (a) the share of the first layer's pre-activation squared norm that comes from
each input block (own observation, state, joint observations, ego), (b) the GRU's update/reset
gate saturation (fraction of gate units below .05 or above .95), (c) the sensitivity of the mean
action to the agent's own current observation and to its ego one-hot (finite perturbation of
fixed relative size, mean absolute change in the mean action). No optimizer step anywhere; policy
execution of 2 × 3 × 32 evaluation episodes is recorded as exposure, not as a fit.
- Expected (unscaled): the state block gives more than 90 % of the first layer's pre-activation
  norm; own-observation and ego sensitivities are small.
- Expected (scaled): the state block's share falls below one half; own-observation sensitivity
  rises by at least a factor of three. Gate saturation: expected lower when scaled; loosely held,
  because two ReLU layers and orthogonal init with gain .01 may already keep the gates unsaturated.
- If the probe shows no material difference in (a)–(c), the conditioning account is weakened
  before any fit; I would then run at most one scaled fit (772803) rather than three, to see
  whether the native outcome disagrees with the probe, and say so here before launching.

**Step 2, three fits:** the scaled construction on 772803, 772903, 773003, each paired with the
completed CF_E0005 fit of its block (`b03_e0005_*`), which differs in the scaling flag alone; the
flag-off path is bit-identical and B02 showed a rerun reproduces bit for bit across launch shas,
so references are not rerun. D1280 of the same blocks (`b01_s1_d1280_*`) is carried for
description. Three of the idea's six fits; the other three are not reserved for anything and
nothing is added after scores are seen.

**Predictions (sign and threshold; no invented probabilities).**
- Intermediate, in the fits: actor displacement after rollout 1 above the reference's on three of
  three blocks (reference .026–.029); at rollout 45 the network part of the displacement (the
  log-std part removed as sqrt(3)·|H/3 − 1.4189| / ‖θ0‖) at least twice the reference's. These
  are parameter distances and I hold them as weak evidence of function change; the probe's
  sensitivity measure, repeated on the trained policy at rollout 45, is the better read and is
  expected above its own initial value.
- Native: training return U over rollouts 35–45 above the reference on at least two of three
  blocks and above 25 in the mean; late-window J (panels 30–45) above the reference on at least
  two of three blocks; and J_late − J_init larger than the reference's on at least two of three,
  so that a better starting policy is not read as restored learning.
- D1280 relation: no prediction. Scaling could close much of the gap or little of it.

**Strongest simpler alternatives.** A higher J from a better initial function rather than from
learning (hence J_init); scaling acting as a learning-rate change on the first layer rather than
as restored sensitivity (the probe's sensitivities before/after speak to it); block noise (late
windows, three blocks, sign counts only).

**What I would do with it.** Intermediate and native both move: this becomes the flat
construction, the scale hazard is reported as a defect of the B01 comparator (B01's label stands
as read; its meaning is narrowed in RESEARCH), and the same scaling question is put to D's
coordinator, which reads the same raw state and does not learn. Intermediate moves, native does
not: conditioning was real but not binding; no second scaling variant; the comparator limitation
is recorded and the direction's k question is taken up inside the D family. Native moves without
the intermediate: keep the construction, revise the mechanism. Neither: the account is weakened
and I stop comparator repair here.

**Reading limits.** Exploration; three blocks; historical references; blocks already used for
every flat setting since B01, so no gap size and no competence claim; no MEI verdict.

**Engineering.** The scaling touches the shared learner (`hmasd/networks.py`
`SkillDiscoverer._apply_central_input`, one application point for acting, replay and
evaluation): Implementer from a scope note, independent Reviewer, DM acceptance, then launch.

## 2026-09-19 21:05 PDT — read: the temporary temporal-alignment design (independent collaborator); what it changes for FSD

The owner pointed me to `docs/research/designs/TEMPORAL_BEHAVIOR_STATE_ALIGNMENT_20260919.md` on
the published branch `codex/temporal-state-alignment` at
`646ab539d2a2ef689d0e4ee977f327f79cf2215b` (an owner-assigned bounded design and prototype, not a
direction; it had read this notebook up to the response entry at `1b1b91400`). Read in full. It
runs nothing on FSD, claims no FSD result and says so; I treat it as a simple-model bridge.

**What I take from it.**
- A sharper wording of the skill-channel explanation, now that "learning coordinator" is
  withdrawn. D's skill is a *persistent policy mode*: a label held k = 10 ticks that modulates
  the actor's features before the GRU while per-tick feedback and action sampling continue. A
  mode drawn without regard to state still makes behaviour temporally coherent: with a mode
  mean m_z held two ticks and independent residual e_t, Var(a0 + a1) = 4 Var(m_z) + 2 Var(e)
  against 2 Var(m_z) + 2 Var(e) when the mode is redrawn each tick, at equal per-tick variance.
  So D may explore (and cover the area) differently from CF, whose only randomness is an
  independent Gaussian per tick, without any learned skill selection. This is a bridge with its
  stated omissions (no boundaries, feedback, teammates, learning); it predicts neither J nor a
  D advantage.
- Two estimands that my notes have blurred: what persistence does for *training-time
  exploration* and what it is worth at *deployment*. In these runners training samples actions
  and evaluation is deterministic, so a D-over-CF difference in J45 can come from how the policy
  was explored into, from the mode mixture still present at evaluation, or both.
- The identification caution for any later exchange-style diagnostic: an online-minus-exchanged
  gap is Cov(p, A) and splits into a new-observation part and a retained-history part that can
  cancel; a zero gap does not show that state is unused, a positive one does not show that new
  information is used. For FSD the analogous exchange (joint skill-label sequences between
  worlds under a frozen checkpoint) would ask about state-aligned skill *identity*, not timing,
  since the clock is fixed; with skill choice near uniform I expect it to show little, and these
  runners save no checkpoint, so it is not free. Not scheduled.
- The likelihood warning: giving a flat learner temporally correlated action noise while keeping
  independent marginal Normal likelihoods credits parameters that cannot affect return (the
  document's exact two-step example gives a spurious gradient component of rho). Any
  "CF with coherent exploration" arm must carry the conditional density through PPO's ratio and
  the recurrent replay, or it confounds the learner with the mechanism.

**What it does not change.** B05 stands as written: it tests a confirmed construction hazard
that is present from the first update, and nothing in the design speaks to it. The design
itself says it neither diagnoses the CF input hazard nor replaces this repair.

**What it changes.** The branch of B05's "what I would do with it" where scaling is not enough.
The next explanation in line is then persistent-mode exploration, and the direction's own axis
gives the cleanest contrast for it without touching the flat learner or any likelihood: D with
its skill held k = 10 against D with the skill redrawn every tick (k = 1), same coordinator,
same low-level code, the coordinator being near-uniform in both. Intermediate prediction:
lower temporal autocorrelation of actions and less area covered per episode in training at
k = 1; native: lower training return and J at k = 1 if coherence is what D's low level gains
from. That would be evidence about fixed persistence, the first half of this direction's
question, obtained inside the D family; it would still say nothing about an *unfixed* k.
Recorded as the candidate that follows B05, not scheduled and not yet a prospective entry.

## 2026-09-19 21:35 PDT — flat input scale B05: code written, independently reviewed, accepted

Implementer (Opus) from my scope note; independent Reviewer (read-only); I read the diff, ran the
checks and applied the Reviewer's fixes myself.

**Shared learner** (`hmasd/networks.py`, `SkillDiscoverer`, +65 lines): optional config field
`central_snapshot_state_affine` = (offset, scale), validated, held as non-trainable
non-persistent buffers, applied to the leading `state_dim` entries of the central input inside
`_apply_central_input` only. Field absent: the executed line is the old concatenation.
Implementer's bit-identity check against `HEAD`'s module (flag off and on, no affine): RNG state
after construction, `state_dict`, parameter count, `forward`, `evaluate_sequence`, `get_value`
all identical; the update-phase reference tape rebuilt under both sources has the same digest.

**Thin entry** `scripts/run_fsd_flat_input_scale_b05.py` (`fit`, `probe`, `reduce`), object
`FSD_FLAT_INPUT_SCALE_B05`, arm `CF_S` run as the frozen `CF` arm. The affine is derived from the
actual environment instances (area 1,000; heights 50–150; 6 UAVs × (x, y, z), 50 users × (x, y),
clock) and refuses a layout that does not close at `state_dim` = 119. With no arm the config
equals the recorded `b03_e0005_772803_a01` `learner_config` (tested against the real file). The
affine is outside the frozen config dump, so a CF_S fit's recorded config equals CF_E0005's and
the declared difference is the summary's `central_snapshot_state_affine`, which `fit_endpoint`
recomputes from the recorded bounds.

**Reviewer: ACCEPT WITH FIXES**; no finding in the shared-learner change. Verified by the
Reviewer independently: the transform reaches acting, the replayed update and the separately
built evaluator; the PPO ratio before the first step is 1 everywhere except the episode's last
stored transition, where old and new log-probs differ by up to .005 — with and without the
affine alike (.0064 without), so it is a property of the CF recurrent replay already at `HEAD`,
one row in 500, not of this change; the probe's hooks leave the panel bit-identical to the frozen
evaluation; gate packing, masked hidden state and block ranges are right. Findings and what I
did: F1 (the probe reader accepted a probe of another panel size, construction or source, e.g.
the tiny test's, and `reduce` would have differenced it against full fits): fixed — the reader
now requires the frozen panel size, the block's evaluation seed, a recorded source equal to the
requested one and equal configs in both constructions, and `reduce` refuses a probe whose
configs, affine or source are not the fits'. F2 (the probe executes policy without admission):
accepted as designed and recorded in the prospective entry; `--launch-sha` is now mandatory and
must equal `HEAD`. F3 (block shares published without their definition): definition added — the
share is over the sum of the four per-block squared norms, bias and cross terms left out, not a
share of the actual pre-activation norm. Also added a guard that the log-std correction's three
action dimensions are the recorded ones. The Reviewer notes the correction is exact only for
equal per-dimension log-stds (otherwise a lower bound on the log-std part) and is at most .2 %
of the total on the three references, so my "network part" prediction is in effect about the raw
displacement.

**Checks (mine, after the fixes).** B05 + B04 + B03 tests 26 passed; CF pathway tests with the
new affine tests 69 passed. Pre-existing and unrelated (Reviewer confirmed): one `ha_ctse` stub
test, the stale cached update-phase tape under `temp/`, a basename clash when the whole FSD test
tree is collected at once.

**Deviation from the prospective entry.** The probe runs on `wsl_4070`, not locally: three UCOPE
fits of the Codex session are running on this machine's CPU and I will not add load to their
walls. It runs from the node checkout at the published sha, unadmitted as designed, zero
optimizer steps; outputs under `runs/flexible_skill_duration/b05_probe_<block>/`.

## 2026-09-19 21:40 PDT — B05 step 1 read (zero fits): unscaled, the CF actor's own observation does not reach its GRU; the three fits are launched

**Execution facts.** Three probes on `wsl_4070` from the node checkout at the published
`52400ff4d3ebe284cbc12dc8b8c510022b850d98` (recorded and requested sha equal), unadmitted as
designed, node otherwise idle, about 18 s per construction; status complete, optimizer steps 0 on
learner and evaluator, 2 × 32 evaluation episodes per block (192 in all, 96,000 team steps of
policy execution, no training), the recomputed baseline action reproduces the panel's action
exactly in all six. Collected by one rsync; the three `summary.json` sha256-identical to the node.
Outputs `runs/flexible_skill_duration/b05_probe_{772803,772903,773003}/`.

**Observations** (untrained policy, same seed for both constructions; ranges over three blocks).

| measure | unscaled (CF_E0005 as run so far) | scaled (CF_S) |
| --- | ---: | ---: |
| state block's share of the first layer's per-block pre-activation norm | 1.0000 | .73–.76 |
| own current observation's share | below 5e-6 (raw input share 4–5e-8) | .031–.035 |
| GRU update / reset gate units saturated | .976–.980 / .975–.981 | 0 / 0 |
| mean-action change, own observation × 1.05 | 3.9–4.4e-7 | 7.7e-6–1.0e-5 |
| mean-action change, ego one-hot moved | 8.8–9.6e-6 | 1.9–2.1e-4 |
| J_init (32 worlds) | .299, .271, .212 | .158, .262, .254 |

(The share's denominator is the sum of the four per-block terms; bias and cross terms are left
out. Absolute sensitivities are tiny in both because the action head starts at gain .01; the
ratio is the read.)

**Predictions, scored.** Unscaled state share above 90 %: held (1.0000). Unscaled sensitivities
small: held. Scaled state share below one half: failed (.73–.76; 118 coordinates of order .5
still outweigh a sparse 104-entry observation; the point of the prediction, that the other
blocks become visible, holds: own observation from under 5e-6 to .03). Scaled own-observation
sensitivity at least three times higher: held, 18 to 26 times; ego 21 to 23 times. Gate
saturation lower when scaled (loosely held, I doubted it): held decisively, 98 % to 0.

**A fact I did not predict.** The untrained unscaled policy scores J_init .299, .271, .212 on
the three blocks; the CF_E0005 fits' late-window J after 45 rollouts is .290, .214, .283. The
difference is −.009, −.057, +.071, mean +.002. The best flat learner so far ends where its
untrained policy starts. "Does not learn" is now measured against a level, not inferred from
displacement or a surrogate. (B04's arms end within about .07 of the same level on every block, some above and some below; B01's CF, with the entropy bonus, ends below it.)

**Interpretation.** Strengthened, strongly: with raw-metre coordinates the CF actor is, from
initialisation, a function of the held snapshot almost alone, fed through a GRU whose gates are
98 % saturated, so neither the agent's own current observation nor its identity measurably
changes its action; every flat fit since B01 trained that construction. This is a defect of the
comparator's construction, present in B01's frozen CF as carded and implemented (my
implementation note of 2026-09-18 called the snapshot "normalized"; it never was, because the
running normalisers are off in these configs). Untouched: whether repairing it makes the flat
learner learn (that is step 2), how much of the D1280–CF gap it explains, and anything about k.
Contrary evidence kept: the scaled policy's J_init is not higher (.158/.262/.254 against
.299/.271/.212), so conditioning by itself buys no better starting policy.

**Decision, as written beforehand.** The probe shows a material difference in (a)–(c), so the
three fits run. Launched through `flat_input_scale_b05/launch_fit.sh` and the admission kernel
at launch sha `52400ff4d3ebe284cbc12dc8b8c510022b850d98` (the probes' source), node idle
beforehand, all admitted at the first request, alive with empty `stderr.log`.

| tag | arm | block | operation ref (under `/home/wu/projects/HMASD/.git/hmasd-admission/`) |
| --- | --- | --- | --- |
| `b05_s_772803_a01` | CF_S | 772803 | `4001f96dd3bc79448ec5b910edbbaad3899ae01ae85783d762ddd18fda99d8e9.json` |
| `b05_s_772903_a01` | CF_S | 772903 | `c5f8f6079c786b3fdb8bfa7fdc83e0e8a0cbe372852013fb674754525f3c027a.json` |
| `b05_s_773003_a01` | CF_S | 773003 | `881b27d0df8a9364dffa8f306eb512e7bdec28f61d4c5de9b5d9f347d05fd85a.json` |

No B05 fit score or diagnostic is read before all three are terminal.

## 2026-09-19 22:55 PDT — flat input scale B05 read: with the coordinates scaled the flat actor trains; it rises from its starting level on three of three blocks and stays below D1280

Reads against the prospective entry of 20:40 PDT and the step-1 entry of 21:40 PDT. Nothing was
added after seeing scores. Exploration, targeted single change: no MEI verdict, no gap size.

**Execution facts.** Three of three planned fits admitted at the first request on `wsl_4070`,
launch sha `52400ff4d3ebe284cbc12dc8b8c510022b850d98` (the probes' source), all exit 0 with 45
rows, status complete, empty `stderr.log`; one rsync, 27 files, the three `summary.json`
sha256-identical to the node. `reduce` complete with the three probes, no invalid fit, reference
or probe: every new fit's recorded configuration equals its CF_E0005 reference's, the recorded
affine is the one its recorded bounds imply, and each probe's configurations, affine and source
are its fit's. `runs/flexible_skill_duration/b05_reduce/summary.json`, sha256
`f57b3e281a221d1c9e60790ba177e24feda7d6755df2143172029a5d2dcc4f8d`. Wall about 4,200 s per fit at
three concurrent, peak RSS 1.3 GiB. Fits used: 3 of the idea's 6; the batch is closed.

**Observations.**

| block | J_init unscaled | CF_E0005 late | rise | J_init scaled | CF_S late | rise | D1280 late | D1280 − CF_S late |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 772803 | .299 | .290 | −.010 | .158 | .244 | +.086 | .432 | +.189 |
| 772903 | .271 | .214 | −.057 | .262 | .364 | +.102 | .395 | +.031 |
| 773003 | .212 | .283 | +.071 | .254 | .355 | +.101 | .452 | +.097 |
| mean | .261 | .262 | +.002 | .225 | .321 | +.096 | .426 | +.105 |

CF_S minus CF_E0005: late window −.046, +.150, +.072 (mean +.059); J45 −.130, +.050, +.091
(mean +.004). On 772803 CF_S is at .30 by panel 5 and drifts down to .198 at panel 45 (early
window .300, late .244); on the other two it holds or rises.

Diagnostics, mean of three blocks (CF_E0005 / CF_S / D1280): actor displacement after rollout 1
.027 / .091 / .153; at rollout 45 .071 / .531 / 1.156 (log-std part under 1 % in the flat arms);
mean policy loss −.0005 / −.016 / −.026; action entropy at rollout 45 3.96 / 3.84 / 7.46;
training return U over rollouts 35–45 23.3 / 25.9 / 29.2 (per block CF_S 23.3, 27.5, 26.8 against
23.7, 21.2, 25.1).

**Predictions, scored.**
- Intermediate, displacement after rollout 1 above the reference on three of three: held
  (.089, .091, .094 against .026, .029, .027).
- Intermediate, network displacement at rollout 45 at least twice the reference's: held, 7.5
  times. Both are parameter distances; the better read I asked for, the sensitivity measure
  repeated on the trained policy, was not taken: these runners save no checkpoint, which I should
  have seen when writing the entry. Unmeasured, not failed.
- Native, U over rollouts 35–45 above the reference on at least two of three and above 25 in the
  mean: held (two of three; 25.9), narrowly.
- Native, late-window J above the reference on at least two of three: held (two of three).
- Native, J_late − J_init larger than the reference's on at least two of three: held, three of
  three, and the rise is the same size on every block (+.086, +.102, +.101) while the reference's
  is −.010, −.057, +.071.

**Interpretation.**
- Strengthened: the comparator's failure to train was, in large part, its input construction. One
  information-preserving change to the actor's appended block, nothing else, turns an actor that
  moved .07 in 45 rollouts into one that moves .53, makes the surrogate improve, and gives a
  consistent rise of about .10 J from the untrained level where the unscaled learner had none.
  Pro's diagnosis is borne out on the intermediate and, more modestly, on the native side.
- Weakened: that the scale hazard is the whole D1280–flat difference. CF_S is below D1280 on
  three of three in the late window (+.19, +.03, +.10), its training return is 3 below D's, its
  actor moves half as far, and on one block it peaks early and declines. With three blocks every
  interval here contains zero; signs and the per-block pattern are what I read.
- Untouched: persistent-mode exploration, critic quality, discriminator residuals; and the
  question of k. Also untouched and now plainly relevant: CF_S runs at a learning-rate multiplier
  (.5) and an entropy coefficient that were selected for the blind construction, so it is an
  untuned learner; I am not going to tune it on these blocks.
- Contrary evidence kept: the scaled policy starts lower on 772803 (.158) and part of "rise" on
  that block is recovery to the level the unscaled policy starts at; the rise criterion alone
  would flatter CF_S there. Late-window level against CF_E0005 on that block is negative.

**Standing.** CF_S replaces CF_E0005 as the flat construction for anything that follows. The
frozen B01 object and its label `D_REFERENCE_ABOVE` stand as read under its card; what the label
means is narrowed: B01's CF actor was, by construction, nearly blind to its own observation and
identity (step-1 probe), so B01 compared D1280 with a defective comparator, and +.29 J is not an
estimate of a matched-information gap. The defect was mine (2026-09-18 implementation note
called the snapshot normalised; the normalisers are off in these configs). The present
description: on three blocks already used for selection, D1280 is above the repaired, untuned
flat learner by about .1 J in the late window, three of three; no size claim.

**Next.** As written beforehand: put the same question to D's coordinator, at zero fits first.
It embeds the same raw-metre state through one linear layer, its skill choice stays near uniform
and it barely moves; both low-level critics read the raw state too. A forward probe of the
untrained and (since no checkpoint exists) only the untrained coordinator can say whether its
logits are insensitive to the state or saturated from initialisation. If they are, the
direction's own question has been asked so far of a coordinator that cannot see, and the next
prospective entry is a scaled-state D, which is also the prerequisite for any k contrast,
including the k = 10 against k = 1 persistence contrast recorded at 21:05.

## 2026-09-19 23:20 PDT — zero-fit inspection planned: does D's coordinator see the state? (forward probe of the untrained D1280, no learner change)

Follows the "Next" of the B05 reading. No fit, no learner change: the probe feeds the untrained
coordinator the state as it is (raw metres) and, separately, the same state pre-transformed by
B05's affine, which at initialisation is exactly what a scaled-state D would compute.

**Source facts (read now).** `SkillCoordinator` embeds the 119-entry raw state with one
`nn.Linear` (gain 1) into one token and each agent's scaled observation into another; the seven
tokens go through a default (post-norm) `nn.TransformerEncoder`, so attention queries and keys
are formed from the un-normalised token embeddings; team and agent skill logits come from a
decoder on top. The low-level critic (`R_Critic`) takes the central observation through the same
`MLPBase` → FiLM → GRU path as the actor, with no input normalisation.

**What is measured**, per block (772803, 772903, 773003), D1280 construction, untrained, on the
inputs of one frozen evaluation panel (32 worlds), zero optimizer steps, for the raw and the
pre-scaled state: (a) the norm of the state token's embedding against the observation tokens';
(b) first encoder layer attention: mean maximum attention weight per query and mean attention
entropy (recomputed from the layer's own projection weights); (c) sensitivity of the team-skill
and agent-skill probabilities (total-variation change) to an agent's own observation × 1.05, to
moving one UAV by 50 m in the state, and to swapping two agents' observations; (d) the skill
distributions' entropy at initialisation; (e) for the low-level critic: GRU gate saturation and
the change in value when one UAV is moved 50 m. J_init of the untrained D1280 is recorded too
(raw state only; the pre-scaled state is a forward calculation, not a policy that is executed).

**Expected (sign; held loosely where said).** Raw: the state token's norm is more than 100 times
an observation token's; first-layer attention is near one-hot (mean maximum weight above .9);
skill probabilities move less under an own-observation perturbation than they do with the
pre-scaled state, by at least a factor of three. Loosely held: post-norm layers may rescue much
of this, and the decoder may start so close to uniform that every sensitivity is tiny in both.
Critic: gates mostly saturated with raw state, as in the CF actor; yet D's critic does fit, so I
expect its saturation to be lower than the actor's 98 % or harmless for a value function of the
state. If raw and pre-scaled differ little on (b) and (c), the coordinator's standing still has
another cause (its reward, its batch, its learning rate) and a scaled-state D is not the next
entry.

**What I would do with it.** Material difference: prospective entry for a scaled-state D
(coordinator and both critics read the state through the same affine, flag-gated, reviewed), read
first on whether the coordinator moves and its skill choice leaves uniform, then on J. No
material difference: go to the persistence contrast (k = 10 against k = 1) with D as it is.

## 2026-09-19 23:50 PDT — D state probe B06 read (zero fits): the untrained coordinator sees its observations and the state as it is; the blindness conjecture is weakened

**Execution facts.** `scripts/probe_fsd_d_state_scale_b06.py` (Implementer from my scope note;
I read the script, ran its checks — 24 passed with B05's — and accepted it myself: no shared
learner, runner, environment or evaluator is touched, so no independent Reviewer). Commit
`bc244d1f5`, run locally (load average below 1; the node was not needed), three blocks in
parallel, 61–62 s each, `status: complete`, `optimizer_steps: 0`, learner and evaluation config
differences from the recorded `b01_s1_d1280_<block>_a01` fits `{}` on all three. Capture per
block: 25 of 50 decision calls (800 rows) for the coordinator, 25 of 500 critic calls (4,800
rows); `assign_and_value_batch` is never called on the D route; the held replay reproduces the
deterministic chain exactly. Outputs `runs/flexible_skill_duration/b06_probe_{772803,772903,
773003}/summary.json` (sha256 `8f196920…`, `494c376e…`, `e308bda8…`). Exposure, not fits: three
untrained 32-world panels.

**Observations** (772803 / 772903 / 773003; raw → pre-scaled).

| measure | raw | pre-scaled |
| --- | --- | --- |
| state token norm ÷ observation token norm | 5,110 / 4,170 / 4,260 | 5.2 / 4.5 / 4.5 |
| first-layer attention, mean max weight (uniform 1/7 = .143) | .67 / .62 / .57 | .16 / .16 / .16 |
| first-layer attention entropy (ln 7 = 1.946) | .73 / .84 / .95 | 1.94 / 1.94 / 1.94 |
| attention mass on the state token | .54 / .48 / .39 | .14 / .14 / .14 |
| team-skill entropy (ln 6 = 1.792) | 1.72 / 1.68 / 1.60 | 1.67 / 1.60 / 1.54 |
| agent-skill entropy, mean | 1.73 / 1.65 / 1.63 | 1.70 / 1.59 / 1.63 |
| agent 0's skill TV, own observation × 1.05 | 4.2e-4 / 1.3e-3 / 2.2e-3 | 9.3e-4 / 1.1e-3 / 7.9e-4 |
| agents 0, 1 skill TV, observations swapped | .008 / .020 / .016 | .011 / .011 / .011 |
| team-skill TV, observations swapped | .0018 / .0040 / .0041 | .0004 / .0003 / .0003 |
| agent-skill TV, UAV 0 moved +50 m | .0028 / .0028 / .0036 | 1.0e-4 / 1.0e-4 / 1.0e-4 |
| low-level critic GRU gates saturated (update) | .969 / .972 / .968 | 0 / 0 / 0 |
| critic \|Δv\| for the +50 m move (mean \|v\| .5–1.1) | .043 / .029 / .035 | 4e-4 / 6e-4 / 1e-3 |

Raw per-head attention is uneven: some heads at a max weight of 1.0, others at .3. `J_init` of
the untrained D1280: .327 / .132 / .141 (mean .200).

**Against what I wrote at 23:20.** State token more than 100 times an observation token: held
(about 4,000–5,000 times). First-layer attention near one-hot, mean max above .9: **failed**
(.57–.67; partly saturated, not one-hot). Own-observation sensitivity at least three times
higher pre-scaled: **failed** — the ratio pre-scaled/raw is 2.2, .85 and .36 on the three
blocks, no consistent sign; the swap contrast agrees (.011 against .008–.020). Critic gates
mostly saturated raw: held, and as expected it does not make the critic blind — its value
moves *more* under the physical move on the raw state than on the pre-scaled one, because the
critic reads nothing but the state, so there is nothing for the state to swamp.

**Interpretation.** The CF actor's defect was one block of an additive first layer drowning the
others ahead of a GRU. The coordinator does not have it: each token is embedded separately and
the post-norm LayerNorm after the first layer renormalises every token, so the observation
tokens keep a path to the logits of about the same strength in both versions, and the state
reaches the logits more strongly raw than pre-scaled. In both versions all sensitivities are
small in absolute terms (TV of 1e-3 to 2e-2) because the decoder starts near uniform. So:
"D's coordinator barely learns because it cannot see its input" is **weakened** — at
initialisation it sees both. **Untouched:** whether partly saturated first-layer heads and a
saturated critic GRU slow *learning* (gradient through a saturated softmax or gate is small;
a forward probe cannot say) — but D's critic fits its target and D's J rises, so I do not
pursue it now. **Strengthened, mildly:** the reading of D1280 as a near-uniform skill
assigner whose gains come from the low level.

Two side observations, recorded without a conclusion. (1) The untrained coordinator's skill
entropy is 1.60–1.73; the trained D1280's logged entropy is 1.74–1.78 — training moves the
coordinator *toward* uniform, not away (different sampling: evaluation-panel decision states,
deterministic chain, here; training rollouts there). (2) D1280's rise from its untrained level
is +.105 / +.263 / +.311 (mean +.23, late window .432 / .395 / .452) against the repaired flat
CF_S's +.086 / +.102 / +.101 (mean +.10); one untrained panel per block and different
initialisations, so a level comparison only, but it says D's advantage over CF_S is made
during training rather than inherited from its starting point (D starts *lower* on two of
three blocks).

**What follows, as written at 23:20.** No material difference on the measure that matters, so
no scaled-state D. Next is the persistence contrast inside the D family — k = 10 against
k = 1 with D as it is — as one prospective entry, after I have read how k enters the D route's
high-level reward, discount and coordinator batch, since those change with k and have to be
named as package differences before the fits, not after.

## 2026-09-19 23:58 PDT — prospective: persistence contrast inside the D family, skill held 10 steps against redrawn every step (explore, six fits)

**Idea.** D1280's coordinator is a near-uniform assigner (entropy 1.74–1.78 of 1.79), its
discriminator reward a near-constant offset, and yet D1280 rises +.23 J from its untrained
level where the repaired flat CF_S rises +.10. The explanation in line (21:05 entry, from the
temporal-alignment design): a skill held for 10 steps is a *persistent policy mode*, so D's
training-time exploration is temporally coherent — Var(a0 + a1) = 4Var(m) + 2Var(e) with the
mode held, 2Var(m) + 2Var(e) with it redrawn — and the low level gains from that. The
direction's own axis tests it without touching the flat learner: the same D with the skill
redrawn every step.

**How k enters the D route** (Scout map, static, read before this entry). Decision cadence on
the d2 route is governed by `skill_cap_k_max` and `team_cap_k_Z` (`hmasd/agent.py:482-483,
2596, 2613`), *not* by `config.k`; with c = c_Z = inf decisions fire only at resets and caps.
`config.k` on this route only sets the low-level update's BPTT chunk length
(`agent.py:6306-6309`; the sampler carries skills per step, `hmasd/utils.py:1281-1282`) and
two unconsumed buffer fields. The team and individual discriminators have no k dependence.
The high-level return is a discounted within-segment sum with `gamma ** elapsed` per hop
(`agent.py:2353-2355`, `utils.py:1018+`). No validation refuses caps of 1
(`configs/config_1.py:803-812`); the frozen runner's `arm_panels` does hard-code 10/10/10, so
this object reduces with its own reader, as B05 did.

**Arms** (thin entry over the frozen B01 runner, blocks 772803 / 772903 / 773003, 45 rollouts,
panels as B01 stage 1, no shared-learner change):

- `D_K10` — D1280 exactly as recorded, rerun with a read-only behaviour capture. B02 showed a
  D1280 rerun is bit-exact on the node; here bit-identical panel scores against
  `b01_s1_d1280_<block>_a01` are the runtime proof that the capture changes nothing. If a block
  is not bit-identical, the capture is suspect and that block's behaviour measures are not read.
- `D_K1` — the same with `skill_cap_k_max = team_cap_k_Z = 1`. `config.k` stays 10, so the
  low-level update (chunk length, minibatches, epochs) is the same law in both arms.

**Package differences other than persistence, named now.** (1) The coordinator's sample pool is
about 8,000 rows per rollout instead of 800. I set `coordinator_batch_size = 12800` on `D_K1`,
so both arms take one full-pool minibatch per epoch, 15 coordinator optimizer steps per
rollout; B02 found no detectable difference between 15 and 105 steps at k = 10. The pool size
itself cannot be matched. (2) The coordinator's per-hop discount and segment return are over 1
step instead of 10: intrinsic to persistence, not separable. (3) Evaluation is deterministic
(argmax skill) in both arms; at caps of 1 the evaluator re-chooses the argmax every step, which
on a slowly changing state is *not* a random redraw. So J compares deployed policies, and the
exploration claim is read on training-time measures first.

**Behaviour capture** (training collection, per rollout, both arms): autocorrelation of the
executed actions at lags 1, 2, 5, 9, 10, 20 (per lane × agent × action dimension series,
mean-removed, averaged); per-UAV distinct 50 m cells visited per episode and path length over
net displacement; fraction of steps on which an agent's skill changes (expected about .083 at
10, .83 at 1 for a uniform assigner).

**Expected, if persistence is what D's low level gains from.** Intermediate, rollouts 35–45:
action autocorrelation at lag 5 higher in `D_K10` than in `D_K1` by at least .05 on three of
three blocks, and more cells visited in `D_K10`. Native: late-window J of `D_K1` below
`D_K10` by at least .05 in the mean and on at least two of three blocks (half of the
D1280 − CF_S gap of .105), training return U lower as well. I hold this loosely: at
initialisation the FiLM modulation by the skill may move the mean action very little against
unit action noise, in which case the first intermediate prediction fails outright.

**What each outcome would do.** Both hold: the persistent-mode explanation is strengthened, and
the direction's first half — does a *fixed* persistence matter — has its first evidence inside
the D family; an unfixed k is still untouched. Autocorrelation differs but J does not: mode
persistence exists but is not what makes D better; weakened. Autocorrelation does not differ:
the skills are behaviourally inert at this training length, the hierarchy's advantage is
unrelated to skills, and the live difference between D and CF_S becomes the actor's input (104
entries of own observation against 853) and the state-only critic — that would be the next
entry. `D_K1` *above* `D_K10`: contrary to the explanation; recorded as such.

**Cost.** Six fits (the idea's allowance; `D_K10` reruns are started training attempts and
count). `D_K1` costs more per rollout: a decision pass every step and ten times the coordinator
update rows. Node `wsl_4070`, at most four concurrent. Nothing is added after scores are seen.

## 2026-09-20 00:25 PDT — read: owner-supplied cross-interpretation (FSD × UCOPE × temporal alignment); what I adopt for FSD

**Source.** A package the owner handed me (`research_cross_interpretation_20260919.zip`, sha256
`dbbd19e2c1a7425d…`, local, not in the repository): a main report, three proposed notebook
fragments and an exact-arithmetic check of its finite models. It is advisory, pinned to this
notebook at `33dbff37e` — so it predates the B06 reading (23:50) and the persistence entry
(23:58). I record my response here in my own words rather than pasting its FSD fragment; the
UCOPE and temporal-design fragments belong to their own lead and I do not touch those files.
No fit, no code, no run follows from this entry.

**Checked before adopting.** Its B05 numbers against the run files: CF_S minus CF_E0005 at the
last panel (rollout 45) is −.130 / +.050 / +.091, mean +.004 — correct
(`b05_s_*` against `b03_e0005_*`); in the late window it is −.046 / +.150 / +.072, mean +.059,
one block adverse.

**Adopted, and it sharpens my 22:55 reading.**
1. *Four different judgments*: the input contains the information; the module responds to it;
   the learner progresses from its own initialisation; the attained native level is higher.
   B05 established the second at initialisation and the third (+.086 / +.102 / +.101 from its
   own J_init on three of three blocks). It did **not** establish the fourth: scaled against
   unscaled the endpoint difference is about zero at rollout 45 and mixed in the late window,
   and the block where CF_S starts lowest (.158) admits the reading "recovered to the level the
   unscaled construction started at". My 22:55 entry says "the flat actor trains"; that stands.
   Anything that reads as "the repaired flat is better at the end" does not, and I did not
   measure the trained policy's sensitivity (no checkpoints). CF_S remains the flat
   construction because the unscaled one is blind to its own observation, not because it
   scores higher. B01's frozen label and the narrowing of its meaning stand as written.
2. *UCOPE is a contrary constraint, not support.* UCOPE's B04 found no established advantage of
   short command persistence over ordinary feedback (B − G: −.030 / +.008 / +.007). It neither
   supports nor refutes persistent skill-mode value here: D holds a *label* while the low level
   keeps sampling feedback-dependent actions every tick; UCOPE's KEEP copies the *command*.
   Different interventions; their scores are not pooled and I will not cite either for the
   other.
3. *Retraining and a fixed-weight intervention answer different questions.* B07 is a
   retraining contrast (Δ_train in the report's terms): it can say whether training with caps
   of 1 ends somewhere else, not whether the trained D1280 *needs* its held label at
   deployment. The second would take a checkpoint these runners do not save; not planned.
4. *Exchange / projection / best restricted gate are three quantities.* For a binary END/KEEP
   choice with advantage A and retained information C, the value of new information to the
   best gate is (E|A| − E|E[A|C]|)/2: it needs A to change *sign* within some C, not merely to
   vary. This is the right yardstick for the direction's second half (an unfixed k, i.e. an
   interruption gate) when it comes back; nothing in FSD estimates it today, and it is a local
   ideal-gate identity, not a native estimate.

**One place I go further than the report.** It cautions that a high skill entropy is not
per-state independence, marginal and conditional entropy being different statistics. Correct
in general; here the logged number is the conditional one — `update_coordinator_d2` averages
the per-sample entropy of the coordinator's own distribution (`hmasd/agent.py`, the
`team_entropy`/`agent_entropies` terms of the PPO loss). So 1.74–1.78 against ln 6 = 1.79 means
a mean KL from uniform of .01–.05 nats *per state*: near-uniform at almost every visited
state. That supports "near-uniform assigner" as a description of the sampling distribution in
training. It still does not license "random skills beat flat" as a mechanism — the argmax
used at evaluation can be strongly state-dependent under a near-uniform distribution — and
B07's capture will log the skill-change rate in training for exactly that reason.

**Against the B07 entry (23:58).** The report asks that a k comparison name its coupled
changes in update frequency, return boundaries and exposure. The entry names the coordinator's
sample pool (×10), the update steps (matched by batch size), the per-hop discount and segment
return (intrinsic), and the deterministic evaluation. One addition, recorded now before any
score exists: the *low level's* exposure is identical in both arms (same steps, same update
law, `config.k` held), but its conditioning input changes about ten times as often, so its GRU
sees a faster-switching label — a consequence of the intervention itself, not separable, and a
reason a lower J at caps of 1 would show that *this* low level gains from a held label, not
that temporal coherence of exploration is the channel. The action-autocorrelation and coverage
measures are what speak to the channel. B07's design is otherwise unchanged.

## 2026-09-20 00:50 PDT — persistence B07: entry code written and accepted

Implementer (Opus) from my scope note; I read the construction, the capture and the fit wiring,
ran the checks (52 passed with B05 and B06; the Implementer's cross-object run of 133 passed in
both orders) and accepted it myself: no shared learner, runner, environment or evaluator is
edited. `scripts/run_fsd_persistence_b07.py`, its launch script and tests.

What the code fixes beyond the 23:58 entry, recorded before any score exists.
- Both arms are built as the recorded D1280 construction, then the arm's overrides; the fit
  refuses unless the changed config fields are *exactly* the declared ones (`D_K10`: none;
  `D_K1`: `skill_cap_k_max`, `team_cap_k_Z`, `coordinator_batch_size`), on learner and
  evaluation config. `config.k` is 10 in both arms.
- At caps of 1 the team decision fires every step and forces every agent to be redrawn (the
  team cap is tested first, `hmasd/agent.py:2596`), so `D_K1` is "every skill redrawn every
  step" (tiny run: all segments of length 1), and both arms take 15 coordinator optimizer steps
  per rollout (asserted at read time).
- The capture wraps the learner agent instance's `step` (call first, copy after; the evaluator
  is another instance). A real tiny fit with and without it is bit-identical in panels and
  training rows; on the real host the proof is `D_K10` against the recorded D1280 panels.
- The wall plan is recorded, never a deadline. Tiny-host cost ratio of a `D_K1` rollout to a
  `D_K10` one: 1.74, a floor (the gap pass plus a decision pass every step).
- **Late window.** The reduce reports two: B05's definition (the last four panels, 30–45) and
  panels 35–45. My earlier late-window numbers (D1280 .426, CF_S .321) are B05's definition, so
  that is the one I read for the declared J prediction; the other is reported beside it.
  Behaviour measures are read over rollouts 35–45 as declared.
- Path length is three-dimensional, cells are the 50 m x, y grid.

## 2026-09-20 00:55 PDT — persistence B07: first wave admitted on `wsl_4070`

Node checkout fast-forwarded to the published `4a654ca0e4868a28df3d487e5d83ddc6049fe1db`
(the node reaches GitHub only from its login shell; a plain-shell fetch hung and was stopped,
nothing else affected), node idle beforehand. Four fits launched through
`persistence_b07/launch_fit.sh` and the admission kernel, all accepted at the first request,
alive with empty `stderr.log`. The three `D_K1` fits go first because they are the slower arm;
the other two `D_K10` fits follow as slots free (at most four concurrent).

| tag | arm | block | operation ref (under `/home/wu/projects/HMASD/.git/hmasd-admission/`) |
| --- | --- | --- | --- |
| `b07_k1_772803_a01` | D_K1 | 772803 | `a5ae3d1a0d36d7c6ba8ddaed2bffd427d8e8a941463fa423875d590dd7e322c6.json` |
| `b07_k1_772903_a01` | D_K1 | 772903 | `afad43bb886e0866844c2c95af9cf32a3805e0495d72cdd437f81e079f051beb.json` |
| `b07_k1_773003_a01` | D_K1 | 773003 | `d58454c1d727566e88bc8dd3c71d03c58b0c049b8c2e15d593045c6dbb3c6a4b.json` |
| `b07_k10_772803_a01` | D_K10 | 772803 | `cd23a74bcbb2974c3ba7a48652971a6e87d7668fdacce02109d4ca27c7fc1681.json` |

## 2026-09-20 01:10 PDT — persistence B07: two `D_K1` fits killed by the node's out-of-memory killer at their first coordinator update; plan for the remaining two fits (no score seen)

**Execution facts.** About one minute after admission, `b07_k1_772803_a01` and then
`b07_k1_772903_a01` exited with code −9 at boundary "rollout 0 collected"; the node's kernel
log names the out-of-memory killer (killed python at 8.3 GB anonymous RSS while still
growing; the node has 15.8 GB). Cause, measured on the survivor: a `D_K1` coordinator update
takes the whole 8,000-row pool in one minibatch (`coordinator_batch_size = 12800`, my design
choice at 23:58) and its resident memory swings between about 6 and 12 GB on the CPU within
every update. Three at once cannot fit. Neither killed fit completed an update or a panel, so
no score exists from them; their partial roots stay on the node as they are and will be
collected with the batch. They are started training attempts: **two of the six fits are
consumed**. My error: I sized the wall for `D_K1` and did not size its memory; the tiny-host
test has a 40-row pool and could not show it.

`b07_k1_773003_a01` survived (it started its update after the other two were gone) and
`b07_k10_772803_a01` runs beside it: about 5 min per rollout for `D_K1` (collection plus
update, some of it under memory pressure), about 150 s for `D_K10`; free memory about 1.2 GB
at the `D_K1` peaks. Nothing else is launched while they run together.

**Plan for the remaining two fits, fixed now.** Both go to `D_K1` on the two blocks that lost
theirs — `b07_k1_772803_a02` and `b07_k1_772903_a02`, new roots, same launch sha, same
construction, run **one at a time** with nothing else heavy on the node. I do not change
`coordinator_batch_size` to make them fit: the surviving block already runs the declared
construction, and mixing constructions across blocks would cost more than the hours.
Consequence: `D_K10` with the behaviour capture exists on block 772803 only. For the J
contrast the `D_K10` side on 772903 and 773003 is the recorded D1280 fit of the same
construction (B02 showed the rerun bit-exact on this node, and 772803 checks it again here);
the behaviour contrast (autocorrelation, cells, skill change) is three `D_K1` blocks against
one `D_K10` block, and the declared "three of three blocks" reading of the lag-5 difference
becomes one paired block plus two unpaired ones. That is a weaker intermediate reading than
the entry promised, recorded here before any score.

## 2026-09-20 05:30 PDT — persistence B07 read: redrawing every skill every step changed neither behaviour nor attained J on the one block that has it; the batch is closed with two cells missing

**Execution facts, by kind.**
- *New training results (two fits, both exit 0, launch sha `4a654ca0e`).*
  `b07_k10_772803_a01` (`D_K10`, 6,814 s, peak RSS 2.4 GB) and `b07_k1_773003_a01` (`D_K1`,
  15,465 s, peak RSS 14.1 GB). Both took 675 coordinator and 101,250 low-level optimizer
  steps. Collected by rsync, `summary.json` sha256 equal to the node's.
- *Technical failures (two fits consumed, no score).* `b07_k1_772803_a01`, `b07_k1_772903_a01`:
  killed by the node's out-of-memory killer at their first coordinator update (01:10 entry).
  Partial roots collected and kept.
- *Missing cells.* `D_K1` on 772803 and 772903; `D_K10` with capture on 772903 and 773003. At
  01:10 I planned two `_a02` retries. The admission kernel resolves that request to the
  existing terminal operation (`request_resolution: existing_operation`,
  `explicit_retry_available: false`): operation identity is direction, sha and runner arguments,
  not the output tag, by design ("cannot turn into an … output-renamed retry"). I did not work
  around it, and the owner's instruction of this morning is not to add experiments to
  complete an original plan. **The retries are withdrawn; the two unused fits stay unused; the
  batch is closed at four started fits.**
- *Historical references.* The recorded D1280 stage-1 fits (B01) and, as context, CF_S (B05).
  `D_K10` reproduces the recorded D1280 of 772803 bit for bit on all nine panels, so the
  capture is read-only on the real host and the recorded D1280 of 773003 is the same
  construction as `D_K10` would have been there (not rerun; no behaviour capture for it).
- Reduce: `runs/flexible_skill_duration/b07_reduce/summary.json` (sha256 `3945044e…`), status
  `incomplete` as it must be; no block has both new arms.

**Observations.** The only J contrast is block 773003, `D_K1` (new) against the recorded D1280.

| 773003 | D1280 (recorded, caps 10) | `D_K1` (caps 1) |
| --- | ---: | ---: |
| J late window (panels 30–45, the declared one) | .4517 | .4565 |
| J panels 35–45 / J45 | .462 / .499 | .466 / .464 |
| training return U, rollouts 35–45 | 29.7 | 33.3 |
| low-level policy loss / actor displacement at 45 | −.053 / 1.15 | −.067 / 1.22 |
| coordinator displacement at 45 | .047 | .040 |
| team / agent skill entropy at 45 (ln 6 = 1.792) | 1.66 / 1.78 | 1.77 / 1.79 |
| discriminator accuracy, team / individual, rollouts 35–45 (chance .167) | .30 / .25 | .20 / .21 |
| deployed (argmax) label changes per agent-step, last panel | .015 | .028 |

Behaviour in training, rollouts 35–45 — **different blocks**, `D_K10` on 772803 and `D_K1` on
773003, so descriptive only: agent skill change per step .082 against .833 (the intervention
took: a uniform assigner would give .083 and .833); executed-action autocorrelation at lags
1 / 5 / 10 of +.055 / +.016 / +.012 against +.069 / −.013 / +.008; cells visited per UAV per
episode 223 against 221; path length 55.1 km against 53.6 km; net displacement 574 m against
581 m. In rollouts 1–5 the two are equally indistinguishable (cells 115 / 117, all
autocorrelations below .003 in size).

**Against the 23:58 entry.** Lag-5 autocorrelation higher with the skill held, by at least
.05: **failed** — it is about +.02 with the skill held and the unpaired difference is +.03;
executed actions are close to white in both arms. More cells visited with the skill held:
**failed** (223 against 221, unpaired). `D_K1` below `D_K10` by at least .05 J: **failed** on
the one block that can speak (−.005 in the declared window; J45 alone is +.035 the other way
round; one block, conditional evaluation noise of a panel about .03). Training return lower at
caps of 1: **failed**, it is higher (33.3 against 29.7). The outcome I wrote as "`D_K1` not
below `D_K10`, autocorrelation does not differ" is the one observed, at one block.

**Interpretation.**
- *Did holding the skill change actual behaviour?* Not detectably, in any measure I captured,
  although the label itself changed ten times as often. I do not read the absent
  autocorrelation difference as "skills are useless": with unit action noise the series is
  dominated by noise, and a label could still shift the mean action by an amount these
  statistics cannot see. What carries weight is the conjunction: label cadence ×10, and the
  paths, coverage, training return, low-level learning curve and attained J all stay put.
- *Did it improve finite-training performance?* No evidence that it did; on one block the
  retrained caps-1 learner attains the same J and a higher training return. One block cannot
  show equivalence, and B01's block-to-block SD of a fit is about .08.
- *Persistent-mode explanation of D's rise* (21:05): **weakened**. Its premise — a held label is
  a behavioural mode whose persistence makes exploration coherent — finds no support: no
  behavioural signature of holding, and no loss from not holding.
- *Low-level conditioning* (the coupling I added at 00:25: the low level's label input switches
  ten times as often): the low level learned as fast or faster under it, so either it is
  robust to label switching or, more simply, **it makes little use of the label**. The
  discriminators agree in direction: they recover the label from the next state or observation
  at .25–.30 with the label held and .20–.21 without, against a chance of .167 — and even the
  held-label figure can come from the coordinator's state-dependent *choice* rather than from
  the label shaping behaviour. **Not measured:** the label's effect on the action mean at
  fixed input. That is the missing measurement, and it needs a checkpoint.
- *Strengthened:* D1280's advantage over the repaired flat CF_S (about .10, late window, three
  blocks, untuned flat, no size claim) is made by something other than skill persistence. What
  still differs between the two: the actor's input (104 own-observation entries against 853),
  the critic (state only, conditioned on the team label), the intrinsic term (near-constant),
  and the label as a possibly near-inert FiLM input. *Untouched:* everything about an unfixed
  k; and B05's standing.
- *Retraining against a fixed-weight rule change.* B07 is retraining: it says where training
  with caps of 1 ends up. It does not say what the trained D1280 would do if its labels were
  redrawn, frozen or randomised at deployment; no checkpoint exists to ask. Deployment differs
  from training in both arms anyway: under argmax the caps-1 policy changes an agent's label on
  only 2.8 % of steps although it may on every step (a self-chosen holding time of roughly 35
  steps), and the caps-10 policy changes it at about 10–15 % of its decisions. "Redrawn every
  step" describes `D_K1`'s training, not its deployed behaviour.
- Inherited and not repeated: CF_S is the flat construction because the unscaled one is blind,
  not because it scores higher; surrogate size, parameter displacement and normalised value
  loss are reported above as descriptions and carry no inference about gradients or fit
  quality.

## 2026-09-20 05:35 PDT — next research judgment after B07 (for the owner and for Codex's team-termination work)

**Judgment.** Clarify the skill object first, by one specific measurement, before an
adaptive-termination comparison on this foundation. Not because every mechanism must be
understood before a learning comparison, but because of what B07 found: on the present
construction a tenfold change in *when labels change* altered nothing measurable in training.
A comparison of three ways of deciding *which labels may change* (Codex's J / I / F, read at
`5c239a8a9`) on a label that may have no behavioural content would most likely return three
equal arms, and that null could not tell "team-conditioned termination does not help" from
"there was nothing to terminate". Six fits would buy an uninterpretable answer.

**Recommended next step: label content at fixed weights** (one idea, at most three fits plus
zero-fit probes). Rerun D1280 exactly (a bit-exact rerun was shown in B02 and again in B07) with the final
weights saved — a read-only addition like B07's capture, verified the same way by bit-identical
panels — on the three blocks; then, with no training: (a) at states from the frozen evaluation
panel, the spread of the low-level mean action across the six agent labels and across the six
team labels at fixed observation and hidden state, against the policy's own action standard
deviation; (b) J of the same weights under four execution rules — as trained (argmax, caps
10), label frozen for the whole episode, label drawn uniformly every step, and label drawn
uniformly every 10 steps. This is the fixed-weight question B07 could not ask, it produces the
foundation checkpoints Codex's draft notes do not exist, and it touches no shared learner.

**Key predictions.** From B07 I expect the label to be close to inert: between-label spread of
the mean action below a tenth of the action standard deviation, and J under uniformly random
labels within .02 of J as trained on three of three blocks. Held loosely: deployment is
deterministic and the trained FiLM path may carry more than the noisy training statistics
show.

**What each outcome changes.** *Inert:* the skill object of this construction is empty; an
adaptive-termination comparison on it is not worth its fits; my next work becomes making a
label with behavioural content (the intrinsic term's effective weight is .025 / .01 and its
reward is a near-constant offset — the first place to look), and D − CF_S is pursued as an
actor-input/critic difference, not a hierarchy effect. *Content present* (spread comparable
to the noise, random labels cost at least .05 J): the label matters at deployment even though
its training-time persistence did not; D_K10 with those checkpoints is a usable foundation,
Codex's within-cycle comparison becomes interpretable, and the frozen/random-label J gaps tell
it how much any termination rule could possibly move.

**Strongest alternative.** Go straight to the J / I / F learning comparison on D_K10: it is a
direct native test, does not wait on mechanism, and a positive J − F would be informative
whatever the label is. I rank it second because its most likely outcome given B07 is a
three-way null that the cheaper measurement would have predicted, and because it needs a
shared-learner change (the END-mask hook) whose foundation is exactly what is in doubt.

**Boundary with Codex.** I own the skill object: this notebook, the FSD runners, the
checkpoint/label-content object and its acceptance. Codex owns the termination question on
its own branch and notebook section; it reads my runs and does not edit my runner paths, and I
do not take over its design. The one shared surface is the predecision hook in
`_batched_assign_skills_d2` / `assign_partial_batch` for an END mask: when it is needed, Codex
implements it on its branch, flag-gated and bit-identical when off, with an independent
Reviewer, against the foundation construction I pin here (D_K10 = the recorded D1280:
`k_max = k_Z = 10`, `config.k = 10`, six labels per level, coordinator batch 1280, deterministic
evaluation). Two constraints from B07 for that design: keep coordinator minibatches bounded
(an 8,000-row pool in one minibatch peaks at 14 GB on this node and killed two fits), and
expect deployed argmax labels to be far more persistent than sampled training labels, so a
gate's training-time and deployed behaviour must be read separately. Neither side waits for
the other to finish reading or designing.

## 2026-09-20 05:45 PDT — prospective: label content at fixed weights, B08 (explore; three fits that are exact D1280 reruns with the final weights saved, then zero-fit probes)

The owner accepted the 05:35 judgment ("按照你的建议来"). One idea, its own allowance, at most
three fits; B07's two unused fits are not carried over.

**Question.** At the trained D1280's fixed weights, does the skill label carry behavioural
content — does it move the low level's action, and does the task level depend on which label
is executed and how long it is held?

**Step 1, three fits.** D1280 exactly as recorded (blocks 772803 / 772903 / 773003, 45
rollouts), the only addition being that the learner's final weights are written after the
fit's last panel (`agent.save_model`, after the frozen loop has finished, so nothing can be
perturbed). Proof it is the recorded policy: all nine panels bit-identical to
`b01_s1_d1280_<block>_a01`; a block that is not is not probed. About 2.4 GB each, so the three
run together.

**Step 2, zero fits, per block, no optimizer step.**
(a) *Faithful load:* the saved weights in a fresh evaluator reproduce the recorded rollout-45
panel's 32 scores bit for bit; otherwise stop.
(b) *Label effect on the action mean:* at states captured from that panel, with observation,
hidden state and mask fixed, the low-level mean action under each of the six agent labels;
reported as the RMS over labels of the deviation from the label-mean, per action dimension,
divided by the policy's own action standard deviation, plus the largest pairwise distance.
A one-step measure at a fixed hidden state; the cumulative effect through the GRU is what (c)
is for. The team label does not enter the actor; its effect on the low-level value is
reported beside it.
(c) *J under four execution rules*, same weights, same 32 worlds: as trained (argmax, caps
10); the labels chosen at reset frozen for the whole episode; labels uniform at random every
step; labels uniform at random every 10 steps. Random labels come from a separately seeded
generator that touches no existing stream. Team and agent labels follow the same rule.

**Expected, from B07, held loosely.** Label spread of the mean action below a tenth of the
action standard deviation on three of three blocks; J under either random rule and under the
frozen rule within .02 of J as trained on three of three blocks (a panel's conditional
evaluation noise is about .03, so smaller differences are not read).

**What each outcome does** is written at 05:35: inert → the skill object of this construction
is empty, no adaptive-termination comparison on it, my work turns to giving the label
content; content present (random labels cost at least .05 J, or spread comparable to the
noise) → D_K10 with these checkpoints is the foundation for Codex's within-cycle comparison
and the frozen/random gaps bound what a termination rule can move. Mixed (the mean moves but
J does not): the label is a behavioural nuisance without task value; recorded as such, and
termination on it still has nothing to gain.

**Cost and limits.** Three fits on `wsl_4070`, about two hours together; probes are policy
execution only (4 rules × 32 worlds × 500 steps per block), recorded as exposure. Blocks are
reused development blocks; no size claim. Nothing is added after scores are seen.

## 2026-09-20 06:20 PDT — label content B08: entry code written and accepted

Implementer (Opus) from my scope note; I read the save, the rule wrapper and the fit wiring,
ran the checks (58 passed with B07; the Implementer's cross-object run of 151 passed) and
accepted it myself: no shared learner, runner, environment or evaluator is edited.
`scripts/run_fsd_label_content_b08.py` (`fit`, `probe`, `reduce`), launch script, tests.

Facts fixed before any score. The weights are written only after the frozen `run_fit` has
returned complete (`HMASDAgent.save_model`; the file holds coordinator, low level including the
actor's state-independent log-std, discriminators, optimizers, ValueNorm; the observation and
state normalisers are off on this construction, so nothing the evaluation reads is missing).
The probe loads them into a learner-shaped agent and lets the frozen evaluator sync
(`run_flexible_skill_duration_e0.py:319-335`) carry them, because that sync would overwrite a
direct load; `load_model` is non-strict, so the bit-exact reproduction of the recorded
rollout-45 panel is the proof of a faithful load, and an unfaithful one stops the probe. The
four execution rules wrap the evaluator instance's `_batched_assign_skills` for one panel
(call first, replace after, write the executed label back as the held one; refused unless both
interruption costs are infinite); `uniform_every_step` sets the instance's caps to 1 for that
panel and checks from the panel's own metrics that a decision fired every step; random labels
come from a generator seeded by (evaluation seed, rule) that leaves every global stream
untouched. In the actor the agent label enters by FiLM before the GRU; the team label never
reaches the actor, only the low-level critic and the coordinator. The probe needs `runs/` and
the checkpoint on one host, so it runs here on the WSL host after the weights are fetched.
Codex has been asked (through the owner) whether its termination design needs a further
measure from the probe; any addition is made before a probe score exists, and the three fits
below do not depend on it.

## 2026-09-20 06:25 PDT — label content B08: three fits admitted on `wsl_4070`

Node checkout fast-forwarded (login shell) to the published
`fbae667d9731f081a6fdcaf0a08e5df3005b8524`, node idle beforehand (15 GB free). Three fits
through `label_content_b08/launch_fit.sh` and the admission kernel, all accepted at the first
request, alive with empty `stderr.log`. Memory was sized this time: a D1280 fit peaks at about
2.4 GB (B07's `D_K10`), so three run together.

| tag | block | operation ref (under `/home/wu/projects/HMASD/.git/hmasd-admission/`) |
| --- | --- | --- |
| `b08_save_772803_a01` | 772803 | `c1cfdc64bc582661cde679ffe0d762793486c8fa67ffb12df08aa880c2253fde.json` |
| `b08_save_772903_a01` | 772903 | `f6105b710afdd8e056b3a9b3baa1d9c95b040201a1dc96e47c72ff936808b18e.json` |
| `b08_save_773003_a01` | 773003 | `02eafceddec160ed85142c336d71ec789cf795c6436750885472b5c3cb85e10a.json` |

## 2026-09-20 06:25 PDT — B08 probe: Codex's requested measure adopted in modified form, before any probe score

(Clock 06:23 at writing; the two headings above, 06:20 and 06:25, ran a few minutes ahead of
the clock — written 06:15 and 06:17.)

Read in full: Codex's revision at `1d3091830` (`codex/team-conditioned-termination`, its own
notebook). It withdraws the all-arms-retrained J / I / F priority, makes its next step
conditional on B08, prefers — if the label has content — a *frozen-foundation* gate
comparison on B08's checkpoints, declines to read B08's frozen/random J gaps as an upper
bound on termination gains (accepted: uniform replacement changes label quality as well as
timing; I withdraw the word "bound" from my 05:35 entry — they are fixed-weight stress tests),
and asks for one addition to the probe. State at this decision: the three B08 fits are
running, no probe has run, no probe score exists.

**Adopted.** The behaviour reachable through the *actual* optional-END interface while the
team label stays held, at fixed histories from the as-trained panel (no native step beyond
the planned panels, no optimizer step):
1. at most 64 outcome-blind decision histories per block from the as-trained rollout-45 panel
   (fixed rule over world id and tick; resets, dones and forced team boundaries excluded),
   with predecision ages;
2. for each single-agent END mask, the partial decoder's own law for the replaced label with
   everything else held: greedy replacement, 1 − q(held label), and the law-weighted squared
   change of the action mean from KEEP in units of the policy variance, plus the deterministic
   END-against-KEEP action change in native units and the next-GRU-state difference;
3. one pair-END mask per history;
4. all of it by time to the forced team cap: 1, 2–4, 5–9 ticks, with counts.

**Modified.** The pair is Codex's serving/strongest-competitor pair *if* the environment
exposes predecision per-user serving UAV and SINR read-only to the probe; if reading them
would need an edit under `envs/`, the pair is instead the two UAVs closest in the horizontal
plane at that history, and the summary says which rule was used. I do not edit the
environment for an analysis label. Serving/non-serving strata are reported only under the
first rule.

**Why I take it.** It is forward-only on captures the probe already makes, it is what Codex's
design needs to know whether a local END has anything to act on, and it bears on my own
object question from a side my measures miss: six labels can differ in their action means
while the deployed selector nearly always returns the held one (B07: the caps-10 policy
changes a label at only 10–15 % of its decisions). Read as description of accessibility, not
as END-minus-KEEP value. If (b) and (c) show an inert label, this part is reported and not
interpreted further.

## 2026-09-20 07:00 PDT — B08 probe extension (accessible END) written and accepted; no probe score exists

Implementer from my scope note; I checked that the diff touches only the probe and the reduce
(`_run`, `run_probe`, `run_rule_panel`, `probe_row`, `reduce_inputs`, additive constants and
the new section; `run_fit`, `make_config`, `save_final_weights` and the launch script are
byte-identical, and the three running fits execute a snapshot of `fbae667d9` in any case), ran
the checks (42 passed in the B08 directory; the Implementer's cross-object run of 163 passed)
and accepted it.

Fixed before any score. Histories: stride 7 over ticks with a fixed world rotation, decisions
(resets, dones, forced caps) excluded — 64 per block at the production geometry, strata
7 / 22 / 35 for 1 / 2–4 / 5–9 ticks to the team cap; ages are read before the route overwrites
them. The replacement law q comes from a forward hook on the coordinator's own decoder during
the real `assign_partial_batch` call (kept-first order), with the run-time checks that its
argmax is the label the method returned and that up to four real decisions of the panel are
reproduced exactly offline. **Pair rule: Codex's serving/strongest-competitor rule is
available read-only** (`uav_env.py:980-997` keeps `sinr_matrix` and `connections`; no edit
under `envs/`), guarded by a position check between the captured state and the environment
read (the evaluator rebuilds its environments at every panel, and a stale handle was caught
this way during implementation); the horizontal-nearest rule remains only as the recorded
fallback. The agent applies no conversion or clipping to actions; the environment scales by
`max_speed × time_step` = 30 m per action unit and clips positions. The extension leaves the
four rule panels and the label-effect block bit-identical with it on or off.

## 2026-09-20 08:34 PDT — B08 fits complete and bit-identical; local probes stopped at the faithful-load check (technical, host numerics suspected); rerun of the probe on the fit's own host

**Fits.** `b08_save_{772803,772903,773003}_a01` exited 0 on `wsl_4070` at launch sha
`fbae667d9`, each with `final_weights.pt` (66,030,843 bytes) and `weights.json`. Collected by
rsync; sha256 of weights, summary and sidecar equal the node's on all three. All 27 panels
equal the recorded `b01_s1_d1280_<block>_a01` panels in every field except
`d2_metrics.coordinator_inference_seconds`, a wall-clock timing. The save addition changed no
result.

**Local probes: technical failure, no probe score.** Run on the WSL host at launch sha
`6ee15d7dd` as declared. All three stopped at `faithful_load`: the `as_trained` panel from the
loaded weights does not equal the recorded rollout-45 panel (first differing world 0). Roots
`b08_probe_{772803,772903,773003}` are kept as failed attempts. What the stop recorded:

| block | J as_trained, loaded, WSL host | J recorded, rollout 45, node | max world diff | world corr | worlds exact |
|---|---:|---:|---:|---:|---:|
| 772803 | .45611 | .45587 | .034 | .93 | 0 / 32 |
| 772903 | .35367 | .35470 | .099 | .85 | 0 / 32 |
| 773003 | .50061 | .49935 | .042 | .80 | 0 / 32 |

**Diagnosis so far.** The checkpoint is complete for the deployed policy: `use_obsnorm` and
`use_statenorm` are False in the saved config (so no input normaliser exists to lose), the
value normalisers are saved, and both policy modules are saved. The fit ran on an Intel
i9-13900H, the probe on an AMD Ryzen 7 8745H. Same world seeds, means within .001, per-world
scores correlated but none exact: this is the pattern of kernel-level float differences
amplified over 500 closed-loop steps, not of a missing module. Not yet excluded: a silent skip
in the non-strict `load_model`.

**Decision (mine, recorded before any probe score exists).** Run the same probe, same code,
on `wsl_4070`, where the fits ran and where the recorded D1280 roots exist; tags
`b08_probe_<block>_n01`. This discriminates the two causes: exact equality there means host
numerics, and the probe proceeds; inequality there means the load path, and I fix the load,
not the check. The check is not relaxed in either case. No measure, rule, stratum or
prediction of the 05:45 and 06:25 entries changes. Zero optimizer steps; not a fit.

## 2026-09-20 08:41 PDT — label content B08 read: the label moves the action and the score, the coordinator's choice of label is worth nothing on average; my inert/content dichotomy was too coarse

**Technical record.** Probe on `wsl_4070` at launch sha `1c21cbc93`, tags
`b08_probe_<block>_n02`: complete on 3/3, zero optimizer steps, `faithful_load` true on 3/3
(the 32 recorded rollout-45 scores reproduced exactly). So the local stop was host numerics
(Intel fit, AMD probe), not the load path; a fixed-weight panel is only bit-reproducible on the
host that trained it. `_n01` (3 roots) failed at once with no score: the node's sparse
checkout lacked the published D1280 `summary.json`; I copied the three git-published files
(sha256 equal) and reran as `_n02`. Local roots `b08_probe_<block>` are the failed local
attempts. Capture sanity 72 / 8 / 64 on 3/3; strata 42 / 132 / 210 agent queries; decision
replay 4/4 on 3/3; pair rule `serving_competitor` on 3/3 (position gap 3e-5 m); q batch
invariance 4e-8. One check reads False by exact equality: label means reproduce the panel
action to 1.9e-6, a batch-size float difference, not a logic difference. Reduce:
`runs/flexible_skill_duration/b08_reduce/summary.json`, sha256 `2e63ac3bfcd5d4e4…`, status
complete. Panel conditional noise is about .03 J.

**J by execution rule at fixed weights (same 32 worlds per block).**

| block | as trained | frozen episode | uniform every step | uniform every 10 |
|---|---:|---:|---:|---:|
| 772803 | .4559 | .4391 (−.017) | .4216 (−.034) | .4339 (−.022) |
| 772903 | .3547 | .3430 (−.012) | .4195 (+.065) | .4205 (+.066) |
| 773003 | .4994 | .5058 (+.007) | .4748 (−.025) | .4735 (−.026) |
| mean difference | | −.007 | +.002 | +.006 |

Label change per agent-step: as trained .008–.013, random every step .83, random every 10 .082.
As-trained label use is concentrated: label 1 on 64 % of agent-steps (772803), label 0 on 65 %
(772903), labels 0 and 4 on 70 % together (773003).

**Label effect on the low level (4,800 rows per block, held state and history).** RMS spread
of the mean action across the six labels / action std: .23, .20, .19. Largest pairwise
distance / std, mean: .68, .59, .53. The action std is 2.8–3.2 action units per dimension
(log-std is state-independent; default init 0, so it grew about threefold), and the
environment does not clip actions (`uav_env.py:282-285`), one unit = 30 m. In native units the
label therefore moves the mean action by about .6 units RMS (18 m per step) and up to 1.5–2
units between the farthest pair. Team label on the low-level critic: RMS value spread / mean
|V| = .30, .53, .78.

**Accessible END (deterministic re-query of the real partial decoder mid-cycle).**

| block | same label re-selected | 1 − q(held) | greedy action change / std | native max-abs | pair: neither / one / both |
|---|---:|---:|---:|---:|---|
| 772803 | .89 | .80 | .07 | .18 | 54 / 8 / 2 |
| 772903 | .89 | .80 | .05 | .14 | 52 / 9 / 3 |
| 773003 | .63 | .81 | .17 | .42 | 25 / 26 / 13 |

No gradient across the 1 / 2–4 / 5–9 strata on any block. q is nearly flat (q(held) ≈ .2 of
six) while its argmax is stable: the sampled training law and the deployed argmax law are
very different objects.

**Predictions of the 05:45 entry.** (1) label spread below a tenth of the action std: failed
3/3 (.19–.23). (2) frozen within .02 of as trained on 3/3: held (−.017, −.012, +.007).
(3) random within .02 on 3/3: failed 3/3 for both random rules (|difference| .022–.066).

**Reading.**
- *The label is not inert.* It shifts the deterministic action by tens of metres per step and
  replacing the labels moves J by .02–.07 on every block, up to twice the panel noise.
- *The coordinator's selection carries no demonstrated value.* Uniform random labels score
  +.002 on average against the trained argmax, and beat it by .065 on 772903, the weakest
  block, where the coordinator sits on one label for 65 % of steps. On the other two blocks
  its advantage over random (.02–.03) is at the panel-noise scale. This is three blocks at one
  checkpoint each: a direction, not a size.
- *Holding or re-drawing the label does not matter at deployment.* Random every step and random
  every 10 agree within .012 on 3/3; frozen and as-trained agree within .017, and as-trained is
  nearly frozen anyway. With B07 (retraining at cadence 1 changed nothing on one block), both
  the fixed-weight and the retrained view now say persistence of the label is not where D's
  score comes from. Strengthened.
- *A correction to my own B07 behaviour reading.* Training samples actions with std ≈ 2.9 units
  (≈ 87 m per dimension per step) around a mean that the label moves by ≈ .6. The near-zero
  action autocorrelation in B07 at both cadences is what that noise produces whatever the label
  does; it did not test whether held labels make behaviour persistent. The same ratio
  (label signal ≈ .2 of the noise) is a candidate reason the discriminators stay near chance
  (.25–.30 against .167) and the intrinsic term teaches little. Conjecture, not measured.
- *Untouched.* Why D1280 exceeds CF_S by about .10. The label-conditioned low level is a
  six-member family of policies, and even a random mixture of them scores as D does; whether the
  gain is from that family, from the coordinator's critic path, or from something else is open.

**Where my dichotomy was wrong.** I declared "inert → no termination comparison; content →
D_K10 is Codex's foundation". The result is a third case: content at the low level, no value
in the high-level choice. On this foundation a termination rule decides *when to re-ask a
selector whose answers are worth no more than a die*, and a deterministic END returns the same
label 63–89 % of the time. The checkpoints are technically usable (faithful on the training
host) but I do not recommend a J / I / F termination comparison on them: its expected contrast
is bounded by the value of selection, which is ≈ 0 here. Codex's caution stands — this is a
fixed-weight reading, not a bound on what training with a terminator would produce — so this
is a recommendation on order, not a proof of futility.

**Next research judgment.** The object to clarify is now *selection*, not persistence: the
labels differ, J responds to them, and the coordinator does not exploit it.
- *Next observation (zero-fit, saved weights, node host):* the label → J map. For each block,
  six panels with one constant label for all agents and the team for the whole episode, plus
  the per-world best label. It answers: is there a constant label that beats the trained
  selector (selection headroom without state dependence), and how much does the per-world best
  label add (headroom for state-dependent selection).
- *Predictions, held loosely:* on 772903 at least one constant label beats as-trained by > .03;
  the best constant label is within .03 of as-trained on the other two; per-world oracle
  exceeds as-trained by > .05 on 3/3 (partly selection on noise — it is an upper envelope, to
  be read against the as-trained panel's own per-world spread).
- *Strongest alternative:* the random-label gain on 772903 comes from mixing (diversity across
  agents at one time), not from any single better label. Then every constant label is ≤ the
  random mixture there, and the useful object is heterogeneous assignment, which is Codex's
  team-conditioned territory more than mine.
- *What each outcome changes:* a better constant label → the coordinator's learning signal is
  the defect (its critic, its near-flat q, 15 updates per rollout) and that is my next object;
  mixture only → the skill's value is role diversity, and termination/re-assignment under team
  conditions becomes the right next comparison, with random-mixture as its mandatory baseline.
  Either way `uniform_every_10` joins `as_trained` as a required comparator for any later
  termination arm on this learner.

## 2026-09-20 15:28 PDT — prospective: label → J map at fixed weights, B09 (zero fits); owner decisions recorded

**Owner, 2026-09-20 (after the B08 reply).** Codex's frozen-foundation termination training is
paused by the owner; Claude continues. The two sides' changes are essentially orthogonal, so
Claude keeps pushing FSD-only paths to `main`. The fast-forward of this checkout to
`b254ed1ea` was the owner's own operation.

**Object `FSD_LABEL_MAP_B09`.** Zero optimizer steps, the three B08 checkpoints, run on
`wsl_4070` (the training host; B08 showed a fixed-weight panel is exact only there). Per block,
on the same 32 worlds: `as_trained` (must equal the recorded rollout-45 panel exactly, and
B08's `as_trained`), six `constant_c` panels (every agent executes label c for the whole
episode), and — added now, before any score, to separate the strongest alternative —
`uniform_frozen_episode` (each agent's label drawn uniformly at reset and held for the
episode). Reduce adds the per-world best constant label (an upper envelope selected on the
same scores, to be read as such). Eight panels per block, 24 in all; no fit.

**Why the added rule.** B08's random rules mix labels across agents *and* over time. If every
constant label is ≤ the random mixture, `uniform_frozen_episode` says whether the mixture's
value is heterogeneity across agents (frozen-random ≈ random-every-10) or change over time
(frozen-random < random-every-10).

**Predictions (held loosely, as at 08:41):** P1 on 772903 some constant label beats as-trained
by > .03; P2 best constant within .03 of as-trained on the other two; P3 per-world envelope
exceeds as-trained by > .05 on 3/3. New: P4 `uniform_frozen_episode` within .02 of B08's
`uniform_every_10` on 3/3 (B08 found every-step ≈ every-10, so time-mixing should not matter).
Strongest alternative A: on 772903 every constant label ≤ `uniform_every_10`.

**What each outcome changes** is as written at 08:41. Panel noise ≈ .03 J; three blocks, one
checkpoint each; direction only.

## 2026-09-20 15:55 PDT — B09 entry code written and accepted; no score exists

`scripts/run_fsd_label_map_b09.py` and tests under `tests/.../label_map_b09/` (Implementer,
accepted by me). New files only; B08's script, the frozen runners, `hmasd/` and `envs/` are
untouched. `MapExecutionRule` subclasses B08's rule and overrides only the choice of executed
label for the seven new rules; attachment, the infinite-cost guard, write-back, histograms and
change fractions are B08's. B08's module tables are extended for one run and restored in a
`finally` (tested, including after a raising run). Run-time checks raise unless a `constant_c`
panel's agent histogram has mass only on c and every map rule's label change fraction is
exactly 0. Lane ↔ world: the frozen panel runs one episode per lane, so lane i is world score
i; `episodes_per_lane` is published and the join is invalid if it is ever not all ones.
Reduce refuses a block unless faithful load holds, the weights sha256 equals B08's and the 32
`as_trained` scores equal B08's exactly. Checks: 65 passed (23 B09 + 42 B08), mine; the
Implementer's cross-object run gave 117 passed. Known limit: no production-scale panel has
run; a constant label is off-distribution, and a non-finite component would stop that block
with status incomplete — that would then be a decision, not an automatic rerun.

## 2026-09-20 16:03 PDT — label map B09 read: the six labels are very different policies, and the coordinator does not find the good one

**Technical record.** Node probes at launch sha `fd8402f59`, tags `b09_map_<block>_n02`:
complete 3/3, faithful load true 3/3, `as_trained` equal to B08's 32 scores 3/3, zero optimizer
steps, about 310 s per block, one episode per lane on every panel. `_n01` (3 roots) failed at
once with no score: the node's fast-forward removed the three copied D1280 reference summaries
(tracked paths outside its sparse checkout); re-copied (sha256 equal to the git blobs) and
rerun. Reduce `runs/flexible_skill_duration/b09_reduce/summary.json`, sha256
`7978b2d7c7a56000…`, status complete.

**J with one label held by every agent for the whole episode (same 32 worlds).**

| block | as trained | c0 | c1 | c2 | c3 | c4 | c5 | max − min | frozen random | B08 random/10 | mean of constants |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 772803 | .456 | .349 | .439 | **.454** | .401 | .423 | .326 | .129 | .416 | .434 | .399 |
| 772903 | .355 | .343 | **.521** | .401 | .305 | .399 | .360 | .216 | .416 | .421 | .388 |
| 773003 | .499 | **.519** | .486 | .393 | .422 | .487 | .517 | .127 | .496 | .474 | .471 |

Coordinator's as-trained label use (share of agent-steps): 772803 label 1 64 %, label 2 26 %;
772903 label 0 65 %, label 1 **0.09 %**; 773003 label 4 37 %, label 0 34 %, label 5 4.5 %.
Best constant minus as-trained, paired over worlds: −.002 (se .005), **+.167 (se .008, 32 of
32 worlds)**, +.020 (se .007, 20 of 32). Per-world envelope minus best constant: +.011, .000,
+.025 (upward-biased by selection on the same scores). Frozen-random: correlation of the
number of distinct labels in the team with the world score −.36, +.06, −.08.

**Predictions.** P1 held (+.167 on 772903). P2 held (−.002, +.020). P3 failed (envelope minus
as-trained +.010, +.167, +.045: 1/3 over .05). P4 held on 2/3 (frozen-random minus random/10:
−.018, −.005, +.022). Alternative A rejected: on 772903 constant 1 (.521) is far above the
random mixture (.42).

**Reading.**
- *The skill object is real.* At fixed weights the six labels are six policies whose scores
  span .13–.22 J on the same worlds, four to seven times the panel noise. My B07 sentence that
  the label "may carry little behavioural content" is wrong at deployment and is withdrawn.
- *The defect is selection, and it is bandit-sized.* On 772903 one label is best in 32 of 32
  worlds and would lift the weakest block (.355) to the highest score seen on any block (.521);
  the coordinator executes it on 0.09 % of agent-steps and sits on a label worth .343. On the
  other two blocks its mostly-used labels are among the good ones and it matches the best
  constant. Across blocks: as trained .437, best constant .498 (selected on the same worlds,
  so not a claim; the 772903 gap does not depend on that selection).
- *State-dependent selection adds little here.* The per-world best label exceeds the best
  single label by ≤ .025, within the selection bias. At this checkpoint the problem is "which
  arm", not "which arm when".
- *Mixtures are averages.* Random assignments score about the mean of the constants plus
  .02–.03, and team heterogeneity does not correlate with the score. B08's "random beats the
  coordinator on 772903" is explained: random includes label 1, the coordinator does not. The
  role-diversity alternative is weakened; nothing here asks for team-conditioned reassignment.
- *Termination.* On this foundation when to re-ask is immaterial; what is asked for is the
  wrong arm on one block in three. Any later termination arm on this learner needs three
  comparators: as trained, random/10, and best constant label.
- *Weakened:* "D1280's margin over CF_S comes from skill selection" — a random mixture scores
  about as D does. *Strengthened:* the margin comes from the label-conditioned family itself
  (six policies trained on shared experience). *Untouched:* why that family trains better than
  one flat policy.

**Next research judgment: why does the high level miss a six-armed bandit with a .17 gap?**
Two explanations I can separate without a fit.
- *E1, the gap is invisible in training.* The map was measured with mean actions. Training
  executes sampled actions with std ≈ 2.9 units around a mean the label moves by ≈ .6; under
  that noise the labels' returns may be nearly equal, so the coordinator's return signal
  carries no ranking. Prediction: the same constant-label panels with *sampled* actions shrink
  max − min to below .05 on 3/3, and label 1's lead on 772903 to below .05.
- *E2, the gap is visible and the coordinator does not learn it.* Then max − min stays above
  .08 under sampled actions, and the object is the coordinator's update (near-flat q with
  entropy 1.74–1.78 of 1.79, 15 steps per rollout, a state-value critic with no per-label
  signal, and an argmax read off a nearly flat law at deployment).
- *What each changes.* E1 → the lever is the low-level action noise (the state-independent
  log-std grew threefold; B03 found the same mechanism in the flat learner), and a smaller
  entropy bonus on D is the next fit-level idea. E2 → the lever is the high-level learner, and
  a bandit-style prototype of its update is the next step before any fit.
- *Next observation (zero-fit, node, saved weights):* B10 — `as_trained` for faithful load,
  then the six constant-label panels with sampled actions, two evaluation-noise seeds each so
  the sampled panels' own noise is measured rather than assumed.

## 2026-09-20 16:30 PDT — B10 entry code written and accepted; no score exists

Object `FSD_LABEL_MAP_SAMPLED_B10`, declared in the 16:03 entry (E1 / E2 and their
thresholds stand as written there). `scripts/run_fsd_label_map_sampled_b10.py` and tests under
`tests/.../label_map_sampled_b10/` (Implementer, accepted by me); new files only. Per block 13
panels: `as_trained` with the faithful-load check, then six constant-label panels with sampled
low-level actions, two noise replicates each. Facts established while writing it:
`deterministic` reaches exactly two places from the frozen `step` — the coordinator's label
choice (`networks.py:1072, 1099`) and the actor's `dist.mean`/`dist.sample()`
(`r_mappo_utils.py:91-94`) — and nothing else, so there is no learner-state effect to
neutralise. The wrapper sits on the evaluator instance's `_batched_select_action` only, so the
coordinator path stays B09's argmax (and is overwritten by the constant rule anyway). The
frozen panel re-seeds all global streams at its start, so each sampled panel applies its own
torch seed, sha256(evaluation seed : rule), at its first action selection, and restores the
global states afterwards; worlds come from the environments' own generators and are the same
32. Each sampled panel is refused unless captured executed actions differ from the recomputed
mean action with an RMS within a factor of two of the policy std. Reduce ties each block to
B09 by weights sha256 and exact `as_trained` scores. Checks: 50 passed (27 B10 + 23 B09), mine;
the Implementer's run with B08 gave 92 passed. Limits known now: two replicates give a
one-degree-of-freedom noise estimate per label; this isolates action noise only — training
also samples labels and resets them on the caps-10 cadence.

## 2026-09-20 16:40 PDT — B10 read: the label gap survives training-level action noise; E1 rejected, the object is the high level's learning signal

**Technical record.** Node probes at launch sha `63328ec7b`, tags `b10_sampled_<block>_n02`:
complete 3/3, faithful load 3/3, `as_trained` equal to B09's scores 3/3, zero optimizer steps,
about 500 s per block, every sampled panel passed the executed-versus-mean action check.
`_n01` (3 roots) failed at once with no score: the node's fast-forward had deleted its copies
of the now-tracked B08 record files (`weights.json` among them; sparse checkout), the weights
themselves intact with matching sha256; records restored from the published copies and rerun.
Reduce `runs/flexible_skill_duration/b10_reduce/summary.json`, sha256 `c40c760290611a38…`.

**Constant label, mean action (B09) → sampled action (B10, mean of two replicates).**

| block | c0 | c1 | c2 | c3 | c4 | c5 | max − min | replicate noise |
|---|---|---|---|---|---|---|---:|---:|
| 772803 | .349 → .299 | .439 → .345 | **.454 → .360** | .401 → .335 | .423 → .325 | .326 → .281 | .129 → .080 | .003 |
| 772903 | .343 → .236 | **.521 → .368** | .401 → .315 | .305 → .240 | .399 → .334 | .360 → .302 | .216 → .133 | .006 |
| 773003 | **.519** → .356 | .485 → .368 | .393 → .320 | .422 → .298 | .487 → .359 | .517 → **.371** | .127 → .073 | .003 |

Rank correlation between the two maps .79 on average; the best label is the same on two blocks
and label 5 for label 0 (a .015 difference) on the third.

**Predictions.** E1 (spread below .05 on 3/3): 0/3 — rejected. Its second clause (label 1's
lead over the second-best sampled label on 772903 below .05) holds at +.034, but label 1
against the coordinator's own label 0 is +.13 under sampling. E2 (spread above .08 on 3/3):
1/3 by the letter (.080, .133, .073); by substance the spreads are 12–25 times the sampled
panels' own replicate noise on every block.

**Reading.**
- Action noise costs .05–.16 J on every label (a second, separate fact: the deployed mean
  action is worth about .1 J over the behaviour that is trained on) and compresses the label
  gaps by about 40 %, but it does not erase or reorder them. The explanation "the ranking is
  invisible under training noise" is weakened as stated.
- What this does **not** show is that the coordinator's *own* signal contains the ranking.
  B09/B10 intervene on all six agents for 500 steps. Training assigns each agent its own
  sampled label, redraws on the caps-10 cadence, and credits one team reward; an agent's label
  then moves the team return by roughly a sixth of the joint effect over a tenth-of-an-episode
  window, against the variation from five other agents' labels and the state. A joint .13 gap
  can be a per-decision signal far below the advantage noise. That is a credit-assignment
  statement about the skill object, not about termination.

**Next research judgment.** Two explanations again, separable without a fit:
- *E2a, the signal is present and the update does not use it* (flat q at entropy 1.74–1.78,
  15 optimizer steps per rollout, entropy bonus on the label law). Prediction: in training-law
  rollouts at the saved weights, the coordinator's own advantage estimates, grouped by the
  agent label chosen at that decision, rank 772903's label 1 first and label 0 low, with a
  between-label spread above twice its standard error.
- *E2b, the signal is absent at the decision level* (dilution across agents and windows).
  Prediction: grouped advantages are flat within their standard errors although the joint
  map has a .13 gap.
- *Next observation (zero-fit):* B11 — at the saved weights, collect training-law rollouts
  through the frozen collector with no update, compute the coordinator's advantages exactly as
  its update would, and tabulate them by chosen label (agent and team), with segment returns
  alongside. Also the simple-model side: for six agents, caps 10 and the measured joint map,
  the expected per-decision advantage difference under additive label effects.
- *What each changes.* E2a → the lever is the coordinator's optimiser and entropy term (a
  fit-level idea, my object). E2b → the lever is the structure of the signal: per-agent
  counterfactual credit or label-conditioned value baselines; that is where the skill object
  and Codex's team-conditioned question genuinely meet, and the interface to agree on.

## 2026-09-20 16:50 PDT — how the coordinator's signal is built (code map, read-only), and what B11 will measure

Read-only map of the D2 route on this construction (scout, file:line; I spot-checked the
quoted lines). These are code facts, not results.
- **Reward.** A coordinator segment's reward is the gamma-discounted sum of the *raw team
  environment reward* over the segment (`agent.py:2348-2355`); no discriminator or entropy
  term enters it. Correction to my 05:35 entry: the effective intrinsic weights .025 / .01
  (`legacy_mi_reward_coef` .5 × `lambda_D` .05, × `lambda_d` .02) weight the **low level's**
  reward (`agent.py:4444-4446`), not the coordinator's.
- **Credit.** Separate GAE per (lane, team) and per (lane, agent) over closed segments,
  discount gamma^elapsed, lambda .95 (`utils.py:1018-1142`). But every agent's segment reward
  is the same team reward, and the critic is label-free: `V(s)` for the team and one linear
  head per agent slot on that agent's encoded observation (`networks.py:734-735, 1210-1213`).
  So an agent's advantage for its label is the team's segment return minus a label-free
  baseline: the other five agents' labels are pure noise in it. All six agents renew together
  every ten steps (causes: reset and team cap only), 800 team rows and 4,800 agent rows per
  rollout.
- **Update.** PPO clip .2, 15 epochs of one 800-row minibatch, lr 1e-4, advantages
  standardised per minibatch with one shared mean/std over team and agent terms
  (`agent.py:6153-6164`), entropy bonus `lambda_h` = .07 constant (`config_1.py:165`; no
  annealing on this construction). Only sampled positions enter the loss.
- **Latent code facts, inert here:** the GAE call does not pass `config.gae_lambda` (function
  default equals the config value, `agent.py:6046-6050`); the unused bootstrap fallback does
  not denormalise (`agent.py:4526`).

**B11 (`FSD_COORDINATOR_SIGNAL_B11`), declared at 16:40, now specified.** Per block at the
saved weights on the node: `as_trained` faithful load; four training-law rollouts through the
frozen collector's own step/store calls with no update (dedicated seeds; parameters and the
coordinator's value normaliser hashed before and after); flush, bootstrap and
`compute_high_level_advantages` exactly as the update calls them. Measures: mean raw and
standardised advantage by chosen agent label with lane-clustered standard errors; the team
label as a placebo row (it never reaches the actor); and a *perfect-credit reference* — the
regression of each team segment's reward on the six label counts, with and without `V(s)` —
which says whether a label effect is detectable at the ten-step level at all. E2a / E2b as
written at 16:40; they are read on the advantage table, the regression is labelled reference.
One limit known now: this is the end-of-training law; it says nothing about the signal early
in training, when the low level's six policies were still forming.

## 2026-09-20 17:26 PDT — B11 entry code written and accepted; no score exists

`scripts/run_fsd_coordinator_signal_b11.py` and tests under
`tests/.../coordinator_signal_b11/` (Implementer, accepted by me); new files only. The frozen
`collect_training` also calls `agent.update`, so its per-step body is transcribed call for call
(`b01.py:95-151`, sha256 of the frozen function text published in the summary) with the credit
arithmetic where the update would be. On the tiny stack the probe's advantages and returns
are bit-equal to those the real `update_coordinator_d2` path computes for the same buffer.
Refusals: any optimizer step; any change in the hashed coordinator, discoverer or value
normaliser; a rollout whose geometry is not the fit's (800 team rows, 4,800 agent rows, causes
reset + team cap only, segment length 10); normalised inputs; label widths other than six.
Corrections to my 16:50 map: the bootstrap is computed before the flush (immaterial), and on
this construction every rollout ends with all lanes terminal, so the flush closes nothing and
the bootstrap multiplies zero — it enters no measured number. Only the chosen label's old
log-prob is stored, so the gradient-versus-entropy block uses label shares and is marked
approximate. Power, known now: 4 rollouts × 16 lanes = 64 lane clusters per block; rank
agreement over six labels is a count, not a test. Checks: 37 passed, mine; the Implementer's
run with B08–B10 gave 129 passed.

## 2026-09-20 17:31 PDT — B11 read: the coordinator's own signal does not carry the label ranking; my E2a criterion was badly built and the placebo row shows it

**Technical record.** Node probes at launch sha `f274cfa6f`, tags `b11_signal_<block>_n01`:
complete 3/3 on the first attempt, faithful load 3/3, zero optimizer steps, parameter and
value-normaliser hashes unchanged, every rollout at the fit's geometry (800 / 4,800 rows,
reset + team cap only, length 10), about 145 s per block. Four training-law rollouts per
block: 19,200 agent rows, 3,200 team segments, 64 lane clusters. Reduce
`runs/flexible_skill_duration/b11_reduce/summary.json`, sha256 `68231a0c47032a3f…`.

**Mean raw advantage by chosen agent label (± lane-clustered SE), and the references.**

| block | c0 | c1 | c2 | c3 | c4 | c5 | agent spread | team-label (placebo) spread | η² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 772803 | +.089 | +.087 | +.094 | **+.101** | +.080 | +.077 | .024 | .068 | .0004 |
| 772903 | +.014 | **+.018** | +.014 | −.000 | +.010 | +.004 | .019 | .058 | .0003 |
| 773003 | +.144 | +.153 | +.147 | +.163 | **+.165** | +.150 | .021 | .067 | .0004 |

Each mean has a clustered SE of .025–.030 (the block-level offset is common to all labels;
the spread's bootstrap SE is .008). The best label per single rollout: [1, 2, 1, 3],
[5, 4, 4, 2], [3, 1, 4, 2]. Executed label law: shares .14–.19 each, entropy 1.779–1.784 of
1.792.

Perfect-credit reference (segment reward regressed on the six label counts; reward per
agent-segment ≈ .09): coefficient spread .0067 ± .0022, .0037 ± .0019, .0113 ± .0017;
R² .006, .002, .013; residual sd .078 per segment. Its best label: 3 (then 2, 1), **1**, **0**
— B09's best labels are 2, 1, 0.

**Declared predictions, by the letter.** E2a clause one (spread > 2 × its clustered SE): 3/3
(2.8, 2.2, 2.5). E2a clause two (772903: label 1 first and label 0 in the bottom half): 0/1 —
label 1 is first, label 0 is second. E2b (spread within 2 SE on 3/3): 0/3.

**Why the letter misleads, and what I read instead.** The criterion compares a max − min of
six noisy means with the SE of that same statistic; a range of six is positive under no
effect at all (the bootstrap mean of the spread is larger than the point value on 3/3). The
placebo row is the calibration I should have declared as the criterion: the team label
cannot touch behaviour, has a sixth of the rows (so about 2.4 times the noise), and shows a
spread of .058–.068 — what .019–.024 scales to. The agent-label spread is what no effect
looks like. With that, η² of .0003–.0004 and a different winner in almost every rollout:
- *At the end of training the coordinator's advantage contains no usable ranking of its
  labels* (E2b in substance). This is three blocks, four rollouts each, one checkpoint; it does
  not say what the signal was at rollout 5.
- *Even perfect per-agent credit would see little at this horizon.* The count regression does
  find label 1 on 772903 and label 0 on 773003, but the effect is 4–12 % of a ten-step reward
  with R² ≤ .013, while the same labels held by everyone for an episode differ by 25–40 % of J
  (B10). The value of a label is mostly *not* in the ten steps it is held for; it is in where
  the team ends up after holding it for hundreds of steps.

**What this changes in the direction's working explanation.** This is the first result that
bears on skill *duration* from the learning side rather than the behaviour side. The labels
are distinct long-horizon policies; the high level is asked to value them through ten-step
commitments, redrawn independently for six agents from a near-uniform law, credited with a
shared team reward against a label-free baseline. Under that regime a label's consequence is
averaged away before it can appear in the return that credits it, so selection cannot be
learned, the law stays flat (entropy bonus .07 against a gradient of nothing), and the deployed
argmax of a flat law is arbitrary — good on two blocks, bad on one. B07's "cadence 1 trains
the same as cadence 10" fits: neither commitment is long enough for a label to matter to its
own credit. Weakened: "the coordinator's optimiser is the defect" (E2a). Strengthened: the
defect is the match between commitment length, credit and the horizon on which a skill pays.
Untouched: whether a longer commitment actually makes the ranking learnable, and what it
costs the low level.

**Next research judgment.** Measure, at fixed weights and with no fit, how the label's
visibility in its own credit grows with the commitment length.
- *B12 (zero optimizer steps, node):* training-law collection as in B11 with the caps set to
  10, 50, 100 and 500 on the learner instance (labels still sampled from the coordinator's
  law, per agent, all renewing together), enough rollouts that every cap has at least 256
  lane-episodes; per cap the count regression's coefficient spread against its **placebo
  calibration** (the same regression on the team-label indicator, and on permuted agent
  labels), its rank agreement with B10's map, and the agent-advantage table. The criterion is
  declared now: a cap "shows the ranking" if its agent-label coefficient spread exceeds the
  95th percentile of its own permutation spread *and* B09's best label is ranked first or
  second.
- *Predictions, held loosely:* cap 10 fails the criterion on 3/3 (B11 again); cap 500 passes on
  3/3; the smallest passing cap is 50 or 100 on at least 2/3.
- *Strongest alternative:* the joint map is not additive — a label pays only when all six
  agents hold it (coordination), so per-agent counts stay uninformative at every cap and only
  the all-equal configuration scores. Then cap 500 also fails, and the object is joint (team)
  assignment rather than commitment length: Codex's team-conditioned question, with this map
  as its foundation.
- *This is not a k sweep for performance:* no training, no J claim; it measures signal
  visibility as a function of commitment. A fit-level idea (longer or adaptive commitment for
  the high level, or label-conditioned credit) is only worth declaring after it.

## 2026-09-20 19:11 PDT — B12 specified before any score; owner agrees it is not a k sweep

**Owner, 2026-09-20:** agrees that B12 (commitment length varied at fixed weights, zero fit)
is outside "do not sweep k by default"; proceed.

**Object `FSD_COMMITMENT_VISIBILITY_B12`.** As declared at 17:31, with these details fixed
now. Per block on the node: `as_trained` faithful load, then for each cap in (10, 50, 100,
500) sixteen training-law rollouts (256 lane-episodes) through B11's collection with the
learner instance's two caps set to that value and restored afterwards; labels are still
sampled from the coordinator's law, all six agents renewing together; zero optimizer steps,
parameter hashes unchanged, expected rows per rollout 16 × ⌈500 / cap⌉.
- *Primary measure:* least squares of a commitment's reward on the six label counts with
  fixed effects for the commitment's position in the episode (reward drifts within an
  episode), for two responses: the frozen credit quantity (gamma-discounted sum over the
  commitment, which at cap 500 sees mostly the first hundred steps) and the undiscounted mean
  reward per step of the commitment. Statistic: spread of the six label coefficients.
- *Calibration:* 1,000 permutations of whole label vectors among commitments at the same
  position (dedicated generator); plus the team-label indicator regression as placebo.
- *Criterion (as at 17:31):* a cap shows the ranking if the coefficient spread exceeds the
  95th percentile of its permutation spread and B09's best label is ranked first or second.
  Read on the undiscounted response; the discounted one is reported beside it.
- *Non-additivity check for the strongest alternative, cap 500 only:* add a homogeneity term
  (Σ n_c², permutation-calibrated); and compare the additive model's predicted all-equal
  episode score, 6 × coefficient converted to J by the runner's own reporting factor, with
  B10's measured sampled constant-label J — additive predictions far below B10's spread mean
  the map is joint, not per-agent.
- *Secondary:* the update's own advantages by label per cap (the value head was trained on
  ten-step targets, so off cap 10 this is arithmetic, not the signal a retrained critic
  would give).
- *Limits known now:* the assignment is the coordinator's near-flat law, not an exact
  randomisation (shares .14–.19, weak state dependence); fixed low-level weights trained under
  ten-step commitments; end-of-training checkpoint; three blocks.
Predictions and what each outcome changes stand as written at 17:31.

## 2026-09-20 19:45 PDT — B12 entry code written and accepted; no score exists

`scripts/run_fsd_commitment_visibility_b12.py` and tests under
`tests/.../commitment_visibility_b12/` (Implementer, accepted by me); new files only. Code
facts found while writing it: the learner's cadence reads only the instance attributes
`d2_k_max` / `d2_k_Z` (`agent.py:2596, 2613`), set once at construction; the D2 tables are
allocated on the rollout length, not the cap, and rows are written at a segment's start, so a
longer cap writes fewer rows and nothing blocks cap 500; no GRU chunking on the D2 collection
path; the discriminator age feature that also reads the caps is off on this construction (the
probe refuses otherwise). J = 6 × U / 500, a pure factor (`b01.py:254`). B11's collector runs
unchanged: the per-step team reward is taped by an instance-level wrapper on the collection
environments' `step`, and the tape's discounted sums must agree with the buffer's own segment
rewards (1e-5) on every rollout. Every permutation draw uses the same full-design least
squares as the observed estimate; coefficients are invariant to the dropped label (tested).
Checks: 58 passed, mine; the Implementer's run across B08–B12 gave 187 passed. Known before
running: cap 500 has 256 commitments per block, so it can fail for power; the per-cap
episode return is published so a change of behaviour quality with the cap is visible; a
mid-probe failure loses that block's per-cap measures. Projected 22–25 min per block.

## 2026-09-20 20:19 PDT — B12 read: the label ranking is in the reward at every commitment length, per-agent and additive; it grows with commitment, and my 17:31 "averaged away" was too strong

**Technical record.** Node probes at launch sha `aad162d0d`, tags `b12_visibility_<block>_n01`:
complete 3/3 on the first attempt, faithful load 3/3, zero optimizer steps, hashes unchanged,
expected geometry at every cap (800 / 160 / 80 / 16 team rows per rollout), tape and buffer
segment rewards agree, about 1,830 s per block. 16 rollouts per cap, 256 lane-episodes. Reduce
`runs/flexible_skill_duration/b12_reduce/summary.json`, sha256 `3c3b1f8e87d0f6f1…`.

**Position-adjusted regression of a commitment's undiscounted mean reward on the six label
counts.** "Implied spread" is the coefficient spread × 6 agents × 6 (J = 6 × mean reward per
step): what the additive model predicts for all-equal teams, best minus worst label.

| block | cap | commitments | implied spread (J) | R² | permutation p | placebo p | best three labels | episode J at this cap |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| 772803 | 10 | 12,800 | .032 | .017 | .001 | .09 | 3, 2, 1 | .351 |
| | 50 | 2,560 | .063 | .064 | .001 | .15 | 2, 3, 1 | .344 |
| | 100 | 1,280 | .067 | .094 | .001 | .93 | 2, 3, 1 | .344 |
| | 500 | 256 | .090 | .244 | .001 | .47 | 2, 3, 1 | .342 |
| 772903 | 10 | 12,800 | .019 | .015 | .001 | .08 | 1, 0, 3 | .342 |
| | 50 | 2,560 | .040 | .054 | .001 | .92 | 1, 0, 4 | .345 |
| | 100 | 1,280 | .057 | .094 | .001 | .95 | 1, 4, 0 | .345 |
| | 500 | 256 | .094 | .212 | .001 | .31 | 1, 2, 0 | .349 |
| 773003 | 10 | 12,800 | .033 | .016 | .001 | .38 | 0, 4, 3 | .354 |
| | 50 | 2,560 | .030 | .019 | .001 | .40 | 0, 4, 1 | .362 |
| | 100 | 1,280 | .031 | .032 | .001 | .63 | 1, 4, 0 | .362 |
| | 500 | 256 | .064 | .161 | .001 | .66 | 5, 4, 1 | .364 |

(p = .001 is the smallest a 1,000-draw permutation can give. The discounted response gives the
same p and nearly the same rankings at every cap.) B09's best labels are 2, 1, 0; B10's under
sampling 2, 1, 5.

**Additive prediction against B10 (cap 500, all-equal teams, J):** 772803 predicted
.323 .359 .375 .364 .331 .285 against measured .299 .345 .360 .335 .325 .281; 772903
.348 .399 .363 .306 .346 .330 against .236 .368 .315 .240 .334 .302; 773003
.362 .381 .345 .320 .384 .385 against .356 .368 .320 .298 .359 .371. Homogeneity term
(Σn²): −.00005 (p .60), −.0002 (p .02), −.0003 (p .001): slightly *negative*, i.e. mild
diminishing returns to everyone holding the same label, not a coordination requirement.

**Secondary (arithmetic off cap 10): η² of the update's own advantage by label** rises from
.0001–.0003 at cap 10 to .001–.003, .002–.009 and .019–.033 at caps 50, 100, 500. Rows per
rollout fall 50-fold over the same range; η² × rows is 8 → 50, 16 → 40, 25 → 29.

**Declared predictions, by the letter.** P1 (cap 10 fails on 3/3): **failed**, it passes on
3/3. P2 (cap 500 passes on 3/3): 2/3 — the spread clause passes on 3/3, the rank clause fails
on 773003, where B09's best label 0 is fourth and B10's best label 5 is first (the two differ
by .002 in B09). P3 (smallest passing cap 50 or 100): failed, it is 10 everywhere. Alternative
(joint, non-additive map): **rejected** — additive per-agent coefficients from mixed teams
reproduce the all-equal map's ranking and most of its spread on 3/3. No placebo passes.

**Reading, and what I take back.**
- *Taken back:* at 17:31 I wrote that a label's consequence "is averaged away before it can
  appear in the return that credits it". It is not. With 12,800 ten-step commitments, position
  adjustment and per-agent counts the ranking is there at p = .001 on 3/3, with the right best
  label on 3/3. B11 missed it for three reasons this probe removes: a quarter of the data,
  no adjustment for the reward's drift within an episode, and a statistic (the raw advantage
  by own label) in which the other five agents' labels and the state are unmodelled noise.
- *Strengthened:* the labels are per-agent, approximately additive, long-horizon policies.
  A label held for ten steps delivers a fifth to a half of what it delivers held for the
  episode (.02–.03 against .06–.09 J implied spread), and the share of commitment reward it
  explains rises from 1.5 % to 16–24 %. Holding labels for 500 steps costs the fixed low level
  nothing (episode J within ±.01 of cap 10 on 3/3).
- *The defect, stated more carefully:* the ranking reaches the coordinator's credit at a
  per-decision signal-to-noise of about 10⁻⁴ (η²), because its advantage is a shared team
  return against a label-free baseline. Against that stands an entropy bonus of .07 on
  standardised advantages. A maximum-entropy learner's stationary law is
  q(c) ∝ exp(A(c) / λ_h); with standardised label advantages of order .01 that is a law within
  ±15 % of uniform — which is the law observed (shares .14–.19, entropy 1.78 of 1.79). The flat
  law is what this signal and this temperature produce, and its argmax is the argmax of
  noise. E2a and E2b were a false dichotomy: the signal is present *and* unusable as credited.
  (Simple-model consistency, order of magnitude only; not a fit.)
- *For the direction's question:* longer commitment raises the per-decision η² by two orders
  of magnitude and the information per rollout (η² × rows) by one to six times, at no
  behavioural cost at fixed weights. That is the first positive evidence in this direction
  that skill duration matters — for the high level's learning signal, not for behaviour.
- *Untouched:* whether the best label is the same through training (one checkpoint); whether a
  low level trained under long commitments keeps six distinct policies; whether any of this
  moves J in a fit.
- *For Codex:* team-conditioned reassignment finds no support here (additive, mildly
  sub-additive, no coordination term); a termination rule would act on a selector whose
  credit is the defect. The pause on frozen-foundation termination training remains my
  recommendation.

**Next research judgment: three fit-level ideas now have a measured basis; I recommend one.**
- *I1, additive label credit (recommended).* Give the coordinator a label value it can learn:
  a per-agent, label-conditioned baseline or an explicit additive label-value estimate
  (the count regression, online) used as the agent-label advantage. Measured basis: finds the
  right best label at cap 10 on 3/3 from 16 rollouts. Prediction: the label law leaves
  uniform within 15 rollouts (entropy below 1.6), the most-used label at the end is among the
  fixed-weight top two on 3/3, late-window J above D1280 by > .03 on at least 2/3.
  Strongest alternative: the ranking drifts during training faster than the estimate tracks
  it, so the law sharpens onto stale labels and J does not move.
- *I2, longer high-level commitment (caps 50–100).* Basis: η² × rows up to sixfold, no
  behavioural cost at fixed weights. Risk: fewer high-level updates per rollout, and the low
  level is retrained under it, which B12 cannot speak to.
- *I3, lower coordinator entropy coefficient.* Cheapest, but it sharpens a law whose argmax is
  currently noise; on its own I expect it to lock in arbitrary labels. Useful only with I1.
- *Not recommended now:* adaptive termination — nothing measured here says *when* matters
  before *which* is learnable.
Before any fit: a prospective entry with arms, blocks, horizon, seeds and planned fits, and an
independent review of the learner change (I1 touches the shared coordinator update).

## 2026-09-20 20:36 PDT — owner decision: I1 goes first; I2 and I3 kept as reserve ideas with their material

**Owner, 2026-09-20:** proceed with the recommended I1; record the material for the other two
options as later alternatives. This entry is that record; it declares no run for I2 or I3.

### Reserve idea I2 — longer high-level commitment
- *What:* train D with both caps above 10 (candidates 50 and 100; `skill_cap_k_max` and
  `team_cap_k_Z`, read once at construction, `agent.py:482-484`; cadence at `agent.py:2596,
  2613`). `config.k` stays 10: it is only the low level's BPTT chunk (`agent.py:6306-6309`).
- *Measured basis (B12, fixed weights):* per-decision η² of the coordinator's own advantage by
  label rises from .0001–.0003 (cap 10) to .001–.003 (50), .002–.009 (100), .019–.033 (500);
  η² × rows per rollout 8 → 48 → 72 → 50, 16 → 19 → 29 → 40, 25 → 28 → 16 → 29 on the three
  blocks; a label's implied all-equal spread .02–.03 J at cap 10, .03–.07 at 50–100, .06–.09
  at 500; episode J within ±.01 of cap 10 at every cap.
- *What B12 cannot say:* the value head off cap 10 is arithmetic (trained on ten-step
  targets); the low level would be retrained under long commitments and may not keep six
  distinct policies (discriminator accuracy is already .25–.30 against .167); coordinator rows
  per rollout fall to 160 (cap 50) or 80 (cap 100) with the same 15 epochs, so
  `coordinator_batch_size` and the entropy balance change meaning; B07's cadence-1 arm needed
  14 GB because its single minibatch held 8,000 rows — the opposite regime, no memory risk
  here.
- *Prediction if run alone:* law still within ±25 % of uniform (the credit is still a shared
  return against a label-free baseline; η² .003–.009 is thirty times better and still small),
  J unchanged within .03. I2 is more promising combined with I1 than alone.
- *Discriminating observation:* label-law entropy by rollout and the fixed-weight label map
  (B09) at the end; cost 3 fits for one cap, 6 for two.

### Reserve idea I3 — lower coordinator entropy coefficient
- *What:* `lambda_h` .07 → smaller (candidates .02, .007) for the coordinator's loss only
  (`agent.py:6200`; constant on this construction, `config_1.py:165`). Check first whether
  the same attribute feeds any low-level term — B03 found the flat learner's action-noise
  inflation came from `lambda_l`, a different coefficient; the two must not be confused.
- *Measured basis:* stationary maximum-entropy law q ∝ exp(A / λ_h); standardised label
  advantages of order .01–.04 (B11) against .07 give shares within ±15 % of uniform, which is
  what is observed (.14–.19).
- *Why not alone:* the per-rollout best label by the coordinator's own advantage changes
  almost every rollout (B11: [1,2,1,3], [5,4,4,2], [3,1,4,2]); a lower temperature sharpens
  onto that noise. Prediction if run alone: entropy falls below 1.6, the most-used label at
  the end is in the fixed-weight top two on at most 1/3, J unchanged or lower, and unused
  labels' policies degrade from lack of exposure.
- *When it becomes useful:* after I1 (or I1 with I2) gives a credit whose ranking is stable
  across rollouts; then the temperature is the knob that converts a stable ranking into
  exploitation. Cost 3 fits per value.

### Also kept from this series (not ideas, facts a later design should reuse)
- Action noise: the state-independent log-std grew to ≈ 2.9 units and costs every label
  .05–.16 J against the mean action (B10); a D-side analogue of B03's flat-learner finding,
  untested as a lever.
- Required comparators for any later arm on this learner: as trained, random every 10, best
  constant label (B08, B09).
- A fixed-weight panel is exact only on the training host; node fast-forwards delete tracked
  run records from the node's sparse checkout (restore before a probe).

## 2026-09-20 20:44 PDT — prospective: additive label credit as an external label bandit, B13 (six fits)

**Idea I1, first form.** Test the claim "if label selection is learned from additive
per-agent credit, D's score rises" in the most direct way, without editing the shared
learner: the coordinator's agent labels are replaced, in training, by draws from a
context-free law driven by the count regression B12 validated, and deployment executes the
estimated best label. B09 found state-dependent selection worth ≤ .025 at these checkpoints,
so a context-free law loses little. If this works, the in-learner form (additive credit
inside the coordinator's advantage) is the follow-up; if not, it is not worth building.

**Code facts this rests on (read-only map, file:line in the scout's return; I checked the
call order).** With an instance wrapper on the learner's `_batched_assign_skills` that
rewrites the returned labels and writes them back (B08's pattern), the low-level actor and
critic, the intrinsic reward and both discriminators all train on the *executed* labels
(`agent.py:3266-3294, 4042-4127, 6353-6455`). The coordinator's D2 rows would mix executed
labels with the sampled labels' log-probs (`agent.py:2321-2343`) — an invalid PPO ratio that
nothing asserts against — so the coordinator's update is switched off with the existing
`disable_high_level_training` (`agent.py:7182-7190`); its network then never reaches the
environment except through the team label, which never reaches the actor. Infinite
interruption costs are required, as in B08.

**Object `FSD_LABEL_BANDIT_B13`.** D1280 construction; declared config difference
`disable_high_level_training = True` only. Training seeds = block seeds 772803, 772903,
773003 (the D1280 fits' own initial weights and worlds), 45 rollouts, panels at 5…45, final
weights saved. Two arms, three blocks, **six fits planned**, two waves of three on
`wsl_4070` (≈ 2.9 GB and ≈ 2.3 h per fit). The batch is not extended after scores.
- *Estimator (both arms).* After each rollout: least squares of each ten-step commitment's
  undiscounted mean team reward on the six agent-label counts with position fixed effects
  (B12's estimator, 800 commitments), centred coefficients β_r with lane-clustered variances;
  β̂ ← .8 β̂ + .2 β_r (first rollout: β̂ = β_1), variances combined with the same weights;
  z_c = β̂_c / ŝe_c.
- *Arm `BANDIT`.* At every agent decision the label is drawn from
  q = .7 · softmax(z) + .3 · uniform (rollout 1: uniform), by a dedicated generator
  seeded from (training seed, arm). The .3 floor keeps every label's policy and the
  discriminators trained. Constants are declared here and not tuned.
- *Arm `UNIFORM`.* q uniform throughout; the estimator runs passively. This separates
  learning the ranking from concentrating exposure on it, and is the coordinator-off control.
- *Evaluation at every panel boundary, same 32 worlds:* `best_estimate` (every agent executes
  argmax β̂, B09's constant rule) and `uniform_every_10` (B08's rule) as the selection-free
  reference on the same weights; at rollout 45 also the six constant-label panels (the arm's
  own label → J map). Recorded per rollout: β̂, z, q, label shares, discriminator accuracy,
  action std.
- *References (published, not rerun):* D1280 as trained, J45 .456 / .355 / .499, late window
  (30–45) .432 / .395 / .452; B09's best constant label on D1280's weights .454 / .521 / .519.

**Predictions (held loosely).**
- P1 `BANDIT`'s law leaves uniform: largest label share above .4 by rollout 15 on 3/3.
- P2 at rollout 45 argmax β̂ is among the top two labels of the arm's own map, 3/3, both arms.
- P3 `BANDIT` `best_estimate` J45 exceeds D1280 as trained by ≥ .03 on at least 2/3, mean
  over blocks ≥ +.05; late window likewise ≥ +.03 in the mean.
- P4 `BANDIT` minus `UNIFORM` on `best_estimate` J45 within ±.03 on at least 2/3 — I do not
  know whether concentrated exposure helps the deployed policy or starves the others.
- *Strongest alternative:* the ranking drifts faster than a five-rollout average follows, or
  the ten-step response ranks labels myopically (B12: label 3 over label 2 on 772803 at cap
  10): the most-favoured label changes three or more times after rollout 15 and
  `best_estimate` is no better than `uniform_every_10`.
- *What each outcome changes.* P2 and P3 hold in both arms, arms equal → the gain is learnable
  selection itself; the in-learner credit is justified and cheap to specify. `BANDIT` above
  `UNIFORM` → exposure is a second lever. P2 fails → the ten-step response is the wrong
  credit and I2 (longer commitment) moves ahead of the in-learner form. P3 fails with P2
  holding → selection was not what limited D, and the explanation returns to the low level.
- *Limits known now:* three blocks that have carried every setting since B01; no size claim;
  one new learner-side mechanism and one switched-off component at once, which `UNIFORM`
  separates only partly; panels with sampled worlds have ≈ .03 J conditional noise.

## 2026-09-20 21:59 PDT — B13 entry code written, amended, independently reviewed and accepted; no score exists

`scripts/run_fsd_label_bandit_b13.py`, `experiments/.../label_bandit_b13/launch_fit.sh` and
tests under `tests/.../label_bandit_b13/` (Implementer; one amendment and the review fixes
are mine). New files only.

**Amendment to the 20:44 specification, made before any score.** One rollout has 16 lane
clusters against 55 design columns, so its clustered variance has rank at most 16 and can only
understate; z would be inflated and the law would sharpen on noise. The denominator of z is
now sqrt(max(var̂, empirical)), where var̂ is the declared .64 / .04 combination and
`empirical` is the stationary variance of β̂ implied by the rollout-to-rollout innovations
d_r = β_r − β̂_{r−1}: innovation ← .8 · innovation + .2 · mean_c d_r[c]² (first innovation: its
own value), g = .2 / 1.8, empirical = innovation · g / (1 + g), one number pooled over the six
labels. It can only lower |z|. Nothing else of the specification changes. The published
`estimate` carries `standard_error`, `innovation` and `empirical_variance`, and the summary
carries this text, so z is reproducible from the record.

**What the code established (file:line in the summary's source notes).**
`disable_high_level_training` switches off the coordinator's update, its value normaliser's
update and the rollout-end flush — the last harmless here because every lane is terminal at
every rollout end, and the fit refuses a rollout without its 800 closed team rows; D2 storage
is not gated by it. `rows_M*` in `d2_metrics` are flush-only counters and read 0 on this
object. The estimator runs inside a wrapper on the learner's `update`, after the frozen update
and before `clear_buffers`; the law in force during rollout r is the estimate at the end of
r − 1. The raw per-step team reward comes from an environment-side tape whose discounted sums
must reproduce the buffer's segment rewards (1e-5) every rollout. Each boundary's panels are
genuine frozen `evaluate_panel` calls; they run inside the frozen RNG-preserving context, and
a test shows the extra panels leave every training row unchanged.

**Independent review (hmasd-reviewer, read-only): ACCEPT WITH FIXES, no blocker.** Ten
invariants checked against `hmasd/agent.py`; all hold, with the note that `bind()` leaves
B01's identity globals rebound, as B07 and B08 do. Fixed before acceptance: the amendment is
now in this notebook and in the published record (was only in a docstring); a frozen fit that
returns complete with no summary or learner seen is a failure, not a silent success; weights
are written under a pending name, digested, renamed, then given their sidecar; `reduce`
refuses a missing launch sha; the `rows_M*` note; a docstring that claimed a comparison
`reduce` does not make. Review limits: nothing at production geometry has run; the
800-commitment, 55-column regime is first exercised by the fits themselves.

**Kept as declared, to be stated with the reading:** the two arms draw labels from different
dedicated streams (seeded by training seed and arm), so they differ by trajectory noise from
the first step as well as by the law. A B13 checkpoint carries `disable_high_level_training`
and coordinator rows with mismatched labels and log-probs: nothing may train a coordinator
from it. Checks: 39 B13 tests passed (81 with B08), mine, after the fixes; the Implementer's
run with B07, B08, B09 and B12 gave 190 passed before them. Projected ≈ 8,000 s and ≈ 3.0 GB
per fit; two waves of three.

## 2026-09-20 22:01 PDT — B13 first launch refused by the admission kernel before any spawn; one-line fix

At `c3a4966c3` the three `BANDIT` launches were refused: "runner must contain exactly one
require_admission(__file__, direction='flexible_skill_duration') call". The runner passed the
direction through a module constant; the kernel's static check wants the literal. No process,
output root or admission record was created. Fixed by writing the literal (no behaviour
change); the fits launch from the next published sha. Control revision adopted at this
boundary: main's constitution amendment of 2026-09-20 (DMs publish their own RESEARCH entry
to main; proactive Pro consultation at four decision points). The working explanation of this
direction changed materially between B08 and B12, so a Pro consultation on that explanation
and on what B13 can and cannot show is due; I send it while the fits run, because the fits are
the owner's decision and the advice can change their reading and the follow-up, not whether
this evidence is worth collecting.

## 2026-09-20 22:10 PDT — B13 wave 1 admitted on `wsl_4070` (three `BANDIT` fits)

Launch sha `91e344eecc9603f64f2e8c0504b92117fc35d5df`, through
`experiments/candidates/flexible_skill_duration/label_bandit_b13/launch_fit.sh` and the
admission kernel, about 22:03 PDT. Tags and operation claim keys:
`b13_bandit_772803_a01` `82a774c8cd241eb24d0c5af93ddb4dbbaa8d721e14dd69b4f652102f18c4274f`;
`b13_bandit_772903_a01` `4fe063a29e9f4913f89712a80b3ad357a8d218999e869aa5081940a623fb663b`;
`b13_bandit_773003_a01` `367ba0526f32753155d22e96ee32aff3ef219b81f426700976692e3b0f5f6f57`.
Technical observation only (no score read): after two rollouts the estimator record on 772803
is finite and the law has left uniform (largest q ≈ .41). Wave 2 (three `UNIFORM` fits)
launches at the same sha when these exit; the batch stays six fits.

## Pro question 2026-09-20 coordinator-signal-explanation-and-b13-scope
Conversation: new (WSL Jev route; the address stays in the local operation file, named here by question key)
Question: Between B08 and B12 the DM replaced its explanation of why the hierarchical learner (D1280) gains nothing from its coordinator's label selection. The new explanation: the six labels are six materially different low-level policies whose effect on the score is per-agent and roughly additive, but the coordinator's own per-decision advantage carries almost none of that ranking (η² ≈ 1e-4 by agent label, smaller than a placebo grouping's spread), because it is a shared ten-step team return against a label-free baseline, while an entropy bonus of .07 holds the law near uniform; longer commitment raises the per-decision signal about a hundredfold at no behavioural cost at fixed weights. Is that explanation supported by the recorded quantities, what simpler or contrary account do they leave open, and, given it, what can the running B13 batch show and not show, and which follow-up (in-learner additive label credit, longer high-level commitment, lower coordinator entropy, or none) is best justified under each B13 outcome? The answer can change how the DM reads B13, which follow-up it proposes to the owner, and whether it keeps advising Codex to pause team-conditioned termination training. It does not change B13's declared arms, seeds or size (six fits, owner-approved, running), and it is advice, not approval.
Standing:
  Earlier Pro advice and why it is not reused: "Pro question 2026-09-19 b01-after-stage0-next-step" and "Pro question 2026-09-19 flat-learner-stands-still-critic" in this notebook concern the flat comparator CF against D. Neither covers the coordinator's label selection inside D, and all evidence below is newer. Their cautions that carry over: displacement and near-zero surrogates are weak diagnostics; per-minibatch advantage standardisation makes the policy loss zero at the old policy; every setting since B01 has been tried on the same three blocks (772803, 772903, 773003), so no size is claimed.
  Observations (completed, committed; J = 6 × U / 500, 32 fixed evaluation worlds per block, replicate noise .003–.006, sampled-world conditional noise ≈ .03).
  B07: redrawing every agent's label every step during training changed neither behaviour nor J on the one block that completed (two cells lost to the node's memory killer; closed without extension).
  B08 (three exact D1280 reruns with weights saved, bit-identical panels, then zero-fit probes on the fit host): J as trained .456 / .355 / .499; uniform random labels every 10 steps .434 / .421 / .474; random every step .422 / .420 / .475; one label frozen per agent per episode .439 / .343 / .506. The label moves the mean action by .19–.23 of the action std.
  B09 (one constant label for all agents, whole episode, mean actions): per-label J spans .326–.454, .305–.521, .393–.519. On 772903 the coordinator uses label 1 on 0.09 % of decisions although label 1 is best in 32 of 32 worlds (.521 against .355 as trained). State-dependent selection over the best constant label is worth ≤ .025.
  B10 (same map under the training action noise): every label loses .05–.16 J, the spread shrinks to .080 / .133 / .073 from .129 / .216 / .127, rank correlation with the mean-action map ≈ .79. The DM's alternative E1 (the gap vanishes under training noise) was rejected.
  B11 (the coordinator's own advantages recomputed exactly as its update computes them, no update): spread of the mean standardised advantage by agent label .024 / .019 / .021 against .068 / .058 / .067 for a placebo grouping by team label; η² by agent label .0003–.0004. The DM's pre-declared criterion was met by the letter and withdrawn as miscalibrated (the range of six noisy means is positive under no effect); the placebo is the calibration.
  B12 (commitment cap varied at fixed weights, zero fits; regression of each commitment's mean team reward on the six agent-label counts with position fixed effects, lane clusters): permutation p = .001 at every cap on 3/3, no placebo passes; implied all-equal spread in J .032 / .019 / .033 at cap 10 rising to .090 / .094 / .064 at cap 500; additive predictions reproduce the B10 map, the Σn² homogeneity coefficient is slightly negative; advantage η² rises from .0001–.0003 at cap 10 to .019–.033 at cap 500; episode J stays within ±.01 across caps. The DM's 17:31 statement that the label's consequence is "averaged away" was withdrawn: the ranking is in the reward at every cap, the coordinator's estimator does not extract it.
  Code map (16:50 entry): coordinator segment reward = γ-discounted sum of the raw team reward, no intrinsic term; GAE per (lane, team) and per (lane, agent) with γ^elapsed, λ .95; team critic V(s), one linear head per agent on its own observation, both label-free; advantages standardised per minibatch with one shared mean and std; 800 team rows and 4,800 agent rows per rollout, 15 PPO steps of one 800-row minibatch, lr 1e-4, clip .2, entropy coefficient `lambda_h` .07 constant.
  The DM's inference the question tests: with a maximum-entropy law q ∝ exp(A/λ) and per-label standardised advantage differences of ≈ .02, the law stays within about ±15 % of uniform relative weight and its argmax is set by noise and early drift, which matches the observed laws (64 % / 26 %, 65 % / 0.09 %, 37 % / 34 %) only if something else concentrates them; the DM has not explained the concentration. This is a known gap.
  Contrary or limiting evidence kept in view: fixed-weight maps are not what a learning coordinator faces (the low level co-adapts, the map may drift; B13's alternative prediction covers this); the B09 best constant label is a maximum of six on the evaluation worlds and is optimistic as a reference; small η² with 4,800 rows × 45 rollouts may still be learnable, so "absent per decision" is not "unlearnable"; B07 has one block; the low level's FiLM conditioning, discriminators and intrinsic reward (weights .025 and .01, low level only) were not varied; D128 and D1280 did not differ (B02).
  B13 (prospective entry 20:44, acceptance and amendment 21:59, launch 22:01 and 22:10): coordinator update off; agent labels drawn from q = .7 softmax(z) + .3 uniform, z from an exponentially averaged per-rollout count regression (`BANDIT`), or uniform with the estimator passive (`UNIFORM`); deployment executes argmax β̂ for every agent; comparators are D1280 as trained (published, not rerun), `uniform_every_10` on the same weights, and the arm's own six constant-label panels at rollout 45. Predictions P1–P4 and the strongest alternative are in the 20:44 entry. Known limits: arms draw labels from different random streams; one mechanism added and one component removed at once; the z denominator was amended before any score because the per-rollout clustered variance is rank-deficient (16 lanes, 55 columns).
Context:
  Governance: `docs/project/OPERATING_CONSTITUTION.md` sections 1, 3, 5, 7, 8 (source_sha); the 2026-09-20 amendment makes this consultation the DM's duty at a changed failure explanation. `docs/research/RESEARCH.md` pause line and the `flexible_skill_duration` row (source_sha): FSD is active, led by the Claude session; the owner removed the per-idea fit allowance on 2026-09-20 (arms, horizon, seeds and planned fits are still declared before running; a batch is never extended after its scores; a failed idea is not renamed). Owner division of 2026-09-20: this direction owns what a sustained skill is and how it affects behaviour and learning; the Codex direction owns when a team continues, ends or regroups commitments; the owner asked that flat tuning, k sweeps and added ablations not be the default.
  Method: `.agents/skills/hmasd-scientific-tools/SKILL.md` sections "Update the working explanation", "Simple-model and literature bridges", "Comparators and MARL information", "Statistics", "Cost and exposure" (source_sha).
  Evidence, this notebook (source_sha), entries of 2026-09-20: "05:30 PDT — persistence B07 read", "08:41 PDT — label content B08 read", "16:03 PDT — label map B09 read", "16:40 PDT — B10 read", "16:50 PDT — how the coordinator's signal is built", "17:31 PDT — B11 read", "20:19 PDT — B12 read", "20:36 PDT — owner decision: I1 goes first; I2 and I3 kept as reserve ideas", "20:44 PDT — prospective: additive label credit as an external label bandit, B13", "21:59 PDT — B13 entry code written, amended, independently reviewed and accepted".
  Raw outputs (source_sha): `runs/flexible_skill_duration/b08_reduce/summary.json`, `b09_reduce/summary.json`, `b10_reduce/summary.json`, `b11_reduce/summary.json`, `b12_reduce/summary.json`, `b07_reduce/summary.json`, and the D1280 references `runs/flexible_skill_duration/b01_s1_d1280_772803_a01/summary.json` (likewise 772903, 773003).
  Code, actual learning path (source_sha): `hmasd/agent.py` near lines 2321–2355 (D2 row storage and segment reward), 6153–6164 (advantage standardisation), 7182–7190 (`disable_high_level_training`), 4444–4446 (low-level intrinsic weights); `hmasd/utils.py` 1018–1142 (coordinator GAE); `hmasd/networks.py` 734–735, 1210–1213 (label-free critics), 1072, 1099 (label choice); `configs/config_1.py` line 165 (`lambda_h`); `scripts/run_fsd_coordinator_signal_b11.py` `collect_training_law`; `scripts/run_fsd_commitment_visibility_b12.py` `label_regression`; `scripts/run_fsd_label_bandit_b13.py` `LabelEstimator` and `SOURCE_NOTES`.
  Primary sources, only if the bridge needs them: counterfactual and difference-reward credit for a shared team reward (Foerster et al. 2018, COMA; Wolpert and Tumer's difference rewards), SMDP option-value learning (Sutton, Precup and Singh 1999), and the softmax form of an entropy-regularised policy. Cite the passage used; do not reconstruct project rules from historical specifications.
Prospective cost: B13 is six fits, ≈ 2.3 h each in two waves of three on one node, decided and running; nothing in this question adds to it. The follow-ups the answer can reorder: in-learner additive label credit — a change to the shared learner's coordinator advantage (Implementer task plus independent review, the dominant non-fit cost) and about six fits (two arms, three blocks); longer high-level commitment (caps 50 or 100) — about six fits, configuration-level, with a memory risk on the 16 GB node; lower coordinator entropy (`lambda_h` .02 or .007) — about six fits, configuration-level, judged useful only once a stable ranking exists. Zero-fit probes at fixed weights cost ≈ 10–30 min each on the fit host.
Constraints: seeds and matched baseline per constitution section 8; no training, no edits
  outside the empty "### Answer" subsection; write only there on branch claude/fsd-pro-critic.
  Read the question at the pinned source, but fetch the latest target file before editing
  and use its actual blob SHA. Preserve all other bytes; stop on overlapping edits.
  On successful write, report the actual commit. On write failure return the complete
  answer in chat, not just a SHA, status message or link.
Return: (1) For the explanation above: what B07–B12 strengthen, weaken and leave unresolved, naming any quantity the DM misreads — in particular whether η² of the standardised advantage by label is the right measure of what 15 PPO steps on 4,800 rows can learn, whether the entropy argument is quantitatively right for this loss (standardised advantages, clip .2, coefficient .07, six labels), and what would explain the concentrated yet valueless laws actually observed. (2) The strongest simpler or contrary account the code or the recorded outputs can confirm or exclude at zero fits, with the file and quantity to look at. (3) For B13 as declared: which conclusions each outcome pattern of P1–P4 licenses and which it does not, given the comparators, the switched-off coordinator, the different label streams and the optimism of a best-of-six reference; any reading rule the DM should fix before scores exist (it will be recorded as adopted or rejected before the reduce is run, never applied after). (4) A simple-model bridge if one helps: a bandit or SMDP prototype for label credit under a shared additive reward, with its assumptions and the MARL coupling it omits (low-level co-adaptation, non-stationary map, discriminator pressure). (5) The follow-up best justified under each B13 outcome, with a predicted intermediate change, a native consequence, and fit and non-fit cost; "none" is a legitimate answer. (6) Whether the recorded evidence supports the DM's advice that team-conditioned termination or reassignment has no support on this learner yet. End with MATERIAL_DISSENT yes/no.
### Answer

*Saved from chat by the DM (2026-09-20): Pro read the repository at the pinned sha through the GitHub connector but did not complete the write (its interface required a whole-file replacement it could not verify); `deliver` returned NOT_DELIVERED with no commit on `claude/fsd-pro-critic` and the question unchanged. Chat text sha256 `45493b976d0f07e4f3fa6a2906ce97828584da78d75234df24a2cbe227604957` (13,970 characters). Wording unchanged; the displayed and inline formulas, which the chat rendered one symbol per line, are re-typeset on one line each, the tab-separated tables are set as Markdown tables, section titles are set as headings or bold, and a source chip the chat showed after the COMA sentence is kept as a parenthesis.*

GitHub 读取成功，但本次未完成写回，没有生成 commit。 最后刷新时，claude/fsd-pro-critic 上目标文件的 blob SHA 仍是 b587ed9e23e89a305886ea1508a8789192a109a7，指定 ### Answer 仍为空。当前写入接口要求整文件替换，而连接器返回的长文件未能通过 files.materialize 落盘以校验其余字节；我没有执行无法可靠保证保留原文的覆盖。这不是已经确认的权限拒绝。以下提供完整答复。

依据版本： d279082068380b497abf76b412ea0c11b2a519eb。以下仓库路径、数量和代码判断均指该固定版本；最新分支只用于检查写入位置，没有用于替换研究输入。B13 后来的结果没有作为输入。本答复没有启动训练或探测，没有修改 B13 的批次，也没有代替 DM 作出批准决定。题面将本次咨询限定为解释、读法与后续建议，并保留现有种子、比较器和批次约束。

总判断：标签具有任务相关的行为内容、十步数据中存在可提取的标签差异，这两点得到加强；“现有信用不可学习”“熵已经被确认为失败原因”“长承诺没有成本”“近似加性排除了 team-conditioned 决策价值”，则超出了证据。 B13 可以检验一个外部选择与训练暴露方案是否有效，但不是自动裁决 I1、I2、I3 的机制实验。尤其需要在看分前撤回两条过强的解释规则：P2 失败不直接推出 I2；P2 成功而 P3 失败也不直接否定选择瓶颈。

#### （1）B07–B12 加强、削弱和留下了什么
**证据链的有效部分**

| 研究 | 得到支持的结论 | 不能随之推出的结论 |
| --- | --- | --- |
| B07 | 唯一可用的同块 J 比较，没有显示训练时 cap 10 优于 cap 1：晚窗约 .4517 对 .4565。 | 不是三块等价性结果。行为捕获实际上比较了不同块的 D_K10 与 D_K1；没有任何一块同时完成两个新臂。不能把“未看到自相关差异”当作标签无内容。 |
| B08 | 固定输入下标签改变动作均值；RMS 差异为动作标准差的 .19–.23。改变执行规则也改变 J。 | 不能由跨块平均收益接近零，推出每块的选择都无价值。更不能把高动作噪声下近零自相关解释成标签不起作用。 |
| B09 | 至少在 772903，存在很大的常量标签选择机会：.521 对原部署 .355。 | 每个 world 从六个“全员同标签、整回合持有”的策略中选最优，只是一个受限策略类的 oracle；不是一般状态依赖、逐 agent、回合内重分配的价值上界。 |
| B10 | “标签差异在训练动作噪声下消失”受到直接反证：跨度仍约 .080/.133/.073。 | 这些仍是固定权重、全员同标签、长持有的面板，不等于真实训练中十步混合分配的价值函数。 |
| B11 | 当前信用的边际标签统计弱、逐 rollout 排名不稳定，是合理的学习困难线索。 | 小 η²、较大的所谓 placebo 跨度，都不能证明真实 PPO 梯度不含可学习信号。 |
| B12 | 十步计数数据已经能提取与固定权重标签表现有关的结构；部分长 cap 的区分度更强。 | 不是长期训练收益实验，也没有证明所有交互可以忽略，更没有证明百倍 η² 等于百倍学习效率。 |

B07 的不完整性、未配对行为比较，以及 B08 对先前自相关解释的修正，都已在笔记自身记载；不应在新的解释中再次压缩成“重抽标签改变不了行为”。 B09–B12 的相应范围和限制见固定问题、原始 B10 输出及 B12 汇总。

还应收窄“六个 materially different policies”的措辞：证据支持这个标签条件化策略族中存在实质差异，并不证明六个标签彼此都实质不同，也不证明这种区分贯穿训练。例如 B09 的 773003 中标签 0 与 5 的差别很小。

**第一处数量误读：.024/.019/.021 不是标准化优势跨度**

B11 原始汇总的 quantity 明确说统计的是 mean raw advantage；.0238115… 对应字段也是 agent_label_spread。固定问题把这组数称作“mean standardised advantage”的跨度，是实质性的单位误写。

以 772803 为例，由已记录的 `mean_standardised_advantage_indicator_c / share_c` 直接相除，可得标准化优势的六个条件均值约为

(.01345, .00774, .02198, .04051, −.01301, −.01883),

跨度约 .05934，而不是 .02381。这是对已记录数量的算术换算，不是新的梯度测量。B11 的 policy_gradient 还明确标为 score_function_with_shares_as_q：它把边际执行份额当成条件概率，不能替代实际网络梯度。

**第二处误读：η² 不是 PPO 梯度的信噪比**

这里的 η² 衡量的是标签分组均值解释了多少优势方差。真实策略更新涉及的却是

`g = E[ ∇_θ log q_θ(C_i | x, 解码前缀) · A_i ]`.

边际分组忽略了状态、agent 身份、自回归前缀和网络 Jacobian。不同上下文的有效梯度可能在边际标签均值中抵消；反过来，边际标签均值也可能包含状态选择造成的差异。因此，η² 小是诊断线索，不是“梯度不可用”的判决量。B11 的统计实现和实际 PPO 路径支持这一测量对象的区分。

“4,800 rows × 15 steps × 45 rollouts”同样不能直接作为独立样本量。每个 rollout 的 4,800 agent rows 来自 800 个共同 team 决策，六个 agent 共享环境回报，且位于 16 条 lane 的连续轨迹中；15 个 PPO epoch 反复使用同一批数据，不产生 15 倍新证据。另一方面，也不能由这些依赖关系反推“有效样本只有一个”或“肯定学不会”。跨 rollout 的策略族还在变化，不能把 45 批当作同一个静态标签模型的独立重复。

**第三处误读：实际 loss 的熵比例不是简单的 .07**

agent.py 的 agent policy loss 除以有效 agent 总数，而 entropy 先对同一 team row 的 agent 熵求和，再除以 team batch size。对于这里六个 agent 同时有效的构造，忽略共享参数、team 分支、value loss 和 clipping，agent 部分的局部 bandit 类比是

`max_{q_i}  (1/6) Σ_i E_{q_i}[A_i] + λ_h Σ_i H(q_i)`.

对应的独立分布解是

`q_i(c) ∝ exp( a_i(c) / (6 λ_h) )`,

即这个类比下的有效温度约为 .42，不是 .07。这里的六倍来自六个 agent 的 sum/mean 不一致，不是“类别数是六”本身。

数量上，优势差 .02 在温度 .42 下的最大最小概率比约为 1.049；用 .07 则为 1.331。用上面 772803 的实际标准化边际跨度 .05934，前一个比值约为 1.152。这些只能说明“近均匀分布与当前量级相容”，不能证明真实网络达到这一平衡，也不能把最大最小概率比直接写成相对均匀的 ±15%。

还有三点影响解释：

熵梯度在严格均匀分布处为零，不是一个恒定大小 .07 的力压住任何小信号。

在旧参数处 ratio 为 1，.2 clipping 尚未截断该点的局部策略梯度；后续 epoch 的情况必须另读。

共享 encoder 同时接收 policy、entropy 和 value 梯度；局部 bandit 公式不是整个神经网络的收敛证明。

甚至 Standing 中沿用的“标准化使旧策略处 policy loss 必为零”，在这个具体实现上也不应照搬：共同标准化保证的是

`Ā_team + 6 Ā_agent = 0`,

而代码把两个分别求平均的 policy loss 相加，旧策略处的标量是 `−Ā_team − Ā_agent`，不必为零。无论它是否接近零，都不能据此判断梯度是否有效。

**第四处误读：“近均匀却集中”的缺口其实已经有代码答案**

训练时的采样概率与部署时的 argmax 使用频率不是同一个量。

networks.py 在 deterministic=False 时采样，在 True 时取 argmax。即使每个状态上的概率都很接近均匀，一个很小但方向稳定的 logit 偏好，也可以让同一标签几乎总是被 argmax 选中。因而训练份额 .14–.19、熵接近 ln 6，与部署中 64%、65% 等集中使用率完全相容，不需要额外的“概率集中机制”。08:41 的 B08 笔记本来已经明确指出这一点。

但这只解释集中，尚未证明那些微小偏好全部是噪声。它们也可能包含训练目标与部署目标不一致、状态依赖偏好、critic/encoder 耦合或早期路径依赖。应把“argmax of noise”降为待检验解释，而不是由高熵直接推出的事实。

**第五处误读：team label 不是这里有效的零效应 placebo**

B11 的说明从“team label 不直接进入低层 actor”，推出“固定权重时不能改变执行动作，因此其分组结构全是状态造成的”。这个推论漏掉了路径：

`Z ⟶ q(C_1, …, C_6 | s, Z) ⟶ 低层动作 ⟶ R`.

SkillDecoder.forward 确实把 team_skill_embedding(Z) 放入解码序列，之后的 agent-label 分布依赖它。固定权重并不会切断这条路径。只有当 agent labels 被外部固定、覆盖时，才能用“不直接进入 actor”排除这条行为影响。B11 的原生采样收集没有这一条件。

因此，较大的 team-label 跨度不能作为 agent-label 效应无效的校准证据；B12 中“不通过该 placebo”也不能补上这个因果论证。另一个较小但相关的措辞问题是：agent value head 读取经过中央 encoder 的 observation token，并非未经交互的“只看自己原始 observation”的简单线性 baseline。

**B12 的积极结果应保留，但须改写其强度**

B12 的 r_squared 是标签计数与位置固定效应共同模型的 R²，不是标签单独解释的方差。将 .015→.24 直接说成“标签解释的回报比例”不准确；应另比较位置-only 模型或报告增量解释量。其置换将完整计数向量在相同 position 内重排，保留了同一时刻的组成，但不保留状态与历史条件。原生 coordinator 又是状态依赖、自回归的。因此这些 p 值是在所设置换模型下的强关联证据，不等于已经排除了状态混杂的随机化因果检验。

“加性预测复现 B10 地图”也过强。772903 的标签 0，预测约 .348，B10 实测约 .236，差约 .112。这不自动证明非加性，因为收集与评估 worlds 不同；但足以说明绝对地图并未复现。一个略负的 `Σ_c n_c²` 系数，只削弱“全员同标签才有收益”这一特定解释，不能排除身份相关、标签对相关或状态相关的协作效应。

η² × rows 还有单位问题。 cap 10 每 rollout 有 4,800 agent rows；cap 500 只有 96。结合笔记列出的 η²，单 rollout 的乘积量级应分别约为 .5–1.6、1.8–3.2，而不是 8–25、29–50。后者与 16 个 rollout 池化后的行数相容。应核对原始 probe 的该字段；不能把它继续称作“每 rollout 信息量”。即使单位改正，`n η²` 也只是启发式，不是考虑了聚类、参数化和目标变化的有效信息量。这里我完成的是量纲核对，没有重算未读取的逐行优势数组。

最后，实际 GAE 是

`δ_j = R_j^(γ,k) + γ^{k_j} V_{j+1} − V_j`,  `A_j = δ_j + γ^{k_j} λ A_{j+1}`.

十步是决策间隔，不是信用的硬截断。 改 cap 同时改变承诺、样本数、GAE 的物理时间尺度，并把固定 critic 用到非训练 cap 上。“百倍每决策 η²”可以保留为特定固定权重统计的变化，不能改写成百倍可学习性；“episode J 在 ±.01 内”也只是这些条件下的点估计，不是训练无成本或行为等价证明。

#### （2）最强的更简单或相反解释，以及零 fit 的区分方法

我认为最值得优先检验的是：

当前 learner 可能在学习一个近均匀、强正则化的随机训练策略；部署却把它的微小偏好用 argmax 放大。与此同时，B09 的长持有常量标签地图，与 coordinator 真正优化的随机动作、原生续接策略下的 SMDP 价值并不是同一个被估计对象。失败可能首先是训练—部署及目标错位，而不是“十步回报没有可学信用”。

其中“argmax 放大近均匀偏好”已经由代码和 B08 记录确认；“真实梯度是否稳定、是否被正则化抵消、是否优化了不同排序”仍未确认。原始 coordinator 有跨 segment 的 GAE，而 B13 回归的是十步段的未折扣平均即时回报，这也是需要保持的目标区别。

最有区分力的零-fit 检查不是再看 loss 标量，而是：

| 检查 | 文件与数量 | 什么结果会改变解释 |
| --- | --- | --- |
| 区分概率与 argmax | B11 label_law、B09 部署 histogram；networks.py 的选择分支和实际条件 logits | 已足以排除“训练概率必须集中才能产生集中部署”的说法。完整条件 q 可进一步区分稳定微偏好与边际平均掩盖的状态结构。 |
| 真实局部梯度分解 | agent.py:6115–6210 的原 loss；B11 collector 的实际输入、顺序、mask、优势；分别读 policy、entropy、value 对标签对比方向的投影 | 若正确排序方向跨 lane/rollout 稳定，却主要被 entropy/共享梯度抵消，I3 的优先级上升；若方向本身不稳定或不对应正确的续接价值，不能只降温度。 |
| 匹配被估计对象 | 用 B11/B12 的 collector 和同一 checkpoint，比较同一前缀下标签改变对“原生续接回报”与“整回合固定标签回报”的排序 | 若二者稳定不同，就不能拿 B09 排名直接判定原 PPO 信用错误；若原生续接也存在稳定机会而真实梯度提不出来，才加强信用改造解释。 |

这些是建议，不是已执行的结果。真实梯度检查需要条件概率及上下文，不能从 chosen log-prob 和边际份额补造；若上下文未保留，只能在 fit host 做新的只前向收集，再进行不含 optimizer step、normalizer 更新的计算。它也只能在固定参数处检查局部梯度，不能假装重放了 15 次实际 PPO 更新。题面给出的零-fit 探测成本约为每项 10–30 分钟，应计入成本，不应自动全做。

#### （3）B13 的结果究竟许可什么；看分前应固定什么读法
**先限定 B13 识别的对象**

B13 的主比较是 coordinator update 关闭条件下，外部自适应标签分布与外部均匀分布的训练方案比较。它不是原 D1280 的信用头单因素替换。关闭的还包括 coordinator value 更新；低层和判别器继续训练，team label 仍参与这些路径。两臂标签 RNG 不同，因此即使第一轮都均匀，轨迹也不相同。历史 D1280 是重要参照，但不是这个批次的同时重跑控制。

也不应反过来把 BANDIT 的回归一概称为“非随机化、因此有选择偏倚”：它在给定 rollout 历史后，以不依赖当前状态的同一个 q 独立抽取 agent labels。非均匀不等于非随机化。 其主要问题是覆盖度、有限样本、模型误设、跨 rollout 非平稳，以及短期回报不等于长期部署价值；不是仅仅因为 q 集中了就失去当前段的随机分配性质。

**P1–P4 必须按原定义报告**

| 指标 | 成功许可的结论 | 不许可的结论 |
| --- | --- | --- |
| P1：15 rollout 内最大执行份额 > .4，三块 | 外部训练暴露机制确实离开了均匀。 | 不证明标签选对、信用估计正确或 J 提升。失败也不否定被动估计加部署选择的价值。 |
| P2：最终估计标签位于本臂六标签地图 top two，两臂各三块 | 最终估计与该臂当时的常量策略地图有一定一致性。 | 不证明整段训练都选对；也不证明学会了原 D1280 的排序。集中暴露可能把被偏爱的标签训练成最后的赢家。 |
| P3：BANDIT 对历史 D 的最终及晚窗增益达阈值 | 整个方案在这些重复使用的开发块上取得宣告的 native 改善。 | 不独立识别 additive credit、coordinator-off、暴露变化或低层共同适应的贡献。 |
| P4：两臂最终 best_estimate 差在 ±.03 内，至少两块 | 达到了预先给定的描述性接近规则。 | 不是统计等价性结论；两臂一起很差也能满足它。 |

P3 原文只对 BANDIT 定义。“P3 在两臂都成立”不应被当成已经定义好的原始预测；UNIFORM 对历史 D 的同类比较可以明确列为辅助结果，不能悄悄改写原预测。

**最重要的预先读法：把选择收益与训练方案收益拆开**

建议 DM 在首次 reduce 前记录采用或拒绝以下辅助读法，不改变 P1–P4，也不增加面板或 fits。

对每臂 a 的最终权重，定义：

`E_a = J(best_estimate)`,  `R_a = J(uniform_every_10)`,  `C_a = (1/6) Σ_{c=0}^{5} J(constant_c)`,  `M_a = max_c J(constant_c)`.

读三个不同的差：

- `E_a − R_a`：固定权重上的部署规则收益。 它包含“选哪个标签”及“整回合持有，而非每十步独立重抽”的共同变化，不是纯标签选择效应。

- `E_a − C_a`：同一常量策略类内的选择收益。 `C_a` 是“每回合均匀抽一个全员常量标签”的期望分数。它与 `E_a` 的承诺方式一致，更适合回答“估计器是否在六个常量策略中选出了有用的一个”。这完全利用已宣告的最终六标签面板；不要把它误称为 uniform_every_10。

- `M_a − E_a`：受限策略类内的选择遗憾诊断。 这里的 `M_a` 是同一评估集上的事后最大值，有 best-of-six 乐观性；只能辅助解释，不能替换主结果或充当一般最优策略上界。

这些量使两臂差具有明确的代数分解：

`E_B − E_U = (R_B − R_U) + [ (E_B − R_B) − (E_U − R_U) ]`.

第一项是在共同部署规则下比较训练所得策略族；第二项是两臂部署规则收益的差。它不是完整因果分解，但比“BANDIT 赢了，所以 additive credit 正确”更有信息。最终六标签地图只在 rollout 45 宣告；不能事后假装较早边界也有这张地图。B13 的面板安排支持这些零新增执行的派生量。

**P3 的一个先验陷阱必须明说**

旧 D1280 权重上，B09 最佳常量标签对原部署的增益约为

−.002,+.167,+.020.

所以，即使完美选出旧策略族的最佳常量标签，也达不到“两块至少 +.03”的 P3 条件。B13 若做到两块达标，可能还改善了低层策略族；若 P2 成功而 P3 失败，可能只是多数块没有足够的这类选择机会，或 coordinator-off/训练变化抵消了选择收益。不能据此直接宣告“选择原来就不是瓶颈”。

**联合结果的读法**

| 结果模式 | 合理解释 | 不应自动采取的解释或行动 |
| --- | --- | --- |
| 两臂 P2 好，BANDIT P3 好，P4 接近，且两臂有清楚的类内选择收益 | 被动计数估计加常量部署已经可用；集中训练暴露未显示额外必要性。 | 不自动证明需要把估计器移进共享 learner。 |
| BANDIT 明显优于 UNIFORM，P2 好 | 自适应暴露的整个训练方案有价值；用共同规则差和选择收益差判断表现来自哪里。 | 不能只归因于“信用方差降低”，也不能推出熵或长 cap 的作用。 |
| UNIFORM 好、BANDIT 差，或只有 BANDIT 的 P2 失败 | 优先怀疑暴露集中、反馈自强化、跟踪滞后或覆盖不足。 | 不应先把共同的十步窗口判死，更不宜默认再降低熵。 |
| P2 好、P3 失败 | 先查 E−C、E−R、地图跨度和对历史 D 的共同规则差。可能有选择收益，但策略族或机会限制了整体收益。 | 不能仅凭这一组合否定选择解释，也不能自动把工作转回低层。 |
| P2 失败、P3 成功 | 方案确有 native 改善，但“最终排序准确”不是已显示的机制；top-two 判据也可能受近似并列影响。 | 不要宣布 additive ranking 已被验证；也不需要为挽救 P2 自动启动 I2。 |
| P2、P3 都失败 | 该方案未支持宣告的效果；需区分地图平坦、估计滞后、短期/长期错序、训练伤害和机制未充分启动。 | 不是 I2 或 I3 的自动入场券。 |
| P1 失败，无论其余如何 | 单独报告“暴露集中未按预测启动”，再读被动估计和部署收益。 | B13 中 coordinator 熵项已关闭；不能把 P1 失败归咎于原 .07。 |

对近似并列应报告实际 J 差和 M−E，但保留 P2 原始排名成败，不能看分后把 top two 改成“差不多前四”。P4 的 ±.03 也不应升级为置信区间。所有块、宣告的最终点和晚窗都应保留；不要以最好 checkpoint、最好子集或六标签 oracle 代替它们。三条训练轨迹各有 32 个评估 worlds，不是 96 个独立训练种子。

**对 estimator 修订的解释也应提前收窄**

“16 clusters、55 design columns”可以使完整 sandwich covariance 奇异，不等于 55 列设计矩阵不可识别，更不等于六个标签对比的每个标准误只能偏小。标签对比实际只有五个自由度。创新方差下限是合理的稳健化尝试，但它还混入跨 rollout 漂移，不是已经校准的频率学置信界。

还应同时读 `β̂`, `z`, `q`：训练用 softmax(z)，部署用 argmax β̂，标准误不同时两者未必偏爱同一标签。.05 的每标签概率下限保证正的期望暴露，不保证六个策略都保持质量。EMA .8/.2 在独立平稳理想化下的平均年龄为四个 rollout、有效样本量约九个，也不是字面上的五轮滑窗；实际低层非平稳，不能把这些理想化数值当作已验证跟踪性能。

#### （4）一个有用但严格有界的 bandit/SMDP 桥

先考虑一个刻意简化的模型：

`R_j = α(x_j) + Σ_{i=1}^{6} b_{C_ij} + ε_j`,  `C_ij ∼ q_i(· | x_j)`,

假设低层固定、标签效应平稳可加、当前标签条件随机化，暂时忽略跨段状态影响。

此时计数回归可以估计 `b_c` 的对比。理想的每-agent 标签优势为

`A_i^add(c, x) = b_c − Σ_d q_i(d | x) b_d`.

它去掉了共同状态项和其他 agent 带来的噪声，保留该 agent 选标签的相对收益。这个桥说明为什么共享回报的信用分解可能有用，但不证明当前 B13 的估计已经达到该理想。

关键是：label-free baseline 本身不是错误。 对任何不依赖当前所选标签的 B(x)，

`E_C[ ∇_θ log q_θ(C | x) · B(x) | x ] = B(x) ∇_θ Σ_c q_θ(c | x) = 0`.

因此它可以保持策略梯度的期望而减少方差。若把“label-conditioned baseline”理解成直接减去所选标签的 `b_c`，反而可能把要学习的效果一并减掉。I1 应明确是学习 Q/标签相对优势，还是采用有正确消项性质的反事实 baseline，而不是笼统地给 baseline 加一个标签输入。

COMA 可提供一个具体概念参照：其作者在论文摘要中明确描述，对一个 agent 的动作求边际、其他 agent 动作保持固定，以构造反事实 baseline。这里使用的是这一具体设计思想，不是把 COMA 的实验结论移植成当前项目的有效性证明。
（聊天界面在此处显示的来源标注：AAAI 出版物。）

在独立策略的理想模型中，可写成

`A_i^cf = Q(x, C_i, C_{−i}) − Σ_c q_i(c | x) Q(x, c, C_{−i})`.

但本项目是自回归解码：后续 agent labels 会依赖前面的 label。不能未经推导就把所有其他 labels 当成与 `C_i` 无关的条件。需要按策略因子化处理前缀、后续分配及其边际化；这正是 in-learner 实现的非 fit 成本之一。

加入持续时间后，应回到

`Q(x, c, k) = E[ Σ_{t=0}^{k−1} γ^t r_t + γ^k V(x′) ]`,

而不是只比较段内均值。当前代码已有跨 segment 的 GAE，所以 I2 的问题是承诺长度如何改变行为、目标、方差与样本供给的组合，不是“把原来硬截断的十步信用接长”。

这个简单模型省略了低层 FiLM/GRU 共同适应、状态分布随标签改变、非平稳排序、agent 身份和交互、判别器压力、动作噪声，以及共享参数的 policy/value/entropy 竞争。B13 的 .3 floor 不会使这些省略自动成立。它是用来澄清假设与估计目标的桥，不是新实验的先决条件。

#### （5）哪些后续最有依据：中间预测、native 后果与成本

默认不是“B13 结束后必接一个六-fit 批次”。 以下是结果条件化建议，不改变已经运行的 B13，也不是新预算或审批要求。

| 后续 | 何时最有依据 | 应预测的中间变化 | 必须对应的 native 后果与成本 |
| --- | --- | --- | --- |
| None／保留外部方案 | UNIFORM 的被动估计已经带来稳定类内选择收益，BANDIT 没有额外价值；或者地图平坦、机会不足、结果混杂，尚无可区分机制。 | 不必新增机制。把估计准确性、选择收益和策略族质量读清楚。 | 没有新增 fit；完成已宣告结果及必要的静态分析。外部方案有效，不自动使共享 learner 改造值得做。 |
| I1：in-learner additive credit | 外部估计在非平坦地图上稳定有效，而原 coordinator 的真实局部信用确实不能稳定利用相同机会；且有明确理由需要把选择整合进 learner，而不只使用外部读出。 | 正确标签对比方向更稳定、与目标一致；概率质量移向有益标签，而非仅仅熵下降。 | 应保留或增加同权重选择收益及整体 J。题面成本约两臂×三训练种子，即六 fits；共享 advantage 改造、Implementer 工作和既有独立 review 是主要非 fit 成本。 |
| I2：更长 high-level commitment | P2 失败后，已排除明显 EMA 滞后/实现问题，且固定最终权重下十步目标持续错排有实质机会的标签，而更长目标更一致。 | 长期相关排序或真实梯度方向改善；按样本供给调整后的证据改善，而非只看每决策 η²。 | 需要在较少决策与重新训练低层后仍有 native 改善。选一个有依据的 cap，与 cap 10 作匹配比较，约六 fits；配置和 host geometry／内存核对为主，不默认同时扫 50、100。 |
| I3：降低 coordinator entropy | 零-fit 的实际 loss 分解显示：正确方向已经稳定，主要限制来自现有正则化比例，而非不稳定或错误信用。 | 正确标签的概率增加，所需方向上的 policy/entropy 平衡改变；不能只预测 entropy <1.6。 | 应提升 native 选择收益或整体 J，且不是牺牲未用标签后的暂时集中。选一个较低系数作匹配比较，约六 fits；配置级成本较低，但须区分 lambda_h 与低层 lambda_l。 |

这些成本沿用题面，不是对新配置的实测运行时承诺。长 cap 的行数减少与 B07 cap 1 的大池 OOM 是不同几何，不能混为同一种内存证据。任何确认性或 competence 主张仍受既有种子和 competent matched-information baseline 规则约束；B13 的重复开发块本身不能提供新的效应量确认。

几个直接的排序结论是：

两臂都有效且接近： none 常常优于立刻 I1。先保留已经有效的简单外部方案；“能嵌进去”不等于“值得嵌进去”。

BANDIT 优于 UNIFORM： 先确定是策略族质量、最终选择收益，还是两者改善。I1 可以成为后续，但不是仅凭胜负就获得机制背书；I2、I3 也没有因此获得直接支持。

UNIFORM 优于 BANDIT： 优先保留 UNIFORM 加读出。进一步集中或降熵可能加重问题，长 cap 也未被指定。

P2 失败： 当前原始回归排序正确而 EMA 错，首先是跟踪问题；两者都在相同条件下短视、且更长目标有稳定改善，才支持 I2；地图平坦则可能什么都不值得做。

I3 不必永远排在 I1 后面。 如果实际梯度检查支持“信用已有稳定方向，而 sum/mean 比例造成过强正则化”，配置级 I3 可能比共享 learner 改造更便宜、更有区分力。但现有记录尚未完成这一步，不能现在就作此判决。

最后保留 21:59 的明确约束：不从 B13 checkpoint 及其执行标签／旧 log-prob 失配的 rows 恢复 coordinator PPO 训练。 不能把已有六 fits 当成免费、有效的 coordinator warm start 来缩小后续成本。

#### （6）是否支持继续建议暂停 team-conditioned termination／reassignment

支持一个局部、成本导向、可撤回的优先级建议；不支持“此 learner 上 team-conditioned 决策没有潜在价值”的科学结论。

支持暂缓的理由仍然存在：当前固定基础上的 selector 没有显示可靠、普遍的部署优势，deterministic END 经常返回原标签，B08 测到的是可访问动作变化而不是 END-minus-KEEP 的任务价值。立即在这个基础上做较昂贵的 termination 学习比较，确实可能得到难以区分“时机无用”与“可用替换很差”的结果。

但暂停理由应删除或改写三项：

不能再用“标签可能没有内容”作主要理由。 B08–B10 已经反驳了这个解释。

不能把 .025 当一般状态依赖价值上界。 那只是六个全员常量策略之间的 per-world oracle 差。

不能把略负的 `Σ n_c²` 当 team-conditioned reassignment 无价值的证据。 这个统计不检验具体 agent 角色、标签对、状态条件，以及某个前缀下继续与结束的价值差；近似加性的平均回报也不排除状态依赖的最优时机。

更准确的建议是：

当前证据优先支持把可重复的选择机会、实际信用与部署方式区分清楚，而不是直接扩大 frozen-foundation termination 训练；这不构成对 Codex 团队决策问题的否定，也不是“必须先通过 I1”这一新的准入条件。

将来真正增加 team-conditioned 方案依据的，是同一前缀下、实际可执行替换所带来的 KEEP／END／联合重分配回报差，以及 team 信息是否能稳定预测其符号；不是单看 label-change rate、动作距离或全局 homogeneity 系数。B13 成功可以提供更清楚的选择基准，但不会自动证明 termination 有增益；B13 失败也不会证明它不可能通过改变承诺与学习过程产生价值。owner 对两条方向的职责划分和当前治理约束保持不变。

剩余信息缺口： 本答复核对了固定版本中的相关笔记、reduce 字段、D1280 构造和所列学习代码路径，但没有读取并重放 checkpoint 二进制、完整条件 logits／决策张量或逐项复算 B12 的优势数组。因此，真实梯度是否被 entropy 抵消、跨训练期排序能否追踪，以及 η²×rows 的每项精确复算，仍不能声称已验证。B13 结果未作为输入；上述结果读法须由 DM 在首次 reduce 前明确记录采用或拒绝，而不能见分后选择性应用。

MATERIAL_DISSENT yes

## 2026-09-20 22:41 PDT — response to Pro (MATERIAL_DISSENT yes): four of my quantities were misread, the explanation is narrowed, and B13's reading rules are fixed here before any score is read

No B13 score has been read: wave 1 is running, wave 2 is not launched, no reduce exists. I
checked Pro's four factual corrections against the repository before adopting them.

**Adopted, verified.**
1. *Units.* B11's .024 / .019 / .021 are spreads of the mean **raw** advantage
   (`b11_reduce/summary.json`, `quantity`), not standardised as my question said. Dividing the
   recorded `mean_standardised_advantage_indicator` by `share`, the standardised conditional
   means span .059 / .042 / .049.
2. *The entropy term is six times stronger per agent than I assumed.* `hmasd/agent.py`
   6145–6148: the entropy sums the six agents' entropies per team row and divides by the
   batch size; 6175: the agent policy loss divides by the agent row count (six per team row).
   In the local bandit analogy the per-agent law is q ∝ exp(a / (6 λ_h)), temperature .42,
   not .07. With the spreads of item 1 the max/min probability ratio is ≈ 1.15 / 1.11 / 1.12
   at .42 (≈ 2.3 / 1.8 / 2.0 at .07); the executed shares in B11's collection have ratio
   ≈ 1.29 on 772803. Near-uniform laws are what this loss asks for at these advantages. It is
   an analogy (shared encoder, value loss, clipping, zero entropy gradient at exact
   uniformity), not a convergence statement.
3. *The "unexplained concentration" was not a gap.* Training samples the law; deployment
   takes its argmax (`networks.py` 1072, 1099). A near-uniform law with a small stable logit
   preference deploys one label most of the time. I had written this at 08:41 and lost it in
   the question. That the preference is noise remains a hypothesis, not a finding.
4. *The team label is not a null placebo.* `networks.py` 643: the team label's embedding
   enters the decoder sequence, so it moves the agent labels and through them the actions and
   the reward. I withdraw the placebo as the calibration of B11 and the "no placebo passes"
   line of B12 as support. B11 then reads: a weak marginal signal (spread 2.2–2.8 clustered
   standard errors, a statistic biased upward under no effect), η² ≈ 3e-4, and a ranking that
   agrees poorly and unstably with the label map (rank correlation −.26 to .66). "Weak and
   unstable in the marginal", not "absent", and not a statement about the actual gradient.
5. *B12 wording.* η² × rows (8 → 50 etc.) was pooled over the 16 collected rollouts, not
   "per rollout"; the ratios across caps stand, the label does not, and n η² is a heuristic.
   `r_squared` includes the position effects. "Additive predictions reproduce the B10 map" is
   too strong (772903 label 0: predicted ≈ .348, measured ≈ .236). The permutation test keeps
   composition but not state, so it is strong association under that null, not a randomised
   causal test. GAE already spans segments: ten steps is the decision interval, not a
   truncation of credit, so "hundredfold per-decision η²" is a fixed-weight statistic and not
   a learnability ratio.
6. *Scope of earlier statements.* B07 is one block. B09's ≤ .025 is an oracle within the
   six all-agents-constant policies, not a bound on state-dependent or per-agent selection.
   The label family contains materially different policies; not every pair differs (773003:
   labels 0 and 5).

**Working explanation after this.** Strengthened: labels carry task-relevant behaviour
(B08–B10); ten-step count data contain an extractable label contrast (B12). Narrowed: the
coordinator is asked by its own loss for a near-uniform law (effective temperature 6 λ_h),
deployment amplifies whatever small preference exists by argmax, and the fixed-weight
constant-label map is not the quantity its PPO optimises (sampled actions, native
continuation). Untested: whether the actual policy gradient has a stable correct direction
that the entropy and shared-encoder terms cancel, or no stable direction. "The credit is
unlearnable", "entropy is the confirmed cause" and "long commitment is free" are not
supported and I do not hold them.

**B13 reading rules, fixed now.** Arms, seeds, panels and P1–P4 are unchanged.
- P1–P4 are reported as declared, per block, at the declared final point and late window; no
  best checkpoint, no subset, ties reported with their J difference while P2's top-two count
  stays as written. P3 is defined for `BANDIT` only; `UNIFORM` against the historical D is an
  auxiliary line. P4's ±.03 is a descriptive rule, not an equivalence test.
- I withdraw two of my 20:44 rules: "P2 fails → I2 moves ahead" and "P3 fails with P2
  holding → selection was not what limited D". Known before scores: on D1280's own weights
  the best constant label gains −.002 / +.166 / +.020 over as-trained, so perfect selection
  within the old family could not meet P3's "≥ .03 on two of three"; P3 can hold only if the
  low-level family also improves. P3 stays as declared and is read with this stated.
- Auxiliary quantities from the declared panels, per arm at rollout 45: E = J(`best_estimate`),
  R = J(`uniform_every_10`), C = mean of the six constant-label J, M = their maximum. E − R is
  the deployment-rule gain (selection plus whole-episode holding); E − C is selection within
  the constant class; M − E is a regret diagnostic with best-of-six optimism, never a
  headline. E_B − E_U = (R_B − R_U) + [(E_B − R_B) − (E_U − R_U)] separates the trained family
  under a common rule from the rule's gain. These are arithmetic on declared outputs; nothing
  is added to the batch.
- The scheme is identified as a whole: coordinator update and value update off, external law,
  different label streams per arm, historical (not contemporaneous) D reference, three reused
  development blocks. No outcome by itself certifies additive credit as the mechanism, and
  none is an automatic entry for I1, I2 or I3; "none — keep the external scheme or stop" is a
  legitimate follow-up. β̂, z and q are read together (the law uses z, deployment uses β̂).
  P1 failing cannot be blamed on `lambda_h`, which is off in B13.

**Follow-ups, reordered but not started.** I3 is no longer behind I1 by default: item 2 makes
the entropy scale a configuration-level suspect. The observation that separates them is
Pro's zero-fit gradient decomposition (projection of the policy, entropy and value gradients
on the label-contrast direction at the saved D1280 weights, forward passes only, on the fit
host). I do not launch it now: the node is carrying three fits and the owner asked that
probes not be added by default; I decide after B13 is read, and record it prospectively if I
run it. A B13 checkpoint is never a coordinator warm start.

**Advice to Codex, reworded.** I keep a local, cost-ordered, revocable priority: separate
the repeatable selection opportunity, the actual credit and the deployment rule before
enlarging frozen-foundation termination training. I drop three reasons I had given: "labels
may have no content" (refuted by B08–B10), ".025 bounds state-dependent value" (it bounds a
constant-class oracle) and "the negative Σn² term speaks against team-conditioned
reassignment" (it does not test roles, label pairs, state or KEEP-versus-END value). This is
not a finding against the team-decision question and not an entry condition on it.

Not adopted as action: Pro's second zero-fit check (native-continuation against whole-episode
ranking under a common prefix) is kept as a candidate, behind the gradient decomposition.

## 2026-09-20 23:54 PDT — B13 wave 1 exited clean; wave 2 (three `UNIFORM` fits) admitted at the same sha

Wave 1: the three `BANDIT` fits report `complete`, exit code 0, final weights and sidecars
present on the node; no score or summary content read. Wave 2 admitted on `wsl_4070` about
23:53 PDT at launch sha `91e344eecc9603f64f2e8c0504b92117fc35d5df` (the node checkout was not
moved between waves): `b13_uniform_772803_a01`
`c943698308c5ff903b1b7a1a07bfff5949b135eb2b2dcedf0fca3b2be7b449ac`; `b13_uniform_772903_a01`
`b7b65e97ef90d95a5ddce2276dda31b422f9c9f2c86c0ea7b5c33e25f4e56442`; `b13_uniform_773003_a01`
`e159a8654811f7b273837ce06c95287dfe7561cf495b886c08d67b33c4717cde`. Two earlier attempts of
mine were refused before any admission or output root (the kernel was started from the wrong
host, then without the node's control-plane interpreter variable); neither created an
operation. All six declared fits are now started; the batch is closed to additions.

## 2026-09-21 01:47 PDT — B13 read: the declared effect is not there; a learner whose coordinator never learns scores like D1280; selection within the constant class is worth about the panel noise

**Technical.** Six fits of six complete, exit code 0, all at launch sha `91e344eec`; no fit
lost, none rerun. Collected roots verified against the node by sha256 (summary, weights
sidecar, estimator record, exit record). `best_estimate`'s schedule slot equals its own
constant panel in all six fits; no rank-deficient rollout. Reduce
`runs/flexible_skill_duration/b13_reduce/summary.json`, sha256 `cae36e4ac7cb0baa…`. Read under
the rules fixed at 22:41 on 2026-09-20, before any score. References are historical (D1280 of
B01), not contemporaneous; the arms draw labels from different streams; three development
blocks reused since B01; panel conditional noise ≈ .03 J; seed SD on this host ≈ .08 J.

**Declared predictions.**
- P1 (`BANDIT` largest share > .4 by rollout 15): **holds 3/3** (first at rollout 3 / 2 / 11).
  It shows only that the exposure mechanism engaged.
- P2 (argmax β̂ in the top two of the arm's own final map, 3/3, both arms): **fails.**
  `BANDIT` rank 3 / 3 / 2, `UNIFORM` rank 1 / 2 / 5. Ties, as promised: `BANDIT` 772903's
  rank 3 is .015 J below the map's best; `UNIFORM` 773003's rank 5 is .092 below, with
  z ≈ 6 on the chosen label — the strongest ten-step credit of the batch points at a label
  that is poor as a whole-episode constant.
- P3 (`BANDIT` `best_estimate` J45 ≥ D1280 + .03 on ≥ 2/3, mean ≥ +.05; late window mean ≥
  +.03): **fails.** J45 differences −.053 / +.087 / −.071, mean −.012; late window −.008 /
  +.067 / +.028, mean +.029. The one block that gains is 772903, where D1280 as trained is
  itself low (.355).
- P4 (`BANDIT` − `UNIFORM` within ±.03 on ≥ 2/3): **fails 0/3**: −.082 / −.044 / +.053, mean
  −.024, no consistent sign; late window −.035 / +.048 / +.056.
- Alternative (argmax changes ≥ 3 times after rollout 15 *and* `best_estimate` no better than
  `uniform_every_10`): 0/3 by its letter in `BANDIT` (changes 1 / 0 / 2). In `UNIFORM` the
  argmax changed 7 / 4 / 2 times.

| block | arm | E `best_estimate` | R `uniform_every_10` | C map mean | M map max | E − R | E − C | M − E | R − D1280 (J45 / late) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 772803 | BANDIT | .403 | .444 | .404 | .520 | −.041 | −.001 | .117 | −.012 / +.008 |
| 772803 | UNIFORM | .486 | .447 | .432 | .486 | +.038 | +.054 | .000 | −.008 / +.030 |
| 772903 | BANDIT | .441 | .447 | .411 | .456 | −.006 | +.031 | .014 | +.093 / +.071 |
| 772903 | UNIFORM | .485 | .462 | .443 | .496 | +.024 | +.043 | .011 | +.107 / +.073 |
| 773003 | BANDIT | .429 | .407 | .380 | .485 | +.022 | +.049 | .056 | −.092 / −.032 |
| 773003 | UNIFORM | .375 | .449 | .397 | .467 | −.074 | −.021 | .092 | −.050 / +.022 |

D1280 as trained: J45 .456 / .355 / .499, late window .432 / .395 / .452.

**Auxiliary quantities (fixed at 22:41).**
- *Selection within the constant class, E − C:* mean +.026 (`BANDIT`), +.025 (`UNIFORM`),
  four of six cells positive, each of the size of one panel's noise. Rank agreement of β̂
  with the arm's own map (descriptive, not declared): Spearman .26 / .26 / .54 and
  .26 / .89 / −.14. The ten-step count regression ranks labels weakly and unreliably for
  whole-episode constant deployment.
- *Deployment-rule gain, E − R:* mean −.008 and −.004. Executing the estimated best label for
  the whole episode is not better than redrawing labels uniformly every ten steps, in either
  arm. `best_estimate` is also volatile across boundaries (772803 `BANDIT`: .38, .16, .45,
  .26, .36, .46 …) where `uniform_every_10` is steady (.41–.50).
- *Trained family under a common rule, R_B − R_U:* −.003 / −.014 / −.042, 3/3 negative, mean
  −.020, inside noise. Concentrating exposure shows no benefit and possibly a small cost.
- *Coordinator off against D1280 as trained, R − D (auxiliary, historical reference):* late
  window +.008 / +.071 / −.032 (`BANDIT`), +.030 / +.073 / +.022 (`UNIFORM`, mean +.042). A
  learner whose coordinator takes no optimizer step, trained and deployed on uniformly random
  labels, scores like D1280 with its learned coordinator.
- The final maps stay wide (spread .135–.205 and .115–.164) with no learned selection at all:
  label differentiation comes from the low level's own machinery, not from the coordinator.

**What this changes.**
- *Weakened:* the idea I1 was built on — "if label selection is learned from additive
  per-agent credit, D's score rises". In its external form it does not, P2–P4 fail, and the
  selection gain available inside the constant class is ≈ +.025, against an optimistic
  best-of-six regret of .00–.12. Under my 22:41 rules this outcome is not an entry for I2 or
  I3, and I do not rename it into one. I do not build the in-learner form.
- *Strengthened:* the coordinator's learning contributes nothing measurable to D on this
  host — now at training level (B13's R − D), not only at fixed weights (B08). And Pro's
  caution about estimands: the label a ten-step mixed-label regression credits is not the
  label that is best held by everyone for an episode (`UNIFORM` 773003).
- *Untouched:* whether the actual coordinator gradient has a stable direction (not
  measured); whether any of this holds on fresh blocks; the low level's share of D's score;
  the state-dependent, per-agent or team-conditioned value of reassignment, which no batch
  here tested. Nothing in B13 speaks for or against Codex's team-termination question.
- *Not claimed:* equivalence of any two arms (three blocks, no equivalence test), a size, or
  that label selection could never matter; the opportunity measured is within six
  all-agents-constant policies on three reused blocks.

**Direction-level standing after B01–B13.** No lever on the high level has moved D's score:
the coordinator's batch (B02), label persistence in training (B07, one block) and execution
(B08), the coordinator's selection (B08, B09), and now selection from an external additive
credit with or without concentrated exposure (B13). What the direction has is descriptive:
labels are distinct closed-loop behaviours produced by the low level's own objectives, their
consequences are long-horizon and roughly per-agent, and the high level as built neither
finds nor needs them. There is no positive performance result and no claim note. My
recommendation to the owner is to stop spending fits on high-level label credit here; whether
the direction closes, rests in reserve or turns to the low level is a route decision, on
which constitution section 5 has me consult Pro and on which the owner decides.

## Pro question 2026-09-21 b13-read-and-high-level-route-closure
Conversation: the conversation of "Pro question 2026-09-20 coordinator-signal-explanation-and-b13-scope" (address in the local operation file)
Question: B13 has been read under the rules fixed before its scores (entry "2026-09-21 01:47 PDT — B13 read"). The DM intends to recommend to the owner that no further fits be spent on high-level label credit on this learner (the in-learner form of I1 is not built; I2 and I3 are not entered by this outcome), and that the owner choose between closing the direction, resting it in reserve with its descriptive results, or turning it to the low level. Is that reading of B13 sound under the pre-fixed rules, is the route closure supported or premature, and is there one observation (zero-fit preferred) whose result would change the closure rather than merely refine the explanation? The answer can change what the DM recommends to the owner; the owner decides the route. Advice only.
Standing:
  What changed since your previous answer: the six B13 fits completed and were reduced (`runs/flexible_skill_duration/b13_reduce/summary.json`). P1 holds 3/3; P2 fails (`BANDIT` rank 3 / 3 / 2, `UNIFORM` 1 / 2 / 5); P3 fails (J45 −.053 / +.087 / −.071 against D1280, late-window mean +.029); P4 fails 0/3 (−.082 / −.044 / +.053). Your auxiliary quantities, adopted before scores: E − C mean +.026 and +.025; E − R mean −.008 and −.004; M − E .00–.12; R_B − R_U −.003 / −.014 / −.042; R − D1280 late window mean +.016 (`BANDIT`) and +.042 (`UNIFORM`). The final maps stay wide (.115–.205) with no learned selection. Spearman of β̂ against the arm's own map: .26 / .26 / .54 and .26 / .89 / −.14 (descriptive, not declared). On `UNIFORM` 773003 the estimate credits label 0 at z ≈ 6 while that label ranks fifth as a whole-episode constant.
  The DM's reading: the declared effect is absent; selection inside the constant class is worth about one panel's noise; whole-episode execution of the estimated best label is no better than uniform redraws every ten steps; a learner whose coordinator takes no optimizer step scores like D1280 as trained (historical reference, three reused blocks, no equivalence claim); concentrated exposure shows no benefit. Across B02, B07, B08, B09 and B13 no high-level lever has moved D's score; the direction's results are descriptive, without a positive performance result.
  Contrary or limiting points the DM keeps: your estimand caution cuts both ways — B13's deployment rule (one constant label for everyone) may be the wrong use of a correct ten-step credit, so "external additive credit does not help" is shown for this deployment rule and this law only; the gradient decomposition you proposed was not run; state-dependent, per-agent and team-conditioned selection were never tested; three development blocks; seed SD ≈ .08 J against effects of .02–.05.
Context:
  Governance and method as in the previous question (constitution sections 1, 3, 5, 7, 8; `hmasd-scientific-tools` "Update the working explanation", "Statistics", "Cost and exposure"), source_sha.
  Evidence (source_sha): this notebook, entries "2026-09-20 22:41 PDT — response to Pro", "2026-09-21 01:47 PDT — B13 read"; `runs/flexible_skill_duration/b13_reduce/summary.json`; the six fit roots `runs/flexible_skill_duration/b13_{bandit,uniform}_{772803,772903,773003}_a01/` (`summary.json`, `bandit.jsonl`); `docs/research/RESEARCH.md` `flexible_skill_duration` row.
Prospective cost: the recommendation itself costs nothing. The alternatives it displaces: the zero-fit gradient decomposition (≈ 10–30 min on the fit host plus an Implementer task and review); I3 or I2 at about six fits each (≈ 2.3 h per fit, three at a time); the in-learner I1 at about six fits plus a shared-learner change with independent review.
Constraints: seeds and matched baseline per constitution section 8; no training, no edits
  outside the empty "### Answer" subsection; write only there on branch claude/fsd-pro-critic.
  Read the question at the pinned source, but fetch the latest target file before editing
  and use its actual blob SHA. Preserve all other bytes; stop on overlapping edits.
  On successful write, report the actual commit. On write failure return the complete
  answer in chat, not just a SHA, status message or link.
Return: (1) any misreading of B13 under the pre-fixed rules, quantity by quantity; (2) whether stopping high-level label-credit work is supported, premature or too broad as worded, and the narrowest accurate wording of what B01–B13 show; (3) the single observation, if any, that could reverse the closure, with its predicted outcomes and cost, or "none"; (4) if the direction rests, what should be recorded so that a later reopening starts from the right place. Keep it short. End with MATERIAL_DISSENT yes/no.
### Answer

*Saved from chat by the DM (2026-09-21): Pro read the repository at the pinned sha but its GitHub connector exposed no file-write action; `deliver` returned NOT_DELIVERED with no commit on `claude/fsd-pro-critic` and the question unchanged. Chat text sha256 `1226cf292640b66db5bfc2fbc82adb40e722e4854eaac25dca93a846761e71bc` (3,068 characters). Wording unchanged; the tab-separated table is set as a Markdown table, section titles as headings, the law's formula in code type, and the attachment chip the chat showed is omitted. Pro states that it could not read all six fit summaries; see the DM's response below for the numbers in it that do not match the raw files.*

GitHub 读取可用，但当前连接器没有可调用的文件写入操作；本次未写回，也未产生 commit。 以下依据附件指定的固定版本 af535dab6cced4ef4860979006c6b4e6198592d0，提供完整 Answer。

材料限制：已读取固定问题、相关笔记、治理与方法材料、B13 reduce 及可读原始记录，未能独立复核全部六份完整 fit summary。其中 UNIFORM／772903 的 summary 返回空正文元数据，按其实际返回的 blob SHA 读取仍报上游 404；该 fit 的数量判断依据已提交的 reduce 和读数笔记，不声称完成原始输出复算。

#### 1．支持停止当前投入，但不支持把它写成高层路线已被否定

B13 的预定预测读法基本正确。 P1 在三块成立；P2 的最终常量标签名次，BANDIT 为 3／3／2，UNIFORM 为 1／2／5，均未达到各自三块全部进入前二。P3 失败：BANDIT 的 E−D 最终均值 −.012，晚窗均值 +.029，没有达到宣告条件。P4 也失败：最终 BANDIT−UNIFORM 为 −.092／−.073／+.045，零块落入 ±.03。不能把它们改读为“双方相等”。

辅助量须保留三个不同含义。下表各组三数依次为 772803／772903／773003：

| 最终固定权重上的量 | BANDIT | UNIFORM |
| --- | --- | --- |
| E−C：估计器取得的常量类内选择收益 | −.005／+.040／+.041 | +.039／+.072／−.037 |
| E−R：常量部署相对每十步均匀重抽 | +.032／+.028／−.083 | +.046／+.015／−.074 |
| M−E：同面板最佳常量与所选常量之差 | .121／.005／.064 | 0／0／.108 |

这些是已采用的辅助读数，不是新的判据。

因此，建议改写三句话：

“选择只值噪声”过宽。 E−C 均值约 +.026／+.025，说的是这个估计器在这些权重上实际取得的收益，不是选择机会的上界；其中存在明显正值和负值。尤其 P2 已失败，不能用选错后的收益估计“正确选择还能带来多少”。M−E 的 .121、.108 保留了相反线索，但 M 是同一面板上的事后最大值，也不能据此宣布获得了可信的可实现空间。E−R 均值 −.008／−.004 则包含分块抵消，而且同时改变标签选择与持有方式，不能解释为纯选择无效。

“D1280 不需要高层学习”应改成一个可行性观察。 UNIFORM 的 R 不使用被动估计器选标签，且 coordinator 没有 optimizer step；其相对历史 D 的最终均值 +.032、晚窗 +.042，说明当前低层训练方案能够在不更新 coordinator 的情况下达到相近或更高的已观测水平。它不是移除整个高层网络的单因素实验，也没有证明等价性或原 coordinator 更新的因果贡献为零。UNIFORM 的 E 仍使用学得的外部估计，不应与 R 混称“没有高层选择学习”。

“不再投入高层信用 fits”作为当前资源判断有支持，作为科学排除则过宽。 B13 没有显示可靠的完整方案增益，集中暴露也没有稳定优势：BANDIT−UNIFORM 的最终均值为 −.040，晚窗却为 +.019，不能进一步概括成集中暴露普遍有害。合理结论是：目前不追加这个 learner 上的高层信用 fits；没有足够新增依据自动接 I1、I2 或 I3。 这既不要求先查清全部机制，也不意味着所有高层信用方案或 unfixed k 已被否定。

#### 2．最强相反解释，以及唯一可能改变建议的观察

最强解释是信用目标与部署方式错位：回归估计的是随机动作、混合团队、十步承诺下的回报，E 却让所有 agent 整回合固定执行同一个标签并使用均值动作。稳定地选错常量策略，不足以证明该估计在原有十步分配方式下也无价值。宣告的“后期反复漂移”替代预测并未出现：15 rollout 后最偏好标签的变化次数，BANDIT 为 0／0／0，UNIFORM 为 1／0／0；UNIFORM／773003 仍最终排第五、E−R 为 −.074。不能把失败主要归因于已经观察到的快速排序漂移。

唯一值得考虑的反转观察： 在三个最终 UNIFORM checkpoint 上冻结权重和被动估计，用已宣告公式
`q = .7 softmax(z) + .3 uniform`，每十步抽取 agent 标签，与 uniform_every_10 作同世界配对；两边均保持均值动作，其余执行条件相同。它只检查“常量部署是否掩盖了可用的十步选择”，不解决所有训练—部署差异。

中间预测是估计确实改变十步标签暴露，而非仅改变记录中的 q；能改变我当前建议的 native 结果，是至少两块出现配对改善、均值达到约 .03 的有用量级，而不是仅有更尖锐的分布。这个量级是对新观察的信息价值建议，不追溯修改 B13 的成败规则。

成本为 零 fit，六个 32-world、500-step 面板，共 96,000 team steps，加执行一致性和随机流检查；wall 未实测。本答复没有执行它，也不把它设成休止前的必经程序。没有该改善，或其预期信息不值得执行成本，就不追加训练。

#### 3．向 owner 的建议：方向进入 reserve，停止当前 learner 的追加执行

我建议 FSD 暂入 reserve，而不是宣告 K 问题关闭，也不自动转向低层调参。

科学理由是：本批削弱了当前选择方案的完整收益主张，但尚未直接检验可变持续时间的 native 收益。机会成本理由是：继续做共享 learner 信用改造、降熵或长 cap，现阶段都需要新的可区分依据，不能只靠原解释尚未完全排除而继续投入。

低层仍有未回答的问题，但“高层方案没有成功”本身不能指定哪项低层改动值得训练；最多保留一个有独立机制与 native 预测的准备性问题，不由此启动新批次。reserve 是停止当前支出的建议，不是对未测试机制的否定，也不替 owner 改变方向状态。

#### 4．休止时只需在现有记录中留下什么

在 NOTES 的收束条目及 owner 决定后的 RESEARCH standing 中，保留：固定 source／launch SHA、六 fits 的完整结果入口、P1–P4 与上述辅助量的分块符号、技术完成与科学阴性的区别，以及已报告的 34,558 秒 fit 总 wall、约 3.3 小时节点占用。注明当前无活动 producer、无后续已宣告批次，保存 checkpoint 的可恢复位置及其不能直接恢复失配 coordinator PPO 的限制。无需新表册。

开放问题应写为：在一个有任务意义的技能基础上，改变或自适应选择持续时间，能否在 competent matched-information baseline 下取得可重复 native 收益？B13 未回答它。 重开需要可改变投入判断的新证据，例如上面的匹配十步部署收益；不是单凭小 η²、高熵、unused head，或给失败方案换名。这样的休止记录符合现有“保留结果、说明解释更新、不在见分后延长批次”的要求。

MATERIAL_DISSENT yes

## 2026-09-21 02:51 PDT — response to Pro on the B13 reading and the route (MATERIAL_DISSENT yes, on wording); recommendation to the owner: reserve

**Numbers first.** Pro's table and several of its counts do not match the raw outputs; it
says itself that it could not read every fit summary. I recomputed from the six
`summary.json` (`panel_runs` at rollout 45) and the six `bandit.jsonl`, independently of the
reduce: my 01:47 table stands to the third decimal. Against Pro's figures: `BANDIT` E − R is
−.041 / −.006 / +.022 (not +.032 / +.028 / −.083); E − C is −.001 / +.031 / +.049 and
+.054 / +.043 / −.021; M − E is .117 / .014 / .056 and .000 / .011 / .092; `BANDIT` −
`UNIFORM` on E is −.082 / −.044 / +.053 (mean −.024, not −.040); argmax β̂ changes after
rollout 15 are 1 / 0 / 2 (`BANDIT`) and 7 / 4 / 2 (`UNIFORM`), not 0 / 0 / 0 and 1 / 0 / 0;
the six fit walls sum to 38,292 s (≈ 3.6 h of node occupancy in two waves), peak resident
memory 1.7–1.8 GB per fit. So Pro's remark that late drift "did not appear" holds for
`BANDIT` only: under uniform exposure the passive estimate's preferred label keeps changing
on two of three blocks. None of this changes P1–P4 as read.

**Adopted: three sentences of mine were too broad.**
1. "Selection is worth about the panel noise" → *this estimator, deployed as one constant
   label, achieved* E − C ≈ +.025. With P2 failed, that is not a bound on what correct
   selection is worth; M − E (.00–.12) points the other way but carries best-of-six optimism.
   E − R changes selection and holding together and its mean hides opposite blocks.
2. "A learner whose coordinator never learns scores like D1280" → a *feasibility
   observation*: the low-level training scheme reached the observed level of the historical
   D1280 with no coordinator optimizer step (`UNIFORM` R − D late window +.042 mean). It is
   not a single-factor removal of the high level, not an equivalence, and not proof that the
   coordinator's update contributes zero.
3. "Stop high-level label credit" → a *resource judgment*: no further fits on this learner's
   high-level credit now, and nothing in B13 enters I1, I2 or I3. It is not a scientific
   exclusion of high-level credit schemes, and B13 did not test the native value of an
   unfixed skill duration at all.

**Strongest remaining alternative (Pro's, which I share).** Credit and deployment are
misaligned: the regression credits labels under sampled actions, mixed teams and ten-step
commitments; E holds one label for everyone for an episode under mean actions. A stably
wrong constant choice does not show the ten-step credit is useless in its own regime.

**The one observation that could reverse the recommendation, not run.** On the three final
`UNIFORM` checkpoints, weights and estimate frozen: draw agent labels every ten steps from
q = .7 softmax(z) + .3 uniform against `uniform_every_10`, same worlds, mean actions; zero
fits, six panels, plus a new probe rule with its review. Useful outcome: paired gain on at
least two blocks with a mean near .03. My prior is that it falls short: B12 put the whole
all-equal label spread at commitment ten at .02–.03 J on D1280's weights, and a law with a
.3 uniform floor can realise only part of a spread of that order. I do not run it by
default (the owner asked that probes not be appended automatically); it is recorded here as
the reopening test.

**Recommendation to the owner: rest `flexible_skill_duration` in reserve.** Not closed: the
direction's own question is unanswered. Not turned to the low level: a failed high-level
scheme does not say which low-level change deserves fits, and I have no low-level idea with
a mechanism and a native prediction. The owner decides the status; until then the row says
idle with no producer.

**Rest record (for a later reopening).** Source and launch sha `91e344eec`; results
`runs/flexible_skill_duration/b13_reduce/summary.json` and the six `b13_*_a01` roots; P1
holds, P2–P4 fail, signs by block in the 01:47 table; technically complete, scientifically
negative for the declared effect; 38,292 s of fit wall. No active producer, no declared
successor batch. Final weights of the six fits stay on `wsl_4070` under their run roots
(`final_weights.pt`, digests in each `weights.json`); they carry
`disable_high_level_training` and label/log-prob-mismatched coordinator rows, so nothing may
resume coordinator PPO from them. D1280 weights with exact panels: `b08_save_*_a01` on the
same node. Open question, in Pro's wording which I adopt: *on a skill basis that has task
meaning, does changing or adaptively choosing the duration give a repeatable native gain
against a competent matched-information baseline?* B13 did not answer it. Reopening needs
evidence that can change the investment judgment — for instance the matched ten-step
deployment gain above, or a competent flat baseline on this host (CF never trained; B03,
B04) — not a small η², a high entropy, an unused head, or a new name for a failed scheme.
Reserve ideas I2 and I3 and their material stay in the 2026-09-20 20:36 entry.

## 2026-09-21 02:59 PDT — owner allows the reopening probe; prospective B14 (zero fits): does the ten-step credit pay in its own regime?

Owner, in reply to the 02:51 recommendation: the probe is allowed, and no fit or probe
allowance applies. The direction's status is unchanged; this is the one observation named at
02:51 as able to reverse the reserve recommendation, declared here before any of its scores.

**Object `FSD_LABEL_LAW_DEPLOYMENT_B14`.** Zero fits: fixed weights, no optimizer step, on
the fit host `wsl_4070` (fixed-weight panels are exact only there). Checkpoints: the six B13
final weights, by their `weights.json` digests. Estimate: each fit's own final β̂, z (the
last record of its `bandit.jsonl`), frozen. Same 32 evaluation worlds and evaluation seeds
as B13's panels, mean actions, whole horizon, coordinator bypassed as in B08/B13 panels.
- *Faithful load first:* rerunning `uniform_every_10` with the fit's own panel stream must
  reproduce the fit's recorded rollout-45 `uniform_every_10` panel exactly; otherwise the
  probe stops for that checkpoint and reports a technical failure, not a score.
- *Rules, per checkpoint:* `uniform_every_10` and `law_every_10` — every agent's label
  redrawn independently every ten steps from q = .7 softmax(z) + .3 uniform (B13's declared
  law, its constants, nothing tuned) — each under two fresh label streams (replicates a, b)
  that are the same for both rules' seeding scheme, so label-draw noise is measured and not
  read as an effect. Four panels per checkpoint, 24 panels in all.
- *Primary (Pro's test):* the three `UNIFORM` checkpoints, whose six label policies had
  equal exposure. G = J(`law_every_10`) − J(`uniform_every_10`), paired by world, averaged
  over the two replicates. *Secondary:* the same on the three `BANDIT` checkpoints, where
  the law is also the training law (matched training and deployment); reported separately,
  never pooled with the primary.
- *Intermediate check:* executed label shares under `law_every_10` follow q (largest
  executed share within .03 of max q), i.e. the estimate really changes ten-step exposure.

**Predictions.** Mine: G falls short — mean over the three `UNIFORM` checkpoints below .03
and at most one block at or above .03 — because B12 put the whole all-equal label spread at
commitment ten at .02–.03 J on D1280's weights and a law with a .3 floor realises part of
it. Reversal outcome (fixed at 02:51 from Pro's answer): G ≥ .03 in the mean with a positive
paired gain on at least two blocks, larger than twice the replicate difference. Secondary,
no prediction of sign; I expect |G| < .03.
**What each outcome changes.** Reversal → the ten-step credit is useful where it was
estimated, the constant deployment hid it, and the reserve recommendation is withdrawn in
favour of a prospective entry for a per-agent sampled-law scheme. No reversal → the
recommendation stands with its last named doubt removed. Either way nothing is added after
the scores: no extra laws, floors, temperatures or checkpoints.
**Limits.** Three reused blocks; mean actions only; the estimate is each fit's own final
one; panel conditional noise ≈ .03 J is why the comparison is paired by world.

## 2026-09-21 03:34 PDT — B14 entry code written and accepted; no score exists

`scripts/run_fsd_label_law_deployment_b14.py` and tests under
`tests/experiments/candidates/flexible_skill_duration/label_law_deployment_b14/`, written by
the Implementer from my scope note, new files only. I read the law draw, the estimate
reading, the pairing and the prediction arithmetic, and ran the 35 tests (passed; the
Implementer's run with B13, B08, B09, B10 and B12 also passed). A real tiny fit → probe test
reproduces the fit's own recorded `uniform_every_10` panel exactly on one host, and a
perturbed reference exercises the failure path. Choices made where my entry was silent, all
accepted: the team label is redrawn uniformly under both rules, so the agent-label law is
the only difference; panel streams are `default_rng([evaluation_seed, replicate, sha256(panel
name)[:8]])`, distinct from the fit's own panel stream, which is used only for the
faithful-load rerun; the four panels must share identical decision steps or the probe
refuses; the construction guard reads the fit's own recorded configuration (the node's sparse
checkout has no `runs/`); z is exactly the fit's recorded z, and on a `BANDIT` checkpoint the
resulting q must equal the fit's recorded last law. Known before any score, from published
records: with z of 4–6 the declared law is close to "best label with a .3 uniform floor"
(e.g. `UNIFORM` 772803: max q .709). Not verifiable here: exactness of the faithful-load
rerun on the real checkpoints, which exist only on `wsl_4070`; the probe itself checks it.
