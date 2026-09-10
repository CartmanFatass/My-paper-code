# VSPC1 B02 scientific intake — 2026-09-08

**Accept valid complete UP for master8102.** The selected gated-critic package
again improves the primary over the intact MLP, with a positive GATED−H point
estimate. The claim remains two local finite-budget observations: MLP is below H
in both, markedly in B02, and neither seed variation nor mechanism attribution is resolved.

## 1. What I checked and the rule applied

Read the complete [CM collection](VSPC1_NATIVE_HOLD_VALUE_B02_COLLECTION_20260908.md)
and relevant unchanged native summary, exact executed script, supervisor log,
configuration/seeds/counts, checkpoints and calculation receipts in its
[evidence JSON](VSPC1_NATIVE_HOLD_VALUE_B02_COLLECTION_EVIDENCE_20260908.json),
commit `bc45c2f48c4072c2565ae5d93c34da2ffe829d25`.
Compared them against the frozen [B02 card §§2–7](VSPC1_NATIVE_HOLD_VALUE_B02_SCIENCE_CARD_20260908.md)
and current [P55 allocation](../../portfolio/handoffs/2026-09-08-p55-vspc1-independent-hold-value-pair.md).
Reused the accepted source and independent-review findings; no CM execution,
checkpoint evaluation or focused test was repeated by the DM.

The decisive rule is applied verbatim:

> Delta>.01 with trustworthy primary
>
> UP: one local native signal for the complete gated package; consider, but do not automatically allocate, one or two independent paired fits. Preserve H comparisons and every adverse episode.

The reference-limit rule also applies verbatim:

> One/both learners below H
>
> Retain trustworthy Delta, but narrow usable-control wording. Even an UP does not automatically justify another pair; do not rescue it by ignoring H.

The complete P55 allocation stop is:

> **P55 ends after this one pair and intake regardless of sign**.

The primary's dependencies are present: two512-episode fits,1024 actual Adam calls
per fit, and32 finite final sampled endpoint/reset identities per learner and H.
The summary names object B02, master8102 and source
`0ec208899f5e8b4c190ab7bd9806be2cc30b6fda`. The exact script and clean detached
source match the binding. Counts reconcile to286720 native team steps,
2048 Adam calls,96 final evaluations,1120 complete episodes and two constructors.
No partial step, missing H, nonfinite parameter/loss, cap breach or publication
gap is recorded. Actual compound PPO, reward/information and final-only selection
remain the accepted comparison. These facts establish technical conformance;
the return comparison below supplies the scientific observation.

Used the scientific-tools run-level summarizer on four learned endpoint rows,
already averaged once over each policy's32 final evaluations. Pairing is declared
within8101 and8102, with the common task label denoting the unchanged comparison.
H is excluded from training-run n. The [analysis JSON](VSPC1_NATIVE_HOLD_VALUE_B02_ANALYSIS_20260908.json)
retains per-pair contrasts, SEs/adverse identities, exposures, descriptive n2
summary, resource arithmetic and prediction score. The DM added zero model,
environment, optimizer or evaluation exposure.

## 2. Observation that bounds the result

| Pair | GATED−MLP (conditional SE) | GATED−H (conditional SE) | MLP−H (conditional SE) |
| --- | ---: | ---: | ---: |
| B01/8101 | +.0293656586 (.0052742257) | +.0194005494 (.0103456891) | −.0099651092 (.0107309824) |
| B02/8102 | +.1157271305 (.0094720558) | +.0265020852 (.0093884822) | −.0892250453 (.0107656186) |

B02 endpoints are GATED .1889430171, MLP .0732158866 and H .1624409319.
All three contrasts share the matched evaluation rows. Their adverse counts are
1/32,11/32 and29/32, respectively; B01's6/32,7/32 and16/32 remain preserved.
See the [B02 E0 record](VSPC1_NATIVE_HOLD_VALUE_B02_RESULT_EVIDENCE_20260908.md)
and unchanged [B01 E0](VSPC1_NATIVE_HOLD_VALUE_B01_RESULT_EVIDENCE_20260908.md).

Both individual primary means exceed .01. The run-level descriptive mean is
+.0725463945, sample SD .0610667824, **n=2 matched independent training pairs**.
This answers P55's bounded repeatability question positively at the point-estimate
level, with substantial difference in magnitude. It is not a new aggregate pass
criterion, stable population estimate, equivalence result or64-seed experiment.
Conditional episode SEs are not training-population uncertainty. The follow-on
was chosen after B01 UP; this adaptive selection is disclosed, not relabeled C.

The strongest support is two separately trained package gains at equal information
and learning exposure, with both GATED−H means positive. The strongest
qualification is the weak MLP reference: B02 is .089225 below H on average and
loses to H in29 episodes. Algebraically .089225 of its .115727 primary gap is the
H−MLP component,77.10%; the corresponding .026502 GATED−H component remains
positive. About91.78% of the widening from B01 is the lower MLP relative to its H
anchor. These are identities among observed means, not a diagnosis of value
learning, causal attribution to the gate or a claim that Hover is optimal.

The unchanged gate still acts through prior hold/state → scalar baseline and joint
optimization → local actor update → motion/service → native return. The actor has
no added information, recurrence continues during holds, and no duration-search or
counterfactual target is introduced. GATED/MLP native training nonzero-r fractions
are about1.124%/1.131%, and final d4 fractions .4875/.45625. Gate absolute movement
2.601896 and total relative movement .538932/.461260 establish exposure only.
The full MLP already shares nonlinear features; extra gate capacity, joint clipping,
value scale and seed-specific on-policy optimization remain surviving alternatives.
No evidence here selects one of those explanations or proves a defect.

Historical UCOPE6902 T−G−.0503654/T−H−.0332645 and6901 weak G−H−.0282038 remain
context with a different actor/clipping comparison. They are not pooled as gate
evidence or erased. Tuned same-information headroom is absent; H is attained and
untuned. No unique sharing, stable superiority, transfer, optimality, C promotion,
family closure, recast, lifecycle, priority or formal UAV-entry claim follows.

## 3. Question-driven evidence and next-discriminator rationale

The new question is whether the enlarged primary supports a stronger mechanism
claim, or chiefly motivates a comparison under a better-scaled shared training
regime. Reuse the verified ACAC/UTE/MVD source distinctions in
[B01 intake §3](VSPC1_NATIVE_HOLD_VALUE_B01_INTAKE_20260908.md#3-question-driven-literature-reuse):
they still limit this to a scalar critic-package effect. No new timing, macro
observation or value-decomposition mechanism is inferred from the second UP.

A bounded search of the current190-record formal Inst-sci catalog for the PPO/
value-normalization question found MAPPO/PopArt mentions in other records, but did
not locate the requested MAPPO study itself. The My-lib README still distinguishes
synthetic registries and manually imported searchable page snapshots; no verified
unified real-corpus coverage is claimed and fixtures are excluded. This is a local
coverage statement, not an absence-of-literature conclusion.

For that specific gap, verified Yu et al., *The Surprising Effectiveness of PPO
in Cooperative, Multi-Agent Games*, arXiv2103.01955v4 (4 Nov2022),
[§5.1](https://arxiv.org/html/2103.01955v4#S5.SS1). They regress normalized value
targets and restore value outputs to return units for advantage calculation;
their MPE/SMAC studies motivate value normalization as a practical training choice.
Their GAE/game settings differ from this complete gamma1-return-to-go UAV learner.
This supports a candidate comparison, not a diagnosis or a promised improvement here.

My inference is to prefer a later **single matched GATED/full-MLP comparison with
value-target normalization applied symmetrically to both**, keeping original actor
information, native reward/endpoint, H, learning counts and complete caps. This asks
whether the gate's local gain persists under the shared training change and whether
MLP's H-relative behavior improves. It does not require exact headroom, a full causal
audit or a tuning sweep before real B work. The future card must fix the running
statistics and native-unit value conversion; no code, key or final contract for that
comparison is frozen here. It would be a changed training regime, not a third seed
to pool with B01/B02. No implementation pointer is sent to CM during this intake.

## 4. Prediction, costs and owner flags

The prospective UP(.55) prediction is a **hit**, binary-event Brier .2025.
B01's WITHIN(.65) miss and .4225 score remain unchanged. Two different forecast
events do not establish calibration. Owner prediction: **not taken (unattended)**;
no relevant reply or owner ratification was present at this boundary.

B02 enclosing wall304.52s, conservative arm upper bounds158.206214s/146.874405s
and peak RSS542.0625MiB conform to the original complete caps. Both fresh memory
readings15642329088 bytes pass4GiB. Aggregate CPU/device/thread census and the
admission/startup/exit residual split remain unmeasured; the summary's raw labels
are preserved. Across the two valid pairs,573440 native steps/4096 Adam/192 eval
and613.15s summed enclosing wall give306.575s per valid pair. This is not study
critical-path time or aggregate CPU. The [E0](VSPC1_NATIVE_HOLD_VALUE_B02_RESULT_EVIDENCE_20260908.md)
records exact timings, receipts and engineering scope/no-breach facts.

For the unallocated next comparison, dominant work would remain2 fits×512×256
training team steps plus3×32×256 final evaluation steps:286720 native steps,
2048 Adam calls,96 evaluations; one pair, no nested search. Retain1800s/arm and
3600s/pair complete caps. Normalization adds ordinary scalar-statistic/target work
whose incremental wall is unmeasured; this does not justify a calibration run or
more native calls. No current invocation is allocated by this projection.

Owner flags: weak learned comparator relative to H; only two training pairs;
extra gate capacity/shared optimization alternatives; no tuned headroom. The
unexecuted next-task recommendation is flagged Portfolio in the audit/P2 item.
No critic dissent was overruled; the premature hard-KILL finding was resolved
before submission. The new-wrapper correction does not relax a scientific cap.

## 5. Decisions this intake produces

1. **Validity and reading, object tier.** Options: (a) accept valid complete UP
   with the H qualification; (b) invalidate because MLP is weak; (c) promote the
   large margin to stable superiority. Recommend and select (a). Complete primary
   dependencies satisfy the unchanged rule; neither the baseline weakness nor
   missing optional telemetry erases that observation. Owner-delegated decision
   (unattended,2026-09-03 instruction): (a). **OWNER_DELEGATED**.
2. **P55 execution boundary, object tier.** Options: (a) finish the one-pair
   allocation with all-outcome intake; (b) append an unassigned third pair or extra
   evaluation to refine the result. Select (a) under P55's explicit stop. B objects
   have no consumption state, and an allocation ending does not close the family.
   **OWNER_DELEGATED within P55 / no further invocation**.
3. **Next-discriminator advice, object tier.** Options: (a) recommend one later
   symmetrically value-normalized GATED/MLP/H B comparison; (b) recommend another
   unchanged pair; (c) retain the result with no next-investment recommendation.
   Recommend and select (a) as advice only. The observed MLP/H weakness makes a
   concrete common training change more informative than simply adding another
   instance to the same comparison; it does not prove normalization will help.
   Owner-delegated decision (unattended,2026-09-03 instruction): (a), a reversible
   recommendation with **zero code, seed allocation or execution** in P55.
4. **Future task allocation, Portfolio tier.** Options: ratify / refuse / amend
   that proposed bounded next assignment. Recommend ratify; none is executed by
   this DM. Return the question and cost above through Root to Portfolio for a new
   concrete assignment. This changes no cross-direction priority/lifecycle policy
   and invents no owner reply. **DM_RECOMMENDATION / NOT_EXECUTED**.

Recommend one later matched GATED-V/full-MLP/H B comparison with symmetric value-target normalization and unchanged native measurement and budgets; do not append another pair to P55.

The audit records these choices and the unexecuted recommendation. The owner-console
CLI created asynchronous P2 [20260908-vspc1-005](../../portfolio/owner/inbox/2026-09-08/20260908-vspc1-005.json)
with [this packet](VSPC1_NATIVE_HOLD_VALUE_B02_FOLLOWUP_OWNER_PACKET_20260908.json),
no auto-applied allocation and no invented reply; ordinary result/prediction facts
have no separate item. The Chinese
[owner brief](../../portfolio/owner/briefs/vsp_c1/2026-09-08_NATIVE-HOLD-VALUE-B02.md)
states the same bounded result and remaining question. P55's execution and intake
are complete, with no new Pro request, source change, run, third pair or extra H.
