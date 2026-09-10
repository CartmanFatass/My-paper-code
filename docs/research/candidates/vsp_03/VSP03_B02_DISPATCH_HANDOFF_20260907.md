# VSP03 B02 exact dispatch handoff

**SUPERSEDED BY PATH_UNAVAILABLE STOP BEFORE DISPATCH.** Root/DM reported the same
DNS failure and directed no retry until external route state changes. The commands
below were prepared but never executed; they are retained as unexecuted technical
context, not an active dispatch request. See `VSP03_B02_RESULT_EVIDENCE_20260907.md`.

Root published and pushed accepted source/card at
`00ebefa5823dbb41e64aed11b90ba26a8ff97020`. Source acceptance and independent review
are complete. No pre-run model, rollout, helper rerun or fixture is needed.

CM's configured SSH attempt failed before remote connection:

```text
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node '/usr/local/bin/agent-task --help'
exit1: ssh: Could not resolve hostname hmasd-wsl-node: No such host is known.
```

This is a local hostname-resolution failure. No staging, admission, supervisor handle
acceptance or scientific invocation occurred. Root is the specified permitted route;
no alternate hostname, transport or execution node was attempted. CM retains technical
collection ownership. Proposed handle `vsp03-b02-p09-20260907` remains unaccepted.

## Exact source staging and invocation for Root

Use the configured remote repository `/home/wu/projects/HMASD`, interpreter
`/home/wu/.venvs/hmasd/bin/python`, and existing `/usr/local/bin/agent-task` interface.
Stage the pushed SHA as a detached worktree, without an authoring branch:

```bash
git -C /home/wu/projects/HMASD fetch origin main
git -C /home/wu/projects/HMASD worktree add --detach /home/wu/hmasd-worktrees/vsp03-b02-p09-00ebefa5823dbb41e64aed11b90ba26a8ff97020 00ebefa5823dbb41e64aed11b90ba26a8ff97020
```

If that path already exists, inspect it rather than overwrite it. Source staging and
SSH/supervisor dispatch are outside scientific runtime; the complete capped execution
starts with the reviewed outer timeout below. The supervisor cwd is exactly
`/home/wu/hmasd-worktrees/vsp03-b02-p09-00ebefa5823dbb41e64aed11b90ba26a8ff97020`.
Dispatch this payload once under handle `vsp03-b02-p09-20260907`:

```bash
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VSP03_B02_COMMAND='VSP03_B02_STARTED=$(/home/wu/.venvs/hmasd/bin/python -c "import time; print(time.perf_counter())")
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p09_20260907_admission.json && exec /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b02.py --seed 4 --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p09_20260907 --started-monotonic "$VSP03_B02_STARTED" --node wsl_4070'
/usr/bin/timeout --signal=KILL 120s bash -c "$VSP03_B02_COMMAND"
```

Root applies its known supervisor CLI syntax to this exact cwd/name/payload; CM's SSH
failure prevented inspecting that interface and this handoff does not invent flags.
The shell is identical to the independently reviewed launch boundary, with source SHA
and cwd now resolved. Require the adjacent destination receipt to admit memory; no
preflight-only scientific root/model/tape is constructed. No second invocation, retry,
local fallback or changed120s cap is authorized.

## Return to CM

Return authoritative acceptance (or refusal) for this same handle, actual supervisor
argv/cwd, task/log/status locations, and observation adoption ACK. At terminal return,
retain status/exit/whole-command elapsed plus complete stdout/stderr, admission JSON and
the terminal output tree. CM will inspect primary/per-world outputs, counts, curves,
exposure, weights/readback and complete-cap facts, prepare E0 under this preparation
root, and hand it to DM/Root for scientific intake and explicit-path publication.

The earlier local-Conda helper result remains3 passed in4.57s. It was not a remote
check. Root's separately reported Windows interpreter lacking NumPy is a distinct
dependency fact and neither invalidates that check nor authorizes a rerun.
