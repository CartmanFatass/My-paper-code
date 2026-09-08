Claim: A06 will observe the active Python call path if the original R09 chain leaves a readable fatal-stack report within one bounded attempt on the pinned system312 runtime.
Binding MARL structure: systems / information flow.

This runtime question does not itself test partial observability or non-stationarity;
it protects the event-address and learner path used by the same-information multi-agent comparison.

Object: `FRRIE-R09-FATAL-CALLPATH-A06-P31-20260908`.
Class: **A/RECON**. Status: `EXACT_COMMAND_FROZEN / READY_FOR_ONE_ATTEMPT`.
Allocation: at most one new complete120s observation; section7 records exact-command acceptance.
No invocation has started. This A object has no consumption state.

## 1. Decision question and retained-evidence check

Authority: [P31](../../portfolio/handoffs/2026-09-08-p31-frrie-fatal-callpath.md)
at main `989238f449e5e7b2ad59068b6e56096556d6586c`, applying the
[A05 intake](FRRIE_R09_FIRST_EXCEPTION_A05_SCIENTIFIC_INTAKE_20260907.md) §4.
Use evidence-spec §§3–4 and §11.8, particularly §§11.8.6–7; the next observation
need not reconstruct a causal writer or explain every historical failure.

DM inspected only the named retained A05 `supervisor/task.log`,
`supervisor/process-time.txt`, `remote_readback.txt` and E0 inventory under
`temp/directions/finite_resource_relational_inductive_efficiency/exp/a05_collection_p27/`.
The1006-byte log records a segmentation fault for Python PID2765962;42.71s is
the measured complete wall. It contains no Python traceback, fatal stack or
capture marker. The recorded inventory has no readable fatal/core artifact in
the owned cwd/output/supervisor paths. Other system-managed locations remain
unassessed; there is no exhaustive dump search or debugger execution. Those
retained bytes cannot answer the missing active-callpath question.

Question: at a fatal failure, does the active Python stack lie in original
program execution, traceback/debugger handling or the bounded capture helper?
The source of a fault and the writer of corrupted state are different questions.
An observed Python stack can locate callers without identifying either cause.

Select a separate observation that adds startup `-X faulthandler` to the accepted
A05 command. Keep the accepted standalone helper and173-byte pdb input unchanged.
Original scientific source, root3, runtime and complete schedule remain fixed.
This is a changed observation channel under P31, not a retry charged to P27.

The existing [CPython3.12 documentation](https://docs.python.org/3.12/library/faulthandler.html)
retrieved for A05 intake §4 documents fatal-signal Python stacks on stderr,
bounded by100 threads×100 frames and500 characters per string. Reuse that
verified source; it promises neither a trace in this failure nor address locals.
P23's source assessment remains relevant grounding; no new mechanism/comparator
design or literature search is needed for this startup-option change.

Decision value: a readable stack can select which existing path needs the next
inspection. A blind real B preserves the missing-location risk and larger full
schedule envelope. This one observation keeps real original learning in its
path; it adds no exact-support, writer-diagnosis or zero-learner prerequisite.

## 2. Primary observation, reading rule and interpretation

Primary: the fatal signal/termination facts and the active-thread Python frames
retained on stderr, including enough callers to distinguish original execution
from traceback/capture handling. Preserve other thread stacks separately; do not
treat a waiting thread as the faulting one. Record truncation or ambiguity and
source-relative file/function/line where readable. A stack is a path observation,
not a C stack, memory state, causal writer or runtime-reliability certificate.

If an ordinary uncaught Python exception reaches pdb first, retain its original
traceback and the unchanged A05 bounded record, then q/EOF. A helper error is
separate from the original exception. Keep normal/partial learner outputs and
original-program exit facts; debugger or supervisor exit0 alone is not success.
No continuation, step, second scientific-body traversal or second capture is allowed.
The accepted A05 normal-entry/restart-notice interpretation remains in force.

Apply the first matching row:

| Branch | Rule and bounded reading |
| --- | --- |
| `A06_NONCONFORMING` | Original source/runtime/RNG/schedule or approved observation bytes differ, observation advances/mutates scientific state, a second scientific traversal occurs, or the complete cap/allocation is breached. Preserve independent facts; no conforming diagnostic result or algorithm polarity. |
| `A06_FATAL_CALLPATH_CAPTURED` | The original process suffers a fatal failure and a readable active-thread fatal stack supplies enough caller context to distinguish original execution from traceback/debugger/capture handling. Record the exact observed path, signal, ambiguity and truncation; a different fatal signal is reported separately from P27 recurrence. No causal-writer attribution follows. |
| `A06_PYTHON_EXCEPTION_OBSERVED` | No fatal-callpath reading applies, but the first original uncaught Python exception and its traceback are retained. Record its identity and any trustworthy bounded state, including failed capture separately. This is bounded nonreproduction of the requested fatal observation, not clearance of A05/P22. |
| `A06_NORMAL_COMPLETION` | The original program completes normally within the cap with its outputs retained and no uncaught exception. Preserve all output for separate validity review; this observation is not a replacement shorter R09 comparison or reliability proof. |
| `A06_INCONCLUSIVE` | Failed admission, missing/ambiguous fatal trace, timeout, hard failure without a usable call path, or missing original-program termination evidence prevents the preceding readings. Record every trustworthy partial fact and the exact boundary; stop without retry, clearance or scientific polarity. |

Categorical **minimum effect of interest**: one readable active call path that
separates original execution from exception/capture handling, because it changes
the next bounded inspection. There is no return threshold for this measurement.
How the result will be interpreted: meeting that threshold supports a targeted
path inspection; an incomplete trace leaves the dependency unresolved; a capture-
or debugger-active path contradicts the predicted original-execution location.
The table controls all readings, including different errors and normal completion.
Missing optional resource telemetry does not erase independently trustworthy frames.

DM prediction: **fatal-callpath capture in original execution, low confidence**.
P22 observed a serialization failure, but A05 provides no evidence of its fatal
location. A readable debugger/capture path, ordinary Python-exception-only outcome
or normal completion contradicts this prediction. Failed admission, nonconformance,
timeout or failed path collection leaves it unscored. Owner prediction:
**not taken (unattended)** unless a reply is available at intake.

No tuned same-information host headroom record exists; this A does not measure it.
R09 MEI0.005, existing tight/wide/uniform comparator set and R06–R08 evidence remain
unchanged: root1 N15+0.005548293532 is conditional support; root2−0.001948094523
contradicts material recurrence; R08's root1 cut is not independent-root evidence.
No native-return, stable-superiority, mechanism, transfer, UAV or C claim follows.

## 3. Exact scientific and observation bindings

| Quantity | Frozen value |
| --- | --- |
| Original scientific/preflight source | `43eec21e9584c83e5e8d940402d7e4570b454e59` |
| Accepted helper/input source | `30643b7359b35c6e9d5751147d0999bc629a966d` |
| Helper | `experiments/candidates/finite_resource_relational_inductive_efficiency/r09_first_exception_a05/capture.py`,11464 bytes,SHA256 `0e75801266db0dc339da63ddd1a1f5a981b5b26bfc4ae243e87f8feb678f87b8` |
| Pdb stdin | `FRRIE_R09_FIRST_EXCEPTION_A05_PDB_COMMANDS_20260907.txt`,173 bytes,SHA256 `361c1df2f98b3291416cb1b7f20195440dd1f01a535586123f8889aab4a643f0` |
| Staged diagnostic paths, outside scientific tree | `/home/wu/hmasd-inputs/frrie-a05-first-exception-p27/capture.py` and `pdb_commands.txt`; reuse exact accepted bytes/readback, no rewrite |
| Actual node / host | `hmasd-wsl-node` / `LAPTOP-U9TDKC8A`, Ubuntu24.04/WSL2 |
| Existing interpreter | `/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python` |
| Runtime pins | P22 system CPython3.12.3/GCC13.3.0; all23 installed pins including NumPy1.26.3/Torch2.7.0+cu118, per P22 E0 |
| Fresh handle | `frrie-a06-fatal-callpath-p31-43eec21e` |
| Fresh detached cwd | `/home/wu/hmasd-worktrees/frrie-a06-fatal-callpath-p31-43eec21e` at original43ee |
| Fresh output relative to cwd | `temp/directions/finite_resource_relational_inductive_efficiency/exp/a06_fatal_callpath_p31` |
| Primary retained fatal text | Same handle's `/home/wu/.agent-tasks/frrie-a06-fatal-callpath-p31-43eec21e/task.log` stderr stream |
| Optional A05 record / original outputs | Fresh output's `summary.json` / `learner/`; the A05 helper schema and environment-variable names stay unchanged |

The sole command is the accepted [A05 Root handoff](FRRIE_R09_FIRST_EXCEPTION_A05_ROOT_HANDOFF_20260907.md)
§2 literal at `137ed1fda47662f4eb51fa9d70f41a6a3675d2a2`, with only fresh
handle/cwd/output substitutions above and `-X faulthandler` inserted between
`"$python"` and `-m pdb`. Keep `-c continue`, root3, the same stdin and q/EOF,
original-source `admit-memory && program`, thread environment and timeout wrapper.
Keep its helper variables and heredoc label; no unrelated command amendment.
CM publishes the resulting sole literal and byte digest before DM binds launch.

The unchanged event→entity/public-role address→exogenous tape→same-information
action/credit path→actual learner→native return chain is linked in A05 card §§2,4
and the [R09 card](FRRIE_R09_THIRD_ROOT_SCIENCE_CARD_20260905.md). CPU FP32,
original FP64 reductions, Torch1/four-worker/native32, LR0.003, beta boxes,
128 paired updates and original checkpoints/uniform/rosters stay fixed. No
first-input cutoff, alternative RNG path, import probe, setup or source correction.

## 4. Work, budget and engineering scope

At most **one chain×two arms×128 paired updates**, with one root3 and the original
8192 training/512 evaluation tapes,18 cells,16384 factual episodes,256 Adam/backward
calls and1316864 total native slots as A05 card §4's computed maxima. Nominal
per-arm LR exposure≤0.384, relative to initialization half-range≤7.68, is a
configured exposure statement, not measured motion. Actual updates/episodes/tapes
remain unknown until output proves them; do not infer zero from missing publication.

One outer **TERM115s plus at most5s grace =120s complete cap** covers adjacent
admission, startup/imports, original native build/load, initialization, evaluation,
training, fatal reporting/capture, publication and termination. The fresh native
build is inside this chain; do not reuse or alter P22/A05 native artifacts.
Fresh original preflight must pass physical and effective available memory≥4GiB
on the pinned actual node immediately before program entry. Root uses the existing
detached `agent-task` route and observes the same accepted handle; no relaunch.

A05's42.71s is a known complete-chain anchor, not a recurrence/completion forecast.
One120s cap is both the maximum invocation-wall sum and its execution critical path;
aggregate CPU/control-plane elapsed/scratch remain unmeasured unless existing
receipts supply them. GNU-time wall/peak RSS and fresh admission are retained.
Additional algorithmic arms/candidates are zero. Added fatal reporting is bounded
by the documented100-thread×100-frame limits; existing A05 capture remains32
frames/14 fields/256-character primitive text. All reporting shares the120s cap.

Validation is **static command/syntax/delta checking only**. Reuse A05 handoff §3's
accepted inert evidence; no new fixture, scientific smoke, cost pilot or import.
Engineering scope §4 need: reuse the existing optional bounded diagnostic facility
for active fatal frames and A05 exception state. No new research code, runner,
framework, retry/observer machinery or telemetry beyond the existing receipt is
needed. Exact P31 input/digest documentation is an assignment requirement, not a
new runtime validator. All other §4 additions: none; no §5 budget exception sought.

## 5. Complete CM assignment and stop

1. **Deliverable:** prepare one A06 Root handoff with exact sole command/argv,
   unchanged diagnostic input bindings and static acceptance, following §§2–4.
2. **Owned paths:** new `FRRIE_R09_FATAL_CALLPATH_A06_ROOT_HANDOFF_20260908.md`
   in this direction directory and ignored `temp/directions/finite_resource_relational_inductive_efficiency/exp/a06_preparation_p31/` receipts. Read original A05 helper/input/handoff at §3 revisions; no source or test edits. Reuse `C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`, `codex/frrie`, as sole writer through commit/push. DM owns this card, owner item and later intake; preserve all other work.
3. **Preserved semantics:** §3 and A05 card §§2,4; only startup fatal reporting
   and fresh paths change. No original source, runtime, seed, schedule, capture,
   termination or comparison alteration. No new child or live scientific command.
4. **Acceptance:** compare the A05 published Git-blob command to A06; normalize
   exactly the declared fresh paths and added startup flag and require equality.
   Check outer Bash/heredoc syntax with `bash -n`, verify helper/input bytes remain
   the §3 bindings, and retain concise checks in the handoff. No target execution,
   package import or repeated A05 fixture. Evidence-spec §§4,11.8.6–7 controls.
5. **Budget/stop:** static preparation only, zero scientific invocations. Commit
   and push the handoff by explicit path, return to DM for exact-card acceptance.
   Root then owns the sole≤120s chain. Reuse this CM for terminal collection/E0;
   DM applies §2, writes intake/Chinese brief/audit, and returns any next-task need
   through Root to Portfolio. Every terminal boundary ends the allocation: no
   retry, fallback, cap extension, new seed, full B, repair or added diagnostic.

The three CM comparison batches are already complete in the current campaign
progress table; enrollment has ended. This assignment is static preparation of
an unchanged-code command, and adds no comparison or scientific invocation.

## 6. Delegated selection and owner surface

Options: (a) prepare the separately allocated fatal-stack observation; (b) stop
with the already retained unreadable-location evidence; (c) repeat A05 unchanged
or repair without a located path. Recommend/select **(a)** under P31.
**Owner-delegated decision (unattended,2026-09-03 instruction): (a).**
This is an object-tier observation choice, with no lifecycle, priority, recast,
UAV entry or scientific-polarity change. New-card P2 is published through the
owner console as [20260908-frrie-001](../../portfolio/owner/inbox/2026-09-08/20260908-frrie-001.json);
reviews were empty at preparation. Ordinary acceptance and intake
decisions remain in this card/intake and audit. The loop does not wait for a reply.

Root appends this row to the shared audit on integration:

```text
| 2026-09-08T07:14:48Z | finite_resource_relational_inductive_efficiency | object | selection | (a) P31 separate fatal-stack observation; (b) stop with retained missing path; (c) unchanged retry/unsupported repair | (a):A06 A_RECON,only startup fatal reporting plus fresh paths,one complete120s after acceptance;no invocation yet | yes | OWNER_DELEGATED (unattended,2026-09-03 instruction); P31 | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_FATAL_CALLPATH_A06_SCIENCE_CARD_20260908.md | none | |
```

## 7. Exact-command acceptance and Root release

DM accepts the [A06 Root handoff](FRRIE_R09_FATAL_CALLPATH_A06_ROOT_HANDOFF_20260908.md)
at **`fc279590ecd88aa3cc2d5c10348453b7dcd4e9fe`**. That CM commit changes
only the new handoff document; it descends the frozen card at4ebe6b9ee. No
scientific source, helper, stdin, test or previous evidence changed.

| Final command binding | Value |
| --- | --- |
| Immutable source | The handoff's sole sh fence at fc279590ecd88aa3cc2d5c10348453b7dcd4e9fe |
| Extraction | Remove only the single LF between final `FRRIE_A05` and the closing fence; retain every other byte |
| Length / CR count | 1200 UTF-8 bytes /0 |
| SHA256 | `67f598644882f596ecbfbced2454003c69c9a04cb153a6f62b23079e00bf72e3` |
| Supervisor argv | `/usr/local/bin/agent-task`, `run`, `frrie-a06-fatal-callpath-p31-43eec21e`, entire literal as one argument |
| Source/input/runtime/output/cap | Exactly §§3–4 and handoff §§1–2; original43ee, unchanged306 helper/stdin, one120s chain |

DM read the complete handoff, actual `static_acceptance.json` and sole committed
literal against §§2–5. CM's reverse-delta equality reports exactly two handle/cwd
substitutions, one output substitution and one startup-flag insertion. Outer and
heredoc `bash -n` returned0 with empty output; committed helper/stdin bindings are
unchanged. DM independently read the Git blob's1200-byte command/hash and matched
the retained checked command. It contains exactly one `-X faulthandler -m pdb -c continue`
entry; no scientific command, parser check or fixture was reexecuted during intake.
DM receipt: `temp/directions/finite_resource_relational_inductive_efficiency/exp/a06_preparation_p31/dm_acceptance_readback.json`.

Reused inert evidence supports the bounded A05 capture/termination recipe only;
it does not check the original learner's complete publication pipeline. Actual
fatal-stack availability and the scientific chain's terminal behavior remain
unobserved. Counts during this preparation:0 scientific invocations,0 new
fixture/import invocations. No engineering-scope §5 breach is evidenced.

Object-tier technical options: (a) accept the conforming static handoff and
release the already allocated one observation to Root; (b) return a concrete
command gap for correction. Recommend/select **(a)**.
**Owner-delegated decision (unattended,2026-09-03 instruction): (a).**
Main owner reviews were empty at this boundary; no new owner instruction was
inferred. Root integrates this binding and dispatches/observes the same accepted
handle under P31. CM then collects E0 and DM applies §2; no terminal result yet.

Root appends the following ordinary technical row alongside §6's selection row:

```text
| 2026-09-08T07:22:28Z | finite_resource_relational_inductive_efficiency | object | technical | (a) accept exact static handoff; (b) return concrete command gap | (a):A06 command1200B SHA256 67f598644882f596ecbfbced2454003c69c9a04cb153a6f62b23079e00bf72e3 accepted;Root one120s dispatch next;scientific invocations0 | yes | OWNER_DELEGATED (unattended,2026-09-03 instruction); P31 | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_FATAL_CALLPATH_A06_SCIENCE_CARD_20260908.md#7-exact-command-acceptance-and-root-release | none | |
```

scope: none
