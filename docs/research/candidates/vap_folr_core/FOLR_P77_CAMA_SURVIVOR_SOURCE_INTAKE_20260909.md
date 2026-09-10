Claim under assessment: CAMA Traffic Junction has real multi-step roster events, but its supplied observation/lifetime interface does not yet support the requested clean true-survivor RETAIN/RESET contrast.
Binding MARL structure: (a) roster change; (d) other-agent non-stationarity or partial observability.

# FOLR P77 Traffic Junction survivor-state source intake — 2026-09-09

**NO_READY_CONTINUATION under the assignment's unchanged permitted-information boundary.**
The new finding is a specific source/interface mismatch, not another absence-of-positive-result
assessment. This completes the bounded mapping assignment without opening a family, changing
ACTIVE/MEDIUM, recasting, freezing a card, implementing an adapter, or sending a Pro request.

## 1. Scope, checks and reading rule

P77 asks for the concrete multi-step survivor-state intervention left unselected by
[P68 §6](FOLR_P68_MULTISTEP_REENTRY_INTAKE_20260908.md), using its already identified
Traffic Junction/CAMA host. It permits source reading, retrieval, arithmetic and question
preparation; target imports, model construction/calls, simulator/episode/diagnostic/probe,
implementation, cards, masters, invocations and Pro Send remain zero. A precise no-ready return
is an explicit completion branch. The independent unit is this **A/RECON source assessment**.

I checked current AGENTS and docs instructions, the current Portfolio FOLR row, DIRECTION's
accepted B04 science, P68's unresolved comparison, and evidence-spec §§3–5.2 and 11. The rule
applied verbatim from §11.8.6 is:

> An ordinary B must run the real environment, policy, learner, trainer and evaluator; its transitions,
> updates, evaluation and selection exposure and primary comparison must be readable, with reward,
> information and budget semantics intact.

Section 11.8.1 also controls: missing exact headroom, a tuned baseline, or a complete causal
explanation does not block a B. The issue here is the information/identity meaning of the
proposed intervention. No exact ancestry audit, census, diagnostic run or proof is demanded.

The designated checkout is `C:/Projects/HMASD-worktrees/codex-vap-folr`, branch
`codex/vap-folr`, starting clean at `0131f327fb6a7043dfa5dbb75cd258afd11c12d0` and pushed.
Current main's AGENTS/relay instructions were read from the main checkout. Required science
and method inputs matched; no main index or unrelated source was edited. Root integrates the
four explicit result paths, preserving main's existing September 9 audit rows.

## 2. Verified source-to-consequence path

The P68 library retrieval already verified CAMA, Shao et al., ICML 2023, `MARL-0409`, Appendix
G.2 (source JSON pages 16–17, elements 497–507). Its paper repository link redirects from
`qyz55/CAMA` to `thu-rllab/CAMA`. I retrieved the official code at immutable commit
`1d8d6f8c44102d7b8904bf44eeb38cd1276dbb58` and read 17 files as text. The
[facts JSON](evidence/2026-09-09-p77-cama-survivor-source.json) records exact source URLs,
byte digests, relevant line ranges and computed counts. No code was imported or executed.
P68's verified library coverage and its Sable history comparator remain reused; there was no
repeat broad literature search or inferred novelty verdict.

All following ranges are relative to that CAMA commit:

- **Event and entity ownership.** `CAMA/envs/traffic_junction/traffic_junction.py:16–23,52–75`
  defines easy mode as a 7×7 road grid, five fixed slots and a 20-step episode, with initially
  inactive slots and one forced arrival. Mask `0` means active. Each spawn assigns an entrance
  and goal. An uninterrupted active slot keeps its physical position, target and waiting value;
  `_remove_car` clears them (`133–151`). The source has no generation/epoch identifier.
  Interpreting each activation as a new physical trip is a proposed lifetime definition,
  distinct from the controller's persistent slot index.
- **Departure and replacement timing.** `step:77–99` moves active cars, calls `get_reward`, then
  calls `_add_car`. Goal completion and collision remove cars inside `get_reward:101–138`.
  `_add_car:156–183` can reactivate a removed slot before the next boundary observation.
  Therefore an active→active mask can contain a departure and new arrival. This is an actual
  source path; its frequency has not been sampled. `_add_car` also runs on the final episode
  step, when no further native action remains.
- **Available information.** `get_entities:185–189` supplies current target/position features;
  `get_masks:196–203` supplies distance-based visibility and active/inactive masks. The selected
  source configuration uses `vision:1`, a 3×3 neighborhood. An active car reobserves its own
  goal and position at each step, unlike B04's one-time private cue. The API does not return
  the internal arrival/removal list or a slot generation. The recurrent agent applies the
  visibility mask before attention and masks inactive Q outputs. The controller receiving a
  global mask for bookkeeping is not proof that all hidden event timing is actor-permitted.
- **State lifetime and action path.** `CAMA/modules/agents/entity_rnn_agent.py:23–34,69–88`
  uses a GRU and zeros initial state, but carries its recurrence through inactive slots; only
  the Q output is zeroed. `CAMA/runners/episode_runner.py:94–117` initializes hidden state once
  per whole episode, selects actions and calls the native step. The entity controller also
  appends the preceding slot action (`CAMA/controllers/entity_controller.py:11–30`). A new
  trip can therefore receive predecessor/inactive-slot hidden state and a predecessor action
  feature. It is not enough to reset only newly visible `1→0` slots and call all other `0→0`
  slots true survivors.
- **Native consequence and credit.** Active cars choose among stay and four grid movements;
  valid road moves change position. Native team reward combines Manhattan-distance progress,
  the source waiting penalty, and collision penalties (`101–131,208–209`); the runner sums it
  over the episode (`122`). No synthetic reward is needed. The source increments waiting for
  all slots and does not reset it in every spawn path; it must not silently be rewritten as
  active-trip age. Shared actor parameters and the centralized QMIX learner expose partner
  co-adaptation during learning. A primitive environment tick is one opportunity, with the
  source discount `0.99`; no variable-duration or semi-Markov object is present.

Thus the host genuinely contains a multi-step action/reward path and membership events.
It does not already implement the lifetime/observation boundary required by a clean selective
survivor intervention. These are separate findings.

## 3. Concrete candidate assessed and the unresolved boundary

The candidate is deliberately simple. At each real participant arrival/departure, **RETAIN**
keeps a still-living car's complete causal GRU state; **RESET** clears that survivor state
before processing its next permitted observation. Both use the same recurrent attention actor,
parameters per arm, observation features/masks, native objective, training exposure and evaluation
rule. Every new trip should start with fresh hidden state and no predecessor action in both arms;
inactive slots should not accumulate transferable hidden history. No state or optimizer is copied
from another entity. The competent same-information comparator is ordinary full-history RETAIN,
using the source generic `qmix_atten` path, not a weak writer or reset control.

This candidate would measure the native cost or benefit of erasing survivor history. The complete
GRU can contain past observations of other cars. It is not strictly self-ancestry state, and a
RETAIN gain cannot silently broaden the old typed-only FOLR definition or establish typed routing
value. That prospective family meaning requires Convergence if a conforming question is selected.

Two direct implementations fail to preserve the stated candidate:

1. **Use only consecutive active masks.** This finds some genuine events but misses same-step
   same-slot replacement. It can call a new trip a survivor and retain predecessor state/action.
   At boundaries with multiple events it can also reset a replacement while reporting survivor
   erasure. This is a comparison of slot-memory rules unless its event population and lifetime
   claims are explicitly changed. It is not the requested true-survivor experiment by default.
2. **Read internal removal/spawn callbacks.** This distinguishes trips and permits fresh entrants,
   but survivor resets now depend on events absent from the supplied observation history,
   potentially including events outside local view. The reset itself changes the actor's state
   and subsequent action, even if no event bit is appended to its feature vector. Equal callback
   access across arms does not by itself establish preservation of the source's permitted
   information boundary. Treating lifecycle metadata as newly common and public would be an
   explicit scientific change, not an ordinary adapter fix under this assignment.

Neither finding proves that an observation-compatible restricted event population is impossible,
or that a study with declared common lifecycle metadata lacks value. It identifies the missing
meaning for this requested comparison. I do not invent a restricted event detector, add public
event bits, disable same-step respawn, manufacture a new lifetime, or treat internal simulator
access as automatically permitted. The serious zero-work alternative is to retain the ordinary
recurrent comparator and leave this specific extension unselected; its existing history capacity
already supplies RETAIN without claiming a new typed mechanism.

**Training versus evaluation.** If a later scope resolves that boundary, both policies must learn
under their respective state rule, including the online and target replay unrolls
(`CAMA/learners/q_learner.py:89,117,129–144`), with the same terminal handling and native TD loss.
Each then receives final frozen greedy evaluation under its own trained rule. Applying RESET
only to weights trained under RETAIN would instead measure frozen-policy dependence/distribution
shift; it must not be called the equal-training comparison. The two policies' traffic histories
can diverge after their actions differ. Seed labels do not give identical realized event tapes:
spawn uses global `np.random`, whereas the environment's `seed()` initializes `self.random`.

## 4. Small real B work considered, without selecting it

This counterfactual arithmetic keeps the real source actor/learner rather than requiring search
before learning. Its generic actor has a 64-unit GRU, 128-unit attention embedding and four heads;
the learner uses FlexQMixer, double Q and RMSprop with learning rate `0.0005`. A source algorithm
and reasonable architecture are a competent comparison design, not measured tuned competence
at a new small exposure. That missing measurement is not the no-ready reason.

An illustrative two-arm, one matched training instance at **5,000 complete 20-step episodes per
arm**, serial collection and one replay update per new episode after the buffer reaches 32,
would have:

| Quantity | Per arm | Pair |
| --- | ---: | ---: |
| Training environment ticks | 100,000 | 200,000 |
| Actual RMSprop steps | 4,969 | 9,938 |
| Online + target replay GRU row forwards | 33,391,680 | 66,783,360 |
| Final frozen greedy evaluation episodes | 32 | 64 |
| Evaluation environment ticks | 640 | 1,280 |
| Total environment ticks | 100,640 | 201,280 |

The dominant replay factor is `4969 × 32 episodes × 21 sequence positions × 5 slots × 2
online/target passes` per arm, plus online backward and mixer work. Source acting includes one
terminal-state controller pass: 105,672 controller calls per arm for collection and final
evaluation, or 1,056,720 acting GRU row forwards across the pair. Row forwards are work units,
not independent training instances. There are no nested candidates, hypothetical trajectories,
solver search, diagnostic sweeps or extra validation episodes in this scale example.

The serial/one-update cadence keeps the source parallel-eight/eight-update ratio, but this is
not its 4-million-step reproduction. Its original epsilon anneal is 500,000 ticks; retaining it
at 100,000 leaves substantial exploration, while shortening it would be another explicitly
recorded common B configuration choice. Neither choice is made here. RMSprop can move at the
nonzero nominal rate: `4969 × 0.0005 = 2.4845`; this nominal learning-rate path is not measured
parameter displacement or a displacement bound. Same-information tuned Traffic Junction headroom
is absent, with no extrapolation of B04's host-specific MEI or headroom.

Wall cost is **unknown**. B04's 40.371825 seconds is not a coefficient for this recurrent learner.
An illustrative complete cap of 1,800 seconds per arm/3,600 across the pair is a possible future
stop envelope, not a cost prediction, admission or allocation. Any portable invocation would
follow remote-first at its committed source and fresh node admission. No hardware-dependent
scientific estimand is proposed here. This is a comparison with a small real B, not a reason to
commission a finite diagnostic or cost experiment first.

Machine-generated current exposure: **scientific invocations=0; target imports=0; models=0;
model calls=0; training ticks=0; optimizer steps=0; evaluation episodes=0; native calls=0;
diagnostics=0; Pro Sends=0; cards=0; RNG masters=0.** Engineering-scope §4 needs **none** for
this intake; there is no implementation or §5 budget breach.

## 5. Retained empirical evidence and claim ceiling

B04 remains `B04_WITHIN_MEI`: mean STALE_LOAD return-AUC difference `0.0026041666667` against
MEI `0.05`, with paired differences `+0.001953125, −0.000244140625, +0.006103515625`.
TYPED and GENERIC final return were both `0.98828125`; LATCH was `0.9986979167`, RESET
`0.5065104167`. The update-16 positive transient `0.0221354167` remains visible. RESET's
information loss is not typed-over-generic efficiency. B04's 444,672 training transitions,
1,536 optimizer steps and 49,920 evaluation episodes are historical exposure, not P77 work.
Its native first-action ceiling, frozen writer, small scalar host and three seeds still bound
its conclusion. No DISH or other stopped family is reopened, pooled or reinterpreted.

Strongest support for this no-ready return is the exact ordering of removal, same-slot refill,
boundary masks and recurrent carry. Strongest contradiction to a broad negative is the genuine
multi-step host, observable events within it, a useful generic recurrent learner, and B04's
positive/transient evidence. There is no measured traffic return, event frequency, memory effect
or runtime here. The ceiling is a source/interface assessment, not failure of multi-step memory
or an exact impossibility result.

## 6. Decisions this intake produces

1. **Object-tier readiness.** Options: (a) publish the specific source/information mismatch and
   return no-ready; (b) assume internal lifecycle callbacks are permitted and author that changed
   comparison; (c) equate boundary slot masks with physical-trip identity. Recommend/select **(a)**.
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** The P77 assignment
   explicitly authorizes this return branch. This is reversible, `OWNER_DELEGATED`, owner flag
   `none`. It adds concrete source findings beyond P68's unselected intervention.
2. **Direction tier.** No family opening, closure, recast, park or Pro decision is formed.
   Prompt Author instructions were read for the conditional ready route; no Issue, TASK,
   HANDOFF or Transport request was created. A different explicit information/lifetime boundary
   could support a later proper-node question, but is not selected or commissioned here.
3. **Root action.** Accept/integrate this completed source assessment, retain the FOLR boundary
   and choose any working-set replacement within Portfolio authority. This return makes no
   lifecycle, priority, capacity or investment change. The designated direction checkout remains
   the reusable authoring checkout, with Root owning its eventual integration/reclamation.

The all-age owner-review query returned `[]` at this boundary; no differing instruction or
unscored prediction reply was found. Owner prediction: **not taken**. No new empirical
prediction was posed. No P1/P2 item is added for this ordinary readiness decision: there is no
new card, direction decision, material dissent, close call, second recast or Portfolio proposal.
The audit row and [Chinese brief](../../portfolio/owner/briefs/vap_folr_core/2026-09-09_P77-cama-survivor.md)
record the completed A result.

The next discriminator, if separately scoped, is a native sampled-return comparison of trained
survivor-memory rules under an explicitly permitted lifetime/event interface. The concrete
unresolved question is which events and trip boundaries may control state without changing the
claimed information set. No run, additional assessment or Pro round is requested by this intake.
