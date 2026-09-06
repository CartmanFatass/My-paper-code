# FRRIE next-object selection after the R09 failure-chain map — 2026-09-06

Direction Manager: the Claude research hub. This selects the next object after the valid A01
(`A01_DIFFERENT_ORIGINAL_FAILURE`) and the read-only engineering map
`FRRIE_R09_FAILURE_CHAIN_MAP_20260906.md` (Grok Build, detached worktree at 43eec21e, no source
change, no run). Object tier under AGENTS.md §2: the next rung inside the open R09 third-root
family, whose B remains frozen and unexecuted (`FRRIE_R09_THIRD_ROOT_SCIENCE_CARD_20260905.md`,
INCOMPLETE).

## What the map established (observation of source, not of the failure)

- One `asdict` call site on the failing path (`tapes.py:96`), on a validated 12-field frozen
  slotted dataclass; no shadowing, monkeypatch or iterator argument anywhere in the launch bytes.
- The event-time loop of the same tape serializes the same class successfully before the uplink
  assignment at `tapes.py:216`, so a static "this class always fails" explanation is impossible.
- Before the production tapes (256 episodes × rosters 9 and 15, order 10⁶ SHA-256/`asdict`
  calls) `execute()` runs no native32 build, `ctypes.CDLL` or torch op; only the import-time
  libtorch and numpy loads precede tape construction. The output directory is created after the
  tapes, which is why neither R09 nor A01 left one.
- The R09 source blobs on the failing path are byte-identical between 43eec21e and `main`; `main`
  changed unrelated `b01/` training files that sit on the import graph.
- The A01 pdb commands printed the B01 training-tape address fields, which `R02EvaluationAddress`
  does not have, and used `up 6`, which overshoots; the map lists the working expressions.
- Local Windows CPython 3.10.20 constructs one roster-9 tape on these bytes without error.

## Options

1. **A02 capture reconstruction** (recommended): the A01 chain again at 43eec21e on wsl_4070
   under faulthandler and pdb, with a corrected read-only postmortem command file that prints the
   actual evaluation address, the field-iteration locals and the tape-loop indices. 60 s cap,
   zero source change, ~20 s expected. The A01 intake proposed exactly this discriminator.
2. **Runtime-isolation probe**: a new small script building the production tapes at 43eec21e in
   two arms, without and with the import-time torch load, to test whether the import-time
   library load is implicated. New source, two invocations, a few minutes; informative even if
   the failure is intermittent, but it changes the chain and would be selected blind to the
   failing state that option 1 can still capture cheaply.
3. **Outcome-blind full R09 attempt at a new sha**, `-X faulthandler`, no pdb, 2,700 s cap. The
   third-root B itself. The failure has appeared in two of two runs of this chain, both during
   tape construction; §8 permits a credible alternative path without resolving unrelated
   failures, but this failure is on the B's own primary path and is not unrelated.
4. **Park the third-root family** at this boundary. Nothing forces it; the family is the
   direction's only unexecuted discriminator and the diagnosis is cheap.

## Recommendation, selection and provenance

Recommendation: option 1, because it is the cheapest observation that can turn the A01 fact into
a classifiable one, uses the recorded chain unchanged, and its no-failure branch would itself
justify option 3 (intermittency recorded). Runner-up: option 2, which follows if A02 captures a
non-source cause or the signal recurs. Options are not a close call.

Owner-delegated decision (unattended, 2026-09-03 instruction): **(1)**. Label
`OWNER_DELEGATED`, kind `selection`, owner flag `none`. The card
`FRRIE_R09_SEGFAULT_A02_CAPTURE_SCIENCE_CARD_20260906.md` is frozen with the DM prediction
`A02_SERIALIZATION_FAILURE_CAPTURED`; the owner prediction slot is not taken. No Pro round is a
launch condition for this A (§11.4). Execution goes to the operator on wsl_4070 at 43eec21e; the
Grok map is the engineering preparation, no CM code task exists, and no result-bearing B is
launched by this selection.

## What this selection does not do

It does not rehabilitate R09, score its native-return prediction, change the frozen third-root
card, classify the original SIGSEGV, change lifecycle or priority, or authorize a second
diagnostic if the first returns a preferred-failure-absent branch.

scope: none
