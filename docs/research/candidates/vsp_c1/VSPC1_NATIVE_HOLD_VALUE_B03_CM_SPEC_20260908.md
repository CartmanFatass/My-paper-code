# VSPC1 B03 — common value-target normalization CM handoff

1. **Deliverable.** Implement [B03 card §3](VSPC1_NATIVE_HOLD_VALUE_B03_SCIENCE_CARD_20260908.md#3-frozen-normalization-semantics)
   exactly for one prospectively selected8201 pair. Return accepted committed
   source, focused-check evidence, independent review/disposition and the exact
   staged detached command for Root. This engineering assignment includes no
   native run, timing probe, calibration or standalone runner fixture. P60 owns
   the subsequent single pair and all-outcome intake.

2. **Ownership and complete starting code.** Reuse
   `C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906`, branch
   `codex/direction-vsp_c1`, with the committed card/spec revision named by the
   Root handoff. Complete accepted B02 code is
   `0ec208899f5e8b4c190ab7bd9806be2cc30b6fda`. Complete starting source is
   `e5cc7ce67cf9dfa4ebd95324bf5c67423bc9977a`: it additionally reconciles main's
   accepted UCOPE `entropy_coef` argument (`56433ec55`) with its .01 default.
   Own the minimal opt-in normalization changes in UCOPE
   `experiments/candidates/ucope/uav_motion_prefix_b01/learner.py`
   (`collect_episode`, `update`) and VSPC1
   `experiments/candidates/vsp_c1/native_hold_value_b01/study.py`
   (`run_pair`, final state/publication). New computational code belongs in
   `experiments/candidates/vsp_c1/native_hold_value_b03/` (`__init__.py` and
   `value_normalization.py`); own new fixed
   `scripts/run_vspc1_native_hold_value_b03.py` and mirrored
   `tests/experiments/candidates/vsp_c1/native_hold_value_b03/`
   (`test_normalization.py`, `test_binding.py`). Own B03 technical acceptance/
   review records and its exact launch artifact under the existing direction temp
   surface. The critic architecture, both historical runners, UCOPE policy/
   environment, native adapter/environment, old cards/results and other directions
   are read-only. DM owns science/card/audit/owner files. You are not alone in this
   checkout; preserve others' edits and serialize overlapping writes/index work.

3. **Preserved semantics and changed boundary.** Card §§2–3 fix native value
   conversion, old-value advantage timing, cumulative FP32 moments, scale floor,
   normalized loss units, per-arm training-only updates and frozen evaluation.
   Make the change opt-in through simple direct parameters; unnormalized callers
   retain their current computation and defaults. Preserve the shared
   `entropy_coef` interface and the VSPC1 value .01; do not inherit UCOPE's
   separately selected zero-entropy experiment. No registry, adapter framework,
   global mutation, alternate PPO implementation or generic configuration layer.
   The B03 CLI accepts only `--seed 8201 --out <path>`, enables this method, and
   publishes object `VSPC1-NATIVE-HOLD-VALUE-B03` and the B03 card path. Both final
   checkpoints agree on object/configuration/source and carry their own moments.
   Keep the raw model parameter set, initialization copies, seed domains, generator
   ownership, actor/hold/reward law, compound ratios, complete rollout/Adam counts,
   final-only endpoint/H order and continuous deadlines. Label normalized value
   loss and retain actual moments/counts in existing rollout/summary/checkpoint
   records. Serialization/readback must not train or re-evaluate a policy.
   Implementation-relevant source rationale is B02 intake §3 and its exact MAPPO
   §5.1 pointer; this card, not the paper's unstated defaults, defines the method.

4. **Acceptance.** Inspect the affected source and demonstrate these concrete
   boundaries with deterministic tensor examples and stubbed run plumbing:

   - Empty initialization and population-moment merge, including constant-target
     floor. For successive batches `[1,3]`, `[5,7]`, expect `n=4,mean=4,M2=20,
     scale=sqrt(5),updates=2`; no gradients/optimizer parameters for moments.
   - Collection decodes native values using its old moments, without changing
     them. The update uses those saved native values for once-normalized detached
     advantages before fitting new moments; all four epochs reuse the same
     advantages and normalized targets. Check value-loss/native-credit units and
     gradients with fixed small tensors, not a complete native training fit.
   - One moment update per two-episode rollout, every native target row once,
     no agent or epoch multiplication; fresh independent state for each arm.
     Evaluation/H cannot mutate or fit moments. Check default unnormalized
     collector/update still use native values and native MSE.
   - Fixed8201 propagation/rejection before scientific state; unchanged historical
     runners/defaults; full stubbed schedule and card §4 private RNG domains;
     summary plus both checkpoint identities and moment round-trip; final-only
     native endpoint arithmetic remains the accepted reading. No B01/B02 label
     may leak into B03 publication, and no new native source is constructed by
     the run-plumbing tests. Use FP32-appropriate numerical tolerances, not a
     cross-platform bit-equality requirement.

   Exact original focused command (≤300s total, including needed corrections):

   ```text
   C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/native_hold_value_b03_normalization tests/experiments/candidates/vsp_c1/native_hold_value_b03 tests/experiments/candidates/vsp_c1/native_hold_value_b02/test_binding.py tests/experiments/candidates/vsp_c1/native_hold_value_b01/test_study.py::test_cli_fixed_configuration_without_running_fixture
   ```

   Reuse the unchanged B01/B02 acceptance; do not replay their synthetic runner
   fixture or training. Small tensor/gradient unit checks are engineering evidence
   and must be separated from native scientific exposure. Retain the needed
   result then clean only this invocation's verified temp scratch, per tests/AGENTS.
   Use the same available independent reviewer for the changed numerical/credit,
   RNG, checkpoint and treatment/comparator-symmetry boundary. CM dispositions
   concrete findings; no full historical reread or additional native smoke.

   Apply evidence-spec §4,§11.4,§11.8.3,§11.8.6–7,§11.9 and scope spec §§4–5.
   After code acceptance/commit/push, supply the full launch SHA, exact detached
   remote cwd, root/admission paths, requested handle and a literal LF shell
   command/script. Use the existing B02 command pattern with whole-process wall/
   peak RSS, actual-node fresh admission and continuous1800s/3600s deadlines;
   no pre-publication hard-KILL wrapper. Stage/syntax-check the shell text without
   executing its payload. Root integrates source/bindings and submits exactly it.

5. **Budget and stop.** Scope §4:none; ≤2000 new non-test source lines and
   runner≤600, with no extra framework, profiling, retry/resume or checkpoint
   orchestration. Scalar moments are existing-critic scientific state. Commit
   by explicit pathspec with attribution and `scope: none`, then push immediately.
   Original native work is one pair,286720 team steps,2048 Adam,96 final eval;
  1800s/learned arm and3600s through H/publication/exit, CPU FP32, one process/
   numerical thread on the configured remote node. This handoff stops at accepted
   source plus the ready exact Root command. The same CM later collects the sole
   accepted handle; no second normalized pair, old pair, sweep, extra H, alternate
   seed or retry follows. In-scope check/implementation repairs remain here;
   return an actual scientific-scope or budget conflict. The three CM comparison
   batches are complete at `a6dbacb36`; no fourth capture/arm is enrolled.
