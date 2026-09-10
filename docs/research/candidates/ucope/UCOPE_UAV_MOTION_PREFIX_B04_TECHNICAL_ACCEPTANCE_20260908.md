# UCOPE B04 — conditional duration implementation and technical acceptance

**Accepted source: `7693b7af6b7d89cdaa028659d606a37dee9eb68e`.** The selected P61 B04 head, density and identity changes pass the focused suite and independent review. This task executed **zero scientific invocations**. DM owns accepted-source binding and Root owns the selected subsequent7201 launch.

## Delivered surface and preserved behavior

Contract: [B04 code specification §§2–6](UCOPE_UAV_MOTION_PREFIX_B04_CODE_SPEC_20260908.md), [card §§2–6](UCOPE_UAV_MOTION_PREFIX_B04_SCIENCE_CARD_20260908.md) and [P61 intake](UCOPE_POST_B03_CONVERGENCE_INTAKE_20260908.md). Full task/source/checks reached Root before coding; the three CM comparison batches were complete and no fourth was enrolled.

CM reused `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`, branch `codex/ucope`, starting clean at `c54d8d9403d8613550b6b050f3df465d1b0e1424`. Accepted B03 research source was unchanged at dispatch. No unrelated edits or new authoring branch occurred. CM owned the following six code/test paths through explicit-path commit and immediate push:

- `policy.py`: T-only Linear67→32, tanh, Linear32→2 head, private CPU default-generator seed b+12 under a restoring RNG context, ordinary initialization followed by final-layer-only zeroing. Sample velocity first; duration sees its owner's actual detached tanh latent. During recomputation, select true duration-mask rows before head forward, skip an empty mask and scatter density/entropy back to the original shape. Preserve the velocity Jacobian. Existing exposure gains duration_hidden/duration_final groups only for B04; initially zero groups have null relative displacement and retain absolute movement.
- `study.py`: b04/7201, agent_compound and entropy0; derived `treatment_duration_mode=sampled_command` and `treatment_duration_head_seed=b+12` enter effective Config and both checkpoints. Summary identifies the real object/card/section5. Arm metadata says T owns the head and G has duration mode none/seed null. Synthetic mode retains its fixture identity. Direct single-pair aggregate refusal is explicit.
- `scripts/run_ucope_uav_motion_prefix_b01.py`: named b04 route, wrong real-master refusal and aggregate refusal before input/workload access.
- `test_conditional_duration.py`, `test_pair_plumbing.py`, `test_motion_prefix.py`: changed-boundary coverage and existing fixtures redirected to pytest's supplied base temp directory so this invocation can remove its own scratch.

Learner, environment/adapter/native source, observations, actor/common critic architecture, complete native RTG, Adam, recurrent chunks, old-logp/advantage detachment, held ownership, per-agent clipping/reduction, stochastic final primary and publication logic were not changed. Historical independent heads and p21/p24/b02/b03 defaults remain. Published historical exposure calculations retain their old bytes, including their old epsilon denominator; B04's zero-initial group is separately truthful.

Engineering scope §4: **none**, as selected in card/spec§6. Non-test diff **+68/−23 lines**; runner **54 lines**. No framework, compatibility layer, telemetry service, profiler, registry, recovery system or new source-level execution guard was added. Metadata and test scratch handling serve the explicit contract. Dependency versions were not changed.

## Exact-source checks and corrections

Source/tests were committed and pushed before remote execution. Commit tree: `9b3221e69f3251ec030cfb0fb05b0d2a85126fa9`. Configured `hmasd-wsl-node` used detached checkout `/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b04-p61-check-20260908`, interpreter `/home/wu/.venvs/hmasd/bin/python`, CPU FP32 and the existing one-thread test setup. Existing remote Git objects plus347 missing committed objects were staged using authenticated SCP; the415747-byte pack digest was checked before indexing. HEAD and checkout diff were verified. No uncommitted source was staged.

Preparation first encountered local cp1252 decoding of Git path output, corrected by `--no-object-names`, then Windows text-pipe CRLF rejected by Bash, corrected by sending the existing LF script as bytes. These were staging failures, before any accepted test process. Raw staging facts and scripts are retained in [staging inputs](../../../../temp/directions/ucope/test/b04_p61_check_20260908/staging-inputs.json) and adjacent `stage*.txt`/`stage.sh`. Source-carrier pack files were removed locally and remotely after successful staging; their digest remains in the receipt.

The selected test command was unchanged:

```text
/home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --basetemp temp/directions/ucope/test/uav-motion-prefix-b04-p61 tests/experiments/candidates/ucope/uav_motion_prefix_b01
```

| Supervisor suffix after `ucope-uav-motion-prefix-b04-p61-check-20260908` | Observed terminal fact | Measured test-process wall |
| --- | --- | --- |
| no suffix |40 passed,31 setup errors, exit1: fresh checkout lacked the parent of pytest's base temp directory |2.90s (pytest2.30s) |
| `-scratch-parent02` |exit1 before pytest: launcher suffix replacement accidentally changed cwd to an absent checkout; no tests started |no test invocation |
| `-scratch-parent03` |correct original cwd plus parent mkdir; **71 passed**, exit0 |**2.14s** (pytest1.75s) |

The source did not change between these attempts. Concrete command/fixture setup corrections justified repeating the affected suite. **Cumulative measured directory invocation wall5.04s**, within300s. The final timeout was297s to retain the cumulative allowance after the first2.90s. The mandated `-p no:cacheprovider` produced one harmless existing `cache_dir` configuration warning. No separate smoke, warm-up, profile, benchmark, fixture runner or UAV execution occurred.

The final [raw log](../../../../temp/directions/ucope/test/b04_p61_check_20260908/supervisor-parent03/task.log), [runner](../../../../temp/directions/ucope/test/b04_p61_check_20260908/supervisor-parent03/runner.sh) and [status](../../../../temp/directions/ucope/test/b04_p61_check_20260908/suite-parent03-status.json) show **finished, exit0, PID3011231, tmux inactive**, start `2026-09-09T06:59:01+08:00`, end `2026-09-09T06:59:03+08:00`, peak RSS **528820KiB**. Earlier logs remain under `supervisor-first/` and `supervisor-final/` (the latter is the failed suffix02 receipt, not final acceptance). Both actual pytest runners removed their owned base temp after retaining stdout; absence was independently checked after collection. Aggregate CPU was not measured.

## Acceptance evidence and independent review

Actual tensor tests establish the67→32→2 dimensions,2242 head parameters/T68553/G66311 totals, exact uniform initial probabilities, deterministic private b+12 hidden initialization, unchanged common T/G weights and caller/action RNG, and meaningful null/absolute exposure for the zero-initial final layer. A deliberately nonzero head depends on the actual owned command; sampled and recomputed density match a direct compound formula. Perturbed current means/head biases still condition on stored latents. Head and recurrent-feature gradients are nonzero, while the stored-action gradient equals the velocity-only derivative exactly: no conditioning-action gradient leaks through.

Actual synthetic collector/update tests observe five single-owner sampling rows plus five behavior-density rows at each opening, zero later duration forwards, correct mixed t1/t4 holds, original logp shape and four real Adam steps. Each update forwards exactly ten opening rows for two episodes and retains their stored command conditions. Existing clipping, entropy-objective, native-primary/information mapping, RTG/chunk, cap/partial-output and checkpoint-before-evaluation tests remain included. Fake-workload CLI/Config/run_pair checks cover actual master/reset/stream expressions, both-arm grouping/entropy, T-only head seed/mode, saved Config identity, historical routes, wrong-master and aggregate refusal without UAV calls.

The existing configured independent reviewer `rv_ah_ucope_b02_credit` reviewed the complete committed diff and contract, then independently read the raw failures and passing suffix03 receipt without tests, edits or index operations. Final return: **no material findings or unresolved acceptance gaps; no repairs requested**. It verified actual detached owned-command conditioning, opening-mask-before-forward, CPU RNG isolation, retained velocity/recurrent/native credit, truthful metadata/exposure, scope and the5.04s cumulative test bound. This paragraph records that final independent technical review.

These observations establish implementation conformance, not UAV performance, B04 full-run timing or population inference. Historical B02 smoke80.578s/60s breach and previous scientific command failures retain their original meaning.

## Cost/publication boundary and next owner

**Per-arm cost projection:** reuse card§6 and its computed facts. Complete logical invocation remains initialization +131072 training environment/actor steps +1024 Adam calls +8192 final steps +publication per learned arm; G additionally carries8192 H steps, T the selected15680 conditional-head forward rows across the pair route. Prior B03 T143.6449222s/G139.3128413s/whole283.51s are same-loop references, not measured B04 timing. Added head seconds and aggregate CPU are unknown. Original1800s/arm and3600s complete pair caps remain; no timing pilot or cap growth was selected.

**Post-learner path coverage:** unchanged checkpoint/summary/primary/publication code is exercised through existing focused checks, with B04 saved effective Config and T/G head metadata traced through fake workloads. No new standalone smoke or historical replay obligation follows. Real7201 exposure, fitted-checkpoint tensors, native counts and primary remain for terminal collection.

DM next binds this accepted source and hands off to Root's existing P61 route: one fresh admitted remote7201 T/G/H invocation,286720 team steps,2048 Adam calls,96 final episodes and full publication/exit caps. Root owns staging/launch/observation and integration; CM retains terminal collection/technical acceptance; DM interprets every outcome. No retry, second pair, extra H completion/evaluation or tuning is implied. The later command handoff below gives this same remote checkout the imminent7201 execution dependency. Root owns removal only after7201 reaches terminal state and its artifacts, CM collection and DM intake are archived. The shared local direction checkout remains in use by DM/CM.


## Literal7201 command handoff — completion of the existing B04 task

DM accepted the source/review and requested this mechanical command completion under main `ROOT_OPERATIONS.md`, “Execute the supplied launch command”. This is excluded from new coding enrollment. Research source remains **7693b7af6b7d89cdaa028659d606a37dee9eb68e**; no code, test, scientific allocation or accepted-source SHA changed. CM ran no admission or science and no test rerun.

Read-only reconciliation confirmed the existing staged checkout is clean at that exact source, the proposed supervisor reports `not_found`, and the proposed scientific output is absent. This is an observed preparation fact, not future admission or permission to duplicate an accepted handle. Root uses the same checkout with no additional source transfer, worktree or test; reconcile any intervening acceptance before submitting once.

- Node: `hmasd-wsl-node` (configured `wsl_4070`); CPU FP32, runner's fixed one Torch thread.
- Exact cwd: `/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b04-p61-check-20260908`.
- Supervisor: `ucope-uav-motion-prefix-b04-7201-p61-20260908`.
- Output relative to that cwd: `temp/directions/ucope/exp/uav-motion-prefix-b04-7201-p61-20260908`.
- Interpreter: `/home/wu/.venvs/hmasd/bin/python`; pair `b04`, seed `7201`, source defaults1800s/arm and3600s pair.
- Whole detached command uses existing `/usr/bin/time` and3600s external timeout, including fresh admission, initialization, learner, evaluation, publication and exit.

Root executes this **existing local file**, without rebuilding or replacing strings:

```powershell
& 'C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906/temp/directions/ucope/launch/b04_7201_p61_20260908/submit.ps1'
```

Its exact332 UTF-8/LF bytes (including final newline), SHA-256 **44da62269da8e8d10683189284db1884d6260daaff8943746de24c09d01c8f2d**, are:

```powershell
& ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node "/usr/local/bin/agent-task run ucope-uav-motion-prefix-b04-7201-p61-20260908 '/usr/bin/time -f whole_wall_seconds=%e,peak_rss_kib=%M /usr/bin/timeout --signal=KILL 3600s /bin/bash --noprofile --norc /home/wu/hmasd-inputs/ucope-b04-7201-p61-20260908.sh'"
exit $LASTEXITCODE
```

The payload wrapper already staged at **`/home/wu/hmasd-inputs/ucope-b04-7201-p61-20260908.sh`** is the local `temp/directions/ucope/launch/b04_7201_p61_20260908/wrapper.sh` in the authoring checkout. Its exact729 UTF-8/LF bytes (including final newline), SHA-256 **262ce2d711e1ded155abdf375aeb0e5a763f745e385772cfa2234e9506db796f**, are:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b04-p61-check-20260908
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/.agent-tasks/ucope-uav-motion-prefix-b04-7201-p61-20260908/resource_admission.json
mkdir -p temp/directions/ucope/exp/uav-motion-prefix-b04-7201-p61-20260908
cp /home/wu/.agent-tasks/ucope-uav-motion-prefix-b04-7201-p61-20260908/resource_admission.json temp/directions/ucope/exp/uav-motion-prefix-b04-7201-p61-20260908/resource_admission.json
exec /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_uav_motion_prefix_b01.py --pair b04 --seed 7201 --out temp/directions/ucope/exp/uav-motion-prefix-b04-7201-p61-20260908
```

The existing `admit-memory` implementation captures fresh actual-node physical/effective memory, requires both≥4GiB and exits6 on failed admission. `set -e` therefore stops before scientific output/model creation on failure. Its first receipt lives inside the accepted supervisor directory; only successful admission creates the scientific output directory and copies that same receipt there. Root preserves the supervisor receipt even if admission fails. The learner retains original counts/caps and the external timeout bounds the full logical chain; there is no retry in either file.

**Nonexecuting check evidence:** the actual staged LF wrapper passed `/bin/bash -n /home/wu/hmasd-inputs/ucope-b04-7201-p61-20260908.sh`, exit0, and remote `sha256sum` matched the local wrapper digest above. PowerShell `Language.Parser.ParseFile` accepted the actual local `submit.ps1` with zero syntax errors; it was not executed. Raw Bash check and byte facts are retained under [command facts](../../../../temp/directions/ucope/launch/b04_7201_p61_20260908/command-facts.json) and adjacent `wrapper-syntax.stdout.txt`. Subsequent read-only reconciliation again found the7201 handle/output absent and exact staged source unchanged. No nested payload was rebuilt from a prior scientific runner, and no post-check string replacement occurred.

Cleanup recommendation is amended: this staged checkout now has the actual imminent7201 dependency. Root removes it and the staged command wrapper **after terminal7201 artifacts, CM collection and DM intake are archived**, while preserving the accepted output/receipts. Earlier test/setup/launcher failure receipts remain unchanged. This command handoff is ready for DM source binding and Root's single authorized submission; it is not an admission or launch receipt.
