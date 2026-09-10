# UCOPE B04 7201 — terminal technical acceptance

**Accepted: the single P61 invocation completed at source `7693b7af6b7d89cdaa028659d606a37dee9eb68e`, with no observed integrity or cap failure.** [Machine-readable collection evidence](UCOPE_UAV_MOTION_PREFIX_B04_7201_COLLECTION_20260908.json) retains the complete summary, all32 T/G/H outcomes, paired differences, checkpoint group counts/norms, admission and artifact hashes. DM owns interpretation under [card §§4–6](UCOPE_UAV_MOTION_PREFIX_B04_SCIENCE_CARD_20260908.md); Root owns integration and cleanup after intake archival.

## Exact handle and collected publication

Handle `ucope-uav-motion-prefix-b04-7201-p61-20260908` ran on `hmasd-wsl-node` in `/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b04-p61-check-20260908`. CM independently read the same terminal **finished/exit0/PID3012256/tmux inactive** status, exact accepted HEAD and clean remote checkout. Its supervisor command uses the literal wrapper from the [committed CM handoff](UCOPE_UAV_MOTION_PREFIX_B04_TECHNICAL_ACCEPTANCE_20260908.md#literal7201-command-handoff--completion-of-the-existing-b04-task). The collected executed wrapper matches the bound SHA-256 `262ce2d711e1ded155abdf375aeb0e5a763f745e385772cfa2234e9506db796f`.

All seven scientific output files and the supervisor receipts were copied by SCP into the **direction checkout** at `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906/temp/directions/ucope/exp/uav-motion-prefix-b04-7201-p61-20260908/`. Each output SHA-256 matches the independently read remote digest. Both final checkpoints, full episode/rollout/diagnostic JSONL, admission, summary, terminal stdout and executed wrapper remain there; remote originals are retained pending Root cleanup. The collection JSON records exact hashes and local root. H is untuned and has no checkpoint.

The local `verify_collection.py` reads stored JSON and tensors using the configured CPU interpreter. It constructs no model/environment and invokes no learner/evaluator. Its exit0 PASS is based on the checks below; collection adds zero scientific exposure and no test-suite rerun.

## Reconciled technical facts

- Identity: real `UAV_B_EXPLORE`, COMPLETE, B04/7201, declared masters[7201], correct card section5, agent_compound and entropy0. Config/checkpoints/arm metadata agree on T-only `sampled_command` duration with private seed720100012; G has no duration head.
- All1120 episode rows complete256 steps. T/G each have512 training episodes and256 rollout rows with four actual optimizer steps per rollout:131072 training team steps and1024 Adam calls per fit. Episode/reset associations match b+1000+e; all32 final T/G/H resets match b+2000+e. Row decision counts reconcile with each arm's reported training/evaluation totals.
- Counts reconcile to262144 training plus24576 evaluation team steps,286720 scientific UAV calls,2048 Adam calls,96 final episodes,1600 diagnostic rows,1120 explicit resets and two constructor resets. Zero partial episode steps; all fits, learned-arm final evaluations and hover are complete.
- Every numeric JSON value is finite. Both checkpoints contain finite FP32 actor/critic tensors and identical effective Config. Their actual parameter groups and final norms match published exposure. T has68553 parameters, G66311; T's duration head has2242, split2176 hidden and66 final parameters, with shapes32×67 and2×32. G has no duration parameters.
- Both fits show recorded nonzero total displacement: T8.53953742980957 and G9.17547607421875. T duration displacement is0.41481131315231323; hidden0.4102451503276825; final0.06137862801551819. The final group's initial norm is0, its absolute displacement equals its final norm, and its relative displacement is null. These are observations, not requirements that every parameter move or evidence of performance benefit.
- Each episode J equals its recorded complete reward sum/256; the96 final J values match the published arrays exactly. Independently computed paired differences/moments match emitted T−G/G−H. Supervisor stdout contains the same primary/counts as summary; its admission bytes match the scientific admission copy. This checks recorded native-return publication without resimulating rewards.

Fresh actual-node admission passed with physical/effective available memory both **15640686592 bytes**, above4GiB, before scientific output/model creation. The complete invocation took **277.51s**, peak RSS **554964KiB**; terminal log duration277s. Internal charges: T137.67042454401962s, G139.29419632797362s, pair276.9646218509879s. No emitted limits or cap breach; both1800s arm caps and3600s complete-pair cap were met. Aggregate CPU was not measured, and process RSS is not total system memory consumption.

## Preserved endpoint moments and next owner

| Paired native contrast | Mean | Conditional episode SE |
| --- | ---: | ---: |
| T−G |−0.003948225944122139 |0.010191826216031805 |
| G−H |0.0238187196536019 |0.011454243503509544 |
| T−H |0.019870493709479763 |0.014677398371169156 |

The complete single-pair result is ready for DM's card-rule/prediction intake. Independent training n=1 remains unchanged; no multi-pair aggregate, historical pooling or training-population uncertainty is supplied. Technical acceptance does not establish a conditioning mechanism, stable performance, transfer or family disposition.

CM collected from authoring HEAD `86b6c6ace57e73100e96da636254d73b542cdc48`, preserving unrelated changes and accepted source. Only this technical record and its collection JSON are committed. No relaunch, second pair, extra H completion/evaluation, tuning or model invocation occurred. Historical test/setup/launcher failures remain preserved at their original meaning. Engineering scope §4: none. DM next intakes every outcome; Root integrates and removes the remote execution checkout/wrapper only after terminal artifacts, this collection and DM intake are archived. The selected7201 allocation is exhausted; this return allocates no further experiment.
