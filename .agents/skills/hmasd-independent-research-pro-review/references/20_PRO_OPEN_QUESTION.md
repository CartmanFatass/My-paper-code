# Independent MARL research methodology audit

```text
review_mode=INDEPENDENT_RESEARCH_METHODOLOGY_AUDIT
review_scope=independent_advisory_research_methodology_only
project_state_effect=none
code_authority=none
compute_authority=none
formal_workflow_promotion=forbidden
```

## Question

Design a compact scientific-methodology contract for the HMASD Independent
Research Explorer. The Explorer begins from broad literature-oriented
directions and must be able to derive, challenge, combine and refine narrower
research conjectures. The contract must keep this process grounded in MARL as
an experimental science built on probability, statistics, stochastic processes,
reinforcement learning and game theory.

In particular, prevent the workflow from treating innovation as blind neural
network or module accumulation. Require research directions to address the
actual scientific objects, including:

- how changing agent membership creates distinct kinds of nonstationarity,
  information loss, identity/state-ownership problems and credit-assignment
  problems;
- how variable skill duration changes the decision clock, temporal abstraction,
  effective action or option space, credit horizon and the classical
  exploration-exploitation problem;
- how multi-agent strategic dependence, coordination, symmetry and changing
  teammate/opponent policies affect claims and evidence; and
- how estimands, uncertainty, counterexamples, controls and identification
  should govern empirical conclusions.

Do not select a current project direction, propose implementation code,
authorize compute, reinterpret an active result or advance the formal CDC.
Audit the methodology only. Seek omissions, false dichotomies, decorative
module incentives and cases where a simpler recurrent, masked, belief-state,
parameter-sharing, option/SMDP or statistical explanation could account for the
same observation.

## Exact evidence allow-list

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md`
- `.agents/roles/RESEARCH_SCOUT.md`
- `.agents/roles/RESEARCH_INNOVATOR.md`
- `.agents/roles/RESEARCH_CRITIC.md`
- `.agents/skills/hmasd-independent-research-exploration/SKILL.md`
- `.agents/skills/hmasd-independent-research-exploration/references/parallel-research-workflow.md`

Read only these paths from the assigned `stage_commit`. Do not use repository
history, `CURRENT_WORK.md`, code, runtime evidence, formal review rounds,
scientific ledgers or unstated sources.

## Required response

Return every heading below exactly once.

### AUDIT_DISPOSITION

Exactly one of `READY`, `REVISION_REQUIRED`, or `UNRESOLVED`, with a concise
reason.

### SCIENTIFIC_OBJECTS

Define the minimum stochastic-game, partially observed, semi-Markov or other
mathematical objects an Explorer must name before proposing a mechanism.

### MEMBERSHIP_NONSTATIONARITY

Separate the scientifically different sources and consequences of changing
agent membership. State which distinctions, baselines and counterexamples are
mandatory.

### VARIABLE_SKILL_DURATION

State how duration, termination, clocks, option/action-space growth, temporal
credit and exploration-exploitation must be formulated and distinguished.

### GAME_THEORETIC_DISCIPLINE

State the strategic, coordination, symmetry, identity and policy-dependence
questions required for a multi-agent claim.

### STATISTICAL_DISCIPLINE

State required estimands, sampling units, uncertainty, identification,
comparators, negative controls and interpretation limits.

### MODULE_ADMISSION

Give a fail-closed rule for proposing a new network, latent, critic, scheduler,
termination model, reward, graph or attention module. Require the proposal to
state what it replaces, retains and adds, the mathematical problem it solves,
the simplest competing explanation and a discriminating consequence.

### CONJECTURE_AND_COLLABORATION

Define how broad directions become independent conjectures, how initially
independent work may later cross-pollinate, how provenance and competing
families are preserved, and how Critic corrections change subsequent work
without forcing convergence.

### EVIDENCE_PROGRESSION

Give the preferred progression among derivation, counterexample, existing
evidence, toy, bounded prototype and experiment, including stop and escalation
conditions.

### REQUIRED_CAMPAIGN_FIELDS

List the exact fields that should be present in campaign, conjecture,
Innovator-packet, Critic-packet and synthesis records so the methodology can be
checked mechanically without pretending to judge scientific truth.

### DANGEROUS_SHORTCUTS

List concrete failure patterns that should be rejected or explicitly weakened.

### RESIDUAL_AMBIGUITIES

List unresolved methodological choices. Use `none` only if genuinely complete.

### METHODOLOGY_PRINCIPLES_PACKET

Provide a concise numbered set of stable, imperative principles suitable for a
Skill reference. Each principle must include `principle_id`, `rule`,
`failure_prevented`, `required_record_fields`, and `critic_challenge`.
