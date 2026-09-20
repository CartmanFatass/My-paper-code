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
