# ACVC-NATIVE-LINK-LOSS-B01 — P78 technical evidence

## State and scope

**Complete native comparison technically accepted.** The sole allocated invocation exited 0;
all required training/final outcomes, updates, primary contrasts and checkpoints were
collected. Scientific interpretation and any unallocated next object remain with DM.
Contract:
[science card](ACVC_NATIVE_LINK_LOSS_B01_SCIENCE_CARD_20260909.md) §§2–6 and
[prospective facts](ACVC_NATIVE_LINK_LOSS_B01_P78_PROSPECTIVE_FACTS_20260909.json),
frozen at `7ec1849b739cc51f55dee41878da980b8f245b4d`. The checkout began clean on
`codex/acvc`, `C:/Projects/HMASD-worktrees/codex-acvc`. Shared native/UCOPE/MGTAP
source and the fixed DENSE checkpoint remain unchanged.

New source: `experiments/candidates/acvc/native_link_loss_b01/{binding,model,learner,report}.py`,
its `launch.sh`, and `scripts/run_acvc_native_link_loss_b01.py`. Total 469 non-test
lines; runner 149 lines. Scope §4 additions: none, per card §6. Binding owns one-transition
anchor/position arrays per UAV. Each episode owns independent base and gate hidden tensors,
last actual commands, and separate proposal/gate generators. Recurrent replay batches only
independent recorded 32-step chunks; no environment, arm or time parallelism is added.

## Focused acceptance and independent review

Synthetic tests only; no native episodes, cost pilot, checkpoint selection or scientific
training exposure. `tests/experiments/candidates/acvc/native_link_loss_b01/test_link_loss.py`:

| Invocation | Evidence | Whole command wall |
|---|---|---:|
| Full focused file, `--basetemp temp/directions/acvc/test/p78_synthetic_20260909` | 10 passed; final publication test setup failed because scratch parent did not exist. That invocation created no scratch directory. | 5.5010612 s |
| Only publication test after creating scratch parent, `--basetemp temp/directions/acvc/test/p78_publication_20260909` | 1 passed; synthetic T/G/C/F collection, update, checkpoint and JSON publication read back. | 4.2531791 s |
| Only strengthened recurrence test, `--basetemp temp/directions/acvc/test/p78_replay_20260909` | 1 passed; nonzero common/residual projections, 64-step episodes, chunk32 replay, actual-command inputs and frozen base. No scratch directory created. | 4.4827332 s |

Aggregate required check wall **14.2369735 s** (<300 s), charged to the study and
both learned arms. Interpreter: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`;
commands used `-m pytest -q -p no:cacheprovider` and only the indicated owned tests.
There are 11 unique passing tests; the final invocation strengthens one existing test.

Coverage includes nonpadding at zero relative position, first-min ties, empty/saturated/
ambiguous/reset skips, one-transition replacement, normalized coordinate direction,
realized retrace, private recurrence, parameter counts, matched initialization, generic
containment, stream disjointness, masked gradients/entropy and all-row denominator,
stored proposal replay, fixed paired contrasts/min-of-means, boundary rules and output
publication. Synthetic outputs establish changed-path conformance, not native performance.

Independent `hmasd-reviewer` child `review_acvc_link_loss` inspected the complete source
and read-only dependencies. It identified the original zero-projection/single-chunk test
as insensitive to recurrence mistakes; the strengthened test above resolves that finding.
Final review: **no material finding remains**, scope §4 none. Reviewer ran no additional
tests or native episodes. CM retains native runtime and terminal-artifact acceptance.

Scratch cleanup limitation: the runtime rejected both the combined test/cleanup command
(before tests ran) and subsequent explicit PowerShell removal of the verified owned path
`C:/Projects/HMASD-worktrees/codex-acvc/temp/directions/acvc/test/p78_publication_20260909`.
The latter exact action was `Remove-Item -LiteralPath <that path> -Recurse -Force`;
tool result was `CreateProcess ... rejected: blocked by policy`, with no more specific reason.
No bypass or further removal attempt followed. The directory retains only synthetic test
artifacts. CM remains cleanup owner; DM was notified. This does not add a launch condition.

## Prospective cost and publication coverage

Per learned arm the cost law is shared check/startup/C-F/publication/exit work plus its
own initialization, **512 × 256** native collection steps, **1024** complete rollout Adam
updates (each replaying **512 × 5** gate rows in chunk32), **32 × 256** final steps,
exposure calculation and final checkpoint publication. G additionally evaluates/replays
its residual path. C and F each have **32 × 256** final steps and no optimizer work.
The exact total is **294912 team steps / 2048 Adam / 1152 explicit scored resets**, plus
four unscored constructor resets. The card's complete pair-comparison upper count is
57,344,000. Gate match/forward counts exclude optimizer replay/backward/critic work.

Numerical runtime projection remains **unknown** for each arm, as frozen by the card;
historical P75 process walls 353.71/368.12 s are context, not measured costs of this new
gate path. No pilot is allocated or added. The implementation uses the card's selected
budget and existing OS deadlines: ≤1800 s per complete learned arm and ≤3600 s logical
study, conservatively charging shared work to each learned arm. The external process
wall plus 14.2369735 s checks supplies the final study bill; the other learned fit is
excluded from an individual arm's bill. Human authoring, review, Git, SSH and staging
are outside machine invocation wall and are not set to zero or amortized.

Post-learner path coverage: the same runner writes and reads back all-arm JSON primary
outputs and T/G checkpoints in the synthetic publication test. No historical learner or
legacy publication route is used. The final native panel will retain all training/final
episode outcomes and all rollout update records. Fixed contrasts get paired-episode
conditional SE; min-of-means gets no selected-max SE. One training instance cannot
estimate training-seed uncertainty.

## Exact execution plan

One invocation, CPU FP32, Torch intra/inter-op=1, native NumPy unchanged, configured node
`wsl_4070` through `hmasd-wsl-node`; no local fallback, retry, resume or second allocation.
Detached exact-SHA worktree under `/home/wu/hmasd-worktrees/`, `agent-task` supervisor.
The committed `launch.sh` joins destination `admit-memory` to the runner with `&&`.
`/usr/bin/time` records complete process wall, peak RSS and exit; OS timeout bounds
the study and the runner applies remaining complete-arm/shared deadlines.

Fixed input SHA256 verified locally before staging:
`f648f2b100d07335ccd9c79c0476b8e9dba0c1644ae837d622b0c5f711030790`.
Remote existing Python reports Torch 2.7.0+cu118, NumPy 1.26.3; the scientific route
explicitly selects CPU. Source/input staging and accepted-handle facts are recorded
below. CM was sole observer through terminal collection; DM/Root received handle facts,
without observation transfer.

## Accepted invocation

- Source: `f429021166eefa9ee6d9b275ac8c91f1b13a8f28`, committed and pushed before staging.
- Node: `wsl_4070` / `hmasd-wsl-node`; cwd `/home/wu/hmasd-worktrees/acvc-p78-f42902116`,
  clean detached exact-source checkout at launch.
- Supervisor handle: `acvc-p78-native-link-loss-8901-f42902116`; reported PID 3045659.
- Output: `<cwd>/temp/directions/acvc/exp/native_link_loss_b01_8901_p78_20260909`.
- Supervisor log: `/home/wu/.agent-tasks/acvc-p78-native-link-loss-8901-f42902116/task.log`.
- Input: `/home/wu/hmasd-inputs/acvc/p78/final_DENSE.pt`; remote SHA256 equals the frozen
  `f648f2b100d07335ccd9c79c0476b8e9dba0c1644ae837d622b0c5f711030790`.
- Admission: `<cwd>/temp/directions/acvc/p78_admission.json`, assessed
  `2026-09-09T11:06:13.874723Z`; physical and effective available **15,630,286,848 bytes**,
  both ≥4 GiB. Preflight was joined to this invocation by `&&`.
- Initial supervisor observation: running, exit null, uptime7 s, tmux active.
  Native DM was notified; no observation transfer.

Exact submitted command (inside `agent-task run acvc-p78-native-link-loss-8901-f42902116`):

```bash
cd /home/wu/hmasd-worktrees/acvc-p78-f42902116 && HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python bash experiments/candidates/acvc/native_link_loss_b01/launch.sh f429021166eefa9ee6d9b275ac8c91f1b13a8f28 /home/wu/hmasd-inputs/acvc/p78/final_DENSE.pt 14.2369735 3585.7630265
```

Staging facts: direct non-login remote Git transport stalled before any science; its
identified fetch children were stopped. The configured `zsh -lic` network environment
fetched the committed objects. Updating remote tracking ref `origin/codex/acvc` failed
because historical `origin/codex/acvc/next-object-20260904` already exists. No ref was
deleted or rewritten; `cat-file` verified the exact fetched commit, then the configured
network shell created its detached worktree successfully. An initial non-login worktree
checkout similarly failed its promisor-blob fetch and cleaned itself; the successful
exact-SHA worktree is the one above. These were source-staging operations with zero
scientific exposure, not scientific retries. Source code and scientific allocation did
not change.

## Terminal collection and technical acceptance

Supervisor terminal: finished/exit 0/tmux inactive. Its task log records exit at
`2026-09-09T19:12:13+08:00` (`11:12:13Z`), duration 360 s. The supervisor's increasing
`uptime_seconds` is age at observation, not process duration. External `/usr/bin/time`
measured **359.17 s** through process exit and **552292 KiB = 0.526707 GiB** peak RSS.
Runner summary-to-external-process difference is **15.519041 s**; this outer-boundary
work is included in all complete bills, not hidden as free publication or exit.

| Complete accounting | Seconds |
|---|---:|
| Focused checks, all invocations | 14.2369735 |
| Scientific process through exit | 359.17 |
| Logical study bill / summed serial machine invocation wall | **373.4069735** |
| Shared work conservatively charged to each learned arm | 41.9255968 |
| T complete bill | **199.8208294** |
| G complete bill | **215.5117409** |

Both learned arms are below 1800 s and the whole study below 3600 s. The computation's
serial machine critical path is the same 373.4069735 s total; authoring, review waits,
network staging and time between invocations are outside the card's machine bill.
Aggregate CPU and scratch high-water are unmeasured; no aggregate CPU or scratch claim
is made. Actual summary reports Torch intra/inter-op=1, CPU/FP32. Native NumPy geometry
and its thread environment were preserved. Wall/RSS are direct external measurements,
not inferred from exit 0 or admission.

All six remote scientific files' SHA256 values matched their local collected copies.
The complete collected root is
`C:/Projects/HMASD-worktrees/codex-acvc/temp/directions/acvc/exp/native_link_loss_b01_8901_p78_20260909`.
It includes the T/G final checkpoints; both deserialize with correct arm/master,
11425/26306 gate parameters and finite tensors. Their recorded digests are in
[collection acceptance](native_link_loss_b01_p78_20260909/collection_acceptance.json).
The remote source/output root remains available pending Root's normal integration and
execution-worktree reclamation; all result bytes have a verified local copy. No live
scientific process remains, no monitor handover occurred, and no retry was launched.

Committed readable artifacts:
[summary](native_link_loss_b01_p78_20260909/summary.json),
[all 1152 episode rows](native_link_loss_b01_p78_20260909/episodes.jsonl),
[all 512 rollout records](native_link_loss_b01_p78_20260909/updates.jsonl),
[admission](native_link_loss_b01_p78_20260909/admission.json),
[external process timing](native_link_loss_b01_p78_20260909/process_time.txt),
[supervisor terminal](native_link_loss_b01_p78_20260909/supervisor_terminal.json), and
[task log](native_link_loss_b01_p78_20260909/task.log).

Direct collection checks established 1024 training episodes, 128 final episodes,
1152 explicit resets, 4 additional constructor resets, 294912 completed team steps,
1474560 base agent forwards, 1392640 learned-gate agent forwards, 512 rollout records and
2048 Adam records. Each T/G training reset panel is exactly 890101000–890101511;
all four final panels are exactly 890102000–890102031 in episode order. Every episode
has 256 steps and S=256J. Gate aggregates recomputed from episode rows match summary.
Every fixed contrast's mean, sample-SD/√32 SE, signed rule and quarter-S condition were
recomputed directly from retained episode pairs and matched. These are post-collection
read-only arithmetic/output checks, not extra environments, fits, tests or evaluation.

## Native endpoint and verbatim card rules

Native units remain `S = sum_t r_team[t]`, `J = S/256`. Arm means:

| Arm | Final mean J |
|---|---:|
| T | 0.2344827282 |
| G | 0.1975140229 |
| C | 0.1673014978 |
| F | 0.2635633631 |

Card rule: **UP if mean difference >0.01 J; DOWN if <−0.01 J; otherwise WITHIN**.
The quarter-unit test is separately **mean difference >0.25 S**.

| Fixed paired contrast | Mean J difference | Conditional SE J | Mean S difference | Rule | >0.25 S |
|---|---:|---:|---:|---|---|
| T−C (primary) | +0.0671812303 | 0.0115352194 | +17.1983950 | UP | yes |
| T−F (primary) | −0.0290806349 | 0.0105070125 | −7.4446425 | DOWN | no |
| T−G | +0.0369687053 | 0.0111757440 | +9.4639885 | UP | yes |
| G−C | +0.0302125251 | 0.0128636323 | +7.7344064 | UP | yes |
| G−F | −0.0660493402 | 0.0106243579 | −16.9086311 | DOWN | no |

Primary transparent summary `min(mean(T−C),mean(T−F))` is **−0.0290806349 J**
(−7.4446425 S). It is a minimum of panel means, not an episode-wise oracle; no naive
selected-max SE is attached. Each fixed-contrast SE uses 32 paired joint episodes,
conditional on the single matched training instance. These numbers do not estimate
training-seed population uncertainty. All adverse and favorable outcomes are retained.

## Gate exposure and parameter movement

| Arm/phase | Opportunities | Apply on opportunity | Retrace | Distinguishable b/c |
|---|---:|---:|---:|---:|
| T train | 51834 | 20413 | 31421 | 51834 |
| T final | 3338 | 891 | 2447 | 3338 |
| G train | 50076 | 22991 | 27085 | 50076 |
| G final | 2629 | 1353 | 1276 | 2629 |
| F final | 3670 | 0 | 3670 | 3670 |

C does no anchor matching by design; its zero opportunity counter means **not measured**,
not an absence of possible link-loss events. C always sends the base proposal. The apply
counts above concern eligible gate choices; every ineligible step sends the base as well.
Both gate learners received 1024 Adam updates, with finite nonzero gate displacement:

| Arm/group | Initial norm | Absolute displacement | Relative displacement |
|---|---:|---:|---:|
| T gate | 9.3525381 | 2.8876708 | 0.3087580 |
| T common final projection | 0 | 0.2287203 | not defined |
| T critic | 9.2879753 | 6.2130876 | 0.6689389 |
| G gate | 13.1903706 | 1.9953898 | 0.1512762 |
| G common final projection | 0 | 0.0513526 | not defined |
| G residual final projection | 0 | 0.0459827 | not defined |
| G critic | 9.2879753 | 6.7530994 | 0.7270798 |

Full common/residual path movement remains in summary. Gate movement is measured
separately from critic movement; neither substitutes for the signed native outcomes.

## Remaining boundary

No scientific execution or technical acceptance gap remains in this allocated comparison.
The previously reported runtime rejection still prevents cleanup of the single owned
synthetic publication scratch directory; CM retains ownership and has not retried or
bypassed that rejection. The frozen outcome-informed base choice, one fitted instance,
private observed-coordinate ambiguity exclusions and approximate realized retrace limit
the claim as stated in the card. No scientific interpretation, new object, additional
training instance, native diagnostic panel or tuning is selected by this technical return.
DM owns scientific intake; Root owns accepted integration and execution-worktree reclamation.
