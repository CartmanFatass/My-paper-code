# Open question: the G20R identification floor cannot separate the two failures it exists to separate

```text
round=20260724_g20r_identification_floor
branch=untied-k
semantic_author=project_manager
scientific_authority=external_pro
artifact_scope=reviewer_visible_code_side
repair_owner=project_manager_orchestrator
predecessor_round=20260724_g20_credit_rule_zero_fixed_point_r2
compute_spent=one_340_second_bounded_screen
iteration_consumed=false
```

## Evidence to read

- `docs/external-review/rounds/20260724_g20r_identification_floor/20_PRO_OPEN_QUESTION.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260724_ANCHOR_POLICY_ACTION_ADVANTAGE_G20R_SCREEN.md`
- `docs/research/designs/ANCHOR_POLICY_ACTION_ADVANTAGE_G20R.md`
- `docs/external-review/rounds/20260724_g20_credit_rule_zero_fixed_point_r2/21_PRO_OPEN_RAW.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260724_CENTERED_COUNTERFACTUAL_RESIDUAL_G20_ZERO_FIXED_POINT.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `ha_ctse_process/anchor_action_advantage_g20r.py`
- `scripts/screen_anchor_action_advantage_g20r.py`
- `tests/ha_ctse_process_anchor_action_advantage_g20r_test.py`
- `ha_ctse_process/delayed_battery_roster_g18.py`
- `ha_ctse_process/continuous_service_roster_proxy_g17.py`
- `docs/project/CURRENT_WORK.md`

## How to read it

Start with the screen note — it carries every number below and states what was
and was not claimed. The design's section 9 holds the result system whose branch
2 fired. Your previous round's raw is the decision this package implements.

## Decision authority

You are the external GPT-5.6 Pro scientific authority. Thresholds are protected
semantics in this project, so redefining an identification floor is your call,
not a local repair. The orchestrator decides how any accepted definition is
built.

## What was decided last round, and what was built

You ruled: retain the exact-zero fast anchor, retire the residual-table
leave-one-out rule, and move member-resolved credit onto the executed action as
a decision-history-conditioned anchor-policy action advantage with the suffix
marginalized. That was frozen and built. You also required the repaired screen
be re-registered, and warned specifically that *"a critic-identification failure
must not be misreported as a failure of centered authority"*. A dedicated
identification branch was therefore placed ahead of every behavioural branch.

## What the screen found

**The repair works mechanically.** Against the retired rule, which was provably
pinned at zero forever:

| | residual output layer, max abs |
|---|---|
| G20 retired rule | `0.0` |
| G20R on g17 | `0.129744` |
| G20R on g18 | `0.422483` |

`maximum_replay_error = 0.0` and `maximum_anchor_difference = 0.0`: the fast
anchor survives bitwise while the residual moves.

**Branch 2 fired.** The registered floor is
`spread ≥ 0.01 × slow_return_std`, where spread is the mean over active tokens
of `Q_j`'s variation across the `K = 8` resampled anchor actions:

| source | spread | floor | |
|---|---|---|---|
| g17 | `0.005004` | `0.094316` | fail, short by ~19× |
| g18 | `0.042009` | `0.013658` | pass |

## The orchestrator's finding about its own threshold

`slow_return_std` is `9.431579` on g17 and `1.365788` on g18. That statistic
measures how much the realized return varies **across states**. It says nothing
about how much one member's action moves it. Normalizing an action-sensitivity
floor by it therefore cannot distinguish:

- the critic genuinely failed to identify action dependence; from
- the source has large state variance relative to any single action's marginal
  effect, so the ratio is small however well the critic identified.

On g17 the second alone suffices to fail the floor. The threshold as registered
collapses exactly the separation the branch was created to provide. This is an
orchestrator defect in an orchestrator-chosen number, reported as such.

## A reading that did not fire, offered so it does not surprise you later

First-match precedence held and these are **not** claimed as results. They are
disclosed because they bear on whether a floor repair alone is sufficient, and
withholding them would make your decision worse.

- Every G17 compatibility threshold would have passed: held-out `0.944830`,
  iid `0.950439`, gain `0.442770`, minimum episode `0.911817`, effort
  correlation `0.973218`, mix correlation `0.991315`, MAEs `0.021979` and
  `0.015775`. The anchor-relative action credit did not damage the accepted fast
  controller.
- G18 moved the wrong way: final utility `0.352932` against an anchor of
  `0.666667` — gain `-0.313735` — with spike utility `0.0` and rotating-member
  effort share `0.014493`. **This is on the source whose critic did clear the
  floor.**

The second is why a threshold fix may not be the whole answer.

## What is asked

1. **How should the identification floor be defined?** It must separate a critic
   that has not learned action dependence from a source whose state variance
   dwarfs any single action's marginal effect. A normalizer built from the
   action's own marginal scale — for example the spread of `Q_j` across
   resampled anchor actions measured against the residual variation of the slow
   return after conditioning on the decision history, rather than against its
   raw standard deviation — is the orchestrator's inference, offered to be
   replaced rather than adopted.

2. **Is a floor repair sufficient?** On g18 the critic cleared the floor and the
   delayed phase still degraded utility below its own frozen anchor. Does that
   observation, once a corrected floor admits it, refute the C1 anchor-policy
   conditional action advantage on this source — or is it consistent with an
   identified-but-poorly-fit critic, in which case what would distinguish the
   two?

3. **Does P2's status change?** Your last round kept P2 the active candidate
   scoped to sources preserving the immediate aggregate. Nothing here was
   registered against it, since branch 2 fired first. Does the disclosed G18
   reading move P2, or does it remain untouched until a re-registered screen
   produces it as a fired branch?

## Not the subject

The exact-zero anchor, active-set centering, the zero-fixed-point theorem and
its narrowing, and the P1/P3/P4 dispositions from your last round. Every closed
G17/G18/G19/G20 result. You are not asked for an implementation plan, a file
list, or authorization for any compute.
