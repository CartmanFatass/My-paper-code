# R44-FS-NRC Controller Disposition

Date: 2026-07-16

## Verdict

`VALID_FAIL_R44_FSNRC`

R44 preserved the frozen R41B Alice--Bob service anchor and satisfied the
registered implementation and safety contracts, but it produced no temporal
decoupling. The frozen-source `K=50` renewal-timing route is therefore
permanently retired without a rescue run.

## Direct evidence

- Both arms completed 320,000 environment steps, 200 outer updates, and 3,000
  factor optimizer steps. All five source optimizer paths took zero steps.
- Both arms retained deterministic final win/key0/key1 rates of
  `0.93/1.00/0.93`; treatment-minus-control win CI was `[0, 0]`.
- Source modules, source optimizers, and source ValueNorms had exact zero drift
  in both arms. Stored/replayed renewal likelihood and conditional-ratio error
  were both zero.
- The inactive control renewal actor had zero drift and zero nonzero-gradient
  steps. The treatment actor had relative drift `0.353245` and nonzero
  gradients on all 3,000 factor steps.
- Nevertheless, both arms had zero discordance, `1.0` full-sync RENEW rate,
  and zero minimum KEEP/RENEW marginal. Their zero-step and final deterministic
  outcomes and complete high- and low-action traces were exactly equal.

## Analyzer correction

The first analyzer pass returned `INVALID_R44_FSNRC_IMPLEMENTATION` solely
because it accidentally required a nonzero critic gradient on every one of
3,000 optimizer steps. The registered M0 contract requires finite critic
gradients and at least one nonzero exposure in each arm. The control and
treatment renewal critics had 3,000 and 2,992 nonzero-gradient steps,
respectively, with finite gradients on all 3,000 steps.

The analyzer condition was corrected from `critic_nonzero_steps == 3000` to
`critic_nonzero_steps > 0`, and only analysis was rerun. Training, artifacts,
thresholds, and scientific metrics were unchanged.

## Binding boundary

The result establishes that the registered next-check renewal credit can move
the treatment renewal actor while leaving deterministic renewal decisions and
temporal behavior unchanged on the frozen R41B source system. This retires:

- the frozen-source `K=50` renewal-timing route;
- the same next-check renewal-credit estimator under budget, seed, learning
  rate, entropy, temperature, or threshold changes;
- attempts to rescue the line by weakening the service or decoupling gates.

It does not test or retire new skill discovery, joint low-level adaptation,
general asynchronous skill learning, S7 transfer, open rosters, or variable
team membership. No successor is implemented or launched before one
structurally different causal edge and its abandonment gate are selected.
