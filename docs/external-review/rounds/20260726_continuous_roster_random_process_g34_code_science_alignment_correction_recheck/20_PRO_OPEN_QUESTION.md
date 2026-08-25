# External Pro open question: G34 alignment-correction recheck

```text
review_type=CODE_SCIENCE_ALIGNMENT_CORRECTION_RECHECK
audit_mode=read_only_correction_diff
compute_budget=zero
original_audit_target_commit=599e3b2c9209f969baceb1e1a452953fa4375900
original_mismatch=docs/external-review/rounds/20260726_continuous_roster_random_process_g34_code_science_alignment_audit/21_PRO_OPEN_RAW.md
repair_implementation_code_commit=973589414a865cf79ef9f80a33a8feb2d4aabf40
recheck_target_commit=15f95889f4a318905ba45a1977b5e9079d114545
index=docs/research/designs/CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_CODE_SCIENCE_INDEX.md
formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

You are External Pro acting only under `.agents/roles/EXTERNAL_PRO.md`. Inspect
the exact pushed recheck target and the allow-list in
`01_SHARED_SOURCE_MANIFEST.md`. This is the single permitted correction-only
recheck of the repaired claim-bearing diff. Do not reopen any design point or
repeat the full original audit.

Question: are both exact result-changing paths named in the original
`MISMATCH` now closed before any G34 positive branch can be selected?

Check only:

1. Whether every model-bearing cell independently strict-loads the exact G32
   checkpoint declared by its replicate, checkpoint kind and capacity, and
   requires the computed digest to equal both serialized before/after states;
   a zero/final checkpoint routed under the wrong label must fail closed.
2. Whether every episode serializes its 48-step reward and actual roster-size
   traces; utility, minimum-step utility, all four event windows, all five
   process segments and roster validity are recomputed from those traces before
   analysis; inconsistent summary or trace tampering must fail closed rather
   than feed the bootstrap or positive branch.
3. Whether the corrected index and focused tests point to and exercise those
   two closures without changing the frozen source, cell inventory, controller,
   threshold, sample count, algorithm, estimand or first-match semantics.

Return exactly one disposition:

- `AUDIT_DISPOSITION=ALIGNED` if both exact mismatch paths are closed in the
  recheck target.
- `AUDIT_DISPOSITION=MISMATCH` only if one of those two exact paths remains,
  naming the still-conflicting code behavior and the smallest in-contract
  correction.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only if judging one of those two
  corrections exposes one previously unstated result-changing scientific
  choice.

Do not identify unrelated new issues, broaden the audit, request compute, or
introduce a new algorithm, controller, solver, source, search, threshold,
evidence volume, experiment or formal run. Do not accept or redesign PM's code.
Stop after the single scoped disposition.
