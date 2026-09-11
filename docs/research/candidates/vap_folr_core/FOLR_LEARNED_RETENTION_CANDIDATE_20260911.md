Claim under consideration: learning one event-conditioned survivor-memory attenuation scalar may improve finite-training native return over the existing event-aware recurrent RETAIN policy on the explicit public-lifecycle easy Traffic Junction host.
Binding MARL structure: (a) roster change, under multi-agent partial observability; an agent must act from its own history while other physical trips enter and leave and partners learn jointly.

## 1. The direction question and recommendation

Should this particular learned-retention family be opened narrowly for a later,
separately allocated B comparison, or should FOLR make no new family investment?
The DM recommends the narrow opening as an **unexecuted close call**. A scalar
operation at a known public event makes a concrete finite-learning question;
ordinary event-aware RETAIN is a strong alternative because its GRU already learns
input/history-dependent gates. The source supplies no new information advantage
and no theorem that either architecture contains or improves on the other.

This is the one design/question/intake chain selected by Portfolio response
`0dbbcbf807509ccc34a3a1de353114be88896897` §5 and mapped at
`bb40797dc5312641ac640664cbf7c2bd174d9815` §FOLR. It is a candidate note, not a B
card, freeze or implementation specification authorizing work. Only the original
`em:vap_folr_core:convergence` node decides the family disposition. The current
allowance is **zero implementation and zero numerical work**, including after an
OPEN/RECAST. The fixed .5/easy-host/5000-training/128-final recipe remains narrowly
paused by the prior complete Convergence decision; this is not a third half pair
or a re-audit. Portfolio lifecycle, priority, capacity and recast counts do not
change through preparation.

## 2. One proposed operation, available information and physical identity

Let `x_it` be the current 64-wide `relu(fc2(...))` input already computed by
`Actor.forward`; it uses observation-masked local attention, own previous action,
the completed public lifecycle event and own birth. Let `c_it` identify a true
continuing physical trip, `e_t` the public event from the preceding completed
transition, and `hbar_it = c_it * h_i,t-1`. The proposed scalar is shared across
agents and times:

`g_it = sigmoid(w_x · x_it + w_h · hbar_it + b)`

`h_in_it = g_it * hbar_it` when `c_it and e_t`, otherwise `hbar_it`;
then apply the ordinary `GRUCell(x_it, h_in_it)` and existing entity mask/Q head.
There are 64 + 64 + 1 = **129 additional trainable coefficients**. The one proposed
initialization is zero weights and bias `log(99)`, giving .99 attenuation at an
eligible event. This is near RETAIN, not exact initial-policy equality or a tuned
value. No coefficient, bias, seed or architecture search is proposed.

Physical newcomers have no incoming history or preceding trip's action. A true
survivor retains its own state until this proposed operation; departures and
padding carry none, and a departure/refill in the same slot starts a different
trip. No gradient/state may cross distinct trips. The scalar receives only its
own available input/history; no future birth, unobserved other-agent history or
global critic state is added. The public event is already an explicit shared
information extension of this host, not a recovered privilege in original CAMA.

The causal path being proposed is completed native event -> continuing trip ->
legal current input and own history -> altered incoming GRU state -> changed Q
and action -> native traffic consequence and team reward. During real learning,
the shared actor and mixer optimize together and partners co-adapt. A return
change would concern that whole learned package; it would not identify stale
memory, an optimal useful-history fraction or a causal effect of event timing.

## 3. The competent null and source requirements

Use the existing **event-aware RETAIN** with the same local/public inputs,
lifetime handling, attention/GRU/Q path, learner, native reward and exposure as
the primary legal null. It already receives event/own birth before `fc2`, and a
GRU already gates using input/history. The candidate therefore adds an unproven
inductive bias and 129 parameters. An extra gate could be redundant, attenuate
useful memory, saturate near .99 or worsen optimization. Conversely its direct
event-boundary attenuation could make a useful finite-training policy easier to
learn. Neither position requires a novelty claim or an expressivity proof.

Source inspected at `c6be208cd514b5d12fb13c7637e2d6376de11eb6`: `model.py`,
`environment.py`, `attention.py`, `collection.py`, `learner.py` in
`experiments/candidates/vap_folr_core/public_lifecycle_b01/`, and
`scripts/run_folr_public_lifecycle_b01.py`. Their relevant current bytes match.
Collection carries actor state one step at a time; replay stores complete
episodes and reconstructs from zero. Both online and target actors call the same
forward law. A later implementation must preserve that consistency, target
state-dict copying, RMSprop inclusion of gate parameters and checkpoint contents.
It must preserve common actor/mixer initial parameters and isolate additional
gate-constructor RNG draws; the actor is currently constructed before the mixer.
Existing episode/minibatch sampling and native/action RNG consumers stay intact.
These are design requirements inferred from source, **not runtime acceptance of
an unimplemented candidate**. No model, fixture, test or optimizer was created.

The node may reject the candidate or justify a stronger legal comparator in this
same question. It must name that comparator and the decision it would protect;
an extra ablation or capacity-matching prerequisite is not automatic for B. Do
not silently replace the specified scalar gate with a different mechanism.

## 4. Evidence, headroom and possible interpretation

The fixed-half evidence stays separate and keeps its original absolute MEI 1:

| Completed B pair | RETAIN final mean | HALF_EVENT final mean | HALF minus RETAIN | Original branch |
| --- | ---: | ---: | ---: | --- |
| HALF-B01 | 1.68046875 | 3.2459375 | +1.56546875 | HALF_EVENT_ABOVE_MEI |
| HALF-B02 | 9.471796875 | 5.17875 | -4.293046875 | RETAIN_ABOVE_MEI |

Their training means also point in opposite directions, and attenuation occurred
in both. Neither observation establishes adaptive retention's necessity or its
failure; no learned scalar was tested. The older full-EVENT and 32-final histories
remain distinct. Both HALF forecasts were WITHIN_MEI at low confidence and missed;
the owner prediction was not taken. No new performance prediction is scored here.

Matching tuned upper-minus-baseline headroom is absent. The proposed future MEI
is provisionally 1 native return unit, one tenth of the host's collision penalty;
any later selected card must justify its own margin. If a future learned-gate
comparison exceeds that margin, recommend a bounded learning follow-up while
retaining the single-pair limit. Inside it, report no practically separated
package on that fit; do not claim equivalence. An opposite result favors RETAIN
on that fit and supports stopping or revisiting this specific added operation,
without rejecting all memory adaptation. These are descriptive possibilities,
not a frozen future decision rule or a current execution selection.

## 5. Decision value and dominant work, without an allocation

A possible later minimal real B would train one independent pair, learned gate
versus event-aware RETAIN, for 5,000 episodes / 100,000 ticks / 4,969 updates each,
then 128 final greedy episodes each. That is 2 learners, 10,000 training episodes,
9,938 updates, 256 final episodes and 205,120 team ticks. The retained base law is
66,783,360 online/target replay GRU rows and 1,076,880 acting rows, **plus gate
work on the new arm**. It has no nested search, exact upper, full-support census,
causal audit or extra validation experiment. Actual gate evaluation cost and
later necessary engineering checks remain unknown.

Such a pair would directly observe whether this concrete architecture changes a
finite learned-policy package against the competent null. Evaluation episodes
are conditional samples, not independent fits. Same seed labels do not identify
paired post-action worlds: native traffic and replay share action-dependent RNG
consumers. No episode-wise matched-world causal estimate or stable superiority
would follow. A positive result is not a prerequisite for opening or measuring B.

The strong competing choice is no new family investment, preserving RETAIN and
the exact fixed-half pause. It spends no new empirical allocation but leaves the
adaptive architecture unmeasured. The case for opening is the direct, bounded
decision value of the possible pair, not the mere smallness of 129 coefficients
or an assumption that document/Pro work is cheaper. Historical HALF-B02 native
wall 1517.20 s and known support 67.6955750 s are context only: new wall, memory,
support and cap are **unknown and unallocated**, and the old 3900 s is not renewed.
Authoring, Pro and intake effort is unmeasured. No extra cost experiment is asked.

## 6. Scientific reading and limits

Current FOUNDATIONS §§2–4,6 and the empirical topic support the own-history
information boundary, finite-learning package comparison and independent fit as
the empirical unit. The local-literature route first searched catalog metadata.
The verified My-lib default records are synthetic fixtures; this is no negative
claim about its unindexed real holdings. InstSci's current catalog has 190 rows;
11 matched the stated recurrent/retention/memory/gated/Sable/CAMA search. CAMA
`MARL-0409.json` has SHA256
`ee9d7b6adc209780a1bb0ad95d73332e9fe4456bfe7ed738926510f70448b20b`.
Direct reads of PDF pp2–3 (kids23,45–46) support local observation-action history
and a GRU; pp16–17 (kids308–309,312–313) support the modified traffic host and
collision penalty. This strengthens the recurrent null and limits original-CAMA
claims. It does not validate the new public-event protocol or the proposed gate.
No unviewed Sable passage or library-wide novelty result is asserted. Exact
retrieval, source and integer-count facts are in this question's `FACTS.json`.

Engineering Scope Spec §4: this documentation-only object needs none. The next
action is one fixed original-node question and complete conformance intake, or
an exact access/specification conflict return. It creates no automatic successor.
