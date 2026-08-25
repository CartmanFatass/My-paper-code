# External Pro open question: G35 alignment-correction recheck

```text
review_type=CODE_SCIENCE_ALIGNMENT_CORRECTION_RECHECK
audit_mode=read_only_correction_diff
compute_budget=zero
original_audit_target_commit=49b3ba9399b056bd601863d6b0f2305c222f1f66
original_mismatch=docs/external-review/rounds/20260726_continuous_roster_reactive_reduction_g35_code_science_alignment_audit/21_PRO_OPEN_RAW.md
repair_implementation_code_commit=f626dfd8a345ef670e08e601344b67e28ffb3563
recheck_target_commit=472178e3cc7675a8ba1044558b47dd094c34138f
index=docs/research/designs/CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_CODE_SCIENCE_INDEX.md
formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

You are External Pro acting only under `.agents/roles/EXTERNAL_PRO.md`. Inspect
the exact pushed recheck target and the allow-list in
`01_SHARED_SOURCE_MANIFEST.md`. This is the single permitted correction-only
recheck of the repaired claim-bearing diff. Do not reopen any design point or
repeat the full original audit.

Question: is the exact result-changing formal-preflight route named in the
original `MISMATCH` now closed before training and again before any
conclusion-bearing G35 formal branch can be selected?

Check only:

1. Whether formal preflight loads `train_manifest.json`,
   `evaluation_manifest.json` and `analysis_result.json`, runs the existing
   training and evaluation validators, and fails before training on an
   unreadable, summary-only or otherwise invalid artifact set.
2. Whether it requires exact equality with the frozen nonformal configuration:
   one replicate, two arms, 10 fast plus 10 return-to-go updates per arm, 33
   cells, 28,032 real transitions, 120 optimizer steps and zero evaluation
   updates; a wrong-inventory preflight must fail closed.
3. Whether the projection is recomputed from the three finite nonnegative
   serialized stage times; whether analysis is bound to the exact validated
   train and evaluation files by digest; and whether the recomputed projection,
   not a favorable stored summary alone, must be at or below 28,800 seconds.
4. Whether formal artifact validation repeats the same check from the
   serialized absolute `preflight_root`, so later path, manifest, digest or
   stage-time tampering routes analysis to the invalid branch.
5. Whether the corrected index and focused tests point to and exercise these
   closures without changing an arm, source, seed, credit rule, threshold,
   evidence volume, estimand or first-match branch.

Return exactly one disposition:

- `AUDIT_DISPOSITION=ALIGNED` if the exact mismatch route is closed in the
  recheck target.
- `AUDIT_DISPOSITION=MISMATCH` only if that exact route remains, naming the
  still-conflicting code behavior and the smallest in-contract correction.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only if judging this correction
  exposes one previously unstated result-changing scientific choice.

Do not identify unrelated new issues, broaden the audit, request compute, or
introduce a new algorithm, controller, solver, source, search, threshold,
evidence volume, experiment or formal run. Do not accept or redesign PM's code.
Stop after the single scoped disposition.
