# FRRIE R09 tape-isolation probe A03 — intake (2026-09-06)

Object `FRRIE-R09-SEGFAULT-A03-TAPE-ISOLATION-20260906` (A/RECON), card
`FRRIE_R09_SEGFAULT_A03_TAPE_ISOLATION_SCIENCE_CARD_20260906.md`, CM record
`FRRIE_R09_SEGFAULT_A03_TAPE_ISOLATION_CM_RECORD_20260906.md` (Grok Build, hub-reviewed,
`50283c9cf`). Direction Manager: the Claude research hub. Evidence root
`a03_tape_isolation_20260906/{t0,t1,t2}/` (summary where written, task logs, admissions,
supervisor files, T2 stdin; byte-verified copies).

## 1. Provenance and technical facts (observation)

- Node `wsl_4070`, detached worktree `/home/wu/hmasd-worktrees/frrie-a03-50283c9cf` at
  `50283c9cfffeaba913572fe43f5a8dbf311abe7e` (clean before and after), interpreter
  `/home/wu/.venvs/hmasd/bin/python` = CPython 3.10.21 (`Sep 1 2026`, `Clang 22.1.3`, uv-managed
  `cpython-3.10-linux-x86_64-gnu`), numpy 1.26.3, torch 2.7.0+cu118 where imported, one compute
  thread, `-X faulthandler`, `timeout 300 s` per arm, fresh admission before each arm (15.67 GiB
  available, floor 4 GiB, all three passed), one `agent-task` per arm, launched once each in
  the order T0, T1, T2. The seven exercised modules are byte-identical to `43eec21e` (CM record).
- Work per repetition as frozen: 64 training tapes for updates 1 and 2 (T0 through the
  parent-module replica, T1/T2 through `production_training_inputs`), plus 512 evaluation tapes
  in T1/T2. Root `…0003`, label `FRRIE-B09-CONTACT-BLOCK-003`.

| arm | torch at work start | tracer | completed work before failure | failure | wall | exit |
| --- | --- | --- | --- | --- | --- | --- |
| T0 | absent (also absent at exit) | none | rep 0: update 1 (2.96 s), update 2 (2.95 s) | rep 1, update 1: `AttributeError: 'tuple_iterator' object has no attribute 'name'` in `dataclasses._asdict_inner` ← `tapes.py:373 generate_episode_tape` | 8 s | 1 |
| T1 | present (`2.7.0+cu118`) | none | rep 0: 512 evaluation tapes (18.62 s), update 1 (3.01 s), update 2 (3.01 s) | rep 1, evaluation: `SystemError: error return without exception set` in `R02EvaluationAddress.__init__` ← `b01_contact_r02/tapes.py:217` | 31 s | 1 |
| T2 | present | pdb (`-c continue`) | rep 0 evaluation and update 1 at least (no summary written) | SIGSEGV in `rng.py:185 validate` ← `tapes.py:101 _semantic_address` ← `tapes.py:374 generate_episode_tape` ← `b01_contact_r02/tapes.py:246 production_training_inputs` (faulthandler) | 84 s | 139 |

- Digests: T0 and T1 produced identical digests for update 1 (`0f0fb392…`) and update 2
  (`7e155dc5…`); T0's update-1 digest equals the local Windows CM run's digest (`0f0fb392…`).
  Every completed phase in every arm agrees with every other arm's same phase; no completed
  repetition differs from another. T2 wrote no summary, so its digests are unobserved.
- Peak RSS: T0 38 MB, T1 349 MB. `sys.flags` ordinary (hash randomization on). No terminal
  exhausted the cap.

## 2. Rule applied (card, first match)

> `A03_CORRUPTION_WITHOUT_TORCH`: T0 raises an original exception or fatal signal in its tape
> work. The corruption does not require the torch extension or a tracer; the interpreter build,
> numpy, or the host is implicated.

**Reading: `A03_CORRUPTION_WITHOUT_TORCH`.** T0, a process that never imported torch (verified
absent in `sys.modules` at work start and at exit) and ran no tracer, produced a Python-level
impossibility (`fields(dataclass)` yielding a `tuple_iterator` where a `Field` belongs) inside
the same address-hashing tape loop after 128 successful tapes, the fourth distinct failure of
this class in the family (R09 SIGSEGV; A01 `tuple_iterator` field; A02 out-of-range `basin`;
A03 T0 `tuple_iterator`, T1 `SystemError`, T2 SIGSEGV). T1 and T2 failing too is consistent
with, not additional to, that reading; the branches `ONLY_WITH_TORCH` and `ONLY_UNDER_PDB` are
excluded because T0 did not pass. `DIGEST_MISMATCH` does not apply: every completed phase
matched across arms and against the local run, so the corruption manifests as exceptions and
signals, not as silently wrong tape bytes, on this evidence. Not a deterministic source defect:
the same bytes complete the same work locally (Windows, conda CPython 3.10, 6.9 s per update)
and completed it on the node twice before failing in each arm.

Bounded: which of interpreter build, numpy wheel, or host (memory, kernel, CPU) is the agent is
not identified; three repetitions per arm were enough to reproduce in every arm, so the failure
is not rare at this exposure (three of three arms, each within 31 s of tape work).

## 3. Predictions scored

- DM: `ONLY_WITH_TORCH` or `ONLY_UNDER_PDB` (low confidence), `NO_CORRUPTION` the competitor,
  `WITHOUT_TORCH` least likely because the node had run much pure-Python and numpy work without
  incident. **Wrong**: the least-likely branch is the observed one.
- Owner: not taken (unattended).

## 4. Decisions this intake produces

Card consequence for this branch: a host/interpreter question for the owner, and **no R09
launch on this substrate until it is answered**. Applied as follows.

- Object tier, `OWNER_DELEGATED`: the A03 result is accepted as valid at A/RECON; the R09 B
  stays frozen and unexecuted; no fourth repetition, no extra arm. Options considered for the
  next step: (a) a second isolation probe A04 that repeats the T0 arm unchanged under a
  different interpreter build available on the node (system CPython or a fresh non-uv build)
  and, separately, under the same uv interpreter with the numpy wheel replaced by the node's
  system numpy, so the interpreter and the wheel are separated from the host (recommended:
  zero science, minutes of work, discriminates the three suspects); (b) run the full R09 chain
  on the local Windows environment (host portability was not predeclared for R09's native
  build; rejected as a launch, kept as a fallback question for the owner); (c) park FRRIE at
  this boundary until the owner rules on the node. The owner item below carries (a)–(c) with
  (a) recommended; under the standing delegation the hub freezes the A04 card once the node's
  interpreter inventory (operator, 2026-09-06) shows which builds exist, and does not launch
  anything else on the uv interpreter for FRRIE. The Codex loop, which shares this node, is
  informed through the direction record and Portfolio row.
- No Portfolio change; FRRIE remains `ACTIVE`/HIGH and stays in the Claude working set only for
  A04; if no alternative interpreter exists on the node, FRRIE parks and the slot is refilled.

Owner brief (Chinese): `docs/research/portfolio/owner/briefs/finite_resource_relational_inductive_efficiency/2026-09-06_R09-A03-tape-isolation.md`.

scope: none
