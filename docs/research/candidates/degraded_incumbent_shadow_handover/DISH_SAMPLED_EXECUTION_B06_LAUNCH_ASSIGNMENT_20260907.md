# DISH B06 explicit launch assignment — prepared, not dispatched

Root's 2026-09-07 preparation task asks for the complete next handoff and explicitly forbids
launch. This document supplies that handoff for the existing CM
`/root/dm_amx_dish_seed101/cm_am_dish_seed101`. **No supervisor request, remote staging,
admission, initializer or scientific invocation was issued in preparing it.** Root can dispatch
this bounded assignment separately; source acceptance and this document do not constitute that
dispatch. No new Pro round or owner-console approval is requested.

## 1. Five-item CM handoff

1. **Deliverable and goal.** When explicitly dispatched, execute and collect the one already
   selected seed113 B06 invocation. Return the exact launch/terminal facts, retained outputs and
   an E0 result/CM acceptance record under the direction directory. DM reads the scientific
   result. The [technical intake](DISH_SAMPLED_EXECUTION_B06_TECHNICAL_INTAKE_20260907.md)
   §§1–4 already accepts implementation and focused synthetic coverage; do not repeat it merely
   because execution is now assigned.
2. **Owned paths and entry points.** Execute the bindings and payload in §§2–3. Source is
   `scripts/run_dish_sampled_execution_b06.py` and
   `experiments/candidates/degraded_incumbent_shadow_handover/sampled_execution_b06/study.py`,
   with their accepted B04/B02/R06 dependencies at the bound SHA. Collect only this invocation's
   runtime envelope; write evidence beside this assignment. CM retains its existing own
   branch/worktree and preserves others' edits. No source modification is selected. A concrete
   defect threatening the comparison returns with evidence; changed source is a new launch,
   never an unrecorded retry of this command.
3. **Preserved semantics.** [Frozen card](DISH_SAMPLED_EXECUTION_B06_SCIENCE_CARD_20260906.md)
   §§2–5 supplies the learner, master/address laws, host/device, all sixteen rows, endpoint,
   primary, native companions and seven result branches. In particular, one LOW_LR learner
   supplies both final modes; use its own initialization and update16 state. Keep native
   float64/policy FP32 and one CPU compute thread. Do not change seed, sample count, horizon,
   RNG, native promotion, selection, dtype or device to fit the execution window.
4. **Acceptance and collection.** Apply card §§4–7 and evidence-spec §§4, 5.2, 11.4,
   11.8.6–11.8.7. The real learner, counts, finiteness, all primary rows and native consequences
   must be readable. Follow §4 below for stdout, publication and observation ownership. Exit0
   alone does not establish scientific completeness. Preserve exceptions, partial exposure and
   independently trustworthy rows; missing optional resources remain `resources_unmeasured`.
5. **Budget and stop.** One complete 1800s cap, with the accepted 10s check charge and at most
   1790s left for the entire new chain. §3 allocates its stopping/publication time without adding
   work. Stop at completion, that bound, nonfinite learner state or a fault threatening the
   primary. No extra A, training seed, sample, intermediate checkpoint, native timing pilot or
   second invocation is assigned. Engineering-scope §4 additions needed: **none**; use the
   existing supervisor, OS timer and observation route. Current preparation ends at pushed
   documentation, without dispatching CM or executing the payload.

## 2. Concrete source, node and paths

| Binding | Value |
| --- | --- |
| Accepted source / execution SHA | `373d187200a91942385e9380770dcf9f8098aada` |
| Integrated technical intake | `e29bbec1dc374a4f19565b0360057f6eea0cdd88` |
| Node / transport | `wsl_4070`, SSH target `hmasd-wsl-node` |
| Remote repository | `/home/wu/projects/HMASD` |
| Detached execution worktree / cwd | `/home/wu/hmasd-worktrees/dish-b06-seed113-20260907-run01` |
| Planned supervisor handle | `dish_b06_seed113_20260907_run01` — prospective, not accepted |
| Interpreter / supervisor | `/home/wu/.venvs/hmasd/bin/python`; `/usr/local/bin/agent-task` |
| Runtime envelope, relative to cwd | `temp/directions/degraded_incumbent_shadow_handover/exp/sampled_execution_b06_seed113_20260907_run01` |
| Scientific output / runner `--out` | `<envelope>/result` |
| Admission / runner `--admission` | `<envelope>/admission.memory.json` |
| Full command outputs | `<envelope>/stdout.log`, `stderr.log`, `whole_chain.time.txt` |

The absolute envelope is the stated cwd plus its stated relative path; the payload expands it
explicitly. It may hold logs and the receipt before admission, but **do not create `result`**:
the runner calls `args.out.mkdir(parents=True)` after admission and requires that path absent.
No scientific state is constructed by directory preparation. Preserve a collision or an
uncertain accepted handle and reconcile it; do not overwrite/relaunch it under this assignment.

Use the current `.codex/hmasd-compute.toml` route. After actual dispatch, the existing remote
repository may fetch the already pushed commit and create this detached worktree:

```bash
git -C /home/wu/projects/HMASD fetch origin &&
git -C /home/wu/projects/HMASD worktree add --detach \
  /home/wu/hmasd-worktrees/dish-b06-seed113-20260907-run01 \
  373d187200a91942385e9380770dcf9f8098aada
```

This binds execution to accepted committed bytes; current control-plane instructions still
govern collection and observation. The relevant B06/B04/B02/R06, native and admission source
surfaces have no diff between the bound source and preparation baseline
`051aaa87e4bfae5aec6372cd5350ce02d4a213bc`. No code copy from an uncommitted checkout, GPU
substitution, Windows fallback or migration of a live process is selected.

## 3. Exact prospective supervisor payload and cap accounting

Run this on `hmasd-wsl-node` only after the separate execution dispatch. The heredoc creates
one ordinary command string for the existing supervisor, not a new execution helper/framework.

```bash
dish_b06_command=$(cat <<'DISH_B06_COMMAND'
export DISH_B06_CWD=/home/wu/hmasd-worktrees/dish-b06-seed113-20260907-run01
export DISH_B06_ENVELOPE="$DISH_B06_CWD/temp/directions/degraded_incumbent_shadow_handover/exp/sampled_execution_b06_seed113_20260907_run01"
mkdir -p "$DISH_B06_ENVELOPE" &&
/usr/bin/time -v -o "$DISH_B06_ENVELOPE/whole_chain.time.txt" \
  /usr/bin/timeout --signal=ALRM --kill-after=9s 1780s bash -lc '
    dish_b06_chain_started=$SECONDS
    cd "$DISH_B06_CWD" &&
    export PATH="/home/wu/.local/bin:/usr/lib/wsl/lib:$PATH" \
      PYTHONPATH="$DISH_B06_CWD" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
      OPENBLAS_NUM_THREADS=1 MAX_JOBS=1 &&
    /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py \
      admit-memory --out "$DISH_B06_ENVELOPE/admission.memory.json" &&
    exec /home/wu/.venvs/hmasd/bin/python scripts/run_dish_sampled_execution_b06.py \
      --seed 113 --out "$DISH_B06_ENVELOPE/result" \
      --admission "$DISH_B06_ENVELOPE/admission.memory.json" \
      --prior-check-seconds "$((10 + SECONDS - dish_b06_chain_started + 1))"
  ' > "$DISH_B06_ENVELOPE/stdout.log" 2> "$DISH_B06_ENVELOPE/stderr.log"
DISH_B06_COMMAND
)
/usr/local/bin/agent-task run dish_b06_seed113_20260907_run01 "$dish_b06_command"
```

The same-node `admit-memory` and runner are joined by `&&`: missing/failed admission or either
physical/effective available memory below 4GiB prevents the runner, RNG masters and learner.
`exec` replaces the admitted shell with the runner, so the OS timeout targets that process
directly. The preserved CPU/thread settings cover admission, imports/build/load, learning and
all evaluation/publication. Native build/cache loads, if needed, stay inside the timed runner.

| Charge/allocation | Seconds | Meaning |
| --- | ---: | --- |
| Already accepted required checks | 10 | Measured 8.6709155s, conservatively charged once; technical intake §3 |
| Remaining whole-chain allowance | 1790 | Admission, shell/Python startup, build/load, learner, all16 evaluations, reduction, publication and command closure share this |
| Outer ALRM point | 1780 | From timeout start, including admission; invokes the runner's existing interruption path if still active |
| Maximum subsequent KILL grace | 9 | Inside the remainder, for interruption/publication/termination; no extra training allowance |
| Remaining command/time-output margin | 1 | Also inside the remainder; never a cap relaxation |

Thus `10 + 1780 + 9 + 1 = 1800`. Reserving the final ten seconds is an execution allocation
inside the unchanged cap, not an extra stage or permission to trim scientific exposure. The
runner's internal timer also receives the existing 10s plus an upward-rounded elapsed
pre-run/admission charge: Bash integer elapsed seconds +1. Retain its actual resolved value
from stdout. This includes admission in its allowance; do not pass a bare10 and silently give
admission separate time. Do not add that pre-run charge again to the whole-chain measurement.

For cost intake, retain the OS whole-chain wall and supervisor start/terminal evidence, including
command setup/closure where reported, and add the earlier10s once. Record actual scope and any
overrun; timer settings are not a claim of perfect OS scheduling or proof of cap conformance.
The source disables its own timer before publication, so the external timeout remains necessary
through JSON/stdout completion. Additional required execution checks outside this command must
reduce the remaining allowance and be recorded before an actual dispatch; none are selected
here. Repository reading, command authoring and Git integration are control-plane work.

The existing [exposure/cost record](sampled_execution_b06_20260906/EXPOSURE_AND_COST.json)
remains binding: 1 learner ×16×32×128 =65,536 ordinary transitions; 16×4×8 =512 optimizer
steps; 4 initial MODAL +4 final MODAL +8 SAMPLED =16 episodes, <=19,200 evaluation ticks.
Native training is `2N+2E+H` in [131,072,1,572,864]; sampled policy uniforms <=96,000.
E/H/R and new wall remain unmeasured. B05's 212.86s LOW_LR and 7.11s shared-reference timings
are planning anchors, not a measured B06 price. No additional scientific exposure occurred here.

## 4. Accepted-handle observation and complete collection

After actual supervisor acceptance, retain the receipt and send the accepted handle plus a link
to this assignment/card to the Root configured in `.codex/hmasd-monitor.toml`, following
`docs/project/EXPERIMENT_MONITOR.md` §Assignment and adoption. Native CM/DM uses collaboration;
a separate app task uses `send_message_to_thread` without model/effort overrides. Supply the
actual launch SHA/cwd/node, receipt/log/result paths, acceptance/start time, expected terminal
bound and CM identity. These are missing run facts, not another launch condition.

The launcher owns observation until Root's adoption ACK; Root records the handle and reads
back the existing shared heartbeat as ACTIVE before ACK. Root then owns routine observation,
CM owns collection/technical acceptance, and DM owns scientific intake. Do not relaunch to
transfer observation. Read-only status/log commands after acceptance are:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task status dish_b06_seed113_20260907_run01
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task logs dish_b06_seed113_20260907_run01 40
```

At the authoritative terminal event, collect the complete envelope through the configured SCP
route to the matching local temp relative path in CM's worktree. Retain admission, both full
logs, whole-chain timing, supervisor command/exit evidence and every produced file under
`result`, including `summary.json`, `paired.json`, initialization/reset files, the update16
checkpoint and learner/episode records. Do not copy a live tree for routine monitoring.

Normal source publication writes summary/paired before adding `completed_wall_seconds` and
`charged_wall_seconds`; the **last complete stdout JSON** has those fields. Preserve and read
both representations with their scope rather than rewriting raw output. Interrupted publication
may leave a different subset; report that subset and counts. A timeout/exception/SSH failure is
not a signed performance result. Do not fabricate the full primary, infer a new retry budget,
or select another sample/seed. Apply card §5 only to the trustworthy measured comparison.

## 5. Decisions and current intake state

1. **Object-tier next-step preparation.** Options: (a) return this complete prospective CM
   assignment; (b) infer a run dispatch from technical acceptance; (c) leave the known bindings
   unresolved. Recommend/select **(a)** under Root's current explicit preparation-only task.
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a)** for the routine concrete
   bindings; `OWNER_DIRECT` current Root task preserves the no-dispatch boundary.
2. **Object-tier execution allocation.** Options: (a) share1790s across admission/run/publication
   with the1780+9+1 allocation above; (b) give the runner1790s plus uncharged admission/publication;
   (c) buy a timing probe. Recommend/select **(a)** prospectively. No invocation occurs now.
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**

The task produced a launch assignment, not a new valid scientific result. B06 remains unrun;
Delta_exec is unmeasured and its <=-24 low-confidence prediction remains unscored. Owner
prediction: not taken. Primary-checkout owner reviews returned `[]` at this boundary; no
applicable unapplied review or nonempty DISH audit override was present. Owner flags: none.
Ordinary technical/object decisions remain in this record/audit under the current P1/P2-only
owner skill. No new card, direction/Portfolio decision, Chinese valid-result brief or DIRECTION
science update is required. The next discriminator remains the complete frozen B06 comparison.

Preparation checks: Python recomputed the stated budget/exposure arithmetic from the existing
cost record. Git Bash `--noprofile --norc -n` parsed the three Bash blocks, the supervisor
payload and its inner command without executing them. This checks command syntax, not remote
availability, resource admission or native runtime behavior. No scientific tests were rerun.
