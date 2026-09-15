# ACVC fixed-rate-pair B01 exact execution

Author/technical acceptance owner: `/root/dm_acvc_resume_20260914`, authoring at `C:/Projects/HMASD-worktrees/codex-acvc` / `codex/acvc`. [The card](../../ACVC_CLUSTER_FIXED_LR_PAIR_B01_SCIENCE_CARD_20260914.md) binds exactly two originals under the complete Portfolio allocation. Source **2bbaa99ad9cc717d89e47a1f24d9acd76dce4f97**, published before staging. The numerical source is fixed even when subsequent evidence-only commits update this document.

Destination **hmasd-wsl-node**, detached checkout `/home/wu/hmasd-worktrees/acvc-rate-pair-b01-2bbaa99ad`; Python `/home/wu/.venvs/hmasd/bin/python`, CPU FP32 and one numerical thread per original. [COMMANDS.json](COMMANDS.json) contains the literal argv, identities, source and original output paths. The two commands are separate originals, each with fresh adjacent physical/effective ≥4 GiB admission inside the committed launch script; neither admission covers the other. No original has been accepted at this prospective publication.

## low

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run acvc-rate-low-b01-27931-2bbaa99ad env HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 bash /home/wu/hmasd-worktrees/acvc-rate-pair-b01-2bbaa99ad/experiments/candidates/acvc/cluster_fixed_lr_pair_b01/launch.sh 2bbaa99ad9cc717d89e47a1f24d9acd76dce4f97 /home/wu/hmasd-worktrees/acvc-rate-pair-b01-2bbaa99ad/temp/directions/acvc/exp/cluster_fixed_lr_pair_b01_27931_low low
```

## reference

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run acvc-rate-ref-b01-27931-2bbaa99ad env HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python PYTHONDONTWRITEBYTECODE=1 bash /home/wu/hmasd-worktrees/acvc-rate-pair-b01-2bbaa99ad/experiments/candidates/acvc/cluster_fixed_lr_pair_b01/launch.sh 2bbaa99ad9cc717d89e47a1f24d9acd76dce4f97 /home/wu/hmasd-worktrees/acvc-rate-pair-b01-2bbaa99ad/temp/directions/acvc/exp/cluster_fixed_lr_pair_b01_27931_reference reference
```

The launch script refuses only reuse of the exact original output directory, joins admission and runner with `&&`, and records original stdout/stderr, native GNU wall/peak-RSS/user/system/exit, episode/update logs, one final checkpoint and summary. Its inner3600 s / outer3660 s +10 s watchdogs are ordinary fault containment; the endpoint is fixed episodes/updates, not elapsed time. Two disjoint single-process originals may overlap; no framework, worker pool or extra compute is created. Native wall sum and aggregate CPU are reported separately from overlap elapsed and from unknown full support/provider costs.

Remote staging uses `git worktree add --detach --no-checkout` followed by restoring only the configured source scopes. No unrelated historical document restore or source copy from uncommitted Windows files is used. Source differences over the relevant scopes and destination `bash -n` must be checked as technical facts. Independent Astra/high review found and DM repaired one offline partial-ingestion defect. The same Reviewer checked the published correction and returned no residual material finding. Training/evaluation/launch bytes are unchanged. DM accepts the complete technical path; zero originals were used for verification.

After each accepted original, DM hands its exact handle to reusable native monitor `/root/dm_acvc_resume_20260914/mon_ll_acvc`, receives MONITOR_ADOPTED directly, and stops routine polling. Reconcile uncertain acceptance on the same handle before any further action. Preserve every original partial/outcome; no retry or seed replacement. The other original remains selected regardless of observed score, subject to concrete integrity/resource constraints.

Canonical owner item `docs/research/portfolio/owner/inbox/2026-09-14/20260914-acvc-013.json`; main audit2026-09-14 line117. Root owns main publication. No control-plane dirty path was changed. Local test cleanup was rejected before execution, so its exact scratch remains preserved in ENGINEERING.md; no alternative deletion was attempted.

Actual source staging completed at the full commit above; scoped source diff and destination bash syntax passed. The initial source-only9b44896d9 checkout contained no result output or unique untracked file and was safely retired after preserving its published source; disk and worktree registration absence were verified. Both staging receipts are retained in STAGING.json.
