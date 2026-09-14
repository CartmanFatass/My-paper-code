# ACVC extended-exposure B01 exact execution

Source: `66ea85e0154e838ccb570eab81e2fecea8ff5973`, pushed on codex/acvc; the isolated new runner and numerical dependencies are read from this exact commit. Control: C:/Projects/HMASD main81cb312ff and configured hmasd-wsl-node. Author/acceptance owner: `/root/dm_acvc_resume_20260914`, working at C:/Projects/HMASD-worktrees/codex-acvc. Independent high-risk Reviewer returned no material defect; nine synthetic checks passed. [Card](../../ACVC_CLUSTER_EXTENDED_EXPOSURE_B01_SCIENCE_CARD_20260914.md) fixes the sole original invocation and all scientific endpoints.

Destination checkout: `/home/wu/hmasd-worktrees/acvc-extended-b01-66ea85e01`, detached at source above. Output: `/home/wu/hmasd-worktrees/acvc-extended-b01-66ea85e01/temp/directions/acvc/exp/cluster_extended_exposure_b01_27457`. Handle: `acvc-extended-b01-27457-66ea85e01`. Python: `/home/wu/.venvs/hmasd/bin/python`; CPU FP32/thread1. Launch script syntax checked by destination `bash -n`, without scientific execution.

Exact local PowerShell command (ordinary argv; scientific launch not yet accepted in this prospective version):

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run acvc-extended-b01-27457-66ea85e01 env HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 bash /home/wu/hmasd-worktrees/acvc-extended-b01-66ea85e01/experiments/candidates/acvc/cluster_extended_exposure_b01/launch.sh 66ea85e0154e838ccb570eab81e2fecea8ff5973 /home/wu/hmasd-worktrees/acvc-extended-b01-66ea85e01/temp/directions/acvc/exp/cluster_extended_exposure_b01_27457
```

The committed launch script joins destination memory admission to the exact runner using `&&`. It records admission, original stdout/stderr, GNU wall/RSS/exit, full episode/update logs, both snapshots and final summary. Ordinary inner3600s/outer3660s+10s watchdogs preserve the scientific exposure endpoint. One original only; reconcile uncertain acceptance on this handle, never duplicate. Monitor will receive this accepted handle and return directly to DM.

Canonical owner item: `docs/research/portfolio/owner/inbox/2026-09-14/20260914-acvc-011.json` on main, produced with item.py --root C:/Projects/HMASD. Main audit `2026-09-14.md` line103 is this selection. The colliding branch-local draft is preserved as evidence only. Root owns main/index integration; no control-plane dirty path was changed.
