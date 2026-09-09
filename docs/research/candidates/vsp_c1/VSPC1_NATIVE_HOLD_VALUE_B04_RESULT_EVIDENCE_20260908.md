# VSPC1 B04 — E0 launch-failure evidence

**No scientific performance result.** P66's sole accepted supervisor submission
failed before opening the launch script, before remote admission and before any
model, learner or native evaluation. There are zero new independent training
pairs. Under the explicit safe-stop instruction, the submission allowance is
exhausted and no correction or new submission follows.

## Bound identity and rule applied verbatim

The [B04 card](VSPC1_NATIVE_HOLD_VALUE_B04_SCIENCE_CARD_20260908.md) fixed
master8202, the unchanged normalized GATED/full-MLP/H comparison, UP(.60),
MEI .01 and original complete caps. Accepted scientific source is
`a33a3820fe9d4a46a3231bcf267afc956554b6c5`; final staging/review evidence is
`97151526cf409d8eb16a88a353ea6037813cd019`; DM binding is
`0a15321955b9dbea57f5cec0174421bbb62e82e6`. Those records describe the intended
method and actually verified staged source. They are not execution evidence.

The applicable card §4 row is:

> A primary dependency is incomplete
>
> No dependent performance judgment; retain independently trustworthy counts/returns. Missing H alone leaves a trustworthy primary pair reportable with H-relative use unresolved.

Here neither learned endpoint nor H exists. UP, WITHIN and DOWN cannot be read
from an absent Delta. The prediction remains unscored, not a miss or a zero-valued
endpoint. Under evidence-spec §§4,5.2,11.8.6–7, a transport failure does not become
scientific polarity. B objects have no consumption state; P66 allocation closure
does not mean that a valid complete B result or any C object was consumed.

## Direct observed failure and deviation

[CM collection](VSPC1_NATIVE_HOLD_VALUE_B04_COLLECTION_20260908.md) and its
[full raw evidence](VSPC1_NATIVE_HOLD_VALUE_B04_COLLECTION_EVIDENCE_20260908.json)
are committed at `337ba6f3893a71354820c661150834f1cce50e77`, returned by Root
after main integration. Direct status is `failed`, exit127, supervisor PID3014192,
tmux inactive. The full terminal log records start and end at
`2026-09-09T07:55:19+08:00` = `2026-09-08T23:55:19Z`, displayed duration0s.
The later `uptime_seconds=791` is not runtime; the terminal record is decisive.

The accepted script path was:

```text
/home/wu/hmasd-inputs/vspc1_hold_value_b04_8202_a33a3820fe9d.sh
```

The actual retained supervisor wrapper instead executes:

```text
/bin/bash /home/wu-inputs/vspc1_hold_value_b04_8202_a33a3820fe9d.sh
```

The full log reports:

```text
/bin/bash: /home/wu-inputs/vspc1_hold_value_b04_8202_a33a3820fe9d.sh: No such file or directory
```

This directly establishes an actual-versus-accepted command-path deviation.
Root identified its submission typo in the collection/intake handoff. The missing
path prevented the script from opening; therefore its enclosing timer, `cd`,
remote admission and scientific runner chain were never reached. This is not an
exception thrown by the normalized learner or a failure of its accepted source.

Both the intended output root
`/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b04_8202_a33a3820fe9d`
and sibling `native_hold_value_b04_8202_a33a3820fe9d_admission.json` were directly
absent at collection. No summary, checkpoint, episode/rollout rows, parameter
movement, moment state, native return or evaluation artifact was produced.

## Counts, resources and preserved receipts

| Quantity | Observed/bounded fact |
| --- | ---: |
| Accepted supervisor submissions | 1 |
| Remote admission invocations | 0 |
| Scientific invocations / independent training pairs / learned fits | 0 /0 /0 |
| Native team steps / Adam calls / evaluation episodes | 0 /0 /0 |
| Scientific model/optimizer/moment state | Not created |
| Delta, learned/H endpoints, prediction score | Unavailable/unscored |
| Native wall and peak memory | Unmeasured/null |
| Supervisor displayed duration | 0s, coarse wrapper display |

The zero-exposure facts follow from the directly observed pre-script boundary
and absent roots; they are not values from a generated native counter artifact.
Displayed0s does not mean zero machine work or measured learner wall. The expected
286720 steps/2048 Adam/96 evaluations and1800s-per-arm/3600s-pair caps were never
exercised by a scientific process, so no complete scientific cap-conformance
measurement exists. The earlier engineering result remains seven focused cases
in5.3719231s process wall,35 new non-test lines and scope §4:none, without a §5
implementation-budget breach. The submitted command failed conformance to the
accepted path; that deviation remains separate from code acceptance.

Original terminal files remain untouched at
`/home/wu/.agent-tasks/vspc1_hold_value_b04_8202_a33a3820fe9d/`.
The full task log, actual wrapper, raw status/exit and absence observations are
retained in the committed JSON. Its local source copy is
`temp/directions/vsp_c1/collection/native_hold_value_b04_8202_a33a3820fe9d/failed_collection_evidence.json`.
The accepted script/source/staging, B03 failed and corrected handles, and all
historical scientific evidence remain preserved. Collection and DM intake use
stored/direct read-only evidence only; no repair, restaging, admission, test,
model, retry or relaunch occurred during intake.

The [DM intake](VSPC1_NATIVE_HOLD_VALUE_B04_INTAKE_20260908.md) records the
unscored B04 forecast, unchanged prior science, allocation closure and clean
safe stop. The learning-repeatability question remains unanswered by P66.
