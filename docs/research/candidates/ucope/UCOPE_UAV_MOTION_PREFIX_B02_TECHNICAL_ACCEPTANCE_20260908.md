# UCOPE B02 implementation and independent credit review

P47 commissioned the full [code specification §§1–8](UCOPE_UAV_MOTION_PREFIX_B02_CODE_SPEC_20260908.md), superseding preparation-only wording. Implementation and functional checks are complete. **Unconditional technical acceptance is withheld: the one synthetic CLI fixture took 80.578 seconds against its 60-second bound.** No scientific pair or repeat fixture was launched.

## Delivered source and boundaries

Authoring checkout: `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`, branch `codex/ucope`. Starting HEAD `1d46ddc2b142a2c2b98922a8f46e2d2609bda859` was clean. Its package/runner/test surface has no diff against bound source `b5607f46fea91379582af8bf87e60b61bc4a269b`. CM retained sole editing/index ownership for this slice.

- `policy.py`: the existing density calculation explicitly retains the agent axis for B02; each entry sums its three velocity coordinates and its own opening duration. Historical joint reduction order and entropy remain unchanged.
- `learner.py`: B02 stores detached old densities `[H,5]`, stacks `[E,H,5]`, checks all finite entries and reconstructs differentiable new densities. It masks inactive actor terms, sums agents and then averages all primitive rows. Old values, normalized advantages, recurrent chunks, targets and optimizer remain the existing path.
- `study.py` and the existing runner: `--pair b02`, masters 7001/7002, B02 card/object and `agent_compound` identity reach collection/update, checkpoint configuration, summaries and read-only aggregation. The B02 engineering route keeps fixture identity/master 9001. Aggregation rejects mismatched real objectives and synthetic mixtures.
- Added `test_agent_clipping.py`; extended `test_pair_plumbing.py`. Existing `test_motion_prefix.py`, `environment.py` and all unowned source are unchanged.

State ownership remains episode-local holds/history, separate T/G parameters/optimizers/generators, and collected immutable samples/old densities used for four epochs. Shapes remain CPU FP32, actor `[E,H,5,108]`, critic `[E,H,136]`, scalar primitive rewards/values/advantages `[E,H]`; only B02 log-density storage retains five owners. No sampling, action, reward, information, initialization or gradient-boundary change was added.

Engineering scope §4: **none** per code spec §7/card §7. Non-test source diff is +60/−21 lines; runner is 52 lines. No dependency installation, profiling, new framework, resource machinery or scientific invocation occurred.

## Focused checks and single fixture

All commands below ran from the authoring checkout with the existing local CPU scientific interpreter. These are short synthetic engineering checks permitted by code spec §7; no remote source staging or real environment constructor/reset/step was used.

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q tests/experiments/candidates/ucope/uav_motion_prefix_b01
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_ucope_uav_motion_prefix_b01.py --pair b02 --engineering-fixture --seed 9001 --out temp/directions/ucope/test/uav_motion_prefix_b02_fixture
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -c "import json,pathlib; p=pathlib.Path('temp/directions/ucope/test/uav_motion_prefix_b02_fixture'); s=json.loads((p/'summary.json').read_text()); c=s['counts']; assert s['mode']=='ENGINEERING_FIXTURE' and s['scientific_uav_calls']==0; assert s['object']=='UCOPE-UAV-MOTION-PREFIX-B02' and s['ratio_grouping']=='agent_compound'; assert s['configuration']['pair']=='b02' and s['configuration']['ratio_grouping']=='agent_compound'; assert (c['train_team_steps'],c['eval_team_steps'],c['team_steps'],c['optimizer_steps'])==(32,48,80,8); assert s['primary']['complete']; rows=[json.loads(x) for x in (p/'episodes.jsonl').read_text().splitlines() if x]; assert len(rows)==10; print('B02 fixture readback: 80 synthetic steps, 8 Adam, 0 UAV calls')"
git diff --check
```

The original focused suite exited 0: **53 passed in 107.46 seconds**, below 300 seconds. Console evidence was returned in the CM tool transcript; no separate stdout log was created. New deterministic checks cover positive/negative clipping, five 1.05 ratios, inactive gradients, all-held denominator, behavior-policy gradient scale against a direct joint reference, duration ownership, old/new detachment, real synthetic T/G collection/update, unchanged update RNG, and vector nonfinite stop. Injected CLI tests route 7001/7002 through actual Config/study without UAV execution, including seed domains and checkpoint configuration. Aggregation checks preserve means 2/5, joint 3.5, conditional SE sqrt(.5), endpoint SD sqrt(4.5), and rejection/negative/partial cases. Existing information/reward/history/primary/dependency/clock checks remain covered.

The one CLI fixture exited 0 with `COMPLETE`, complete primary/hover, no diagnostic limits, and:

| Observed event | Count |
| --- | ---: |
| Training / evaluation / total synthetic team steps | 32 / 48 / 80 |
| Actual Adam calls / rollouts | 8 / 2 |
| Complete training / evaluation episodes | 4 / 6 |
| Velocity / duration decisions | 293 / 20 |
| d4 samples / recurrent observations | 9 / 320 |
| Diagnostic frames / partial steps / UAV calls | 100 / 0 / 0 |

Original readback passed. Additional read-only assertions confirmed two rollout rows with eight epoch records/Adam calls and 100 diagnostic lines. Files remain in [the original fixture root](../../../../../temp/directions/ucope/test/uav_motion_prefix_b02_fixture/summary.json): `summary.json`, `episodes.jsonl`, `rollouts.jsonl`, `diagnostics.jsonl`, `final_T.pt`, `final_G.pt`. No outcome was removed and no fixture rerun occurred. Synthetic scores are not UAV evidence. Unit tests additionally exercised their scoped deterministic/synthetic cases; their updates are not scientific exposure.

## Timing gap and bounded existing-evidence inspection

Raw runner clocks: pair `80.57799999997951` seconds; T `78.89099999994505`; G `1.687000000034459`. The runner sets `WHOLE_START` at line 3 before remaining imports/CLI parsing/Torch initialization. Thus the original complete smoke includes startup. `cap_breach=false` refers to the existing 1800-second arm/3600-second pair clocks; it does not certify the 60-second engineering limit. No separate complete external process wall, aggregate CPU or peak RSS was recorded; tool wait durations are not substituted for them.

At DM's request CM inspected only the existing clocks, source and file metadata. UTC filesystem creation times: output directory 16:08:19; JSONL files 16:08:20; final T checkpoint 16:09:03; final G checkpoint 16:09:04; summary 16:09:05. These locate the large elapsed interval before G, but do not isolate imports, first optimizer/library work or host/filesystem delay. Source retains the existing one-thread CPU chain, and the B02 increment is pointwise density/mask arithmetic. **No evidence-supported source correction was identified.** No profiling probe, warm-up, new execution, semantic substitution or budget increase followed.

Per-arm prospective cost context remains card §7: complete T/G planning references 148.27/141.37 seconds from historical same-loop evidence, with unmeasured incremental B02 cost; B02 density work is 2,621,440 terms/fit and log-density storage is 10,240 bytes/rollout. These are planning context, not measured B02 UAV time or a fivefold whole-run projection. Scientific limits remain 1800/arm, 3600/pair, 7200 summed. This task launches zero scientific pairs and cannot establish their runtime conformance.

Post-learner publication coverage is established by the complete synthetic checkpoint/row/summary path and readback. The missing acceptance fact is a complete conforming smoke within 60 seconds; the existing observation fails that bound. Any next action remains with the assigned DM/Root route, using this retained gap rather than an automatic repeat.

## Independent review and CM disposition

Configured independent `hmasd-reviewer` child `rv_ah_ucope_b02_credit` inspected the actual diff/callers/tests and read back published fixture artifacts without edits, duplicate learner execution or scientific execution. It found **no material credit-correctness defect**: compound grouping, old/new gradients, held masks, sum/mean scale, both-arm wiring, entropy/MC/chunks/Adam, historical behavior and B02 identity conform. It confirmed 80 steps, eight Adam calls, ten episode rows, 100 frames and zero UAV calls. Scope review found no §4 additions.

Its one material acceptance finding is the 80.578-second smoke overrun. CM accepts that finding and retains it unresolved. Functional correctness and publication evidence pass; unconditional technical acceptance and scientific feasibility are not claimed. The checked implementation commit is for Root integration/review; DM owns disposition of the timing gap and subsequent source/card binding. Masters 7001/7002 remain unexecuted by this CM.
