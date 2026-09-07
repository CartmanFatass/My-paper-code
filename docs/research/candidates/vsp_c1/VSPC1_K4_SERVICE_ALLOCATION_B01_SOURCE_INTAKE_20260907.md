# VSPC1 SERVICE-ALLOCATION-B01 — source/card conformance intake, 2026-09-07

**Decision: accept the integrated implementation as conforming to the selected card.**
This is an object-tier technical decision under P07-VSPC1-IMPLEMENT-01. The two seed402
execution calls remain undispatched; Portfolio's separate execution command is the next
routing step. No scientific result or performance sign is produced by this intake.

## 1. Authority and inspected evidence

- Frozen [science card §§2–7](VSPC1_K4_SERVICE_ALLOCATION_B01_SCIENCE_CARD_20260907.md)
  and [five-item CM handoff](VSPC1_K4_SERVICE_ALLOCATION_B01_CM_HANDOFF_20260907.md),
  integrated at `a66351805`; implementation assignment at
  `3e415347f7268c048b2015a9594d47be8fa876ba` supersedes preparation-only dispatch wording.
- Source/test commit `63b8a6888e780f06d783bd900e052f9f08cf2d9f` and complete
  [CM technical acceptance](VSPC1_K4_SERVICE_ALLOCATION_B01_TECHNICAL_ACCEPTANCE_20260907.md)
  at `cf4e9f488ea103e8ebac5321918c9ce84460fca1`.
- Root integrated those returns at `d91fec012fa3e25f47a8a9eec50cc1a4d32fee47`.
  Compared the integrated card, source, tests and technical record against the accepted
  source returns: no byte change on those surfaces. Prior reactive-B01 source remains intact.
- DM read all four changed source/test files and the complete technical record; inspected
  saved synthetic configuration and publication JSON directly, without rerunning CM checks.
  CM's independent reviewer read the implementation, card, tests and saved artifacts and
  returned no material finding. That review is engineering scrutiny, not empirical replication.
- Applied evidence-spec §§4, 5.2, 11.4, 11.7–11.9 and engineering-scope §§3–5. No concrete
  conflict with the card, current owner instruction or applicable specification was found.

The card §7 acceptance rule applied verbatim is:

> Acceptance protects the changed three-queue transition/conservation and cyclic partner tie;
> simultaneous old-h decisions; held actions and actual terminal/segment targets; equal
> episode/period loss; three-action scoring and declared RNG separation/pairing; rule legality
> and its own endogenous trajectories; and readable endpoint/contrast/SE/AUC/branch publication.

The selected experiment's result branches were not applied to synthetic fixture values.

## 2. Source findings against the card

`experiment.py` preserves the three-queue host: partner selection uses the old public hold,
cyclic tie order and current queues; focal actions remain held for the declared period.
Simultaneous service removes one job per distinct chosen queue, or one joint job when choices
coincide, then applies arrivals, capacity clipping/overflow and the new public hold. Each
controller collects its own evolving queues and partner actions from paired exogenous tapes.
The LQ-EXCLUDE reference uses the legal observation, renews on its own opportunities and has
no learner, tuning or shared endogenous trajectory.

The FACTOR/GENERIC feature maps, initialization order and 372/393 trainable parameters match
the card. PCG64 namespaces and seed derivation preserve separate training/evaluation streams,
periods and exploration slots. Actual segment rewards are served jobs divided by 96; terminal
targets have no bootstrap; nonterminal Double-Q targets use online selection and frozen-target
evaluation. One optimizer step follows each batch of 16 complete episodes, with equal episode
and period weights, gradient clipping and the declared target-copy schedule. Checkpoints use
the current learner. Source records actual counts and prospective norm/movement measurements.

`reporting.py` pairs endpoint episode indices within each period, weights the periods equally
and reports conditional paired SEs for fixed policies. It retains all five checkpoints, AUC,
initial changes, all three contrasts and period losses. Numeric branch flags are descriptive
inputs: the DM still interprets uncertainty, usefulness and the full card reading. A missing
rule result leaves a trustworthy FACTOR–GENERIC contrast reportable at its narrower ceiling;
missing learner primary data does not acquire a complete-result label.

The thin runner keeps FACTOR as the first complete call and GENERIC plus the single final
reference evaluation and paired publication as the second. All required reference/publication
work remains in that second invocation. CPU float32, one compute thread and the fixed training
budget remain selected. No new guard, worker pool, registry or retry machinery was introduced.
An optional configuration-description CLI path exists but was not invoked and is not required.

## 3. Counts, receipts and actual engineering exposure

Changed non-test source totals **502 lines**: experiment 309, reporting 109 and runner 84;
the module subtotal is 418, not the complete non-test total. Tests add 281 lines. Scope §4
needs none and adds none. The 2,000-line attempt and 600-line runner limits are respected;
no section 5 budget breach is recorded.

CM recorded one focused suite: **9 passed in 6.06 seconds**, below the five-minute budget.
The cache-directory warning with cacheprovider disabled does not affect the checked behavior.
No full runner, selected-seed probe, benchmark or unchanged repeat suite was performed.

Actual fixture exposure: three seed9402 network initializations, one target deepcopy, one
synthetic Adam step over 64 terminal rows, and one zero-learning-rate scalar SGD gradient
check over 64 terminal rows. Four hand-built host episodes contribute 192 primitive ticks;
six standalone transition rows bring host fixture work to 198 ticks. A separate scalar rule
oracle uses 48 checker ticks. No optimized policy was evaluated in the environment. These
fixtures are not independent learning runs or evidence for the selected B performance question.

DM directly read saved files beneath the CM worktree's
`temp/directions/vsp_c1/test/service_allocation_synthetic_20260907/`:
`test_features_models_and_sourc0/configuration_exposure.json` reports seed9402, 372/393
parameters and matching selected configuration counts; `test_primary_publication_three0/pair.json`
contains the three synthetic contrasts and the fixed-policy SE scope; its
`pair_without_rule.json` preserves the same FACTOR–GENERIC result with
`learner_contrast_only` status. These contain synthetic inputs, not measured B returns.

Selected B exposure remains **zero**: no seed402 model, optimizer update, host episode,
evaluation or result-bearing invocation. No selected-run memory receipt or handle exists.
DM intake performed reads only. Full engineering wall/CPU usage is unmeasured; 6.06 seconds
is the focused-suite wall time, not the cost or feasibility of either selected invocation.

The unchanged prospective [counts record](VSPC1_K4_SERVICE_ALLOCATION_B01_COUNTS_20260907.json)
declares 4,096 training episodes, 256 Adam updates and 1,280 evaluation episodes per learner;
the reference adds 256 final episodes and zero learner updates. Total host work is 528,384
primitive ticks, 512 learner updates, 2,816 evaluation episodes and 1,138,688 scalar learner
Q predictions. Two complete calls remain the selected execution boundary: 258,048 ticks for
FACTOR and 270,336 for GENERIC plus reference, each capped at 2,700 seconds including publication.
Source acceptance makes no runtime or selected-model movement guarantee.

## 4. Decisions this intake produces

Options: (a) accept integrated implementation conformance and return to Portfolio; (b) send a
concrete semantic gap back to the same CM; (c) exceed the current command by launching seed402.
Recommendation and executed choice: **(a)**. Direct source and artifact inspection found no gap
that warrants (b); execution is outside this implementation command.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Kind: technical;
reversible: yes; owner flag: none. Recorded in the
[2026-09-07 audit ledger](../../portfolio/audit/2026-09-07.md). Current owner reviews and the
relevant ledger rows contain no unapplied override. No new card, close call, material dissent
or direction decision arises, so no separate P1/P2 item is inserted. The owner prediction is
`not taken`; the existing DM prediction remains unscored because no selected result exists.
There is no new valid-result Chinese brief: this is implementation acceptance only.

## 5. Bounded reading and next discriminator

Strongest support is direct implementation of the legal information/action/credit path and
focused checks of its transitions, weighting and publication. The present claim ceiling is
**source/card conformance**, not mechanism value. No scientific contradiction was measured;
the strongest unresolved alternative is that the same-information greedy rule supplies all
useful control and neither learner adds native return. Historical two-queue findings, family
boundaries and the missing new-host headroom record remain unchanged.

Portfolio receives this technical intake for its next execution decision; no priority,
lifecycle, recast or additional object is selected here. After a separate execution command,
the next scientific discriminator is the fixed update256 FACTOR–GENERIC native return
comparison, both learners against LQ-EXCLUDE, and both period results at the declared MEI.
Any later result remains one fixed-seed B exploration, not stable superiority, optimality,
causal attribution to sharing or transfer. Root observes accepted handles; CM collects and
technically accepts outputs; DM performs scientific intake. No experiment was relaunched or
transferred by this source acceptance.
