# PM code-side reconciliation — G20R identification floor

Date: 2026-07-24

```text
round=20260724_g20r_identification_floor
stage_commit=52d89863f02c9a86520952d086a26b58ce8caf3d
raw=21_PRO_OPEN_RAW.md
convergence=22_PRO_CONVERGENCE.md
authority=external_pro
adopted=in_full
compute_authorized=none
iteration_consumed=false
```

Pro's ruling is adopted in full. This file records what it decides, what it
changed on reconsideration, and the code-side consequences I now own.

## The re-review was load-bearing

The first answer was produced under a curtailed generation — our transport
clicked `Answer now` at roughly four minutes against a predecessor that had
reasoned for eighteen. The convergence turn ran `15m 46s` and **retracted two of
its own load-bearing conclusions**:

| Curtailed answer | After full reasoning |
|---|---|
| `NMSE < 1` as a mandatory identification gate | **retracted** — use positive-scale held-out `R^2`, contrast alignment, and oracle actor-gradient alignment |
| `rotating_mask` and individual battery are the missing critic inputs | **retracted as a complete inventory** — the real omission is far larger |
| cross-fitting required | refined — independent fit/credit/audit roles and held-out qualification required; literal K-fold optional |
| G18 lowers C1 plausibility | refined — lowers confidence in the current *implementation and qualification protocol*, no formal update to the C1 class |

Had we acted on the curtailed answer we would have made a narrow, wrong repair:
add two fields and adopt a gate Pro has since withdrawn. This is the concrete
cost of curtailment, and the reason the prohibition is now absolute.

## Adopted — identification

The scalar floor is replaced by a **sequential, source-specific qualification
protocol**, not a better constant:

- **Stage A** — is there a source action effect to identify at all? Measured as
  the true within-history action advantage on the C1 action support under the
  declared suffix policy, via paired replay. Failure means
  `SOURCE_ACTION_EFFECT_NOT_IDENTIFIED`, which is not a critic failure.
- **Stage B1** — did the critic identify the source action contrast? Positive-
  scale held-out fit, not raw NMSE.
- **Stage B2** — does the identified critic produce the correct actor direction?
  Oracle actor-gradient alignment.

Gates are **sequential and source-specific**. A G17 identification failure must
not silently mask G18 when direct G17 compatibility passes — which is exactly
what the retired combined `q_identification_ok` did on the completed screen.

## Adopted — the `Q_j` input contract

The critic conditions on a permutation-consistent pre-action sufficient
statistic: centralized critic state, the **full masked table of per-member
observations** in anonymous routing order, detached pre-action recurrent states,
active/lifecycle/membership-transition state, routing position, the **full
ordered action prefix paired with its member context** — not merely its sum —
and the focal action.

Prohibited inputs: any action at a position greater than `j`, next state, future
reward, unannounced future membership event, decision-time-unavailable ledger
identity, and hard-coded semantic interpretation of observation coordinates. The
representation must be equivariant to simultaneous permutation of lifecycle rows;
routing position may index a chain factor but must never become a member
identity.

**On leakage.** Pro is explicit that this does not endanger the protected fast
path, subject to seven ownership conditions the frozen design already declares
and the completed screen already verified bitwise. The formulation I adopt
verbatim as the guard: *what must be prohibited is not "critic sees observation";
it is critic-to-actor information flow outside the detached scalar credit path.*

## Adopted — data roles

Independent **fit / credit / audit** roles with held-out critic qualification are
required. Literal K-fold cross-fitting is optional. The actor may not be updated
before the critic qualifies — the completed screen violated this by computing the
advantage from an unqualified critic and updating the actor anyway.

## What this does and does not move

- **P2 — unchanged and untested.** Nothing here registers against it.
- **C1 — unchanged as a mathematical class.** The G18 reading lowers confidence
  in the current implementation and qualification protocol only. It is not
  evidence against the estimator class, and must not be cited as such.
- **The completed screen** stands as an invalid instantiation, already recorded.
  Its numbers are not evidence for or against any candidate.

## Code-side consequences I own

1. The `Q_j` input contract is rebuilt to the frozen statistic above. The root
   defect was mine: the design's section 2 described a broad `h_j` while section
   5 listed four realized inputs without observation, and I accepted the narrower
   reading when the implementer explicitly flagged the contradiction.
2. The result system is re-registered with source-specific sequential branches
   and the five distinct failure classes Pro names: no source effect, effect
   outside centered authority, unfit critic, wrong actor-credit direction, and
   qualified behavioral failure.
3. The pre-freeze design check gains the question this episode exposed: **does
   the critic receive the variables the measured effect depends on?** Neither the
   original check nor its threshold pass asked it.
4. No compute. Pro states plainly that only after the re-registered contract
   exists could a new screen be interpretable, and this ruling authorizes neither
   implementation nor any run.

## Next action

Zero-compute re-registration of the G20R identification and result contract,
freezing the nine items Pro enumerates. The bounded screen stays withheld until
that contract exists.
