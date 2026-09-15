# ACVC cluster/MAPPO comparison B02 — execution record

Object: one further unchanged C/M paired block, master 28431 / evaluation namespace 38431
(`em:acvc:convergence` A, k = 1; Portfolio grant G,
[decision](../../../../portfolio/decisions/2026-09-15-acvc-one-block-replication-grant.md)).
Wrapper `scripts/run_acvc_cluster_mappo_comparison_b02.py` (reviewed at `3ae041d9e`), launch
script `experiments/candidates/acvc/cluster_mappo_comparison_b01/launch_b02.sh`, launch source
`codex/acvc 2dc9631c8644464b8c4189a53344b2956c3eb3b4`, remote worktree
`/home/wu/hmasd-worktrees/acvc-b02-2dc9631c8` ([STAGING.json](STAGING.json)), on-policy
`de66d7a4b` at `/home/wu/hmasd-inputs/acvc-mappo-b02-28431/on-policy`
([DEPENDENCY.json](DEPENDENCY.json)). Ordinary plans C 1,800 s / M 1,600 s are not caps.

## Launch conditions (evidence spec §11.4)

Source committed and pushed; identity tests green at review; admission inside the supervised
command (`admit-memory --out <output>/admission.json && …`); exposure line: 2 fits, 2,162,688
team ticks, 16,384 PPO minibatches, 24,576 optimizer steps, four sole-final 64-world panels;
zero new exposure beyond the grant.

## Exact command form (one original per handle, arguments as separate tokens)

```
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run <handle> \
  env HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 \
  bash <W>/experiments/candidates/acvc/cluster_mappo_comparison_b01/launch_b02.sh \
  2dc9631c8644464b8c4189a53344b2956c3eb3b4 <W>/temp/directions/acvc/exp/cluster_mappo_comparison_b02_28431_<arm> <arm> \
  /home/wu/hmasd-inputs/acvc-mappo-b02-28431/on-policy
```

## Launch record

| Arm | Handle | Launch (UTC) | Remote pid | Admission | State |
| --- | --- | --- | ---: | --- | --- |
| C | acvc-mappo-c-b02-28431-2dc9631c | 2026-09-15T13:26:42Z | 3732902 | passed, 5,225,508,864 B available | finished exit 0; native wall 2,495.72 s, peak RSS 562,308 KiB (beside four FSD fits); collected to [native/C/](native/C/), [C_COLLECTION.json](C_COLLECTION.json) |
| M | acvc-mappo-m-b02-28431-2dc9631c | 2026-09-15T16:01:41Z | 3736172 | passed, 13,061,177,344 B available | running beside five FSD elements (single thread); expected end about 16:45Z |

Sequencing per the grant: ready FSD work has first access; this fit is single-thread backfill
(block-1 peak RSS 561,040 / 589,924 KiB) and did not displace any FSD element (available
memory 5,049 MiB before launch, 4,319 MiB after). Operator observation at launch: `stderr.log`
is empty (0 bytes); the operator's "[exited with code 0]" note was the tool's own trailer, not
file content. Observation continues through the hub's monitor; collection into this folder at
terminal state.
