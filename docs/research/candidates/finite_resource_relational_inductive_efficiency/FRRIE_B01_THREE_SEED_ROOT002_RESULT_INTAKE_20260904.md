# FRRIE B01 three-seed root 002 — result intake (2026-09-04)

Status: `ACCEPTED SINGLE-SEED / B01_SEED_VALID_DIRECT / AGGREGATE WITHHELD`

## What I checked

I checked the terminal `summary.json` against
`FRRIE_B01_THREE_SEED_SECTION11_SCIENCE_CARD_20260904.md`, its launch record, root-001 intake,
evidence specification §4/§5.2/§11, and engineering-scope §4–§5. Specifically:

- the frozen root-002 literal bytes, fixed-host placement, fresh 4 GiB admission, exact exposure
  line, process and log receipts, and the distinction between process-acceptance SHA `8fee334c`
  and the later doc-only summary-observed HEAD `ae6a191e`;
- byte identity of all three declared source blobs across those two commits;
- all 23 completion comparisons, 512 paired checks, 512 pre-contact information checks, and the
  factual/audit/nonfactual work partition;
- all 98 actual-host cells, 24 central descriptors, two uniform cells, action/native-event counts,
  tape reuse, model/optimizer preservation, and contact audit;
- the 59,094-byte result artifact and SHA-256
  `c993fd694db31294e220d6b921c1c097a308ee406744d80d7c1c85a4318c47fa`;
- zero-byte stdout/stderr, terminal observation, and hash-preserved native DLL relocation;
- the accepted 599-line non-test implementation, 29.2% conservative orchestration share, final
  `2 passed`, and absence of an engineering-scope §4 addition; and
- owner reviews at this clean boundary, which returned no unapplied instruction.

The frozen per-seed rule applies verbatim: invalid does not fire; the seed is valid direct B
evidence; the three-seed aggregate rule is not applied. B objects have no consumption state.

## Observation that bounds the result

On literal root `FRRIE-B01-FRESH-BLOCK-002`, both arms completed 512 real RSCF/Adam updates. Each
arm used 32,768 factual episodes, 393,216 factual learner transitions, 638,976 factual-suffix audit
slots, 1,490,944 nonfactual suffix slots, and 512 backward/Adam calls. The evaluator completed 98
cells, 25,088 episodes, and 301,056 transitions.

The tight projection never changed an FP32 coordinate; full model/optimizer state and evaluation
traces were equal throughout the no-contact path. Thus `d_INT=d_ROT=0` for every checkpoint and
roster. Overall `L_inf(theta_512-theta_0)/0.05` was `2.017686367` in both arms, showing that an
absolute displacement of `0.100884318` elsewhere did not imply tight-`beta` contact.

At update 512 the shared learned intact returns were `0.0174102`, `0.0221716`, `0.0305828`, and
`0.0451000` for `N={6,9,15,21}`. EDGE minus uniform was `+0.0058027` at `N=9` and `+0.0055035` at
`N=15`, below the registered `0.08` screen on this seed. Held-out `V_u` remained tiny; its maximum
over checkpoints/held-out rosters was `0.000270478`. These are literal-root descriptions, not a
three-seed competence or package result.

Claim ceiling: one root, the fixed local Windows host, 512 updates, and the declared 98 cells. No
inference is made about root 003, a post-contact treatment effect, stable competence,
seed-population behavior, semantic/relational value, arbitrary-`N`, churn, deployment, or safety.

## Owner flags

1. The DM prediction `B01_WIDE_INCOMPETENT` is conditional on at least one seed contacting by
   update 512. Roots 001 and 002 have not contacted, but root 003 remains unobserved, so the
   prediction is not yet scored. The owner slot remains `not taken (unattended)`.
2. The only treatment difference did not activate on a second ordered root. Exact arm equality is
   strong support for these two observed paths and no evidence about value after contact.
3. Both observed roots are below the EDGE competence screen, but neither the competence nor
   no-contact branch may be applied before root 003 completes.
4. Peak RSS is unavailable. The result remains valid and is marked `resources_unmeasured`.
5. The monitor retained no numeric process exit code; direct facts are terminal process state,
   complete summary, and empty logs.
6. The summary's `ae6a191e` HEAD is a doc-only launch-record commit after process acceptance. All
   declared source blobs match `8fee334c`; this is provenance, not a failure.
7. The card's fixed-host wording pins roots 002/003 to root 001's Windows execution surface. The
   Linux remote route would change frozen host/toolchain semantics and was not used.

## Usage record

- this valid result: `6,861.782764 s` wall on `local_windows`, CPU FP32; peak RSS unavailable;
- cumulative accepted result-bearing wall for R128 plus roots 001–002: `17,015.031482 s`;
- cumulative accepted-attempt compute divided by three valid results: `5,671.677161 s` per valid
  result; test-only native/collector work excluded.

## Decisions this intake produces

### Disposition and continuation

Options:

1. accept root 002 as valid single-seed direct evidence and continue to the already frozen root
   003 invocation;
2. quarantine or repeat root 002 despite all frozen validity checks passing;
3. apply a three-seed branch from roots 001–002 alone; or
4. change treatment, comparator, roots, budget, host, or result rule after observing two roots.

Recommendation: option 1. Options 2–4 contradict the frozen rule or invent result-sensitive work.
No new object-tier selection is required: the earlier audited decision already fixed ordered roots
`001..003`, and applying the deterministic per-seed validity rule is not a new choice. Root 003 is
continuation of that accepted object, not a new family or rung. The active five-direction working
set retains FRRIE; that Portfolio scheduling fact does not alter this scientific disposition.

No Direction- or Portfolio-tier decision is produced. The three-seed result rule remains pending.

## Direction update and next discriminator

`DIRECTION.md` is updated with the accepted mechanism-level observation: root 002 completed the
full 512-update/98-cell path without contact and with direct arm equality. The strongest support is
the complete paired learner/evaluator trace. The strongest contradiction to package value is
nonactivation on a second root; the strongest contradiction to an “insufficient total movement”
explanation is absolute `L_inf` displacement of about `0.10088` outside tight-contact coordinates.

The next discriminator is unchanged root 003 on the same fixed host. Only after three valid seed
summaries may the registered aggregate branch be applied.

## Evidence paths

- card: `FRRIE_B01_THREE_SEED_SECTION11_SCIENCE_CARD_20260904.md`;
- launch: `FRRIE_B01_THREE_SEED_ROOT002_LAUNCH_20260904.md`;
- result: `FRRIE_B01_THREE_SEED_ROOT002_RESULT_EVIDENCE_20260904.md`;
- owner brief:
  `docs/research/portfolio/owner/briefs/finite_resource_relational_inductive_efficiency/2026-09-04_FRRIE-B01-THREE-SEED-ROOT002.md`;
- runtime summary:
  `temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_three_seed_root002_8fee334c_20260904T141201Z/summary.json`.
