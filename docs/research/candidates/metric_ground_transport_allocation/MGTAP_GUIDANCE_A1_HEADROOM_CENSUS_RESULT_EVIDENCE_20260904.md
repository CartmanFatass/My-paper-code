# MGTAP guidance A1 current-host headroom census — result evidence

- Direction: `metric_ground_transport_allocation`
- Object: `MGTAP-GUIDANCE-A1-HEADROOM-CENSUS-20260904`
- Evidence class / claim ceiling: **A/RECON**; accepted-evidence availability
  only, no algorithm effect
- Card: [`MGTAP_GUIDANCE_A1_HEADROOM_CENSUS_SCIENCE_CARD_20260904.md`](MGTAP_GUIDANCE_A1_HEADROOM_CENSUS_SCIENCE_CARD_20260904.md)
- Card commit: `e77e03f23e5bab4b7cbd66676608f4ef3ce8dcc3`
- Observation time: `2026-09-04T07:14:00-07:00`
- Validity: **complete static census**
- Result branch: **`HC-B / UPPER_PRESENT_BASELINE_RESULT_UNAVAILABLE`**
- Guidance-A1 estimand: **`H_A1(6)=NOT_IDENTIFIED`;
  `H_A1(12)=NOT_IDENTIFIED`**

## 1. Direct inventory and receipts

The bounded pass inspected all nine tracked documents frozen by the card. Their
working-byte SHA-256 receipts were:

| tracked evidence | bytes | SHA-256 |
| --- | ---: | --- |
| guidance | `14,630` | `25af716f2db87336d73846c2227149b2925eb1ae3e741fea08b84ebfb640356d` |
| `PORTFOLIO.md` | `14,491` | `08e0aae82189b1cbc15e05ea3da7e1a2ef7966419f63b2190016ed81b02b601f` |
| `DIRECTION.md` | `26,754` | `bcd7cd340188de0c104d54a565b1b790aaaca01ea583524e3a5a1f9d642938f8` |
| B1 science card | `46,964` | `db624d05b49c6957028c0a8b3d2eb833a4823ac04a89f5a0b232dd84dab6cbfe` |
| result-blind activation map | `9,152` | `d279c20bb8193ef2e6f0fa6acb3af6be80bf04e584af3c07b6b83c1b4bfb04aa` |
| revision-04 result intake | `4,404` | `ca7c9360556bd1b90df934e4b7beffaf0ef4f0c8c82193a98fc1ca220b5998b9` |
| revision-04 Pro result intake | `5,168` | `104b90d56ceaca304eb5ae361b24464cafce03d43056eec0d9fc438719caca1d` |
| matched-support resource handoff | `17,434` | `6114654ca1735cde6b3a25fda62dec25ca36738444c4302ab629965073a8df49` |
| R01 successor authority | `28,600` | `fc0fbca6005845ec476922d82a7454f6c8ed14c2b7f4097342e853c20b6edf87` |

The nine-path Git diff from entry snapshot
`b9c63e6d8fbc6f8b74470c8e2312c2c1b42c6a8c` to the census commit was empty.
Concurrent documents outside those paths were not inspected or incorporated.

The three retained R01 payload files were present at the accepted runtime root:

| payload object | bytes | SHA-256 |
| --- | ---: | --- |
| `summary.json` | `418` | `a48151cf0a6ab94950ea3ed471d643f2caacea4e750ea244e652006944a6d283` |
| `manifest.json` | `3,580` | `eb24ac8f534e54b4cff8f110c1c6b0808e0d10ab61997aeb2065416903286614` |
| `tables.npz` | `51,690` | `93f5446735638a948b38fdd1d26664be953ff765d9811d452825378cb8cf7b3a` |

The bounded receipt/extraction command completed in `0.8 s`, below the
15-minute control-plane cap. It created no scientific root, RNG master, model,
optimizer, checkpoint, or external side effect. This was not a result-bearing
experiment, so no memory-admission or resource-telemetry receipt applies.

## 2. Reference and comparator census

| required or nearby item | direct observation | A1 eligibility |
| --- | --- | --- |
| stated upper reference | `ORACLE`, the canonical nonanticipating immediate-reward-maximizing legal integral allocation | reference present |
| strongest generic design | `FREE-EDGE-FEASIBLE`: identical information, feasible action/decoder, 60 output-connected scalars, equal reachable class, samples, six-config tuning, optimizer, communication, and useful work | design present |
| revision-04 generic outcome | selected configuration exists, but every cell failed the frozen optimization-validity gate: `abs(V64-V32)=(0.046616,0.041676,0.044181,0.044181) > 0.005` | invalid as a competent final baseline result |
| R01 generic outcome | all four cells selected grid index `4`; all failed the universal stationarity gate | stopped before final fitting/evaluation |
| valid final tuned same-information generic results | `0` | missing |
| matched `J_ORACLE(n), J_FREE(n)` pairs for `n={6,12}` | `0 / 2` | missing |

The R01 gate values were:

```text
METRIC/INTACT  0.011467827690972154
METRIC/CUT     0.011041259765624978
FREE/INTACT    0.01181369357638884
FREE/CUT       0.01181369357638884
registered inclusive limit = 0.005
```

The retained R01 payload exactly records `gate_passed=false`,
`gate_failure_reason=ALL_CELL_STATIONARITY_GATE_FALSE`, and
`branch=BOUNDED_NONIDENTIFICATION_STRUCTURAL`. Expected and actual gate-only
work match:

```text
optimizer updates                 24,576
calibration-training decisions     2,359,296
validation decisions                 294,912
autoregressive agent steps        15,925,248
conclusion-training decisions              0
base-evaluation decisions                  0
replay-evaluation decisions                0
```

The 16 final seed identifiers are reserved metadata only. There is no final
seed packet, checkpoint-512 estimand, held-out efficacy interval, or accepted
generic-baseline endpoint.

## 3. Ineligible raw numbers preserved in their original meaning

Two nearby quantities remain real observations, but neither is guidance-A1
headroom:

| quantity | value | why ineligible |
| --- | ---: | --- |
| minimum deterministic `ORACLE - PUBLIC-LOAD-SOFTMAX` normalized gap | `0.09578626764286009` | comparator is fixed, untuned, and weaker-information diagnostic only |
| revision-04 `METRIC-GROUND - FREE-EDGE-FEASIBLE` at `N=6` | `0.010834` (`[0.010041, 0.011628]`) | treatment-minus-generic, not upper-minus-generic; branch 1 controlled |
| revision-04 `METRIC-GROUND - FREE-EDGE-FEASIBLE` at `N=12` | `0.010156` (`[0.009455, 0.010858]`) | treatment-minus-generic, not upper-minus-generic; branch 1 controlled |

The two revision-04 values are retained only for audit and prospective design.
The accepted first-match result explicitly supports no positive, negative,
generic, equivalence, retention, or deletion claim.

## 4. Frozen rule applied verbatim

The first applicable branch from the card is:

> `HC-B / UPPER_PRESENT_BASELINE_RESULT_UNAVAILABLE`: the stated upper
> reference exists, but no valid final tuned same-information generic result
> exists for at least one held-out roster. Report `H_A1=NOT_IDENTIFIED`.

`HC-X` does not apply because the tracked receipts and retained R01 bytes are
internally reconcilable. `HC-A` fails because the competent final baseline
count is zero. `HC-C` and `HC-D` fail because the `ORACLE` reference is stated
and bound to the host. The result is therefore exactly **`HC-B`**, with no raw
guidance-A1 gap to report.

No draft MEI is applied. No algorithm polarity, B authorization, direction
lifecycle, fusion, or Portfolio disposition follows.

## 5. Exposure and scientific/engineering boundary

```text
new learner parameters = 0
initialisation scale = not applicable
parameter displacement = 0
environment transitions = 0
learner/trainer/evaluator calls = 0/0/0
optimizer updates = 0
RNG draws = 0
checkpoint reads/writes = 0/0
```

These zero counts describe this census, not the historical C attempts. No code,
runner, test, validator, gate, registry, telemetry, or other Engineering Scope
Specification section 4 machinery was added. No section 5 budget was breached.

Scientific result and engineering conformance remain separate: the historical
payload receipts establish that the recorded R01 bytes and counts exist; they
do not make the failed stationarity gate an efficacy result. Likewise, the
absence of a competent final baseline is an evidence-availability fact, not a
negative algorithm result.

## 6. Direct observation, inference, and limits

Directly observed:

- the canonical `ORACLE` upper reference is explicitly defined on the frozen
  host;
- `FREE-EDGE-FEASIBLE` is the strongest same-information, equal-class generic
  comparator design;
- revision 04 failed all four frozen optimization-validity cells before any
  efficacy branch could control;
- R01 failed all four stationarity cells and executed zero conclusion training,
  base evaluation, and replay evaluation; and
- no accepted matched `ORACLE-FREE` endpoint is available at `N=6` or `N=12`.

Direction-local inference: the host contains coupled allocation and a shared
team-return credit path because each entity action changes residual capacity
and later legal consequences. The current evidence does not establish that
this structure is the binding obstacle relative to a competent generic
learner. That is advice for Root's aggregation, not Portfolio action.

Strongest support for real task headroom: the minimum accepted deterministic
oracle-minus-load gap across the certified claim states is
`0.09578626764286009`.

Strongest contradiction to a mechanism-headroom reading: that diagnostic sees
strictly less information and is untuned, while the required competent
same-information generic result is absent.

Surviving alternative: shared unfinished finite-budget optimization explains
both stopped objects, and a competent tuned equal-class generic learner may
close much or all of the oracle gap.

The next discriminator, only if separately selected, is a valid final
`FREE-EDGE-FEASIBLE` result on this exact population with the already-declared
information, tuning, work, native endpoint, and matched oracle aggregates. This
census does not open, implement, or launch that object.
