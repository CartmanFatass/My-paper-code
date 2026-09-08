# FSD native renewal A01 — P21 readiness intake

2026-09-07. **READY for Root's exact allocated G → C → H route.** This is technical/card
readiness, not a native-return result. Actual staging, admission and scientific execution
have not yet occurred in this preparation.

## Assignment, actual checks and applicable rule

P21 FSD at `d3f03ffa42c19c3a3eeba176ec10bd2e19d6ade5` releases only the existing selected
panel after ordinary readiness. The card's new section 7 records that allocation at
`01770d8dd6bb59460667efa26e3d94677e65ab37`; sections 1–5 remain scientifically unchanged.
The designated checkout is `C:/Projects/HMASD-worktrees/codex-fsd`, branch `codex/fsd`.
The P21 reconciliation merge `39bd56de9c277c53a2441d69efbbb9e63809f972` retained all
125 main audit rows, which already contained all 101 existing direction-checkout rows,
and was immediately pushed. No unrelated source or dirty work was replaced.

Accepted implementation is `4c87eecdde0f67eef7e1f9b872d10f13dca68d40`, two owned files:
342-line runner and 296-line focused test. The DM read the actual load, fresh-state/action,
scoring, pairing and publication paths against the frozen card/spec. Source differences from
that baseline to the launch SHA are empty for the runner/test, config.py/config_1.py,
hmasd/, relay-corridor code and E2/E3 runners. The existing independent integration review
by `/root/fsd_cm_baseline_a01/fsd_integration_review` therefore remains applicable and
reported no material finding; no independent empirical evidence is inferred from that review.

The DM directly read the archived `checks.json`, `FINAL_RESPONSE.md` and fixture summary at
`C:/Projects/HMASD/temp/cm-model-comparison/20260907/batch-02/outputs/baseline/turn-01/return/`.
They report 12 passing focused cases, exit 0, pytest 1.83 s and the successful original
fixture/readback. The fixture actually contains 6 engineering episodes, 24 scoring steps,
144 agent observations, 8 fake controller batches, 4 Greedy batches, zero actual model
constructions/loads, training or optimizer steps. CM's handoff also records the separate
normal integration checks and independent review. No passing suite or fixture was rerun
for this documentation-only continuation. Actual checkpoint restoration remains untested.

The applied integrity rule from evidence-spec section 4 is:

> treat an engineering or instrumentation failure as limiting the dependent observation; a
> separate direct fact remains reportable when it is independently trustworthy;

CM published the complete literal handoff at `27728719fbcb90a37af106850b9c8bfa81ecc37e`.
DM acceptance returned three concrete command-document gaps to that same CM: avoid creating
scientific result directories before admission; restrict new time output to wall/RSS/exit;
and preserve otherwise trustworthy results when only optional telemetry is missing. All
three were corrected at `407f11189a69561795cecabe951720a73c752e95`. The revised Bash blocks
passed remote `bash -n` parsing with exit 0, without executing the policy commands. The DM
read the exact correction diff. No source or scientific definition changed; no new test,
checkpoint smoke, cost probe, comparison enrollment or invocation resulted from the correction.

## Exact accepted execution binding

Use **launch SHA `01770d8dd6bb59460667efa26e3d94677e65ab37`** for all three processes.
The complete commands and terminal conditions are in
`FSD_NATIVE_RENEWAL_CONTROL_A01_P21_ROOT_HANDOFF_20260907.md` at corrected commit
`407f11189a69561795cecabe951720a73c752e95`. A later document commit does not substitute a
new scientific source identity. Root owns actual integration/staging/admission/launch and
observation; CM `/root/fsd_cm_baseline_a01` owns technical collection, this DM the intake.

- Node/runtime: configured wsl_4070 / LAPTOP-U9TDKC8A,
  `/home/wu/.venvs/hmasd/bin/python`, declared Python3.10.21/Torch2.7.0+cu118/NumPy1.26.3;
  CPU FP32 learned path, four Torch threads and original float64 host/reward accumulation.
- Detached cwd: `/home/wu/hmasd-worktrees/fsd-native-renewal-a01-p21-01770d8dd`.
- Frozen checkpoint staging: `/home/wu/hmasd-inputs/fsd-native-renewal-a01-p21/large_d2_seed2/checkpoint_final.pt`,
  64,782,527 bytes and SHA256 `2f9f6c771d757db51991bab71b53687f34057dc4ddae5132b24d42afae683b89`.
  The original local source path is in the card and handoff. Staging verifies bytes only;
  C/H's allocated invocations perform the real independent loads.
- Output parent under cwd:
  `temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_p21_20260907/{G,C,H}`.
  The existing adjacent admission writer creates its receipt parent after measurement.
- Proposed supervisor names: `fsd_native_a01_p21_G_01770d8dd`,
  `fsd_native_a01_p21_C_01770d8dd`, `fsd_native_a01_p21_H_01770d8dd`.
  They become accepted handles only from actual supervisor receipts; none is claimed accepted here.

Root executes the three literal blocks in order, with fresh memory admission immediately
before each exact runner and the existing hard 180 s timeout around its complete process.
Root applies the handoff's terminal conformance checks and obtains CM technical acceptance
at each dependency; score sign/MEI does not change the already allocated order. Known cap or
dependent loading/state/reward/output failures stop the dependent list, with no retry,
replacement, extra diagnostics, samples, resets or cap extension. H reads completed G/C
outputs and publishes its panel inside H's cap. Missing optional time/RSS alone is reported
as resources_unmeasured when the independent timeout/terminal/post-publication facts suffice.

The fixed planned work remains 96 episodes, 38,400 scoring steps, 230,400 agent observations,
800 C/H controller batches, 400 Greedy batches, two policy constructions/loads and zero
training/optimizer updates; 180 s complete per policy and 540 s summed wall. The old cost
anchors are unchanged and do not measure the new complete path. Current new scientific
exposure is zero; actual resource admission is pending on the execution node.

## Decisions this intake produces

Options: (a) accept the corrected unchanged-source handoff and execute the named P21 route;
(b) return a concrete remaining technical defect to the same CM; (c) change the scientific
design, rerun a real-checkpoint smoke or expand the allocation. Recommend and select (a):
the inspected code, retained engineering evidence and corrected literal commands cover the
declared contract without a new unresolved prelaunch defect. Option (c) is outside P21.
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** P21 supplies the
execution allocation; this object-tier acceptance does not select another scientific question.

Owner review commands returned `[]` in both main and the direction checkout at the clean
acceptance boundary. Owner prediction remains not taken (unattended); the card's existing
low-confidence DM prediction is unchanged and unscored. This ordinary technical decision
uses card/intake/audit records, without another P1/P2 item or owner wait.

A scoped integration fact for Root: current main lacks
`pro_packets/20260907_native_renewal_convergence/archive/RESPONSE.md`, while this direction
checkout preserves the already accepted full response from `a19678fb7e0618db0c665dabe3d3cc769dc93ff5`.
Bring that accepted 188-line archive into main with the named FSD integration; do not substitute
the preserved short blocker. The immutable decision remains available and unchanged, so this
main-tree omission is not a new Pro decision or a scientific launch condition.

## Claim ceiling and unresolved empirical questions

No new native score exists in this preparation. The source action/state path and retained
checkpoint support trying this conditional measurement; E2/small-seed2 support, six competent
losses and E4's public null retain their earlier meanings. Runtime loading, full batch32 wall,
H−C and residual G−H/eligible wrong-role loss are unknown. Tuned generic headroom remains absent.
The next discriminator is the exact panel at its A/RECON measurement ceiling. Its result
does not establish learning value, training-population uncertainty, a unique mediator,
stable superiority, UAV entry or an automatic next family.
