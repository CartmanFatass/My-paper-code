# VSPC1 B02 — minimal fresh-pair binding handoff

1. **Deliverable.** Implement only the prospective seed/object/card binding for
   [B02 card §§2–6](VSPC1_NATIVE_HOLD_VALUE_B02_SCIENCE_CARD_20260908.md), master8102,
   preserving the complete accepted B01 learner. Return accepted committed source,
   focused-check evidence, independent review/disposition and an exact Root launch
   command/script. No native experiment is part of this engineering handoff.

2. **Ownership and starting code.** Reuse
   `C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906`, `codex/direction-vsp_c1`.
   Start from the committed B02 card revision after input-only `749f52741`;
   B01 implementation is `65c89368ab0fc7402fb0e24254447629e829a12d`.
   Own `experiments/candidates/vsp_c1/native_hold_value_b01/study.py` for the
   minimum reusable identity binding, new `scripts/run_vspc1_native_hold_value_b02.py`,
   and `tests/experiments/candidates/vsp_c1/native_hold_value_b02/test_binding.py`.
   Own B02 technical acceptance/review documents and a simple exact command artifact
   under this direction's existing temp surface. B01 runner, critic, UCOPE learner/
   policy/environment and native adapter/environment are read-only. DM owns the
   card, science, audit and owner records; serialize all shared index operations.

3. **Preserved semantics and changed boundary.** The B02 runner accepts only
   `--seed 8102 --out <path>` and uses unchanged Config values except seed8102.
   It names `VSPC1-NATIVE-HOLD-VALUE-B02` and this B02 card in the summary;
   both checkpoint object/seed/configuration/arm identities agree with the run.
   No B01/8101 label may leak into B02's scientific publication. The existing
   B01 runner remains byte-identical with real8101 and engineering9001 bindings.
   Shared-study default calls retain their original object/card/seed behavior.
   Use simple parameter passing; no registry, config layering, compatibility shim
   or global mutation. Ordinary implementation details remain with CM.
   Preserve [B01 CM spec §§2–4](VSPC1_NATIVE_HOLD_VALUE_B01_CM_SPEC_20260908.md),
   especially common initialization, private per-arm generators, complete matched
   reset identities, explicit compound PPO, final-only endpoints, H and deadline
   ownership.8102 never loads8101 checkpoints. Do not change parameters, reward,
   information, norm reporting, budgets, failure handling or primary arithmetic.

4. **Acceptance.** Review actual changed code and trustworthy focused checks of:
   fixed8102 CLI propagation/rejection before scientific state; unchanged B01 CLI;
   summary plus both checkpoint identities; b=810200000 and all card §3 seed
   domains/private matched streams; unchanged final-only counts and reading.
   Use stubs for run-level publication/seed tests, without a real8102 model or
   native environment. Reuse B01 acceptance for unchanged computation; do not
   replay its synthetic runner fixture or real training. Existing no-run B01 CLI
   check may run once alongside the new binding checks. Independent review is
   required for the affected RNG/identity/publication boundary; reuse the available
   reviewer for corrections and resolve concrete findings within this assignment.

   Exact focused command, with creator-owned scratch removed after retaining the
   needed check result under tests/AGENTS.md:

   ```text
   C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/native_hold_value_b02_binding tests/experiments/candidates/vsp_c1/native_hold_value_b02/test_binding.py tests/experiments/candidates/vsp_c1/native_hold_value_b01/test_study.py::test_cli_fixed_configuration_without_running_fixture
   ```

   Apply evidence-spec §4,§11.4,§11.8.3,§11.8.6–7,§11.9; engineering scope §4–5.
   After source acceptance/commit/push, CM binds its exact SHA, detached remote cwd,
   output/admission/handle and whole-process timing in the existing Root command
   pattern. Supply literal LF shell text; syntax-check that staged command without
   invoking its scientific payload. Root integrates accepted source and submits
   that exact command under ROOT_OPERATIONS.md's supplied-command section.

5. **Budget and stop.** Scope §4:none; ≤2000 new non-test lines, runner≤600,
   focused checks≤300s total, no new standalone synthetic fixture/profile/native
   run. Tests use the existing local scientific interpreter; clean only this
   invocation's verified temp scratch. Preserve all unrelated work and commit by
   explicit pathspec, with attribution and `scope: none`, then push immediately.
   Root alone submits the one selected remote8102 pair after fresh admission;
   card §5 fixes286720 steps/2048 Adam/96 eval and1800s/arm,3600s/pair through exit.
   No third pair, tuning, ablation, extra H or blind retry. Source defects threatening
   the selected claim return a precise gap; ordinary repairs remain with this CM.
   The three CM comparison batches ended at `a6dbacb36`; no fourth capture follows.
