# G35 formal-result scientific disposition brief

```text
semantic_author=project_manager
artifact_scope=reviewer_visible_scientific_boundary
scientific_authority=external_pro
review_mode=FORMAL_RESULT_SCIENTIFIC_DISPOSITION
round=20260726_continuous_roster_reactive_reduction_g35_formal_result_review
formal_compute_authority=none
registered_branch=CURRENT_STATE_REDUCTION_SUFFICIENT_G35
```

## Purpose

Formal iteration 26 has a mechanically valid, non-rescuable registered branch:
`CURRENT_STATE_REDUCTION_SUFFICIENT_G35`. Both freshly paired arms pass the
frozen access gates. The REC-minus-CS pooled and per-capacity upper confidence
bounds all remain below the frozen 0.05 materiality margin, so the exact
first-match selector stops at the current-state-sufficient branch.

This round asks External Pro only for the scientific meaning of that branch,
the smallest retained and retired units, exact CDC/portfolio/ledger edits and
one next scientific action inside the active dynamic-roster research goal. PM
owns code and mechanical closure but has no scientific authority.

## Frozen facts

- source commit: `f626dfd8a345ef670e08e601344b67e28ffb3563`;
- CPU, torch `2.7.0+cpu`, one thread;
- train/evaluate/analyze exit codes all zero; no retry, resume or fallback;
- schema 2, `formal=true`, `operational_valid=true`, no operational errors;
- 3 replicates, 2 arms, 99 evaluation cells, 12,672 evaluation episodes;
- 1,069,056 total real transitions and 3,600 training optimizer steps;
- every conclusion metric recomputed from serialized 48-step traces;
- all fresh zero/final checkpoint and manifest-digest bindings reproduced;
- code-science correction recheck disposition: `ALIGNED`;
- first-match branch reproduced exactly as
  `CURRENT_STATE_REDUCTION_SUFFICIENT_G35`.

Both common arm access predicates are true. The REC-minus-CS pooled CI95 is
`[-0.0173505, -0.0081213, 0.0007130]`; the capacity 6/8/12 UCBs are
`-0.0066404`, `0.0030353` and `0.0054082`, each below the registered `0.05`
margin. `current_state_sufficient=true`; `recurrent_advantage=false`.

## Decision boundary

Decide only what G35-P0 establishes about a fully informed current-state arm
relative to the matched learned-state-carry arm under this source, training
budget, architecture, controls and gates. Do not turn a finite-margin
sufficiency result into global recurrence impossibility or remove the retained
true-time, age, previous-action, centralized-critic or G31-credit controls.

G33 remains abandoned by direct user instruction and cannot be selected. The
answer does not authorize code, Git, browser actions, workflow changes or
compute. If the one next action is claim-bearing, freeze its exact scientific
boundary or name the smallest required design audit; do not leave PM to choose
among scientifically distinct defaults.
