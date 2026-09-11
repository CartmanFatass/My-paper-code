# VSP03 B03 technical source acceptance

Implemented the selected single-G driver and matching seed5 runner in the existing
shared direction checkout/branch, starting clean at6d45dee87753a0f3f0fe82cf4c2b68524f3aa45c.
DM owns scientific intake; this record concerns source conformance and execution facts.

B03 imports unchanged B02 Model/worlds/action_tapes/rollout/metrics/difference and B01
objective/vectors/scales/write_json/peak_rss. No B01/B02 byte changed (git diff exit0).
The driver constructs G once with arm index1, trains128 batches then evaluates G greedy,
G stochastic, R and R0 once each on identical1024-world inputs. Greedy G minus R0 is primary;
all five selected contrasts retain sample SD and conditional-world SE. One independent
training instance is recorded, never a T/G training pair. The old fixture is absent.

State ownership remains B02's per-rollout arrays; evaluation shares immutable draws/phase.
Models/optimizer live within the one run, with no replay, recurrent state or resume.
Float64 PCG64 worlds and float32 public observations/CPU learner stay unchanged. Direct-b,
shared team credit, actual valid rows, entropy schedule and real Adam remain inherited.

Checks: local scientific Python3.10 with -B, pytest -q -p no:cacheprovider
--basetemp temp/directions/vsp_03/test/b03_cm_20260908
 tests/experiments/candidates/vsp_03/vsp03_b03/.
First check had2 passed/1 setup error because the basetemp parent did not exist (1.86s).
Created that parent; corrected invocation:3 passed in1.79s. AST/compile checks also pass.
The tests use static source connections and two literal endpoint values, with JSON readback;
zero models, RNG draws, rollouts, training or evaluations were executed. They establish
changed wiring/primary helper behavior, not runtime endpoint existence or performance.

Automatic approval review rejected removal of the invocation scratch directory as
"blocked by policy". Its exact retained path is
C:/Projects/HMASD-worktrees/dm-vsp03-p07-prep-20260907/temp/directions/vsp_03/test/b03_cm_20260908.
The rejected action was native PowerShell Remove-Item -LiteralPath $scratchPath -Recurse -Force
after Resolve-Path and an exact absolute-path equality check. The tool gave no fixable
path-verification reason. CM retains cleanup responsibility when policy permits it; no other scratch
or scientific evidence was touched. This is a tooling fact, not a scientific result.

Scope before writing: card section7 explicitly requests none of scope-spec section4's
optional machinery. None added: only small driver, runner, tests and records. Driver128
lines and runner28 lines are below2000/600; independent review checks scientific meaning
and unnecessary orchestration. No profiler, pool, guard, registry or recovery layer.

See [launch boundary](VSP03_B03_LAUNCH_BOUNDARY_20260908.md) for the complete command,
per-arm cost projection and post-learner path coverage. Configured remote supervisor help
was reachable (its usage response exits1); this was no admission or scientific invocation.
The exact launch Bash block passed remote bash -n via stdin (exit0), without execution.
Independent [source review](VSP03_B03_SOURCE_REVIEW_20260908.md) returned no material
finding. CM accepts this source for the selected contract; DM source intake precedes
the sole source-bound launch. No run yet.

## Executed source and collection

Accepted source4eb8a36b9184633f5e28eff999a99f2dbc948040 was pushed and DM's changed
comparison intake was committed at215849916 before launch. Configured zsh -lic
successfully staged its clean exact-SHA remote worktree. An earlier source-only fetch
without that network shell hung; its identified Git processes were terminated before
successful staging. No scientific construction/admission occurred in that repair.

The sole invocation published primary/count/weight outputs; see
[VSP03_B03_RESULT_EVIDENCE_20260908.md](VSP03_B03_RESULT_EVIDENCE_20260908.md).
Root recorded the accepted handle and terminal observation, then returned collection
to this CM. Direct artifact readback is accepted; numeric supervisor exit is unavailable.
The generated wrapper evaluates the payload containing top-level exec /usr/bin/time,
which replaces the wrapper before its exit-code/footer publication. This explains the
missing receipt from inspected source; it does not supply an observed exit0. No source,
supervisor or payload repair, second invocation or additional evaluation was attempted.
