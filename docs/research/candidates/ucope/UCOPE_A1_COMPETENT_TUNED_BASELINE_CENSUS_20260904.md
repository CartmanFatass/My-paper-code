# UCOPE A1 — competent tuned-baseline census and minimal headroom order

- Direction: `ucope`
- Record type: read-only **A/RECON census**
- Census result: **`BASELINE_COMPETENCE_UNRESOLVED`**
- Date: 2026-09-04
- Lifecycle effect: **none**; UCOPE remains under the current Portfolio authority

## 1. Question and claim ceiling

Does the accepted UCOPE evidence already contain a prospectively trained or tuned,
same-information baseline that satisfies the direction's full competence predicate and can serve
as the competent comparator for a native-return headroom audit?

This census reads accepted records only. It performs no training, tuning, environment execution,
solver call, model selection or result-bearing invocation. Its ceiling is an inventory statement
about the current evidence tree, not a claim that UCOPE lacks headroom or that the direction should
hold, park or close.

## 2. Eligibility rule

An eligible tuned baseline must:

1. be a learned or prospectively tuned policy, not an oracle or closed-form exact-solve ceiling;
2. use the same information available to the candidate mechanism;
3. be evaluated on its declared full competence predicate, including finite/unique action scores,
   oracle root agreement, maximum regret at most `1/50`, and forced-PROBE tail agreement at least
   `19/20`; and
4. pass the object-level competence rule on its full required panel, not merely one component such
   as `C_root`, one favorable fold, a majority statistic, or the competence-free `A_paid` predicate.

## 3. Read-only census

| accepted evidence | strongest learned/tuned competence observation | eligible competent baseline? |
| --- | --- | --- |
| competence-first B1 | all three arms `0/3` competent seeds; 0/18 final policies | no |
| odd-support audit | `0/72` odd-competent and `0/72` near-competent policies | no |
| exposure-ladder rung 1 | `0/12` policies; no arm competent | no |
| competence-whitened R01 | `WHITENED-10X 3/6`, `RAW-10X 0/6` | no |
| root-conditioning R01 | whitened root reaches `C_root 5/6`, but full `C_even` remains `3/6` | no |
| tail-margin remedies | best arm full `C_even 3/6`; no arm reaches 6/6 | no |
| paid-acquisition B01 | treatment and reference full `C_even 3/6`; `A_paid` is competence-free | no |
| three-witness hinge | treatment and dose null full `C_even 3/6` | no |

The competence-whitened closed-form `EXACT-SOLVE` ceiling is `C_even 6/6`, and the root-conditioning
exact solve is `C_root 6/6`. These are strong analytic feasibility/headroom witnesses, but neither
is a trained or tuned baseline. They cannot fill the requested comparator role by relabeling.

## 4. Census conclusion

No accepted learned or tuned UCOPE baseline is competent on its full declared panel. The current
gap is therefore:

```text
BASELINE_COMPETENCE_STATUS=UNRESOLVED
COMPETENT_TUNED_BASELINE_ID=NONE
HEADROOM_POLARITY=NONE
```

Learner noncompetence is not evidence of absent headroom. The competent exact-solve ceiling is the
strongest contradiction to such a negative reading: it shows that the finite representation can
support the competence predicate under at least one closed-form construction, while the existing
learned/tuned routes have not supplied a competent comparator.

The quarantined remote root-target attempt is excluded from this census. Its numerical-conformance
failure neither strengthens nor weakens baseline competence.

## 5. Minimal competence-to-headroom A/RECON order

Only the following order is frozen; no result-bearing launch is authorized by this record.

### Step A1 — tuned-baseline competence

`UCOPE-A-RECON-TUNED-BASELINE-COMPETENCE-R01`

When a prospectively defined tuned same-information baseline artifact exists, audit that artifact
against the unchanged full competence predicate and native consequence panel. The strongest legal
comparator is the exact-solve ceiling, retained explicitly as a ceiling rather than relabeled as a
tuned baseline. A nonpass records `BASELINE_COMPETENCE_UNRESOLVED` and stops the order without any
headroom polarity.

### Step A2 — competent-baseline headroom

`UCOPE-A-RECON-COMPETENT-BASELINE-HEADROOM-R01`

This step becomes cardable only after Step A1 identifies a competent tuned baseline. It then
compares the prospective mechanism or exact ceiling with that baseline under identical information,
panel, action semantics and native return. The estimand is native-return headroom over the strongest
competent tuned baseline, not predictive fit or oracle agreement alone.

Until A1 passes, A2 is `NOT_LAUNCHABLE_BASELINE_COMPETENCE_UNRESOLVED`. Candidate bytes, exposure,
cost law, machine-time cap and result branches are intentionally not invented before an eligible
baseline exists; each must be frozen prospectively if the order resumes.

## 6. Non-goals and authority boundary

- no unapproved `HOLD`, MEI, lifecycle, priority or Portfolio action;
- no inference that technical or learner nonpass means no headroom or a negative direction;
- no tuning, learner construction, optimizer update or baseline selection inside this census;
- no use of an exact/oracle ceiling as though it were a tuned baseline;
- no change to paid-acquisition or COUNT/RAW records; and
- no override of the current root-target A/RECON object or its no-science intake.

## 7. Object-tier decision

Options:

- **(a) Record the competence gap and freeze only the A1-then-A2 order above.**
- **(b) Treat the exact-solve ceiling as a competent tuned baseline and jump to headroom.**
- **(c) Treat existing learner noncompetence as absent headroom or direction-negative evidence.**

Recommendation: **(a)**. It preserves the competent-comparator requirement without manufacturing a
baseline or scientific polarity.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`.

## 8. Principal evidence

- `UCOPE_COMPETENCE_FIRST_SCOUT_R01_B1_RESULT_EVIDENCE_20260901.md`
- `UCOPE_A_RECON_B1_ODD_SUPPORT_VS_EVEN_HELDOUT_COMPETENCE_AUDIT_R01_RESULT_EVIDENCE_20260901.md`
- `UCOPE_COMPETENCE_WHITENED_R01_RESULT_EVIDENCE_20260903.md`
- `UCOPE_ROOT_CONDITIONING_R01_RESULT_EVIDENCE_20260903.md`
- `UCOPE_TAIL_MARGIN_REMEDIES_R01_RESULT_EVIDENCE_20260903.md`
- `UCOPE_PAID_ACQUISITION_B01_RESULT_EVIDENCE_20260903.md`
- `UCOPE_THREE_WITNESS_HINGE_R01_RESULT_EVIDENCE_20260904.md`
