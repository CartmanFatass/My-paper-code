# FRRIE A04 preparation intake — 2026-09-07

Assignment: **P11-FRRIE-A04-PREP-01**. Outcome: a concrete single-stack A/RECON card and
unchanged-code handoff prepared; no installation, tape generation, scientific invocation or Pro Send.

## 1. What was checked and the rule applied

Read A03 intake §4 and the two current A03-related DIRECTION sections, the current Portfolio row
and P11 assignment, A03 card/CM record, runner and directly exercised input code. Applied evidence
spec §§3–4, 5.1, 11.4, 11.7–11.9 and engineering-scope §§4–5. No historical citation expansion or
new mechanism attribution was needed. Scientific-tools was used for metadata retrieval and counts.

P11's controlling preparation boundary, verbatim:

> No A04 result-bearing probe, repeated T0 arm, local R09 fallback or scientific execution is
> allocated by P11.

A03 intake §4 stop, verbatim:

> Card consequence for this branch: a host/interpreter question for the owner, and **no R09
> launch on this substrate until it is answered**.

Read-only inventory is valid only as an access/version/package fact under §5.1. It supplies no
new evidence that an interpreter, NumPy wheel, host or source code caused the old failures.

## 2. Inventory evidence and counts (direct observation)

Raw output: [node inventory](FRRIE_A04_PREPARATION_NODE_INVENTORY_20260907.json), observed
`2026-09-07T21:07:12.169379+00:00` through configured SSH target `hmasd-wsl-node`.
The command used `/usr/bin/python3 -I -S -` with stdlib `pathlib`, `subprocess`, `sys`, `sysconfig`
and JSON. Child version queries also used `-I -S`; package facts came from reading installed
METADATA/WHEEL and pyvenv.cfg files, never NumPy, torch or FRRIE imports. `-S` reports base-prefix
behavior; interpreter identity here uses executable resolution and version, not activated sys.path.

| Surface | Observed fact |
| --- | --- |
| Host | `LAPTOP-U9TDKC8A`, Ubuntu 24.04.3 LTS, x86_64, WSL2 kernel `6.6.87.2-microsoft-standard-WSL2` |
| Configured project Python | `/home/wu/.venvs/hmasd/bin/python` resolves to uv CPython 3.10.21, Clang 22.1.3; configuration includes optimization and LTO |
| Alternative Python | `/usr/bin/python3` resolves to `/usr/bin/python3.12`, CPython 3.12.3, GCC 13.3.0 |
| Project NumPy | `1.26.3`, wheel tags `cp310-cp310-manylinux_2_17_x86_64` / `manylinux2014_x86_64` |
| Project torch metadata | `2.7.0+cu118`, cp310; no torch import was performed |
| Alternative package roots | No NumPy metadata/package directory found in `/usr/lib/python3/dist-packages`, `/usr/local/lib/python3.12/dist-packages`, or the two checked CBSC system312 venv site-packages |
| Existing alternative venvs | `hmasd-cbsc-system312-a02-20260907` and `...a03-20260907` both resolve to system312; neither is an FRRIE installation target |
| Venv tool | `/home/wu/.local/bin/uv --version` returned `uv 0.12.9 (x86_64-unknown-linux-gnu)` |

The inventory checked five package roots and 13 executable-name paths. Nine Python paths reduce
to two build identities; four `*-config` helpers printed usage and exited 1, not interpreter
failures. A first shell/heredoc transport produced a trailing `NameError: PY`; the corrected
stdin-to-Python read returned exit 0. Neither call imported the workload or changed the node.
Raw runtime copy: `temp/directions/finite_resource_relational_inductive_efficiency/exp/a04_p11_prep_20260907/`.

The [count output](FRRIE_A04_PREPARATION_COUNTS_20260907.json) was computed locally using only
stdlib arithmetic from the existing T0 loop. Prospective count is 384 tape constructions / 128
distinct inputs; all actual P11 learner, native, tape and model counts are **zero**. No memory
admission was sought because no result-bearing probe was attempted. Inventory wall is not an
A04 runtime estimate. The card retains unknown installation/import and system312 throughput costs.

## 3. Authority reconciliation and evidence bounds

No later A04 card was found in the direction tree. `item.py reviews --json` returned `[]` at
this clean boundary; the relevant September 6/7 audit owner cells are empty. Existing owner item
`20260906-frrie-002` is open with `auto_applied: null`, not an owner reply. It is preserved.

A03 intake §4 recommended a changed interpreter plus a separate same-uv/changed-wheel test;
its final sentence prohibited further FRRIE work on the uv interpreter. The later DIRECTION
section and owner item describe waiting for owner input to install. P11 now explicitly assigns
inventory and prospective preparation under ordinary delegation, **without** installation or
execution. It therefore permits this preparation without treating silence as an owner answer.
The historical claim that every isolated install exceeds unattended authority is not imported as
a general rule; this task stops at preparation because P11 expressly excludes execution.

The proposed single changed stack is an object-tier narrowing of that diagnostic, not a recast,
direction lifecycle action or answer to the old causal question. No system NumPy wheel was found;
changing from cp310 to cp312 necessarily changes the NumPy binary as well as Python. Full suspect
separation is neither available from this inventory nor required by the selected path question.
No new uv arm or Windows R09 route is commissioned. DIRECTION is not edited because no new
mechanism-level result exists.

Strongest support for trying this path: an actual alternate system build exists and A03's accepted
T0 implementation works without torch; the recorded Windows phase completed. Strongest
contradiction: A03 T0 failed after 128 tapes without torch or tracing, and this proposal retains
the physical host. Package availability/importability and full-chain completion are unobserved.
R06's positive N15 root-1 gap, R07's within-MEI negative N15 gap and R08's negligible chart-cut
attenuation remain the mechanism evidence; this inventory changes none of their readings.

## 4. Decisions this intake produces

1. **Object-tier preparation.** Options: (a) prepare one unchanged T0 invocation in a dedicated
   system312/NumPy1.26.3 environment; (b) seek a multi-arm interpreter/wheel attribution design;
   (c) yield without a concrete card. Recommend and select (a): it gives a bounded usable-path
   observation with known loop size, while (b) adds unneeded causal work and an unavailable wheel.
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Preparation only.
2. **Technical reuse.** Options: (a) retain the accepted runner, its raw A03 implementation label,
   and A04's distinct card/handle/root; (b) commission a renamed wrapper or metadata adapter.
   Recommend and select (a); source code needs no change. **Owner-delegated decision (unattended,
   2026-09-03 instruction): (a).** No new CM engineering assignment or comparison enrollment.

Owner flags: no close call, critic dissent or second recast. New-card item
`docs/research/portfolio/owner/inbox/2026-09-07/20260907-frrie-001.json` was created only through
`item.py`, with `auto_applied: accept` meaning preparation retained, not execution allocated.
Audit rows: `docs/research/portfolio/audit/2026-09-07.md#L81` and `#L82` in this branch.
No actual owner instruction was pending to mark answered.
Prediction: no A04 result, so unscored; owner slot not taken. The A03 DM's failed prediction stays
failed. This inventory was not preceded by a new prediction and is not scored retrospectively.

## 5. Return boundary and next discriminator

Designated authoring checkout: `C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`, shared
branch `codex/frrie`. It began clean/detached at `5f4d6f26bd3b73a8e49656d7c10077b688f36183`;
no live native FRRIE writer or local/remote FRRIE branch was found. The old HEAD is preserved at
`refs/archive/frrie-pre-p11-20260907`. This existing checkout was brought to committed main input
`d6844bb25f6f1030aa7123467935861dcc719450` before authoring. No new worktree was made.

Checks: explicit bound-source diff empty; outer and inner command text each passed `bash -n`
(exit 0, parse only); candidate LF payload 1379 bytes; one supervisor and one T0 invocation in
the text; all owner packet evidence quotes match their source; Chinese brief 346 characters.
These static checks ran no command payload, package import, resource admission or workload.

Root integrates the explicit preparation commit and returns the candidate to Portfolio. Exact
remaining dependency: an allocated later task for **one** dedicated NumPy acquisition/install
and complete T0 probe (300 s plus 5 s kill grace), with a named CM collector. The
[handoff](FRRIE_R09_A04_PROSPECTIVE_HANDOFF_20260907.md) fixes its source, interpreter, command and
acceptance. Missing package bytes and untested importability are technical facts, not scientific
polarity. Return here for scientific intake after any allocated terminal result. Do not relaunch
R09 or infer a Portfolio/lifecycle action from this return.

Chinese inventory/preparation brief:
`docs/research/portfolio/owner/briefs/finite_resource_relational_inductive_efficiency/2026-09-07_A04-preparation.md`.

scope: none
