# VNFC memory-bounded K=1024 R02 — remote attempt-01 quarantine

- Object: `VNFC-CONTROLLER-HEADROOM-A-RECON-MEMORY-BOUNDED-K1024-R02`
- Evidence class / claim ceiling: `A/RECON`; unchanged finite sixteen-world measurement fact
- Launch SHA: `cccecffdee006b2943bb5f28797ae7ae3d02f53f`
- Remote node: `wsl_4070`
- Agent task: `vnfc-mb1024-r02-cccecffd-20260904-01`
- Terminal disposition: **`PACKAGING_FAILURE / MB1024-INCOMPLETE`**
- Scientific disposition: no result, no polarity, no object consumption

## Direct launch observation

The unique remote task was accepted once and reached terminal status `failed`, exit code `2`, in
one second. Its single payload joined the remote resource admission and exact runner with `&&`.
No second task or local duplicate was started.

The fresh remote admission passed before the runner:

| field | observed |
| --- | ---: |
| assessed | `2026-09-04T14:18:27.455458Z` |
| physical available | `12,831,141,888` bytes |
| effective available | `12,831,141,888` bytes |
| required floor | `4,294,967,296` bytes |
| pass | `true` |
| receipt SHA-256 | `7b1d49dcb76112ee9290380fe74a552608118134fc03ecc98b054f6f62910ed1` |

The runner then published exactly one `summary.json` with branch `MB1024-INCOMPLETE`, wall
`0.03486561299996538` seconds, peak RSS `343,142,400` bytes, and this reason:

```text
FileNotFoundError: [Errno 2] No such file or directory:
'/home/wu/hmasd-worktrees/vnfc-mb1024-r02-ce80bc14-20260904-01/docs/research/candidates/variable_n_fleet_churn/VNFC_CONTROLLER_HEADROOM_K256_ACCEPTED_WITNESS_20260904.json'
```

The summary SHA-256 is
`d429017f2c3d63514e2c6d12653c702ade3bb63cad07be354c48c0a8f42e46f9`. The result root,
preflight receipt, task log, runner wrapper, terminal status, and exit code were copied back only
after terminal status and their local hashes match the remote hashes.

## Reproduction and classification

On the recorded `cccecffd...` worktree, a non-result configured-interpreter call to
`accepted_k256_worlds()` reproduced the same `FileNotFoundError` at `analysis.py:113`. The sparse
checkout contained the configured code/test paths but omitted the card-required accepted K=256
witness. The witness is tracked at
`docs/research/candidates/variable_n_fleet_churn/VNFC_CONTROLLER_HEADROOM_K256_ACCEPTED_WITNESS_20260904.json`
with SHA-256
`3bdff4a303218438c38c7d73534894e6bfc3a2e5acd385952c4fdee73db882fc`.

CM classified the terminal as **`PACKAGING_FAILURE / MB1024-INCOMPLETE`**. The failure occurred
before the first `run_headroom_fixture()` call. Deterministic target fixtures may have been rebuilt
in memory, but no native world execution, beam endpoint, BCRH endpoint, PERSIST endpoint, K=1024
headroom observable, or branch predicate was evaluated. Error text alone was not used for this
classification; the failing read was reproduced over the recorded bytes.

This is engineering conformance evidence only. It cannot support `MB1024-A`, `MB1024-D`, host
saturation, search insufficiency, learner value, or any lifecycle decision. The passing admission
belongs only to attempt-01 and cannot admit another invocation.

## Decisions this quarantine produces

Options:

- (a) quarantine attempt-01 permanently, add the exact witness directory to the sparse checkout,
  verify the witness hash, repeat the full Linux focused suite and `.so` load check, then use one
  new task, result root, launch record, and fresh admission;
- (b) interpret the incomplete summary as a negative controller-headroom result;
- (c) recover or reuse the old task, result root, or admission receipt;
- (d) stop the unchanged object because of the packaging failure.

Recommendation: **(a)**. It repairs only remote assembly, is outcome-blind and reversible, and
preserves every frozen scientific, numerical, RNG, comparator, exposure, cost, and branch
semantic. Options (b) and (d) would turn an unavailable input into scientific polarity. Option (c)
would violate create-once and fresh-admission requirements.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. Attempt-01 is permanently quarantined. A fresh attempt is permitted only after
all five CM conditions hold: exact witness present; hash `3bdff4a...82fc`; full Linux focused suite
passes; `.so` prebuild/load passes; and a new task/root receives its own immediately preceding
4-GiB admission. No code or scientific-card change is authorized by this decision.

## Evidence paths

- Local quarantined summary:
  `temp/directions/variable_n_fleet_churn/exp/controller_headroom_mb1024_r02/remote_attempt_01_result/summary.json`
- Local admission:
  `temp/directions/variable_n_fleet_churn/exp/controller_headroom_mb1024_r02/remote_attempt_01_preflight.json`
- Local task facts:
  `temp/directions/variable_n_fleet_churn/exp/controller_headroom_mb1024_r02/remote_attempt_01_task/`
- Frozen card:
  `VNFC_CONTROLLER_HEADROOM_A_RECON_MEMORY_BOUNDED_K1024_R02_SCIENCE_CARD_20260904.md`

