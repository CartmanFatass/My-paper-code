# CRTO probe-cut R01 scope and grounding

Cycle: `2026-08-29.8-portfolio-crto-probe-cut-01`

Milestone: `SCOPE_FROZEN`

Snapshot state: `WORKING`

## Question and scientific object

This is a fresh probe-only material cycle. It does not reopen, rerun, repair,
rename, validate, or scientifically rescue terminal `CRTO-B1-SCIENCE-20260812-04`.
The v4 seed-2101 scripted-support observation at optimizer update 1,000 is
frozen evidence: development normalized MSE was `0.4738729000` against
`<= 0.01`, and development coordinate-sign accuracy was `0.8565487266`
against `>= 0.95`. No learned-policy optimizer update occurred.

The new question is whether one copy of that exact seed-2101 probe trajectory,
continued without a new scientific choice to a fixed total of 10,000 Adam
updates, reaches both unchanged development thresholds at the sole decision
endpoint. The scientific object is the exact
`52 -> 64 -> 32 -> 24` supervised decoder from raw
`[Y, mu, vech(L)]` to `[r, p, a]` on the same predictor-fit plus calibration
rows and the same untouched scripted development split. It is not a policy,
MARL treatment, or new B1 comparison.

## Frozen treatment, clock, and measurements

Optimizer update is the exposure clock. The treatment is only the additional
updates after the frozen update-1,000 state, ending at update 10,000. The
architecture, parameter initialization lineage, full Adam parameter and moment
state, Adam hyperparameters, batch size 256, global gradient clipping at 1.0,
canonical fit-row order, one PCG64 permutation seeded by `600000 + 2101`, cyclic
wrap without reshuffle, and exact post-update-1,000 batch cursor are protected.
Because the fit population has 48,384 rows, that cursor is 14,080 rows into the
fixed permutation after update 1,000.
The development split cannot affect optimization, stopping, selection,
reshuffling, restart, tuning, thresholds, or the returned checkpoint.

At each fixed boundary 1,000, 2,000, ..., 10,000, record the final minibatch
fit MSE for the update ending at that boundary, development normalized MSE
using the registered fit-coordinate variance
denominator, and development coordinate-sign accuracy on targets with absolute
value at least `0.05`. These boundary measurements are descriptive except for
the fixed update-10,000 endpoint. No best checkpoint is selected.

The only decision gate is:

- pass if update 10,000 has development normalized MSE `<= 0.01` and sign
  accuracy `>= 0.95`;
- otherwise fail and stop this exact decoder package without another retry,
  policy training, or downstream CRTO claim.

## Competing explanations and interpretation ceiling

The simple optimization-exposure explanation predicts that the same trajectory
can attain both registered support gates after the additional fixed exposure.
The competing package-inadequacy explanation predicts that the exact raw
packet, bottleneck, initialization, Adam path, and cyclic order still do not
attain both gates at 10,000 updates. A pass makes limited update exposure the
leading explanation for seed 2101's update-1,000 failure. A fail makes this
exact 10,000-update decoder package inadequate for the registered support
premise and stops it.

Neither branch proves structural function-class sufficiency or insufficiency.
A fail remains compatible with a poor optimizer basin, conditioning, cyclic
order, initialization, or a horizon beyond 10,000. A descriptive intermediate
joint pass followed by endpoint failure would be direct evidence against a
structural class-inadequacy reading and would leave non-monotone optimization or
checkpoint instability as the strongest objection, while the endpoint-governed
package would still stop. The phrase “raw-packet/function-class bottleneck” is
therefore bounded to the registered decoder package and cannot be used as an
approximation lower bound.

The development panel is untouched by gradients but already observed at update
1,000, and the cycle deliberately follows that selected seed. The result is a
single-trajectory diagnostic, not independent confirmation. Probe parameters
never enter a policy. No result establishes added information, residual-semantic
uniqueness, off-support hypothesis-class equality, all-seed competence, policy
value, variable-`K` value, warehouse or UAV value, safety, deployment, or
general option value.

## Result-blind validity boundary

A scientifically valid continuation must preserve the exact update-1,000
trajectory state, including the next cyclic batch. Loading a complete serialized
checkpoint is sufficient. A deterministic reconstruction is not automatically
sufficient: before executable authorization, the Innovator challenge and EM
synthesis must decide what direct equality witness would make reconstruction a
copy rather than an impermissible restart or v4 rerun. Reinitialization at
update 1,000, resetting Adam moments or the permutation cursor, reshuffling,
development-driven choice, or an unverified replay changes the object and makes
the observation technical invalid rather than scientifically negative.

The maximum observation count is one strict result command, one seed, one probe
trajectory, ten fixed metric boundaries, no learned-policy activity, and no
downstream experiment. The intended resource envelope is one CPU, no GPU, at
most 2 GiB resident memory, and at most 1,800 seconds wall time. Crossing a
resource bound or losing state continuity yields only a technical gap.

## Authorities and current stop condition

The result-blind authority set is:

- Git baseline `0ddeed0fc50b75c4bf47b4f2bc2bf6721c8ec19d`;
- `docs/research/candidates/commitment_residual_triggered_options/DIRECTION.md`;
- `docs/research/candidates/commitment_residual_triggered_options/CRTO_B1_SCIENCE_CARD.md`;
- `docs/research/candidates/commitment_residual_triggered_options/CRTO_B1_V4_PREACTIVITY_SUPPORT_GATE_INTAKE.md`;
- `docs/project/ALGORITHM_PRINCIPLES.md`; and
- `docs/research/portfolio/PORTFOLIO.md`.

No executable observation is authorized at this milestone. The next action is
the mandatory fresh GPT-5.6 Pro Innovator challenge, followed by EM synthesis.
Only if that synthesis freezes an exact continuation command and observation
contract and still finds execution scientifically necessary may EM transfer the
direction writer to one fresh Sol/high CM.
