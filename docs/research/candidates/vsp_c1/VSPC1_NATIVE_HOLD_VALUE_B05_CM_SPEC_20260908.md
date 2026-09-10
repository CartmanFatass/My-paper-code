# VSPC1 B05 — complete proposed engineering assignment for Root allocation

**P68 is preparation only. This is the complete future source task, not a CM
dispatch or scientific allowance.** Root receives this identical task, committed
starting source and original acceptance before assigning engineering. The three
temporary model-comparison batches are complete (`a6dbacb36`); no fourth is
enrolled. The current Root/CM operations route remains controlling.

1. **Deliverable and goal.** Implement the fixed ordinary width-133 critic and
   thin B05/8301 binding to compare it with the unchanged normalized gated critic.
   Return committed/pushed source, focused acceptance evidence and independent
   review of the changed architecture/initialization/RNG/publication boundary.
   The [card §§2–6](VSPC1_NATIVE_HOLD_VALUE_B05_SCIENCE_CARD_20260908.md#2-preserved-native-learner-and-information-path)
   supplies the complete method. This proposed engineering task ends at source
   acceptance; a native invocation requires Root's concrete later allocation.

2. **Owned paths and committed source.** Reuse
   `C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906`, branch
   `codex/direction-vsp_c1`. Complete starting source is
   `d220ef01c717c3053c2b26528c6f984302ee4aee`; the card/spec delivery is a doc-only
   descendant and contains this source. Retain required committed control-plane
   inputs and preserve any later unrelated work before editing. Own new
   `experiments/candidates/vsp_c1/native_hold_value_b05/critic.py` and a package
   marker if needed, `scripts/run_vspc1_native_hold_value_b05.py`, mirrored
   `tests/experiments/candidates/vsp_c1/native_hold_value_b05/`, and B05 technical
   acceptance/review records. You may minimally extend the existing
   `native_hold_value_b01/critic.py::models` and `study.py::run_pair` /
   `checkpoint_identity` for this single comparator and its publication fields.
   Use a direct optional second-MLP-width argument defaulting to 128, with B05
   passing 133 and its explicit extra-initialization seed; no general model
   registry, factory or configuration layer. Ordinary helper names/placement
   within these owned paths remain CM choices.

   `ucope/uav_motion_prefix_b01/policy.py::Critic,templates,arm_copy`, its learner,
   environment and imported study helpers, all native environment code,
   `native_hold_value_b03/value_normalization.py`, and historical runners are
   read-only. Minimal reuse of existing test helpers is allowed, preserving their
   original cases. The default width-128 path, old configuration/checkpoint fields
   and historical scientific semantics must remain unchanged; new architecture
   fields are attached to the B05 path. A necessary change beyond these surfaces
   returns the precise dependency to DM. DM owns card/intake/DIRECTION/audit/owner
   records. You are not alone in the checkout: preserve others' edits and serialize
   overlapping editing/index operations.

3. **Semantics to preserve and exact change.** Implement card §3's ordinary
   `136→128→133→1` tanh MLP with all 34,827 critic parameters trainable. Copy its
   common subnetwork exactly, initialize appended `5×128` rows then five biases
   from the private CPU FP32 `b+12` uniform generator, and zero only the five new
   output weights. GATED and common actor/duration initialization stay intact.
   No global/action/reset RNG consumption changes. Keep independent arm objects,
   optimizers, generators and moment state. Do not freeze the appended hidden
   units: their first-step zero incoming gradients are the declared initialization.

   The thin runner accepts only `--seed 8301 --out <path>` and rejects other keys
   or fixture/width flags before model/environment state. It uses the existing
   `Config(seed=8301)`, `normalize_value=True`, fixed width 133, object
   `VSPC1-NATIVE-HOLD-VALUE-B05` and this card path. Card §4 supplies all RNG keys;
   §§2,5–6 supply native method, sampling, moments, counts and continuous deadlines.
   Retain internal arm/contrast keys. Every B05 summary and final checkpoint must
   include its own object/master, the per-arm critic architecture and actual
   critic parameter count; its published `MLP-V` is explicitly width 133. Readback
   checks those B05 identity fields through existing publication logic. Old
   width-128 artifacts cannot be presented as B05 results. No source state or
   output from earlier scientific runs is reused.

4. **Original acceptance.** Use focused tensor/gradient checks for the changed
   critic plus pure-data/stubbed checks for the scientific pipeline. Reuse
   accepted normalization/PPO/native/H/deadline checks on unchanged paths;
   do not run real native constructors, a learner fixture, timing/calibration,
   or a historical suite without a changed dependency.

   - Check architecture, all 136 inputs, ordinary full connectivity, 34,827 vs
     34,817 trainable critic parameters, exact common copied tensors, draw order
     and zero appended outputs. On fixed bounded tensors, compare its initial
     values with the common ordinary critic at FP32 `rtol=1e-5, atol=1e-6`;
     structural equality of copied tensors is exact. This focused regression
     tolerance is not a cross-platform scientific criterion.
   - Check the global RNG state and matched common actor/critic initialization
     survive wider construction, the extra generator is distinct, and action/reset
     domains match card §4 without shared mutable arm objects. A deterministic
     tensor backward/update check demonstrates new output weights can receive
     gradients and appended incoming weights can subsequently learn; no native
     episode or PPO fit is needed for that numerical boundary.
   - Check valid/invalid CLI binding, width/normalization propagation, the unchanged
     default width-128 route, B05 summary/checkpoint architecture/count identity
     and readback. Reuse the full stubbed pair schedule to cover 286,720 steps /
     2,048 Adam / 96 evaluations, H order, final moments, and unchanged primary
     branch keys including thresholds/incomplete inputs. Stub counts are engineering
     evidence and never scientific exposure or return.

   Original focused command, at the configured local interpreter (≤300s total):

   ```text
   C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/native_hold_value_b05 tests/experiments/candidates/vsp_c1/native_hold_value_b05
   ```

   If an existing helper/caller changes, include its directly affected existing
   cases in the same total budget; reuse broader prior acceptance. Retain an
   independent reviewer for the changed architecture, initialization/RNG,
   normalized learner integration and publication meaning. Reuse the same
   available reviewer and CM for corrections. Report the actual diff, check
   wall, resolved findings and any remaining numerical/semantic gap. Applicable
   rules are evidence spec §§4,5.2,11.4,11.7,11.8.1–3,11.8.6–8 and engineering
   scope spec §§4–5. Test success is source acceptance, not mechanism evidence.

5. **Budget and stop.** Scope §4:none; new non-test source≤2000 lines, runner≤600,
   focused checks≤300s total. Commit by explicit pathspec with attribution and
   `scope: none`, and push immediately. Ordinary in-scope check/code repairs
   continue; a scope/budget/meaning conflict returns the concrete gap. No generic
   source manifest, runtime validator, resume/retry orchestration or new telemetry.
   This proposed engineering deliverable includes zero scientific invocations,
   remote staging/admission or accepted handles, and stops at accepted source.
   If subsequently allocated, the single B05 pair uses card §6's configured
   remote-first CPU FP32/one-process/one-thread route, 1800s per complete arm /
   3600s through H/publication/exit, and all outcomes. Current operations assign
   staging, bounded launch, observation, collection and technical acceptance as
   one useful CM batch; no per-command Root relay is added. That future batch
   and any extra seed, tuning, evaluation or retry are outside P68 preparation.
