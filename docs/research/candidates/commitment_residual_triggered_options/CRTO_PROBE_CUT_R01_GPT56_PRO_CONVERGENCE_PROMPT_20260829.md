# Independent convergence challenge: CRTO lost-state continuation

Please provide a fresh, independent scientific convergence review of a narrow
probe-only decision. Do not infer what outcome we prefer, do not perform code
review, and do not authorize activity. Your job is to find the strongest
evidence-based objection to the current synthesis, identify any missing direct
fact that could change it, and state the smallest scientifically defensible
conclusion.

An earlier CRTO-B1 v4 preactivity gate trained a supervised
`52 -> 64 -> 32 -> 24` probe on raw `[Y, mu, vech(L)]` packets to reconstruct
24 explicit `[r, p, a]` coordinates. For seed 2101, the fixed update-1,000
checkpoint failed both registered development gates: normalized MSE was
0.4738729000 against at most 0.01 and sign accuracy was 0.8565487266 against at
least 0.95. The failure was valid, no policy optimizer update occurred, and v4
is terminal. A fresh cycle was authorized to ask only whether a copy of that
exact trajectory, continued without any changed row, state, optimizer choice,
order, restart, selection, or tuning, would meet both unchanged gates at the
sole update-10,000 endpoint.

The intended scientific treatment is 9,000 additional updates from the same
complete dynamic state. That state includes all probe parameters and buffers,
every Adam first- and second-moment tensor and step counter, update count 1,000,
the fixed PCG64 permutation, and its cursor 14,080 rows into the 48,384-row fit
population. At fixed 1,000-update boundaries, final-minibatch MSE and the two
development metrics would be recorded descriptively; update 10,000 alone would
govern disposition. An endpoint pass would show that extra exposure was
sufficient for this exact trajectory. An endpoint failure could stop only the
exact architecture-initialization-objective-Adam-order-final-checkpoint package;
it could not prove raw-packet information loss or structural function-class
insufficiency. A prior descriptive pass followed by endpoint failure would
instead directly expose checkpoint instability.

No executable result was observed. Direct inspection at Git commit
`0ddeed0fc50b75c4bf47b4f2bc2bf6721c8ec19d` found that the historical function
constructed the probe and Adam optimizer in memory, performed 1,000 updates,
and returned the probe plus a scalar report. Its caller bound the probe to a
local throwaway name, wrote only scalar diagnostics, and raised immediately on
failure. The first subsequent checkpoint write was only on the passing path and
was for another model. The durable result JSON contains no seed state reference.
Its declared output root is absent, and a read-only search across the saved
project and native HMASD worktrees found no CRTO probe/Adam/cursor checkpoint or
full-state digest.

Two independent result-blind local audits agreed that the fixed continuation is
the smallest exposure discriminator only if exact state continuity exists.
They also agreed that update-10,000 failure cannot identify a structural
function-class bottleneck because unweighted training MSE differs from the
variance-normalized/sign decision gates, and optimizer basin, conditioning,
cyclic phase, and loss alignment survive. A separate fresh GPT-5.6 Pro
Innovator response concluded that physical process continuity is unnecessary
if complete state equality can be proved, but the published scalar metrics are
many-to-one and cannot establish Adam/cursor identity. It judged an original
state bundle or digest—or a fully recorded original numerical environment plus
a defensible bit-determinism proof—necessary before a reconstruction can be
called the same continuation.

The current synthesis is that the requested scientific object is technically
unavailable. A new uninterrupted from-genesis replay could be a separately
frozen canonical-replay probe, but without a direct comparison target it cannot
be described as a copy of the lost observed state. Therefore no exact result
command can be frozen, no CM should be created, and no probe should run in this
cycle. The representation-versus-optimization question remains unanswered;
this is an evidence-availability boundary, not negative science.

The public baseline scientific references are in
https://github.com/CartmanFatass/My-paper-code at commit
`0ddeed0fc50b75c4bf47b4f2bc2bf6721c8ec19d`. The relevant files are
`docs/research/candidates/commitment_residual_triggered_options/DIRECTION.md`,
`CRTO_B1_SCIENCE_CARD.md`,
`CRTO_B1_V4_PREACTIVITY_SUPPORT_GATE_INTAKE.md`,
`docs/project/ALGORITHM_PRINCIPLES.md`, the current CRTO portfolio row,
`experiments/candidates/commitment_residual_triggered_options/training.py`, and
`execution.py`. The current owner-local cycle scope is preserved at Git commit
`fff35a15650812c33c00798fd892c72c18fd7a07`, and the complete synthesis is
stated directly in this prompt; neither is assumed to be connector-readable.
Source code is scientific provenance here, not a request for a general
implementation review.

Please challenge the synthesis directly. Does the frozen deterministic source,
seed lineage, and matching historical scalar metrics suffice scientifically to
identify the lost update-1,000 state, or is a retained full-state/digest or
stronger numerical-provenance witness required? Is declining to create CM and
declining to run the replay the correct bounded disposition? Name one concrete
fact, if any, that could still make the exact continuation executable without
changing the cycle. Finally, state the narrowest conclusion and its strongest
remaining objection. Do not convert a technical gap into representation,
optimization, policy, CRTO-family, lifecycle, warehouse, UAV, safety, or
deployment evidence.
