# VSPC1 B04 — independent normalized pair CM handoff

1. **Deliverable.** Implement the minimal prospective master8202/object/card
   binding for P66's one independent normalized GATED-V/full-MLP-V/H pair.
   Return accepted committed source, changed-boundary checks and independent
   review, actual exact-source remote staging and a literal ready command for
   Root. This engineering delivery makes no native invocation, smoke, timing
   or calibration call. The [card §§2–5](VSPC1_NATIVE_HOLD_VALUE_B04_SCIENCE_CARD_20260908.md#2-preserved-method-and-information-path)
   fixes science; CM does not rewrite it.

2. **Owned paths and complete source.** Reuse
   `C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906`,
   `codex/direction-vsp_c1`, at the committed card/spec revision supplied in the
   handoff. Accepted normalized source is
   `7a8ed3aa5d25ded71164aa338749d09318124dcf`, already contained in clean
   preparation HEAD `7df73a14e7d78bfe762bbf0c42630cfc50af2dd9`.
   Own new `scripts/run_vspc1_native_hold_value_b04.py`, mirrored
   `tests/experiments/candidates/vsp_c1/native_hold_value_b04/`, and B04 technical
   acceptance/review plus exact launch artifacts in the existing temp direction
   surface. You may minimally reuse/factor B03 binding-test helpers if that avoids
   duplication, preserving the existing8201 tests and citing the affected checks.
   The existing B03 runner, `native_hold_value_b01/study.py`,
   `native_hold_value_b03/value_normalization.py`, critic, UCOPE learner/policy/
   environment and imported UCOPE study helpers are read-only accepted code;
   no algorithm change is requested. A necessary production change beyond the
   thin binding returns its concrete need to DM first. DM owns card/intake/
   DIRECTION/audit/owner records. You are not alone in this checkout: preserve
   others' edits and serialize overlapping writes/index operations.

3. **Preserved semantics.** Reuse the B03 thin-runner path with
   `Config(seed=8202)`, `normalize_value=True`, object
   `VSPC1-NATIVE-HOLD-VALUE-B04` and card
   `docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_B04_SCIENCE_CARD_20260908.md`.
   Accept only `--seed 8202 --out <path>` and reject other seeds/fixture flags
   before scientific state. Card §§2–4 inherit the exact normalization, .01
   entropy, initialization/actor/full-MLP/gate, PPO/native credit, moment update,
   hold/reward/RNG and sampled endpoint semantics. Both final checkpoints and
   every publication identity belong to B04/8202; no B03 label/output is reused.
   Use the fresh domains in card §3 with private arm generators and no prior
   weights, optimizer or moment state. Complete counts, continuous deadlines,
   H order and publication/readback remain as accepted. No new generic CLI,
   registry, framework, resume/checkpoint orchestration or configuration layer.

4. **Acceptance.** Reuse the accepted B03 normalization/learner review and
   arithmetic checks. Inspect the changed caller and demonstrate valid8202
   propagation, wrong-key/fixture rejection before scientific state, unchanged
   method/configuration, independent paired RNG-domain mapping and B04/8202
   summary/checkpoint publication identity. Use focused deterministic pure-data
   or stubbed plumbing checks on these changed boundaries; existing full-stub
   helpers may be reused. No real model/environment constructor, native fit,
   standalone training fixture or new evaluation is needed. Do not rerun the
   full normalization or historical suite without a changed boundary or finding.

   Original focused command (≤300s total, including needed corrections):

   ```text
   C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/native_hold_value_b04_binding tests/experiments/candidates/vsp_c1/native_hold_value_b04
   ```

   If an existing test helper is changed, additionally run its directly affected
   existing cases within the same total cap. Reuse the same available independent
   reviewer for the changed key/object/RNG/publication and launch-staging boundary.
   CM dispositions findings and returns actual diff/check evidence. Apply evidence
   spec §§4,11.4,11.8.3,11.8.6–7,11.9 and engineering scope spec §§4–5.

   After source commit and immediate push, use the existing remote Git/bundle
   route to stage a clean detached worktree at that exact full SHA. **Directly
   verify the cwd, HEAD and required source files before declaring the command
   ready**; preserve B03's failed and corrected handles. Supply a new B04/8202
   handle, absolute output/admission paths and a literal LF shell payload with
   fresh actual-node `admit-memory` before scientific state. Reuse the corrected
   B03 whole-process wall/peak-RSS command pattern, original continuous caps and
   full terminal publication/exit accounting. Syntax/readback of staged script
   is allowed; do not execute its payload or admission. Root integrates, submits
   and observes the sole scientific invocation after the DM binding.

5. **Budget and stop.** Scope §4:none; new non-test source≤2000 lines, runner≤600,
   focused checks≤300s total. Commit explicit paths with attribution and
   `scope: none`, pushing immediately. P66's original one-pair work is286720
   native team steps/2048 Adam/96 eval, plus its512 existing moment merges;
   CPU FP32, one process/numerical thread on `hmasd-wsl-node`,1800s per learned
   arm and3600s through H/publication/exit. This first delivery stops at accepted
   source, actual staging and the exact Root command. The same CM later collects
   the one accepted handle. No third normalized pair, tuning, extra H/evaluation,
   alternate seed or scientific retry is allocated. Ordinary in-scope check
   repairs stay here; return an actual scope/budget conflict. The three CM
   comparison batches are complete at `a6dbacb36`; no fourth capture is enrolled.
