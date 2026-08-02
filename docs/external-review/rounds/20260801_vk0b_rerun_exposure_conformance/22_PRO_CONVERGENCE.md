CONFORMANCE
CONFORMS — the amendments close the V-K0B exposure-rerun design-conformance check

The amendment section resolves every blocking item from the preceding CHANGES_REQUIRED ruling without changing the scientific experiment. It preserves:

the same six training seeds;

the same configuration and architecture;

640,000 environment interactions and 1,000 outer updates per seed;

three high PPO passes per update;

the frozen evaluation bank and 32/32 serialization-order split;

the support and competence floors;

the bootstrap;

the first-match result mapping;

and the prohibition on pooling with the historical invalid run.

That is the correct handling of Outcome B: the missing fields were never accumulated and could not be reconstructed, so an identically specified operational rerun with added non-behavioral instrumentation is admissible. The historical V-K0B result remains invalid rather than adverse-valid, while V-K0A remains accepted standing evidence.

Previous blocking item	Closure
Shared optimizer did not prove actor/value exposure	Closed by A-W6-1
High-pass statuses did not exhaust all opportunities	Closed by A-W6-2
“High-check sequence” was underdefined	Closed by A-W6-3
One ending-authority scalar lost concurrent events	Closed by A-W6-4
Actual-exposure block lacked an immutable evidence chain	Closed by A-W6-5
Counter instrumentation might alter training	Closed by A-W6-6

No new protected scientific decision is introduced.

A-W6-1 — shared optimizer

Closed.

The amendment correctly treats high_opt as one shared actor/value optimizer and maps its step count onto both registered exposure fields. It does not fabricate two optimizer objects or change the training architecture.

The load-bearing addition is the complete parameter-coverage certificate:

every trainable high-actor parameter in high_opt
every trainable high-value parameter in high_opt
every such parameter has optimizer state
all step values equal
shared step count = 3000

This resolves the precise gap identified in the preceding ruling: uniformity over whatever optimizer-state entries happen to exist is not sufficient.

At Gate B, high_optimizer_parameter_coverage_ok must be derived from exact parameter identity or membership, not merely from equality of aggregate counts. That is a realization check, not an open design choice.

A-W6-2 — exact optimizer exposure

Closed.

The amendment now defines an exhaustive partition:

N
attempted
	​

=N
stepped
	​

+N
skipped
	​

+N
aborted
	​

.

It also freezes the exact valid exposure:

completed outer updates        = 1000
high passes attempted          = 3000
high passes stepped            = 3000
high passes skipped            = 0
high passes aborted            = 0
shared optimizer steps         = 3000

Most importantly, an honestly recorded skip is no longer treated as excusing reduced exposure. Any nonzero skip or abort invalidates the run under the unchanged contract.

That correctly preserves the distinction between:

accurately documenting a deviation; and

satisfying the registered exposure.

A process that aborts before it can serialize the complete terminal block is also fail-closed through A-W6-5: absence of the required block or source manifest cannot be interpreted as zero aborted passes.

A-W6-3 — high-check sequences

Closed.

The amendment gives “high-check sequences” the correct executable meaning:

one completed shared autoregressive edit sequence whose full two-agent token vector was committed to the high-check buffer.

It correctly includes initial assignments and excludes due calls that never produce and commit a complete sequence.

The structural identity

N
KEEP
	​

+N
SET
	​

=2N
high check sequences
	​


is the right conformance invariant for the frozen two-agent source.

No per-agent sequence object is needed. The agents contribute tokens inside one shared ordered sequence.

A-W6-4 — ending semantics

Closed.

The two-field representation removes the loss identified in the previous design:

incumbent_end_authority_at_check
post_window_end_authority

A final-check voluntary SET followed by episode termination can now record both events rather than forcing one to overwrite the other.

The vocabulary is also corrected:

initial_assignment remains a segment-origin fact;

it is not an ending authority;

none_open explicitly records the absence of an ending event;

structurally unreachable authorities remain legal schema values without being fabricated.

The vk0-trace-2 schema may leave these fields unused by the present V-K0B statistics. Their role is durable semantic correctness for later natural-hazard or censoring analysis.

A-W6-5 — immutable exposure provenance

Closed.

The chain is now complete:

training run manifest
    -> source-labelled actual_exposure block

launcher manifest
    -> source run-manifest hash
    -> checkpoint hash
    -> exposure_audit status

evaluation manifest
    -> exact copied exposure block
    -> exact source-manifest hash

analyzer
    -> independent validation before row 2

The allowed evidence-source labels are appropriately narrow. In particular:

config
nominal
expected
derived_from_budget

cannot masquerade as actual exposure.

The schema version vk0b-exposure-1 makes this evidence surface independently identifiable and prevents the historical incomplete manifest from being silently accepted.

A-W6-6 — noninterference

Closed.

The proof-sized witness is the right Gate-B control:

Identical initial state and seed must produce byte-identical policy tokens, actions, rewards, optimizer evolution, and model parameters with instrumentation enabled versus disabled, apart from the new counters and manifest fields.

This establishes that the counters observe rather than alter training. It is implementation conformance, not a new scientific experiment.

The witness should compare complete optimizer and model state after at least one exercised high update, not merely final scalar losses or step counts. That is a Gate-B realization detail.

INTERPRETATIONS
1. Shared high optimizer
Accepted

One shared high_opt satisfies both actor and value exposure fields when—and only when—the complete parameter-coverage certificate passes.

The scientific record should state:

high_optimizer_semantics = SHARED_ACTOR_VALUE_OPTIMIZER
high_actor_optimizer_steps = 3000
high_value_optimizer_steps = 3000
high_optimizer_steps_shared = 3000

These are three semantic views of one measured counter, not three optimizer executions.

2. High-check sequences
Accepted

The binding definition is:

completed shared autoregressive high-check decisions committed to the buffer

It is not:

the number of maybe_assign_skills calls;

the number of due predicates;

a separate sequence count for each agent;

or the number of continuation-value refreshes.

3. Counters count but never gate training
Accepted

The trainer must not alter, retry, skip, stop, or repair an update because a scientific exposure counter changed.

Training proceeds according to its ordinary execution. The launcher and analyzer subsequently decide whether the resulting run matches the frozen scientific contract.

This preserves the project’s evidence rule: instrumentation measures actual learning opportunity without creating that opportunity. Equal environment steps alone are not sufficient; optimizer exposure must also be recorded.

CONVERGENCE_DECISION
TOUCHPOINT_2                           CONFORMS

IDENTICAL-CONTRACT RERUN ROUTE         FROZEN
SHARED HIGH OPTIMIZER SEMANTICS        FROZEN
EXACT HIGH-PASS EXPOSURE               FROZEN
COMPLETED HIGH-SEQUENCE DEFINITION     FROZEN
SEGMENT-END REPRESENTATION             FROZEN
ACTUAL-EXPOSURE EVIDENCE CHAIN         FROZEN
COUNTER NONINTERFERENCE REQUIREMENT     FROZEN

NEW PROTECTED DECISION FOUND           NO
ANOTHER PRO DESIGN ROUND REQUIRED      NO

The next permitted boundary is the proof-sized implementation/Gate-B conformance package. It should include explicit negative witnesses for:

one actor or value parameter absent from the shared optimizer;

one parameter lacking optimizer-state step data;

one skipped or aborted high pass;

a sequence/token-count mismatch;

an inadmissible exposure source label;

a modified or mismatched source-manifest hash;

a final-check SET carrying both ending events;

and instrumentation-on versus instrumentation-off trajectory equality.

Those are tests of the frozen design, not new scientific choices.

V-K0A continues to stand. The historical V-K0B result remains invalid. V-K0C, V-K1, order-randomized training, and the constrained renewal-class mechanism remain held until the identical-contract rerun produces a valid result. This ruling authorizes neither implementation nor the rerun.