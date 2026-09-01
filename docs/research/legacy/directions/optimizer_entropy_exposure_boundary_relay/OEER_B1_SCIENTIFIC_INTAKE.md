# OEER-B1 scientific intake

Owner: `direction:optimizer-entropy-exposure-boundary-relay` Explorer Manager  
Candidate: `CAND-OPTIMIZER-ENTROPY-EXPOSURE-BOUNDARY-RELAY`  
Treatment: `OEER-B1-BOUNDARY-RELAY-v1`

## Intake basis

The CM return reports a valid production exit with the complete registered
budget: 65,536 future action/update rows from eight seeds, four sign-balanced
roots, 32 continuations per root, and 64 updates per continuation. This intake
interprets those returned scientific facts; it does not re-accept runtime or
implementation correctness.

## Scientific conclusion

The result supports one narrow direct optimizer-history claim and does not
support the proposed entropy-to-exposure relay.

| Contrast | Observation | Interpretation |
|---|---:|---|
| `D_M` | `-3.24e-08` | Practical absence at this host and budget. The `0.01` entropy pulse did not leave a material persistent effect through its first parameter displacement under common future exposure. |
| `D_H` | `-0.0250633`, 95% CI `[-0.0250825,-0.0250440]`, Holm `p=.03125` | Claim-qualified directional material effect. With first post-boundary parameters matched, carrying the prescribed nonempty Adam state reduced normalized correct-action trajectory area by about 0.025 relative to the fresh-state continuation, after subtracting state created by the RESET boundary step. This supports a carried-Adam legacy beyond first-position mismatch in this toy. |
| `A_M` | `-5.17e-11` | Numerically and practically negligible, but `X_M=0`; the action-to-exposure edge was not realized. Therefore this is not evidence for or against closed-loop amplification of the mutation channel. |
| `A_H` | `0.000585`, with seed-sign heterogeneity | Numerically within the practical-absence band, but `X_H=0`; the history-amplification question was unexposed. The heterogeneous signs also prohibit a directional amplification claim. |

The negligible generic envelopes do not rescue an entropy claim: the observed
entropy-mutation effects themselves are many orders below the `0.02`
materiality threshold. Thus there is no entropy-direction-specific mutation or
amplification result to distinguish from generic perturbations.

The composite question is therefore separated as follows:

- **supported:** inherited Adam state can change later learning despite matched
  first parameters, and in the frozen host the change is harmful on `U`;
- **practically absent here:** a material persistent entropy-displacement
  channel;
- **not exposed:** action-controlled amplification of either mutation or
  optimizer-history channels.

`D_H` is not an entropy interaction: it averages the history residual over
`PULSE` and `ZERO`. It must not be reported as evidence that entropy was relayed.

## Strongest remaining explanation

The parsimonious explanation is a host-specific mismatch between the prescribed
nonempty Adam moments/step count and the subsequent four-root BCE gradients. It
can depress future learning even when the first post-boundary parameters are
matched. `DELTA_MATCH` rules out first-parameter mismatch, but this experiment
does not show that the carried state arose from a variable-`k` learning process,
that such a legacy is general across checkpoints or optimizers, or that skill
duration decisions amplify it. The absent exposure separation leaves the latter
question unanswered.

## Exact variable-`k` design consequence

OEER supplies a control requirement, not an algorithm component:

1. Do not add an entropy schedule, entropy pulse, or optimizer reset mechanism
   to a variable-`k` algorithm on this evidence.
2. When a later fixed-`k` to adaptive-`k` curriculum or warm start is evaluated,
   optimizer history must not differ silently between algorithm arms. Start both
   arms from a common optimizer state or a common fresh optimizer.
3. If carrying pretrained state is itself part of the intended training method,
   cross `CARRY` versus `FRESH` with fixed versus adaptive `k`, or isolate a new
   duration/termination head's optimizer, so an adaptive-`k` benefit cannot be
   attributed to optimizer history.
4. The negative `D_H` makes carried state a plausible training-boundary hazard
   here; it does not establish that reset is universally preferable. In
   particular, do not reset shared optimizers at runtime `KEEP`, `SET`, or skill
   termination events merely because a skill boundary occurred.

This consequence applies only when a scientifically justified variable-`k`
candidate reaches such a training comparison. It supplies no variable-`N`
design decision.

## Successor judgment

No OEER-B2, coefficient sweep, larger seed panel, or repaired SELF-exposure run
is warranted from this result. The entropy branch is practically absent, and
the closed-loop branch produced no exposure contrast. The direct Adam-history
finding is sufficiently resolved for its present purpose: carry its optimizer-
matching control into the next independently valuable variable-`k` toy rather
than opening another optimizer-only direction.

A new discriminator becomes worthwhile only if a concrete variable-`k`
algorithm uses warm-started training or learned duration/termination and its
scientific question requires deciding between carried and fresh optimizer
history. That should be a factor inside the duration-shaped algorithm test, not
an automatic continuation of OEER.

## Claim ceiling

Within the frozen four-root bilinear-logit full-feedback host, prescribed Adam
state and hyperparameters, 64-step horizon, fixed panel, and eight-seed tape set,
carrying the nonempty Adam state causally lowered later normalized correct-action
area by about 0.025 despite matched first parameters. The entropy-displacement
effect was practically absent. No conclusion is available about closed-loop
amplification because the exposure edge was not realized.

The result does not establish an entropy mechanism, optimizer-state necessity,
general superiority of reset, variable skill periods, learned termination,
MARL coordination, variable agent count, robustness or task-performance gain,
or transport to a UAV simulator or real UAV. It does not retroactively establish
the mechanism in VSP02, G52, or G53.
