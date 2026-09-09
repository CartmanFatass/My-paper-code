# ACVC-NATIVE-LINK-LOSS-B01 — P78 technical evidence

## State and scope

Engineering accepted; one scientific invocation accepted and currently observed. Contract:
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
explicitly selects CPU. Source/input staging and accepted-handle facts will be recorded
below. CM is sole observer through terminal collection; DM/Root receives handle facts,
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
