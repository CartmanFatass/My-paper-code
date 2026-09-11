Claim: In one fresh N7 training pair, placing native service return in its six occurrence intervals may improve final recovery over the same MAPR learner receiving only terminal return.
Binding MARL structure: (a) agent-count scaling or roster change; temporal allocation of shared team credit after a single member loss is the selected intervention.

# VNFC-N7-NATIVE-SERVICE-CREDIT-B02 — B/EXPLORE

## Decision, question and identity

Selected by [Convergence sections III–VI](pro_packets/20260910_native_service_credit_reentry/archive/RESPONSE.md)
at `10bb08476ff58afd25b90b21cd2d1a739b25ca4b`, accepted in
[re-entry intake section 9](VNFC_NATIVE_SERVICE_CREDIT_REENTRY_INTAKE_20260910.md#9-reconciled-full-response-and-direction-decision--2026-09-11).
One new training pair only. Seed `2026091101`, evaluation seed `2026091102`, namespace
`VNFC-N7-NATIVE-SERVICE-CREDIT-B02-20260911`; no old model, optimizer or scientific RNG state.
These identities are selected before any question-relevant output, without seed screening.

Question: does INTERVAL yield enough native recovery benefit at the matched budget to
justify later selecting this recipe again? The containing null is the actual TERMINAL
MAPR-4 learner. Both start from identical fresh 89,090-parameter tensors, with independent
optimizer storage. Execution inputs, action grammar, network and optimizer settings match;
training-label time information intentionally differs. DIRECT is historical evidence,
not a third arm. Fixed BCRH is a native reference, not a proven same-information upper.

Headroom: no tuned same-information baseline/upper pair on this host. Old MAPR–BCRH gaps
of roughly .04–.06 motivate a new absolute MEI of `.02 R_fail_60`, chosen with knowledge
of those outcomes. The old B01 `.10` remains unchanged. No compatible tuned baseline
package has been established; reuse the already competent TERMINAL update and BCRH path.

## Treatment and protected native path

Use the original two-zone, one-loss post-loss N=7 host, 120 prehistory ticks followed by
120 post-loss ticks, six decisions of 20 ticks each. Preserve surviving entity identity,
canonical opaque-rank presentation, legal masks, fixed occupants, physical command mapping,
role acquisition/travel, failure event and public observation. No join/rejoin/replacement,
truncation, new memory or changed time scale. The shared policy co-adapts through PPO;
the question is not individual causal agent credit or recurrent roster-state management.

Own trajectory counters at reset and six endpoints are `F_j,T_j`, j=0..6, initially zero.
Terminal positive demand denominators `D_F,D_T` are exogenous but used only after full
collection. INTERVAL labels are
`r_j=.5*(F_(j+1)-F_j)/D_F+.5*(T_(j+1)-T_j)/D_T`, j=0..5.
TERMINAL labels are `[0,0,0,0,0,J]`, `J=.5*F_6/D_F+.5*T_6/D_T`.
Failed-zone counters freeze after j=3 (60 s); total counters continue to j=6 (120 s).
The six INTERVAL labels sum to the same complete native J. Do not average interval ratios,
drop later total service, add shaping or change weights. Both arms retain the same kinds
of native snapshots; neither sends future denominators to actor/critic or updates mid-episode.

Complete data flow: member loss -> surviving entities/role obligations -> public observation
and four-token joint assignment -> native interval service -> own-trajectory credit labels ->
six-step GAE/PPO -> changed parameters -> fresh complete native evaluation.

Keep gamma=1, lambda=.95, terminal next value/advantage zero, detached old values/targets.
`delta_j=r_j+V_old_(j+1)-V_old_j`, `A_j=delta_j+.95*A_(j+1)`, `Y_j=A_j+V_old_j`.
Construct unnormalized critic Y before normalizing actor A; retain original zero-variance
behavior. PPO: four epochs, eight minibatches of 24 joint decisions, clip [.8,1.2],
value coefficient .5, entropy .01, global gradient clip .5; AdamW lr3e-4,
betas(.9,.999), eps1e-8, matrix decay1e-4/vector decay0. Use own sampled commands for replay.

Reuse addressed HMAC derivation and canonical Stiefel initialization through the existing
N7 helpers, with the new namespace and seeds. The inherited RNG prefix is a derivation
label, not old state. Training worlds pair between arms per round; fresh evaluation
worlds pair across arms/checkpoints. Action and minibatch streams are arm-specific.
Model and optimizer storage are separate. No model draws occur in the non-environment tests.

## Exposure and primary measurement

Machine-derived counts and historical displacement are in
[EXPOSURE_AND_COST.json](pro_packets/20260910_native_service_credit_reentry/EXPOSURE_AND_COST.json):
the fields marked proposed/unselected there are historical proposal state; this card
selects those exact counts without changing the original file.

Exposure line: 1 training pair, 2x89,090 parameters; each arm 64x32=2,048 complete training
episodes /12,288 joint transitions /2,048 backward and optimizer steps. Combined:
4,096 training +384 policy evaluation +64 reference=4,544 complete episodes;
1,090,560 native ticks including prehistory; 4,096 optimizer/backward calls;
768 collection forwards, 4,096 optimizer forwards, 36 evaluator forwards, 384 full BCRH calls.
The 2,112 unique exogenous fixtures are not 4,544 independent worlds. Historical same-size
MAPR displacement/initial L2 was .292124/.304535; new movement is unmeasured until this run.

Each round has 16 worlds per failed zone. The fixed 64-world panel has 32 per zone;
evaluate each policy greedily at rounds 0/32/64, fixed BCRH once. Round64 is the only primary.
Primary: mean paired final `INTERVAL - TERMINAL R_fail_60` over all 64 worlds.
Retain each arm's final-minus-initial and BCRH difference; all J_ext/U_total/U_intact,
zone1/zone2 results, safety/exclusivity violations and existing 20-second recovery context.
Conditional paired world SE does not estimate training-seed population uncertainty.

## Reading rule and prediction

Read the final comparison, learning gains and native tradeoffs together. (1) Recovery
gain >=.02 with nonnegative full-J difference and no concealed intact/zone loss is a
usable local signal; recommend considering a separately selected independent pair.
(2) Recovery improves with adverse J/intact/zone movement: mixed native tradeoff, not
cost-free improvement. (3) Small/mixed/uncertain recovery difference: describe amplitude,
cost and conditional uncertainty; inside ±.02 is not equivalence and earns no automatic
seed extension. (4) TERMINAL better, especially on recovery and J: evidence against this
recipe at this budget, preserving that narrow adverse result. Any invalid primary limits
only its dependent claim; credible partial facts remain. All outcomes end this allocation.

How the result will be interpreted: above MEI may justify another decision, inside MEI
may offer little further decision value, opposite sign argues against this recipe.
The rule does not require every world/zone to agree or statistical significance.
DM prediction: both arms learning is more plausible than a >=.02 INTERVAL advantage
without native cost; low confidence in the primary sign. Owner prediction: not taken
(unattended). No stable superiority/equivalence, unique credit cause, pure variance reduction,
Markov-label theorem, optimality, cross-N/repeated churn/UAV transfer or deployment claim.

## Complete budget and host

Exactly one accepted scientific invocation: `T_native<=600 s`, `T_support<=300 s`,
`T_native+T_support<=900 s`. No second accepted invocation, pilot, calibration, extra
arm/panel/checkpoint, retry, replacement or automatic successor. No historical balance transfers.
Native includes imports/build/init, both complete learners, every selected evaluation,
BCRH, checkpoint/result construction, publication/readback and process exit. Support includes
actual preparation, necessary focused checks, committed source staging, admission, Monitor
commands, collection/readback and closeout. Nested clocks are not double-counted; deliberation
and idle queue/network time are separate. Missing support timing leaves full-cost conformance
unestablished. A cap failure does not make a scientific negative or permit shortening science.

Per arm planning: `2048*c_collect +64*c_update +192*c_eval + delta_new`;
historical MAPR term170.3534712763 s, two MAPR plus shared/reference/publication
400.2884091133 s. New counter/target/output costs and current-machine variation are unknown.
Old complete walls306.68/388.75 s are planning inputs, not new measurements or upper bounds.
No prospective exact cost proof or calibration is selected. Existing complete cost law is
retained per actual arm; the 600 s total is not a per-arm allowance.

Execution is pinned to configured `wsl_4070`, CPU float64, one computation thread and the
unchanged single-process native batch path. No local fallback is selected. Use detached
exact committed/pushed SHA worktree and existing `agent-task`; fresh physical/effective
memory>=4 GiB admission on that node immediately precedes the invocation with `&&`.
Use the existing supervisor timeout for this complete invocation; no new restart machinery.
DM sends MONITOR_ADD to the live primary-control config endpoint, then stops routine polling.

## L0 implementation and acceptance

Goal: the one exact comparison above, readable in summary.json and its episode/curve outputs.
Owned checkout `C:/Projects/HMASD-worktrees/codex-vnfc`, branch `codex/vnfc`; baseline response
HEAD `10bb08476ff58afd25b90b21cd2d1a739b25ca4b`. Owned new code:
`experiments/candidates/variable_n_fleet_churn/native_service_credit_b02/learning.py`,
`scripts/run_vnfc_native_service_credit_b02.py`, and mirrored tests. Reuse N7 B01's native,
collector, PPO, checkpoint and publication functions; extend only its `learning.py`
and `experiment.py` for snapshot collection, supplied targets and two selected arm names.
Their existing defaults preserve the historical runner. No native or core change is needed.

Shapes/lifetime: per round 32x6 joint transitions, six public-input tensors; per episode
7x4 integer counter snapshots `[fail_delivered,fail_demand,total_delivered,total_demand]`.
The counters live beside rollout records, outside model inputs. Targets are detached float64
32x6 arrays. Rollout tensors are discarded after the round, checkpoints carry separate model/
optimizer state. Summary and native rows are the publication consumers; no resume path.

Acceptance: focused non-environment targets/counter/readout check; inspect original TERMINAL
recursion, interval normalization, 60/120 boundary and behavior-input separation. Independent
Astra/high read-only review covers changed reward, initialization, RNG and publication.
Actual run must expose both learners' real nonzero transitions/gradients/updates/movement and
readable primary counts. Native counter/physical consequences use the accepted path and the
formal run, not an additional environment check. Tests share the 300 s support allowance and
clean their own temp directory. Source<=2,000 new non-test lines; runner<=600; no E01 exception.

Engineering Scope section 4: needs no new machinery. Reuse existing checkpoints, JSON
readback, wall/RSS reporting, detached supervisor and Monitor. No new guards, provenance
system, diagnostic service, retry tree, registry or full-history replay is introduced.
On a concrete semantics or budget conflict, retain evidence and return it without replacing
the selected intervention. DM owns technical acceptance, collection/intake and scoped cleanup;
Root integrates accepted commits and confirms retention/reclamation. No current run exists.
