# R15 — The Steering Objective: Derivation Sketch

Author: CC (Claude, cross-validation), 2026-07-03.
Status: derivation SKETCH for the Round 15 paper-level idea. Not a full
theorem; every informal step is flagged in §7. The archived Round 15 review is
in `docs/archive/legacy-memory/backup_20260706/cross_validation.md`; this file is
the durable research record for that prototype stage.

Thesis: replace skill IDENTIFIABILITY (HMASD's discriminators) with skill
STEERING — skills are responses to a recognized interaction situation;
intrinsic pressure = (individual) be informative beyond the coordinator's own
prediction, (team) steer the situation beyond its natural drift.

## 1. Notation

```text
s_t            global state;  o_i_t  local observation;  a_i_t  action
kappa_tau      recognized slow situation at check interval tau,
               kappa = f_enc(s) (OPT omega/compact -> discrete class)
z_i            response skill of agent i (prototype-response code)
xi_tau         joint response profile (z_1..z_n at interval tau)
pi_h(z_i | kappa, z_{1:i-1}, o_i)   sequential (AR) assignment policy
pi_l(a_i | o_i, z_i)                low-level executor (skill bottleneck)
beta_i         situation-validity hazard (keep/terminate at checks)
O_t            optimality variable, p(O_t=1|s,a) = exp(r(s,a))
```

## 2. HMASD's bound (their Eq. 3), term names

```text
log p(O_0:T) >= E_q [ Sigma_t  r(s_t, a_t)
    + log p(Z | s_t)  + Sigma_i log p(z_i | o_i_t, Z)     (diversity)
    - log q(Z | s_t)  - Sigma_i log q(z_i | o_i_t, Z)     (skill entropy)
    - Sigma_i log q(a_i | o_i_t, z_i) ]                   (action entropy)
```

Practice: p(Z|s) ~ team discriminator q_D; p(z_i|o',Z) ~ individual
discriminator q_d (implemented on the NEXT observation, their Eq. 4);
q(Z|s), q(z_i|...) = the transformer coordinator; q(a|o,z) = pi_l.

## 3. Lemma 1 (vacuity) and its corollary

Substitute a RECOGNIZED team latent kappa = f(s_t) for the sampled Z:

```text
(i)  skill entropy term: q(kappa|s) is a point mass at f(s)
     -> -log q(kappa|s) = 0 identically. No entropy pressure exists.
(ii) diversity term: the variational approximator q_D(kappa|s) trained by CE
     converges to the point mass, so log q_D(kappa|s) -> 0 for every visited
     s. H(kappa|s) = 0 -> the MI bound saturates with ZERO policy-dependent
     gradient. The team identifiability reward is DEAD under recognition.
```

Corollary (what survives): the prior-corrected variant
`log q_D(kappa|s) - log p(kappa)` degenerates to `-log p_hat(kappa)` — a
COUNT-BASED SITUATION-NOVELTY bonus. Under recognition, the only remnant of
HMASD's team reward is exploration over situation classes; every trace of the
coordination signal is gone. (This remnant is itself a usable cheap lever:
see §6, optional novelty bonus.)

Consequence: any recognition-first design MUST source team pressure from
something kappa does not already determine — i.e. from the FUTURE.

## 4. Recognition-first semi-Markov PGM

Generative story (the p-side edges we posit):

```text
(a) situation drift+control:  p(kappa_{tau+1} | kappa_tau, xi_tau)
    responses are parents of the NEXT situation — skills steer.
(b) local marks:              p(z_i | o_i_{t+1}, kappa)
    a response leaves evidence in its agent's next observation
    (the recognition-side analogue of HMASD's q_d target, kept on o_{t+1}).
(c) persistence: z_i survives each check with prob (1 - beta_i); termination
    variables enter the joint like actions (mask-before-sample preserved).
```

Variational family = the policy factorization: AR assignment pi_h, executor
pi_l, hazard head; kappa treated as observed given s (encoder stop-grad per
iteration; grounding handled separately, §7).

## 5. The bound, term by term

Structured VI over this PGM (HMASD's own procedure, new edges) yields:

```text
J = E [ Sigma_t r(s_t, a_t) ]                                    (task)

  + lambda_ind Sigma_{t,i} [ log q_d(z_i | o_i_{t+1}, kappa)
                           - log pi_h(z_i | kappa, z_{1:i-1}) ]  (individual)

  + lambda_team Sigma_tau  [ log q_phi(kappa_{tau+1} | kappa_tau, xi_tau)
                           - log q_phi(kappa_{tau+1} | kappa_tau) ] (team)

  - Sigma_{t,i} log pi_l(a_i | o_i, z_i)                         (action ent.)
  + hazard log-prob terms (termination decisions, PPO-standard)
```

KEY OBSERVATION (the fusion): HMASD's Eq. 3 contains the PAIR
`+log p(z_i|o',Z)` (diversity) and `-log q(z_i|o',Z)` (skill entropy) as two
separately-implemented terms (discriminator reward + coordinator entropy
bonus). Evaluated pointwise and summed, that pair IS the individual term
above with the AR coordinator as the null model. The coordinator-residual
reward is therefore NOT a new mechanism bolted onto HMASD — it is HMASD's own
bound read carefully, with the pair fused and the null updated to the
recognition-first posterior (the AR policy). One term then supplies:

```text
identifiability pressure   (low level: make o' informative of z)
assignment entropy         (-log pi_h rewards non-obvious assignments)
anti-duplication           (a response the AR chain predictably duplicates
                            has high pi_h prob -> low reward)
```

and is structurally immune to usage-imbalance (the null IS the usage
distribution) and duration shortcuts (per-step form, no segment features).

The team term is the unique survivor of Lemma 1: with the present determined
by kappa, information about the joint response can only be injected into the
FUTURE — `I(xi ; kappa' | kappa)` in residual (drift-corrected) form.

## 6. Implementation mapping (all modules exist or are specced)

```text
individual term   Stage-1 Part B, amended: q_d head unchanged; the prior head
                  p(z|kappa) is DELETED; the null is the STORED assignment
                  log-prob log pi_h(z_i | kappa, z_{1:i-1}), broadcast over
                  the skill's lifetime steps. Requires AR-first selection
                  (Part A amendment) so the null exists.
team term         Stage 4 as planned (q(kappa'|kappa,xi) and drift head),
                  now derived rather than imported from DADS.
hazard terms      existing keep/edit + situation-validity hazard (Stage 2).
action entropy    existing low-level entropy bonus.
novelty remnant   OPTIONAL cheap lever from the Lemma-1 corollary:
                  -log p_hat(kappa) count-based situation-novelty bonus,
                  default off, available before Stage 4 if team exploration
                  stalls. One counter, no networks.
```

## 7. Honesty ledger (what is sketch, not theorem)

```text
1. The -log q(kappa'|kappa) drift baseline: introduced as a prior correction
   (HMASD's own log q - log p move). Its expectation is not policy-free
   (kappa' distribution depends on the policy); treat as a control-variate-
   style residual estimator, standard for MI-style intrinsic rewards, not as
   an exact bound term.
2. kappa = f_enc(s) with a LEARNED encoder: the derivation holds per
   iteration with the encoder stop-gradded; co-training the encoder re-opens
   representation-hacking (guard via the grounding head + freeze/train
   alternation, R14 Part C / R12.5 gate).
3. Semi-Markov bound: hazard terms enter informally as decision log-probs;
   a fully rigorous SMDP ELBO is future work — flag in the paper.
4. Lemma 1(ii) assumes q_D reaches the point mass; finite-sample q_D gives a
   small transient gradient that decays as q_D trains — worth one line in
   the paper, changes nothing qualitatively.
5. Moving null: as pi_h sharpens, the individual reward shrinks. Feature
   (annealing as coordination becomes predictable) AND risk (premature
   self-extinction). Pre-registered metric in the spec readout table.
```

## 8. Falsifiable predictions (ablation map)

```text
P1 replace AR null with uniform prior  -> usage-imbalance shortcut returns
                                          (reward concentrates on rare z).
P2 remove team term                    -> steering/formation tasks (relay
                                          chain, two-tempo gridworld) fail;
                                          individual separation alone stalls.
P3 individual reward trajectory decays as coordination sharpens (moving
   null) WITHOUT behavioral separation collapsing — else self-extinction.
P4 lifetime heterogeneity emerges from kappa_i validity hazard on
   heterogeneous-tempo tasks and does NOT emerge on S7-S1 — predicted, not
   a failure (R11.6 scoping).
P5 recognition-Z HMASD control (P2 parallel track) retains performance on
   S7-S1: context suffices there. If it collapses, kappa* commitment moves
   up the build order and the paper narrative shifts to
   "recognition + minimal commitment".
```
