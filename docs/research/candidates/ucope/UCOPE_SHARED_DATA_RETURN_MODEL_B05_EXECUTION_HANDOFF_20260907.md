# UCOPE B05 same-budget pair — executable handoff, not dispatched

**P10-UCOPE-PAIR-PREP-01 is preparation only. Execution is unallocated.** These exact commands
are candidates for a subsequent Portfolio allocation through Root. The requested existing CM
route is recorded below but was not present in the current native inventory; no replacement
or implementation task is selected by this handoff.

## 1. Five-item handoff for a subsequent execution command

1. **Deliverable/goal:** if allocated later, execute the prospective B05 seeds 6701 then 6702
   through the existing shared runner; collect all outcomes and E0 evidence for joint DM intake.
   The [card §§2–5](UCOPE_SHARED_DATA_RETURN_MODEL_B05_SCIENCE_CARD_20260907.md#2-fixed-datasets-learning-and-information)
   supplies the comparison and counts. No implementation is required by this interface.
2. **Owned checkout/paths:** reuse `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`,
   branch `codex/ucope`; preserve unrelated edits and serialize its index ownership. Read-only
   entry is `scripts/run_ucope_shared_data_return_model_b02.py::run`, with model/evaluation in
   `experiments/candidates/ucope/shared_data_return_model_b02/`. Future owned outputs are the
   two roots in §2 and `UCOPE_SHARED_DATA_RETURN_MODEL_B05_RESULT_EVIDENCE_20260907.md` in this
   direction directory. The DM owns scientific intake/brief; CM owns collection/technical acceptance.
3. **Preserved semantics:** card §2 changes only seed, B05 result identity and output/handle names.
   Keep 512 batches, the full three-policy evaluation, shared observed labels, binary64 order,
   B02 RNG-family literal, native reward/cost/information, ties/fallback and every outcome.
   Call the existing API explicitly; do not edit historical CLIs or their defaults.
4. **Acceptance and route:** reuse B04's accepted budget/default/seed/publication checks and
   independent affected-path review at source `71433bfabb70481def4329e622a838fa0cd9eeec`.
   Card §§2–5 and evidence-spec §§4, 5.2, 11.4, 11.8.3, 11.8.5–11.8.8 control; no repeated smoke
   or new validation arm is required for this unchanged source/API. Each future summary must
   bind the exact source, selected seed/B05 identity/512 batches, readable nonzero real counts,
   complete full evaluation, primary/acquisition/cost/plan measurements and exposure. Preserve
   partials and optional `resources_unmeasured`. After Root integrates/pushes this preparation,
   only a subsequent Portfolio command may allocate execution. The same CM then supplies each
   accepted handle/node/source/cwd/log/root/receipt to Root, retains observation until adoption
   ACK or terminal, and collects when Root reports terminal status. Root owns routine observation
   after ACK under `EXPERIMENT_MONITOR.md`; transfer never relaunches a process.
5. **Budget and stop:** candidate cap 600 seconds per complete dataset command / 1200 seconds
   summed, including adjacent remote admission through publication/exit; zero calls allocated
   by P10. Future order is fixed, with terminal reconciliation between seeds and every valid
   sign retained. A concrete shared scientific-integrity defect, failed admission or unavailable
   source/route returns its evidence to Root/Portfolio without invented retry, seed replacement,
   local fallback, implementation or third invocation. Use only the existing supervisor.

## 2. Bound source, remote paths and exact existing-API commands

- **Launch source:** `71433bfabb70481def4329e622a838fa0cd9eeec`, already accepted and integrated
  on main as `98ee9ec0f`. B05 calls its existing `run` API; no new source SHA is needed for a
  source change. The preparation commit is separate provenance and does not rebind old B04 runs.
- **Node:** `wsl_4070`, SSH `hmasd-wsl-node`, CPU binary64/one scientific process/compute thread;
  Python `/home/wu/.venvs/hmasd/bin/python`.
- **Recorded detached source cwd to reuse:** `/home/wu/hmasd-worktrees/ucope-shared-return-b04-20260907`,
  at the launch SHA above. Its B04 handles are terminal and historical outputs remain intact.
  Availability/current SHA is a recorded B04 fact, not newly remotely observed during preparation.
  If that committed source checkout is unavailable, return the exact route gap under the later
  command; preparation does not stage source or create a remote worktree.
- **Fresh relative roots:** `temp/directions/ucope/exp/shared-data-return-b05-seed6701/` and
  `temp/directions/ucope/exp/shared-data-return-b05-seed6702/`, beneath the bound remote cwd.
  Each future root holds `summary.json` and adjacent `resource_admission.json`; local collection
  uses the same relative paths in the designated direction checkout.
- **Future handles:** `ucope-shared-return-b05-seed6701-20260907` and
  `ucope-shared-return-b05-seed6702-20260907`; logs `/home/wu/.agent-tasks/<handle>/task.log`.
  These are prospective names, not accepted handles. No remote availability probe or Send occurred.

The following are exact **remote bash command strings** for the configured SSH execution route.
Each starts the existing detached supervisor, with `/usr/bin/time` outside a whole-command
`timeout --signal=KILL 600s` and destination preflight joined directly to the API call by `&&`.
The embedded Python only selects existing API arguments; B04's restricted seed CLI is not used.
The commands are recorded here, not executed.

### Seed 6701

```sh
/usr/local/bin/agent-task run ucope-shared-return-b05-seed6701-20260907 '/usr/bin/time -f '"'"'whole_wall_seconds=%e peak_rss_kib=%M'"'"' /usr/bin/timeout --signal=KILL 600s /bin/bash --noprofile --norc -c '"'"'cd /home/wu/hmasd-worktrees/ucope-shared-return-b04-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/shared-data-return-b05-seed6701/resource_admission.json && /home/wu/.venvs/hmasd/bin/python -c "from scripts.run_ucope_shared_data_return_model_b02 import run; import sys; raise SystemExit(run(sys.argv[1], seed=int(sys.argv[2]), object_id=sys.argv[3], batches=int(sys.argv[4])))" temp/directions/ucope/exp/shared-data-return-b05-seed6701 6701 UCOPE-SHARED-DATA-RETURN-MODEL-B05 512'"'"''
```

### Seed 6702

```sh
/usr/local/bin/agent-task run ucope-shared-return-b05-seed6702-20260907 '/usr/bin/time -f '"'"'whole_wall_seconds=%e peak_rss_kib=%M'"'"' /usr/bin/timeout --signal=KILL 600s /bin/bash --noprofile --norc -c '"'"'cd /home/wu/hmasd-worktrees/ucope-shared-return-b04-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/shared-data-return-b05-seed6702/resource_admission.json && /home/wu/.venvs/hmasd/bin/python -c "from scripts.run_ucope_shared_data_return_model_b02 import run; import sys; raise SystemExit(run(sys.argv[1], seed=int(sys.argv[2]), object_id=sys.argv[3], batches=int(sys.argv[4])))" temp/directions/ucope/exp/shared-data-return-b05-seed6702 6702 UCOPE-SHARED-DATA-RETURN-MODEL-B05 512'"'"''
```

## 3. Exact return and acceptance identities

Requested CM: **`/root/dm_ucope_question_prep/cm_am_ucope_native_return_b01`**.
Native inventory query for `/root/dm_ucope_question_prep` returned no agents during P10 prep.
Preserve this named route and return the unresolved identity to Portfolio; do not create a CM
or silently substitute Root for CM technical acceptance.

Prepared by DM **`/root/dm_ucope_p10_pair_prep`**; native Root **`/root`**, configured Root app
task **`01a07249-b095-7821-8ce2-e9c32ba85267`**. No model/effort override is needed.
If Portfolio subsequently supplies allocation and resolves the existing route, Root dispatches
that CM, adopts accepted handles, notifies the same CM at terminal, integrates its complete
E0 collection, and returns the integrated evidence to this DM for all-outcome scientific intake
and the Chinese brief. If the DM identity is no longer available, Root returns that exact gap
to Portfolio. Scientific classification stays with DM; allocation/routing stays with Portfolio.

Preparation release: DM retains sole edit/index ownership through its explicit commit/push,
then returns the clean checkout. There is no active CM writer, run, monitoring adoption or
experiment result from this assignment. Root's next step is integration and the Portfolio return,
not execution of §2.
