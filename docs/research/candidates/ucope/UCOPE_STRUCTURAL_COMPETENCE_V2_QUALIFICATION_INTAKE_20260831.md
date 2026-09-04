# UCOPE structural competence V2 technical qualification intake — 2026-08-31

## Disposition

The exact committed implementation at
`b79438edc3585ad3dd86ad3fc70308c219688f09` completed the authorized
non-result V2 sequence from `C:/Projects/HMASD` with CPython 3.11.9 at
`C:/Users/fires/AppData/Local/Programs/Python/Python311/python.exe`:

```text
freeze-reference-bundle  -> COMPLETE
check-binding             -> MATCH
assess-run                -> PERFORMANCE_READY
```

This is a resource and technical qualification only. `run` and `validate`
were not invoked, the fixed scientific result root does not exist, and no
outcome slot or scientific interpretation is authorized.

## V2 bundle and binding

The create-once V2 bundle is:

```text
temp/directions/ucope/exp/ucope-structural-competence-reference-bundle-v2/
```

It contains 91 ordered members and 95 files in total. Its retained binding
receipt is:

```text
temp/directions/ucope/exp/ucope-structural-competence-reference-bundle-v2/
  prefit-binding-receipt.json
```

The receipt records `status=MATCH`, 90 prefit members, one postfit member,
80 gzip members, and exact canonical comparison plus deterministic replay of
all `1,638,400` retained training rows. The separately invoked binding check
returned the same counts and `UCOPE_STRUCTURAL_REFERENCE_BUNDLE_V2`.

The bundle-freeze admission and resource records are:

```text
temp/directions/ucope/exp/ucope-structural-competence-reference-bundle-v2/
  resource-admission.json
  resource-ledger.json
temp/directions/ucope/exp/ucope-structural-competence-controls-v2/resource-receipts/
  freeze-reference-bundle-9ca05c22600d41f5806769e508a42fd6.json
```

The independent binding-check admission and ledger are:

```text
temp/directions/ucope/exp/ucope-structural-competence-controls-v2/resource-receipts/
  check-binding-79e32fa62ddb4bc99e98d176197ea349.json
  check-binding-ledger-22a17c25c8b148d48e47c4ef1cfcb166.json
```

## Outcome-blind assessment

The complete assessment receipt is:

```text
temp/directions/ucope/exp/ucope-structural-competence-controls-v2/assessments/
  assess-run-6d2ae6a71c8949d19d6f20375dc6050a/assessment-receipt.json
```

It records `complete=true`, `performance_disposition=PERFORMANCE_READY`, and
`exact_refit_equal=true`. Fixed technical work was:

- 90 prefit members compared;
- `1,638,400` canonical rows replayed;
- `9,830,400` exact row decodes;
- `3,276,800` exact root-normal accumulations; and
- two exact in-memory solve passes in two independent prefit modules.

The receipt records zero postfit members opened, zero serialized solve
documents, and zero scientific outputs created. It contains no matrix, rank,
coefficient, policy, competence, oracle, or result disposition.

Its admission and ledger are:

```text
temp/directions/ucope/exp/ucope-structural-competence-controls-v2/resource-receipts/
  assess-run-12814833c930459ebf577378bb7bd821.json
  assess-run-ledger-0f4a420b455444cea9e878ae7d6e1492.json
```

## Measured resource facts

All three fresh admissions passed both the physical and effective 4 GiB
floors. Available bytes were `17,343,864,832` for bundle freeze,
`17,392,603,136` for binding check, and `17,376,743,424` for assessment.

| Entry | Wall s | CPU s | Peak RSS bytes | Peak threads | Aggregate I/O bytes | Scratch bytes | Durable bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bundle freeze | `255.5301346` | `258.8125` | `67,334,144` | `5` | `182,080,549` | `30,295,835` | `30,295,835` |
| binding check | `249.5618848` | `251.71875` | `101,576,704` | `5` | `121,375,898` | `0` | `0` |
| assessment | `1054.5743775` | `1066.890625` | `114,110,464` | `5` | `182,035,085` | `0` | `0` |

Every ledger records one worker, zero scientific child processes, and
`passed=true` under the frozen ceilings and publication headroom.

## Supersession and authority boundary

The earlier V1 bundle and V1 READY assessment remain immutable, superseded,
non-consuming technical evidence. They cannot qualify V2 because the live
runner is bound only to the exact V2 path-and-format tuple. Nothing in this
intake mutates, aliases, upgrades, or interprets V1.

The fixed result root remains absent:

```text
temp/directions/ucope/exp/ucope-structural-competence-r01
```

Therefore the current authority is exactly:

```text
V2_TECHNICAL_QUALIFICATION=PERFORMANCE_READY
SCIENTIFIC_RESULT=ABSENT
OUTCOME_AUTHORIZATION=NO
RUN_INVOKED=false
VALIDATE_INVOKED=false
```

Any outcome-bearing `run` still requires a separate explicit Root grant.
This intake creates no acquisition, COUNT/RAW, representation, competence,
seed-population, safety, deployment, or lifecycle polarity.
