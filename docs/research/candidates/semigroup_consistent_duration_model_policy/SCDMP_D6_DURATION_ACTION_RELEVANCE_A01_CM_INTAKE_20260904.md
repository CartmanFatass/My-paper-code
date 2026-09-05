# SCDMP D6 duration-action relevance A01 — CM intake (2026-09-04)

- Object: `SCDMP-D6-DURATION-ACTION-RELEVANCE-A01`
- Evidence class: A/RECON
- Implementation commit: `368f5eda848ce92a2dc1b0d2a3d84651fb02454c`
- Engineering disposition: technically accepted for one frozen scientific invocation
- Scientific result: none

## What this intake checked

1. The returned diff is confined to the declared A01 package, runner, tests and the permitted
   outcome-blind numeric card appendix. It imports no withdrawn-B package, model, optimizer,
   learner or branch rule.
2. The generated native translation unit comes from the canonical source by one plain
   `tau[i] - 0.88` to `tau[i] - 0.92` substitution. Direct no-index diff showed that as the only
   changed native line; `Z_LIMIT=.25` and every other native equation remain unchanged.
3. The runner fixes source streams `9011/k7` and `9013/k13`, targets `64/160/256`, literal
   `p=(1,2,3,4), q=0`, the six action order, evaluation domain `9029`, sixteen prospectively
   materialized tapes per state, same-`k` continuation, native endpoint and exact integer
   `Y/S/V/B7/B13/D/R7/R13/W_j/W` reducers.
4. The successful path requires exactly two source trajectories and, if the population exists,
   1,152 candidate missions/evaluator calls. It reports actual source/candidate/native transition
   counts and state/action/graph terminal-family counts. Its seven branches match the frozen order.
5. Independent high-risk review initially returned three findings: orchestration over 30%, an
   unneeded non-Windows RSS branch and loss of accumulated counts on cap-stop invalid publication.
   Narrow repairs reduced conservative physical orchestration to `216/723 = 29.88%`, retained only
   the Windows RSS path, and made both cap paths publish accumulated counts with
   `A_INVALID_EVIDENCE`. Independent re-review closed all three.
6. The one permitted focused invocation ran the parameterized seven-branch tests and the sole toy
   native CLI smoke: `8 passed, 1 warning in 6.13 s`. The warning is the repository's existing
   pytest configuration warning, not an A01 failure.
7. Direct toy observations were one source trajectory, two native missions, 687 native
   transitions, `5.603353600017726 s` smoke wall and
   `t_native_mission=0.002741849995800294 s`. It published no A branch and declared no scientific
   state.
8. The frozen cost law gives
   `P=2×(0.002741849995800294×1,154)+60=66.32818979030708 s`, within the `1,800 s` cap.
9. Non-test research code is `723/2,000` lines, the runner is `172/600`, tests are 66 lines, and
   conservative orchestration is `29.88%`. `scope: none`; no §4 machinery was added.
10. CM ran no resource preflight and no scientific A invocation. Six-state establishment, the
    1,152-mission table and every A branch remain unobserved.

## Observation and bounded interpretation

Technical acceptance establishes only that the frozen source/census path compiles in its toy
profile, the branch rule is represented, actual activity can be counted and the prospective
machine-time projection is below cap. It does not establish that the fixed source trajectories
reach all six states, that full tapes terminate conformantly, that `W`, `R7` or `R13` have any
value, or that D6 is useful.

The strongest technical support is the independent re-review plus the direct native toy path. The
strongest residual risk is that the full fixed source population and 1,152 mission inventory have
not run. That uncertainty is exactly what the A object measures and is not an engineering reason
to add another smoke.

## Decisions this intake produces

Options:

1. **(a), recommended:** accept the conforming implementation and cost row, commit this intake,
   then launch exactly one A01 invocation at the committed bytes; the runner itself performs the
   fresh 4 GiB admission before native state creation.
2. **(b):** require another smoke or repeated focused suite, contrary to the one-smoke contract and
   without a named unresolved defect.
3. **(c):** reject or quarantine the implementation despite the closed independent review and
   passing direct observations.

Recommendation: (a). It is the next frozen rung, changes no scientific meaning, stays under every
engineering/resource budget and is the only option that observes the admitted A question.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance label:
`OWNER_DELEGATED`. The audit ledger records this decision. It authorizes only the exact command:

```text
python scripts/run_scdmp_d6_duration_action_relevance_a01.py --seed 9029 run
  --output-root temp/directions/semigroup_consistent_duration_model_policy/exp/d6_duration_action_relevance_a01/A01_20260904
  --receipt temp/directions/semigroup_consistent_duration_model_policy/exp/d6_duration_action_relevance_a01/A01_20260904_admission.json
  --projected-seconds 66.32818979030708
```

The result root, receipt and sibling stdout/stderr logs must be absent before launch. The process
must be detached. No second invocation, changed coordinate, retry, resume or result-aware extension
is authorized.
