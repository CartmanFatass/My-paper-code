# N / k / Many-Agent MARL Deep Dive

This directory is the focused reading and code-inspection workspace for the
HMASD variable-roster and asynchronous-skill-lifetime research question.

## Research question

Can a cooperative MARL architecture simultaneously:

1. keep coordination computation and parameter semantics independent of the
   active team size `N`;
2. survive within-episode leave, rejoin, dropout, and new-agent events; and
3. decouple each agent's realized skill lifetime `T_i` from the shared check
   clock `k0` without breaking SMDP credit or PPO on-policy semantics?

No selected paper solves all three. The purpose of this folder is to isolate
the smallest reusable mechanism from each paper and record its migration
boundary.

## Layout

- `papers/`: downloaded conference PDFs. These are local-only because the
  project ignores PDF files.
- `analysis/`: one mechanism-level analysis per paper.
- `code/`: shallow official source checkouts selected after analysis. This
  directory is local-only and ignored by the project Git repository.
- `PAPER_SELECTION.md`: selection rationale and download status.
- `SYNTHESIS.md`: cross-paper architecture and experiment implications.
- `CODE_INDEX.md`: exact repositories, revisions, key files, and inspection
  status.

## Decision labels

- `ABSORB`: the mechanism directly fills an HMASD contract gap.
- `CONDITIONAL`: useful only behind a separate causal gate or after adapting
  incompatible assumptions.
- `DIAGNOSTIC`: useful as a comparator, stress test, or measurement tool.
- `DO_NOT_ABSORB`: conflicts with the current algorithm contract.

This is literature and implementation-inspection work only. It does not
authorize a successor implementation or experiment launch.

## Completed corpus

- 8 conference papers with locally verified PDFs;
- 8 paper-by-paper mechanism and code-boundary analyses;
- 6 selected official source checkouts;
- 2 paper-only candidates whose code was deliberately not downloaded after
  the contract mismatch was established.

Read [SYNTHESIS.md](SYNTHESIS.md) first for the cross-paper decision, then
[CODE_INDEX.md](CODE_INDEX.md) for exact source snapshots and key files.

## Per-paper analyses

| ID | Analysis | Primary value |
|---|---|---|
| P01 | [ACE](analysis/P01_ACE.md) | asynchronous execution and dropout stress |
| P02 | [ACAC](analysis/P02_ACAC.md) | duration-correct asynchronous credit |
| P03 | [InforMARL](analysis/P03_InforMARL.md) | variable-size local graph representation |
| P04 | [Sable](analysis/P04_Sable.md) | 1,000+ agent sequence-scaling reference |
| P05 | [ExpoComm](analysis/P05_ExpoComm.md) | bounded sparse many-agent topology |
| P06 | [Safe-M3-UCRL](analysis/P06_SafeM3UCRL.md) | mean-field and population-safety boundary |
| P07 | [CT-MARL](analysis/P07_CTMARL.md) | irregular-time value-semantics diagnostic |
| P08 | [IARO](analysis/P08_IARO.md) | relative representation and synchronization boundary |
