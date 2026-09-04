# MGTAP B02 technical evidence

## Engineering contract before implementation

The assigned observable is the finite-training normalized return curve of the
existing METRIC/INTACT and FREE/INTACT actors on N=4/8. Acceptance requires the
card's actual learner, paired tapes, complete update/checkpoint measurements,
counts, ordinary publication, and separately measured cost pilot. Technical
acceptance establishes implementation conformance, not geometry-specific efficacy.

Source baseline: science-card commit `22ae3de13064ace946d58ed337269bca1fd9f546`.
CM worktree: `C:/Projects/HMASD-worktrees/cm-n5-b02-20260904`, branch
`codex/cm-n5-b02-20260904`; initially clean. Implementation uses a separate
`impl-n5-b02-20260904` worktree and branch. Owned source is only the new
`mgtap_b02_curves/` package, its mirrored tests, and
`scripts/run_mgtap_b02_curves.py`. This document and B02 result evidence are CM
owned. The card, intake, owner/audit records, old primitives, configuration,
Portfolio and tracker table are outside this slice.

Protected contract: 60 float64 CPU parameters; one thread; zero initialization;
SGD learning rate 0.1, momentum and weight decay zero; existing score maps,
features, logit clip, exploration mixture, legal autoregressive action support,
entropy, gradient clipping, reward, and loss normalization. Every update uses
the complete N=4/8 factorial: 48 episodes, 96 allocation transitions and 576
agent steps. No oracle value or utility enters policy inputs or learner labels.
New B02 phase addresses pair training tapes and presentation permutations by
seed/update/N and evaluation tapes by seed/population row, independently of arm
execution order and checkpoint. The old C registered phases and activity marker
are never invoked. There is no recurrence or resume state in this object.

The production chain is public demand/roles -> paired presentations/tapes ->
unchanged Actor and legal decoder -> unchanged native reward -> REINFORCE loss
and SGD -> retained update measurements and checkpoint parameters -> fixed-panel
evaluation -> episode arrays and summary. Actor owns W/V and fixed B; tapes are
ephemeral inputs indexed outside actor state; oracle outputs are diagnostics.
The old trainer owns a registered-activity side effect, so B02 must not call its
group creation/fit path. Its formulas are reused in the new bounded loop.

Non-goals: old C reopening, stationarity selection, tuned baseline selection,
CUT controls, metric-specific causality, held-out population transfer, GPU or
cross-host bit identity, efficacy or lifecycle decisions. The competing
predictions are generic conditioning with little aggregate difference, positive
METRIC curve separation, or a conditioning disadvantage favoring FREE.

Engineering scope section 4 additions: **none**. Existing agent-task and memory
preflight are reused externally. No new distributed execution, resume/retry,
lease/heartbeat, provenance guard, incident tree, schema/registry/abstraction,
compatibility machinery or resource telemetry beyond wall time and peak RSS.
Required gradients, displacement, parameters and returns are learner measures.
Budgets: <=2,000 new research lines, <=600 runner lines, <30% orchestration,
one toy publication smoke and rule tests under five minutes.

## Prospective execution and cost boundary

Only the named pilot is presently authorized: seed 1907, both arms, 16 updates,
evaluations at 0/16, 16 tapes per each of 24 episodes at each N. Each pilot arm
stops at the next update/evaluation boundary after 30 seconds; shared setup/oracle
has 60 seconds. Preserve partial output if a cap is reached. Pilot observations
are B-development data and excluded from the main estimand.

The prospective execution node is configured `wsl_4070` via SSH
`hmasd-wsl-node`; exact pushed source is used in a detached remote worktree.
Interpreter: `/home/wu/.venvs/hmasd/bin/python`; observed dependency versions:
torch 2.7.0+cu118 and NumPy 1.26.3. The computation stays CPU float64/one thread.
Windows/Linux CPU portability is declared in the card; cross-host bit identity
is not claimed. Local fallback requires no accepted remote process and fresh
local admission. Output will be under the direction's `temp/.../exp/` root.

Per-arm cost projection is measured from this named pilot, before any main run:
`P_A = 2 * 3 * (256*u_A + 17*e_A)`, where u is seconds per complete update and e
seconds per complete N=4/8 evaluation panel. Shared setup is separate. The DM
must accept the measured projection within 300 seconds per arm before the main
panel is launched. Main seeds remain 203/211/223, each with 256 updates and the
17-point grid; no seed, treatment, threshold or stop rule changes from pilot data.

Post-learner path coverage: this new object will have one end-to-end toy test
that reaches the same summary/array publication path. Full main aggregation is
tested with synthetic complete-grid packets and rule boundary cases; this does
not constitute a main learner observation. There is no prior failed B02 attempt
requiring offline publication reproduction.

Owner review read at the initial clean boundary returned an empty list from
`tools/owner_console/item.py reviews --json` on the primary control checkout.
## Implementation and focused checks

Implemented 375 research lines: package initializer 1, numerical.py 130,
reporting.py 77 and runner 167; mirrored tests add 145 lines. Unchanged Actor,
decoder, environment, oracle and config primitives remain the numerical route.
The old RNG helper is reused with new `mgtap_b02_training`,
`mgtap_b02_training_episode_order` and `mgtap_b02_evaluation` phase tags. Evaluation
rows batch by N while preserving pair/load/epoch/tape addresses. Outputs retain
each loss, preclip gradient norm, step displacement, cumulative path length,
distance from zero, evaluation parameters and individual episode returns.

Main invocations require `--oracle <pilot/oracle_returns.npy>`: the DM explicitly
confirmed read-only reuse of this pilot-produced deterministic diagnostic. Each
invocation measures setup independently; CM accounts for their cumulative
60-second bound. This input never reaches the actor or learning loss.

Implementer ran the eight numerical/rule cases once: **8 passed in 2.07 seconds**.
The same invocation's smoke fixture could not create its basetemp because the
parent directory did not exist; the runner did not execute. After creating that
local parent, the previously unexecuted smoke passed: **1 passed in 7.20 seconds**,
runner wall 3.026 seconds. No source change occurred between these checks.
Commands used the configured local conda interpreter, `-m pytest -q -p
no:cacheprovider`, the mirrored B02 directory, and basetemp under the direction's
`temp/.../test/` root; the second invocation selected only
`test_curves.py::test_toy_runner_publication`.

The smoke reaches both arms, nonzero updates/gradients/displacement, oracle,
evaluation arrays and summary publication. Numerical cases establish complete
factorial counts, inherited loss equality, batched evaluation versus addressed
blocks at 16 tapes, exact cost formula, ordered branch thresholds and incomplete
panel suppression. The static exposure and count calculation matches the card:
main per arm/seed 256 updates, 24,576 training transitions, 147,456 training agent
steps, 13,056 evaluation episodes, 26,112 evaluation decisions, and 156,672
evaluation agent steps; maximum SGD path budget 128 against unit reference 1.

Independent reviewer `/root/dm_amx_n5_allocation/cm_ah_n5_b02/rev_axh_n5_b02`
inspected final source/tests and found no material numerical, RNG, comparator,
count, rule or cost discrepancy and no unrequested section-4 machinery. This
was independent inspection, with no duplicate runtime test. The full main
learner grid and main `--oracle` CLI are not exercised by the toy smoke; full-grid
aggregation uses synthetic packets. The actual pilot provides the next runtime
observation. No test establishes scientific efficacy or cross-host bit identity.

Windows smoke peak RSS was unavailable (`resources_unmeasured`): the implementer
reproduced the missing optional psutil import. No package was installed. Linux
uses standard-library `resource.getrusage`. Missing resource telemetry alone
does not invalidate this non-resource claim.

## Frozen pilot command before remote preparation

Node `wsl_4070`; supervisor `/usr/local/bin/agent-task`; exact pushed launch SHA
and accepted handle are recorded below after Git integration. Prospective cwd
is `/home/wu/hmasd-worktrees/mgtap_b02_20260904`. Output is
`temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_pilot_1907`
under that cwd. The single supervised command is:

```text
cd /home/wu/hmasd-worktrees/mgtap_b02_20260904 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_pilot_1907/admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_mgtap_b02_curves.py --mode pilot --seed 1907 --out temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_pilot_1907
```

The exact source worktree will also run the focused suite once before launch.
Only after that and fresh adjacent node admission does the pilot execute. This
is the same carded pilot, with no main arm or alternative configuration launched.
