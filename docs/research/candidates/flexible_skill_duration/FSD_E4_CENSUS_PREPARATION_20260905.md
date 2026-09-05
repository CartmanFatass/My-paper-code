# FSD E4 renewal/reference census — invocation preparation

Status: **source/document inspection complete; invocation card not frozen; no run**.
Inspected source: `056b796f7e95103a18bb521410151c946163495d` on local main.
This prepares the sole next object selected in
`FSD_E3_COMPLETE_CONVERGENCE_INTAKE_20260905.md` and its complete archived
`pro_packets/20260905_e3_complete_convergence/archive/RESPONSE.md`.
It makes no new direction or Portfolio decision and does not resume a blocked workflow.

## Question, scope and contrary expectation

For the existing finite renewal host, what native return opportunity separates public reactive
renewal from fixed clocks and the complete open-loop reference set? Class A/RECON; no training.
The claim ceiling is a numerical reference opportunity on this host. It is not D2/D8 advantage,
tuned-generic headroom, a variance-only causal intervention, or an E4 learner-readiness claim.
E3 remains 18/18 valid with its original bounded H0 and competent small-seed2 contrary evidence.

At K=2, the public change flag and lagged cue identify the unique new latent, and the existing
GreedyOnPublicState implementation reuses switching. A positive reactive-versus-clock gap may
therefore be entirely scripted. Deterministic D20 from age0 is expected to align with k20;
this is a source-derived prediction, not a newly observed result. No gain magnitude or ordering
between learned methods is predicted. Learning MEI is inapplicable; unresolved numerical
differences remain unresolved. Owner prediction: not taken for this preparation.

## Exact existing computation

The public API is `envs.relay_corridor.references.enumerate_references(config)`.
`ReferenceReport` includes all open-loop candidates in memory, while `as_dict()` omits them.
`proposal_config()` supplies an E3 Bernoulli configuration and must not be used unchanged.
The following is a constructor specification, **not an executed command or an existing CLI**:

```python
RelayCorridorConfig(
    n_agents=6, n_roles=2, n_zones=4, n_regions=2, horizon=400,
    delta=0.4, event_process="renewal", renewal_law=law,
    renewal_mean=20.0, lognormal_shape=1.0,
    d0_k_set=(1, 2, 5, 20, 40), rho=0.0, c_probe=0.0,
    e5_coupling_enabled=False, role_decode="argmax",
)
```

The three source tokens are `deterministic`, `geometric`, `lognormal` (the last means rounded
lognormal). Both regions receive the same law. Entity/zone/region membership is fixed. Initial
dwell age is zero; lease renewal costs one zero-service step and does not reset regional dwell
age. DP propagation is not learner exposure: training episodes, learner transitions, optimizer
updates and checkpoint/model selection are all zero.

Source anchors: `envs/relay_corridor/config.py:36,213`; `references.py:61,187,202,231,277`;
`renewal.py:124,148,199,257`; `host.py:208,266,342`. Existing tests at
`tests/relay_corridor_host_test.py:249,356,527` cover relevant laws, phase and references;
they were inspected, not rerun in this preparation.

## Structural cost and missing actual-node projection

For each law the existing work is
`2 regions * (1 switching + 5 fixed-k + 2 roles * 6 open periods) = 36 DP evaluations`.
Greedy at K2 reuses switching. Each DP propagates H400 over shape
`(K, 2, 2, age_states, 2)`; each law combines `2^4 * 6 = 96` candidates without extra DP.

| Law | Age states | Cells per DP state array | H * cells * 36 (structural work proxy) | Wall projection / cap |
| --- | ---: | ---: | ---: | --- |
| deterministic D20 | 20 | 320 | 4,608,000 | unmeasured / not frozen |
| geometric mean20 | 2 | 32 | 460,800 | unmeasured / not frozen |
| rounded-lognormal mean20 shape1 | 400 | 6,400 | 92,160,000 | unmeasured / not frozen |

Total: 108 DP evaluations and 288 candidate values. The proxy is not a FLOP count, seconds,
or a measured speed ratio; vectorization and law construction contribute differently.
Lognormal also performs finite support calibration and moment calculation. These costs must
be included in any actual-node wall projection, including cold-cache construction.
E3's 18.3575 valid-cell hours cannot supply this enumerator's timing coefficient.

No wall-time coefficient, numerical error bound or per-law cap was measured or silently chosen.
Before execution, the invocation card must state its actual-node cost measurement method,
per-law projection/cap, numerical reporting tolerance and exact committed runner command.
This is an unfinished invocation contract, not an additional Pro or owner-approval gate.

## Smallest missing engineering surface

No existing E4 census CLI was found. Existing FSD E0/E2/E3 scripts enter training/rollout paths.
A thin research runner must call the existing enumerator and publish a single summary per law;
it need not rewrite the DP, simulate trajectories, introduce a learner or modify core APIs.
The required summary is:

- Exact config/source/node/command; zero learner exposure; wall time and peak RSS where measured.
- Law identity, numerical mean and variance, age cap and hazard table.
- For rounded-lognormal: calibrated log location, finite moment support cap, computed mass and
  residual mass `1 - computed_mass`; distinguish finite moment truncation from the H400 DP age cap.
  Existing `_moments()` returns mean, second moment and mass. Its private status must be explicit
  if reused by a disposable research runner; no new core compatibility API is needed.
- J_switch, J_greedy, every J_k and k*, all 96 role-map/period/value rows, best open-loop value,
  m, m_dur, and `J_best_fixed_k - J_fixed_k[20]`.
- Numerical error/consistency observations and the exact status of incomplete output.

`as_dict()` alone is insufficient. Do not replace expected-reference values with noisy host
rollouts, call `resolution_ok()` as a new learning gate, or present floating arithmetic as
infinite-support exactness. Stop a law on nonfinite values, unexplained calibration/reference
mismatch or its prospectively declared cap. Preserve partial output as incomplete, without
scientific polarity, outcome-based changes or automatic learner follow-up.

No source was added in this preparation. Any later implementation needs its own bounded
assignment, applicable engineering scope accounting and focused verification. A portable
result invocation then uses the configured remote node, exact committed/pushed bytes and
fresh physical/effective >=4GiB admission immediately before the same detached command.
Prior platform restrictions remain unresolved; this document does not lift them.
