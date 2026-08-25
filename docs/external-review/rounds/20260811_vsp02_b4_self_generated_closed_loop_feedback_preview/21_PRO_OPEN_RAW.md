SOUND_AS_WRITTEN
The proposed comparison defines a coherent single-edge, dynamic total-effect intervention.
Let E
t
	â€‹
 denote the immutable address-indexed exogenous tape, C the unchanged collector, U
O
	â€‹
 the original-objective update, and U
C
	â€‹
 the oracle-sign update. The three recursions are:
B
t
G
	â€‹
S
t+1
	â€‹
B
t
F
	â€‹
	â€‹
=C(G
t
	â€‹
,E
t
	â€‹
),
=U
C
	â€‹
(S
t
	â€‹
,B
t
G
	â€‹
),
=C(F
t
	â€‹
,E
t
	â€‹
),
	â€‹
G
t+1
	â€‹
F
t+1
	â€‹
	â€‹
=U
O
	â€‹
(G
t
	â€‹
,B
t
G
	â€‹
),
=U
C
	â€‹
(F
t
	â€‹
,B
t
F
	â€‹
).
	â€‹
The treatment selector changes only the source argument of the batch-generating structural equation for the oracle-sign learner:
B
t
	â€‹
={
C(G
t
	â€‹
,E
t
	â€‹
),
C(F
t
	â€‹
,E
t
	â€‹
),
	â€‹
feedbackÂ cut,
selfÂ feedback.
	â€‹
The original-objective generator is a prospectively fixed nuisance process present independently of the selector. Under the stated noninterference obligations, the self-feedback arm cannot alter that generator, its tapes, batches, updates, or successor states. Therefore changing the selected parent of B
t
	â€‹
 is a well-defined edge replacement rather than an uncontrolled bundle of simultaneous interventions.
The initialization and first-update construction correctly establish the causal origin of divergence:
G
0
	â€‹
=S
0
	â€‹
=F
0
	â€‹
 at the complete byte state.
B
0
G
	â€‹
=B
0
F
	â€‹
 under the common tape.
The shadow and self-feedback learners apply the identical oracle-sign update to identical states and identical frozen batches.
Consequently, their first oracle-sign successor states are identical under the already-stated exact-route and noninterference requirements.
The first permitted causal difference between them arises when the next batch is sourced from G
1
	â€‹
 rather than F
1
	â€‹
.
The written invariants therefore already entail the congruence condition that equal complete oracle-sign states plus equal frozen batches produce equal complete successor states. Recording that equality during technical acceptance would witness an existing invariant; it is not a new scientific repair or a second axis.
Subsequent differences in occupancy, actions, rewards, returns, targets, coefficient distributions, gradients, clipping, Adam moments, critic state, or recurrent representation are correctly classified as descendants of the batch-source selector. They must be allowed to vary for a total-effect estimand. Holding any of them fixed would instead block part of the feedback pathway and change the scientific question into a controlled-direct-effect or mediator-specific intervention.
The feedback-exposure requirement also does not introduce another axis. It is a prospectively declared whole-run activity gate, not post hoc subgroup selection and not conditioning on the direction or magnitude of a mediator. If no later action or transition row differs under the indexed tape, the finite experiment has not realized an observable data-path perturbation, so routing the result to inconclusive is appropriate.
The positive branch can support only the stated comparator-specific conclusion: under this exact toy, update law, mixture, roots, and finite budget, connecting the oracle-sign learner to its own future batches was locally sufficient whereas feeding it the registered original-generator batches was not. It cannot identify which descendant carried that effect and cannot validate the coefficient as a policy-gradient advantage.
Strongest prospective falsifier: B4_FEEDBACK_LOCAL_INSUFFICIENT exactly as registeredâ€”feedback exposure realized in every unit, every validity and activity gate passing, and all three arms exact-correct in 0/5 units. That outcome cleanly falsifies the local sufficiency of this exact self-generated closed-loop feedback intervention under the fixed B4 budget. Any partial self-feedback recovery, nuisance recovery, shadow recovery, or failed exposure remains inconclusive rather than a weaker or reinterpreted conclusion.
