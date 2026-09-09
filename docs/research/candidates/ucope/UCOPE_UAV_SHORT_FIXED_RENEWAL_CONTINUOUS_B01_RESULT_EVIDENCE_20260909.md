# UCOPE continuous short fixed renewal B01 — engineering evidence

## 1. Implementation boundary (2026-09-09)

The new driver conforms to the frozen [card §§2–6](UCOPE_UAV_SHORT_FIXED_RENEWAL_CONTINUOUS_B01_SCIENCE_CARD_20260909.md#2-preserved-learners-and-native-comparison) and [assignment §3](UCOPE_UAV_SHORT_FIXED_RENEWAL_CONTINUOUS_B01_8601_INTAKE_20260909.md#3-five-item-cm-assignment).
This is implementation evidence only: **zero scientific invocations, zero native calls, zero master8601 RNG/model generation, no scientific output root**. Root accepted the frozen card; source acceptance/integration remains the next boundary before the one allocated invocation.

Final source **8a2e20630c6d68f7faed1c54a39ffc792b922fc6**, pushed to `codex/ucope`. Authoring checkout `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`, starting clean at `66ddec1278e0e170644ee14b155fbd0292b04e57`.
Four new paths: `experiments/candidates/ucope/uav_short_fixed_renewal_continuous_b01/{__init__,study}.py`, `scripts/run_ucope_uav_short_fixed_renewal_continuous_b01.py`, and `tests/experiments/candidates/ucope/uav_short_fixed_renewal_continuous_b01/test_continuous.py`.
452 added lines (study215, CLI33, init1, tests203);249 non-test lines.
**Engineering scope §4 additions: none**, per card§6. No shared runtime edits. The four shared `uav_motion_prefix_b01/{study,policy,learner,environment}.py` working blobs equal accepted `52bf50a089d3389d9fada0b531e4f4e56e83f9b8`.

Each F/G arm owns one actor, critic, Adam and two private training generators through the continuous fit. Updated-rollout boundaries invoke evaluation with fresh separate generators, then the next training episode resets the same arm environment. Raw targets/None moments, compound clipping, frozen full F head with random hidden layer/zero final layer, physical{1,2} renewal and native reward are unchanged. Episode records carry checkpoint plus episode identity. One H vector is reused across all three panels. Final2048 F−G is the primary; full completion additionally requires every scheduled panel, H and both fits. Final trained policy files are saved before final evaluation, preserving the completed fit if subsequent evaluation fails. No intermediate recovery files, RNG guard, extra environment or scientific diagnostic was added.

## 2. Focused acceptance

Evidence directory (ignored local artifacts): `temp/directions/ucope/analysis/continuous-8601-implementation-20260909/`. Files: `focused.log`, `final-failure.log`, `fixture-summary.json`, `source-identity.json`, `cleanup-blocker.txt`.

Interpreter: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`. Commands use `-m pytest -q -p no:cacheprovider --basetemp <own scratch>`.
First command selects the new test directory: **11 passed in4.00s**, outer **5.1503854s**. Added failure coverage selects `test_continuous.py::test_final_evaluation_failure_preserves_fit_and_primary`: **2 passed in3.84s**, outer **4.8885118s**. Total13 passing cases,7.84s pytest,10.0388972s outer, within300s support budget. Existing cache_dir configuration warning is unrelated; no unchanged suite or native smoke was rerun.

The real synthetic9001 path covers both continuous fits, all three panels and H:208 synthetic steps,24 Adam calls,26 explicit resets,two constructors/resets,zero native calls. Checks establish:

- Actor/critic/optimizer identity and cumulative Adam steps across checkpoints.
- Persistent private training generators and evaluation nonmutation of their states, optimizer state, model state_dict (parameters/buffers), and global RNG.
- Exact reset/action-seed laws and disjoint real seed domains using arithmetic only;8601 CLI is tested against a stub, never a scientific model.
- Frozen2242 F head,66311 trainable parameters per arm, final checkpoint equality, raw None targets, sampled execution, literal d2/d4, expected call ordering.
- Native-return formula inherited through the synthetic collector, three separately labelled panels, shared H, paired vectors/SE/sign counts/MEI.
- Early-panel failure never supplies a final primary; failed final F evaluation retains completed fit/checkpoint; H failure retains the complete final F/G primary with limits; on-disk summary and curve match returned output.

Independent reviewer `rv_ah_ucope_b02_credit` returned **no unresolved material finding** bound to source `a7f1a8bf4acbad1f666997a12b8f624773ee1672`. Two material findings were corrected before that commit: trainable reporting filters frozen parameters; full-fit state/checkpoint precede final evaluation. Reviewer inspected accepted reset/cache behavior and final test receipts, without extra runtime execution. Its return confirms continuous optimizer/model/training-RNG lifetimes, separate evaluation streams, frozen F head, final primary and shared H match the card. These checks establish implementation conformance, not native affordability, benefit, comparator competence or scientific validity.

## 3. Cost and publication coverage before any launch

**Per-arm cost projection:** reuse card§4's P84 complete-path reference and prospective facts; no new probe. Native-work scaling F674.7740192240556s,G/H533.3443125521298s,sum1208.1183317761854s. Largest-component reference cost envelope F983.2421422979096s,G/H800.0164688281948s. These remain forecasts; extra curve publication and trajectory costs are unmeasured. Original1800s per arm/3600s whole limits remain. Sequential F→G study critical path is the whole invocation, distinct from summed measured arm walls and unmeasured aggregate CPU. One invocation contains1163264 native steps,8192 Adam calls,4096 training episodes,448 evaluation episodes,4544 explicit resets plus2 constructor resets. No exposure/count/cap has been reduced.

**Post-learner path coverage:** synthetic fixture exercised three labelled F/G panels,H-once pairing,final checkpoint and JSONL/summary publication; focused partial cases cover final F/H failures. It does not measure the remote native curve runtime or produce a scientific primary. Exact launch argv/node,admission,detached handle and Monitor handover belong in a later execution section after Root integrates/accepts source.

## 4. Remaining technical boundary

Test scratch was created only at `temp/directions/ucope/test/continuous-8601-implementation-20260909` and `temp/directions/ucope/test/continuous-8601-final-failure-20260909` in the named checkout. After preserving logs/fixture summary, both resolved absolute targets were checked before exact `Remove-Item -LiteralPath ... -Recurse -Force`. Automatic approval review rejected that operation before execution: `exec_command CreateProcess: rejected: blocked by policy`. Both completed scratch directories remain; this CM retains cleanup ownership pending a permitted external-state change. No bypass, repeated request or deletion of other scratch/evidence occurred. Prior reported cleanup gaps remain untouched.

DM accepts this technical result; Root owns source integration and returns the original CM for the already allocated launch. At that time CM reads the live main Monitor endpoint, dispatches MONITOR_ADD after accepted launch, returns pending adoption/collection and stops routine polling; Root confirms adoption and resumes original CM for terminal collection. No launch is claimed in this implementation record.

## 5. DM publication-pointer correction

DM requested one literal metadata correction after acceptance inspection: source commit `8a2e20630c6d68f7faed1c54a39ffc792b922fc6` changes only `card_section=6` to `card_section=(6 if config.fixture else 5)`. Native output now points to the frozen primary/rule in card§5; fixture output points to engineering acceptance in§6. The exact source diff is one line; reviewed/tested computation, loops, RNG, counts and budgets remain identical to `a7f1a8bf4acbad1f666997a12b8f624773ee1672`. The independent review and13 passing cases above carry forward on that basis. Focused diff inspection and `git diff --check` passed; no suite repetition, native work or blocked-cleanup retry occurred. Source was committed and pushed immediately.
