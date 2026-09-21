# VSP-03 research notebook

## 2026-09-21 — independent DM adoption and opportunity-rule comparison

Owner explicitly reopened this direction with B and C and authorized research execution.
This task is the direct DM for `vsp_03`, not a Root or a child DM. Native task
`01a0c347-9e60-77f1-b503-46ed4f80b314`, host `local`, authoring checkout
`/home/fires/.codex/worktrees/e481/hmasd-wsl`, branch `codex/vsp03-opportunity-rule`.
No inherited live experiment or uncertain send was assigned. No App message, reporting
loop or acknowledgement to another task is authorized. The owner-selected shared
activation is being published separately; until native canonical registration is present,
this task continues reading, design and implementation but launches no result-bearing run.

Adopted the current constitution, the direction-manager developer-instructions body,
`hmasd-scientific-tools` and `hmasd-research-engineering`. Actual session settings are
the runtime's settings. Fits record cost, with no allowance or old running window.
Historical records retain their original meaning and are not rewritten.

### Evidence adopted and present judgment

Read the complete Portfolio Pro Answer and Decision at
[`b6093d211fa33a81d05d490ffa5bc920f43605eb`](https://github.com/CartmanFatass/My-paper-code/blob/b6093d211fa33a81d05d490ffa5bc920f43605eb/docs/research/RESEARCH.md#portfolio-review-2026-09-21-closed-direction-research-value),
the direction record at `e130c1cdabae114ab98948f28f437167847e9a9e`, the B06/B07
result evidence and the actual B02/B06 source. B06 final-512 G−R0 is
`.02599609375 / .0145068359375 / .0096875` (mean `.016730143229166668`);
B07 final is `.0115673828125` with 128→512 `−.0016064453125`. The positive
endpoint observations survive. Stable strong superiority, monotonic training improvement,
UAV benefit and a special decentralized-MARL mechanism are not established. The old
initialization and shorter-training adverse evidence remains contrary evidence.

Reuse the complete Pro advice for this decision: fixed 512-update ordinary G versus a
competent transparent opportunity rule O, retaining R0/R; evaluate complete team J and
cost components; accept a useful ordinary rule as an answer. This advice covers the
question, comparator and development comparison, but not a future confirmation plan.
The owner's simultaneous activation supersedes the review's old pending-selection prose.

Verified interface: two public targets, 40 transitions, alternating two-tick clocks through
t32, each target's clock every four ticks. SUBMIT is legal even when not ready and commits
eight ticks whether successful or not. Success requires presence after all eight service
transitions. Native per-job units are `200*success −10*attempt −waiting_ticks`, team
J is their sum /400. Fourteen actor features contain current time, own and partner
presence/age/armed/expired/ready, partner pending, clock parity and next partner clock.
No future random tape is a policy input. The armed/expired/ready latches affect R0/R,
not the physical service success law. A t26 submission removes the partner's t28 and
t32 opportunities. Blocking is an observed scheduling event, not by itself a causal error.

Working hypothesis: much of G's gain over readiness can be represented by a finite-horizon
public opportunity calculation. Own survival and waiting trade against the value of the
partner's delayed or removed next/last opportunity. Strongest simpler explanation is a
good single-job timing rule without a material shared-slot correction. The discriminating
comparison therefore includes a same-model single-job diagnostic. A reduction in last-clock
blocking without J improvement does not count as a successful mechanism explanation.

### L0 — fitted public opportunity rule and B08 runner (before code)

Deliverable: one new disposable `experiments/candidates/vsp_03/opportunity_b08/`
module, `scripts/run_vsp03_opportunity_b08.py`, and mirrored focused tests. Preserve all
historical code, especially B02 rollout and B06's G model/objective/Adam/512 updates.
No FSD, B or C code/notebook/run edits. DM owns this notebook and the runner; an optional
Implementer may own only the new opportunity model/planner and its tests. An independent
Reviewer checks scientific semantics, observation rights, numerical recursion and admission
before launch. No helper launches experiments or edits this notebook.

Planned O: fit an explicit two-parameter age-dependent transition family from the **same
eligible 14-feature observations produced by G's training**, grouped by episode and mapped
back to physical target identity. Presence departure hazard `1/(age+c)` and absent return
probability `p` are estimated, not read from environment constants; declare the age-Markov,
independent-target family as O's structural modeling assumption. Consecutive observations
separated by delta ticks contribute their multi-step endpoint likelihood; no latent
intermediate transition, future draw, evaluation observation or service outcome is supplied
to this fit. G and O have the same raw observation/reward access; the algorithms consume
that data differently. This is not an equal-compute comparison or a claim that model
structure is free. O's fitting/planning work and structural assumption are reported.

O solves the finite-horizon WAIT/SUBMIT recursion for full remaining team units under that
fitted model. At a free eligible clock, WAIT moves two ticks if both jobs are pending;
SUBMIT costs 10, earns 200 times eight-step survival, and blocks the partner until its
clock t+10 (if any), regardless of success. One-pending-job WAIT advances four ticks.
All intervening pending-job waiting and horizon non-submission costs are included.
Readiness is not an action mask. `O_self` uses the same fitted survival/model but chooses
from the single-job recursion, ignoring partner opportunity loss; it is an attribution
diagnostic, not a competent primary baseline. `O_known` uses the actual transition
parameters solely as an explicitly extra-model-knowledge diagnostic, never the primary.

Checks: literal service-survival cases; independent recursion on late-horizon cases,
including failed submission occupancy and final clocks; observation-to-identity mapping;
no future/evaluation leakage; native units and per-job components; unchanged G update
exposure; fail-closed admission and SHA identity; runner output/count/readback coverage.
Synthetic test fixtures do not provide scientific scores or tune the study.

Initial cost design (not yet a launch declaration): three fresh independent blocks,
G 512 updates ×128 complete episodes per block; three G fits and three fitted-law O fits.
R0/R/O_self/O_known require no optimizer training. No hyperparameter or checkpoint search.
Fix actual seeds, evaluation panels, likelihood optimizer and exact work counts after the
implementation is reviewable, before any result. Development interpretation only; a later
confirmation would need its own claim note, fresh seeds and Pro criticism of the actual plan.
First concrete next step: implement the model likelihood and two-job recursion while the
DM builds the admitted runner around the unchanged G learner and reads shared registration.
