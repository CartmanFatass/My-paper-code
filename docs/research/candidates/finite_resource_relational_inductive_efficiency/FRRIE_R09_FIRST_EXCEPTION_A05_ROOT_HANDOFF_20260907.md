# FRRIE R09 first-exception A05 Root handoff — 2026-09-07

**CM implementation and focused acceptance are complete; the scientific diagnostic is unlaunched.** DM next accepts these bytes/stop facts and commits the [A05 card](FRRIE_R09_FIRST_EXCEPTION_A05_SCIENCE_CARD_20260907.md) binding. Root then owns the sole P27 admission, detached dispatch and observation. No repeat fixture, setup, package acquisition, import certificate, scientific smoke or repaired run follows from this handoff.

Authority: A05 card §§1–6 at `74a547f4a9ec4d5ea9245c180963590cf7b44401`, P27 main `a10e37e5161ae444f24db08844c621738ddbad7d`. The standalone capture and inert fixture are committed/pushed at **`30643b7359b35c6e9d5751147d0999bc629a966d`** (initial implementation66106b3 plus the narrow absent-attribute repair) on shared `codex/frrie`, `C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`. Original scientific/preflight source stays **`43eec21e9584c83e5e8d940402d7e4570b454e59`**.

## 1. Bound bytes and source preservation

| Owned surface at30643b7 | UTF-8/LF bytes | SHA256 |
| --- | ---: | --- |
| [Standalone capture](../../../../experiments/candidates/finite_resource_relational_inductive_efficiency/r09_first_exception_a05/capture.py) | 11464 | `0e75801266db0dc339da63ddd1a1f5a981b5b26bfc4ae243e87f8feb678f87b8` |
| [New A05 pdb input](FRRIE_R09_FIRST_EXCEPTION_A05_PDB_COMMANDS_20260907.txt) | 173 | `361c1df2f98b3291416cb1b7f20195440dd1f01a535586123f8889aab4a643f0` |
| [Direct inert fixture](../../../../tests/experiments/candidates/finite_resource_relational_inductive_efficiency/r09_first_exception_a05/test_capture.py) | 8392 | `6bd53d10cb2b357004160cf43b2fb6bc94b11e77c1187006e5d64505ae78d2ef` |

The new input is exactly two lines: a standalone `exec` expression in a fresh namespace, then `q` and EOF. **It is paired with `python -m pdb -c continue -m scripts.run_frrie_b01_contact_r09`**, as in the sole literal below. It must not be used at a pre-execution prompt without the initial `-c continue`. The helper reads `sys.exception()` while pdb's exception handler is active; it does not rely on the historical fixed-depth frame movements or `sys.last_traceback`.

The original528-byte stdin remains SHA256 `00631d27830cfb14b002aa0268d5ccc5d3b40a72a7a8f7d44a3c4ce295a7da65`. Local retained/bound comparisons confirm unchanged `rng.py`, `tapes.py`, contact `experiment.py/tapes.py/semantics.py`, original R09 script and resource-preflight script. The complete implementation diff from74a547f4 contains only the three new code/input/test paths above; no original file was edited. Remote acceptance readback matched all three committed digests. These are byte-preservation facts, not a scientific runtime certificate.

Root provisions the fresh detached original43ee worktree from card §4. Materialize its original scientific/preflight surface; do not execute the current authoring branch's scientific tree. Separately stage the **Git-blob bytes from30643b7**, without text-pipeline rewriting, to:

- `/home/wu/hmasd-inputs/frrie-a05-first-exception-p27/capture.py` from the capture path above;
- `/home/wu/hmasd-inputs/frrie-a05-first-exception-p27/pdb_commands.txt` from the new A05 input above.

Read back those byte digests before dispatch as ordinary staging acceptance. These diagnostic files remain outside the original scientific tree. Preserve P22's source/native binary, original stdin, environment and outputs. No code/input staging into the future scientific cwd or launch occurred during this CM preparation.

## 2. Sole Root command and frozen runtime

| Binding | Value |
| --- | --- |
| Node / supervisor | `hmasd-wsl-node`, `LAPTOP-U9TDKC8A`, `/usr/local/bin/agent-task` |
| Handle | `frrie-a05-first-exception-p27-43eec21e` |
| Fresh detached scientific cwd | `/home/wu/hmasd-worktrees/frrie-a05-first-exception-p27-43eec21e` at original43ee |
| Existing interpreter | `/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python` |
| Runtime | P22 system CPython3.12.3/GCC13.3.0; retained23 installed pins including NumPy1.26.3/Torch2.7.0+cu118; no setup/install/download |
| Diagnostic output | cwd's `temp/directions/finite_resource_relational_inductive_efficiency/exp/a05_first_exception_p27/summary.json` |
| Original learner output | same output root's `learner/`; retain every partial/normal output |
| Adjacent admission | same output root's `learner_admission.json`, original-source preflight joined by `&&` |
| Complete time bound | outer TERM115s plus at most5s grace =120s, including admission/imports/native build/all original work/capture/publication/termination |

After DM's exact binding is committed/pushed, Root passes this entire literal as **one argument** to `agent-task run frrie-a05-first-exception-p27-43eec21e` on the configured node. The supervisor supplies its handle directory for GNU-time output. This is one logical invocation; no fallback/retry/resume/extension or second acceptance attempt is implied by a timeout, missing capture or ambiguous acceptance. Observe/reconcile the same accepted handle.

```sh
/usr/bin/time -f 'process_wall_seconds=%e peak_rss_kib=%M' -o /home/wu/.agent-tasks/frrie-a05-first-exception-p27-43eec21e/process-time.txt /usr/bin/timeout --signal=TERM --kill-after=5s 115s /usr/bin/env -u BASH_ENV -u ENV -u ALL_PROXY -u all_proxy /bin/bash --noprofile --norc <<'FRRIE_A05'
set -euo pipefail
repo=/home/wu/hmasd-worktrees/frrie-a05-first-exception-p27-43eec21e
out="$repo/temp/directions/finite_resource_relational_inductive_efficiency/exp/a05_first_exception_p27"
python=/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python
cd "$repo"
export PATH=/usr/bin:/bin:/home/wu/.local/bin:/usr/lib/wsl/lib
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export FRRIE_A05_HELPER=/home/wu/hmasd-inputs/frrie-a05-first-exception-p27/capture.py
export FRRIE_A05_OUTPUT="$out"
/usr/bin/python3.12 scripts/hmasd_resource_preflight.py admit-memory --out "$out/learner_admission.json" && "$python" -m pdb -c continue -m scripts.run_frrie_b01_contact_r09 --output-root "$out/learner" --admission-receipt "$out/learner_admission.json" --seed 3 < /home/wu/hmasd-inputs/frrie-a05-first-exception-p27/pdb_commands.txt
FRRIE_A05
```

Command binding: read this document's sole sh fence from its published Git blob and remove only the single LF separating the last `FRRIE_A05` line from the closing fence. The resulting command is **1187 UTF-8 bytes, zero CR bytes**, SHA256 **`2976134a5690041fea083bef024aff1e28c92225c4d42479ccca38599893976d`**. Both the outer Bash text and the embedded body passed `bash -n` with exit0/no diagnostics; neither was executed. Helper/input Python syntax also passed non-executing compilation.

The command retains root3, original R09 module/default128-update/checkpoint/uniform/roster schedule, CPU FP32/original FP64 reductions, Torch1/four-worker/native32 and the original build/load route. Both physical/effective memory availability must pass the fresh original preflight's4GiB floor. No extra guard, compatibility probe or source rewrite appears in the command. Missing admission or a failed chain leaves its evidence in place and ends the allocation.

Cost/exposure: P22's61.54s remains the complete-chain anchor, not a recurrence prediction. This A05 has at most one120s critical path/summed invocation wall; actual per-arm times/aggregate CPU/scratch are unknown unless retained outputs provide them. Original maxima are128 paired updates,256 backward/Adam calls,16384 factual episodes/196608 transitions,1261568 training native slots plus55296 evaluation slots, total1316864 slots. Inputs are at most8192 training and512 evaluation tapes. Actual counts remain whatever this chain reaches, not those maxima or zero. Wall/peak RSS are recorded by the existing GNU-time wrapper. No cost pilot or separate setup budget.

## 3. Actual focused acceptance and readback

The **one** allowed stdlib fixture ran from detached committed66106b3 at:

`/home/wu/hmasd-worktrees/frrie-a05-inert-p27-66106b3f2`.

Exact fixture program command:

`/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python tests/experiments/candidates/finite_resource_relational_inductive_efficiency/r09_first_exception_a05/test_capture.py`

The shell supplied `/usr/bin/timeout --signal=TERM --kill-after=1s 24s` around that command, bounding the complete fixture to25s including startup/grace. Fixture subprocess calls separately impose at most10s each. No pytest, conftest, scientific package, native library, tape, model or learner was loaded/executed.

Observed interpreter: `3.12.3 (main, Jul 15 2026, 23:46:41) [GCC 13.3.0]`, executable exactly as pinned above. Fixture exit0, **0.073838544s** measured fixture wall, exactly **2 inert program subprocesses**:

| Inert case | Child wall | Readback |
| --- | ---: | --- |
| Target-like exception with extra intervening frames | 0.038935445s | One module-body traversal, one summary write, complete capture;11 traceback frames,14 coordinates, update7/paired6, per-arm Adam/backward6, training slots29568, `dict_valueiterator`; no missing components/capture errors |
| Normal `SystemExit(0)` | 0.031284294s | One module-body traversal, one summary write, original exit0; `observation=no_active_exception_at_entry_prompt`, `original_exception=null` |

The target-like fixture deliberately compiles synthetic frame identities and raises the builtin TypeError by iterating an inert Field. It tests frame selection and output, not FRRIE or the original failure's cause. All recorded source-shape checks in this ordinary-state fixture were true. Additional in-process inert checks established32-frame truncation/incomplete marking, at most14 dictionary entries,256-character text truncation and bounded huge-integer handling. Unexpected-container/iterator/representation sentinels reported **zero `iter/next/repr/str` operations**; a pre-existing iterator still yielded its first item after a reference read.

After that fixture, final inspection found that an absent `__dataclass_fields__` attribute was being described through the helper's sentinel identity. The in-scope repair at **30643b7359b35c6e9d5751147d0999bc629a966d** adds exactly two helper lines: `if value is MISSING: return {"status": "absent_attribute"}, False`. All other helper bytes, including ordinary/target table handling and termination, are identical to66106b3; the173-byte pdb input is unchanged. The final fixture adds its focused assertion and call only. DM accepted reusing the existing two-child evidence without repeating either child.

Only `check_absent_field_table` from the committed final fixture was then invoked in-process under the same pinned interpreter (`python -`, stdin retained as `absent_attribute_check.py`), using `runpy.run_path` without running the fixture's `main`. It passed, with **zero additional program subprocesses**, 0.019970510s measured wall; combined inert acceptance time is **0.093809054s**, within25s. `absent_attribute_invocation.json`, `absent_attribute_stdout.txt` and remote `a05-inert-3l171rhb/absent_attribute_acceptance.json` preserve that exact command/readback. Final source syntax and remote byte readback also passed. This distinction avoids claiming a second full fixture run or a final-revision rerun of the two pdb cases.

Termination readback was explicit. The target-like stdout contained `Post mortem debugger finished. The fixture_target will be restarted`, then the module-line1 prompt and EOF. Its body marker file still had exactly one line. Normal stdout contained `The program exited via sys.exit(). Exit status: 0`, followed by the line1 prompt, no-active-exception summary and `q`. Its marker also had exactly one line. This establishes the pinned pdb recipe's no-second-body behavior for both inert cases; the actual scientific terminal log still must be checked.

Retained remote fixture receipt:

`/home/wu/hmasd-worktrees/frrie-a05-inert-p27-66106b3f2/temp/directions/finite_resource_relational_inductive_efficiency/test/a05-inert-3l171rhb/acceptance.json`.

Copied raw source/readback/fixture stdout/stderr/summary/marker files and exact local syntax/command receipts live under:

`temp/directions/finite_resource_relational_inductive_efficiency/exp/a05_preparation_p27/`.

`static_acceptance.json`, `static_acceptance_66106b3.json`, `remote_source_sha256_30643b7.txt`, `fixture_invocation.json` and `fixture/acceptance.json` identify the inputs and checks. No repeat smoke is needed before the scientific dispatch. Source staging initially encountered the node's non-login network route and an existing nested remote-tracking ref collision; configured `zsh -lic` and `git fetch --refmap= origin codex/frrie` completed retrieval without pruning/renaming any unrelated ref. Those failed staging commands launched no fixture or scientific program.

## 4. Capture interpretation and remaining boundary

The helper's standalone namespace performs only bounded reads. It records at most32 traceback frames,14 named address coordinates and at most14 entries per ordinary field table; unexpected containers are described without custom iteration. The fields-frame object/table identities and generator `.0`/optional `f` identities remain available for comparison. Original locals are not assigned or traversed as unrestricted graphs. Missing/ambiguous frames and failed reads are separate from explicit structural mismatches. A helper read failure is recorded separately from the original exception; a hard/publication failure remains an inconclusive boundary with its log retained.

`capture_complete` describes availability of the exception-state record, not scientific validity or a final A05 branch. DM applies card §3 to the actual exception, state/type/identity record and termination evidence. A normal-entry `no_active_exception_at_entry_prompt` record is separate from post-mortem capture; its false `capture_complete` means no exception was captured, not that a normal program necessarily failed. Original normal completion must be established from its retained log/outputs. An entry prompt alone, or debugger/supervisor exit0, never establishes scientific success.

The live P22 cause and future A05 state remain unknown. No snapshot reconstructs the writer of malformed state, clears P22, proves Python/native/host causation or grants R09 a result. P22 remains `R09_INVALID_INCOMPLETE` with unknown actual optimizer counters and conditional evaluation lower bounds. A05's DM prediction/reading rules, original R09 MEI0.005 and historical outcomes are unchanged.

Scope:284 new helper lines plus2 input lines;200 test lines are separate. No new runner, scientific source edits, framework, retry machinery or standing observer. The only scope-spec §4 item is the card §2/§5.5 named reuse of existing optional pdb exception-state observation. The three CM comparison batches are complete; this is new bounded diagnostic coding after enrollment ended, not relabelled collection, and no extra arm/child was created.

**Next owner:** DM accepts and freezes the exact code/input/command bindings; Root then dispatches/observes the one specified chain. On Root's terminal receipt, reuse this CM for collection/E0, then DM intakes the registered rule. Until that accepted dispatch, actual scientific invocation count is **zero**.

scope: none
