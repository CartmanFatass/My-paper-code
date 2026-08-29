# EGRCR revision 2026-08-28.7 discriminator selection

Observed at: 2026-08-28T20:32:12Z

## Question

Does the retained B1 host contain a legal, generic-cue-preserving
wrong-waiter comparison that changes waiter identity and its bounded
consequence while preserving every non-identity marginal? If not, would a new
execution in that host answer a Portfolio question not already answered by the
intact-versus-GAE allocation and utility result?

## Inputs

- Exact shared baseline
  `b4762febd12b62748d35e2b1a1dffdfb8d776180`.
- `EGRCR_B1_SCIENCE_CARD.md`.
- `EGRCR_B1_CALIBRATION_RESULT.json`.
- `EGRCR_B1_RESULT.json`.
- `EGRCR_B1_TECHNICAL_RESULT_INTAKE.md`.
- `experiments/candidates/expressibility_gated_renewal_credit_relay/config.py`.
- `experiments/candidates/expressibility_gated_renewal_credit_relay/experiment.py`.

## Tool and command

The retained JSON was parsed read-only with PowerShell `ConvertFrom-Json` to
compare root-level GAE/INTACT utility and fixed-token allocation. The frozen
four-world implementation was then evaluated read-only with:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -c "from experiments.candidates.expressibility_gated_renewal_credit_relay.experiment import Opportunity,_quartet; print([(k,l,o,_quartet(Opportunity(0,'x',k,l,o,False))['kappa'],_quartet(Opportunity(0,'x',k,l,o,False))['waiter'],_quartet(Opportunity(0,'x',k,l,o,False))['generic_waiter']) for k in ('JOINT','SOLO') for l in (1,2) for o in (0,1)])"
```

This is deterministic inspection of the already committed scientific object,
not a new result-bearing experiment or a repeat of B1.

## Observation

The B1 artifact reports exact GAE/INTACT equality in native normalized bounded
utility and fixed-token joint allocation at all twelve roots. Aggregate
`D_IG_N=0` and `Psi_G=0`, each with zero standard deviation and zero-width
confidence interval. The proximal request-probability contrast did not cross a
scarce allocation boundary.

The four-world inspection returned:

```text
JOINT lag 1: kappa=+0.16666666666666663 for older_id 0 and 1
JOINT lag 2: kappa=+0.20000000000000007 for older_id 0 and 1
SOLO  lag 1: kappa=-0.16666666666666666 for older_id 0 and 1
SOLO  lag 2: kappa=-0.2                 for older_id 0 and 1
```

`Opportunity.cue` is the type sign with prospectively scheduled flips, and
`_world` makes the bounded consequence depend on type and lag, not
`older_id`. The registered `_cut_mapping` groups on the same physical
`older_id`, lag, action, and propensity, then maps every `JOINT` packet to a
`SOLO` packet and vice versa. Thus it changes type/sign and generic
cue-to-outcome supervision while leaving physical waiter identity fixed.

Within a fixed type, lag, and generic cue/sign context, changing the waiter
record cannot change `kappa`: all eligible packets have the same interaction
value. A same-type event-key derangement is therefore a dummy control, not an
identity-effect test. An opposite-type derangement changes the scientific
content as well as the record association.

## Limitations

This static observation does not prove that waiter identity can never matter
in another host. B1 has only two symmetric physical agents and no
consequence-distinct waiter identities within a generic pre-action context.
The deterministic inspection also does not evaluate multi-update learning,
sample efficiency, a learned estimator, or another policy head; those objects
are outside the cycle claim and cannot repair the registered intact-versus-GAE
task-value null.

The historical confirmation observer lacked a separate child-exit and peak-RSS
receipt, but the retained result is complete for the comparisons used here and
records all roots, panels, caps, work controls, and zero anomalies. No source
or result repair is indicated.

## Judgment impact

No new executable observation in B1 can create the missing identity contrast,
and repeating or adding seeds cannot change the exact structural equality.
Repairing only the cut would refine attribution of the positive
intact-versus-cut effect while leaving the already observed zero incremental
utility/allocation over GAE untouched. It would not change the Portfolio
investment decision.

The smallest decision-changing discriminator is therefore a prerequisite,
not an executable B1 repair: identify a genuinely different, independently
motivated host with at least two consequence-distinct eligible waiters inside
the same generic pre-action/cue stratum, then demonstrate prospectively that a
same-information oracle association policy has actual scarce-allocation and
bounded-utility headroom over ordinary GAE. Only after those facts exist would
a cue/sign-preserving wrong-waiter key derangement be answer-changing.

Because neither prerequisite exists in the traceable evidence, this cycle
uses zero of its one allowed CM observation rounds. No result command, source
change, test change, or top-level CM task is authorized or created.

## Result paths

- `docs/research/candidates/expressibility_gated_renewal_credit_relay/EGRCR_B1_RESULT.json`
- `docs/research/candidates/expressibility_gated_renewal_credit_relay/evidence/2026-08-28-7-pilot-evidence-packet.md`
- `docs/research/candidates/expressibility_gated_renewal_credit_relay/workflow/research/state.json`
