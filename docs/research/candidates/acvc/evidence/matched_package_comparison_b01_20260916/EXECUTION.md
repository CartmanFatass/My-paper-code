# ACVC matched-package comparison B01 — execution record

Object: one fresh prospectively paired block, MASTER 28731 / evaluation namespace 38731, one C fit
and one M fit of the unchanged recipes, six sole-final panels C / F(C) / own-dwell(C) / M / F(M) /
own-dwell(M) on the common final worlds; sole primary P = mean64[J(F(C)) − J(F(M))] at ±.01 J
([card](../../ACVC_MATCHED_PACKAGE_COMPARISON_B01_PROSPECTIVE_CARD_20260915.md), fixed by
`em:acvc:convergence` 2026-09-16 02:48Z, A with corrections, `PRO_FINAL`; Portfolio grant G3,
[decision](../../../../portfolio/decisions/2026-09-15-acvc-direction-investment-lifecycle.md)).
Thin entry `scripts/run_acvc_matched_package_comparison_b01.py` (`--arm C|M`; `--mode reduce`)
binding the identities and plans before any recipe import; launch scripts
`experiments/candidates/acvc/matched_package_comparison_b01/launch_c.sh` and `launch_m.sh`; eight
focused synthetic tests under `tests/experiments/candidates/acvc/matched_package_comparison_b01/`
(L0 commit `codex/acvc dadba46f9`, review minors resolved at `841e5c35b`; with the B02, B01-transfer and
block-2 binding suites: 26 passed, 1 skipped on the control plane without the on-policy checkout; 27
passed on the node at `dadba46f9` (03:02Z) and again at the launch sha, see below). Launch source
`codex/acvc 841e5c35b1b9c0fe56f852f62f5235ae345b3227`; remote detached worktree
`/home/wu/hmasd-worktrees/acvc-matched-b01-841e5c35b` (fetched by sha; the `dadba46f9` worktree removed). On-policy `de66d7a4b` re-staged at
`/home/wu/hmasd-inputs/acvc-matched-b01-28731/on-policy` for the M arm
([DEPENDENCY.json](DEPENDENCY.json), digest verified, zero native invocations). Plans C 2,600 s /
M 1,200 s are not caps.

## Per-arm cost projection (recorded before launch, AGENTS §5)

Cost laws of the unchanged runners: `wall_C ≈ T_train,C + 3 × T_panel,C`, `wall_M ≈ T_train,M +
3 × T_panel,M + T_binding`; each `T_train` covers 4,096 H256 training episodes (1,048,576 team
ticks, 2,048 two-episode rollouts, four PPO epochs per rollout; C 8,192 joint optimizer steps, M
8,192 actor + 8,192 critic steps); each `T_panel` covers 64 episodes (16,384 ticks; three loads of
the one snapshot per arm); `T_binding` is the numpy `Binding.observe` work on the wrapped panels.

| Arm | Basis | Projection |
| --- | --- | --- |
| C | block 1 C 1,670.62 s beside one fit, block 2 C 2,495.72 s beside four fits; no standalone C runtime is established; three panels are inside those walls | **about 1,700–2,600 s alone (plan 2,600 s)**; per-arm invocation below the runtime-spec toy threshold 2,700 s only if run alone, which is an engineering threshold, not a cap or gate |
| M | B01 / B02 transfer fits alone on the node with the same three panels: 985.12 / 989.80 s native wall (about 0.9 ms per training tick; panels 12–14 s each) | **about 1,000 s alone (plan 1,200 s)** |
| Peak RSS | one policy instance alive at a time per process, one snapshot on CPU, one fresh cluster env per panel | about 0.6 GiB per arm (C 562,308 KiB and M 585,504 / 588,916 KiB measured) |

Launch order: C then M (G3 ordinary order); the second original is launched when the node can
accommodate it with its own fresh admission. Concurrent originals would be an operational variant
only; no historical contention figure is claimed as a concurrent-pair speedup or slowdown.

Exposure line: 2 fits, **2,195,456 scored team ticks** (2,097,152 training + 98,304 evaluation),
16,384 PPO minibatches, 24,576 optimizer calls, two final snapshots loaded three times each, six
sole-final 64-world panels, nine environment constructions; exactly the G3 inclusive ceiling;
nothing transferred from any completed fit.

## Launch conditions (evidence spec §11.4)

Source committed and pushed at the reviewed sha; focused tests green locally and on the node;
admission inside each supervised command (`admit-memory --out <output>/admission.json && …` under
GNU time); the exposure line above. Independent review of the changed behaviour (identity
binding, dispatch and the paired reducer) per G3: independent `hmasd-reviewer` (Opus) of `codex/acvc
dadba46f9`: **accept**, no MATERIAL finding; each named risk traced (C parser sees the bound master and
writes plan 2,600 s and the unchanged C/F/dwell panels; the M binder sets the common object and the
transfer counts satisfy `fit_eligible`; the entry's top-level imports pull neither `mappo` nor `c_fit`;
the reducer's `bind_c()` is process-local; both summaries carry the same object; the suites coexist in
either order; protected bytes untouched by `git diff --name-only`). Three MINOR (numpy imported before the
single-thread caps; no input provenance in the reduce summary; silently ignored arguments) resolved at
`841e5c35b` (numpy after the caps, `inputs` with launch shas and summary paths, explicit `parser.error`s);
NOTEs: CLI `allow_nan=False` unreachable from runner summaries; the output parent must be pre-created
in a fresh worktree (done by the worktree script). Focused suites after the repair: 16 passed locally,
node run at the launch sha recorded below.

Frozen launch commands (operator; `<W>` is the detached worktree at the launch sha):

```text
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run <handle-C> \
  env HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 \
  bash <W>/experiments/candidates/acvc/matched_package_comparison_b01/launch_c.sh \
  <launch sha> <W>/temp/directions/acvc/exp/matched_package_comparison_b01_28731_C

ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run <handle-M> \
  env HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 \
  bash <W>/experiments/candidates/acvc/matched_package_comparison_b01/launch_m.sh \
  <launch sha> <W>/temp/directions/acvc/exp/matched_package_comparison_b01_28731_M \
  /home/wu/hmasd-inputs/acvc-matched-b01-28731/on-policy
```

## Launch record

| Handle | Launch (UTC) | Remote pid | Admission | State |
| --- | --- | ---: | --- | --- |
| (not launched) | | | | |

## Terminal record

| Handle | Terminal (UTC) | Supervisor status | Native wall s | CPU s | Peak RSS KiB | Exit |
| --- | --- | --- | ---: | ---: | ---: | --- |
| (none) | | | | | | |
