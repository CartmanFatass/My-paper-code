# RISP-B3 target-bound tracking/relay External Gemini innovation request

```text
direction_id=renewal_indexed_score_plasticity
candidate=RISP-B3-TRG
science_revision=RISP-B3-TRG-SCIENCE-20260815-01
named_target=TRI-SECTOR-DELAYED-ACK-TRACK-RELAY
request_kind=MUTUALLY_BLIND_DIVERGENT_INNOVATION
provider_role=External Gemini innovator
conversation_relationship=continue_existing_RISP_Gemini_conversation
scientific_activity_started=false
```

This is an independent innovation consultation. Do not infer, quote, or
reconstruct another provider's question or answer. Do not validate code or
choose portfolio priority. Stress-test only the frozen science below.

## Frozen target-bound object

Two noncommunicating, parameter-sharing agents independently track a moving
target sector and relay a packet with one of three held beams. Episodes last
192 ticks. At a renewal the controller observes only elapsed time and the
external duration `k`, chooses a beam, and must hold it for `k` ticks. The
hidden target drifts each tick with probability `23/24` of staying and `1/48`
of entering either other sector, independently of the action. At completion,
the recipient returns ACK `Y=+1` with probability `4/5` if the held beam equals
the completion sector and `1/5` otherwise. Physical utility is `kY`. ACK is
unavailable until the hold ends, and only then may update private state before
the next duration/action. The target, future `k`, future reward, and other
agent are never observed.

One shared controller trains at `k={4,8}` and freezes for held-out `k=12` and
switches `4->12`, `12->4`. Each agent mixes a common bounded slow policy and a
private three-action simplex state equally. The recurrence packet contains old
state, selected action, completed ACK, old duration, and old boundary time.

Exact frozen `G` maps success to raw `(+30,-30,-30)` in selected-action order
and failure to `(-30,0,0)`, followed by a bounded rational affinity head. Under
a uniform local prior it has next-policy TV `40/171` after success and
`35/363` after failure. With target-motion eigenvalue `15/16`, its exact next-
hold value gains are

```text
(8/57)*(15/16)^k after success
(14/363)*(15/16)^k after failure,
```

positive for `k=4,8,12`.

The learned treatment initializes/decays its free `3x13` effective matrix about
`G`; the comparator initializes/decays an otherwise identical free matrix
about zero. Both matrices range over every finite binary64 `3x13` matrix and
have identical information, 39 trainable scalars, slow policy, head, loss,
AdamW work, update opportunities, and reset law. Both train for 512 updates
with physical-reward policy loss plus common weight-1 alignment toward the
completed-ACK/action G map. No old checkpoint, seed, coordinate, or result is
reused.

The same full panel contains an inseparable `CONTAIN-G-BOUND` cell: use the new
containing slow checkpoint with exact G and no further fitting. Compare it on
seen and target schedules against the same slow checkpoint with no recurrence,
outcome-independent fixed persistence, and an outcome-independent global-rate
map based on stationary ACK rate `2/5`. G must beat the within-seed best of
these alternatives in physical value by lower95 `>0.02`, retain oracle
headroom `>0.02`, and clear TV-fraction `>0.25`, positive-value fraction
`>0.55`, and mean value gain `>0.005`. A failure deletes completed-ACK
recurrence for this named target/package; a pass immediately opens the already
computed matched held-out/switched-k value comparison, never a standalone
transplant.

Each learned architecture also has intact, conditional-marginal-twin,
no-recurrence, fixed-persistence, and global-rate cells. The twin samples the
exact ACK probability conditional on its controller-visible history/action but
is independent of the recipient target, actual ACK, reward, and next state. It
preserves update opportunity and one-step ACK law while severing realized
lineage. Uniform and current-sector oracle are competence/headroom controls.

Only a complete 16-seed, five-schedule, 13-cell panel is interpretable. Both
learned intact arms must beat their within-seed best no/fixed/global control on
seen schedules and clear oracle headroom, action-TV, positive-value, and mean-
value gates on seen and target mixtures. Physical endpoints are time-weighted
held-out and post-switch values; partial values and renewal-indexed surrogates
cannot select a branch.

The positive branch requires qualified G, both qualified learned arms, anchor
intact advantage over containing, architecture-by-lineage interaction, anchor
intact-over-twin value, both learned arms over fixed/global alternatives,
anchor/contain equivalence under twin, and schedule nonharm. Other frozen
branches delete the recurrence component when G is not exploitable, delete a
harmful G-centered treatment, retain direct recurrence without G-prior
specificity, prefer a no-lineage/fixed/global alternative when equivalent, or
delete only the registered minimum prior claim. All claims are limited to this
finite target/package; there is no arbitrary-`k`, variable-`N`, coordination,
real-UAV, safety, or deployment claim.

## Divergent assessment requested

1. Give the strongest physically plausible tracking/relay counterexample in
   which the local G value certificate is correct but the complete external-k
   physical endpoint is harmed. Identify the exact frozen gate that catches it
   or the missing gate if none does.
2. Audit whether a negative `CONTAIN-G-BOUND` result justifies deleting the
   recurrence component for this named target, or whether slow-policy failure,
   target drift, ACK noise, and fixed/global competition remain confounded in
   a way requiring a science-bearing correction.
3. Find the strongest no-lineage explanation that could survive the
   conditional-marginal twin. Decide whether fixed persistence and the
   stationary `2/5` global-rate control are adequate, and give an exact better
   control only if it remains information-, opportunity-, support-, and
   physical-work compatible.
4. Stress-test literal function-class equality, the target/posterior equations,
   switch windows, physical-time weighting, complete-panel gates, and branch
   precedence. Name any overlap, uncovered outcome, or outcome-changing choice.
5. Propose a strictly more credible target-bound recurrence only if it uses the
   same completed recipient information, shared-parameter external-k setting,
   equal-function-class containing comparison, and direct physical-value
   endpoint. It may not introduce a standalone assay, sign-reversed center,
   second surface, continuous-UAV simulator, or future leakage.
6. State the strongest remaining alternative, exact claim ceiling, and one
   prospective observation that would retain, modify, or delete this named
   recurrence component without tuning on a result.

Return exactly one leading line:

```text
RETAIN_FROZEN_COMPOSITE
```

or

```text
SCIENCE_BEARING_REVISION_PROPOSED
```

Then give the counterexample, proposed correction if any, strongest
alternative, discriminator, and claim ceiling. Do not review files, tests,
random-number addresses, runtime, or compute resources.
