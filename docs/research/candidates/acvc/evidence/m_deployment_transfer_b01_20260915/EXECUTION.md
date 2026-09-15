# ACVC M-deployment transfer B01 — execution record

Object: one fresh M fit of the frozen block-2 recipe, MASTER 28531 / evaluation namespace
38531, with three private final panels M / F(M) / own-dwell(M)
([card](../../ACVC_M_DEPLOYMENT_TRANSFER_B01_PROSPECTIVE_CARD_20260915.md); `em:acvc:convergence`
B with corrections; Portfolio grant G,
[decision](../../../../portfolio/decisions/2026-09-15-acvc-m-deployment-transfer-grant.md)).
Runner `scripts/run_acvc_m_deployment_transfer_b01.py`, wrapped evaluator
`experiments/candidates/acvc/m_deployment_transfer_b01/wrapped_eval.py`, launch script
`experiments/candidates/acvc/m_deployment_transfer_b01/launch.sh` (L0 commit `codex/acvc
fb7f859d9`, main `95c2290a0`; review corrections `a741758a1`, main `deb0eb357`; eleven focused
tests passed on the pinned on-policy checkout). Launch source `codex/acvc
a741758a11e6c9d9888cbc852095544f3df4e04f`, remote detached worktree
`/home/wu/hmasd-worktrees/acvc-transfer-b01-a741758a1` (fetched by sha because a stale
remote-tracking ref `origin/codex/acvc/next-object-20260904` on the node blocks the branch ref).
On-policy `de66d7a4b` at `/home/wu/hmasd-inputs/acvc-transfer-b01-28531/on-policy`
([DEPENDENCY.json](DEPENDENCY.json)). The 2,600 s plan is not a cap.

## Per-fit cost projection (recorded before launch, AGENTS §5)

Cost law of the runner: `wall ≈ T_train + 3 × T_panel + T_binding`, where `T_train` covers
4,096 H256 training episodes (1,048,576 team ticks, 2,048 two-episode rollouts, 4 PPO epochs
per rollout, 8,192 actor + 8,192 critic optimizer steps) and each `T_panel` covers 64
actor-only episodes (16,384 ticks; three loads of the one snapshot); `T_binding` is the numpy
`Binding.observe` work on two panels (5 × 20 entry arrays per tick).

| Quantity | Basis | Projection |
| --- | --- | --- |
| Training plus one M panel | block-2 M fit, same recipe: 2,427.41 s native wall, 2,394.46 s CPU, 585,504 KiB peak | 2,430 s |
| Two added panels | upper bound at the training per-tick rate 2.28 ms/tick × 16,384 ticks each; actor-only ticks are cheaper | ≤ 75 s |
| Binding overhead | two panels × 16,384 ticks of small numpy work | < 20 s |
| **Projected wall, one fit** | | **about 2,500 s (plan 2,600 s)**, far below the runtime-spec UAV threshold 43,200 s per invocation; no cap applies |
| Peak RSS | one policy instance alive at a time (`del policy` between panels), one snapshot on CPU, one fresh cluster env per panel | about 0.6 GiB, under 1 GiB |

Exposure line: 1 fit, 1,097,728 team ticks (1,048,576 training + 49,152 evaluation), 8,192
PPO minibatches, 16,384 optimizer steps, one final snapshot loaded three times, three
sole-final 64-world panels; zero new exposure beyond the grant.

## Launch conditions (evidence spec §11.4)

Source committed and pushed at the reviewed sha; focused tests green; admission inside the
supervised command (`admit-memory --out <output>/admission.json && …` under GNU time); the
exposure line above. Independent Opus review of the L0 and resolution of material findings
precede the launch (grant condition): `hmasd-reviewer` reviewed `fb7f859d9` (accept after
fixes; one MATERIAL: `--mode reduce` ran before the identities were bound, so a real summary
would have read all-INCOMPLETE; two MINOR: an unused early numpy import before the
single-thread pins, and a launch script that silently accepted the b02 four-argument shape;
NOTEs on the by-construction `apply` counter and on test coverage of the publication chain,
which the reviewer exercised out of band with a stubbed trainer: three panels complete,
interventions summed per panel, `post_fit_loads` 3). All three fixes plus a CLI-level reduce
test and a counter clause in `summary["deployment_laws"]` are in `a741758a1`. Ledger row 31.

## Exact command form (one original, arguments as separate tokens)

```
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run <handle> \
  env HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 \
  bash <W>/experiments/candidates/acvc/m_deployment_transfer_b01/launch.sh \
  <launch sha> <W>/temp/directions/acvc/exp/m_deployment_transfer_b01_28531 \
  /home/wu/hmasd-inputs/acvc-transfer-b01-28531/on-policy
```

## Launch record

| Handle | Launch (UTC) | Remote pid | Admission | State |
| --- | --- | ---: | --- | --- |
| acvc-transfer-m-b01-28531-a741758a | 2026-09-15T21:09:14Z | 3745266 | passed, 15,621,808,128 B physical and effective available (floor 4 GiB) | running at 21:09:38Z (uptime 24 s, tmux active); stderr.log 0 bytes; updates at rollout 64 after 31.6 s process wall; expected end about 21:52Z |

Operator: `hmasd-experiment-operator`, one command, pre-launch duplicate check `not_found`, no retry. Node idle otherwise (load 0.00 before launch). Observation: hub-owned bounded status polls; collection after the terminal state.
