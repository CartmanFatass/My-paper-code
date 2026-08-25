# VSP02-B5 Full Adam-State Continuity — Preview Packet

Repository: `CartmanFatass/My-paper-code`  
Remote: `https://github.com/CartmanFatass/My-paper-code.git`  
Branch: `aggressive`  
Direction: `CAND-VSP-02`  
Candidate: `CAND-VSP-02@adversarial-revision-v9`  
Treatment: `VSP02-B5-FULL-ADAM-STATE-CONTINUITY`  
Registered full: `VSP02-B5-REGISTERED-FULL-01`  
Loop: `loop_04`  
Evidence class: `B_TOY_LIGHT`  
Arms: `ADAM_CARRY`, `ADAM_RESET`

Root will supply the final full publication commit and direct commit-pinned GitHub URL after publication; they are intentionally not invented here.

## Dated provenance and claim boundary

Pre-B4 provenance is repo-relative `docs/external-review/rounds/20260729_g31_phase_a_shadow_baseline_module_reduction_g51_formal_result_review/21_PRO_OPEN_RAW.md`, archived G52 design material around lines 718–723, 771–815, and 838–849. The mechanism form is prospective only: complete Adam RESET versus CARRY, equal boundary parameters and first gradients, carried `step`/`exp_avg`/`exp_avg_sq`, and a nonvacuity gate. G51/G52 host, update-100 boundary, thresholds, evidence, code, results, and authority do not transfer. Update `0→1` is the earliest nonvacuous-boundary specialization selected by `EARLIEST_NONVACUOUS_ADAM_BOUNDARY_AFTER_ONE_COMMON_ORACLE_SIGN_UPDATE`, without any B4 outcome, count, or trace. B4 artifacts/results are not inputs and cannot be reinterpreted.

## Proposed source/config/evidence/result paths

All paths are proposed and not yet implemented or run:

- `experiments/candidates/vsp_02/vsp02_b5_full_adam_state_continuity.py` — source.
- `scripts/run_vsp02_b5_full_adam_state_continuity.py` — runner/config binding.
- `tests/experiments/candidates/vsp_02/test_vsp02_b5_full_adam_state_continuity.py` — focused proof.
- `docs/research/candidates/vsp_02/VSP02_B5_FULL_ADAM_STATE_CONTINUITY_CODE_SCIENCE_INDEX.md` — code-science index.
- `docs/research/candidates/vsp_02/VSP02_B5_FULL_ADAM_STATE_CONTINUITY_RESULT.json` — later result.
- `docs/research/candidates/vsp_02/VSP02_B5_FULL_ADAM_STATE_CONTINUITY_PREVIEW_PACKET.md` — this packet.

## Frozen design

Question: after one identical oracle-sign self-feedback update, does carrying versus clearing complete Adam memory change exact cue-mapping acquisition on fresh paired roots?

CARRY retains exact post-update-0 complete Adam slots (`step`, `exp_avg`, `exp_avg_sq`, any configured slot). RESET replaces only those slots with canonical fresh-empty state. Post-update-0 parameters, parameter order/groups and Adam hyperparameters, recurrent/carried learner state, learner counters, RNG, schedule/tape position, and every other state remain byte-identical.

Preserve oracle-sign coefficient `c_i * detach(abs(G_i - b(h_i)))`; actor/critic/GRU/history/observations/masks/reward/return/critic target/entropy/reduction; Adam lr `0.003` and all hyperparameters; global clip `1.0`; behavior mixture `coin<0.8:sample(raw_softmax);else:sample(Uniform(RELEASE,HOLD));likelihood=0.8*raw_softmax+0.1`; batch 8 with cue balance `4/4`; immutable batches; address-indexed exogenous tape; common held-out evaluation; no direct label/cross entropy.

One fresh learner per root collects and freezes a common update-0 eight-episode batch, performs one common oracle-sign Adam step, clones complete state twice, then RESET clears only Adam state. Before either arm updates, update-1 batches are collected/frozen and rows/order/forward values/loss/raw gradients/clipped gradients/preclip norm/clip factor must be byte-identical; differing Adam transforms are then applied. Updates 2–127 may diverge as causal descendants and are not matched away or separately attributed. Both collectors freeze before either update; fixed arm order and noninterference are proven.

Activation requires pre-reset per-parameter Adam `step` exactly 1, every slot finite, and at least one nonzero moment globally. For ordered full parameter vector, `q_r = ||theta_CARRY_after_update1 - theta_RESET_after_update1||_2`; each root requires finite, strictly positive `q_r` and differing parameter hashes. No tolerance/effect threshold; failure is inactive with no rescue or boundary change.

Fresh units `VSP02-B5-U01`…`VSP02-B5-U05`; roots `22050001`…`22050005`; seed prefix `VSP02-B5-V1\0`; fresh assignment/tape namespace and streams `parameter_initialization`, `optimizer_initialization`, `training_address_tape`, `learner_stochasticity`, `minibatch_order`, `evaluation_address_tape`. No silent reuse of B1–B4/G52 roots, seeds, tapes, checkpoints, batches, models, optimizers, or results.

Activity/budget is exact: one common update 0 + 127 updates per arm per root; 128 effective steps per arm; optimizer steps 1,275; real training episodes 10,200; evaluation episodes 1,280; final checkpoints 10; environment-transition cap 57,400; CPU 30 minutes; peak 2 GiB; one pool unit; one result-bearing full; zero retry/rescue/sweep/extra root/checkpoint/threshold/boundary/post-result branch repair.

Evaluation is one 128-row panel per arm/root, cue counts 64/64. Exact success means every cue-0 row chooses HOLD, every cue-1 row chooses RELEASE, and no argmax tie. Recompute from retained rows; no checkpoint selection. Scalar `J_eval`/Kappa/gradient/mediator values are descriptive only.

Let `C` and `R` be registered-root exact-success sets. First-match branches are: (1) `B5_INVALID_OR_INACTIVE` if any identity, reset, common-ancestor, update-1 equality, `q`, oracle-firewall, immutability, noninterference, finite-value, activity, evaluation, retained-validation, or resource gate fails; (2) `B5_NEITHER_ARM_EXACT_SUCCESS_ON_PANEL` if `C=R=empty`; (3) `B5_CARRY_DIRECTION_DISCORDANCE_ONLY` if `C\R` nonempty and `R\C` empty; (4) `B5_RESET_DIRECTION_DISCORDANCE_ONLY` if `R\C` nonempty and `C\R` empty; (5) `B5_NO_EXACT_ENDPOINT_LOCALIZATION_ON_PANEL` if `C=R` nonempty; (6) `B5_BIDIRECTIONAL_PAIRED_ROOT_TAPE_DISCORDANCE` if both discordance sets are nonempty. Set partition plus gate precedence proves exhaustiveness/disjointness. Claims are exact paired-root/tape local only: no population sufficiency, necessity, superiority, or equivalence. Branch 5 is binary endpoint nonlocalization; branch 6 is qualitative finite-panel heterogeneity without identifying root/tape components; branch 2 is not Adam irrelevance. Scalar metrics cannot change a branch.

Strongest alternative/value is compound root/tape-specific acquisition variability under common self-feedback: pairing holds root/tape and self-feedback common; discordance is local causal contrast and bidirectional discordance retains heterogeneity. Plain additional self-feedback roots are a lower-information B4 extension and forbidden, not a comparator. No B5 outcome explains B4.

## External science-only review question

External GPT-5.6 Pro is asked only: (1) whether dated pre-B4 mechanism provenance plus earliest-nonvacuous specialization is prospectively valid rather than post-result selection; (2) whether complete Adam-state carry/reset is one causal axis with later trajectories as descendants; (3) whether the six branches are exhaustive, disjoint, and claim-bounded; (4) the strongest remaining alternative after paired roots/self-feedback; and (5) whether one fixed full can materially change this direction. This is not code, test, debug, runtime, or Git review; no implementation or acceptance authority is requested. Return exactly one verdict: `SOUND_AS_WRITTEN`, `REPAIR_WITHIN_COMPLETE_ADAM_AXIS`, or `REJECT_NOT_PROSPECTIVE_OR_SINGLE_AXIS`.

## Nonclaims

No reinterpretation/rescue/pooling of B4; no transfer of G52 evidence/threshold/code; no claim Adam caused B4 variation; no generic Adam/momentum/bias-correction/component attribution; no root population estimate; no generic self-feedback/on-policy/actor-critic/recurrent/MARL/transfer/sample-efficiency claim; no C/formal/promotion/retirement meaning; no sibling transfer. Any exhausted/nonseparating branch returns through Root to the same EM with no automatic successor.
