# Noncalendar G0 — Direct-Access Source Clarification

The accepted Convergent response for
`20260720_noncalendar_g0_no_access_portfolio` correctly preserves the valid
`NO_ACCESS_BENCHMARK_ORDINARY_CONTROL` result and selects ordinary-access
localization before any hierarchy comparison. Its concrete selected treatment,
however, is not executable or scientifically distinct.

The proposed D1 adds `(g_i-x_i)/4` and `target_changed` to the current D
checkpoint. The frozen D observation is already width 15 and retains:

- common active mean `(g-x)/4`;
- common mean `abs(g-x)/4`;
- common active fraction `target_changed`;
- local `(g-x)/4`;
- local `target_changed`.

Only C masks those demand/error fields. The implementation constructs them in
`NoncalendarTrackingEnv._raw_observations`, and the focused test asserts the
15-dimensional demand-visible view. The selected D1 is therefore identical to
D0. Calling it evaluation-only also conflicts with any genuinely new input
dimension, because the frozen checkpoint cannot consume a changed input shape
without a trained replacement.

This focused clarification does not reopen the accepted evidence validity,
portfolio weights, ordinary-access prerequisite, G0 result, environment,
intrinsic-reward boundary or final capability target. It must replace only the
non-executable selected source with one code-ready smallest source or an
explicit stop.
