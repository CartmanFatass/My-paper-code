# FRRIE R09 first-exception A05 — P27 terminal E0

The sole accepted A05 invocation ended in a hard failure: the shell reports
`Segmentation fault (core dumped)` for Python PID2765962; supervisor exit139,
status `failed`. No Python traceback, target `TypeError`, capture summary or
learner publication was retained. The technical reading is **A05_INCONCLUSIVE**;
DM owns scientific intake. No retry, repair, debugger launch or additional
scientific execution was performed during collection.

## Frozen binding and collected boundary

Apply [card §3](FRRIE_R09_FIRST_EXCEPTION_A05_SCIENCE_CARD_20260907.md#3-reading-rule-mei-and-prediction),
with exact execution bound by its §7 and the
[Root handoff](FRRIE_R09_FIRST_EXCEPTION_A05_ROOT_HANDOFF_20260907.md).
The remote handle is `frrie-a05-first-exception-p27-43eec21e`, node
`hmasd-wsl-node`; cwd is
`/home/wu/hmasd-worktrees/frrie-a05-first-exception-p27-43eec21e`.
Supervisor artifacts remain under `/home/wu/.agent-tasks/` plus that handle.
The output root is cwd plus
`temp/directions/finite_resource_relational_inductive_efficiency/exp/a05_first_exception_p27`.

Remote HEAD is the original `43eec21e9584c83e5e8d940402d7e4570b454e59`;
Git reports no tracked modifications and only the untracked `_native/` directory.
Its one native library, `libfrrie_ridgegate2z_external.so`, is 24488 bytes,
SHA256 `0c1af4bfd791337f4b420010a49cc1f156732a840faa7c69580d3aabcf6044b4`.
This inventory establishes artifact identity, not crash attribution or memory identity.
Runtime selection is the frozen existing offline CPython3.12 environment from
§7; collection did not import it or repeat runtime checks.

The staged helper/input SHA256 values match §7:
`0e75801266db0dc339da63ddd1a1f5a981b5b26bfc4ae243e87f8feb678f87b8`
and `361c1df2f98b3291416cb1b7f20195440dd1f01a535586123f8889aab4a643f0`.
Decoding the supervisor's Bash ANSI-C command literal produces exactly 1187 bytes,
SHA256 `2976134a5690041fea083bef024aff1e28c92225c4d42479ccca38599893976d`,
matching the accepted handoff 137ed1f; helper/input are bound at 30643b7.
The original seed 3, original schedule and one `pdb -c continue` invocation are
retained in that command. No changed-source or cap-breach fact was observed.
These checks do not establish runtime scientific-state equivalence.

## Termination, resources and publication

| Retained observation | Value / limit |
| --- | --- |
| Start / terminal UTC | 2026-09-08 06:24:06 / 06:24:48 |
| Supervisor duration | 42 seconds |
| GNU time complete process wall | 42.71 seconds |
| Frozen complete-chain cap | TERM 115s + kill-after 5s = 120s |
| GNU time peak RSS | 873284 KiB = 894242816 bytes (about 0.833 GiB) |
| Adjacent admission assessment | 2026-09-08T06:24:06.215770Z; passed |
| Available physical/effective memory | 15650717696 bytes, above 4294967296-byte floor |
| Cgroup headroom / aggregate CPU | Not recorded |
| Output-root file inventory | Only file: `learner_admission.json`, 504 bytes; empty `learner/` directory exists |
| Capture summary / learner output | Absent |
| Completed updates, episodes, agent slots | Unknown from retained A05 evidence |

Per-arm cost context: this is the one seedless A diagnostic chain, bounded by its
accepted 120s allocation, not a new sweep. Observed invocation wall is 42.71s;
there is one invocation, so summed invocation wall is 42.71s. Study/control-plane
elapsed and aggregate CPU are not measured. Admission and GNU time RSS are the
available resource observations; they do not establish aggregate concurrent RSS
or uninterrupted memory headroom.

Post-learner publication coverage before launch was the accepted inert target and
normal-entry fixture in card §7. This attempt produced neither a learner artifact
nor `summary.json` nor an `A05_SUMMARY_WRITTEN` marker. Fixture success does not
supply missing runtime state. The retained log does not expose how far scientific
execution advanced. In particular, historical P22 conditional counts are not
A05 counts.

Within this handle's cwd, output and supervisor paths, read-only filename/metadata
inspection found no crash core or fatal-stack artifact. Matches named `core.py`
and its bytecode were ordinary repository modules. The shell's `(core dumped)`
text therefore does not establish that a core is retained in these paths. No
host-wide search or debugger was run; a dump elsewhere remains unassessed.

## Card reading and evidence limits

Card §3's first applicable row is:

> `A05_INCONCLUSIVE`: Failed admission, different first exception, missing state/publication,
> timeout or hard failure prevents the preceding readings. Record the exact boundary and
> every trustworthy partial fact; stop without retry, clearance or scientific polarity.

Admission passed and the measured process ended within the cap. Hard failure plus
missing state/publication prevents both target-state readings and normal completion.
No observed target exception means neither recurrence nor nonrecurrence is established.
No source-defined structure check was captured. The evidence identifies process
termination, not a Python/native/library/host cause or a malformed-state writer.
The first Python exception, if any, remains unknown. This A object has no consumption
state, and no algorithm polarity follows from technical collection.

## Retention and acceptance

The adjacent [machine-readable E0](FRRIE_R09_FIRST_EXCEPTION_A05_RESULT_EVIDENCE_20260907.json)
contains admission values and SHA256/length manifests for every collected raw file.
Raw local copies are retained in the direction checkout at
`temp/directions/finite_resource_relational_inductive_efficiency/exp/a05_collection_p27/`:
`supervisor/`, `output/`, `remote_readback.txt`, and `accepted_command.sh`.
Remote originals remain in place. Collection inspected the actual terminal log,
exit/status, time receipt, complete output inventory, staged hashes and source state;
it reconstructed and checked the exact accepted command. The final recursive-file
assertion and all ten raw length/hash checks pass. An initial directory-inclusive
assertion failed because the empty `learner/` directory exists; file absence was
confirmed and that directory is explicitly recorded in the JSON. These checks establish
the reported technical boundary, not scientific success. Only this E0 and its JSON
are authored; the card, source, intake and prior evidence remain with their owners.
Root integrates this evidence and resumes the existing DM for card §3 intake.

scope: none
