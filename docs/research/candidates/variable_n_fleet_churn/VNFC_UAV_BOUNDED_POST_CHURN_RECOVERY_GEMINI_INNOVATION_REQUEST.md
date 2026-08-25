# Independent innovation request: bounded UAV post-churn recovery

You are advising one prospective scientific definition. This is an independent
innovation review, not mathematical closure, code review, feasibility
acceptance, portfolio ranking, or permission to run an experiment.

## Frozen target and question

The public target is a two-zone UAV surveillance/relay mission. Each zone has
one physically exclusive executor volume and one transparent single-user relay
volume. UAVs move on a fixed deconflicted corridor graph; commands occur every
20 seconds; service acquisition takes 6 seconds and relay acquisition 4 seconds;
energy reserve, clearance and exclusivity are hard constraints. Demand and
obstruction evolve by fixed public Markov laws. At `t=0`, one acquired executor
fails without warning, leaves the controllable roster, and creates a 20-second
physical clearance lock. No other membership event occurs.

The new experiment trains one shared policy only at post-event rosters
`N in {3,5}`, freezes it before any held-out use, and evaluates fresh post-event
`N=7` worlds. Pre-event subsets are sampled treatment-blind from eight fixed
public UAV types. The claim is limited to this exact composition law and one
event.

The question is whether `MAPR-4`, a shared permutation-equivariant masked
autoregressive four-token policy, improves failed-zone acknowledged service in
the first 60 seconds at held-out `N=7` relative separately to:

1. `DIRECT-SET-AR`, a same-information prefix-conditioned residual policy whose
   complete joint command distribution strictly contains MAPR-4;
2. `BCRH-PERSIST`, a deterministic causal receding-horizon controller that
   evaluates every legal immediate command under a safe persistent tail, then
   replans after the next observation. A finite exogenous-state dynamic program,
   exact finite-class argmax and analytic/fixture recovery certificate replace
   any future action tree, full-state graph or global optimality claim;
3. `MAPR-ROW-CUT@0`, a same-checkpoint first-dispatch intervention that
   deranges complete score rows only among UAVs with equal public flight class,
   radio capacity and legal-token mask.

All comparisons also require simultaneous non-harm on intact-zone and total
120-second service. A consistent record-plus-row relabeling must leave the
physical MAPR command invariant. Comparator competence, residual executed-
action use, action sensitivity, association opportunity and cut-induced command
change are prospectively required. Failed gates yield invalidity or
nonidentification rather than a treatment win.

MAPR processes tokens in the public order
`[EXEC_failed, RELAY_failed, EXEC_intact, RELAY_intact]`. For each token it
scores every remaining legal UAV and null from the candidate record, mean/max
roster pool, zone state and token embedding. Earlier choices affect later MAPR
probabilities only by removing the chosen UAV. DIRECT adds a learned prefix-
candidate interaction; zero residual reproduces every MAPR conditional
distribution, while nonzero residuals can reverse later candidate odds based on
the selected prefix.

The primary endpoint is the fraction of failed-zone demand delivered on
`[0,60)`. The practical margin is 0.10, corresponding to one six-second
acquisition interval at the minimum failed-zone demand denominator. Total and
intact-zone non-harm margins are 0.025 and 0.05. Sixteen independent replicate
roles support prospectively simultaneous row-sign inference. Training uses a
fixed 256 updates and 131,072 total episodes across both learned arms; the held-
out panel has 4,096 full rollouts. No old VNFC seed, coordinate, threshold,
checkpoint, result, tensor, solver, feasibility fact, provider ruling or claim
is reused.

The forbidden alternatives are `FIXED-FH`, `GLOBAL-EXACT`, a reachable-state
census, a full-graph quotient/certificate, or any hidden exponential solver
tail. No source, test, probe, coordinate, training, evaluation or compute is
authorized now.

## Requested advisory response

Seek the strongest scientific counterexample or cheaper mechanism-preserving
improvement. In particular:

- Does the four-token order, prefix containment witness, or current-state
  observation leave a causal ambiguity?
- Can the row cut change something other than recipient association despite the
  type/mask blocks and relabel invariance control?
- Is BCRH-PERSIST a defensible competent deployable comparator without smuggling in a
  full solver, and what bounded comparator would be stronger at similar cost?
- Can a favorable result be fully explained by a local clearance/ETA/radio/
  retention heuristic, roster composition, or generic action disruption?
- Is there a lower-work direct UAV-value discriminator that preserves the same
  question and containing comparator?
- Which exact outcome should be `INVALID`, `NONIDENTIFIED`, `DECLINE`, or
  `RETAIN`, and what claim ceiling remains honest?

Return a prioritized advisory with precise repairs. Do not claim closure, review
code, request runtime evidence, rank other directions, propose full-graph exact
planning, or authorize activity.
