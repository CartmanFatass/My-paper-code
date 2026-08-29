# Independent scientific challenge: CRTO seed-2101 probe continuation

Please act as an independent scientific innovator and skeptical methodologist.
We need your result-blind challenge before deciding whether to execute a very
narrow supervised-learning discriminator. This is not a request to review code,
approve an experiment, manage a workflow, or infer a portfolio action. Please
look for a sharper counterexample, a smaller separating observation, a hidden
change of scientific object, or an interpretation that our proposed endpoint
cannot support.

The background is a terminal preactivity observation from a larger candidate
called commitment-residual triggered options. The exact earlier candidate,
CRTO-B1 v4, included a scripted-support decodability gate before any policy
training. For algorithm seed 2101, a fixed neural probe received a 52-coordinate
raw packet `[Y, mu, vech(L)]` and tried to reconstruct the first 24 explicit
residual coordinates `[r, p, a]`. The architecture was
`52 -> 64 -> 32 -> 24` with tanh hidden activations. At its preregistered final
checkpoint after exactly 1,000 Adam updates, development normalized MSE was
0.4738729000 against a required maximum of 0.01, and development
coordinate-sign accuracy was 0.8565487266 against a required minimum of 0.95.
That was a valid failure of the earlier gate. It happened before any learned
policy optimizer update, so there is no CRTO-versus-baseline policy result and
no residual-mechanism, variable-K, warehouse, or UAV result to interpret.

We are not reopening, rerunning, repairing, renaming, or rescuing v4. The new
scientific object is probe-only and asks one question: if a copy of that exact
seed-2101 optimizer trajectory is continued to a fixed total of 10,000 updates,
does the update-10,000 model meet both unchanged development thresholds? The
same fit rows, already defined development split, raw and target coordinates,
architecture, initialization lineage, full Adam state and hyperparameters,
batch size 256, gradient clipping, and example order must be preserved. Fit
examples remain in canonical order and use one PCG64 permutation seeded by
`600000 + 2101`, taken cyclically without reshuffle. There may be no
development-driven stopping, checkpoint selection, restart, tuning, changed
threshold, or new seed. Probe parameters can never enter a policy.

For transparency rather than selection, the run would record the final
minibatch fit MSE at each boundary, development normalized MSE, and development
coordinate-sign accuracy at every
fixed 1,000-update boundary from 1,000 through 10,000. Only update 10,000 is
decision-bearing. A pass requires normalized MSE at most 0.01 and sign accuracy
at least 0.95. A pass would make limited optimizer exposure the leading
explanation for this exact seed's update-1,000 failure. An endpoint failure
would stop the exact architecture-initialization-Adam-order package without
another retry or policy activity; we are considering describing that bounded
package as a raw-packet/function-class inadequacy while expressly withholding
any structural approximation lower bound.

Two concerns already survive our local result-blind audit. First, Adam and
minibatch development metrics need not be monotone. An intermediate boundary
might satisfy both gates and update 10,000 might then fail. Because the endpoint
and no-selection rule remain fixed, the package would still stop, but an earlier
joint pass would contradict a structural function-class-inadequacy reading and
would make optimization or checkpoint instability the strongest alternative.
Second, the exposure must truly continue. With 48,384 fit examples and batches
of 256, one permutation traversal is 189 updates, so the next batch after update
1,000 must preserve the exact remainder position rather than restart at the
permutation origin. The complete parameter values, Adam moments and step count,
and this cyclic cursor are part of the scientific state.

There is also a practical scientific-validity question about the word “copy.”
The repository's historical implementation returned the fitted probe and
reported its metrics but the checked-in code did not itself make the probe and
optimizer checkpoint a durable result artifact on the failure branch. We will
not allow a new random initialization, an Adam reset, a cursor reset, or an
unverified replay. Is a bit-identical deterministic reconstruction from the
frozen initialization, data-generation path, predictor, calibration table,
example rows, permutation, and first 1,000 updates scientifically equivalent to
copying the lost live state? If so, what is the minimum direct equality witness
at update 1,000 that makes the continuation interpretable? If not, should the
cycle end as a technical unavailability rather than execute a scientifically
different restart? Please keep this as a scientific-object question, not a
source-code review.

The relevant public scientific references are in
https://github.com/CartmanFatass/My-paper-code at commit
`0ddeed0fc50b75c4bf47b4f2bc2bf6721c8ec19d`. The narrow authorities are
`docs/research/candidates/commitment_residual_triggered_options/DIRECTION.md`,
`CRTO_B1_SCIENCE_CARD.md`,
`CRTO_B1_V4_PREACTIVITY_SUPPORT_GATE_INTAKE.md`,
`docs/project/ALGORITHM_PRINCIPLES.md`, and the CRTO row in
`docs/research/portfolio/PORTFOLIO.md`. The probe law is visible in
`experiments/candidates/commitment_residual_triggered_options/training.py` and
the probe architecture in `models.py`; those files are scientific references,
not a general code-review assignment.

Please answer the scientific questions directly. Is the fixed continuation the
smallest decision-relevant observation, or is there a strictly smaller
result-blind discriminator that preserves the intended choice? What exact
state-continuity witness is necessary? What should we conclude after (a) an
endpoint pass, (b) an endpoint failure with no earlier joint pass, and (c) an
endpoint failure after an earlier descriptive joint pass? Name the strongest
surviving alternative explanation in every branch. Finally, give the narrowest
claim ceiling and one decisive reason to execute or not execute this probe.

Even a positive answer cannot certify v4. Any later confirmatory B1 would be a
separately authorized fresh all-seed object with rematched work and optimization
exposure and fresh untouched confirmation panels. No answer may establish added
information, residual-semantic uniqueness, equality of hypothesis classes off
support, policy value, variable-K value, general option value, UAV value,
safety, or deployment.
