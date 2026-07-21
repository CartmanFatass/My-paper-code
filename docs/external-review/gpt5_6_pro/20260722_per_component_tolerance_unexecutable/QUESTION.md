# The Per-Component Replay Tolerance Is Not Executable In float32

Sent to GPT-5.6 Pro on 2026-07-22. A formal training run aborted on this. No
result has been observed and no checkpoint was written.

---

```
Use the GitHub connector on private repository CartmanFatass/My-paper-code,
branch `aggressive`. The relevant code is validate_replay and replay_errors in
ha_ctse_process/event_held_commitment_link.py and the constants in
ha_ctse_process/noncalendar_commitment_testbed.py.

WHAT HAPPENED. Formal training aborted partway through replicate 0 with:

  semantic replay tolerance mismatch ['mark_component']
  mark_component        1.9073486328125e-06   <-- exceeds 1e-6
  categorical_component 2.384185791015625e-07
  event_joint           1.430511474609375e-06

Note which check failed. The compositional joint rule you specified worked
exactly as intended: event_joint error 1.43e-06 sat inside its own bound of
1.044e-05 with excess -2.84e-07, and the assembly check passed at
assembly_excess -1.42e-07. The joint level is fine. What failed is the flat
per-component bound of 1e-6 applied to a single transformed-mark component.

THE FAILURE IS PRE-EXISTING, NOT INTRODUCED BY THE PER-FACTOR REWORK. We
checked the code as it stood before that change (commit bcdff53):

  approximate_names = tuple(name for name in errors if name not in exact_names)
  if any(errors[name] > tolerance for name in approximate_names):
      raise RuntimeError(...)

with tolerance = REPLAY_TOLERANCE = 1e-6, and mark_component is in
approximate_names. The original contract would have aborted at the same place
with the same message. This benchmark has never been runnable to completion; the
first full run is what surfaced it.

THE ARITHMETIC. 1.9073486328125e-06 is exactly 2^-19, which is one float32 ULP
for a value whose magnitude lies in [16, 32). So a single transformed-mark
component log-probability reached magnitude at least 16 nats, and the replay
recomputation differs from the stored value by one ULP at that magnitude.

The mechanism is saturation. The mark is z = tanh(u) with u ~ Normal(mu,
sigma^2), sigma = 0.1 + 0.9*sigmoid(s), and the transformed-density Jacobian is
computed as 2*(log2 - u - softplus(-2u)). For u around 8 that term alone is
about -14.6, and the component log-probability passes 16 in magnitude. Training
drives mu, so components grow as the policy sharpens. This is the same argument
that motivated your compositional joint bound, one level further down: a flat
absolute tolerance is being applied to a quantity whose magnitude is not
bounded by the contract.

We had this reasoning and applied it only to the joint. That is our error.

QUESTIONS.

1. Is a flat absolute per-component tolerance executable at all here? The
   quantity is a float32 log-density with no registered magnitude bound, so for
   any fixed atol there exists a magnitude at which one ULP exceeds it. If that
   is right, the current contract is not merely tight but unsatisfiable in the
   limit, and tightening or loosening the number does not fix the form.

2. If the bound should become relative, what is the principled form? The
   candidate is atol + rtol * max(|stored|, |replay|) with rtol a small multiple
   of the float32 unit roundoff 2^-24, derived from the arithmetic rather than
   fitted to the observed 1.907e-06. What multiple, and how should it be
   justified? Should atol remain 1e-6 so that small-magnitude components keep
   their current absolute protection?

3. Should the likelihood accumulate in float64 instead? This is the option we
   would rather you rule on than adopt on our own. One ULP would drop from about
   1e-6 to about 1e-15, which would likely retire the compositional joint bound
   and its gamma_n machinery, this per-component problem, the batch-width
   coupling that forces fork reconstruction to match the collected shape, and
   much of the CPU-versus-CUDA sensitivity. The model has 14,980 parameters and
   the tensors are tiny, so the cost is close to zero.

   Does accumulating the event and primitive likelihoods in float64 change any
   scientific meaning? Our reading is that it changes only the precision of a
   quantity the contract already treats as exact up to reconstruction noise, and
   that the PPO importance ratio, the factorization, the masks and the sampled
   actions are all unaffected. We would rather be told that is wrong now.

4. Whichever form you choose, does it weaken the guarantee that a defective
   component still fails decisively? The per-component class is what currently
   catches an omitted mark component, a wrong mask, an incorrect Jacobian, a
   stale action and a wrong factor support. A relative bound at large magnitudes
   is a larger absolute allowance, and we do not want to discover later that a
   real defect now fits inside it.

CONSTRAINT. No result has been observed and no checkpoint exists. This is a
pre-registration correction to a numerical specification that cannot be executed
as written, not an adjustment made after seeing an outcome.
```
