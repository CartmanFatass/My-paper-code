# CBSC B05 command preparation: concrete source gap

**SOURCE_REPAIR_NEEDED; not launch-ready.** P18 source inspection found that the accepted runner cannot
execute the selected fresh formal seed 21223. A separately scoped source
correction is required. No launch literal is represented as executable here.
No source, target-runtime import, probe, test, remote staging, admission,
installation or scientific invocation was performed.

## Assignment and inspected binding

P18 authority: `80dd2af11d204ef6f57dd9aed98dc5558f69c801`,
[Portfolio handoff](../../portfolio/handoffs/2026-09-07-p18-cbsc-fresh-pair-preparation.md).
Prospective [B05 card](CBSC_OPPORTUNITY_CREDIT_B05_SCIENCE_CARD_20260907.md)
is bound at `a213567ce576ba836427b8490f183120b9de23e6`; its source-gap,
fresh seed/runtime/primary, work and ordered-return sections agree with this
SOURCE_REPAIR_NEEDED disposition.
Inputs: [P17 intake, Concrete next-task need and discriminator](CBSC_LOCAL_ACQUISITION_P17_INTAKE_20260907.md#concrete-next-task-need-and-discriminator)
and B04 card sections Selected learner and credit target; Host, information,
RNG and evaluation; Exposure, cost and execution; Prediction, MEI, reading rule
and stopping. The prospective B05 changes supplied by DM are seed 21223,
both new arms, the P17-observed runtime, and fresh outer paths/handles.

Read-only checkout: `C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`,
`codex/cbsc`, initial clean revision
`cb821b99bf8248b1b79ccb23cca7a4de2c324066`.
`git diff --exit-code a3c2a49bf7002639d43a94f460b688d50c6c42dd --`
returned no differences for the runner, the complete `opportunity_credit_b04/`
directory and the complete `omrc_b01/` directory. This establishes unchanged
bytes for those declared surfaces, not runtime execution in CPython 3.12.3.
Separate supplied preflight provenance remains
`ec8866b3968fcb1566976ce405d7c552d4d9a5de`.

## Blocking source facts

1. `scripts/run_cbsc_opportunity_credit_b04.py:30` compares `--seed` with
   `expected_seed(args.engineering)` and reports an argparse error on mismatch.
2. `opportunity_credit_b04/run.py:28` defines `expected_seed`; line 29 returns
   21211 for engineering and **21217 for formal**. Local stdlib AST inspection
   confirmed those literal values without importing the module.
3. `run.py:108` independently applies the same seed check inside `run_arm` and
   raises `ValueError` on mismatch. Calling that function directly would not
   make seed 21223 conformant. It would already create the output directory and
   set the Torch thread count before this check; no such call was made.

A descendant commit with unchanged source retains both checks. Substituting
21217 would change the selected scientific seed. Runtime monkeypatching or a
relabelling wrapper would be an implementation change outside this preparation.
The precise repair need is a separately selected fresh-object entry/profile
that accepts seed 21223 through both boundaries while preserving the B04 learner,
RNG addressing, evaluation, pairing and old-object behavior. This record does
not choose or implement that repair.

## Minimal correction surface and acceptance facts

The concrete affected surfaces are `scripts/run_cbsc_opportunity_credit_b04.py`
(CLI selection), `opportunity_credit_b04/run.py` (formal seed validation and
summary/pair identity), `opportunity_credit_b04/learner.py` (OBJECT definition)
and `opportunity_credit_b04/snapshot.py` (checkpoint identity consumer). The
latter two require explicit identity treatment, not a change to numerical credit
or optimizer code. Whether to add a fresh B05 entry/profile instead of editing
historical entry points belongs to that bounded implementation assignment.
No change to `omrc_b01/` is motivated by the observed seed/identity gap.

Correction acceptance must establish seed 21223 reaching host, model, action
uniforms and minibatch addressing for both fresh arms; truthful and consistent
B05 summary/checkpoint/pair identity; preserved B04 profile behavior; unchanged
sampled decision-plus-settlement targets, rollout normalization, decision-only
value loss, full recurrent BPTT, public adapters, CPU FP32/one-thread settings,
48 rollouts/768 Adam steps and update 0/48 evaluation. Pair identity checks,
RAW rule reuse, all 32 endpoint differences, full checkpoint/publication readback
and in-STRUCT pairing must remain intact. The exact source/preflight/runtime
binding and complete per-arm deadline/admission literal must then be completed.
This specifies acceptance needs without authorizing a code change or new smoke.

## Historical labels and metadata boundary

`opportunity_credit_b04/learner.py:17` hardcodes
`OBJECT = "CBSC-OPPORTUNITY-CREDIT-B04"`. The runner's console result,
`run.py:187` summaries, `snapshot.py:24` checkpoint payloads and paired summary
all use that object value. Module/runner docstrings also name B04.
The RNG namespace remains B1_RUN by scientific design and is not an identity bug.

Summaries/checkpoints carry actual seed and source information, and fresh output
paths could distinguish a new observation externally. They do not change the
hardcoded artifact object field into B05. Moreover, no seed-21223 artifact can be
produced through the accepted entry points. The correction must explicitly settle
honest B05 object metadata; no claim of unambiguous prospective B05 artifacts is
made from an output directory alone. Existing summaries record thread count,
dtype and device but not interpreter executable/version; the selected prefix
and P17 metadata remain external runtime provenance, not a new runtime test.

## Preserved prospective bindings and return route

Requested runtime, already observed by P17:
`/home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python`,
CPython 3.12.3, NumPy 1.26.3, Torch 2.7.0+cu118. Reuse the P17 primary evidence;
metadata readiness does not establish learner reliability. CPU FP32, one scientific
process and one Torch thread remain selected.

Requested remote cwd:
`/home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907`.
Requested output parent:
`temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b05_20260907`,
with new `raw/` and `struct/` children. Requested handles:
`cbsc-b05-raw-20260907`, then `cbsc-b05-struct-20260907` under existing
`/usr/local/bin/agent-task` on `wsl_4070`. No checkout, output or handle was created.
Full executable source/admission/log/timeout literals remain unresolved because
the source cannot express the selected seed; these names are prospective only.

The unchanged loop arithmetic is 384 training episodes, 768 Adam steps,
58368 training transitions and 64 evaluations/9728 evaluation transitions per
arm, totaling 68096 train/evaluation transitions. Pair totals are twice these.
The three RAW rules add 96 existing-tape passes. Complete cost law includes
startup/admission, host generation, 48 project/rollout/PPO blocks, two evaluation/
checkpoint panels, RAW context, publication/readback, STRUCT pairing and process
finish. Existing B04-card planning references remain RAW 159.38 s and STRUCT
181.56 s (twice the larger historical same-arm B02/B03 walls); both are below
600 s, but they are not measurements of this runtime. No fresh timing was taken.
Requested complete caps remain 600 s per arm / 1200 s summed, including grace;
summed cap is distinct from study elapsed and aggregate CPU work.

After a separately scoped correction and accepted command binding, Root's ordered
route remains RAW observation -> this CM's terminal/primary/seed/runtime/count
collection -> STRUCT only if RAW integrity permits -> this CM's complete pair
collection -> DM intake. RAW score never chooses whether STRUCT runs. STRUCT
must publish/read back the pair inside its own cap; there is no third invocation.
No new engineering smoke or old-budget reset follows. For this preparation,
Root returns the concrete source gap to Portfolio for the bounded correction
assignment; no execution allocation is ready.
