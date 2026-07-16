# Disposition: R42-IRR Failure Review and R43-NRC Selection

Date: 2026-07-16

Source model: GPT-5.6 Pro

Related claim: validity and reusable meaning of `VALID_FAIL_R42_IRR_SERVICE`,
plus the single next fixed-`N` temporal mechanism after retiring R42.

## Decision

Accept the validity verdict and accept the modified single route:

```text
VALID_FAIL_R42_IRR_SERVICE remains binding
-> retire every direct skill-logit residual rescue
-> implement R43-NRC as a source-exact true renewal factor
-> sample a non-incumbent conditional skill only on RENEW
-> separate renewal/check credit from skill/segment-event credit
```

R42 established that the incumbent-conditioned residual was actionable and
learned, but the unchanged complete-replacement action grain and credit did not
produce useful temporal control. It degraded service and converged toward
synchronized replacement with narrow deterministic skill supply. It did not
test a separately sampled renewal action, renewal likelihood, or renewal
credit.

## Accepted R43 boundary

- Keep the source team `Z` sampling and native `k0=50` inspection clock.
- At the first collector initialization only, perform a structural assignment
  without a renewal likelihood. Environment auto-reset never creates a high
  action.
- At an ordinary check, sample a real `KEEP/RENEW` factor for each active agent
  in canonical MAT order.
- KEEP preserves the incumbent and opens no skill factor. RENEW masks the
  incumbent and samples one conditional skill from the remaining `K-1` labels.
- Later agents see the tentative earlier roster; the environment and low actor
  see only the atomically committed final roster.
- Zero initialization must reproduce the complete source post-skill
  distribution and decomposed log probability to `1e-6`.
- Incumbent roster, team `Z`, assignment spell, and commitment age cross
  environment auto-reset and outer-update boundaries. Auto-reset closes only a
  low-level execution fragment and resets the source low recurrent state.
- Renewal PPO uses the next 50-step controller block return. Conditional-skill
  credit ends at the next RENEW or the on-policy update boundary, not at an
  environment reset. Update boundaries bootstrap with the old critic and never
  reuse an old actor likelihood.
- Low policy and original environment-agnostic `q_D/q_d` objective remain
  unchanged. They do not read renewal, age, segment length, or task fields.
- No lifetime reward, renewal entropy, switch penalty, duration action, forced
  refresh, task shaping, variable `N`, S7, or R42 residual is authorized.

## Experiment authorization boundary

Implementation and focused preflight are authorized. The registered local gate
retains R42 exposure: seed `43041`, two concurrent 16-env arms, `320,000` steps
and `200` outer updates per arm, `3,000` updates on each original source path,
100 paired deterministic final episodes, and bootstrap seed `62043`.

The run has only three scientific outcomes after implementation and fixed-anchor
validity: `PASS_R43_NRC_K50`, `VALID_FAIL_R43_NRC`, or a concrete invalid
implementation/anchor branch. There is no rescue or underpowered branch. A PASS
authorizes only one unchanged paired multi-seed Alice--Bob verification.

Raw responses: `GPT5_6_PRO_RESPONSE_RAW.md` and
`GPT5_6_PRO_R43_SOURCE_CLOCK_CORRECTION_RESPONSE_RAW.md`.

The focused correction confirmed the source contradiction and selected
`PRESERVE SOURCE-GLOBAL CLOCK`. The accepted implementation is therefore
`R43-NRC with reset-censored controller time`: exactly two high rows per
environment and outer update, one structural assignment per training
environment for the entire run, and zero reset-triggered high actions.
