"""FSD label bandit B13: additive label credit as an external label bandit, six fits.

Prospective entry in the direction notebook:
docs/research/candidates/flexible_skill_duration/NOTES.md, "2026-09-20 20:44 PDT - prospective:
additive label credit as an external label bandit, B13 (six fits)".

Idea I1, first form.  The claim "if label selection is learned from additive per-agent credit, D's
score rises" is tested without editing the shared learner: the coordinator's *agent* labels are
replaced, in training, by draws from a context-free law driven by the count regression B12
validated, and deployment executes the estimated best label.

Thin entry over the frozen baseline x interruption B01 runner, as B07 and B08 are: the same
collector loop, panel law, summary and fit validation, rebound to this object's identity, on blocks
772803 / 772903 / 773003 with 45 rollouts and the matched-information stage-1 panels (5, 10, ...
45).  Two arms, three blocks, six fits.

  BANDIT   at every agent decision the executed label is drawn from
           `q = .7 * softmax(z) + .3 * uniform` (rollout 1: uniform), by a dedicated generator
           seeded from (training seed, arm).
  UNIFORM  `q` uniform throughout; the estimator runs passively.  It separates learning the
           ranking from concentrating exposure on it, and is the coordinator-off control.

Declared configuration difference from the recorded stage-1 D1280 construction, in both arms:
`disable_high_level_training = True`, and nothing else.  Why it is required: with the labels
rewritten, the coordinator's D2 rows would carry the *executed* labels beside the *sampled* labels'
log-probabilities (hmasd/agent.py:2321-2343 writes `self.env_agent_skills` into the row and
hmasd/utils.py:551-553 stores the chosen label's log-probability alone), which is an invalid PPO
ratio that nothing asserts against.  The flag skips `update_coordinator` entirely
(hmasd/agent.py:7182-7190), so the coordinator takes no optimizer step; a run-time guard makes any
coordinator optimizer step raise and the reader refuses a fit that took one.  `SOURCE_NOTES`
records every reader of the flag with its file:line.

What the rewrite reaches.  An instance wrapper on the *learner* agent's `_batched_assign_skills`
calls the frozen method, rewrites the returned agent labels at the sampled positions
(`_d2_last_step['sampled_mask']`) and writes them back into `env_agent_skills`, so the low-level
actor and critic, the intrinsic reward and both discriminators all train on the executed labels
(hmasd/agent.py:3266-3294, 4042-4127, 6353-6455).  The *team* label is left as the coordinator's
own and never reaches the actor (hmasd/networks.py:1801-1809).  Both interruption costs are
infinite on this construction, so the held label cannot move a decision boundary and the cadence
stays the frozen ten-step one; the wrapper refuses to attach if either cost is finite or if the D2
age feature is on.

The estimator, in both arms, after each rollout's collection and before the next rollout's first
decision: B12's own count regression (`run_fsd_commitment_visibility_b12.label_regression`,
imported, not retyped) of each ten-step team commitment's undiscounted mean team reward on the six
agent-label counts with one fixed effect per commitment position, centred coefficients with
lane-clustered variances; then `beta_hat <- .8 beta_hat + .2 beta_r` and
`var_hat <- .64 var_hat + .04 var_r` (the independent-rollout combination of the same weights),
with the first usable rollout taking `beta_1`, `var_1`; `z_c = beta_hat_c / se_c` with a floor on
the denominator alone.  A rank-deficient rollout (a label absent) is skipped and recorded.

Evaluation at every panel boundary, on the same 32 worlds: `best_estimate` (B09's constant rule
with `c = argmax beta_hat`, the lowest label breaking a tie) in the frozen schedule slot, and
`uniform_every_10` (B08's rule) beside it; at rollout 45 also the six `constant_c` panels.  One
frozen `evaluate_panel` call fans out into those panels, each a genuine frozen call with the rule
attached; the extra panels are moved out of `summary["panels"]` into `summary["extra_panels"]` so
the frozen schedule stays the declared nine.  Every panel runs inside the frozen
`_preserve_rng` (scripts/run_flexible_skill_duration_e0.py:123-133), which saves and restores the
Python, NumPy and torch global streams, so the extra panels leave the training stream where a
single panel would leave it; a test pins that by comparing a fit's training rows with and without
the fan-out.

`fit` is result-bearing and runs only through `scripts/hmasd_launch.py` (runner-side admission).
`reduce` is a pure reading of published summaries and carries no admission.
"""
import argparse
import hashlib
import inspect
import json
import math
import sys
from contextlib import ExitStack, contextmanager
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import probe_fsd_d_state_scale_b06 as probe
import run_fsd_baseline_interruption_b01 as b01
import run_fsd_commitment_visibility_b12 as b12
import run_fsd_flat_entropy_b03 as entropy
import run_fsd_flat_input_scale_b05 as scale
import run_fsd_flat_update_b04 as update
import run_fsd_label_content_b08 as b08
import run_fsd_label_map_b09 as b09
import run_fsd_matched_information_baseline_b01 as matched
import run_fsd_persistence_b07 as persistence
from scripts.hmasd_admission import require_admission

shared = b01.shared
DIRECTION = "flexible_skill_duration"
OBJECT_ID = "FSD_LABEL_BANDIT_B13"
CARD = ("docs/research/candidates/flexible_skill_duration/NOTES.md "
        "(2026-09-20 20:44 PDT, prospective B13)")
BLOCKS = dict(b08.BLOCKS)  # 772803, 772903, 773003
# Both arms are the frozen runner's `("D0", 1280)` renewal route, which is the recorded stage-1
# D1280 construction; the frozen runner dispatches on the arm name, so this object names its own.
ARMS = {"BANDIT": ("D0", 1280), "UNIFORM": ("D0", 1280)}
BANDIT_ARM, UNIFORM_ARM = "BANDIT", "UNIFORM"
# The one declared configuration difference from the recorded D1280 construction, in both arms.
# It is *not* a `config_snapshot` field (scripts/run_flexible_skill_duration_e0.py:208-224 does not
# list it), so the guard in `make_config` requires the recorded snapshot to be identical and checks
# this attribute on the configuration object itself; `declared_config_difference` records it.
DECLARED_FIELD = "disable_high_level_training"
ARM_OVERRIDES = {BANDIT_ARM: {DECLARED_FIELD: True}, UNIFORM_ARM: {DECLARED_FIELD: True}}
ARM_CAPS = b08.ARM_CAPS  # (10, 10): skill_cap_k_max, team_cap_k_Z
SKILL_PERIOD = b08.SKILL_PERIOD  # `config.k`
COMMITMENT_CAP = 10  # the frozen D2 cadence, and the length of the commitments the estimator reads
N_LABELS = b09.N_LABELS  # 6
D_REFERENCE = "D1280"  # the published stage-1 fits of FSD_MATCHED_INFORMATION_BASELINE_B01
RECORDED_FITS = dict(probe.RECORDED_FITS)
GEOMETRY_FIELDS = probe.GEOMETRY_FIELDS
ROLLOUTS = matched.ROLLOUTS  # 45
PANEL_ROLLOUTS = matched.PANEL_ROLLOUTS  # 5, 10, ... 45
# The late window of the notebook entry's own references ("late window (30-45)"): the last four
# panels, which is the window B05 and B07 already read.
LATE_PANELS = PANEL_ROLLOUTS[-4:]  # 30, 35, 40, 45
# The notebook entry's own plan: about 2.3 h and 2.9 GB per fit. A plan, never a deadline.
WALL_PLANS = {BANDIT_ARM: 8300., UNIFORM_ARM: 8300.}
PRIMARY_NAME = f"J_{ROLLOUTS}"
WEIGHTS_NAME = b08.WEIGHTS_NAME
SIDECAR_NAME = b08.SIDECAR_NAME

# the estimator and the law: the entry's constants, declared there and not tuned
EMA_WEIGHT = .8              # beta_hat <- .8 beta_hat + .2 beta_r
NEW_WEIGHT = 1. - EMA_WEIGHT
STANDARD_ERROR_FLOOR = 1e-12  # on the denominator of z alone, to avoid division by zero
EXPLOIT_WEIGHT = .7          # q = .7 * softmax(z) + .3 * uniform
FLOOR_WEIGHT = 1. - EXPLOIT_WEIGHT
SOFTMAX_TEMPERATURE = 1.
LABEL_FLOOR = FLOOR_WEIGHT / N_LABELS  # .05 per label

# the panels
SCHEDULE_RULE = "best_estimate"      # occupies the frozen schedule slot
REFERENCE_RULE = "uniform_every_10"  # B08's rule, the selection-free reference on the same weights
FINAL_MAP_RULES = tuple(b09.constant_rule(label) for label in range(N_LABELS))
DISCOUNTED_AGREEMENT_TOLERANCE = b12.DISCOUNTED_AGREEMENT_TOLERANCE  # 1e-5

# the notebook entry's declared sizes; none of them is a decision rule
PREDICTION_MARGIN = .03      # P3's per-block margin, P4's band and the late-window mean
MEAN_MARGIN = .05            # P3's mean over blocks
SHARE_THRESHOLD = .4         # P1's "largest label share above .4"
SHARE_ROLLOUT = 15           # P1's "by rollout 15"
ALTERNATIVE_CHANGES = 3      # the strongest alternative's "three or more times"
ALTERNATIVE_AFTER = 15       # "after rollout 15"
PANEL_NOISE = b09.PANEL_NOISE  # .03 J conditional evaluation noise

CURRENT = {"arm": None, "admission": None, "summary": None, "agent": None, "rule": None,
           "estimator": None, "tape": None, "stack": None, "counters": None, "out": None}
_orig_make_config = matched._orig_make_config  # the frozen `run_fsd_baseline_interruption_b01`'s
_orig_build_learner = b01.build_learner
_orig_evaluate_panel = b01.evaluate_panel
_orig_base_summary = shared.base_summary
_FLAG = "_label_bandit_wrapper"

SOURCE_NOTES = {
    "z_denominator": (
        "amendment to the prospective entry, recorded in the notebook before any score (NOTES.md, "
        "2026-09-20, B13 acceptance entry). One rollout has 16 lane clusters against 55 design "
        "columns, so its clustered variance has rank at most 16 and can only understate. The "
        "denominator of `z` is therefore sqrt(max(var_hat, empirical)), where `var_hat` is the "
        "declared combination of the rollouts' clustered variances and `empirical` is the "
        "stationary variance of `beta_hat` implied by the rollout-to-rollout innovations "
        "`d_r = beta_r - beta_hat_{r-1}`: `innovation <- w innovation + (1 - w) mean_c d_r[c]^2` "
        "(the first innovation is its own value), `g = (1 - w) / (1 + w)`, "
        "`empirical = innovation * g / (1 + g)`, one number pooled over the six labels. It can only "
        "lower |z|. `estimate.var_hat` alone therefore does not reproduce `estimate.z`; "
        "`estimate.standard_error`, `estimate.innovation` and `estimate.empirical_variance` do"),
    "disable_high_level_training": (
        "the whole effect of the declared flag on this route, by file:line. (1) "
        "hmasd/agent.py:7182-7190 `update` replaces the `update_coordinator` call with zeros, so "
        "the coordinator takes none of its 15 optimizer steps per rollout "
        "(hmasd/agent.py:5099, 5935, 6218, all reachable only through `update_coordinator`) and "
        "`value_norm_coordinator` is never updated (hmasd/agent.py:6075-6078). "
        "The `d2_metrics` counters `rows_M`, `rows_M_agent` and `rows_M_team` are written only by "
        "`_d2_flush_open_segments` (hmasd/agent.py:2412-2418), which this route never calls, so "
        "they read 0 on every rollout of this object; that is not an absence of commitments - the "
        "800 closed team rows are proved per rollout by this object's own commitment reader. "
        "(2) the same skip means `_d2_flush_open_segments` (hmasd/agent.py:5646-5650, inside "
        "`update_coordinator`) is not called at the rollout boundary; on this construction every "
        "lane is terminal at the last step of every rollout, so every segment is already closed "
        "as terminal by hmasd/agent.py:2357-2377 and the fit checks at runtime that the rollout "
        "carries the full `lanes * horizon / cap` closed team rows. (3) hmasd/agent.py:4017 skips "
        "`_store_coordinator_experience`, the `off`-route pending/close mechanism, which the D2 "
        "route already bypasses unconditionally (hmasd/agent.py:3919-3932 returns before it): on "
        "`policy_interruption_mode = 'd2'` that reader is unreachable and the flag changes "
        "nothing there. (4) hmasd/agent.py:394 sets `self.collects_high_level_samples = False`; "
        "the only reader of that attribute in the repository is "
        "experiments/launchers/train_multiproc_config_1.py:5150, a launcher this runner never "
        "uses. (5) the learning-rate schedulers at hmasd/agent.py:7209-7220 are guarded by "
        "`use_lr_decay`, which is False on this construction (configs/config_1.py:217), so the "
        "coordinator's scheduler is not stepped either. (6) the flag is written into the "
        "checkpoint's own `config` by `save_model`, and "
        "scripts/analyze_r39a_fixed_hmasd_anchor.py:497-503 refuses a checkpoint whose config "
        "carries it; that analyzer is the R39 native-anchor reader and is not on this route, but "
        "it does mean a B13 checkpoint is not an input to it. Nothing else in the repository reads "
        "the flag: hmasd/baselines.py sets it for the flat switches and "
        "experiments/launchers/train_multiproc_config_1.py:475-476 refuses it, neither of which "
        "is on this route. The D2 storage path is *not* gated by it: hmasd/agent.py:3919-3932 "
        "calls `_d2_store_transition` under `self.d2_enabled` alone, so the rows the estimator "
        "reads continue to be written"),
    "executed_labels_reach": (
        "the wrapper returns the rewritten agent labels from `_batched_assign_skills`, which "
        "`HMASDAgent.step` passes straight to `_batched_select_action` (hmasd/agent.py:3266-3268) "
        "and puts into `step_data['agent_skills']` (hmasd/agent.py:3285-3287). The collector hands "
        "that `step_data` to `store_transition_batch` "
        "(scripts/run_fsd_baseline_interruption_b01.py:134-136), where it becomes the labels of "
        "the intrinsic reward and of both discriminator buffers (hmasd/agent.py:4042-4127) and the "
        "labels the low-level update replays (hmasd/agent.py:6353-6455 reads "
        "`batch['agent_skills']`). The wrapper also writes them back into `env_agent_skills` "
        "(the D2 route's own held labels, hmasd/agent.py:2714-2716), so the label the agent holds "
        "is the label it executed and hmasd/agent.py:2321-2343 stores the executed label in the "
        "coordinator's own row"),
    "team_label": (
        "the team label is left exactly as the coordinator chose it. It never reaches the "
        "low-level actor (hmasd/networks.py:1801-1809 passes only the observation, the agent label "
        "and the hidden state); it reaches the low-level critic (hmasd/networks.py:1557-1560), the "
        "team discriminator and the coordinator's own decoder"),
    "infinite_costs": (
        "both interruption costs are infinite on this construction, so the held label cannot move "
        "a decision boundary: `team_gap_fire`/`agent_gap_fire` (hmasd/agent.py:2595, 2612) compare "
        "the teacher-forced gap with an infinite cost and never fire, and the cadence is the two "
        "caps alone (hmasd/agent.py:2596, 2613). With a finite cost the rewritten held label would "
        "enter the trigger statistic and the arm would move the decision times as well as the "
        "behaviour, so the wrapper refuses to attach. The D2 age feature must be `off` for the "
        "same reason it must be in B12: `_d2_normalized_team_age`/`_d2_normalized_agent_age` "
        "(hmasd/agent.py:4253-4263) would carry the cadence into the discriminators"),
    "estimator_hook": (
        "the estimator runs inside an instance wrapper on the learner agent's own `update`, which "
        "calls the frozen `update` first and unchanged and then reads the rollout. The frozen "
        "collector calls `agent.update(...)` once per rollout "
        "(scripts/run_fsd_baseline_interruption_b01.py:157-159) and calls `agent.clear_buffers()` "
        "at line 172, after the row is written; the wrapper is therefore the last point at which "
        "the rollout's D2 tables and this object's own reward tape are both complete, and it is "
        "before the panel (line 174) and before the next rollout's first decision. Calling the "
        "frozen `update` first is what keeps the rollout the unwrapped route's: nothing this "
        "object does is visible to the update, and with `disable_high_level_training` the update "
        "writes none of the tables the estimator reads"),
    "per_step_reward": (
        "the response's undiscounted term needs the raw scalar team reward of every step. The "
        "frozen storage keeps it only in two other forms: `d2_team_reward` is the "
        "gamma-discounted sum over the commitment (hmasd/agent.py:2348-2355) and the buffer's "
        "`reward_env` (hmasd/utils.py:248, 411) is `lambda_e * reward` broadcast to the agents in "
        "float32 (hmasd/agent.py:3367 from hmasd/agent.py:4219-4223), a scaled per-agent copy and "
        "not the raw team reward. So this object tapes the reward on the *environment* side, "
        "exactly as B12 does (`run_fsd_commitment_visibility_b12.RewardTape`): a wrapper replaces "
        "`env.step` on each training lane, calls the original first and unchanged, appends "
        "`result[1]` and returns the original result object. The collector's own scalar is that "
        "same value (scripts/run_fsd_baseline_interruption_b01.py:120-127). The tape draws no "
        "randomness, is popped in a `finally`, and is drained into one rollout's array at each "
        "rollout boundary, so it holds one rollout at a time. The runtime proof that the tape is "
        "aligned with the buffer's own commitments is that the gamma-discounted sum of the taped "
        "rewards over each commitment reproduces `d2_team_reward` to float32 precision"),
    "commitments": (
        "one rollout's commitments are the closed team segments of the frozen D2 tables "
        "(`rollout_buffer.get_d2_tables`, hmasd/utils.py:601-633): a valid team row sits at its "
        "own start step (hmasd/utils.py:584-599), carries the six executed agent labels written at "
        "that step (hmasd/agent.py:2329-2333) and its elapsed steps. The position is the 0-based "
        "commitment number within the lane-episode, by the order the starts ran in; a rollout is "
        "one episode per lane (the frozen collector refuses anything else, "
        "scripts/run_fsd_baseline_interruption_b01.py:152-153), so a commitment's position is also "
        "`start / cap`. The fit refuses a rollout whose geometry is not the cap's: "
        "`lanes * ceil(horizon / cap)` team rows, every team row carrying six valid agent rows, "
        "and every elapsed equal to `min(cap, horizon - start)`"),
    "regression": (
        "B12's own estimator, imported and not retyped: "
        "`run_fsd_commitment_visibility_b12.label_regression(counts, positions, response, "
        "clusters, n_positions=...)` is least squares of the response on the six agent-label counts "
        "with one fixed effect per commitment position, one label's count column dropped to break "
        "the exact collinearity, the six coefficients re-centred to mean zero and their "
        "cluster-robust covariance taken through the same contrast "
        "(run_fsd_commitment_visibility_b12.py:529-597). The cluster is the lane within the "
        "rollout - one lane-episode - which is B11's (rollout, lane) cluster inside a single "
        "rollout, so one rollout gives `lanes` clusters. With 800 commitments, 55 columns and 16 "
        "clusters the cluster-robust meat matrix has rank at most 16: the centred variances are "
        "the declared quantity and are used as declared, and that they are estimated from few "
        "clusters is a limit of the reading, not a tuning knob"),
    "rank_deficiency": (
        "a rollout in which some label is never held anywhere gives an all-zero count column (or, "
        "for the dropped label, an exact collinearity with the position dummies), so the design is "
        "rank-deficient and `numpy.linalg.lstsq` would return a minimum-norm solution rather than "
        "an estimate. Such a rollout is skipped - `beta_hat` and `var_hat` keep their values - and "
        "the rollout's own record carries `rank_deficient` and the labels that were absent"),
    "law": (
        "`z` is combined into the arm's law once per rollout, after the estimator's update and "
        "before the next rollout's first decision. BANDIT: "
        "`q = .7 * softmax(z) + .3 * uniform`, the softmax computed on `z - max(z)` so a large `z` "
        "cannot overflow, and `q` uniform while no rollout has yet produced an estimate. UNIFORM: "
        "`q` uniform always, and the estimator runs passively. The .3 floor gives every label at "
        "least .05, which is what keeps every label's policy and both discriminators trained. The "
        "constants are the notebook entry's and are not tuned"),
    "draws": (
        "the executed labels are drawn i.i.d. per (lane, agent) at the sampled positions of each "
        "decision, from `numpy.random.default_rng([training_seed, sha256(arm)[:8]])` - one "
        "dedicated generator per fit, built once. It touches no global NumPy, Python or torch "
        "stream, which a test pins by hashing the three global states across a block of draws. "
        "As in B08's own rules the wrapper draws one `[lanes, agents]` array per call of the "
        "assignment and applies it only where `sampled_mask` is set, so the generator's position "
        "is a function of the step count alone"),
    "panels": (
        "the frozen `run_fit` calls `evaluate_panel(learner, evaluator, summary, out, completed)` "
        "once per boundary through its own module global "
        "(scripts/run_fsd_baseline_interruption_b01.py:280-281), so this object binds that global "
        "for the duration of a fit and restores it in a `finally`. The wrapper puts the frozen "
        "function back while it runs, and fans the one call out into the declared panels, each of "
        "them a genuine frozen `evaluate_panel` call with a rule attached to the evaluator agent "
        "instance, through B08's own `run_rule_panel` with B09's rules bound. `best_estimate` "
        "takes the frozen schedule slot and stays in `summary['panels']`; every other panel of the "
        "boundary is moved into `summary['extra_panels']`, so `panel_rollouts`, the frozen "
        "schedule check and every reader see the declared nine panels. At the rollout-45 boundary "
        "`summary['evaluation']` is pointed back at the schedule slot, because the frozen "
        "`evaluate_panel` assigns it on every call at that boundary "
        "(scripts/run_fsd_baseline_interruption_b01.py:259-261). The evaluation exposure counters "
        "are *not* rewritten: they count every panel that ran, and this object's own reader "
        "expects the fan-out's totals"),
    "panel_rng": (
        "every panel runs inside the frozen `_preserve_rng` "
        "(scripts/run_flexible_skill_duration_e0.py:123-133, entered at "
        "scripts/run_fsd_baseline_interruption_b01.py:202), which saves the Python, NumPy and "
        "torch global states before the panel and restores them after it, and the evaluator is "
        "re-synced from the learner and its lanes reset at every panel "
        "(scripts/run_flexible_skill_duration_e0.py:319-335). The extra panels therefore leave the "
        "training stream exactly where a single panel would leave it and need no further "
        "save/restore; a test pins it by running a tiny fit with and without the fan-out and "
        "comparing every training row"),
    "best_estimate_rule": (
        "`best_estimate` is B09's `constant_c` rule with `c = argmax beta_hat` at that boundary, "
        "the lowest label breaking an exact tie (`numpy.argmax` returns the first maximum), and "
        "with no estimate yet `beta_hat` is the zero vector, so the rule is `constant_0` and the "
        "record says `estimate_available: false`. B09's own `check_rule_record` is applied to "
        "every panel, so a panel that executed any other label raises"),
    "coordinator_steps": (
        "for the duration of a fit the learner's `coordinator_optimizer.step` is replaced by a "
        "callable that raises, in the way B05's `_forbid_optimizer_steps` does, and the frozen "
        "`_StepCounter` it replaces is put back in a `finally`. The discoverer's and the two "
        "discriminators' optimizers are untouched and step normally. Beside that, every rollout "
        "checks the frozen counters (`summary['optimizer_calls']`) and the reader refuses a fit "
        "whose coordinator count is not zero or whose discoverer counts are not positive"),
    "declared_difference": (
        "`disable_high_level_training` is not one of the fields `config_snapshot` records "
        "(scripts/run_flexible_skill_duration_e0.py:208-224), so the declared-difference guard "
        "takes two parts: the recorded snapshot must differ from the D1280 construction's in "
        "*nothing* (the host-geometry fields excepted, and only on a shrunken test host), and the "
        "flag must be False on the baseline configuration object and True after the override. Both "
        "are recorded on the summary as `declared_config_difference`, and the runtime proof that "
        "the flag did what it declares is that the coordinator took zero optimizer steps"),
    "weight_transfer_to_evaluator": b08.SOURCE_NOTES["weight_transfer_to_evaluator"],
    "evaluation_route": b08.SOURCE_NOTES["evaluation_route"],
    "checkpoint_contents": b08.SOURCE_NOTES["checkpoint_contents"],
    "reporting_factor": b12.SOURCE_NOTES["reporting_factor"],
    "lane_cluster": b12.SOURCE_NOTES["lane_cluster"],
    "position_fixed_effects": b12.SOURCE_NOTES["position_fixed_effects"],
    "centred_coefficients": b12.SOURCE_NOTES["centred_coefficients"],
}

INTERPRETATION_LIMIT = (
    "exploration; three blocks that have carried every setting in this direction since B01, so no "
    "size claim and no competence claim; six fits, declared before any score and not extended "
    "after them. One new learner-side mechanism (the external label law) and one switched-off "
    "component (the coordinator's update) move at once, which the UNIFORM arm separates only "
    "partly: UNIFORM still replaces the coordinator's labels by uniform draws, so it is the "
    "coordinator-off control and not a D1280 rerun. The estimator is a context-free law: B09 "
    "found state-dependent selection worth at most .025 J at these checkpoints, which is the "
    "measured reason a context-free law is expected to lose little, not a proof that it does. The "
    "count regression is a regression on the arm's own executed assignment and not an experiment "
    "with assigned treatment in BANDIT, where the law is concentrated by design; its clustered "
    "variances come from 16 lane-clusters per rollout. Panels with sampled worlds carry about "
    f"{PANEL_NOISE} J of conditional noise, so smaller J differences are not read. The recorded "
    "D1280 references are published fits of the same blocks, not contemporaneous reruns.")


def bind(wrap=False):
    """Rebind the frozen runner's identities to this object; loop, panel law and validation stand.

    Readers need the identities only. A fit also wraps `shared.base_summary`, the frozen
    `build_learner` (the one point at which this object reaches the learner agent, its training
    lanes and its `update`) and the frozen `evaluate_panel` (the panel fan-out), and `run_fit`
    takes all three off again, so a later reader or fit of another object in the same process is
    not marked.
    """
    global shared, _orig_base_summary
    shared = b01.shared
    b01.OBJECT_ID, b01.CARD = OBJECT_ID, CARD
    b01.BLOCKS, b01.ROLLOUTS, b01.PANEL_ROLLOUTS = dict(BLOCKS), ROLLOUTS, PANEL_ROLLOUTS
    b01.ARMS, b01.FLAT_ARM = dict(ARMS), matched.CF_ARM  # no flat arm runs here
    b01.WALL_PLANS = dict(WALL_PLANS)
    b01.make_config = make_config
    if wrap:
        current = shared.base_summary  # only ever wrap a plain function, exactly once
        for flag, module in (("_matched_information_wrapper", matched), (entropy._FLAG, entropy),
                             (update._FLAG, update), (scale._FLAG, scale),
                             (persistence._FLAG, persistence), (b08._FLAG, b08)):
            if getattr(current, flag, False):
                current = module._orig_base_summary
        if not getattr(current, _FLAG, False):
            _orig_base_summary = current
        shared.base_summary = base_summary
        b01.build_learner = build_learner
        b01.evaluate_panel = evaluate_panel


# ---------------------------------------------------------------------------
# the construction: the recorded D1280 one, plus the one declared flag
# ---------------------------------------------------------------------------


def host_geometry():
    """This object's own lanes and horizon; B06's `FROZEN_GEOMETRY` is the frozen host's."""
    return {"train_lanes": int(shared.TRAIN_LANES), "eval_lanes": int(shared.EVAL_LANES),
            "horizon": int(shared.HORIZON)}


def config_differences(config, other):
    """Every snapshot field where `config` differs from `other` (B06's comparison)."""
    return probe.config_differences(config, other)


def allowed_differences(arm):
    """The recorded snapshot fields a fit of this object may differ from the D1280 fit in.

    None: the declared difference is not a snapshot field. Only a shrunken test host's geometry is
    ever allowed.
    """
    if arm not in ARM_OVERRIDES:
        raise ValueError(f"unknown arm {arm}")
    allowed = set()
    if host_geometry() != probe.FROZEN_GEOMETRY:  # a shrunken test host, never the frozen one
        allowed |= set(GEOMETRY_FIELDS)
    return allowed


def require_recorded_construction(config, recorded_config, phase, arm):
    """Refuse any difference from the recorded D1280 fit the host geometry does not explain."""
    differences = config_differences(config, recorded_config)
    unexpected = {key: value for key, value in differences.items()
                  if key not in allowed_differences(arm)}
    if unexpected:
        raise ValueError(
            f"the {arm} {phase} is not the recorded D1280 fit's construction: {sorted(unexpected)}")
    return differences


def recorded_fit(seed):
    """The published stage-1 D1280 summary of a block, or None with the reason it is unavailable.

    The execution node's sparse checkout does not carry `runs/`, so a fit cannot depend on this
    file existing. `make_config` refuses any snapshot difference from the same-seed D1280
    construction inside the fit itself; `reduce` checks the fields its panel reader names.
    """
    path = RECORDED_FITS[int(seed)]
    if not path.exists():
        return None, f"{path.relative_to(ROOT).as_posix()} is not in this checkout"
    return probe.recorded_fit(int(seed))[0], None


def _record_recorded_comparison(phase, arm, snapshot, block_seed):
    """Compare one phase's snapshot with the recorded D1280 fit's and put it on the summary."""
    summary = CURRENT.get("summary")
    recorded, reason = recorded_fit(block_seed)
    if recorded is None:
        result = {"available": False, "reason": reason, "differences": None}
    else:
        result = {"available": True, "reason": None,
                  "differences": require_recorded_construction(
                      snapshot, recorded[phase], phase, arm)}
    if summary is not None:
        key = f"{phase}_differences_from_recorded_d1280"
        if summary.get(key) is not None:
            raise ValueError(f"{phase} was built twice in one fit")
        summary[key] = result
    return result


def make_config(arm, envs, seed):
    """The frozen D1280 construction with the one declared flag set; any other difference refuses.

    `configs/config_1.py`'s `update_env_dims` runs `validate_config()` and then
    `calculate_and_set_buffer_sizes()` after the environment dimensions are set; both are re-run
    here in that order after the override, as B07 does, and the guard below shows that neither
    moved a recorded field. The declared field is not a recorded snapshot field
    (`SOURCE_NOTES["declared_difference"]`), so the snapshot must be identical and the flag is
    checked on the configuration object itself.
    """
    if arm not in ARM_OVERRIDES:
        raise ValueError(f"unknown arm {arm}")
    config = _orig_make_config(arm, envs, seed)
    baseline = shared.config_snapshot(config)
    before = bool(getattr(config, DECLARED_FIELD, False))
    if before:
        raise ValueError(
            f"the D1280 construction already carries {DECLARED_FIELD}; it is not this arm's "
            "declared difference")
    overrides = ARM_OVERRIDES[arm]
    for field, value in overrides.items():
        setattr(config, field, value)
    config.validate_config()
    config.calculate_and_set_buffer_sizes()
    snapshot = shared.config_snapshot(config)
    differences = config_differences(snapshot, baseline)
    if differences:
        raise ValueError(
            f"{arm} moved the recorded configuration snapshot in {sorted(differences)}; the "
            f"declared difference {sorted(overrides)} is not a snapshot field and nothing else "
            "may move")
    for field, value in overrides.items():
        if getattr(config, field, None) is not value:
            raise ValueError(f"{arm}'s {field} was not set to {value!r}")
    summary = CURRENT.get("summary")
    if CURRENT["arm"] is not None:  # None reproduces the construction alone (tests)
        block_seed = int(summary["block_seed"]) if summary else int(seed)
        phase = ("learner_config" if (summary or {}).get("learner_config") is None
                 else "evaluation_config")
        _record_recorded_comparison(phase, arm, snapshot, block_seed)
        if summary is not None:
            summary["declared_config_difference"] = {
                "field": DECLARED_FIELD, "baseline": before,
                "fit": bool(getattr(config, DECLARED_FIELD)),
                "in_config_snapshot": DECLARED_FIELD in snapshot,
                "recorded_snapshot_differences_from_the_d1280_construction": {},
                "definition": SOURCE_NOTES["declared_difference"],
                "effects": SOURCE_NOTES["disable_high_level_training"]}
    return config


# ---------------------------------------------------------------------------
# the estimator: B12's count regression, once per rollout, with the entry's EMA
# ---------------------------------------------------------------------------


class LabelEstimator:
    """`beta_hat`, `var_hat` and `z`: B12's centred count regression combined across rollouts.

    First usable rollout: `beta_hat = beta_1`, `var_hat = var_1`.  Then
    `beta_hat <- w beta_hat + (1 - w) beta_r` with `w = .8`, and the variances combined as the
    variance of that same combination of independent rollout estimates,
    `var_hat <- w^2 var_hat + (1 - w)^2 var_r`.  A rank-deficient rollout is skipped and both
    estimates keep their values.

    Amendment recorded in the notebook before any score (2026-09-20, B13 acceptance entry): one
    rollout has 16 lane clusters against 55 design columns, so its clustered variance has rank at
    most 16 and can only understate. The denominator of `z` is therefore the larger of `var_hat`
    and an empirical variance of `beta_hat` taken from the rollout-to-rollout innovations
    `d_r = beta_r - beta_hat_{r-1}`: `innovation <- w innovation + (1 - w) mean_c d_r[c]^2`
    (first innovation: its own value), and with `g = (1 - w) / (1 + w)` the stationary variance of
    `beta_hat` is `innovation * g / (1 + g)`, pooled over the six labels. It can only lower |z|.
    """

    def __init__(self, *, n_labels=N_LABELS, weight=EMA_WEIGHT, floor=STANDARD_ERROR_FLOOR):
        self.n_labels = int(n_labels)
        self.weight = float(weight)
        self.floor = float(floor)
        self.beta = np.zeros(self.n_labels, dtype=np.float64)
        self.variance = np.zeros(self.n_labels, dtype=np.float64)
        self.rollouts_seen, self.rollouts_used = 0, 0
        self.innovation = None  # EMA of the labels' mean squared rollout-to-rollout innovation
        self.skipped = []

    # -- the state ----------------------------------------------------------

    @property
    def available(self):
        return self.rollouts_used > 0

    def empirical_variance(self):
        """The innovation-based variance of `beta_hat` (one pooled number), or None before it exists."""
        if self.innovation is None:
            return None
        gain = (1. - self.weight) / (1. + self.weight)
        return float(self.innovation) * gain / (1. + gain)

    def standard_errors(self):
        """`sqrt(max(var_hat, empirical variance))`, floored on the denominator of `z` alone."""
        variance = np.clip(self.variance, 0., None)
        empirical = self.empirical_variance()
        if empirical is not None:
            variance = np.maximum(variance, empirical)
        return np.maximum(np.sqrt(variance), self.floor)

    def z(self):
        return self.beta / self.standard_errors()

    def argmax_label(self):
        """The deployed label: `argmax beta_hat`, the lowest label breaking an exact tie."""
        return int(np.argmax(self.beta))

    def state(self):
        return {"beta_hat": self.beta.tolist(), "var_hat": self.variance.tolist(),
                "standard_error": self.standard_errors().tolist(), "z": self.z().tolist(),
                "innovation": self.innovation, "empirical_variance": self.empirical_variance(),
                "argmax_beta_hat": self.argmax_label(), "estimate_available": bool(self.available),
                "rollouts_used": int(self.rollouts_used), "rollouts_seen": int(self.rollouts_seen)}

    # -- one rollout --------------------------------------------------------

    def update(self, commitments, *, n_positions):
        """One rollout's regression, and the combination it implies. Returns the rollout's record."""
        self.rollouts_seen += 1
        counts = np.asarray(commitments["counts"], dtype=np.float64)
        absent = [label for label in range(self.n_labels) if counts[:, label].sum() == 0.]
        fit = b12.label_regression(
            counts, commitments["position"], commitments["response"], commitments["clusters"],
            n_positions=int(n_positions), team_size=int(commitments["n_agents"]),
            n_labels=self.n_labels)
        record = {"segments": int(np.asarray(commitments["response"]).size),
                  "absent_labels": absent, "regression": None,
                  "beta_rollout": None, "var_rollout": None,
                  "rank_deficient": True, "skipped_reason": None}
        if fit is None:
            record["skipped_reason"] = "the rollout carries no commitments"
            self.skipped.append(record)
            return record
        record["regression"] = {key: fit[key] for key in (
            "segments", "columns", "rank", "full_rank", "clusters", "positions",
            "small_sample_correction", "dropped_label", "centred_coefficients", "clustered_se",
            "ranking", "best_label", "worst_label", "max_minus_min", "max_minus_min_clustered_se",
            "residual_sd", "r_squared")}
        beta_r = np.asarray([fit["centred_coefficients"][str(label)]
                             for label in range(self.n_labels)], dtype=np.float64)
        errors = np.asarray([fit["clustered_se"][str(label)] for label in range(self.n_labels)],
                            dtype=np.float64)
        var_r = errors ** 2
        record["beta_rollout"] = beta_r.tolist()
        record["var_rollout"] = var_r.tolist()
        record["rank_deficient"] = not bool(fit["full_rank"])
        if absent or not fit["full_rank"]:
            record["skipped_reason"] = (
                f"rank {fit['rank']} of {fit['columns']} columns; absent labels {absent}")
            self.skipped.append(record)
            return record
        if not (np.isfinite(beta_r).all() and np.isfinite(var_r).all()):
            record["skipped_reason"] = "the rollout's estimate is not finite"
            record["rank_deficient"] = True
            self.skipped.append(record)
            return record
        if self.rollouts_used == 0:
            self.beta, self.variance = beta_r.copy(), var_r.copy()
        else:
            weight = self.weight
            squared = float(np.mean((beta_r - self.beta) ** 2))  # against the estimate before it
            self.innovation = (squared if self.innovation is None
                               else weight * self.innovation + (1. - weight) * squared)
            self.beta = weight * self.beta + (1. - weight) * beta_r
            self.variance = weight ** 2 * self.variance + (1. - weight) ** 2 * var_r
        self.rollouts_used += 1
        return record


def label_law(estimator, arm, *, n_labels=N_LABELS):
    """The arm's context-free law over the six agent labels, and the name of the branch it took."""
    uniform = np.full(int(n_labels), 1. / float(n_labels), dtype=np.float64)
    if arm == UNIFORM_ARM:
        return uniform, "uniform"
    if arm != BANDIT_ARM:
        raise ValueError(f"unknown arm {arm}")
    if not estimator.available:
        return uniform, "uniform_no_estimate"
    z = np.asarray(estimator.z(), dtype=np.float64) / float(SOFTMAX_TEMPERATURE)
    shifted = z - z.max()  # stable: the largest exponent is exactly zero
    weights = np.exp(shifted)
    soft = weights / weights.sum()
    law = EXPLOIT_WEIGHT * soft + FLOOR_WEIGHT * uniform
    if not np.isfinite(law).all() or abs(float(law.sum()) - 1.) > 1e-12:
        raise ValueError(f"the label law does not sum to one: {law.tolist()}")
    if float(law.min()) < LABEL_FLOOR - 1e-12:
        raise ValueError(f"the label law is below its declared floor: {law.tolist()}")
    return law, "softmax_z"


def label_generator(training_seed, arm):
    """The arm's dedicated label generator; it touches no global NumPy, Python or torch stream."""
    digest = hashlib.sha256(str(arm).encode("utf-8")).digest()[:8]
    return np.random.default_rng([int(training_seed), int.from_bytes(digest, "big")])


# ---------------------------------------------------------------------------
# the rollout: the reward tape, the executed labels and the commitments
# ---------------------------------------------------------------------------


class RolloutRewardTape(b12.RewardTape):
    """B12's per-step reward tape, drained at every rollout boundary so it holds one rollout.

    The per-lane lists are cleared *in place*: the wrapper closes over the list object, so the tape
    must never rebind `self.rewards`.
    """

    def __init__(self, envs):
        super().__init__(envs)
        self.rollouts_drained = 0

    def drain(self, horizon):
        """One rollout's taped rewards as [horizon, lanes], in the collector's own lane order."""
        horizon = int(horizon)
        lengths = sorted({len(store) for store in self.rewards})
        if lengths != [horizon]:
            raise ValueError(
                f"the reward tape carries {lengths} steps per lane, not the {horizon} of one "
                "rollout")
        values = np.asarray([list(store) for store in self.rewards], dtype=np.float64).T
        for store in self.rewards:
            store.clear()
        self.rollouts_drained += 1
        return values


def attachment_site():
    """file:line of the statement that wraps the learner agent's skill assignment."""
    lines, start = inspect.getsourcelines(LabelBanditRule.attached)
    offsets = [index for index, text in enumerate(lines)
               if text.strip().startswith("agent._batched_assign_skills =")]
    line = start + offsets[0] if offsets else start
    return (f"{Path(__file__).resolve().relative_to(ROOT).as_posix()}:{line} wraps the *learner* "
            "agent instance's `_batched_assign_skills` for the duration of the fit; the frozen "
            "`step` calls it at hmasd/agent.py:3249, and B08 wraps the same method on the "
            "*evaluator* instance for one panel")


class LabelBanditRule:
    """The arm's label law, imposed on the learner agent's own skill assignment.

    The wrapper calls the frozen `_batched_assign_skills` first and unchanged, replaces the agent
    labels at this step's sampled positions by draws from the arm's law, and writes them back into
    `env_agent_skills` so the label the agent holds is the label it executed.  The team label is
    the coordinator's own and is never touched.
    """

    def __init__(self, arm, agent, generator, *, horizon=None, n_labels=N_LABELS):
        if arm not in ARMS:
            raise ValueError(f"unknown arm {arm}")
        config = agent.config
        self.arm, self.agent = arm, agent
        self.generator = generator
        self.n_labels = int(n_labels)
        self.n_agents = int(config.n_agents)
        self.n_z, self.n_Z = int(config.n_z), int(config.n_Z)
        if self.n_z != self.n_labels:
            raise ValueError(f"this object's law is over {self.n_labels} agent labels, not {self.n_z}")
        self.horizon = int(shared.HORIZON if horizon is None else horizon)
        self.law = np.full(self.n_labels, 1. / self.n_labels, dtype=np.float64)
        self.law_source = "uniform"
        self.lanes = None
        self.step_index = 0
        self.calls, self.draws, self.replaced = 0, 0, 0
        self.executed = None          # [horizon, lanes, agents]; -1 where no decision was taken
        self.histogram = np.zeros(self.n_labels, dtype=np.int64)
        self.decision_histogram = np.zeros(self.n_labels, dtype=np.int64)
        self._held = None

    # -- attachment ---------------------------------------------------------

    @contextmanager
    def attached(self):
        agent = self.agent
        if not getattr(agent, "d2_enabled", False):
            raise ValueError("this object's label law is defined on the D2 route")
        if np.isfinite(agent.d2_cost_c) or np.isfinite(agent.d2_cost_c_Z):
            raise ValueError("this object requires infinite interruption costs")
        if str(getattr(agent, "d2_age_feature", "off")) != "off":
            raise ValueError("this object requires the D2 discriminator age feature to be off")
        if (int(agent.d2_k_max), int(agent.d2_k_Z)) != tuple(ARM_CAPS):
            raise ValueError(f"this object runs at the frozen caps {tuple(ARM_CAPS)}")
        if "_batched_assign_skills" in agent.__dict__:
            raise ValueError("the learner already carries an instance-level skill assignment")
        original = agent._batched_assign_skills

        def assign(*args, **kwargs):
            team, agents, log_probs = original(*args, **kwargs)
            agents = self._step(args, kwargs, agents)
            return team, agents, log_probs

        agent._batched_assign_skills = assign  # an instance attribute only; the class is untouched
        try:
            yield self
        finally:
            agent.__dict__.pop("_batched_assign_skills", None)

    # -- the law ------------------------------------------------------------

    def set_law(self, law, source):
        law = np.asarray(law, dtype=np.float64)
        if law.shape != (self.n_labels,):
            raise ValueError("the label law is not a vector over the agent labels")
        self.law, self.law_source = law, str(source)

    def draw(self, shape):
        """`size` i.i.d. labels from the current law; the dedicated generator alone is consumed."""
        self.draws += int(np.prod(shape))
        return self.generator.choice(self.n_labels, size=shape, p=self.law)

    # -- one step -----------------------------------------------------------

    @staticmethod
    def _argument(args, kwargs, index, *names):
        """The frozen `step` calls positionally (hmasd/agent.py:3249); a keyword call is by name."""
        if len(args) > index:
            return args[index]
        for name in names:
            if name in kwargs:
                return kwargs[name]
        raise ValueError(f"the learner's skill assignment was called without {names[0]}")

    def _step(self, args, kwargs, agents):
        env_steps = np.asarray(
            self._argument(args, kwargs, 2, "env_steps_batch", "env_steps"), dtype=np.int64)
        last = self.agent._d2_last_step
        sampled = np.asarray(last["sampled_mask"], dtype=bool)
        agents = np.asarray(agents, dtype=np.int64).copy()
        lanes = int(agents.shape[0])
        if self.lanes is None:
            self.lanes = lanes
            self.executed = np.full((self.horizon, lanes, self.n_agents), -1, dtype=np.int64)
        if lanes != self.lanes or agents.shape[1] != self.n_agents:
            raise ValueError("the collector changed the lane or agent count inside a fit")
        if self.step_index >= self.horizon:
            raise ValueError("more assignment calls in a rollout than the horizon has steps")
        # One episode per lane per rollout is the frozen collector's own rule
        # (run_fsd_baseline_interruption_b01.py:152-153), so the lane step counter is the rollout
        # step index the storage path keys its rows on.
        if not np.array_equal(env_steps.reshape(-1), np.full(lanes, self.step_index)):
            raise ValueError(
                f"the lanes are not all at rollout step {self.step_index}: {env_steps.tolist()}")
        drawn = self.draw(agents.shape)
        executed = np.where(sampled, drawn, agents)
        if self._held is not None and not np.array_equal(agents[~sampled], self._held[~sampled]):
            raise ValueError("a held position did not keep the label this object last executed")
        if not np.array_equal(executed[sampled], drawn[sampled]):
            raise ValueError("a sampled position does not carry this step's drawn label")
        for lane in range(lanes):  # the executed label is the label the agent holds
            self.agent.env_agent_skills[lane] = executed[lane].copy()
        if sampled.any():
            rows = executed[sampled.any(axis=1)]
            self.executed[self.step_index][sampled.any(axis=1)] = rows
            self.decision_histogram += np.bincount(rows.reshape(-1), minlength=self.n_labels)
        self.histogram += np.bincount(executed.reshape(-1), minlength=self.n_labels)
        self.replaced += int(sampled.sum())
        self.calls += 1
        self.step_index += 1
        self._held = executed.copy()
        return executed

    # -- the rollout boundary -----------------------------------------------

    def drain(self):
        """One rollout's executed labels at its decision steps, as [horizon, lanes, agents]."""
        if self.step_index != self.horizon:
            raise ValueError(
                f"the rollout took {self.step_index} assignment calls, not {self.horizon}")
        executed = self.executed.copy()
        self.executed[:] = -1
        self.step_index = 0
        self._held = None  # a fresh rollout resets every lane; nothing is held across the boundary
        return executed

    def provenance(self):
        return {"arm": self.arm, "attached_at": attachment_site(),
                "law": self.law.tolist(), "law_source": self.law_source,
                "n_labels": self.n_labels, "n_agents": self.n_agents,
                "generator": "numpy.random.default_rng([training_seed, sha256(arm)[:8]])",
                "definitions": {"executed_labels": SOURCE_NOTES["executed_labels_reach"],
                                "team_label": SOURCE_NOTES["team_label"],
                                "infinite_costs": SOURCE_NOTES["infinite_costs"],
                                "draws": SOURCE_NOTES["draws"],
                                "law": SOURCE_NOTES["law"]}}


def rollout_commitments(agent, rewards, executed, *, horizon, cap=COMMITMENT_CAP,
                        n_labels=N_LABELS, lanes=None):
    """One rollout's ten-step team commitments: counts, position, response and the runtime checks.

    The labels are the buffer's own, and the check that they are this object's executed labels is
    the runtime proof that the rewrite reached the storage path.
    """
    horizon, cap = int(horizon), int(cap)
    lanes = int(shared.TRAIN_LANES if lanes is None else lanes)
    tables = agent.rollout_buffer.get_d2_tables(horizon)
    if tables is None:
        raise ValueError("the rollout buffer carries no D2 tables")
    team_valid = np.asarray(tables["team_valid"], dtype=bool)[:horizon]
    agent_valid = np.asarray(tables["agent_valid"], dtype=bool)[:horizon]
    if not np.array_equal(agent_valid.all(axis=-1), team_valid) or bool(
            (agent_valid.any(axis=-1) & ~team_valid).any()):
        raise ValueError("the team rows and the six agent rows do not renew together")
    rows = int(team_valid.sum())
    expected = b12.expected_team_rows(lanes, horizon, cap)
    if rows != expected:
        raise ValueError(f"the rollout closed {rows} team commitments, not the cadence's {expected}")
    steps, lane = np.where(team_valid)
    labels = np.asarray(tables["agent_skills"], dtype=np.int64)[steps, lane]
    elapsed = np.asarray(tables["team_elapsed"], dtype=np.int64)[steps, lane]
    stored = np.asarray(tables["team_reward"], dtype=np.float64)[steps, lane]
    sampled = np.asarray(tables["sampled_mask"], dtype=bool)[steps, lane]
    if not sampled.all():
        raise ValueError("a closed team commitment did not sample every agent")
    if np.any(labels < 0) or np.any(labels >= n_labels):
        raise ValueError("a stored commitment carries a label outside the label set")
    expected_elapsed = np.minimum(cap, horizon - steps)
    if not np.array_equal(elapsed, expected_elapsed):
        raise ValueError(f"a commitment's elapsed steps are not the cadence of cap {cap}")
    mine = np.asarray(executed, dtype=np.int64)[steps, lane]
    if not np.array_equal(mine, labels):
        raise ValueError(
            "the labels stored in the rollout buffer are not the labels this object executed")

    rewards = np.asarray(rewards, dtype=np.float64)
    if rewards.shape != (horizon, lanes):
        raise ValueError("the reward tape is not [horizon, lanes]")
    gamma = float(agent.config.gamma)
    response = np.zeros(rows, dtype=np.float64)
    discounted = np.zeros(rows, dtype=np.float64)
    for index in range(rows):
        window = rewards[steps[index]:steps[index] + elapsed[index], lane[index]]
        response[index] = float(window.sum()) / float(elapsed[index])
        discounted[index] = float(
            (np.power(gamma, np.arange(window.size, dtype=np.float64)) * window).sum())
    agreement = float(np.max(np.abs(discounted - stored))) if rows else 0.
    if agreement > DISCOUNTED_AGREEMENT_TOLERANCE:
        raise ValueError(
            f"the taped rewards do not reproduce the buffer's own discounted commitment reward "
            f"(max |difference| {agreement})")

    position = np.zeros(rows, dtype=np.int64)
    for key in np.unique(lane):
        mask = lane == key
        order = np.argsort(steps[mask], kind="stable")
        ranks = np.empty(int(mask.sum()), dtype=np.int64)
        ranks[order] = np.arange(int(mask.sum()), dtype=np.int64)
        position[mask] = ranks
    counts = np.stack([(labels == label).sum(axis=1) for label in range(n_labels)],
                      axis=1).astype(np.float64)
    if not np.array_equal(counts.sum(axis=1), np.full(rows, float(labels.shape[1]))):
        raise ValueError("a commitment's label counts do not sum to the team size")
    return {"rows": rows, "lane": lane, "start": steps, "elapsed": elapsed, "labels": labels,
            "counts": counts, "position": position, "response": response,
            "clusters": lane.astype(np.int64),  # one lane-episode is one cluster
            "n_agents": int(labels.shape[1]),
            "n_positions": int(math.ceil(float(horizon) / float(cap))),
            "discounted_agreement_max_abs": agreement,
            "mean_reward_per_step": float(rewards.mean()) if rewards.size else None}


# ---------------------------------------------------------------------------
# the fit: the estimator hook, the panel fan-out and the refusals
# ---------------------------------------------------------------------------


@contextmanager
def forbid_coordinator_steps(agent):
    """Make every coordinator optimizer step raise; the other optimizers step normally."""
    optimizer = getattr(agent, "coordinator_optimizer", None)
    if optimizer is None:
        raise ValueError("the learner has no coordinator optimizer to hold still")
    original = optimizer.step

    def refuse(*args, **kwargs):
        raise RuntimeError(
            "the coordinator optimizer took a step; this object runs with "
            f"{DECLARED_FIELD} = True and the coordinator must not be updated")

    optimizer.step = refuse
    try:
        yield original
    finally:
        optimizer.step = original


def action_standard_deviation(agent):
    """The low level's own per-dimension action standard deviation, read after an update."""
    try:
        values, note = b08.action_standard_deviation(agent.skill_discoverer.actor)
    except (AttributeError, ValueError) as exc:
        return {"action_standard_deviation": None, "reason": str(exc)}
    values = np.asarray(values, dtype=np.float64)
    return {"action_standard_deviation": values.tolist(),
            "action_standard_deviation_mean": float(values.mean()) if values.size else None,
            "head": note["head"], "definition": note["definition"]}


@contextmanager
def estimator_hook(agent):
    """Wrap the learner's own `update`: the frozen call first, then this rollout's estimate."""
    if "update" in agent.__dict__:
        raise ValueError("the learner already carries an instance-level `update`")
    original = agent.update

    def update(*args, **kwargs):
        losses = original(*args, **kwargs)
        estimate_after_rollout(losses)
        return losses

    agent.update = update  # an instance attribute only; the class is untouched
    try:
        yield original
    finally:
        agent.__dict__.pop("update", None)


def _finite_or_none(value):
    """A loss the frozen update returned, as a float, or None; never a reason to fail a fit."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def estimate_after_rollout(losses=None):
    """One rollout's estimate, law and record; called inside the learner's own `update` wrapper.

    `losses` is the frozen update's own return value, passed through unchanged; the two
    discriminator accuracies are copied into the record so `bandit.jsonl` is self-contained. The
    collector writes the same dictionary to `training_rows[-1]['losses']` a moment later.
    """
    arm, agent = CURRENT["arm"], CURRENT["agent"]
    rule, tape, estimator = CURRENT["rule"], CURRENT["tape"], CURRENT["estimator"]
    summary, out, counters = CURRENT["summary"], CURRENT["out"], CURRENT["counters"]
    horizon = int(shared.HORIZON)
    calls = shared.optimizer_counts(counters)
    if calls["coordinator"] != 0:
        raise RuntimeError(f"the coordinator took {calls['coordinator']} optimizer steps")
    if any(calls[name] <= 0 for name in ("discoverer_actor", "discoverer_critic")):
        raise RuntimeError("the discoverer did not take an optimizer step in this rollout")
    rewards = tape.drain(horizon)
    executed = rule.drain()
    commitments = rollout_commitments(agent, rewards, executed, horizon=horizon,
                                      lanes=int(shared.TRAIN_LANES))
    law_used, source_used = rule.law.copy(), rule.law_source
    fit = estimator.update(commitments, n_positions=commitments["n_positions"])
    law_next, source_next = label_law(estimator, arm)
    rule.set_law(law_next, source_next)
    rollout = int(estimator.rollouts_seen)
    counts = commitments["counts"].sum(axis=0)
    shares = counts / counts.sum() if counts.sum() else counts
    executed_counts = rule.histogram.copy()
    record = {
        "rollout": rollout,
        "arm": arm,
        "commitments": int(commitments["rows"]),
        "commitment_label_counts": counts.astype(np.int64).tolist(),
        "label_shares": shares.tolist(),
        "largest_label_share": float(shares.max()) if shares.size else None,
        "most_executed_label": int(np.argmax(shares)) if shares.size else None,
        "executed_label_entropy": float(
            -np.sum(shares[shares > 0.] * np.log(shares[shares > 0.]))) if shares.size else None,
        "cumulative_executed_label_counts": executed_counts.tolist(),
        "q_used": law_used.tolist(), "q_used_source": source_used,
        "q_next": np.asarray(law_next, dtype=np.float64).tolist(), "q_next_source": source_next,
        "argmax_q_next": int(np.argmax(law_next)),
        "estimate": estimator.state(),
        "rollout_fit": fit,
        "discounted_agreement_max_abs": commitments["discounted_agreement_max_abs"],
        "mean_reward_per_step": commitments["mean_reward_per_step"],
        "optimizer_calls": calls,
        "draws": int(rule.draws), "replaced_positions": int(rule.replaced),
        "discriminator_team_accuracy": _finite_or_none(
            (losses or {}).get("discriminator_team_accuracy")),
        "discriminator_individual_accuracy": _finite_or_none(
            (losses or {}).get("discriminator_individual_accuracy")),
    }
    record.update(action_standard_deviation(agent))
    record = shared.measured(record, "label bandit record")
    if summary is not None and summary.get("training_rows"):
        row = summary["training_rows"][-1]
        if int(row.get("rollout_index", -1)) != rollout - 1:
            raise ValueError("the estimator is not attached to the rollout that just collected")
        row["label_bandit"] = record
    if out is not None:
        with (Path(out) / "bandit.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, allow_nan=False) + "\n")
    return record


def save_final_weights(agent, summary, out):
    """B08's own weights sidecar, with this object's identity; only ever after a complete fit.

    The writer, the file names, the sha256 and the checkpoint inventory are B08's
    (`run_fsd_label_content_b08.save_final_weights`); only the recorded object, arm and law belong
    to this object, so a later probe cannot mistake one object's checkpoint for the other's.
    """
    if summary.get("status") != "complete":
        raise ValueError("a fit that is not complete saves no weights")
    path = Path(out) / WEIGHTS_NAME
    pending = Path(out) / (WEIGHTS_NAME + ".pending")
    agent.save_model(str(pending))
    # Digest and inventory are read under the pending name, so a failure here leaves no file that
    # could be taken for a checkpoint; the rename is atomic and the sidecar follows it at once.
    digest, size = b08.file_sha256(pending), int(pending.stat().st_size)
    inventory = b08.checkpoint_inventory(pending)
    pending.replace(path)
    record = {
        "object_id": OBJECT_ID, "file": WEIGHTS_NAME,
        "sha256": digest, "bytes": size,
        "launch_sha": summary.get("launch_sha"), "block_seed": summary.get("block_seed"),
        "training_seed": summary.get("training_seed"),
        "evaluation_seed": summary.get("evaluation_seed"),
        "arm": summary.get("label_bandit_arm"), "rollouts": summary.get("rollouts"),
        "final_law": (summary.get("label_bandit_final") or {}).get("final_law"),
        "argmax_beta_hat": (summary.get("label_bandit_final") or {}).get("argmax_beta_hat"),
        "saved_after": ("run_fit returned complete: the frozen collector loop, its updates and "
                        f"the rollout-{summary.get('rollouts')} panels had all finished"),
        "writer": "hmasd/agent.py:7351 HMASDAgent.save_model",
        "inventory": inventory}
    shared.write_json(Path(out) / SIDECAR_NAME, record)
    return record


def panel_names(rollouts_completed, label):
    """The declared panels of one boundary: (recorded rule name, the rule that is executed)."""
    names = [(SCHEDULE_RULE, b09.constant_rule(int(label))), (REFERENCE_RULE, REFERENCE_RULE)]
    if int(rollouts_completed) == int(ROLLOUTS):
        names += [(name, name) for name in FINAL_MAP_RULES]
    return names


def evaluate_panel(learner, evaluator, summary, out, rollouts_completed):
    """One frozen panel call, fanned out into this object's declared panels at that boundary."""
    if CURRENT["arm"] is None:  # not inside a bound fit: the frozen panel, unchanged
        return _orig_evaluate_panel(learner, evaluator, summary, out, rollouts_completed)
    estimator = CURRENT["estimator"]
    label = estimator.argmax_label()
    state = estimator.state()
    names = panel_names(rollouts_completed, label)
    schedule_panel = None
    b01.evaluate_panel = _orig_evaluate_panel  # the fan-out runs the frozen panel itself
    try:
        with b09.bound_rules():
            for index, (name, executed) in enumerate(names):
                record = b09.run_rule_panel(
                    executed, learner, evaluator, summary, out, rollouts_completed,
                    evaluation_seed=summary["evaluation_seed"])
                panel = summary["panels"][-1]
                schedule = index == 0
                if schedule:
                    schedule_panel = panel
                else:
                    summary["panels"].pop()
                    summary["extra_panels"].append(panel)
                entry = {"panel_rollouts": int(rollouts_completed), "rule": name,
                         "executed_rule": executed, "schedule_slot": bool(schedule),
                         "constant_label": b09.constant_label(executed),
                         "estimate": state}
                entry.update({key: record[key] for key in (
                    "J_mean", "J_world_scores", "J_world_sd", "returns_U", "component_means",
                    "decision_steps", "steps", "decision_fraction", "agent_label_histogram",
                    "team_label_histogram", "agent_label_change_fraction",
                    "evaluator_optimizer_calls", "definition") if key in record})
                summary["panel_runs"].append(entry)
            if int(rollouts_completed) == int(ROLLOUTS) and schedule_panel is not None:
                # The frozen panel assigns these on every call at the last boundary
                # (run_fsd_baseline_interruption_b01.py:259-261); the schedule slot owns them.
                summary["evaluation"] = schedule_panel
                summary["evaluation_optimizer_calls"] = schedule_panel["evaluator_optimizer_calls"]
    finally:
        b01.evaluate_panel = evaluate_panel
    shared.publish(out, summary, f"panel {rollouts_completed} fan-out")


def build_learner(arm, summary, out, training_seed):
    """The frozen learner construction, with this object's law, tape and estimator attached to it.

    The one point at which this object reaches the learner agent and its training lanes: the frozen
    `build_learner` runs first and unchanged, and the agent it returns is the one the frozen
    collector then steps.
    """
    envs, agent, theta0, counters = _orig_build_learner(arm, summary, out, training_seed)
    if CURRENT["arm"] is not None:
        stack = CURRENT["stack"]
        tape = RolloutRewardTape(envs)
        stack.enter_context(tape.attached())
        rule = LabelBanditRule(arm, agent, generator=label_generator(training_seed, arm))
        estimator = LabelEstimator()
        law, source = label_law(estimator, arm)
        rule.set_law(law, source)
        stack.enter_context(rule.attached())
        stack.enter_context(estimator_hook(agent))
        stack.enter_context(forbid_coordinator_steps(agent))
        CURRENT.update(agent=agent, tape=tape, rule=rule, estimator=estimator, counters=counters,
                       out=out)
        summary["label_bandit"] = rule.provenance() | {
            "commitment_cap": COMMITMENT_CAP,
            "ema_weight": EMA_WEIGHT, "variance_weight": EMA_WEIGHT ** 2,
            "new_weight": NEW_WEIGHT, "new_variance_weight": NEW_WEIGHT ** 2,
            "exploit_weight": EXPLOIT_WEIGHT, "floor_weight": FLOOR_WEIGHT,
            "label_floor": LABEL_FLOOR, "softmax_temperature": SOFTMAX_TEMPERATURE,
            "standard_error_floor": STANDARD_ERROR_FLOOR,
            "training_seed": int(training_seed),
            "estimator": SOURCE_NOTES["estimator_hook"],
            "regression": SOURCE_NOTES["regression"],
            "z_denominator": SOURCE_NOTES["z_denominator"],
            "rank_deficiency": SOURCE_NOTES["rank_deficiency"],
            "per_step_reward": SOURCE_NOTES["per_step_reward"],
            "commitments": SOURCE_NOTES["commitments"],
            "coordinator_steps": SOURCE_NOTES["coordinator_steps"],
            "panels": SOURCE_NOTES["panels"], "panel_rng": SOURCE_NOTES["panel_rng"],
            "best_estimate_rule": SOURCE_NOTES["best_estimate_rule"]}
        shared.publish(out, summary, "label bandit attached")
    return envs, agent, theta0, counters


def base_summary(*args, **kwargs):
    summary = _orig_base_summary(*args, **kwargs)
    arm = CURRENT["arm"]
    summary.update(label_bandit_object=OBJECT_ID, label_bandit_arm=arm,
                   arm_overrides=dict(ARM_OVERRIDES.get(arm, {})),
                   declared_config_difference=None, skill_period_k=SKILL_PERIOD,
                   commitment_cap=COMMITMENT_CAP, admission=CURRENT["admission"],
                   primary=PRIMARY_NAME, final_weights=None, extra_panels=[], panel_runs=[],
                   panel_rules={"schedule": SCHEDULE_RULE, "reference": REFERENCE_RULE,
                                "final_map": list(FINAL_MAP_RULES)},
                   label_bandit=None,
                   learner_config_differences_from_recorded_d1280=None,
                   evaluation_config_differences_from_recorded_d1280=None)
    CURRENT["summary"] = summary
    return summary


setattr(base_summary, _FLAG, True)


def plan_guard(arm, seed):
    """The notebook entry's six fits: both arms on the three blocks."""
    if arm not in ARMS:
        raise SystemExit(f"unknown arm {arm}")
    if seed not in BLOCKS:
        raise SystemExit("this object runs on blocks 772803, 772903 and 773003")


def expected_panels():
    """Every panel a complete fit runs: two per boundary, and the six constants at the last one."""
    return 2 * len(PANEL_ROLLOUTS) + N_LABELS


def check_fit_refusals(summary):
    """The run-time refusals this object declares, checked once the fit has returned complete."""
    calls = summary.get("optimizer_calls") or {}
    if calls.get("coordinator") != 0:
        raise ValueError(f"the coordinator took {calls.get('coordinator')} optimizer steps")
    if any(int(calls.get(name, 0)) <= 0 for name in ("discoverer_actor", "discoverer_critic")):
        raise ValueError("the discoverer took no optimizer step")
    if any(int(calls.get(name, 0)) <= 0 for name in ("team_discriminator",
                                                     "individual_discriminator")):
        raise ValueError("a discriminator took no optimizer step")
    for phase in ("learner_config", "evaluation_config"):
        config = summary.get(phase) or {}
        if config.get("interruption_cost_c") != "Infinity" or config.get(
                "interruption_cost_c_Z") != "Infinity":
            raise ValueError(f"{phase} does not carry infinite interruption costs")
        if config.get("age_feature") != "off":
            raise ValueError(f"{phase} does not carry `age_feature = off`")
    declared = summary.get("declared_config_difference") or {}
    if declared.get("field") != DECLARED_FIELD or declared.get("fit") is not True:
        raise ValueError("the fit does not record its one declared configuration difference")
    rows = summary.get("training_rows") or []
    records = [row.get("label_bandit") for row in rows]
    if len(records) != ROLLOUTS or any(record is None for record in records):
        raise ValueError("the fit does not carry one label-bandit record per rollout")
    runs = summary.get("panel_runs") or []
    if len(runs) != expected_panels():
        raise ValueError(f"the fit ran {len(runs)} panels, not the declared {expected_panels()}")
    for entry in runs:
        if entry["rule"] != SCHEDULE_RULE:
            continue
        histogram = [int(value) for value in entry["agent_label_histogram"]]
        label = int(entry["estimate"]["argmax_beta_hat"])
        elsewhere = {index: value for index, value in enumerate(histogram)
                     if index != label and value}
        if elsewhere or not histogram[label]:
            raise ValueError(
                f"the {SCHEDULE_RULE} panel at rollout {entry['panel_rollouts']} executed labels "
                f"other than argmax beta_hat {label}: {histogram}")
    return True


def run_fit(arm, seed, out, admission=None):
    plan_guard(arm, seed)
    bind(wrap=True)
    CURRENT.update(arm=arm, admission=admission, agent=None, rule=None, estimator=None,
                   tape=None, counters=None, out=None)
    stack = ExitStack()
    CURRENT["stack"] = stack
    try:
        status = b01.run_fit(arm, seed, out)
        summary, agent = CURRENT.get("summary"), CURRENT.get("agent")
        if status == 0 and (summary is None or agent is None):
            raise RuntimeError("the frozen fit returned complete but this object's wrappers saw no "
                               "summary or learner, so none of its refusals could run")
        if status == 0:
            try:
                # Nothing above this line touched the learner; the frozen fit is over.
                check_fit_refusals(summary)
                summary["label_bandit_final"] = CURRENT["estimator"].state() | {
                    "skipped_rollouts": [record for record in CURRENT["estimator"].skipped],
                    "final_law": CURRENT["rule"].law.tolist(),
                    "final_law_source": CURRENT["rule"].law_source,
                    "executed_label_counts": CURRENT["rule"].histogram.tolist(),
                    "decision_label_counts": CURRENT["rule"].decision_histogram.tolist(),
                    "draws": int(CURRENT["rule"].draws)}
                summary["final_weights"] = save_final_weights(agent, summary, out)
                shared.publish(out, summary, "final weights written")
            except Exception as exc:  # a refusal after a complete fit is still a failed fit
                summary["status"] = "incomplete"
                summary["failure"] = f"{type(exc).__name__}: {exc}"
                shared.write_json(Path(out) / "summary.json", summary)
                print(json.dumps({"arm": arm, "seed": seed, "status": summary["status"],
                                  "failure": summary["failure"]}))
                return 1
        return status
    finally:
        stack.close()
        CURRENT.update(arm=None, admission=None, summary=None, agent=None, rule=None,
                       estimator=None, tape=None, stack=None, counters=None, out=None)
        if shared.base_summary is base_summary:
            shared.base_summary = _orig_base_summary
        if b01.build_learner is build_learner:
            b01.build_learner = _orig_build_learner
        if b01.evaluate_panel is evaluate_panel:
            b01.evaluate_panel = _orig_evaluate_panel


# ---------------------------------------------------------------------------
# reading one fit
# ---------------------------------------------------------------------------


def bandit_panels(summary):
    """The frozen B01 panel reader's law, with this object's fanned-out evaluation exposure.

    `run_fsd_baseline_interruption_b01.arm_panels` expects one panel per boundary and a positive
    coordinator count (line 332), neither of which a fit of this object has: it runs two panels at
    every boundary and six more at the last, and its coordinator is switched off. Everything else
    is the frozen reader's own check, in its order: identity, exposure counts, learner updates,
    per-phase construction, lane seeds and the per-panel primary.
    """
    seed, arm = summary["block_seed"], summary["factorial_arm"]
    if arm not in ARMS:
        raise ValueError("not one of this object's arms")
    renewal, batch = ARMS[arm]
    evaluation_seed = BLOCKS[seed]
    lanes, horizon = shared.EVAL_LANES, shared.HORIZON
    panels = expected_panels()
    if (summary["object_id"] != OBJECT_ID or summary["card"] != CARD or summary["arm"] != renewal
            or summary["status"] != "complete" or summary["training_seed"] != seed
            or summary["evaluation_seed"] != evaluation_seed or summary["rollouts"] != ROLLOUTS
            or summary["panel_rollouts"] != list(PANEL_ROLLOUTS)):
        raise ValueError("incomplete or wrong arm/block/object")
    counts = summary["counts"]
    expected_counts = {
        "model_constructions": 2, "training_starts": 1, "checkpoint_loads": 0,
        "training_transitions": shared.TRAIN_LANES * horizon * ROLLOUTS,
        "stored_training_transitions": shared.TRAIN_LANES * horizon * ROLLOUTS,
        "training_episodes": shared.TRAIN_LANES * ROLLOUTS, "update_stages": ROLLOUTS,
        "training_agent_step_batches": horizon * ROLLOUTS,
        "evaluation_steps": lanes * horizon * panels,
        "evaluation_agent_step_batches": horizon * panels,
        "evaluation_episodes": lanes * panels}
    if any(counts[k] != v for k, v in expected_counts.items()):
        raise ValueError("incomplete training/panel exposure")
    rows = summary["training_rows"]
    if (len(rows) != ROLLOUTS or [r["rollout_index"] for r in rows] != list(range(ROLLOUTS))
            or not all(r["updated"] for r in rows)
            or any(summary["optimizer_calls"][k] <= 0
                   for k in ("discoverer_actor", "discoverer_critic"))):
        raise ValueError("missing learner updates")
    if summary["optimizer_calls"]["coordinator"] != 0:
        raise ValueError("this object's arms run with the coordinator's update switched off")
    for key, count, phase_seed in (("learner_config", shared.TRAIN_LANES, seed),
                                   ("evaluation_config", lanes, evaluation_seed)):
        config = summary[key]
        expected = {"n_agents": shared.N_UAVS, "n_users": shared.N_USERS, "num_envs": count,
                    "rollout_length": horizon, "seed": phase_seed,
                    "policy_interruption_mode": "d2", "interruption_cost_c_Z": "Infinity",
                    "interruption_cost_c": "Infinity", "interruption_delta": 1,
                    "age_feature": "off", "n_Z": N_LABELS, "n_z": N_LABELS, "k": SKILL_PERIOD,
                    "skill_cap_k_max": ARM_CAPS[0], "team_cap_k_Z": ARM_CAPS[1],
                    "coordinator_batch_size": batch}
        if any(config.get(name) != value for name, value in expected.items()):
            raise ValueError("arm construction mismatch: " + key)
    if (summary["training_lane_seeds"] != list(range(seed, seed + shared.TRAIN_LANES))
            or summary["evaluation_lane_seeds"] != list(
                range(evaluation_seed, evaluation_seed + lanes))
            or [p["panel_rollouts"] for p in summary["panels"]] != list(PANEL_ROLLOUTS)):
        raise ValueError("wrong lane seeds or panel schedule")
    scores = {}
    for panel in summary["panels"]:
        if (panel["status"] != "complete" or panel["after_update"] != panel["panel_rollouts"]
                or panel["episode_ids"] != list(range(lanes))
                or panel["lane_seeds"] != summary["evaluation_lane_seeds"]
                or panel["steps_per_lane"] != [horizon] * lanes
                or panel["completed_episodes"] != lanes
                or any(panel["evaluator_optimizer_calls"].values())):
            raise ValueError(f"wrong panel {panel['panel_rollouts']}")
        values = np.asarray(panel["native_scores_J"], dtype=np.float64)
        returns = np.asarray(panel["returns_U"], dtype=np.float64)
        if values.shape != (lanes,) or returns.shape != values.shape:
            raise ValueError("missing primary values")
        shared.require_finite((values, returns), "panel primary")
        if not np.allclose(returns * shared.N_UAVS / horizon, values, rtol=1e-9, atol=1e-9):
            raise ValueError("native return scaling mismatch")
        scores[panel["panel_rollouts"]] = values
    return scores


def panel_scores(summary):
    """Every panel this fit ran, as {rule: {boundary: mean J}} and the world scores beside them."""
    means, worlds = {}, {}
    for entry in summary.get("panel_runs") or []:
        rule, boundary = entry["rule"], int(entry["panel_rollouts"])
        means.setdefault(rule, {})[boundary] = float(entry["J_mean"])
        worlds.setdefault(rule, {})[boundary] = [float(v) for v in entry["J_world_scores"]]
    return means, worlds


def fit_endpoint(summary, recorded=None):
    """Validated per-panel world scores of one complete fit of this object."""
    bind()
    if summary.get("label_bandit_object") != OBJECT_ID:
        raise ValueError("not a label-bandit fit")
    arm = summary.get("label_bandit_arm")
    if arm not in ARMS or int(summary.get("block_seed", -1)) not in BLOCKS:
        raise ValueError("not one of this object's six planned fits")
    if summary.get("factorial_arm") != arm:
        raise ValueError("the recorded arm name and the frozen runner's arm disagree")
    if summary.get("arm_overrides") != ARM_OVERRIDES[arm]:
        raise ValueError(f"{arm} does not record its declared override")
    scores = bandit_panels(summary)
    check_fit_refusals(summary)
    means, _worlds = panel_scores(summary)
    for rule in (SCHEDULE_RULE, REFERENCE_RULE):
        if sorted(means.get(rule, {})) != list(PANEL_ROLLOUTS):
            raise ValueError(f"the fit does not carry a {rule} panel at every boundary")
    for rule in FINAL_MAP_RULES:
        if sorted(means.get(rule, {})) != [ROLLOUTS]:
            raise ValueError(f"the fit does not carry a {rule} panel at rollout {ROLLOUTS}")
    # the schedule slot is the `best_estimate` panel: the frozen reader's scores are its scores
    for boundary in PANEL_ROLLOUTS:
        if abs(float(np.mean(scores[boundary])) - means[SCHEDULE_RULE][boundary]) > 0.:
            raise ValueError(f"the schedule slot at rollout {boundary} is not {SCHEDULE_RULE}")
    if recorded is not None:
        for phase in ("learner_config", "evaluation_config"):
            require_recorded_construction(summary[phase], recorded[phase], phase, arm)
    return scores


def bandit_rows(summary):
    """The per-rollout label-bandit records of one fit, in rollout order."""
    records = [row["label_bandit"] for row in summary["training_rows"]]
    if [int(record["rollout"]) for record in records] != list(range(1, ROLLOUTS + 1)):
        raise ValueError("the label-bandit records are not one per rollout in order")
    return records


def label_map(means):
    """The arm's own label-to-J map at rollout 45, from its six constant panels."""
    return {label: float(means[b09.constant_rule(label)][ROLLOUTS]) for label in range(N_LABELS)}


def map_ranking(values):
    """Every label from the highest to the lowest panel J, the lowest label breaking a tie."""
    return [int(label) for label in sorted(values, key=lambda label: (-values[label], label))]


def law_history(records):
    """The per-rollout law, estimate and executed shares, and the readings the entry asks for."""
    shares = [float(record["largest_label_share"]) for record in records]
    argmax_beta = [int(record["estimate"]["argmax_beta_hat"]) for record in records]
    argmax_q = [int(record["argmax_q_next"]) for record in records]
    available = [bool(record["estimate"]["estimate_available"]) for record in records]
    first_above = next((index + 1 for index, value in enumerate(shares)
                        if value > SHARE_THRESHOLD), None)
    changes = lambda series: int(sum(1 for index in range(ALTERNATIVE_AFTER, len(series))
                                     if series[index] != series[index - 1]))
    return {
        "largest_label_share_by_rollout": shares,
        "label_shares_by_rollout": [list(record["label_shares"]) for record in records],
        "executed_label_entropy_by_rollout": [record["executed_label_entropy"]
                                              for record in records],
        "first_rollout_largest_share_above_threshold": first_above,
        "share_threshold": SHARE_THRESHOLD,
        "argmax_beta_hat_by_rollout": argmax_beta,
        "argmax_q_by_rollout": argmax_q,
        "estimate_available_by_rollout": available,
        "law_source_by_rollout": [record["q_next_source"] for record in records],
        "rank_deficient_rollouts": [int(record["rollout"]) for record in records
                                    if record["rollout_fit"]["rank_deficient"]],
        "rollouts_used_by_rollout": [int(record["estimate"]["rollouts_used"])
                                     for record in records],
        "argmax_beta_hat_changes_after_15": changes(argmax_beta),
        "argmax_q_changes_after_15": changes(argmax_q),
        "changes_definition": (
            f"the number of rollouts after rollout {ALTERNATIVE_AFTER} at which the label differs "
            "from the previous rollout's; the primary series is `argmax beta_hat`, which is the "
            f"label `{SCHEDULE_RULE}` deploys, and the law's own `argmax q` is reported beside it"),
        "final_estimate": records[-1]["estimate"],
        "final_q": list(records[-1]["q_next"]),
        "action_standard_deviation_by_rollout": [record.get("action_standard_deviation_mean")
                                                 for record in records],
        "discriminator_team_accuracy_by_rollout": None,
        "discriminator_individual_accuracy_by_rollout": None}


def fit_row(summary, scores):
    """One fit's readings: the panels by rule, the law's history and the fit's own exposure."""
    means, worlds = panel_scores(summary)
    records = bandit_rows(summary)
    history = law_history(records)
    rows = summary["training_rows"]
    history["discriminator_team_accuracy_by_rollout"] = [
        (row.get("losses") or {}).get("discriminator_team_accuracy") for row in rows]
    history["discriminator_individual_accuracy_by_rollout"] = [
        (row.get("losses") or {}).get("discriminator_individual_accuracy") for row in rows]
    values = label_map(means)
    ranking = map_ranking(values)
    final = int(records[-1]["estimate"]["argmax_beta_hat"])
    late = lambda rule: float(np.mean([means[rule][r] for r in LATE_PANELS]))
    return {
        "arm": summary["label_bandit_arm"], "block_seed": int(summary["block_seed"]),
        "object_id": summary["object_id"], "launch_sha": summary["launch_sha"],
        "J_by_rollout": {rule: {str(r): means[rule][r] for r in sorted(means[rule])}
                         for rule in (SCHEDULE_RULE, REFERENCE_RULE)},
        "J_late_window": {rule: late(rule) for rule in (SCHEDULE_RULE, REFERENCE_RULE)},
        "late_window_panels": list(LATE_PANELS),
        f"J_{ROLLOUTS}": {rule: means[rule][ROLLOUTS] for rule in (SCHEDULE_RULE, REFERENCE_RULE)},
        "endpoint_scores_J": {rule: worlds[rule][ROLLOUTS]
                              for rule in (SCHEDULE_RULE, REFERENCE_RULE)},
        f"{SCHEDULE_RULE}_minus_{REFERENCE_RULE}": {
            str(r): means[SCHEDULE_RULE][r] - means[REFERENCE_RULE][r] for r in PANEL_ROLLOUTS},
        "label_map_J": {str(label): values[label] for label in range(N_LABELS)},
        "label_map_ranking": ranking,
        "best_label_in_the_map": ranking[0],
        "final_argmax_beta_hat": final,
        "rank_of_argmax_beta_hat_in_the_map": ranking.index(final) + 1,
        "map_spread": values[ranking[0]] - values[ranking[-1]],
        "schedule_slot_matches_its_constant_panel": bool(
            means[SCHEDULE_RULE][ROLLOUTS] == means[b09.constant_rule(final)][ROLLOUTS]),
        "law": history,
        "final_state": summary.get("label_bandit_final"),
        "declared_config_difference": summary.get("declared_config_difference"),
        "counts": summary["counts"], "optimizer_calls": summary["optimizer_calls"],
        "wall_seconds_before_publication": summary.get("wall_seconds_before_publication"),
        "peak_rss_bytes": summary.get("peak_rss_bytes"),
        "weights": (summary.get("final_weights") or {}).get("sha256")}


def reference_row(summary, scores):
    """A published stage-1 D1280 fit, read by its own object's validator."""
    level = {r: float(np.mean(scores[r])) for r in PANEL_ROLLOUTS}
    return {"J_by_rollout": {str(r): level[r] for r in PANEL_ROLLOUTS},
            f"J_{ROLLOUTS}": level[ROLLOUTS],
            "J_late_window": float(np.mean([level[r] for r in LATE_PANELS])),
            "late_window_panels": list(LATE_PANELS),
            "endpoint_scores_J": np.asarray(scores[ROLLOUTS], dtype=np.float64).tolist(),
            "object_id": summary["object_id"], "launch_sha": summary["launch_sha"],
            "arm": D_REFERENCE, "counts": summary["counts"],
            "optimizer_calls": summary["optimizer_calls"]}


def b09_row(summary):
    """B09's own probe of the same block: its best constant label on the D1280 weights."""
    row = b09.probe_row(summary)  # refuses an incomplete, unfaithful or short probe
    baseline = float(row["J_by_rule"][b09.BASELINE_RULE])
    best = b09.best_constant(row["J_by_rule"], baseline)
    return {"block_seed": row["block_seed"], "launch_sha": row["launch_sha"],
            "weights_sha256": row["weights_sha256"],
            "as_trained_J": baseline, "best_constant": best,
            "best_constant_label": int(best["label"]), "best_constant_J": float(best["J"]),
            "J_by_rule": row["J_by_rule"]}


# ---------------------------------------------------------------------------
# reduce
# ---------------------------------------------------------------------------


def block_reading(rows, reference, b09_reading):
    """One block: both arms beside the published D1280 fit and B09's best constant on its weights."""
    reading = {"arms": {}, "reference": reference, "b09": b09_reading}
    for arm, row in rows.items():
        entry = {
            "J_by_rollout": row["J_by_rollout"],
            f"J_{ROLLOUTS}": row[f"J_{ROLLOUTS}"],
            "J_late_window": row["J_late_window"],
            f"{SCHEDULE_RULE}_minus_{REFERENCE_RULE}_J{ROLLOUTS}": (
                row[f"J_{ROLLOUTS}"][SCHEDULE_RULE] - row[f"J_{ROLLOUTS}"][REFERENCE_RULE]),
            f"{SCHEDULE_RULE}_minus_{REFERENCE_RULE}_late_window": (
                row["J_late_window"][SCHEDULE_RULE] - row["J_late_window"][REFERENCE_RULE]),
            "label_map_J": row["label_map_J"], "label_map_ranking": row["label_map_ranking"],
            "final_argmax_beta_hat": row["final_argmax_beta_hat"],
            "rank_of_argmax_beta_hat_in_the_map": row["rank_of_argmax_beta_hat_in_the_map"],
            "map_spread": row["map_spread"],
            "schedule_slot_matches_its_constant_panel":
                row["schedule_slot_matches_its_constant_panel"],
            "largest_label_share_by_rollout": row["law"]["largest_label_share_by_rollout"],
            "first_rollout_largest_share_above_threshold":
                row["law"]["first_rollout_largest_share_above_threshold"],
            "argmax_beta_hat_by_rollout": row["law"]["argmax_beta_hat_by_rollout"],
            "argmax_beta_hat_changes_after_15": row["law"]["argmax_beta_hat_changes_after_15"],
            "argmax_q_changes_after_15": row["law"]["argmax_q_changes_after_15"],
            "rank_deficient_rollouts": row["law"]["rank_deficient_rollouts"],
            "executed_label_entropy_by_rollout": row["law"]["executed_label_entropy_by_rollout"],
            "action_standard_deviation_by_rollout": row["law"][
                "action_standard_deviation_by_rollout"],
            "discriminator_team_accuracy_by_rollout": row["law"][
                "discriminator_team_accuracy_by_rollout"],
            "discriminator_individual_accuracy_by_rollout": row["law"][
                "discriminator_individual_accuracy_by_rollout"],
            "final_estimate": row["law"]["final_estimate"],
            "wall_seconds_before_publication": row["wall_seconds_before_publication"],
            "peak_rss_bytes": row["peak_rss_bytes"]}
        if reference is not None:
            entry[f"{SCHEDULE_RULE}_minus_d1280_J{ROLLOUTS}"] = (
                row[f"J_{ROLLOUTS}"][SCHEDULE_RULE] - reference[f"J_{ROLLOUTS}"])
            entry[f"{SCHEDULE_RULE}_minus_d1280_late_window"] = (
                row["J_late_window"][SCHEDULE_RULE] - reference["J_late_window"])
            entry[f"{REFERENCE_RULE}_minus_d1280_J{ROLLOUTS}"] = (
                row[f"J_{ROLLOUTS}"][REFERENCE_RULE] - reference[f"J_{ROLLOUTS}"])
        if b09_reading is not None:
            entry[f"{SCHEDULE_RULE}_minus_b09_best_constant_J{ROLLOUTS}"] = (
                row[f"J_{ROLLOUTS}"][SCHEDULE_RULE] - b09_reading["best_constant_J"])
            entry["b09_best_constant_label"] = b09_reading["best_constant_label"]
            entry["final_argmax_is_b09_best_constant"] = bool(
                row["final_argmax_beta_hat"] == b09_reading["best_constant_label"])
        reading["arms"][arm] = entry
    if set(rows) == set(ARMS):
        reading["bandit_minus_uniform"] = {
            f"J{ROLLOUTS}_{SCHEDULE_RULE}": (
                rows[BANDIT_ARM][f"J_{ROLLOUTS}"][SCHEDULE_RULE]
                - rows[UNIFORM_ARM][f"J_{ROLLOUTS}"][SCHEDULE_RULE]),
            f"late_window_{SCHEDULE_RULE}": (
                rows[BANDIT_ARM]["J_late_window"][SCHEDULE_RULE]
                - rows[UNIFORM_ARM]["J_late_window"][SCHEDULE_RULE]),
            f"J{ROLLOUTS}_{REFERENCE_RULE}": (
                rows[BANDIT_ARM][f"J_{ROLLOUTS}"][REFERENCE_RULE]
                - rows[UNIFORM_ARM][f"J_{ROLLOUTS}"][REFERENCE_RULE]),
            "definition": (
                "the arm difference within a block, on the same 32 evaluation worlds and the same "
                "evaluation seeds, so it is paired within the block; the two arms' training "
                "trajectories are not paired, because the law itself moves the behaviour")}
    else:
        reading["bandit_minus_uniform"] = None
    return reading


def prediction_rows(readings):
    """The notebook entry's four predictions and its strongest alternative, counted where read.

    Arithmetic on the blocks that were read, with the statement each count belongs to. A count is
    not a weight of evidence, and none of these margins is a decision rule.
    """
    arm_of = lambda seed, arm: ((readings.get(seed) or {}).get("arms") or {}).get(arm)
    declared = {
        "P1_bandit_law_leaves_uniform_by_rollout_15": {
            "arm": BANDIT_ARM,
            "statement": ("P1: `BANDIT`'s law leaves uniform: largest label share above "
                          f"{SHARE_THRESHOLD} by rollout {SHARE_ROLLOUT} on 3/3"),
            "value": lambda e: e["first_rollout_largest_share_above_threshold"],
            "holds": lambda value: value is not None and int(value) <= SHARE_ROLLOUT,
            "value_definition": ("the first rollout whose executed agent-label shares have a "
                                 f"largest share above {SHARE_THRESHOLD}, or null if none does")},
        f"P2_argmax_beta_is_in_the_top_two_of_the_map_{BANDIT_ARM}": {
            "arm": BANDIT_ARM,
            "statement": (f"P2: at rollout {ROLLOUTS} argmax beta_hat is among the top two labels "
                          "of the arm's own map, 3/3, both arms (this row is `BANDIT`)"),
            "value": lambda e: e["rank_of_argmax_beta_hat_in_the_map"],
            "holds": lambda value: int(value) <= 2,
            "value_definition": ("the 1-based rank of argmax beta_hat in the arm's own six "
                                 f"constant-label panels at rollout {ROLLOUTS}")},
        f"P2_argmax_beta_is_in_the_top_two_of_the_map_{UNIFORM_ARM}": {
            "arm": UNIFORM_ARM,
            "statement": (f"P2: at rollout {ROLLOUTS} argmax beta_hat is among the top two labels "
                          "of the arm's own map, 3/3, both arms (this row is `UNIFORM`)"),
            "value": lambda e: e["rank_of_argmax_beta_hat_in_the_map"],
            "holds": lambda value: int(value) <= 2,
            "value_definition": ("the 1-based rank of argmax beta_hat in the arm's own six "
                                 f"constant-label panels at rollout {ROLLOUTS}")},
        "P3_bandit_best_estimate_beats_d1280_by_the_margin": {
            "arm": BANDIT_ARM,
            "statement": (f"P3: `BANDIT` `{SCHEDULE_RULE}` J{ROLLOUTS} exceeds D1280 as trained by "
                          f">= {PREDICTION_MARGIN} on at least 2/3"),
            "value": lambda e: e.get(f"{SCHEDULE_RULE}_minus_d1280_J{ROLLOUTS}"),
            "holds": lambda value: value is not None and value >= PREDICTION_MARGIN,
            "value_definition": (f"`{SCHEDULE_RULE}` J at rollout {ROLLOUTS} minus the published "
                                 "stage-1 D1280 fit's J at the same rollout, same block")},
        "P4_bandit_minus_uniform_within_the_band": {
            "arm": None,
            "statement": (f"P4: `BANDIT` minus `UNIFORM` on `{SCHEDULE_RULE}` J{ROLLOUTS} within "
                          f"+/-{PREDICTION_MARGIN} on at least 2/3"),
            "value": lambda block: (block.get("bandit_minus_uniform") or {}).get(
                f"J{ROLLOUTS}_{SCHEDULE_RULE}"),
            "holds": lambda value: value is not None and abs(value) <= PREDICTION_MARGIN,
            "value_definition": (f"`BANDIT` minus `UNIFORM` of `{SCHEDULE_RULE}` J at rollout "
                                 f"{ROLLOUTS}, within the block")},
        "A_the_ranking_drifts_faster_than_the_estimate_follows": {
            "arm": BANDIT_ARM,
            "statement": ("the strongest alternative: the ranking drifts faster than a "
                          "five-rollout average follows, or the ten-step response ranks labels "
                          "myopically, so the most-favoured label changes three or more times "
                          f"after rollout {ALTERNATIVE_AFTER} and `{SCHEDULE_RULE}` is no better "
                          f"than `{REFERENCE_RULE}`"),
            "value": lambda e: {
                "changes_after_15": e["argmax_beta_hat_changes_after_15"],
                f"{SCHEDULE_RULE}_minus_{REFERENCE_RULE}_J{ROLLOUTS}":
                    e[f"{SCHEDULE_RULE}_minus_{REFERENCE_RULE}_J{ROLLOUTS}"]},
            "holds": lambda value: bool(
                value["changes_after_15"] >= ALTERNATIVE_CHANGES
                and value[f"{SCHEDULE_RULE}_minus_{REFERENCE_RULE}_J{ROLLOUTS}"] <= 0.),
            "value_definition": (
                "both clauses together: the number of changes of argmax beta_hat after rollout "
                f"{ALTERNATIVE_AFTER}, and `{SCHEDULE_RULE}` minus `{REFERENCE_RULE}` at rollout "
                f"{ROLLOUTS} on the same worlds")},
    }
    rows = {}
    for name, entry in declared.items():
        per_block = {}
        for seed in sorted(BLOCKS):
            source = (readings.get(seed) if entry["arm"] is None
                      else arm_of(seed, entry["arm"]))
            if source is None:
                per_block[str(seed)] = {"read": False, "holds": None, "value": None}
                continue
            value = entry["value"](source)
            per_block[str(seed)] = {"read": True, "value": value,
                                    "holds": None if value is None else bool(entry["holds"](value))}
        rows[name] = {
            "statement": entry["statement"], "value_definition": entry["value_definition"],
            "arm": entry["arm"], "blocks_considered": [int(seed) for seed in sorted(BLOCKS)],
            "blocks_read": int(sum(row["read"] for row in per_block.values())),
            "blocks_holding": int(sum(bool(row["holds"]) for row in per_block.values())),
            "per_block": per_block}
    # P3's two mean clauses and the late-window clause, which are statements about the mean over
    # blocks rather than per-block counts.
    values = [arm_of(seed, BANDIT_ARM) for seed in sorted(BLOCKS)]
    values = [entry for entry in values if entry is not None]
    endpoint = [entry.get(f"{SCHEDULE_RULE}_minus_d1280_J{ROLLOUTS}") for entry in values]
    late = [entry.get(f"{SCHEDULE_RULE}_minus_d1280_late_window") for entry in values]
    endpoint = [value for value in endpoint if value is not None]
    late = [value for value in late if value is not None]
    rows["P3_mean_over_blocks"] = {
        "statement": (f"P3, continued: the mean over blocks of `BANDIT` `{SCHEDULE_RULE}` "
                      f"J{ROLLOUTS} minus D1280 as trained is >= {MEAN_MARGIN}, and the late "
                      f"window likewise >= {PREDICTION_MARGIN} in the mean"),
        "blocks_read": len(endpoint),
        f"mean_J{ROLLOUTS}_minus_d1280": float(np.mean(endpoint)) if endpoint else None,
        f"mean_J{ROLLOUTS}_clause_holds": (bool(np.mean(endpoint) >= MEAN_MARGIN)
                                           if endpoint else None),
        "mean_late_window_minus_d1280": float(np.mean(late)) if late else None,
        "mean_late_window_clause_holds": (bool(np.mean(late) >= PREDICTION_MARGIN)
                                          if late else None),
        "value_definition": (f"the mean over the blocks read of `{SCHEDULE_RULE}` minus the "
                             f"published D1280 fit, at rollout {ROLLOUTS} and over the late "
                             f"window {list(LATE_PANELS)}")}
    rows["counting_note"] = (
        "the counts are the arithmetic of statements declared before the run, on the blocks that "
        "were read. A count of three blocks is not an interval and not a weight of evidence, and "
        "no margin here is a decision rule; a panel's conditional evaluation noise on this "
        f"direction is about {PANEL_NOISE} J")
    return rows


def reduce_inputs(fits, references, b09_probes):
    """Six fits, the three published D1280 fits and B09's three probes of the same blocks."""
    bind()
    shas = {summary.get("launch_sha") for summary in fits}
    if len(shas) > 1:
        raise ValueError(f"mixed launch shas within the batch: {sorted(str(s) for s in shas)}")
    if None in shas:
        raise ValueError("a fit of the batch records no launch sha")

    recorded, reference_failures, seen = {}, {}, set()
    for summary in references:
        seed = int(summary.get("block_seed", -1))
        try:
            if seed not in BLOCKS:
                raise ValueError("the references are fits of the three blocks")
            if summary.get("factorial_arm") != D_REFERENCE or summary.get("stage") != 1:
                raise ValueError("the references are the published stage-1 D1280 fits")
            values = matched.fit_endpoint(summary)
        except (KeyError, TypeError, ValueError) as exc:
            reference_failures[f"{seed}:{summary.get('factorial_arm')}"] = str(exc)
            bind()
            continue
        bind()  # the reference reader rebinds the frozen runner to its own object
        if seed in seen:
            raise ValueError("duplicate reference block")
        seen.add(seed)
        recorded[seed] = reference_row(summary, values)

    b09_rows, b09_failures, b09_seen = {}, {}, set()
    for summary in b09_probes:
        seed = int(summary.get("block_seed", -1))
        if seed in b09_seen:
            raise ValueError("duplicate B09 probe block")
        b09_seen.add(seed)
        try:
            b09_rows[seed] = b09_row(summary)
        except (KeyError, TypeError, ValueError) as exc:
            b09_failures[seed] = str(exc)
        bind()

    rows, failures, supplied = {}, {}, set()
    for summary in fits:
        seed, arm = int(summary.get("block_seed", -1)), summary.get("label_bandit_arm")
        key = (seed, arm)
        if key in supplied:  # a second fit of the same block and arm is never a choice
            raise ValueError("duplicate block and arm")
        supplied.add(key)
        try:
            if summary.get("label_bandit_object") != OBJECT_ID:
                raise ValueError("not a fit of this object")
            values = fit_endpoint(summary, recorded=None)
            rows[key] = fit_row(summary, values)
        except (KeyError, TypeError, ValueError) as exc:
            failures[f"{seed}:{arm}"] = str(exc)
            bind()
            continue
        bind()

    blocks, readings = [], {}
    for seed in sorted(BLOCKS):
        entry = {"training_seed": seed, "evaluation_seed": BLOCKS[seed], "status": "incomplete",
                 "missing_or_invalid": {}}
        present = {arm: rows[(seed, arm)] for arm in ARMS if (seed, arm) in rows}
        for arm in ARMS:
            if arm not in present:
                entry["missing_or_invalid"][arm] = failures.get(f"{seed}:{arm}", "not supplied")
        if seed not in recorded:
            entry["missing_or_invalid"]["d1280_reference"] = "not supplied or not readable"
        if seed not in b09_rows:
            entry["missing_or_invalid"]["b09_probe"] = b09_failures.get(seed, "not supplied")
        entry.update(block_reading(present, recorded.get(seed), b09_rows.get(seed)))
        if len(present) == len(ARMS) and seed in recorded and seed in b09_rows:
            entry["status"] = "complete"
            readings[seed] = entry
        blocks.append(entry)

    complete = [block for block in blocks if block["status"] == "complete"]
    across = b08._across
    arm_value = lambda arm, key: across(
        complete, lambda block, arm=arm, key=key: (block["arms"].get(arm) or {}).get(key))
    result = {
        "object_id": OBJECT_ID, "card": CARD, "command": "reduce",
        "launch_sha": shared.e0._git("rev-parse", "HEAD"),
        "batch_launch_sha": next(iter(shas), None) if len(shas) == 1 else None,
        "reference_object_ids": [matched.OBJECT_ID, b09.OBJECT_ID],
        "status": "complete" if len(complete) == len(BLOCKS) else "incomplete",
        "arms": {arm: {"overrides": dict(ARM_OVERRIDES[arm]),
                       "coordinator_batch_size": ARMS[arm][1],
                       "caps": {"skill_cap_k_max": ARM_CAPS[0], "team_cap_k_Z": ARM_CAPS[1]}}
                 for arm in ARMS},
        "declared_difference": SOURCE_NOTES["declared_difference"],
        "coordinator_off": SOURCE_NOTES["disable_high_level_training"],
        "law": SOURCE_NOTES["law"], "estimator": SOURCE_NOTES["regression"],
        "z_denominator": SOURCE_NOTES["z_denominator"],
        "panels": {"schedule": SCHEDULE_RULE, "reference": REFERENCE_RULE,
                   "final_map": list(FINAL_MAP_RULES), "definition": SOURCE_NOTES["panels"]},
        "quantity": (
            "J of a rule at a boundary is the mean of its panel's native world scores at that "
            "boundary's weights; a difference within a block is on the same 32 worlds and the same "
            f"evaluation seeds. The late window is the mean over the panels {list(LATE_PANELS)}. "
            "The D1280 references are the published stage-1 fits of the same blocks and B09's "
            "best constant is its published probe of those fits' final weights"),
        "blocks": blocks,
        "blocks_read": len(complete),
        "fits_supplied": len(fits), "fits_planned": len(ARMS) * len(BLOCKS),
        "invalid_fits": dict(failures),
        "invalid_references": dict(reference_failures),
        "invalid_b09_probes": {str(seed): text for seed, text in b09_failures.items()},
        "refusals": (
            "a batch of fits at more than one launch sha, a duplicate (block, arm) among the fits, "
            "a summary that is not this object's fit, an incomplete fit, a fit whose coordinator "
            "took an optimizer step or whose discoverer or discriminators did not, a fit that does "
            "not carry one label-bandit record per rollout or all of its declared panels, a fit "
            "whose declared configuration difference is not recorded, and a block whose D1280 "
            "reference or B09 probe was not supplied or is not readable by its own object's "
            "reader. An incomplete fit is listed with its reason and is left out of the counts; it "
            "is never silently dropped"),
        "interpretation_limit": INTERPRETATION_LIMIT,
    }
    for arm in ARMS:
        result[f"J_{ROLLOUTS}_{arm}"] = {
            rule: across(complete, lambda block, arm=arm, rule=rule: (
                (block["arms"].get(arm) or {}).get(f"J_{ROLLOUTS}", {}).get(rule)))
            for rule in (SCHEDULE_RULE, REFERENCE_RULE)}
        result[f"J_late_window_{arm}"] = {
            rule: across(complete, lambda block, arm=arm, rule=rule: (
                (block["arms"].get(arm) or {}).get("J_late_window", {}).get(rule)))
            for rule in (SCHEDULE_RULE, REFERENCE_RULE)}
        for key in (f"{SCHEDULE_RULE}_minus_d1280_J{ROLLOUTS}",
                    f"{SCHEDULE_RULE}_minus_d1280_late_window",
                    f"{REFERENCE_RULE}_minus_d1280_J{ROLLOUTS}",
                    f"{SCHEDULE_RULE}_minus_{REFERENCE_RULE}_J{ROLLOUTS}",
                    f"{SCHEDULE_RULE}_minus_{REFERENCE_RULE}_late_window",
                    f"{SCHEDULE_RULE}_minus_b09_best_constant_J{ROLLOUTS}",
                    "map_spread", "argmax_beta_hat_changes_after_15",
                    "rank_of_argmax_beta_hat_in_the_map"):
            result[f"{key}_{arm}"] = arm_value(arm, key)
        result[f"final_argmax_beta_hat_by_block_{arm}"] = {
            str(block["training_seed"]): (block["arms"].get(arm) or {}).get(
                "final_argmax_beta_hat") for block in blocks}
        result[f"label_map_ranking_by_block_{arm}"] = {
            str(block["training_seed"]): (block["arms"].get(arm) or {}).get("label_map_ranking")
            for block in blocks}
        result[f"first_rollout_largest_share_above_threshold_by_block_{arm}"] = {
            str(block["training_seed"]): (block["arms"].get(arm) or {}).get(
                "first_rollout_largest_share_above_threshold") for block in blocks}
        result[f"rank_deficient_rollouts_by_block_{arm}"] = {
            str(block["training_seed"]): (block["arms"].get(arm) or {}).get(
                "rank_deficient_rollouts") for block in blocks}
    result["bandit_minus_uniform"] = {
        key: across(complete, lambda block, key=key: (block.get("bandit_minus_uniform") or {}).get(
            key))
        for key in (f"J{ROLLOUTS}_{SCHEDULE_RULE}", f"late_window_{SCHEDULE_RULE}",
                    f"J{ROLLOUTS}_{REFERENCE_RULE}")}
    result["d1280_reference_by_block"] = {
        str(seed): recorded.get(seed) for seed in sorted(BLOCKS)}
    result["b09_best_constant_by_block"] = {
        str(seed): (b09_rows.get(seed) or {}).get("best_constant") for seed in sorted(BLOCKS)}
    result["predictions"] = prediction_rows(readings)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fit = sub.add_parser("fit")
    fit.add_argument("--arm", choices=tuple(ARMS), required=True)
    fit.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    fit.add_argument("--launch-sha", help="must equal the admitted source SHA")
    fit.add_argument("--output-root", type=Path, required=True)
    red = sub.add_parser("reduce")
    red.add_argument("--fits", type=Path, nargs="+", required=True,
                     help="this object's six fit summaries")
    red.add_argument("--references", type=Path, nargs="+", required=True,
                     help="the published stage-1 D1280 (B01) summaries of the three blocks")
    red.add_argument("--b09-probes", type=Path, nargs="+", required=True,
                     help="B09's three probe summaries of the same three checkpoints")
    red.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))

    if args.command == "fit":
        # Refuse an out-of-plan arm or block before the single-use admission is spent.
        plan_guard(args.arm, args.seed)
        # Nothing scientific has happened yet: no output, environment, learner or evaluator.
        admission = require_admission(__file__, direction="flexible_skill_duration")
        if args.launch_sha is not None and args.launch_sha != admission["sha"]:
            parser.error("--launch-sha must equal the admitted source SHA")
        head = shared.e0._git("rev-parse", "HEAD")
        if head and head != admission["sha"]:
            parser.error("runner source HEAD is not the admitted SHA")
        return run_fit(args.arm, args.seed, args.output_root.resolve(),
                       admission={"sha": admission["sha"],
                                  "command_sha256": admission["command_sha256"]})

    args.output_root.mkdir(parents=True, exist_ok=True)
    result = reduce_inputs([load(path) for path in args.fits],
                           [load(path) for path in args.references],
                           [load(path) for path in args.b09_probes])
    result["input_fits"] = [str(path) for path in args.fits]
    result["reference_summaries"] = [str(path) for path in args.references]
    result["input_b09_probes"] = [str(path) for path in args.b09_probes]
    shared.write_json(args.output_root / "summary.json", result)
    print(json.dumps({
        "status": result["status"], "blocks_read": result["blocks_read"],
        "invalid_fits": result["invalid_fits"],
        f"J_{ROLLOUTS}_{BANDIT_ARM}": (result[f"J_{ROLLOUTS}_{BANDIT_ARM}"][SCHEDULE_RULE]
                                       or {}).get("mean"),
        f"J_{ROLLOUTS}_{UNIFORM_ARM}": (result[f"J_{ROLLOUTS}_{UNIFORM_ARM}"][SCHEDULE_RULE]
                                        or {}).get("mean"),
        "predictions": {name: entry["blocks_holding"] for name, entry in
                        result["predictions"].items()
                        if isinstance(entry, dict) and "blocks_holding" in entry}}))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
