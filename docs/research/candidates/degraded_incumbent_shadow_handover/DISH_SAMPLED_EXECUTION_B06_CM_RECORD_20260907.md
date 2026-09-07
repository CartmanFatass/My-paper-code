# DISH B06 implementation acceptance — 2026-09-07

Implemented the [bounded handoff](DISH_SAMPLED_EXECUTION_B06_CM_OBJECTIVE_20260906.md) against
base `fde638f9c85d86fc01fe003254397b18dfdeacc6`. No scientific invocation was launched.

The B06 study reuses the B04 learner and B02 episode evaluator. Explicit master-family arguments
reach initialization, environment resets and training flow while preserving B04/B05 defaults.
The width1 evaluation sampler uses the frozen separate policy stream, public pre-step owner
roles, physical tick and original transforms. One native batch supplies ten independently addressed
words per renewal; nonrenewal consumes none. Native/TRAIN source and laws are unchanged.
The same final checkpoint supplies all four modal and eight sampled rows with fresh native and
recurrent state and fixed normalization. The four initial modal companions, native facts and
post-step first-transfer tick/null are retained. Primary publication requires all sixteen rows.

[Focused evidence and cost charge](sampled_execution_b06_20260906/IMPLEMENTATION_CHECKS.json)
records the exact synthetic pytest command, environment and both attempts. Final result: **4 passed
in 1.79s**. Coverage exercises master consumers, addresses/transforms, nonrenewal and modal behavior,
checkpoint/state ownership, native-triggered promotion, first transfer/null, complete reduction and
JSON publication. The first attempt's single failure was a test expectation of STRUCTURED alpha0;
existing production rows use alpha1. Only that test expectation changed. Both attempts are charged.
AST parsing and final whitespace/diff checks passed. No real initializer, learner or native episode
ran; no measured scientific output or performance claim follows from these checks.

Independent reviewer `rev_ah_dish_b05_seed` (Meitner) inspected the final full diff and focused
tests, including the ten-word batching correction, and reported **no material findings**. It confirmed
all protected invariants and the alpha1 correction without rerunning the checks. CM accepts the
implementation at this synthetic/static evidence ceiling.

Engineering-scope §4 additions: **none**, as card §6 requests. Non-test source accounting is
**A=339, D=15**; runner=90 lines; tests=326. A conservative orchestration count includes the whole
runner (90), whole B06 run_study (44), and every added shared-plumbing line (27): O=161,
O/(A+D)=45.48%. This review signal reflects the bounded composition/publication task; the independent
review found no prohibited machinery. No native ABI, training source fork, worker service or registry
was added. Source budgets pass.

Per-arm cost projection remains the card's measured B05 anchors (212.86s LOW_LR and 7.11s shared
reference), with new E/H/R and sampled execution time unknown. No new pilot was selected. Required
local checks are conservatively charged **10s**, leaving **1790s** of the single complete 1800s cap
for a later authorized invocation, including remaining build/load and publication work. The two
execution modes share one learner; they are not independently priced training arms. Study elapsed,
complete machine wall, aggregate CPU and runtime resource conformance remain unmeasured for B06.
Post-learner publication was exercised with synthetic complete/incomplete panels and JSON readback.

Root integrates the pushed CM branch; DM retains scientific acceptance and supplies any separate
launch assignment. A later portable CPU launch uses the configured remote node, exact committed
bytes and fresh same-node memory admission. No B06 handle exists to adopt.
