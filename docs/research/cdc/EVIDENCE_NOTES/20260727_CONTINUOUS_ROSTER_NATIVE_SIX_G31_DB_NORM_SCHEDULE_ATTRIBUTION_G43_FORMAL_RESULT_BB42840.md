# Continuous-roster native-six G43 formal result (mechanical evidence)

```text
status=FORMAL_COMPLETE
operational_valid=true
scientific_disposition=EXTERNAL_PRO_PENDING
iteration_cost_pending_external_pro=true
source_commit=bb42840ab1479abde7f3485006bfbbee981a73cf
aligned_source_commit=45e16f71d171228135b6444bee1678b157d79abe
alignment_stage_commit=889c0b4e3d68a8d74f811ae9ecfe7b5213abfa76
formal_run=logs/formal_continuous_roster_native_six_g31_db_norm_schedule_attribution_g43_cpu_20260727_bb42840_r1
registered_authorization_token=CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_FORMAL_AUTHORIZATION_V1
alignment_disposition=ALIGNED
registered_branch=EXTERNAL_PRO_PENDING
```

The fresh formal train, evaluate and analyze commands all exited zero. The
three required manifests are present and report `status=COMPLETE`,
`formal=true`, and the exact execution source commit. The analysis manifest
reports `operational_valid=true` with an empty operational-error object.

The manifests record the required CPU-only C++ backend
`ContinuousRosterToyBatch_CPU_CPP`, with `required=true` and
`python_fallback=false`, torch intra-op threads equal to one, fixed
`cpu_budget=2`, fixed `process_workers=2`, deterministic preassigned-index
merge, and one thread in each spawned native-library environment variable.
The formal inventory is three replicates, two arms, 100 branch updates per
arm, two PPO passes, 230400 training transitions, 165888 evaluation
transitions, 396288 total real transitions, 1200 optimizer steps, 72
evaluation cells, 48 episodes per cell and 10000 bootstrap resamples. No
intrinsic K search or hypothetical transitions are recorded and checkpoint
selection is final-only.

The exact analysis fields are recorded mechanically below; no scientific
interpretation is made here:

```text
analysis_branch=EQUAL_MEAN_RAW_SUM_SUFFICIENT_G43
thresholds=event_floor=0.85|minimum_replicate_floor=0.85|norm_margin=0.05|process_noninferiority_margin=-0.05|segment_floor=0.85|stochastic_floor=0.8|utility_floor=0.9
dbnorm_access_pass=true
dbnorm_access_confident_fail=false
mean_access_pass=true
mean_access_confident_fail=false
mean_noninferior=true
treatment_activation_valid=true
material_dbnorm_advantage=false
dbnorm_minus_mean_primary_ci95=[-0.011225482067719502,-0.002150755706791103,0.004070022362694589]
dbnorm_minus_mean_capacity_ci95_6=[-0.0068400835244667516,-0.001013545713519486,0.0035977968435704608]
dbnorm_minus_mean_capacity_ci95_8=[-0.011701088560928172,-0.0023679790939476883,0.004730643266352628]
dbnorm_minus_mean_capacity_ci95_12=[-0.014737983302311769,-0.0029713007850666892,0.0037918926160550375]
```

This note records transport and runtime facts only. It does not interpret the
scientific metrics, consume the valid iteration, or change CDC, ledger,
portfolio, or successor state. External Pro disposition is required.
