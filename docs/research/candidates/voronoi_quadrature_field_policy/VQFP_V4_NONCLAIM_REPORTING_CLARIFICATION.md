# VQFP v4 non-claim raw-reporting clarification

Owner: `direction:voronoi_quadrature_field_policy` Explorer Manager  
Identity: `VQFP-V4-NONCLAIM-REPORTING-20260812-01`  
Controlling science revision: `VQFP-B1-MATH-CLOSURE-20260812-04`  
Scientific activity begun: `false`  
Scientific meaning changed: `false`

## Owner ruling

The bare word `overlap` in the reporting-only sentence of the v4 card is
non-claim-bearing and removable. It is not assigned a scalar formula because
at least redundant service intensity and demand-weighted saturation loss are
inequivalent reward-consistent quantities, and neither quantity answers a
registered VQFP question.

`overlap` never appears in `J_episode`, `P`, `R`, `K`, `M`, `T`, `Gamma`, the
two fixed associations, bypass, noisy reversal, oracle headroom, support,
structural controls, availability, branch precedence, family deletion,
resource accounting, second-surface activation, claim language, or the
expected CM-to-EM result packet. Selecting a definition now would introduce an
unregistered descriptive diagnostic without changing any decision.

## Exact reporting consequence

The required episode-level raw summaries are exactly:

```text
raw_return
  = sum_(t=0..31) r_t,

service_mass
  = sum_(t=0..31) sum_j v_j*s_j(t)*(1-exp(-u_j)),

cost
  = sum_(t=0..31) 0.08*sum_i v_i*a_i^2,

action_frequency(a)
  = [1/(32*N)]*sum_(t=0..31) sum_i 1{a_i=a},
    separately for a in {0,1/2,1}.
```

`raw_return=service_mass-cost` holds when the same stored per-tick terms are
used. It is a reporting identity, not a new tolerance, validity gate, or
endpoint.
No `overlap` key, column, aggregate, threshold, missingness flag, or acceptance
condition is required. If code already produces an overlap-like value, it is
unregistered implementation telemetry and must be excluded from scientific
completeness, endpoint availability, model/checkpoint selection, analysis,
rerun decisions, interpretation, and claims. Its absence is not missing
scientific data.

All required primitives needed for the reward, the four retained summaries,
and every registered estimand remain unchanged. `P/R/K/M/T`, all sample and
state counts, thresholds, branch ordering, activity boundary, complexity
ceiling, and construction requirements are unaffected.

## Revision and authority consequence

This resolves an undefined optional reporting label by removing it; it does
not alter the scientific object reviewed by Pro. The controlling revision
remains `VQFP-B1-MATH-CLOSURE-20260812-04`, whose same-direction Pro disposition
is `CLOSED` with zero science-bearing defects and whose owner intake is
complete. No v5 composite or Pro rereview is warranted.

Root may relay this clarification with the unchanged v4 card and handoff to CM.
CM retains authority over implementation and technical acceptance. This ruling
authorizes no code, test, result, production, provider, Gemini, or portfolio
action.
