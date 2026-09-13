# Early-exposure B01 engineering acceptance

Owner: independent MGTAP DM; L0 is the early-exposure science card.
Changes affect only the named attempt's exposure, master and binding counts.
Historical runners, shared learner/encoder/environment/reducer are unchanged.
No Engineering Scope section4 addition or numerical smoke is used.

## Checks and independent review

At 2026-09-13 23:33:45 UTC the sole executed focused suite reported4 passed in
0.46s, command wall1.0968738s and exit0; git diff --check passed. Invocation:

```
python -m pytest -q -p no:cacheprovider --basetemp temp/directions/metric_ground_transport_allocation/test/b256-binding-20260913t2333/pytest tests/experiments/candidates/metric_ground_transport_allocation/mgtap_early_exposure_b01/test_native_binding.py
```

MGTAP_TEST_SCRATCH named that root's stubs subdirectory. No scientific model,
RNG or environment was constructed. A preceding combined test-and-cleanup command
was rejected before process creation and ran zero tests. No deletion workaround
was attempted; the small executed test scratch remains retained.

Independent Astra/high Reviewer /root/mgtap_b256_reviewer inspected the card,
source/runner/tests and relevant accepted dependencies read-only. No material
engineering finding: it independently confirmed per-fit65,536 training ticks,
8,192 final ticks,128 rollouts,512 Adam calls and1,679,360 actor row uses, private
model/optimizer/RNG bindings, unchanged PPO/sampled inference, all32 final
differences, incomplete-primary withholding and partial preservation. No extra
test or numerical probe. Reviewed SHA256 prefixes: study c77780194283,
runner bf776c95cd83, tests331a5ec08b73. Static stubs are interface evidence,
not numerical validation.

## Complete native timing dependency

The Reviewer identified that in-process publication observations cannot account
for stdout/interpreter exit. [COMMAND.sh](COMMAND.sh) encloses admission and
runner with /usr/bin/time plus a900s external timeout, recording actual exit,
complete native wall and peak RSS in supervisor logs. It exports
MGTAP_CHAIN_STARTED_UNIX before the adjacent memory admission. One invocation,
no timing probe. LAUNCH.md will bind its exact published source SHA and handle.

At collection retain the raw supervisor/time receipt. Let W be outer native wall
and C the COND boundary elapsed wall. DENSE receives W-C, including paired
reduction/publication/readback/exit and outer-wrapper remainder once. Require
actual exit0, complete bindings, C<=450, W-C<=450 and W<=900 for complete native
cap compliance. Preserve overruns; in-process COMPLETE alone is insufficient.
Missing exit/wall is an acceptance gap, never zero. Opaque calls remain
non-preemptive within an arm; outer timeout is a fail-safe preserving partials.

DM accepts reviewed source and static checks, subject to actual remote source,
thread/admission/exit facts and full post-run acceptance. Convergence's independent
scientific design and interpretation review is separate, not lifecycle approval.

The same Reviewer read the command and accounting additions and confirmed they
resolve its named dependency specification with no material finding. No extra
test/probe/launch occurred. Actual runtime facts remain subject to collection.
