# VSPC1 native hold-value B01 technical acceptance

Engineering accepted on 2026-09-08, subject to Root integration and the separately
selected native execution route. No native invocation was performed. Checkout:
`C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906`, branch
`codex/direction-vsp_c1`; clean/pushed input
`6f3634dfdbb59cf6dc71b6625e86153a9316b167`. The accepted commit is the commit
containing this document; the CM return supplies its full SHA.

Contract: [CM specification sections 1-6](VSPC1_NATIVE_HOLD_VALUE_B01_CM_SPEC_20260908.md)
and [science card sections 2-6](VSPC1_NATIVE_HOLD_VALUE_B01_SCIENCE_CARD_20260908.md).
Independent [production review](VSPC1_NATIVE_HOLD_VALUE_B01_PRODUCTION_REVIEW_20260908.md)
inspected the actual new implementation and read-only source dependencies.

## Delivered source and boundaries

Owned source is `experiments/candidates/vsp_c1/native_hold_value_b01/{__init__,critic,study}.py`
and `scripts/run_vspc1_native_hold_value_b01.py`; tests mirror the attempt at
`tests/experiments/candidates/vsp_c1/native_hold_value_b01/{test_critic,test_study}.py`.
The original UCOPE environment, actor, collector, return computation, optimizer and
four-epoch update remain unchanged. This study does not call UCOPE run_pair or aggregate.

GATED-V keeps the original full first-layer parameters, partitions only its arithmetic
at remaining-hold columns119/123/127/131/135, and adds one directly constructed zero
128-by5 parameter without a random initializer. Common source tensors are independent
copies; both actors receive the source duration head. Scalar and batched outputs keep
the source shapes. Collection and update explicitly select `agent_compound`.
The ordered GATED-V/MLP-V fits retain two complete episodes per update, private per-arm
training streams, matched reset domains and final-only sampled evaluation; H reuses
the second environment and has no model. JSONL rows retain native prefix/suffix values.
Primary pairing uses episode plus declared reset seed, with no subset mean presented
as complete. Missing H preserves the complete primary; strict MEI branches and three
dependent difference lists are retained. Gate relative displacement is null because
its initial norm is zero; source duration-head exposure is retained, including its
legacy epsilon-based relative number, which is not interpreted as a defined zero-norm ratio.

No scope-spec section 4 machinery is added (card section 6: none). Source is329 lines in the final implementation, including
35 runner lines, below2000/600. Required serial study I/O and budget handling were
independently reviewed for necessity; no framework, new logger, retry, resume,
source-currentness guard, native host change or extra scientific arm is introduced.

## Actual checks

All commands used the configured local scientific interpreter, CPU FP32, with no
package changes. Exact original focused command:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/native_hold_value_b01 tests/experiments/candidates/vsp_c1/native_hold_value_b01 tests/experiments/candidates/ucope/uav_motion_prefix_b01/test_agent_clipping.py
```

Exit0;21 passed in8.12s (command observation approximately10s plus terminal poll).
Coverage includes initialization/no RNG, parameter counts and independent storage,
A0 normalized FP32 correspondence at rtol1e-5/atol1e-6, gate gradients, pre-decision
countdown and masks, recurrent/reward rows, actual CLI/study compound plumbing, seed
domains, final-only sampling, analytic SE/MEI/adverse endpoints, missing primary/H,
partial steps, checkpoint/summary readback and late publication. Six inherited
clipping test cases exercise the unchanged compound learner boundaries.

Review requested the original fake-clock H-overrun case be explicit. Added it to the
existing deadline test and ran this focused correction:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/native_hold_value_b01_h_cap tests/experiments/candidates/vsp_c1/native_hold_value_b01/test_study.py::test_continuous_deadline_and_late_publication
```

Exit0;1 passed in3.69s, tool wall5.070s. After the timing-report fields were clarified,
ran the same single test with `--basetemp temp/directions/vsp_c1/test/native_hold_value_b01_exit_fields`:
exit0;1 passed in3.93s, tool wall5.483s. Total reported pytest15.74s; total command
observation under22s, within300s. All runs report the existing `cache_dir` config
warning because the requested command disables cacheprovider; no test failure.
No repeated full suite or scientific replay followed.

Exactly one original runner smoke:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_vspc1_native_hold_value_b01.py --engineering-fixture --seed 9001 --out temp/directions/vsp_c1/exp/native_hold_value_b01_engineering9001
```

Exit0, tool wall3.991s, summary in-process wall3.297s, below60s. `ENGINEERING_FIXTURE`
status COMPLETE:80 synthetic team steps,8 Adam calls,6 evaluation episodes,10 complete
scored episodes,2 constructor resets,0 partial steps,0 scientific UAV calls and0 optional
frames. Both final checkpoints have explicit object/configuration/seed/algorithm and
duration parameters; all three endpoint lists, dependence identity and finite common,
critic and total norm ratios were read back. Gate absolute displacement0.0130027234554,
relative null. These are engineering facts, not UAV evidence.

Artifacts beneath the checkout's ignored
`temp/directions/vsp_c1/exp/native_hold_value_b01_engineering9001/`:
`summary.json`, `episodes.jsonl`, `rollouts.jsonl`, `final_GATED-V.pt`, `final_MLP-V.pt`,
and `engineering_readback.json`. Ordinary readback exited0, tool wall2.088s, and did not
call the environment or learner. The fixture predates only the reporting-field
clarifications; changed stubbed publication/cap checks cover them. No second fixture.

## Review disposition and remaining execution observations

1. Added the missing fake-clock H-overrun coverage: cap breach is attributed to MLP,
   complete primary survives, and H-relative output remains incomplete. Passed.
2. Source update returns epoch losses only after a complete four-epoch call. The
   summary now explicitly labels loss coverage as completed updates only; actual
   partial-update Adam counts and partial native step/decision counts survive aborts.
   Remaining-hold counts are explicitly returned-complete-episode coverage. No copied
   learner or invented partial losses are added.
3. Internal deadline checks include imports/common initialization, learning, evaluation,
   H and summary/checkpoint readback/publication. They cannot observe interpreter exit.
   Summary labels this boundary, records exact `mlp_start_pair_elapsed`, and leaves
   `complete_exit_cap_conformance` unmeasured. Internal `cap_breach=false` is not a
   statement of whole-process exit compliance. Reviewer found no remaining material
   production defect after these dispositions.

**Required observation on the separately authorized native invocation:** use the
existing detached supervisor's terminal process interval, alongside the internal
pair wall and MLP boundary. Startup belongs to GATED; H, pair publication/readback
and exit belong to MLP. If the external/internal residual cannot be split into
startup versus exit, report the split as unobserved. For cap assessment use conservative
upper bounds: each measured arm interval plus the entire nonnegative residual, with
whole invocation wall as the direct total. This bounds uncertainty without claiming
all residual was MLP work. Existing timestamps that distinguish the components may
replace those bounds. Do not equate supervisor task time including admission with an
exact scientific process interval; a enclosing interval can only be a conservative
bound. The fixture's external-minus-internal~0.694s also includes unpartitioned
launcher/observation overhead and is not all demonstrated scientific compute.
DM explicitly accepted this observation method; caps remain1800s/arm and3600s/pair.
No new telemetry framework or execution is allocated here.

Per-arm cost projection remains the card's reused-loop law: GATED initialization plus
131072 collection steps+1024 Adam calls+8192 evaluation steps+publication; MLP has the
same fit and adds8192 H steps and pair publication/readback/exit. Incremental gate wall
is unmeasured; no new cost-calibration experiment ran. Post-learner publication is
covered by the sole complete synthetic fixture and failure/late-publication tests.
Optional resource telemetry is `resources_unmeasured`; this is no admission receipt.

Root owns integration. The same DM then binds accepted source and directs the
separately selected seed8101 pair plus H through the detached remote route after
fresh mandatory admission. Native behavior, performance and runtime resource/cap
conformance remain unmeasured; engineering acceptance establishes implementation
conformance, not a scientific result or automatic native admission.
