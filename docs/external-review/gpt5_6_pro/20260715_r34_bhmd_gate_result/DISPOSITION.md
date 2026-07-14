# Controller disposition: R34 verdict accepted, first R35 route rejected

Date: 2026-07-15

Source model: GPT-5.6 Pro through the authorized in-app browser handoff. The raw
response is `RESPONSE_RAW.md`.

## Decision

- R34 validity and retirement: **ACCEPT**. The response found no concrete M0
  defect and accepted valid `FAIL_M1_RETIRE_R34_BHMD`. R34 remains permanently
  retired without tuning, expansion, or objective conversion.
- Frozen-source interpretation: **ACCEPT**. The large real/sham gap is evidence
  that wrong label attribution damages the actor, while the source-relative
  failures show that correct BHMD did not create stronger causal skills.
- Continuous/overlapping-manifold explanation: **DEFER AS HYPOTHESIS**. Source
  SNR above real with modest centroid fidelity proves that the registered
  prototype geometry is not equivalent to causal skill quality; it does not by
  itself identify the true manifold topology.
- Proposed R35-OCSF: **REJECT**. No implementation, experiment contract, or
  compute is authorized for it.

## Decisive rejection reason

R35-OCSF trains `q_psi(z | phi(tau))` on the current numerical skill label and
adds `log q_psi(z | phi(tau)) - log q_psi(z)` to low-level PPO/GAE. This is a
process-level old-label classifier intrinsic reward. Sampling `z` online does
not change the label or estimand. It revives the R31/classifier/`q_d`/DIAYN-like
family explicitly prohibited by the tracked question and by the accumulated
R29--R34 failure boundary.

The proposed gate also cannot rescue the route:

- actions in the encoder expose the R29 action-signature shortcut, without an
  action-only null;
- natural `q(z|tau)=z` accuracy reuses the trained reward classifier as its own
  downstream success measure;
- `32 x 80` episodes, 40 PPO updates, and same-rollout arms do not specify a
  coherent on-policy collection contract after actors diverge;
- segment reward timing, recurrent replay, update order, detach, and GAE
  bootstrap semantics are missing;
- the unchanged-source anchor and a precise mechanism-matched comparator are
  absent.
- it jumps directly to reward-on PPO rather than first passing the registered
  reward-off observational and causal-intervention levels.

## Next boundary

The only authorized action is the tracked correction request
`GPT5_6_PRO_CORRECTION_1.md`. It requires one structurally compliant route, or
an explicit abandonment of the current discrete-skill object. Until that
response is archived and dispositioned, there is no R35 implementation or
overnight experiment.
