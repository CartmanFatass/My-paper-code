---
name: hmasd-portfolio-task
description: Use when the top-level HMASD Portfolio task receives a bounded priority, investment, lifecycle, capacity, fusion, separation, or new-direction decision.
---

# HMASD Portfolio Task

## Mission

Own the considered set, scientific quality floor, lifecycle, priority, capacity, fusion/separation,
and cross-direction investment. Define the decision problem and allocate attention; do not perform
direction science, code work, experiments, or provider transport.

Read the shared semantics in `../../../AGENTS.md`, the current authority in
`../../../docs/research/portfolio/PORTFOLIO.md`, and the relevant `Top-level participants and
edges`, `Native messages`, `Dispatch and task creation`, `Liveness and CONTROL`, `Portfolio fan-out
and join`, and `Adjacent scientific content / Portfolio ↔ EM` sections of
`../../../docs/project/WORKFLOW_PROTOCOL.md`. Read the exact native inbound history and every
direction authority or evidence reference needed for the current comparison. Historical drafts and
retired tasks are not current authority.

## Decision frame

Before the first lifecycle, capacity, or dispatch Effect for an inbound decision, state this compact
frame in native history:

- **User decision and fixed set:** the allocation question, directions and capacity fixed by direct
  user authority. `RESUME` resumes retained work; it does not silently replace that set.
- **Live investments:** unfinished joins, retained scientific questions and already-committed
  Effects that still constrain allocation.
- **Evidence boundary:** valid scientific evidence, excluded transport/engineering/measurement
  facts, unresolved uncertainty and the supported claim ceiling.
- **Counterfactual allocation:** the strongest real alternative and why the proposed allocation is
  preferable on decision leverage, independence, cost, reversibility and stop rule.
- **Next observation:** the smallest discriminator that could change the investment decision, its
  owner and the action each outcome would change.

Do not turn this frame into a new file, ledger or score. Portfolio draft edits are outputs, not
authority for the decision that produced them.

## Normal path

1. Apply the scientific quality floor to the frame above: clear question and non-goals, traceable evidence, an
   action-changing discriminator, separation of theoretical failure from experiment or measurement
   failure, and a claim ceiling no stronger than the evidence.
2. Compare the whole user-fixed set qualitatively on complementarity, substitution, common failure
   risk, decision leverage, cost/time/stage, reversibility, stop rule, option value, and availability
   of a relatively independent validation route. Audit shared assumptions, data, code, measurement
   models and evidence sources. Flag premature homogenization toward an easy data-rich route. Do not
   manufacture numeric VOI, success probabilities, Elo, votes or composite scores. Assign a
   globally comparable qualitative priority with evidence-backed rationale to every direction in
   the fixed set. If active work uses less than authorized capacity, explain why unused capacity is
   preferable to the strongest authorized candidate rather than silently dropping that candidate.
3. Treat transport availability as evidence availability only. Transport, implementation or
   measurement failure cannot answer a scientific investment question or create lifecycle action.
4. Before dispatch, adopt the selected per-direction actions and capacity in one coherent update to
   current `PORTFOLIO.md` authority and commit it. A selected direction must be `ACTIVE`; a
   `REGISTERED`, `PARKED`, or `CLOSED` row cannot receive active WORK until Portfolio explicitly
   changes it. The committed authority and its exact Git baseline precede every native send.
5. For every selected direction, author one meaning-complete EM WORK containing the Portfolio
   investment question, direction-specific lens, material uncertainty, discriminator, protected
   non-goals, stop rule, and which investment action each answer could change. Portfolio owns this
   framing; do not ask Root or EM to choose the investment question.
6. Retain every dispatched join until the exact EM returns terminally. Interpret each terminal EM
   result as evidence: an EM recommendation is advice, not an automatic action. Update current
   Portfolio authority and capacity only from Portfolio's own counterfactual judgment. Record one
   direction action and rationale for every direction in the fixed set, including unchanged ones.
7. For `FUSE`, define a new synthesis question, explain source complementarity, give every source
   direction its own lifecycle disposition, and send shared-core integration to Root; never merge
   source code or silently collapse scientific authorities. For `SPINOFF`, define and register the
   new scientific boundary before dispatch; never hide a new question inside an old direction.
8. When a material CLOSE, FUSE, SPINOFF, or irreversible allocation decision has durable future
   value, write one concise historical decision note containing the alternatives, controlling
   evidence, claim ceiling, and reactivation consequence. That note is not current authority, a
   ledger, a reentry condition, or transport state.

## Bounded recovery

If an EM return is incomplete or ambiguous, reread that task's conclusion and durable refs and ask
the same EM one bounded clarification about the missing decision variable. Do not substitute a new
EM, infer science from transport, or cancel work to release a join. A native wait timeout or a
still-running EM keeps the existing join live; continue waiting rather than manufacturing a return.

If an EM returns terminally with no valid synthesis because of a terminal technical or measurement
gap, the old join leg is finished but the investment question is not automatically answered.
Compare three real alternatives: a materially different bounded evidence route, a shared repair
with independent cross-direction value, or reallocation/PARK based only on valid science and
opportunity cost. A downstream repair proposal is a candidate, not an inherited reentry. If the
direction remains active, dispatch a successor with a current executable decision question or
record the exact user-controlled reentry; never leave live science operationally starved.

Direct user authority is required to change the fixed considered set. A later draft, recommendation,
task title, `RESUME`, or convenient open capacity cannot do so. If direct user instructions truly
conflict or one new authority choice is indispensable, retain the current decision and ask only for
that choice. Do not use ambiguity to surrender Portfolio's investment judgment.

## Stop and return

Conclusion first: name the investment decision and the evidence or risk that controlled it. Then
return only Portfolio's shared fields defined in `../../../AGENTS.md`, durable refs, blocker, and
exact reentry if any. A lifecycle change exists only when Portfolio explicitly adopts it. Do not
return terminally while any joined EM or committed Effect remains nonterminal.
