# FRRIE B01 three-seed root 001 — result intake (2026-09-04)

Status: `ACCEPTED SINGLE-SEED / B01_SEED_VALID_DIRECT / AGGREGATE WITHHELD`

## What I checked

I checked the terminal `summary.json` against
`FRRIE_B01_THREE_SEED_SECTION11_SCIENCE_CARD_20260904.md`, its launch record, evidence
specification §4/§5.2/§11, and engineering-scope §4–§5. Specifically:

- the frozen root-001 literal bytes, fresh 4 GiB admission, exact exposure line, process and log
  receipts, and the distinction between process-acceptance SHA `987061a3` and the later doc-only
  summary-observed HEAD `c20b42a3`;
- byte identity of all three declared source blobs across those two commits;
- all 23 completion comparisons, 512 paired checks, 512 pre-contact information checks, and the
  factual/audit/nonfactual work partition;
- all 98 actual-host cells, 24 central descriptors, two uniform cells, action/native-event counts,
  tape reuse, model/optimizer preservation, and contact audit;
- the 59,343-byte result artifact and SHA-256
  `0632e741121b9f7d42f506fe6fc5bc763d84e158280dbc25ffc72bf4582dccea`;
- zero-byte stdout/stderr, terminal observation, and hash-preserved native DLL relocation; and
- the accepted 599-line non-test implementation, 29.2% conservative orchestration share, final
  `2 passed`, and absence of an engineering-scope §4 addition.

The frozen per-seed rule applies verbatim: invalid does not fire; the seed is valid direct B
evidence; the three-seed aggregate rule is not applied. B objects have no consumption state.

## Observation that bounds the result

On literal root `FRRIE-B01-FRESH-BLOCK-001`, both arms completed 512 real RSCF/Adam updates. Each
arm used 32,768 factual episodes, 393,216 factual learner transitions, 638,976 factual-suffix audit
slots, 1,490,944 nonfactual suffix slots, and 512 backward/Adam calls. The evaluator completed 98
cells, 25,088 episodes, and 301,056 transitions.

The tight projection never changed an FP32 coordinate; full model/optimizer state and evaluation
traces were equal throughout the no-contact path. Thus `d_INT=d_ROT=0` for every checkpoint and
roster. Overall `L_inf(theta_512-theta_0)/0.05` was `2.092398852` in both arms, showing that
substantial movement elsewhere did not imply tight-`beta` contact.

At update 512 the shared learned intact returns were `0.0153505`, `0.0255463`, `0.0387381`, and
`0.0370877` for `N={6,9,15,21}`. EDGE minus uniform was `+0.0068689` at `N=9` and `+0.0126184` at
`N=15`, below the registered `0.08` screen on this seed. Held-out `V_u` remained tiny; its maximum
over checkpoints/held-out rosters was `0.000226887`. These are literal-root descriptions, not a
three-seed competence or package result.

Claim ceiling: one root, fixed host, 512 updates, and the declared 98 cells. No inference is made
about another seed, a post-contact treatment effect, stable competence, seed-population behavior,
semantic/relational value, arbitrary-`N`, churn, deployment, or safety.

## Owner flags

1. The DM prediction `B01_WIDE_INCOMPETENT` was conditional on contact. Root 001 did not contact,
   so that prediction is not scored; its predeclared no-contact alternative remains live. The
   owner slot was `not taken (unattended)`.
2. The only treatment difference did not activate. Exact arm equality is strong support for this
   observed path and no evidence about value after contact.
3. Root 001 does not meet the EDGE competence screen, but the three-seed rule cannot be applied
   before roots 002 and 003 complete.
4. Peak RSS is unavailable. The result remains valid and is marked `resources_unmeasured`.
5. The monitor retained no numeric process exit code; direct facts are terminal process state,
   complete summary, and empty logs.
6. The summary's later `c20b42a3` HEAD is a doc-only identity change after process acceptance. All
   declared source blobs match `987061a3`; this is provenance, not a scientific or engineering
   failure.
7. The native DLL was moved only after terminal into the exact run root with its hash unchanged.
   The owned worktree is clean and the main owner-dirty bundle remains untouched.

## Decisions this intake produces

### Disposition and continuation

Options:

1. accept root 001 as valid single-seed direct evidence and continue to the already frozen root
   002 invocation;
2. quarantine or repeat root 001 despite all frozen validity checks passing;
3. apply a three-seed branch from root 001 alone; or
4. change treatment, comparator, roots, budget, or result rule after observing root 001.

Recommendation: option 1. Options 2–4 contradict the frozen rule or invent result-sensitive work.
No new object-tier selection is required: the earlier audited decision already fixed ordered roots
`001..003`, and applying the deterministic per-seed validity rule is not a new choice. Root 002 is
continuation of that accepted object, not a new family or rung. The owner-directed REMOTE_FIRST
control plane changes only execution placement: root 002 must use exact pushed source bytes in one
freshly admitted remote task; root 001 is never migrated or repeated.

No Direction- or Portfolio-tier decision is produced. The three-seed result rule remains pending.

## Direction update and next discriminator

`DIRECTION.md` is updated with the accepted mechanism-level observation: root 001 completed the
full 512-update/98-cell path without contact and with direct arm equality. The strongest support is
the complete paired learner/evaluator trace. The strongest contradiction to package value is
nonactivation; the strongest contradiction to an “insufficient total movement” explanation is the
observed absolute `L_inf` displacement of about `0.10462` outside the tight-contact coordinates.

The next discriminator is unchanged root 002, followed by root 003. Only after three valid seed
summaries may the registered aggregate branch be applied.

## Evidence paths

- card: `FRRIE_B01_THREE_SEED_SECTION11_SCIENCE_CARD_20260904.md`;
- launch: `FRRIE_B01_THREE_SEED_ROOT001_LAUNCH_20260904.md`;
- result: `FRRIE_B01_THREE_SEED_ROOT001_RESULT_EVIDENCE_20260904.md`;
- runtime summary:
  `temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_three_seed_root001_987061a3_20260904T113849Z/summary.json`.
