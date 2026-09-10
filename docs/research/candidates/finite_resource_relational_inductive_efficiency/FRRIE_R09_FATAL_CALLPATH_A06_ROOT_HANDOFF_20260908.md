# FRRIE R09 fatal-callpath A06 Root handoff — 2026-09-08

Static preparation is complete, with **zero scientific invocations**. DM next
binds this exact command in the [A06 card](FRRIE_R09_FATAL_CALLPATH_A06_SCIENCE_CARD_20260908.md).
Root then owns the one detached P31 dispatch and same-handle observation.
Authority is card §§2–5 at `4ebe6b9ee1520a06a9b2f0111ac8704d645e7522`, P31
at main `989238f449e5e7b2ad59068b6e56096556d6586c`, and evidence-spec §§4,11.8.6–7.

Preparation used the tracked-clean existing checkout
`C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`, branch `codex/frrie`,
starting at the card revision above. The only authored tracked path is this handoff.
No code, test, card, input or prior evidence changed; no child was created.

## 1. Source, runtime and retained input

| Binding | Exact value |
| --- | --- |
| Scientific/preflight source | `43eec21e9584c83e5e8d940402d7e4570b454e59` |
| Accepted helper/input revision | `30643b7359b35c6e9d5751147d0999bc629a966d` |
| A05 base command revision | `137ed1fda47662f4eb51fa9d70f41a6a3675d2a2` |
| Node / host / supervisor | `hmasd-wsl-node` / `LAPTOP-U9TDKC8A` / `/usr/local/bin/agent-task` |
| Fresh handle | `frrie-a06-fatal-callpath-p31-43eec21e` |
| Fresh detached cwd | `/home/wu/hmasd-worktrees/frrie-a06-fatal-callpath-p31-43eec21e` at original 43ee |
| Existing interpreter | `/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python` |
| Pinned runtime | P22 system CPython 3.12.3/GCC 13.3.0; existing 23 pins including NumPy 1.26.3/Torch 2.7.0+cu118 |
| Fresh output, relative to cwd | `temp/directions/finite_resource_relational_inductive_efficiency/exp/a06_fatal_callpath_p31` |
| Fatal stderr | `/home/wu/.agent-tasks/frrie-a06-fatal-callpath-p31-43eec21e/task.log` |
| Optional bounded capture / learner outputs | Fresh output's `summary.json` / `learner/` |

Reuse the existing staged files outside the scientific tree, unchanged:

| Staged file | Committed source at 30643b7 | Bytes / SHA256 |
| --- | --- | --- |
| `/home/wu/hmasd-inputs/frrie-a05-first-exception-p27/capture.py` | `experiments/candidates/finite_resource_relational_inductive_efficiency/r09_first_exception_a05/capture.py` | 11464 / `0e75801266db0dc339da63ddd1a1f5a981b5b26bfc4ae243e87f8feb678f87b8` |
| `/home/wu/hmasd-inputs/frrie-a05-first-exception-p27/pdb_commands.txt` | `docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_FIRST_EXCEPTION_A05_PDB_COMMANDS_20260907.txt` | 173 / `361c1df2f98b3291416cb1b7f20195440dd1f01a535586123f8889aab4a643f0` |

The two-line stdin remains the accepted standalone exec in a fresh namespace,
then q/EOF. The `FRRIE_A05_HELPER`, `FRRIE_A05_OUTPUT` names and `FRRIE_A05`
heredoc delimiter deliberately stay unchanged. Reuse accepted staged readback
and fixture evidence from [A05 handoff §3](FRRIE_R09_FIRST_EXCEPTION_A05_ROOT_HANDOFF_20260907.md#3-actual-focused-acceptance-and-readback)
and its final card acceptance. No fixture, scientific smoke, import, installation,
cost pilot or new staging was performed for A06 preparation.

## 2. Sole Root command

After DM commits/pushes its exact binding, Root uses the configured supervisor
argv: `/usr/local/bin/agent-task`, `run`,
`frrie-a06-fatal-callpath-p31-43eec21e`, followed by the entire literal below as
**one argument**, on `hmasd-wsl-node`. Root provisions the fresh detached original
source tree; the native build remains inside the timed chain, with no reused
P22/A05 native artifact. The supervisor provides its handle directory for GNU time.

```sh
/usr/bin/time -f 'process_wall_seconds=%e peak_rss_kib=%M' -o /home/wu/.agent-tasks/frrie-a06-fatal-callpath-p31-43eec21e/process-time.txt /usr/bin/timeout --signal=TERM --kill-after=5s 115s /usr/bin/env -u BASH_ENV -u ENV -u ALL_PROXY -u all_proxy /bin/bash --noprofile --norc <<'FRRIE_A05'
set -euo pipefail
repo=/home/wu/hmasd-worktrees/frrie-a06-fatal-callpath-p31-43eec21e
out="$repo/temp/directions/finite_resource_relational_inductive_efficiency/exp/a06_fatal_callpath_p31"
python=/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python
cd "$repo"
export PATH=/usr/bin:/bin:/home/wu/.local/bin:/usr/lib/wsl/lib
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export FRRIE_A05_HELPER=/home/wu/hmasd-inputs/frrie-a05-first-exception-p27/capture.py
export FRRIE_A05_OUTPUT="$out"
/usr/bin/python3.12 scripts/hmasd_resource_preflight.py admit-memory --out "$out/learner_admission.json" && "$python" -X faulthandler -m pdb -c continue -m scripts.run_frrie_b01_contact_r09 --output-root "$out/learner" --admission-receipt "$out/learner_admission.json" --seed 3 < /home/wu/hmasd-inputs/frrie-a05-first-exception-p27/pdb_commands.txt
FRRIE_A05
```

Read this document's sole sh fence from its published Git blob; remove only the
single LF separating the final `FRRIE_A05` line from the closing fence.
The resulting literal is **1200 UTF-8 bytes, zero CR bytes**, SHA256
**`67f598644882f596ecbfbced2454003c69c9a04cb153a6f62b23079e00bf72e3`**.
The scientific Python argv adds only `-X faulthandler` before `-m pdb`;
`-c continue`, original module, output/admission arguments and `--seed 3` persist.

The cap is one complete **TERM 115s + at most 5s grace = 120s** chain, including
fresh original-source memory admission, imports, native build/load, initialization,
evaluation, training, fatal reporting/capture, publication and termination.
Original `admit-memory && program` requires physical and effective available
memory of at least 4GiB immediately before program entry on the actual node.
Root retains all terminal, stderr, time, admission and partial/normal output facts
and observes this exact handle; uncertain acceptance never permits another launch.

Original root 3, CPU FP32/original FP64 reductions, Torch 1/four-worker/native 32,
LR 0.003, beta boxes, full 128 paired updates, checkpoints/uniform/rosters and RNG
remain fixed. No first-input cutoff, changed schedule, runtime or source repair.

## 3. Static acceptance and cost/coverage limits

Checks read the A05 command directly from the Git blob at 137ed1f. Its 1187-byte
SHA256 matches the accepted `2976134a5690041fea083bef024aff1e28c92225c4d42479ccca38599893976d`.
Exactly these replacements produce the A06 literal:

| Replacement | Occurrences |
| --- | ---: |
| `frrie-a05-first-exception-p27-43eec21e` → `frrie-a06-fatal-callpath-p31-43eec21e` | 2 (supervisor time path and cwd) |
| `exp/a05_first_exception_p27` → `exp/a06_fatal_callpath_p31` | 1 |
| `"$python" -m pdb` → `"$python" -X faulthandler -m pdb` | 1 |

Reversing only those replacements is byte-equal to the A05 Git-blob literal.
Both the outer command and isolated heredoc body were separately supplied on
stdin to `ssh hmasd-wsl-node /bin/bash --noprofile --norc -n`; both returned 0
with empty stdout/stderr. This parsed text only: no command body, Python package,
helper or scientific program ran. Both helper/input Git blobs at 30643b7 match
the frozen lengths/digests and are byte-identical to the starting HEAD blobs.
The new document's extracted literal also matches the checked command bytes.

Retained receipts: direction checkout's
`temp/directions/finite_resource_relational_inductive_efficiency/exp/a06_preparation_p31/command.sh`
and `static_acceptance.json`. They contain exact substitution counts, parser argv,
exit/output and unchanged committed-input hashes. These static facts establish
command conformance, not fatal-stack availability, no-second-body behavior in a
future scientific run, or runtime reliability. A05's accepted fixture remains
the reused recipe/publication-path coverage; no fixture was repeated.

Cost projection: this is one seedless A chain with the card's 120s complete cap,
not a sweep. A05's 42.71s complete wall is the existing anchor, not a forecast of
recurrence or completion. Maximum invocation-wall sum and execution critical path
are 120s; per-arm timing, aggregate CPU, control-plane elapsed and scratch remain
unknown. The card's original exposure ceilings remain unchanged; actual work is
unknown until retained output supports it. Missing output does not imply zero work.
Post-learner coverage is the accepted A05 capture fixture; the added fatal stderr
channel is statically enabled here and still requires actual terminal evidence.

## 4. Terminal route and scope

On terminal receipt this same CM collects E0: fatal signal/termination, active
thread and separate other-thread frames, original exception/capture if any,
partial/normal publication and trustworthy counts. DM applies A06 card §2's first
matching row and writes intake/brief/audit. A readable Python stack locates a path;
it does not identify a native causal writer. Debugger/supervisor exit 0 alone does
not establish original-program completion. Missing trace, ambiguity, different
failure or timeout ends this allocation without retry, fallback, cap extension,
new seed, source repair, full B or another diagnostic.

Engineering scope §4: no new machinery or code. Card §4 explicitly requests reuse
of bounded optional diagnostic reporting; the only observation amendment is the
existing interpreter startup option. Input/digest checks document this exact
assignment and add no runtime guard. The three CM comparison batches are complete.
Next owner is DM for exact command binding, then Root for dispatch/observation.

scope: none
