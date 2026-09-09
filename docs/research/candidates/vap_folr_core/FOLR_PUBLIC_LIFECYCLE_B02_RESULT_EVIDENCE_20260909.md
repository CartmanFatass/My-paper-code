# FOLR B02 execution evidence

Allocation: card§6 and DM intake§§1–2 at `8a6b11b14515faf91db9894b443ce7349489f34f`. Accepted source `434f10cf95f16dd342cbf754382aa76155fcd2b7`. Sole observer/technical acceptance: `/root/dm_folr_p68_reentry/cm_public_lifecycle_b01`; scientific intake: original DM. No observation transfer follows a handle notification.

Exact RETAIN and RESET commands are the two code blocks in [engineering result](FOLR_PUBLIC_LIFECYCLE_B02_ENGINEERING_RESULT_20260909.md#prospective-commands-only--not-submitted), now executed only under this later allocation. They bind new detached cwd `/home/wu/hmasd-worktrees/folr-public-lifecycle-b02-434f10cf`, node `hmasd-wsl-node`, interpreter `/home/wu/.venvs/hmasd/bin/python`, CPU FP32, Torch compute/interop1, seeds7802/107802. Each command joins destination admit-memory with its exact runner; GNU timeout1800s plus bounded5s error-reporting grace and `/usr/bin/time -v` cover complete startup/import/train/evaluate/publication. Roots are `temp/directions/vap_folr_core/exp/public_lifecycle_b02_seed7802_<arm>`, with sibling `<arm>_memory.json` receipts. No B01 state/checkpoint/worktree is reused.

Before launch: per-arm cost projection reuses B01 complete same-workload evidence, RETAIN770.69s/RESET746.89s, with each B02 arm capped1800s and pair3600s. Seed changes can alter realized traffic and cost; these are planning estimates, not upper bounds. Dominant workload remains4969 ×32 ×21 ×5 ×2 recurrent replay row forwards per arm, plus backward/mixer and5032 native episodes. Post-learner path coverage reuses B01 final checkpoint/publication and the accepted B02 controlled seed metadata cases. No pilot or repeated smoke. Supporting checks/readbacks had3.1392171s spent of60s at allocation; staged source/head/preflight-file check0.5890085s adds to that budget, excluding Git/network staging and ordinary observation.

Staging used the configured `zsh -lic` network shell, then created the new detached worktree and verified HEAD, clean declared source surface and preflight helper presence. No source changes. Remote main and unrelated files were untouched.

## Accepted handles

RETAIN: `/usr/local/bin/agent-task run folr-public-lifecycle-b02-retain-20260909` with the exact command above, accepted2026-09-09T20:09:12Z, supervisor PID3066045, tmux `agent_folr-public-lifecycle-b02-retain-20260909`. Fresh destination receipt20:09:12.751945Z passed physical/effective floors:15,637,336,064 available bytes each against4,294,967,296. Initial status running/exit null. One accepted submission consumed; RESET remains pending intact first-arm completion/collection. No retry or fallback.

## Collection and cleanup inventory

At terminal collection retain each summary.json (all32 native returns), final.pt, process.time, supervisor task.log and memory receipt locally under the same relative B02 paths. Supervisor directories hold runner.sh, status, pid, start_time and exit_code. The detached worktree and these two scoped supervisor directories remain for Root's later preservation/reclamation trigger; no deletion is part of this allocation. Previously policy-blocked test scratch remains untouched and CM-owned.
