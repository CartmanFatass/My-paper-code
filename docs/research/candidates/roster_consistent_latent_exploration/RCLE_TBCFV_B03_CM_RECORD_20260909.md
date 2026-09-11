# B03 actor100 implementation and execution record

CM owns the shared `codex/rcle` checkout at
`C:/Projects/HMASD-worktrees/dm-rcle-a02-20260906`, starting clean at
`9c729fb7b675c3d21b35815fa7e46cf6444fa3af`. No historical source changed.
Contract: [frozen card](RCLE_TBCFV_B03_ACTOR100_SCIENCE_CARD_20260909.md) §§2–8.

## Implementation and focused acceptance

New B03 study computes the actual stopped-advantage weighted score loss, keeping separate
episode manager/claim means. It calls the existing batched rollout with true package FLEX
for both weights, reuses B02's full-vector norm0.02 step and subsequent eight-cell baseline
update, and publishes W1-minus-W100 paired primary on the two AC change paths. The unchanged
host supplies public inputs, event derivative/stochastic stops, native demand and held-out
panels. Exogenous semantic addresses contain `cell`, supporting independent cross-path
scenario domains; no training-population uncertainty is inferred.

Existing common initializer allocates six models per learned invocation: one initializer
plus five copies. One FLEX copy trains, five are untrained helpers. Both invocations derive
the same common initial tensor from seed19; initial state dictionaries are retained for
direct comparison. W1 evaluates shared FLEX initialization once. No B01/B02 law is edited.

Focused command (local CPU FP64, no native simulation):
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/roster_consistent_latent_exploration/test/b03-focused-20260909 tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b03/test_b03.py`.

| Invocation | Complete command wall s | Outcome / technical exposure |
| --- | ---: | --- |
| First | 8.0271331 | Fixture setup parent directory absent; zero models/backwards/steps |
| Second | 3.2509898 | Expected fixture norm omitted four manager bias components; one explicit model, two backward calls, two joint step calls |
| Corrected | 3.0972877 | 1 passed; one explicit model, two backward calls, two joint step calls |
| Total | 14.3754106 | Two technical models, four backward/step calls; zero scientific episodes or RNG/native states |

The corrected check establishes lambda1 control limit, actual lambda100 algebra, stopped
return/baseline/old plan/noise, live current deterministic FLEX event-head derivative,
full-vector step magnitude, eight-cell baseline values, actual training caller's FLEX
argument and balanced block, primary sign/pairing/mismatch rejection, and JSON publication
readback. It does not establish native performance. An existing pytest `cache_dir` warning
is unrelated. No extra smoke, simulation or diagnostic is scheduled.

Independent read-only semantic reviewer `rev_ah_rcle_b03` inspected source, inherited
RNG/event boundaries, runner and focused test; no material scientific defect found.
Reviewer found the same four-component fixture expectation defect (corrected), requested
the configured interpreter via `HMASD_PYTHON` (applied), and excluded unused CPU fields
from new time records (applied; aggregate CPU will be unmeasured). External `/usr/bin/time`
is authoritative for complete invocation costs including import and all publication;
summary `wall_seconds` is an internal pre-final-write prefix. CM also makes every fixed
preflight-and-run line explicitly exit on failure, including a failed left side of `&&`.

Post-learner publication coverage: focused synthetic primary plus the same JSON writer
was exercised and read back; no dependency on the historical B02 publication failure.
Engineering scope §4 additions: none per card §7. New source is below2,000 lines,
Python runner below600; final exact counts are recorded at technical collection.

## Frozen execution and costs

Per-arm cost projection reuses the card's count-matched B02 complete-path evidence:
W1 71.47s (source comparator included shared init), W100 71.23s, reference2.62s;
new-law/startup costs unknown until this allocated execution. Each projection is below
600s. Both actual packages are FLEX. No new pilot or deleted scientific arm.

Node `wsl_4070`, CPU FP64, one compute thread. Exact committed source will be in detached
`/home/wu/hmasd-worktrees/rcle-b03-actor100-20260909`; no device/node fallback.
Output root is that checkout's
`temp/directions/roster_consistent_latent_exploration/exp/b03-actor100-20260909`.
Handle: `rcle-b03-actor100-20260909`; CM is sole observer. Following app restart, supervisor
returned `not_found` before any submission; no accepted process or scientific exposure.

Exact fixed scientific command list: `scripts/run_rcle_tbcfv_b03.sh <launch-sha> <out-root>`
with `HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python`. Each line joins fresh same-node
memory admission to its runner with `&&`, then exits on failure. W1, W100 and reference
run sequentially; W1 failure prevents W100. Every interpreter is capped at600s through
publication. Whole command list will run under `timeout 1450`, with external whole-chain
wall/RSS/exit output. Adding14.3754106s checks leaves35.6245894s reserved within1500s for
bounded collection analysis/publication; no cap reset. Git/SSH/staging/agent work is outside
execution timing, reported separately as unmeasured per runtime specification §2.
Native compilation, if needed, occurs inside the charged W1 invocation. Normal completion
is400backward/step calls,25,600training episodes and four2,048-episode evaluation panels.

## Preserved cleanup blocker

Automatic approval review rejected both the initial combined test/cleanup command and a
later isolated `Remove-Item -LiteralPath ... -Recurse -Force`, with `blocked by policy`.
The combined rejection occurred before any test. The exact owned scratch remains at
`C:/Projects/HMASD-worktrees/dm-rcle-a02-20260906/temp/directions/roster_consistent_latent_exploration/test/b03-focused-20260909`.
CM inspected its resolved path and did not bypass or repeat the rejected removal.
DM acknowledged the blocker; Root receives it with final integration facts.
Remote execution checkout is retained until Root's explicit integration/closeout trigger.
