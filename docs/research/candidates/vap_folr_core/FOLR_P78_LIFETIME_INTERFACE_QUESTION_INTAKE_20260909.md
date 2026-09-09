Claim proposed for later exploration: on an explicitly public-lifecycle Traffic Junction variant, preserving a surviving car's recurrent history may improve native return relative to resetting it at membership events.
Binding MARL structure: (a) roster change; (d) other-agent non-stationarity or partial observability.

# FOLR P78 public-lifecycle question preparation — 2026-09-09

**READY_QUESTION; recommend one narrowly scoped B comparison to Convergence, as a close call.**
Only question publication is executed. The prospective information change, family meaning,
training choices, MEI and invocation budget remain unselected/unallocated. P77's exact no-ready
finding for the unchanged source information interface remains accepted.

## 1. Assignment and retained authority

Root accepted [P77](FOLR_P77_CAMA_SURVIVOR_SOURCE_INTAKE_20260909.md) and assigned this new
preparation: ask the original FOLR Convergence node whether an explicit common lifecycle/event
interface warrants a bounded native RETAIN/RESET study, or keep the current no-successor
boundary. This is an A/RECON question-preparation result, not a science card or run allocation.
The designated checkout remains `C:/Projects/HMASD-worktrees/codex-vap-folr`, branch
`codex/vap-folr`, starting clean/pushed at `64db6307b236ffaa98e61f4ea83a5cdbb0a20bfb`.

Direct inputs are P77 §§2–6 and its facts JSON, DIRECTION's accepted B04 science, P68's
unselected multi-step intervention, and evidence-spec §11.8. The 17 source files already
verified at CAMA `1d8d6f8c44102d7b8904bf44eeb38cd1276dbb58` are reused without another
retrieval or source-identification project. Native source, simulator and reward are not changed
by this preparation. Current Prompt Author, GitHub delivery and owner-item instructions apply.

The governing rule is evidence-spec §11.8.1, verbatim:

> Missing an exact upper,
> tuned headroom or complete causal explanation does not block performance exploration.

Section 11.8.6 still requires reward, information, training, comparison and budget semantics
to be readable. This packet proposes an information change explicitly rather than treating
internal callbacks as already permitted. The source facts are sufficient to pose that decision;
event frequency, competence at a small exposure, effect size and wall time remain unobserved.

## 2. Exact prospective interface and the information change

Keep the source easy Traffic Junction physical dynamics, five slots, 20 primitive steps,
vision-1 local entity observations, five actions and native team reward. Keep its actual
goal/collision removal, same-step refill, waiting behavior and RNG consumption. No extra event,
reward or counterfactual simulator call is introduced. This is a proposed **new information
protocol on the source simulator**, not an unchanged CAMA private-information task.

For the completed native transition from time `t` to `t+1`, a common environment-side adapter
would record the following from the actual removal and activation paths:

- `A_before[j]` and `A_after[j]`: whether slot `j` is active before/after the native step.
- `D[j]`: an actually active car was removed in this step. A repeated call on an already
  inactive slot does not create another departure.
- `B[j]`: the slot was activated by a native spawn in this step, including remove-and-refill
  of the same slot. A car identity is its episode, slot and activation occurrence; a reused
  slot is a new trip, never a resumed predecessor. No numeric generation ID enters the actor.
- `C[j] = A_before[j] and A_after[j] and not D[j] and not B[j]`: true continued ownership.
- `E = any(D or B)`: whether any real participant arrival/departure occurred.

The adapter observes these events only while the real step executes. It emits them **after
native reward/removal/spawn and before the next actor input**, never before action `a_t`.
The same interface and timing apply to both arms:

| Recipient | Metadata received | Permitted use |
| --- | --- | --- |
| Both fixed state managers | Existing active mask, `B`, `C`, and `E` | Match state to real trips, clear entrants/inactive slots, and apply the declared survivor rule |
| Both learned per-car actors | Same native local attention features, plus two scalar inputs: global `E` and own `B[i]` | Learn with the same explicit event information; RETAIN can use or ignore it |
| Both replay/target paths | The same recorded next-observation metadata | Reproduce each arm's acting state rule in online and target recurrent unrolls |

The two scalar inputs would be appended to each car's attention representation before its
existing GRU input projection, with identical architecture in both arms. No departure reason,
hidden position/goal, reward label, other car's memory, future event, numerical epoch identifier
or full event-list feature is supplied to the learned actor. `D` is used to derive common
lifetime/event metadata, not appended as an additional actor input.

Both arms keep inactive hidden state zero and initialize a newly activated trip with zero
hidden state. For entity previous-action features, preserve the preceding action only when
the same trip continued (`C`); otherwise use zero in both arms. These are explicit common
departures from the source's slot-persistent GRU/previous-action behavior. Episode reset zeros
all state, sets own birth for the initially active car, and uses `E=0` because there is no
survivor from an earlier episode. Events in the final native step have no subsequent native
action; terminal handling must not count them as post-event control opportunities.

The public global event bit changes what a locally partially observing survivor can know.
Adding it to **both** learned actors matters: otherwise RESET's hidden-state discontinuity
could itself be an extra event signal unavailable to RETAIN. Partial observation of physical
traffic remains, but a result belongs only to this declared lifecycle-visible variant. It
cannot be imported into original CAMA, old B3/B04, or a private-membership task.

## 3. Treatment, comparator and scientific purpose

At the first actor update after the completed transition:

- **RETAIN:** true survivors keep their full causal GRU state; entrants/inactive slots use the
  common fresh-state rule. This is the competent generic recurrent comparator.
- **RESET:** when `E=1`, clear the full GRU state of true survivors before processing the same
  next observation and scalar metadata. Entrants/inactive slots use the identical common rule.
  When `E=0`, survivors carry state normally.

Use the source generic entity-attention GRU/QMIX learner as the common base, not the CAMA coach
as a different treatment. Both policies train under their own state rule with matched model
size, native objective, initialization pairing, exposure, optimizer settings and evaluation
selection. Apply the rule in both online and target replay unrolls. Equal optimizer counts do
not imply equal gradients or parameter movement; changing history and its learning path is
part of this exploratory trained-system comparison. Native trajectories and partner adaptation
may diverge after different actions; equal seed labels do not guarantee the same realized
traffic events, particularly with the source's branch-dependent global NumPy draws.

The proposed primary observation is the difference in mean full-episode native return from
final frozen greedy evaluation of the two independently trained rules. An evaluation-only
RESET applied to RETAIN-trained weights would be a different dependence/distribution-shift
question and is not the proposed comparison. The independent unit is a matched pair of
training instances; evaluation episodes and GRU rows are not extra training seeds.

The source-to-effect hypothesis is: actual other-car arrival/departure → continuing physical
car retains ownership → common public lifecycle cue plus its local observation history →
retain or erase the GRU before another movement choice → real online/target learner exposure
under that rule → native progress/waiting/collision return over the remaining episode.
Recent observations of cars that moved out of view could support a competent later action;
resetting can erase that context. Conversely, retained context can be obsolete or distracting,
and current own goal/position are reobserved every step. These are hypotheses, not source
performance facts or a proof that memory is necessary.

The full recurrent state includes teammate ancestry. A RETAIN gain would be a bounded cost of
survivor-memory erasure on this variant, not typed-state novelty, strictly self-only ancestry,
information necessity, long-horizon superiority, transfer, UAV value or a Portfolio judgment.
A RESET gain would be retained as an opposite-sign finding; an unresolved difference would
bound this setup and exposure. No complete causal diagnosis or exact maximum is needed.

## 4. Minimal trained comparison, costs and serious alternative

Reuse P77's **unallocated scale example**, rather than a diagnostic prerequisite: two arms,
one matched training instance, 5,000 complete 20-step episodes per arm, one replay update per
new episode after 32 episodes, and 32 final greedy evaluation episodes per arm. This gives
200,000 training ticks, 9,938 RMSprop steps, 64 evaluation episodes and **201,280 total native
ticks**. The dominant replay work is **66,783,360 GRU row forwards** across online/target
passes: `2 arms × 4969 updates × 32 episodes × 21 positions × 5 slots × 2 passes`, plus
online backward and mixer work. Acting adds 1,056,720 GRU row forwards including the source's
terminal-state pass. These counts are not measured time or independent samples.

The source common base has GRU width 64, attention width 128/four heads, FlexQMixer and
RMSprop `lr=0.0005`; the nominal `4969 × lr = 2.4845` path is not measured displacement.
The original 500,000-tick epsilon anneal would remain highly exploratory at 100,000 ticks
per arm; any shorter common anneal, final exact card, MEI and stop budget remain future
choices. The example is not the source's 4-million-tick reproduction. It selects no seed,
master, checkpoint, tuning sweep, policy search, diagnostic, or preliminary cost run.

Wall cost remains **unknown**. P77's illustrative 1,800 seconds per arm/3,600 per pair is a
possible future complete stop envelope, not a projection or allocation. B04's 40.371825
seconds does not predict this workload. Portable result-bearing work would use the configured
remote-first route and its own fresh admission; host/device are not proposed as the estimand.
Traffic Junction tuned same-information headroom remains absent and is not a refusal reason.

**Recommendation to Convergence:** select the explicitly public-lifecycle extension for one
bounded real B, narrowly. It would answer whether indiscriminate resetting on genuine roster
events carries a native cost after learners can adapt on a real multi-step coordination host.
The recommendation is a close call because generic RETAIN is already the standard history
path and a reset loss would add no new typed algorithm. The serious alternative is **retain
the no-successor boundary and keep ordinary generic RETAIN without a new claim or compute**.
Pro may prefer that alternative on question value, without declaring memory useless, demanding
a stronger evidence class or treating missing tuned headroom as a gate. No local family/scope
selection is made by this recommendation.

## 5. Evidence limits, exposure and owner surfaces

B04 remains inside its `0.05` MEI at mean stale AUC difference `0.0026041666667`; its individual
positive/negative differences, positive update-16 transient `0.0221354167`, TYPED/GENERIC final
`0.98828125`, LATCH `0.9986979167` and information-cut RESET `0.5065104167` remain preserved.
Its historical 444,672 training ticks, 1,536 updates and 49,920 evaluation episodes are not
current exposure. P68/P77 no-ready findings and all older FOLR/DISH pauses retain their meaning.
DIRECTION is not edited because no new mechanism-level result or direction decision exists.

Machine exposure is generated from the reused P77 facts: **new scientific invocations=0;
target imports=0; models=0; model calls=0; training ticks=0; optimizer steps=0; evaluation
episodes=0; native calls=0; probes/diagnostics=0; implementation=0; cards=0; masters=0;
provider Sends=0.** Engineering-scope §4 needs **none** for this preparation. The proposed
finite in-process state/actor change needs no new registry, resume/distributed execution,
provenance guard, search, schema validator or telemetry framework. No §5 budget breach occurs.
If a B is later selected, its card would name only four additional within-run exposure totals:
births, departures, true-survivor event opportunities and actual survivor resets per arm.
They come from the same native/learner path, require no additional episodes, and would limit
interpretation rather than impose a minimum event census before learning.

The P1/P2 close-call item records the actual choice to publish this question, not approval of
the prospective information change or a launched B. Owner prediction is **not taken**; no new
empirical prediction is posed before a scope decision/card. All-age unapplied reviews were
empty at preparation. The [Chinese brief](../../portfolio/owner/briefs/vap_folr_core/2026-09-09_P78-lifetime-question.md)
states the information change and zero-execution boundary.
The published close-call item is
[`20260909-folr-001`](../../portfolio/owner/inbox/2026-09-09/20260909-folr-001.json).

## 6. Decisions this preparation produces and delivery boundary

1. **Object-tier preparation:** options (a) publish this concrete prospective question;
   (b) return a missing-essential-source-fact gap. Select/recommend **(a)**: no additional
   source fact is required to ask whether the explicit change is worth studying.
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Root's P78 command
   explicitly authorizes preparation. The scientific recommendation and zero-work alternative
   are a close call; no future scientific option is auto-applied.
2. **Direction tier:** ask `em:vap_folr_core:convergence` to select the explicit lifecycle-visible
   extension or retain no successor, with a class-B claim ceiling and reasons. This is the
   original logical node; no family, lifecycle, recast, C promotion or Portfolio disposition
   is selected locally. Exact training/card choices and invocation allocation remain absent.
3. **Provider currentness:** current `.codex/hmasd-transport.toml` requires 6 Pro via configured
   Transport `01a07e52-f085-76a0-886a-4127f490421f`. The project registry observed at preparation
   (version 4, updated `2026-09-09T10:06:00Z`) has neither this binding key nor a FOLR direction
   mirror. The cutover record excludes every pre-`2026-09-05T00:56:02Z` provider conversation,
   including old IDs absent from its inventory. No provider UUID is prebound or invented;
   `requested_conversation_id=null`, reset flag false. Transport alone can observe/bind a
   fresh verified 6 Pro context for this unbound logical node. No archived answer is falsely
   labelled contaminated or negative to obtain a reset.
4. **Root-only return:** publish immutable TASK and bind its full pushed SHA, then commit/push
   HANDOFF on the existing shared branch. Source is actual native author
   `01a08438-c6e4-7981-b75d-ba81fabd4c2f`; parent is Root
   `01a07249-b095-7821-8ce2-e9c32ba85267`; executor is the configured Transport. Return request
   ID, full HANDOFF commit/path and fixed TASK URL to Root. Root owns any dispatch and later
   native receipt forwarding. This DM performs no app Transport dispatch or provider Send.
   The substantive discussion/delivery Issue is
   [FOLR public lifecycle information](https://github.com/CartmanFatass/My-paper-code/issues/15).
   The prepared packet is `pro_packets/20260909_p78_public_lifecycle_convergence/`; its
   committed HANDOFF records the immutable TASK URL without using a moving branch as input.

Strongest support is a concrete intervention aligned to source car lifetimes and an equal
explicit event signal in both actors. Strongest contradiction is that generic recurrent
retention is already standard, own goals are reobserved, and any observed gap could concern
an intentionally poor reset rule on a changed information protocol. The next discriminator,
only if selected and allocated, is sampled native return after real training under these
two rules. Unknown event exposure or cost remains unknown; neither is scientific polarity.
