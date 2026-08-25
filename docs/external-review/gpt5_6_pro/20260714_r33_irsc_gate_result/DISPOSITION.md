# Controller Disposition: R33 Result and R34 Route

Date: 2026-07-14

Source model: GPT-5.6 Pro, two manual submissions of the same tracked question.
The raw responses are `RESPONSE_RAW_A.md` and `RESPONSE_RAW_B.md`. Their
agreement is a repeated sample from one model, not independent scientific
evidence.

## Decision

- R33 validity and retirement: **ACCEPT**. R33 is a valid
  `FAIL_M1_RETIRE_R33_IRSC`; only the registered stable non-additive
  role-swap selector is retired. The result does not prove that every possible
  form of complementarity is absent.
- Proposed R34-BHMD direction: **MODIFY, then accept as the single next edge**.
  It is structurally different from R31 label prediction, R32 direct effect
  maximization, and R33 selection over the existing codebook: it first mines
  behavior modes and then rewrites the low-level codebook by sequence
  distillation.
- Response precedence: use response B's full-episode recurrent replay. Response
  A's stored block-start hidden states become stale as soon as `actor_rnn` is
  updated and are rejected.

## Required modifications

1. Add the unchanged frozen source as a no-update anchor. `real > sham` alone
   can result from damaging the sham rather than creating a mode; R34 must also
   show material gain over the source under the same forced and natural seeds.
2. Mine focal-agent displacement modes only. Teammate displacement is a
   diagnostic/context variable, not part of a label that a single focal skill
   is asked to control.
3. Distill complete 80-step recurrent episodes from zero hidden state. For a
   heldout block, recompute the modified focal actor's prefix hidden from the
   episode start; never restore a source-RNN hidden into an updated RNN.
4. Replace the fixed next-episode sham with a deterministic maximum-Hamming,
   no-self episode-sequence derangement per agent. If even the best derangement
   leaves more than half of labels equal, record a valid degenerate-mode M1
   failure rather than treating it as a useful comparator.
5. Separate the downstream conclusions: M1 tests causal codebook formation;
   M2a tests zero-shot natural use by the frozen old R30 selector; M2b tests
   coverage transport. An M1 pass is preserved if either downstream edge
   fails.
6. Use the train split only for normalization, prototypes, and prototype-to-z
   alignment. Evaluate every nearest-prototype and SNR quantity in that one
   frozen standardized space. Cluster heldout inference by source episode and
   share branch random streams across source, real, and sham.
7. Frozen high parameters and clock are matched, but realized KEEP/SET
   trajectories may diverge after the low actor changes state visitation. Do
   not call them realized-schedule matched.

The exact modified budget, thresholds, result branches, and sole status source
are owned by the R34 block in `memory/ExpRecord.md`. No IMOD code, scheduler,
hazard, queue, teacher mixture, `J`, or ROSTER controller is migrated.
