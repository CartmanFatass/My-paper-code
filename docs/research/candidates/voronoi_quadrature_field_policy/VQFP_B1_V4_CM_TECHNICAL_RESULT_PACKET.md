# VQFP B1 v4 CM technical result packet

Scope: `direction:voronoi_quadrature_field_policy`  
Revision: `VQFP-B1-MATH-CLOSURE-20260812-04`  
Attempt: exact from-scratch recovery attempt 4 after attempt 3's external Windows restart  
CM disposition: technically complete retained question-relevant output

## Production identity and recovery provenance

The exact command was:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.voronoi_quadrature_field_policy --execute --output-root C:/Projects/HMASD/artifacts/voronoi_quadrature_field_policy/vqfp_b1_v4_attempt4_recovery --result C:/Projects/HMASD/artifacts/voronoi_quadrature_field_policy/vqfp_b1_v4_attempt4_recovery/VQFP_B1_RESULT.pt
```

Attempt 3 remains quarantined intact at
`artifacts/voronoi_quadrature_field_policy/vqfp_b1_v4_attempt3_planned_restart`.
No attempt-3 checkpoint, parameter, optimizer state, random state, trajectory,
panel, estimate, or value was loaded or used by attempt 4.

Before launch, system-total CPU was measured exactly three times within 30
seconds: `11.634%`, `44.259%`, and `33.748%`. The bounded restart guard found
no CBS or Windows Update reboot-required marker, no `UpdateExeVolatile`, no
pending computer-name change, no matching reboot/restart scheduled task, no
post-boot restart event, and no matching VQFP Python process. The 24 pending
file-renames were paired print-driver spool replacements, not an update reboot
request. The fresh recovery root did not exist before the one launch.

## Terminal and resource facts

- activity began at `2026-08-12T21:12:29.498226-07:00` immediately before the
  first optimizer mutation;
- the production completion receipt was written at
  `2026-08-13T00:09:58.434416-07:00`;
- retained run elapsed time was `10,651.25` seconds;
- peak RSS was `998,420,480` bytes;
- one CPU process and one CPU thread were registered, with no GPU;
- all resource limits held: under eight hours and under 2 GiB;
- the exact retained ledger is `4,098,048` transitions/states:
  `2,304,000` training, `786,432` ordinary intact, `393,216` ordinary cut,
  `393,216` conflict intact/cut, `196,608` noisy, and `24,576` controls;
- all 24 final update-375 checkpoints exist: both arms for each of the 12
  registered seeds;
- the retained result exists at
  `artifacts/voronoi_quadrature_field_policy/vqfp_b1_v4_attempt4_recovery/VQFP_B1_RESULT.pt`
  and contains all 12 paired seed panels;
- `completion.json`, final `manifest.json`, and `activity.json` agree on the
  revision, command, result path, activity state, resources, and ledger;
- no failure receipt exists, and the retained packet reports no anomalies.

The observation wrapper timed out after one hour while the production process
continued independently. Later process polling established natural exit, but
the wrapper retained no direct exit code. The completed atomic result,
completion receipt, final manifest, exact count ledger, complete checkpoint
bank, and absent process are sufficient for the CM technical terminal. A
backfilled external terminal record truthfully preserves the missing-exit-code
limitation at
`temp/sessions/experiment_operator/vqfp_b1_v4_attempt4_recovery/terminal.json`.

## Retained output facts for same-direction EM intake

These are literal retained-program outputs, not CM scientific interpretation:

- all nine preflight checks are `true`;
- complete paired final checkpoints, single-final-checkpoint panel use, exact
  rule containment, no held-out training/selection, and positive/unit-sum
  volumes are `true`;
- oracle headroom availability is `false` for both registered endpoints;
- endpoint labels are `P=UNAVAILABLE` and `R=UNAVAILABLE`;
- direct classification is `STATISTICALLY_INDETERMINATE`;
- `binding_without_direct_value=false`;
- mechanism gates are `K=true`, `M=false`, `T=false`, and
  `support_and_controls=false`;
- retained inference values are:
  `lower_performance=-0.0016434416687408655`,
  `upper_performance=0.00271726901490684`,
  `lower_robustness=-0.0022503800729578895`,
  `upper_robustness=0.002682652825083947`,
  `lower_quadrature=0.05834208104052163`,
  `lower_action_tv=0.0013405183692655588`,
  `lower_return_contribution=-0.00042287360313289024`, and
  `upper_noise=0.0024039126511599096`;
- the four held-out equal-seed mean differences, in registered
  `(N, regime)` order, are:
  `(4,IID)=0.000922277569770813`,
  `(4,CLUSTER)=0.0009747147560119629`,
  `(14,IID)=0.0015287697315216064`, and
  `(14,CLUSTER)=0.0015705724557240803`;
- aggregate `Gamma=-0.000022922952969868977`, aggregate bypass
  `B=0.000026765608026835253`, action-TV association
  `0.5544984980567509`, and return association `0.18815126797158324`;
- noisy modifier is `NO_NOISY_PANEL_MATERIAL_REVERSAL`;
- the retained second-surface field is
  `DO_NOT_ACTIVATE_UNTEMPERED_2D`;
- the packet's own claim ceiling is
  `finite noise-free exact-cell-average one-dimensional periodic host only`.

## CM acceptance and next owner

CM technically accepts attempt 4 as a complete retained output conforming to
the exact v4 implementation, registered checkpoint/panel lifecycle, count
ledger, and resource envelope. No repair or rerun is indicated or authorized.
Root should relay this packet and the retained result to the same VQFP Explorer
Manager for scientific interpretation. Any valid-result convergence question
belongs to that owner and the existing same-direction ChatGPT Pro conversation.
