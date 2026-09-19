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
