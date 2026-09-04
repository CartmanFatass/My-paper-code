# FRRIE B01 section-11 R128 smoke — result intake (2026-09-04)

Status: `ACCEPTED / R128_VALID_NO_CONTACT / OBJECT-TIER NEXT RUNG SELECTED`

## What I checked

I checked the terminal `summary.json` against
`FRRIE_B01_SECTION11_R128_SMOKE_SCIENCE_CARD_20260904.md`, the launch record, evidence
specification §4 and §11, and engineering-scope §4–§5. Specifically:

- launch SHA `85b96dc80bb0b75ab605fa0cf606bcbb37649152`, root 001, admission timing and both
  `5,235,474,432`-byte memory facts;
- the exact exposure line and the registered three-branch rule;
- all 22 completion comparisons, 128 direct paired checks, 128 pre-contact information checks,
  and exact per-arm factual, native-work, backward, Adam, and evaluation counts;
- all 18 cells, eight `d_u/e_u` rows, action counts, terminal primitive counts, tape reuse,
  model/optimizer preservation, and contact audit;
- the result artifact's 16,186 bytes and SHA-256
  `4fc5e015ab5d8a69ce8b0d954a13527e33248dcb539eb4896c9903a8c8bfa091`;
- zero-byte stdout/stderr receipts and the post-terminal native DLL preservation; and
- the accepted code budgets and absence of unrequested engineering-scope §4 machinery.

The frozen rule applies verbatim: incomplete does not fire; no-contact fires; contact does not.
This is a valid B/EXPLORE observation. B objects have no consumption state.

## Observation that bounds the result

On literal root `FRRIE-B01-FRESH-BLOCK-001`, both arms completed 128 real RSCF/Adam updates with
`98,304` factual learner transitions and `630,784` counterfactual/audit native slots per arm. The
tight projection never changed an FP32 coordinate. Full model/optimizer equality and direct
evaluation trace equality held throughout the no-contact path, so `d_u(N)=0` at every checkpoint
and seen roster.

The learned return was highest at update 64 (`0.0204130` at `N=9`, `0.0291967` at `N=15`) and
fell by update 128 (`0.0195787`, `0.0263511`). EDGE minus uniform at update 128 was only
`+0.0009013` and `+0.0002314`. These are literal-seed descriptions, not package polarity or a
general competence claim.

Claim ceiling: one seed, `N={9,15}`, `INTACT`, 128 updates. No inference is made about contact,
held-out roster transfer, reassociation, stable equality or superiority, semantic mechanism,
arbitrary-`N`, churn, deployment, or safety.

## Owner flags

1. The registered DM prediction `R128_VALID_NO_CONTACT` was correct; the owner prediction slot was
   `not taken (unattended)`.
2. The treatment was not exercised. The direct equality is strong support for the observed-path
   no-contact explanation and no evidence for tight-package value after contact.
3. EDGE competence relative to uniform is weak and initially mixed. A stronger competence reading
   is not supported by this one seed.
4. Peak RSS was unavailable. Per the owner telemetry rule the result remains valid and is marked
   `resources_unmeasured`.
5. The monitor did not retain a numeric Windows exit code, but the process terminated after writing
   a complete summary and both logs are empty. This is recorded rather than converted into a gate.
6. The package-native build initially left one untracked DLL beside source. It was hash-preservingly
   moved after terminal into the run root. The worktree is clean; no owner-dirty main-checkout byte
   was touched.

## Decisions this intake produces

### Decision 1 — next B01 rung (object tier)

Options:

1. prepare the unchanged three-seed B01 rung using the already generated ordered roots `001..003`;
2. repeat the one-seed R128 rung;
3. change the treatment, comparator, seed law, or configuration in response to the result; or
4. park the accepted B01 family at this reversible boundary.

Recommendation: option 1. The science card says every valid R128 branch advances to the unchanged
three-seed rung. Repeating the same valid smoke adds no registered decision, and changing the
object after seeing its value would violate the prospective contract. Parking is reversible but
leaves the selected discriminator unanswered.

`Owner-delegated decision (unattended, 2026-09-03 instruction): (1)`

This is an object-tier selection inside the already accepted B01 family. It does not open, close,
recast, park, or promote the direction and therefore requires no new Pro decision. Portfolio
priority and lifecycle remain Root/owner decisions.

## Direction update and next discriminator

`DIRECTION.md` is updated with the accepted mechanism-level observation: 128 updates were
technically and scientifically valid on one root, no tight contact occurred, and arm equality was
directly observed only on that path. The next discriminator is an outcome-blind card for the
unchanged three-seed B01 rung. Roots, treatment, containing comparator, information, numerical/RNG
semantics, and configuration remain fixed.

The current strongest support is the complete paired learner/evaluator trace. The strongest
contradiction to a package-value reading is nonactivation of the treatment. The unresolved risk is
whether longer exposure creates contact and, if so, whether any return difference survives EDGE
competence and the later held-out/reassociation controls.

## Evidence paths

- card: `FRRIE_B01_SECTION11_R128_SMOKE_SCIENCE_CARD_20260904.md`;
- launch: `FRRIE_B01_SECTION11_R128_SMOKE_LAUNCH_20260904.md`;
- result: `FRRIE_B01_SECTION11_R128_SMOKE_RESULT_EVIDENCE_20260904.md`;
- runtime summary: `temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_r128_root001_85b96dc8_20260904T032143/summary.json`;
- unattended audit: `docs/research/portfolio/audit/2026-09-04.md`.
