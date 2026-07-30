# The successor population's selection rule, frozen before the population exists

Status: **selection RULE frozen. No population selected, generated or inspected.**

Authorized by the Pro ruling of 2026-07-30,
`docs/external-review/rounds/20260730_d7_s_provenance_correction_result/`, §4:

> The evidence design may begin now; the actual population must wait.

and its reason, which is the point of this document:

> This sequencing preserves freshness while avoiding another round in which the
> result-sensitive selection rule is written only after the apparatus output is
> seen.

## What this document is allowed to be

Frozen here, per §4's own list: the scientific question, sample size and hierarchy,
the topology-selection **rule**, block and episode counts, manifest schema and
generation authority, acceptance and invalidity branches, and the prohibition on
reusing H, the re-run and their inspected worlds.

Explicitly NOT here, per §4's second list -- and this is the part that matters:

```text
the exact confirmatory topology list          NOT BOUND
constructing those topologies                 NOT DONE
generating their user-world manifests         NOT DONE
inspecting their coordinates or worlds        NOT DONE
running support probes over them              NOT DONE
inserting them into a conclusion-bearing driver  NOT DONE
```

**A support probe counts as inspection.** Running one to check the candidates
"look usable" is the exact move this sequencing exists to prevent, and it would be
the easiest one to make while believing it was diligence.

## 1. The estimand is unchanged

`U*_stable,src / B_H <= -0.10`, `U*_flex,src / B_H >= +0.10`, agent-level. The R4
absolute focal margin contract
(`docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md`) carries the
gates, the four per-limb states, the nine-row combined mapping, the five-level
precedence and branch 3. **No threshold moves.** This document adds a population
and a provenance mechanism, nothing else.

## 2. The selection rule

**[PM binding, disclosed]** The ruling requires a *deterministic* rule and does not
name one.

```text
CANDIDATE_POOL   integers 20260742, 20260743, ... ascending, unbounded
EXCLUDED         every topology seed this project has ever constructed:
                   20260725            development
                   20260726..20260733  R3 initial
                   20260734..20260741  R4 population (H and the re-run)
SELECTION        the first K candidates in ascending order
K                8
```

Ascending-first, not a hash or a shuffle, for one reason: **it admits no free
parameter.** A hashed draw needs a seed, and a seed chosen after the apparatus
exists is a knob. There is nothing to tune here and nothing to re-roll.

### What the rule must NOT depend on, stated so a violation is visible

The selected set is a function of the exclusion list and `K` **only**. It must
never be filtered, reordered or extended by:

- event support, qualifying-event counts, or any probe over the candidates;
- BS-quadrant class, or any coordinate property;
- whether a candidate's manifests generate without error;
- anything measured after selection.

**On support failure the run reports `SOURCE_EVENT_SUPPORT_INSUFFICIENT` with no
substitution and no expansion.** That branch already exists in the R4 contract and
it is the whole reason the rule can be this rigid: an unusable draw is a
*reportable outcome*, not a reason to draw again.

## 3. Hierarchy, counts and pooling

```text
topology            the top-level bootstrap unit, K = 8
episodes            8 Part-A control + 8 focal audit, per topology
n_select / n_eval   2 / 2
expansion           NONE
```

Identical to R4, deliberately: a successor that also changed the design would make
any difference in outcome uninterpretable.

**Pooling with R3 or R4 data is forbidden, in both directions.** So is pooling H's
shards with the re-run's. Fresh means fresh at the highest inferential unit --
topology -- so new episodes under an old topology are fresh *conditional*
observations and are not new draws from `P_T`.

## 4. The prohibition on reusing what has been seen

```text
H (run 30403322062)            INVALID_R4_REALIZATION, no confirmatory weight
the re-run (30479940700)       EXPLORATORY_BRANCH_ROBUSTNESS_UNDER_
                               UNREGISTERED_WORLD_VARIATION, no confirmatory weight
their worlds                   INSPECTED. Never a manifest source, never a
                               population member, never a comparison baseline for
                               the successor's result
today's diagnostic samples     INSPECTED. Same treatment
```

Both artifacts stay immutable and both remain citable as descriptive
external-return observations of the historical code paths. Neither ever becomes
the fresh confirmatory result.

## 5. Manifest schema and generation authority

Schema 2, `docs/research/designs/D7_S_WORLD_MANIFEST_REPLAY.md`.

```text
generation authority   ONE execution, on ONE machine, under one generator_version
generation timing      AFTER the replay gate passes, never before
storage                create-once; an inventory set-hash freezes the population
                       before the first conclusion-bearing episode
namespace              a successor contract id, distinct from CONTRACT_ID and from
                       R4_POPULATION_NAMESPACE, so every derived seed is distinct
```

The namespace rule is load-bearing and has already cost a round: with
`--population r4` the `run_contract_id` becomes the R4 namespace, which changes
every derived seed for that process. **Shards produced under two different
namespaces are not the same measurement and must never be pooled.**

## 6. The one slot deliberately left open

**A1 versus A2 -- manifest plus one frozen runtime class, versus persisting the
exogenous trajectory or random tape -- is NOT frozen here.** It is a protected
scientific choice, and the measurement that decides it is the replay gate's
full-horizon exercise: if horizon equality holds across independently provisioned
runners under A1, A1 suffices; if later RPGM transitions diverge, A2 is required.

Freezing it now would be choosing before measuring, which is the failure this
whole document is arranged against.

## 7. Acceptance and invalidity branches

Unchanged from the R4 contract, with one addition:

```text
existing   SOURCE_EVENT_SUPPORT_INSUFFICIENT, PRIMARY_G_DEGENERATE,
           INVALID_EVENT_ALIGNED_AUDIT, PART_A_CONTRADICTION,
           the four per-limb states and the nine-row combined mapping
added      MANIFEST_REPLAY_NOT_CERTIFIED -- the run refuses to start if the
           replay gate has not returned PASS for the realization in force, or if
           the manifest inventory's set_hash does not match the frozen one
```

The addition fails **closed and early**: a conclusion-bearing run that discovers
its provenance mechanism is uncertified after 114 minutes has already spent the
compute.

## 8. What still gates this document

```text
Pro must rule on A1 versus A2                                    OPEN
the replay gate must return PASS across independent executions   OPEN
compute for any formal successor run                             user authority
```

Until all three close, this is a frozen rule and nothing else. **No topology in
the candidate pool may be constructed for any reason**, including a smoke test --
the probe refuses R4 seeds today and must refuse the successor set the moment it
is bound.
