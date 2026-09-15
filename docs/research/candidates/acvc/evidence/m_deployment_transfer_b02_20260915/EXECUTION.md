# ACVC M-deployment transfer B02 — execution record

Object: one further independently initialised M fit of the frozen block-2 recipe, MASTER 28631 /
evaluation namespace 38631, with the unchanged three private final panels M / F(M) / own-dwell(M)
([card](../../ACVC_M_DEPLOYMENT_TRANSFER_B02_PROSPECTIVE_CARD_20260915.md); `em:acvc:convergence`
result review B, `PRO_FINAL`; Portfolio grant G2,
[decision](../../../../portfolio/decisions/2026-09-15-acvc-m-deployment-transfer-b02-grant.md)).
Thin entry `scripts/run_acvc_m_deployment_transfer_b02.py` rebinding the identities on the
unchanged B01 transfer runner before any recipe import; launch script
`experiments/candidates/acvc/m_deployment_transfer_b02/launch.sh`; five focused binding tests
under `tests/experiments/candidates/acvc/m_deployment_transfer_b02/` (L0 commit `codex/acvc
6a3967065`; with the ten unchanged B01 tests: 15 passed, 1 skipped without the on-policy
checkout). Launch source `codex/acvc c006c0b2453a44902ebfda827099823a28e136f1`, remote detached worktree
`/home/wu/hmasd-worktrees/acvc-transfer-b02-c006c0b24` (fetched by sha because the node's
stale remote-tracking ref `origin/codex/acvc/next-object-20260904` blocks the branch ref).
On-policy `de66d7a4b` re-staged at `/home/wu/hmasd-inputs/acvc-transfer-b02-28631/on-policy`
([DEPENDENCY.json](DEPENDENCY.json), digest verified, zero native invocations). The 1,200 s plan
is not a cap.

## Per-fit cost projection (recorded before launch, AGENTS §5)

Cost law of the runner (unchanged from B01): `wall ≈ T_train + 3 × T_panel + T_binding`, where
`T_train` covers 4,096 H256 training episodes (1,048,576 team ticks, 2,048 two-episode rollouts,
4 PPO epochs per rollout, 8,192 actor + 8,192 critic optimizer steps), each `T_panel` covers 64
actor-only episodes (16,384 ticks; three loads of the one snapshot) and `T_binding` is the numpy
`Binding.observe` work on two panels.

| Quantity | Basis | Projection |
| --- | --- | --- |
| Training plus one M panel | B01, same recipe and count, alone on the node: 985.12 s native wall for the whole command (983.51 s CPU, 585,028 KiB peak); about 0.9 ms per training tick | about 950 s |
| Two added panels | B01 measured panel phases about 12–14 s each (actor-only ticks plus Binding) | about 30 s |
| **Projected wall, one fit** | idle node; scale by the number of concurrent single-thread fits if contention appears (B01's 2,427 s block-2 basis was measured beside five FSD fits) | **about 1,000 s alone (plan 1,200 s)**, far below the runtime-spec UAV threshold 43,200 s per invocation; no cap applies |
| Peak RSS | one policy instance alive at a time, one snapshot on CPU, one fresh cluster env per panel | about 0.6 GiB, under 1 GiB |

Exposure line: 1 fit, 1,097,728 team ticks (1,048,576 training + 49,152 evaluation), 8,192 PPO
minibatches, 16,384 optimizer steps, one final snapshot loaded three times, three sole-final
64-world panels, five environment constructions; zero new exposure beyond grant G2; nothing
transferred from the B01 fit.

## Launch conditions (evidence spec §11.4)

Source committed and pushed at the reviewed sha; focused tests green; admission inside the
supervised command (`admit-memory --out <output>/admission.json && …` under GNU time); the
exposure line above. Independent review of the changed behaviour (the identity binding) precedes
the launch per the grant: independent `hmasd-reviewer` (Opus) of `codex/acvc 6a3967065`: **accept**, no MATERIAL finding; two MINOR
(no B02 test of the native summary stamping, covered by inference and by `fit_eligible` refusing a
wrong stamp loudly; the on-policy no-op identity test skipped on the control plane) and three NOTEs
(`PRIOR_IDENTITIES` is test-only per the card's disclaimer; in-process B01 reduce after `bind_b02`
unreachable through the launch scripts; no byte-digest guard to be added). Resolution: both focused
suites run on the node in the launch worktree with `HMASD_ON_POLICY_ROOT` set to the staged checkout:
**16 passed** (22:32Z; scratch removed; worktree clean at the launch sha). Ledger row 35.

Frozen launch command (operator; `<W>` is the detached worktree at the launch sha):

```text
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run <handle> \
  env HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 \
  bash <W>/experiments/candidates/acvc/m_deployment_transfer_b02/launch.sh \
  <launch sha> <W>/temp/directions/acvc/exp/m_deployment_transfer_b02_28631 \
  /home/wu/hmasd-inputs/acvc-transfer-b02-28631/on-policy
```

## Launch record

| Handle | Launch (UTC) | Remote pid | Admission | State |
| --- | --- | ---: | --- | --- |
| __LAUNCH_ROW__ |
