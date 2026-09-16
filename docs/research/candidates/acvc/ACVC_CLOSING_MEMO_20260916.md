# ACVC closing memo (lane CLOSE, 2026-09-16 04:30Z)

Written under the owner's workflow-lanes instruction (2026-09-15 21:03 PDT,
`docs/research/portfolio/decisions/2026-09-15-workflow-lanes.md`) after `em:acvc:convergence`
concluded the matched-package question at one block (result review
`2026-09-16-acvc-matched-package-result-review-01`, PRO_FINAL, option A). This memo records what
was asked, what was found, what is excluded and what would reopen the direction. It changes no
label, pools nothing, and decides nothing at Portfolio tier; the bundled Portfolio lifecycle question
follows separately. Lifecycle state at writing: ACTIVE / MEDIUM / recasts 2, lowest sequencing,
slot occupied, no producer, G3 consumed.

## What was asked

Whether the fixed execution package F (the wrapper: binding, private history, retracing, holding)
around a cluster proposer improves expected endpoint native return by more than the local .01 J
minimum effect of interest over the bare proposer and over its own-predicate dwell, on the fixed
five-UAV / fifty-user fresh-DENSE training and evaluation law; later, whether the C-trained private
recurrent proposer package F(C) has any advantage over a conventional MAPPO-style proposer M or its
package F(M).

## What was found (each retained at its own label; no pooling)

| Object | Reading | Label |
| --- | --- | --- |
| FRESH_DENSE_PACKAGE_C01 (five fit-panel units, 2026-09-11) | F − C +.096 J [.075, .117]; F − dwell +.065 J [.038, .092] | JOINT_ABOVE_MEI under the provisional single-task C-BENCH rule; coverage qualified by the iid-normal working model |
| FIXED_F_TRAINING_USE_B01 / B02 (2026-09-12) | training through F: .2975 → .2714 J; recurrence .2657 → .2084 J | DOWN twice; the fixed training change adds nothing |
| CLUSTER_MAPPO_COMPARISON B01 / B02 (2026-09-14/15) | F(C) − M +.023 J then −.039 J; C − M negative in both blocks (−.056, −.087); F − C positive in both (+.046, +.047) | F_ABOVE_MEI then M_ABOVE_MEI; family concluded at two blocks |
| M_DEPLOYMENT_TRANSFER B01 / B02 (2026-09-15) | F(M) − M +.018 J then +.003 J | TRANSFERS then WITHIN_MEI; family concluded at two instances |
| MATCHED_PACKAGE_COMPARISON B01 (2026-09-16) | F(C) − F(M) −.015 J (24/40); F(M) − M +.005 WITHIN; F(C) − C +.046 UP | F_M_ABOVE_MEI on one block; question concluded |

Reading across the objects, without pooling: the wrapper F reliably lifts the C-trained proposer
(three positive F − C blocks of about .045 J and the C01 result), the C-trained proposer itself
trails the conventional proposer M by .05 to .09 J on every block that compared them, and F lifts M
by only .003 to .018 J. The complete packages F(C) and F(M) end within .04 J of each other with the
sign changing across blocks. The one-block dispersion of a package contrast across 64 worlds is
about .09 J, so single-block labels at ±.01 J describe that block only.

## What is excluded

Stable superiority of any package; a training-population mean; a discardable C or M; tuned
headroom (no tuned same-information M baseline was run); equivalence; mechanism attribution (the
wrapped panels differ in history and substitution counts, and dwell(M) still carries binding and
private history, so it is not wrapper-free); C promotion; any default or safety change; any
transfer or recurrence claim beyond the per-instance readings above.

## What would reopen the direction

- A second matched block (option B of the result review: two fits, 2,195,456 scored ticks,
  about 2,250 s native wall) if the choice between complete packages becomes consequential for
  deployment, or if compatible new evidence changes the marginal value of that ranking.
- A concrete reason to make holding-versus-unwrapped development the priority on the M side
  (option C: one fresh M fit with unwrapped-M and own-dwell panels, 1,081,344 ticks).
- A tuned same-information M baseline on the UAV host, which would convert the C − M deficit from
  an untuned package gap into a headroom record. This is the one measurement the direction never
  made and the only one that could change the reading of every block above.

## Retained assets

Runners and protocols under `experiments/candidates/acvc/` (comparison, transfer and matched
thin entries), the six-panel evaluation design, the archived originals of every block
(`PRESERVATION.json` records), and the reducer with its decomposition identity. They are usable by
any direction that needs a package-versus-proposer comparison on this host.

## Recommendation carried to Portfolio (DM, not a decision)

PARK with the assets retained and the three reopening conditions above, releasing the slot. The
DM does not assert exhaustion: option B is defensible, but its expected information (one more sign
on a contrast with .09 J world dispersion) is low relative to the confirmatory work available on
`flexible_skill_duration`. Under the workflow lanes this is the one bundled Portfolio question ACVC
sends.
