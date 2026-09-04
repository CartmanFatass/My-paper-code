# UCOPE numerical-locus diagnostic — resumed engineering intake

- Date: 2026-09-04
- Evidence class / claim ceiling: **A/RECON**, one-block numerical implementation fact only
- Parent: `UCOPE-A-RECON-THREE-WITNESS-ROOT-TARGET-VS-ROOT-FIT-AUDIT-R01`
- Accepted plan: `UCOPE_ROOT_TARGET_VS_ROOT_FIT_AUDIT_R01_NUMERICAL_LOCUS_PLAN_20260904.md`
- Resume authority: owner instruction “我们开始推进自动研究流程”, relayed by Root; the earlier pause is superseded. Root records the separate Portfolio ratification.
- Source baseline: `8d1c597871b38edc7d5f139f34f5a3ce2941c7d0`

## What I checked

I read the actual checkout, root and area instructions, engineering scope specification, evidence
specification including controlling section 11, current Portfolio row, latest DIRECTION entries,
the numerical plan, parent card, rejected implementation record and attempt-02 evidence/intake.
The isolated DM worktree starts clean at the source baseline. Owner reviews for September 4 and
the audit owner column have no UCOPE override; September 3 has no review file. The owner-console
`reviews` command reports no unapplied instructions. The primary checkout review agrees with the
worktree copy.

Direct read-only inspection on configured `wsl_4070` found both historical supervisor entries
inactive: `ucope_root_target_fit_r01_997f49c3_01` has exit 2 and no result root;
`ucope_root_target_fit_r01_997f49c3_02` has exit 6 and its original receipt and summary.
This rechecks terminal state; the earlier CM's recorded reproduction remains the basis for
classifying the shell failure and the eight numerical predicate failures.

| retained remote artifact | bytes | SHA-256 |
| --- | ---: | --- |
| accepted three-witness input in `/home/wu/hmasd-inputs/ucope_root_target_fit_r01_997f49c3_02/summary.json` | 1,273,684 | `1c8b1d217fc924271da62061f7226642a3d040995aba069cabb5df9ff336b676` |
| attempt-02 summary under its exact worktree's result root | 8,366 | `d966848ec6e7ff1361bca1b2a99910879d65af95467098ded9bdb4666f657ccd` |
| attempt-02 admission at that root | 504 | `4bdab9062efb51ed8feefc10ab9960bd2b7acdc2bd9ec18a37bbc90f8d7fbb63` |

No historical task, root, receipt or input is replaced or resumed.

## Exact resumed boundary

The diagnostic is the plan's lexicographically first failure block: seed
`ucope-scout-r01-b1-fresh-00`, fold 0, eight contexts, 40,960 episodes per context, offset
2,000,000. Each of its two pinned node invocations replays **327,680 episodes and 1,638,400
transitions**. The parent audit's **983,040 episodes and 4,915,200 transitions** describe its
three-seed workload, which is not launched by this resume.

The nodes are part of the technical estimand: remote emit-solve, then Windows compare-solve over
the local reconstruction and the unchanged remote payload. This is not a local fallback. There
are zero new seed/draw/sample identities, learner rows, models, optimizers, gradient steps or
parameter updates. One MSE tail is reconstructed per node, then three root solves remotely and
six locally. The machine-time cap remains **61.827 seconds per node invocation**, with no
third invocation, parent rerun, tolerance change or alternative driver.

The existing `CR.root_targets_fp32` computes targets with the accepted FP32 scorer and returns
them in float64 storage. The plan's term “FP32 targets” names that computation. Preserve the
helper's returned dtype, values and C-order bytes; converting storage to float32 would change the
solver input and is not part of this implementation. `numpy.linalg.lstsq(..., rcond=None)` and
the absolute `1e-12` boundary remain unchanged.

The environment-to-consequence path remains accepted deterministic event rows → root/tail role
ownership → same available information → retained tail values → root target/projection. This
diagnostic observes the numerical implementation of that path; it cannot evaluate native action
benefit. The fixed host has no roster, slot-lifetime, membership-change or partner-adaptation
estimand. Its binding structure is `systems / information flow`; this particular numerical
question does not arise from multi-agent non-stationarity.

## Evidence retained at its original meaning

The rejected draft's **98/295 = 33.22%** orchestration was a real engineering-budget breach and
remains documented. It produced no diagnostic result. A different implementation must remove
actual duplicated machinery, without semantic padding, relabeling orchestration, losing required
facts, or waiving the 30% limit.

The separate paid-acquisition B observation remains **5/6 treatment policies positive** under the
competence-free acquisition predicate, with full `+0.021437` gain wherever the treatment pays.
Three-witness coverage remains **6/6 versus 4/6** tail agreement with full competence **3/6 for
both arms** and two adverse root over-probes. Neither the old locks' historical wording nor the
later technical failures erase these observations.

No competent tuned baseline/headroom package has been identified. That limits the separate
competent-baseline comparison; it is not a universal B admission condition and does not block
this read-only numerical diagnostic.

## Decisions this intake produces

### Decision 1 — implement the unchanged diagnostic through direct reuse (object tier)

Options:

- **(a) Replace duplicated wrappers with direct calls to existing binding, resource facts,
  reconstruction, target and solve helpers; accept only a plan-preserving diff below the scope
  budgets.** Execute the already selected diagnostic if engineering acceptance succeeds.
- **(b) Return the earlier architecture's blocker without checking the identified direct-reuse
  path.** Keep the question unresolved and yield the slot immediately.

Recommendation: **(a)**. Existing functions expose the required numerical path and several of
the previously duplicated wrappers, providing a specific reversible way to test the dependency.
If the revised diff still breaches the budget, return it and yield with the exact blocker.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. This is an engineering implementation choice inside the accepted object, not
a new family, direction disposition or Portfolio action. CM owns the isolated implementation,
focused tests, source-line classification and direct runtime observation; the DM interprets the
return against the unchanged plan.

## Boundary state

At this written boundary the implementation is in progress and no diagnostic has launched.
The plan's DM prediction remains identical-byte inputs with a solver difference above the
absolute boundary. Owner prediction remains `not taken (unattended)`. No prediction is scored
before a complete two-node result. The next discriminator is the plan's six-branch comparison,
subject to conformant implementation and fresh node-local admission at each invocation.

Terminal follow-up: direct reuse also exceeded the scope budget and was returned without any
launch. See `UCOPE_ROOT_TARGET_VS_ROOT_FIT_AUDIT_R01_RESUME_TERMINAL_INTAKE_20260904.md` for the
independent 127/219 classification, no-run counts, owner items and clean scheduling handoff.

## Evidence

- `UCOPE_ROOT_TARGET_VS_ROOT_FIT_AUDIT_R01_NUMERICAL_LOCUS_PLAN_20260904.md`
- `UCOPE_ROOT_TARGET_VS_ROOT_FIT_AUDIT_R01_NUMERICAL_LOCUS_IMPLEMENTATION_BLOCKER_20260904.md`
- `UCOPE_ROOT_TARGET_VS_ROOT_FIT_AUDIT_R01_ATTEMPT02_EVIDENCE_20260904.md`
- `UCOPE_ROOT_TARGET_VS_ROOT_FIT_AUDIT_R01_ATTEMPT02_INTAKE_20260904.md`
- `UCOPE_PAID_ACQUISITION_B01_RESULT_EVIDENCE_20260903.md`
- `UCOPE_THREE_WITNESS_HINGE_R01_INTAKE_20260904.md`
- `UCOPE_A1_COMPETENT_TUNED_BASELINE_CENSUS_20260904.md`
