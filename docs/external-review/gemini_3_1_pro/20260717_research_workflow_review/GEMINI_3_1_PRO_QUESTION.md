# Gemini 3.1 Pro Research-Workflow Review

You are an independent divergent-but-disciplined research reviewer. Use only
the information in this prompt. Do not call tools, inspect files, execute
commands, edit the repository, or browse the web.

## Research target

HMASD is being extended toward one shared skill-based MARL algorithm that must
eventually support both:

1. variable team membership/size, including within-episode join and leave;
2. variable per-agent skill lifetime without a combinatorial duration action.

The route must preserve useful HMASD skill semantics, autoregressive
coordination advantages, probability/credit correctness, and anonymous
variable-N execution. Intrinsic reward must remain environment-agnostic; task
fields, goals, contacts, phases, success predicates, distances, and external
reward cannot be used to customize it. Reward shaping must not be confused
with algorithmic exploration.

## Observed workflow failure

The project repeatedly required GPT-5.6 Pro to output exactly one successor
after every valid FAIL. R41--R55 consequently became a serial chain of isolated
access and representation gates. Each gate was individually falsifiable, but
the sequence drifted from the final algorithm target toward asking whether a
new toy, representation, or optimizer could pass its own access threshold.
Several rounds changed environment, representation, and learning objective
together. Negative results retired exact contracts but did not reliably update
a shared causal model of the final algorithm.

The latest candidate is R55-ABRP-G0: replace failed global set attention with a
3,906-parameter anonymous member-entity edge pointer on a fixed-membership,
fixed-horizon typed-backlog toy. Fixed-N specialists are the prerequisite for
a shared variable-N policy. It does not test within-episode membership change,
skill semantics, variable lifetime, or their joint credit problem. Its isolated
implementation was started but has not been tested, committed, or run.

## Proposed workflow correction

Replace "one unique next research route" with:

> Maintain multiple competing causal hypotheses, but execute only one
> information-gaining experiment at a time.

Gemini would act as the divergent reviewer, GPT-5.6 Pro as the convergent
adversarial reviewer, and Codex as controller. A gate is admissible only if its
outcomes distinguish at least two live hypotheses and change a real project
decision. A PASS on an isolated toy does not authorize integration. A FAIL does
not automatically require a successor gate.

## Requested decision

Provide a concise but substantive review with these exact sections:

1. **Workflow verdict** — decide whether the unique-route rule caused harmful
   premature convergence and gate random-walk behavior; distinguish epistemic
   exploration from operational serialization.
2. **Failure diagnosis** — identify the strongest mechanisms that caused the
   R41--R55 drift. Separate evidence-supported causes from inference.
3. **Hypothesis portfolio** — propose at most four structurally distinct
   architecture/credit hypotheses for the final variable-N plus
   variable-lifetime problem. These are hypotheses, not four implementation
   tasks. For each state what it replaces, retains, and adds; map it to dynamic
   N, heterogeneous lifetime, skill semantics, autoregressive coordination,
   credit, computational scaling, and the strongest ordinary-MARL baseline.
4. **Discriminating evidence** — propose the smallest evidence source that
   separates at least two of those hypotheses. Prefer reanalysis, an existing
   environment, or a shared testbed over another bespoke toy. Explain how each
   possible outcome changes the portfolio.
5. **R55 disposition** — choose exactly one of PROCEED, PAUSE, REPURPOSE, or
   RETIRE and justify it by information gain toward the final target, not by
   implementation sunk cost.
6. **Strongest objection** — state the strongest argument that the entire
   variable-N plus variable-lifetime direction is unnecessary or reducible to
   standard MARL plus masking/scheduling, and specify what evidence would
   answer that objection.

Do not invent R56, prescribe parameter tuning, or turn every hypothesis into a
new numbered gate. It is acceptable to recommend stopping experimentation and
performing a cross-round synthesis first.
