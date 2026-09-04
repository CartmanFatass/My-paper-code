# SCDMP D6 event-phase duration-action relevance A02 — CM intake (2026-09-04)

- Object: `SCDMP-D6-EVENT-PHASE-DURATION-ACTION-RELEVANCE-A02`
- Evidence class: A/RECON
- Technical candidate SHA: `b58c93714b0f5a8229b54024254c1bc1ac94f3e0`
- CM disposition: technically accepted
- Scientific result: none yet
- Engineering scope §4: none

## What this intake checked

1. The CM diff is limited to the card's owned A02 package, runner, tests and the outcome-blind cost
   row. It changes no core file and imports no stopped-B learner, model, optimizer, checkpoint or
   scientific state.
2. The existing whole-hold ABI could not expose the two intra-hold event ticks. CM and an
   independent review rejected early/late event substitution and short-`k` state mutation. The
   accepted A02-local composite export instead calls the unchanged primitive transition and
   existing HR/RH plus zero-tick release operator at the exact frozen event tick inside a derived
   translation unit. The only other canonical-source difference is the card's `.88→.92`
   `TAU_LEAK` binding. Native equations, dtype, terminal order, action semantics and core bytes are
   unchanged.
3. The fixed root `9173`, separated K7/K13 source domains, exact source ticks `91/182/273`, public
   countdowns `7/78`, clock policies, graph/action map, primitive-indexed evaluation domain and
   tape sharing are present. The runner publishes all 768 endpoints, twelve `K_b,d` rows, both
   `K_d`, four state-count quantities, latency, utility, terminal/failure rows and complete native
   inventory before applying the exact nine-branch rule.
4. The independent reviewer found one material exception-path defect: a broad runner catch could
   erase already executed counts/endpoints. The narrow repair moved counting to its execution
   owners, preserves partial inventories, emits explicit zero inventory before a census, and keeps
   a completed payload while forcing invalidity after cleanup failure. Re-review closed the finding
   with no new material issue.
5. The sole focused invocation reported `10 passed, 1 warning in 3.79 s`. It covered all nine
   ordered branches and one toy native smoke. The smoke directly observed an aligned HR/`k=7`
   event with latency `0` and an intra-hold RH/`k=13` event with latency `6`; both event and public
   order facts were present. It executed one toy source, two toy missions and 721 native
   transitions, and created no scientific state, tape, result root or A02 branch.
6. The smoke measured
   `t_native_mission=0.0013297499972395599 s`, giving the prospective fixed-panel projection
   `P=2×(t_native_mission×770)+60=62.04781499574892 s < 1,800 s`. Peak RSS was not measured by the
   smoke; this does not affect a non-resource scientific claim. The formal invocation still must
   take a fresh `4 GiB` physical/effective admission and is bounded by the hard `1,800 s` cap.
7. Static budgets are 956 non-test lines below 2,000; runner 188 below 600; tests 66; and
   conservative orchestration `261/956=27.30%` below 30%. No default-prohibited §4 machinery was
   added.

## Observation and evidence boundary

Direct technical observation establishes that the exact calendar can be represented through the
A02-local native interface, that both aligned and intra-hold timing paths compile and execute, and
that the runner's cost projection is below the cap. This is engineering conformance, not mechanism
value.

No fresh resource admission, six-state source population, 96 scientific tapes, 768-mission panel,
scientific endpoint, `K` quantity, A02 branch or result artifact has been observed. Technical
acceptance cannot establish duration-action relevance, D6/D8 value, learner value, B authorization
or Portfolio action.

## Protected launch identity

The single scientific invocation, if launched, is bound to SHA
`b58c93714b0f5a8229b54024254c1bc1ac94f3e0`, seed `9173`, projection
`62.04781499574892`, and the complete frozen card. Its new result root must be absent before launch.
The runner itself performs the mandatory memory admission before native host construction. The
invocation must be detached, must not be retried or resumed in place, and must publish one summary
or a declared no-result/invalid/population branch. A failing step is not classified from error text
alone.

## Decisions this intake produces

Object-tier options:

1. **(a), recommended:** accept the reviewed implementation and cost row, then launch exactly one
   detached scientific invocation at the accepted SHA with fresh admission and a new root;
2. **(b):** repeat the same tests or smoke without a named unresolved defect;
3. **(c):** reject or recast the exact Pro-admitted object despite closed technical review.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** This is reversible in the
sense controlling A/RECON requires: it changes no frozen scientific meaning, A has no consumption
state, and a technical defect would quarantine only its evidence attempt. Option (b) would spend
another invocation without a named discriminator; option (c) would locally override a complete
direction-tier decision.

After a valid result, the DM applies the first matching frozen branch and reopens the same
convergence binding. No A02 branch locally authorizes B.
