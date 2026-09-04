# Remote-first result-compute routing

Date: 2026-09-04

Provenance: `OWNER_DIRECT`

## Decision

HMASD adds `wsl_4070` as its primary result/heavy-compute node and uses a remote-first placement policy.
The local Windows project remains Root's control plane and the place where DM/CM work, review,
Transport, Git integration, and durable research records are coordinated. New result-bearing
invocations that are prospectively portable across the two hosts go to the remote node first.
Long portable builds, focused suites, and verification probes also prefer the node once their exact
source inputs are committed; ordinary edit loops, short checks, and uncommitted work stay local.

The node is declared in `.codex/hmasd-compute.toml`. Direct connection evidence from Codex task
`01a06c53-8c1e-7432-ac60-6614b190007d` and the adopting Root session established:

- SSH user/host: `wu@LAPTOP-U9TDKC8A` through local alias `hmasd-wsl-node`;
- Ubuntu 24.04 on WSL2, Linux `6.6.87.2-microsoft-standard-WSL2`;
- NVIDIA GeForce RTX 4070 Laptop GPU with 8,188 MiB;
- `agent-task` at `/usr/local/bin/agent-task` for detached execution;
- the login shell supplies `uv` and the network proxy; non-interactive GPU commands require
  `/usr/lib/wsl/lib` on `PATH`; and
- credentials are installed only in the local user's SSH directory and are not copied into Git.

Existing live local processes stay local. This decision does not migrate them, restart them, or
reinterpret their results.

## Activation evidence

The node was marked `active` only after two detached `agent-task` checks completed with exit zero:

- `hmasd_env_20260904_v2` installed the Linux execution stack from 63 locally verified offline
  wheels: Python 3.10.21, NumPy 1.26.3, PyTorch 2.7.0+cu118, CUDA 11.8, the NVIDIA CUDA runtime
  dependencies, the server requirements, pytest, psutil, pybind11, and ninja. PyTorch reported
  `cuda_available=true` and identified the RTX 4070 Laptop GPU.
- `hmasd_route_smoke_20260904_01` used detached worktree
  `/home/wu/hmasd-worktrees/route_smoke_20260904_01` at pushed sha
  `0852348499f5c59b150f5cb3b948983b317b15a8`. Its one supervised command ran remote
  `admit-memory && probe`; the admission passed with 15,438,577,664 physical/effective bytes and
  the probe reported host `LAPTOP-U9TDKC8A`, CUDA available, and the expected worktree/sha.

These are infrastructure checks only. They created no scientific root, RNG master, model,
optimizer, result, or direction polarity.

## Standard remote launch boundary

1. The DM declares whether host/device execution is portable or pinned as part of the card. A host
   or device that changes precision, RNG, comparator, budget, or estimand is scientific meaning,
   not a scheduling choice.
2. CM freezes argv, output root, stop condition, execution node, and launch sha; the source commit
   is pushed before remote preparation.
3. The operator creates a detached worktree below `/home/wu/hmasd-worktrees/` at that exact sha.
   It never advances or rewrites a worktree used by a live task. The sparse surface is extended
   only with committed paths required by the exact assignment. A frozen evidence input outside
   Git may be copied to a request-specific directory below `/home/wu/hmasd-inputs/` only when its
   byte digest was already fixed by the card or launch assignment; uncommitted source is never
   staged through this path.
4. One `agent-task` command activates `/home/wu/.venvs/hmasd`, runs the remote
   `scripts/hmasd_resource_preflight.py admit-memory`, and joins the exact runner with `&&`.
   The remote task facts record the host and receipt path. A failed or missing remote admission
   therefore creates no scientific process or output; an admission receipt is never moved between
   node contexts.
5. The operator launches once, observes the same task id to terminal state, and copies only the
   request-specific result root back to the local `temp/directions/` tree. It does not remove the
   remote worktree or output before the local copy is verified.

The node's base checkout is a Git partial clone with a sparse execution surface; per-run worktrees
remain exact-sha Git worktrees. This avoids transferring the repository's large historical result
corpus to a compute node while retaining Git identity for runners.

## Local fallback

Local execution is used for an explicitly Windows/local/device-pinned object, an exact dependency
or source surface not available on the remote node, or a remote resource/connection refusal. A
portable invocation may fall back locally only if no remote process was accepted and a fresh local
4 GiB admission passes. If remote acceptance is uncertain, the exact `agent-task` id is queried;
the command is not resent. A node change after question-relevant output is not a fallback.

Resource availability changes sequencing only. It does not change Portfolio priority, lifecycle,
claim ceiling, or scientific polarity.

## Scope and loading

This owner decision specifically authorizes the distributed/multi-node execution item in
`docs/project/ENGINEERING_SCOPE_SPEC.md` section 4 for this project-level route. It does not
authorize a scheduler, retry loop, lease system, or remote control plane.

No Codex application restart is required. Current sessions can read the tracked decision and node
declaration directly; newly created sessions load the updated project instructions and agent
definitions.
