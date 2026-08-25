# Contract Question: EVENT_HELD_COMMITMENT_LINK_G0 Behavioral Battery

Sent to GPT-5.6 Pro by the user on 2026-07-21, before any result was observed
and before the separate implementation code review in
`docs/external-review/gpt5_6_pro/20260721_event_held_commitment_link_g0_code_review/`.

This question concerns the scientific validity of the result contract, not the
correctness of the implementation.

---

```
Concern raised against the EVENT_HELD_COMMITMENT_LINK_G0 result contract,
grounded in docs/project/ALGORITHM_PRINCIPLES.md.

PRINCIPLE (§2.3): "A long-lived skill must arise from learned behavior under
the declared clock contract, not from a task-specific lifetime reward or an
enlarged duration-action catalogue alone."
PRINCIPLE (§2.2): "Skill-label usage, entropy, or classifier accuracy is not
sufficient evidence of a useful skill."

CONTRACT UNDER QUESTION. The result contract qualifies EHC behaviour with:
  - LCB(P_KEEP) > 0.20 and LCB(P_RENEW) > 0.10 over non-CREATE opportunities
  - LCB(CV(T)) > 0.25 for complete active-step lifetimes
  - LCB(mean(||W_z(z - z_perm)||_2 / sqrt(3))) > 0.10 under z derangement
These separate COMMITMENT_SUPPORTED from REPRESENTATION_ONLY.

OBSERVATION 1 — CV(T) passes by construction.
Delta is SAMPLED uniformly from {4,8,12}; the policy chooses only KEEP/RENEW.
A segment lifetime is T = sum of k Deltas, k ~ Geometric(p_renew).
  Var(Delta)/E[Delta]^2 = (32/3)/64  =>  CV = 0.408 at k=1.
  always RENEW (k=1):   E[T]=8,  CV(T)=0.408
  50/50 KEEP/RENEW:     E[T]=16, CV(T)=0.764
CV(T) >= 0.408 for EVERY policy, including an untrained one. The 0.25 threshold
is satisfied by the Delta sampling distribution alone and carries no information
about learned lifetime heterogeneity — the project's stated target capability.
The lifetime-bin condition ([1,8],[9,16],[17,inf), two bins with LCB > 0.10)
appears similarly satisfiable by construction.

OBSERVATION 2 — natural-use gates are non-degeneracy checks.
Support is binary, so P_KEEP + P_RENEW = 1. Requiring P_KEEP > 0.20 AND
P_RENEW > 0.10 only requires the policy to be non-degenerate; a uniform random
event head passes both. Per §2.2 this is usage statistics, not evidence of use.

OBSERVATION 3 — the intervention gate measures magnitude, not consequence.
||W_z(z - z_perm)|| is logit-perturbation magnitude. A large W_z applied to
meaningless z passes it. It does not test that the perturbation changes
behaviour in a way that helps.

CONSEQUENCE. The primary estimand G = U_EHC - U_DUM remains sound; that
comparison is genuinely mechanism-matched. But the behavioural battery attached
to it may not discriminate a policy that learned structured commitment use from
one that learned nothing, which is precisely the COMMITMENT_SUPPORTED vs
REPRESENTATION_ONLY distinction.

QUESTIONS. (1) Is CV(T) >= 0.408-by-construction correct? (2) Does the battery
discriminate learned behaviour at all? (3) If not, what is the minimal
replacement? One candidate: condition on k, the KEEP-chain length, which is
purely policy-determined, instead of T, which is dominated by the Delta draw.

CONSTRAINT. No results have been observed, so this is a pre-registration
question, not a post-hoc threshold rescue. Thresholds are frozen once the run
starts.
```

## Correction to the question as sent

The claim `CV(T) >= 0.408 for EVERY policy` is **wrong** and was corrected by
the reviewer. The bound holds only within the constant-hazard geometric
renewal family. A deterministic-`K` policy falls below it, and below the
registered gate:

```text
geometric p=1.0 (always RENEW)   CV(T) = 0.408248   passes 0.25
geometric p=0.5                  CV(T) = 0.763763   passes 0.25
deterministic K=2                CV(T) = 0.288675   passes 0.25
deterministic K=3                CV(T) = 0.235702   FAILS 0.25
deterministic K=4                CV(T) = 0.204124   FAILS 0.25
```

This strengthens rather than weakens the objection: a policy that learned a
crisp deterministic renewal rule fails the lifetime gate, while a uniform
random head passes it. The gate is anti-correlated with the learning it is
meant to detect.
