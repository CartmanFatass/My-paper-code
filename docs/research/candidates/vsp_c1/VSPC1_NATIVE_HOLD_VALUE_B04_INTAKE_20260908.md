# VSPC1 P66/B04 intake — no scientific execution; safe stop

**P66 ends with a pre-script launch failure and no performance result.** The
actual supervisor payload used a different path from the reviewed script and
exited127 before remote admission or scientific state. The single submission
allowance is exhausted under Root's explicit safe-stop handoff. No correction,
restaging, repair, retry, new pair or replacement is selected.

## 1. What I checked and the rule applied

Root returned same-CM collection
`337ba6f3893a71354820c661150834f1cce50e77`, already integrated on main. I read
the [complete collection document](VSPC1_NATIVE_HOLD_VALUE_B04_COLLECTION_20260908.md)
and [raw evidence](VSPC1_NATIVE_HOLD_VALUE_B04_COLLECTION_EVIDENCE_20260908.json)
against the [card §§3–7](VSPC1_NATIVE_HOLD_VALUE_B04_SCIENCE_CARD_20260908.md#3-fresh-key-prediction-and-independent-unit),
accepted source/command and [staging receipt](VSPC1_NATIVE_HOLD_VALUE_B04_STAGING_EVIDENCE_20260908.json).
I inspected the exact handle, full task log, actual wrapper, raw exit/status,
absence of admission/output and the intended/submitted path difference. A short
stdlib read of those stored records reconciled status/exit/path/zero-exposure
fields and missing primary without creating a native artifact or running a model.
No CM check or command was repeated.

The controlling card row applies verbatim:

> A primary dependency is incomplete
>
> No dependent performance judgment; retain independently trustworthy counts/returns. Missing H alone leaves a trustworthy primary pair reportable with H-relative use unresolved.

All primary dependencies are unexecuted; this is not merely missing H. No Delta
exists, so none of UP/WITHIN/DOWN applies. The H and conditional-noise rows have
no endpoint to read. Evidence-spec §§4,5.2,11.8.6–7 preserve this launch-path fact
while prohibiting its conversion into a native negative or a zero return.
There is no scientific reinterpretation of the frozen method or earlier results.

The [Root operations rule](../../../project/ROOT_OPERATIONS.md#execute-the-supplied-launch-command)
also states:

> Supervisor acceptance, admission and scientific execution are separate facts. If a command
> fails before admission, retain its exact failed identity and evidence; continue only the
> already-authorized correction after acceptance is reconciled. Never infer a scientific retry,
> changed source or extra allocation from a wrapper failure.

Here Root explicitly instructed no correction/restage/repair/retry and closure
under the owner pause. The general possibility of an authorized pre-admission
correction does not supply one against that current instruction. No conflict or
additional decision is needed to execute the required safe stop.

## 2. Direct observation, exposure and execution conformance

Handle `vspc1_hold_value_b04_8202_a33a3820fe9d`, PID3014192, terminated
`failed`, exit127, tmux inactive. Start and end are both
2026-09-08T23:55:19Z (the raw log uses2026-09-09T07:55:19+08:00), displayed
duration0s. The later supervisor uptime791s is not a scientific or process wall
measurement; the terminal log records the immediate failure.

Accepted path:
`/home/wu/hmasd-inputs/vspc1_hold_value_b04_8202_a33a3820fe9d.sh`.
Actual wrapper path:
`/home/wu-inputs/vspc1_hold_value_b04_8202_a33a3820fe9d.sh`.
The direct wrapper and shell error establish the missing-path failure, and Root
identified its submission typo. The accepted staged script was not opened.
This execution deviation is distinct from the accepted source
`a33a3820fe9d4a46a3231bcf267afc956554b6c5`, its verified detached cwd and the
seven previously passed binding checks.

The admission receipt and output root were directly absent. There was one
accepted supervisor submission, **zero remote admissions, zero scientific
invocations, zero independent training pairs, zero learned fits, zero native
steps, zero Adam calls and zero evaluation episodes**. No model, optimizer,
scientific moment state, checkpoint, summary, endpoint or exposure measurement
was created. These zeros describe the established pre-script boundary, not a
counter file produced by an attempted fit. Native wall and peak RSS are null;
the coarse wrapper duration is not a measured native cost or scientific cap pass.

[E0 evidence](VSPC1_NATIVE_HOLD_VALUE_B04_RESULT_EVIDENCE_20260908.md) retains the
exact failure, counts, paths and resource distinctions. Complete algorithmic
work and caps remain the frozen planned286720 steps/2048 Adam/96 evaluations,
1800s per arm/3600s pair; no budget or source is changed after the failure.
No implementation scope §4 machinery or §5 budget breach was introduced. Actual
command conformance failed at submission; accepted code/check/staging facts do
not make that command equivalent to the reviewed payload.

The original remote log/wrapper/status/exit and local committed collection
remain intact. No source/script rewrite, cleanup of evidence, root recreation,
repair or new scientific call was performed. Root's archive/reclamation route
retains the task receipt and follows the owner's clean-boundary instruction.

## 3. Prediction and surviving scientific position

B04's prospective **UP(.60)** prediction is **unscored** because its event
`Delta>.01` is unavailable. There is no Brier value, missed prediction or
zero-valued observation. Owner prediction is **not taken (unattended)**.
No endpoint CSV or run-level summary is fabricated; `summarize_runs.py` is not
given zero scores or empty pseudo-runs. P66 adds n=0 training pairs.

B03/master8201 remains the sole normalized training-pair observation:

| Contrast | B03 mean difference | Conditional SE | Adverse episodes |
| --- | ---: | ---: | ---: |
| GATED−MLP | +.03980171530455754 | .006008657101475142 | 4/32 |
| GATED−H | +.03521279747565949 | .010408850908328956 | 9/32 |
| MLP−H | −.004588917828898052 | .012026063667580491 | 19/32 |

Its completed WITHIN(.55) forecast remains a miss with Brier .3025. B04's
unscored status does not erase that historical score. B03's earlier pre-admission
failure and corrected valid execution remain separate and unchanged in its
[intake](VSPC1_NATIVE_HOLD_VALUE_B03_INTAKE_20260908.md). The two unnormalized
pairs8101/8102, their adverse outcomes and forecast scores also remain unchanged
and unpooled with normalized evidence.

Claim ceiling: no new learning-performance claim from P66. The strongest prior
support is B03's local gate-package gain and positive GATED−H; its negative
MLP−H, adverse episodes, extra640 parameters, sparse hold exposure and shared
optimization alternatives still bound the result. Tuned matching headroom remains
absent. The repeatability question is unanswered because no second normalized
training pair ran. The launch failure neither strengthens nor contradicts the
proposed hold/state → centralized value/optimization → local action → native
return mechanism. Accepted mechanism-level DIRECTION science is left unchanged.

No new literature question or mechanism interpretation follows from this
transport fact; the existing question-driven sources remain in B03 intake §9.
There is no stable-superiority, normalization-causal, specialized hold-credit,
transfer, C, family/recast, lifecycle/priority or formal UAV-entry decision.

## 4. Decisions this intake produces

1. **Failure classification, object-tier technical.** Options: (a) retain the
   pre-script command-path failure with no scientific result; (b) label the
   package DOWN or assign zero return; (c) invalidate accepted numerical code
   from this launch error. Recommend/select (a), supported by the exact wrapper,
   terminal error and absent roots. Owner-delegated decision
   (unattended,2026-09-03 instruction): (a), **OWNER_DELEGATED**.
2. **Forecast handling, object-tier technical.** Options: (a) keep B04 UP(.60)
   unscored and preserve all prior scores; (b) score the absent primary as a
   miss or remove B03's completed forecast. Recommend/select (a).
   Owner-delegated decision (unattended,2026-09-03 instruction): (a),
   **OWNER_DELEGATED**. Owner prediction remains not taken.
3. **P66 closure and pause, explicit owner-directed technical boundary.**
   Options: (a) finish this failure intake, commit/push/archive it and stop;
   (b) correct/restage/resubmit, add a pair or request a replacement.
   Execute (a) under **OWNER_DIRECT safe pause**, as explicitly applied by
   Root's terminal handoff. There is no remaining execution allocation and no
   successor recommendation. This stops current work; it is not a direction
   PARK, family closure, new scientific polarity or a Portfolio disposition.

Root/CM use “consumed invocation” for the exhausted P66 submission allowance.
Record that allocation boundary without treating a B object as consumed:
there was one accepted supervisor submission, zero scientific invocations and
no valid complete B result. The missing learning observation is not supplied
by the closure decision. No attempt is quarantined as a failed algorithm run.

Owner reviews and relevant ledger owner cells are empty at this intake. The
explicit owner pause relayed by Root and recorded in card §7 controls regardless
of that empty console. The committed owner safe-pause handoff at
`6ca831a5a3431aaa89dc2151ee666191737705df` also requires completion/archival of
the assigned collection/intake, without replacement or new exposure. No owner
reply is invented, and no P1/P2 item is added for these ordinary technical facts.
The [daily audit](../../portfolio/audit/2026-09-08.md) records the decisions;
the [Chinese failure brief](../../portfolio/owner/briefs/vsp_c1/2026-09-08_VSPC1_NATIVE_HOLD_VALUE_B04.md)
reports this no-result boundary using the required six headings. Owner flag:none;
the actual submission deviation and unscored forecast are explicit.

## 5. Clean return and stop

P66's assigned route is exhausted under the safe-stop instruction. Root receives
this pushed intake/E0/card/handoff/audit/brief delivery, preserves parallel ledger
rows and archives it with the already-integrated collection. No run or collection
remains active in this DM/CM chain. The accepted B04 source and unused correct
script stay preserved as provenance; their existence grants no permission to run.

**No retry, repair, restaging, extra pair, replacement request or successor is
selected.** There is no next discriminator allocated during the pause. Further
research requires the owner's explicit resume and a new concrete assignment;
this intake does not author or request one. After Root's archival integration,
this direction chain stops at the clean boundary, with historical evidence intact.
