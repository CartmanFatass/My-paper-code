# The Codex science workflow, reviewed as a research process

Scope: `AGENTS.md`, the fifteen `.codex/agents/*.toml` definitions, the four science skills under `.agents/skills/`, the `scripts/hmasd_*.py` gates and schemas, `docs/research/portfolio/` (PORTFOLIO.md, 25 decision records, two handoffs), `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`, and the intake families as they appear in one direction (`ucope`). Facts below come from a read-only inventory; judgments are mine.

## 1. What the workflow is

Authority. The user request is the authority; repository documents are methods, not permissions. Root is the single coordinator and integrator. Three persistent ChatGPT Pro conversations are the scientific decision nodes: `em:<direction>:innovator` (selects the next object before it is frozen), `em:<direction>:convergence` (decides the direction-local conclusion), and `portfolio:cross_direction` (lifecycle, priority, capacity). The rule that matters most: "A complete Pro decision is final for its node. Root, DM, and EM prepare evidence, execute the decision, and record it rather than overriding it locally."

Execution roles. Fifteen Codex agent definitions with deliberate authority boundaries. Deciders and preparers: direction manager (DM), evidence/experiment manager (EM), code manager (CM). Read-only analysts: cm-scout, design-reviewer, research-critic, research-innovator, research-principles-analyst, research-scout, reviewer, workflow-designer. Writers with fences: implementer (CM-frozen semantic edits only), routine-implementer (behaviour-preserving edits; must refuse any change to backend, dtype, operation order, batching, topology, or the performance disposition), verifier (writes only to a proof root). One executor: experiment-operator, which launches exactly one result-bearing command and "never retry or create a second process".

Transport. Two skills carry evidence to and from the Pro nodes: the prompt author renders an evidence packet (`PROMPT_BODY.md`, `HANDOFF.json`, manifest) and dispatches it to a fixed transport task; the transport skill runs a one-to-one binding between node and conversation with a state machine from RECEIVED to ARCHIVED. Portfolio changes require a `portfolio:cross_direction` decision.

Gates. Mandatory: the 4 GiB memory admission before every result-bearing launch. Conditionally mandatory: `hmasd_run.py prepare/execute/reconcile/promote` when it is the frozen entry point; the operator's terminal observation schema; CM technical acceptance, whose doctrine is "Functional readiness does not imply performance readiness". Optional: capability catalogue, file fingerprint.

Evidence classes. A/RECON, B/EXPLORE, C-BENCH, C-TRANSFER, C-FORMAL. Two rules in the spec are the ones the practice keeps colliding with: "The EM MAY revise architecture, hyperparameters, reward-independent mechanism details, host, budget, measurement, and comparator between named runs after seeing earlier results" (B adaptation is legitimate exploration), and "Only a valid, complete observation of an explicitly frozen C object consumes that exact object" (consumption is a C concept).

Document families. DIRECTION → science card → innovator intake → portfolio selection / value / qualification intakes → CM technical acceptance → prospective contract or freeze → result evidence → convergence decision → closed, or revision-required and loop back.

## 2. What it produces, measured

| Measure | Value | Source |
| --- | --- | --- |
| UCOPE, direction created → first result document | 6 days (2026-08-25 → 08-31) | git log |
| UCOPE, commits touching its docs folder | 30 | git log |
| UCOPE docs folder today | 35 files, 56,982 words | inventory |
| of which decision-type documents (science cards, innovator, CM acceptance, prospective, convergence, closed, revision, value/qualification) | 23 | inventory |
| of which result documents | 4 | inventory |
| Portfolio decision records, 2026-08-28 → 09-01 | 25 | inventory |
| Commits per day touching `docs/research`, 08-27 → 09-01 | 16, 62, 34, 2, 14, 18 | git log |
| Valid learner observations on first-wave objects, whole wave | 1 (UCOPE B1) | first-wave review |
| Wave quarantines that were telemetry or validator failures | 4 of 4 | first-wave review |
| Scientific versus scaffolding lines across the five implementations | about 20k versus 44k | first-wave review |

Read together: the workflow turns a scientific question into a valid learner observation at a rate of roughly one per wave, and it turns Codex usage into documents at a rate of about six decision documents per result document. The commit rhythm (62 one day, 2 two days later) and the safe-stop rule keyed to "Codex account usage reaching 0%" say what the binding resource is: not compute, not ideas, but the usage quota of the executing agents. That is the resource the process should be optimizing, and nothing in PORTFOLIO.md models it (capacity is declared `UNBOUNDED`, every row is owned by ROOT, and there is no per-direction budget).

## 3. What is right about it

- Quarantine discipline and the "incomplete attempt is not a consumed object" rule prevented at least three misreadings this wave (VNFC R01's near-tie, SCDMP RUN-01, the UCOPE early roots). This is the workflow's best feature; keep it.
- The evidence classes are well chosen and the B-adaptation rule is exactly right for exploratory MARL work.
- Provenance: run manifests, admission receipts, code SHAs, and terminal observation schemas make every number traceable. This is rarer than it should be in academic MARL.
- Independent read-only critics and reviewers with no acceptance authority. The design-reviewer and research-critic roles are the right shape.
- The implementer fences (no numeric, RNG, backend, or topology changes without CM freeze) protect bitwise claims where they exist.

## 4. Where it fails, and why

F1. The decider cannot see the code. The Pro nodes decide from rendered packets. Everything a node must trust therefore has to be encoded as a document, a validator, or a create-once artifact, because the node cannot open a file and check. That is the mechanism that generates 44k lines of scaffolding: packet-only trust substitutes bureaucratic completeness for inspection. The clearest case this wave: the UCOPE Convergence chose a coordinate-whitening discriminator on the unchanged budget, while the source shows an optimizer-exposure shortfall of about an order of magnitude (lr 3e-4 for 160/320 steps against order-1 initial coefficients). The packet carried the learning rate and the step counts; it did not carry the initialization scale or the displacement arithmetic that connects them, and a decider who cannot open `model.py` has no way to do that arithmetic. The packet format decided the decision.

F2. "Record rather than override" has no dissent channel. When a Pro decision is wrong on an engineering fact, Root's only lawful moves are to execute it or to spend another Pro round. SCDMP's replacement-identity blocker cost an Innovator round to reach a conclusion the spec already implied (B has no consumption state). A one-page engineering dissent attached to a decision, which re-opens the node with the missing fact, would have cost one message.

F3. C-FORMAL machinery applied to B objects. The spec permits adaptation between named B runs; the practice freezes B objects with hash chains, 75-row journals, byte manifests, and "AUTOMATIC_BUDGET_ENLARGEMENT=false". The result is that a B object cannot test its own leading alternative (UCOPE's exposure), and a completed B run can be discarded unread for a telemetry race (SCDMP RUN-01). Consumption is a C concept; freezing is a C cost.

F4. Telemetry as invalidator. The operator's "never retry" rule is right for outcome-informed retries and wrong for instrumentation races. Four of four quarantines this wave were telemetry or validator failures; none was scientific. The spec already says a technical failure is "no scientific observation", which means the returns of a run whose telemetry failed are still returns; the practice treats the whole artifact as poisoned.

F5. Decision documents outrun results. Twenty-three decision-type documents against four result documents in one direction, three prospective contracts for four results, four convergence intakes. Each document is a Pro round or a Codex task; each costs the binding resource. Several families overlap (portfolio selection, value, qualification, innovator) and could be one object card.

F6. Fifteen roles for a five-direction wave. The roles that produced value this wave are scout, reviewer, implementer, operator, critic, and the two Pro nodes. The DM/EM/CM layering adds an intake document at each handoff without adding a check that the reviewer or critic does not already perform.

F7. No "learnable" gate to match the "performance-ready" gate. CM's doctrine that functional readiness is not performance readiness has no scientific twin: nothing checks, before a B object is frozen, that the learner can move far enough in its budget (exposure arithmetic), that the host margin exceeds the learner's resolution, and that an oracle achieves the competence bar. Every first-wave competence failure would have been caught by that check.

## 5. Recommendations, in the order to adopt them

R1. Two contracts, by class. A two-page B-run contract (code SHA, config, seeds, admission receipt, resource ledger, raw per-episode CSV, curves, competence flags, descriptive statistics, adaptation ledger). The full create-once, byte-manifest, telemetry-invalidation contract only for named C objects. This is already what the spec says; make the templates match it.

R2. A learner exposure card in every packet. Machine-generated, one page: parameter count, initialisation scale, optimizer, learning rate, steps, batch, displacement budget (lr × steps), data volume per parameter, host margins, competence criterion, oracle attainment. Pro nodes then decide with the facts that decided this wave's outcomes. Add the raw curves as an image or a table, never only a verdict string.

R3. An engineering dissent record. Root or CM may attach `*_ENGINEERING_DISSENT_<date>.md` to any Pro decision, stating the missing fact and the proposed amendment; the transport re-opens the node with that one document. "Record rather than override" survives; the fact reaches the decider in one message instead of a round.

R4. Telemetry becomes a recorded field. A missing or failed telemetry field is a recorded defect on the run, never grounds to discard returns; the run's evidence class may be downgraded (no performance claim), not annulled. The operator may retry a run whose failure class is instrumentation, under a fresh named attempt, without a Pro round.

R5. A learnability ladder as the default A/RECON before any B freeze: oracle attains the competence bar; exposure arithmetic passes; one-seed smoke at a tenth of the budget produces a moving curve; margins exceed the learner's resolution. Cheap, mechanical, and it targets the failure mode that consumed the wave.

R6. Model the real capacity. Replace `UNBOUNDED` with a per-wave usage budget per direction, record usage consumed per valid observation, and rank directions by observations per unit usage. The first-wave figure is one valid learner observation for a wave's usage across five directions; the number should be on the portfolio page.

R7. Merge document families. One object card replaces science card plus innovator plus selection plus value plus qualification; one convergence per result document; no prospective contract for B runs beyond the two-page contract. Target: at most two decision documents per result document.

R8. Reduce the roster. Keep scout, reviewer, critic, implementer (with fences), operator, verifier, and the Pro nodes; fold DM into Root and EM into the object card owner. Re-add a role only when a wave shows a check nobody else performs.

R9. Keep everything in section 3. The quarantine rule, the evidence classes, provenance, the implementer fences, and read-only critics are the parts to protect while removing the rest.

## 6. The one-sentence verdict

The workflow is a good pre-registration and provenance system that has been asked to do trust-by-document for a decider that cannot inspect, and that has been priced in the wrong currency; fix the currency (usage per valid observation), give the decider the exposure card and a dissent channel, and reserve freezing for C.


## 7. Addendum, 2026-09-02: the owner's calibration

After reading this review the owner set the research paradigm explicitly, and it is now recorded as §11 of `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`. The owner's diagnosis matches F3 and F7 but is stated as a positive rule rather than a defect: MARL work here starts from an inspiration in a simple setting (bandit, single agent, closed-form toy), goes straight to one-to-three-seed B runs on the real learner, and reserves contracts, oracle comparators, held-out splits, and failure boundaries for the moment a repeatable signal is promoted to a paper claim. The owner also set the theory ceiling: no proofs of roster invariance or duration-independent semantics; at most a suboptimality bound for the scheme as implemented, with assumptions matching that scheme. Suboptimal schemes are legitimate treatments.

What that does to the recommendations. R1 (two contracts by class) and R5 (learnability ladder before a B freeze) are now spec text, with one reduction: §11.4 keeps only the exposure line, the §4 integrity requirements, nonzero learner counts, and resource admission as things that may hold a B launch. R2 (exposure card) survives as that one line. R3 (dissent record), R6 (usage as the currency), R7 (merge document families), and R8 (reduce the roster) are process changes the calibration supports but does not enact; they still need an `AGENTS.md` and `.codex/agents` edit. R4 (telemetry as a recorded field) is explicitly left open in §11.4 because it touches the quarantine doctrine, which the owner has not revisited.

Why the previous paradigm set the bar too high. Every Pro decision node saw a rendered packet and no code, so every trust question was answered with a document or a validator; C-FORMAL machinery was the only kind that could be checked from a packet, so it became the default for everything. The calibration reverses the default: B is the entry class, and formal objects need a named claim that requires them. The measured cost of the old default is in section 2 above: one valid learner observation for a wave's usage across five directions.
