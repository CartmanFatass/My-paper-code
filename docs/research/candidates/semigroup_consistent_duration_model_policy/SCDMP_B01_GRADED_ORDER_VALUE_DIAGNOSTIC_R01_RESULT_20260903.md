# SCDMP graded-order-value diagnostic R01 — result (2026-09-03)

Executed 2026-09-03 by Claude Code (Fable 5.1) against the frozen card
`SCDMP_B01_GRADED_ORDER_VALUE_DIAGNOSTIC_R01_CARD_20260903.md`, object
`SCDMP-A-GRADED-ORDER-VALUE-DIAGNOSTIC-R01`, after both predictions were placed on record
(compliance note C.4, commit `19eeb9338`; card §11).

**Question.** The accepted base run found the order-**swapped** first action fatal in all twelve
`(state, graph)` cells, so the held-out `M - X` was the matched arm's absolute competence rather
than a graded order value. Why is the swapped arm uniformly fatal, and does a survivable
neighbourhood of the host exist in which `M - X` is graded?

**Claim ceiling: `A/RECON`.** No learner was trained, no optimizer step was taken, no action was
selected from an outcome, and nothing here supplies, removes or reverses any order-value polarity.
The accepted base-run result and its published branch `PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL`
are unchanged. This object can bound how that result is *read*; it cannot change it.

| Fact | Value |
| --- | --- |
| Object | `SCDMP-A-GRADED-ORDER-VALUE-DIAGNOSTIC-R01` |
| Evidence class | `A/RECON`; `scientific_polarity: null`, `order_value_polarity: null` |
| Base run read (accepted, published) | `…/exp/RUN-01-REPLACEMENT-01/SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01-ATTEMPT-01` |
| Quarantined root | `SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01` — **not opened, traversed, read, hashed or copied** |
| `mf_rs_native.cpp` | **unedited**; sha256 `94ed52b662d79aed532fa1d57ee07e7136fcbefd00f377f2b7dd6fdc48f086ed`, 19,286 B — byte-identical to the base run's recorded value |
| HEAD at launch | `ee84406cc5aa0c659c9088792dfb838492bedbf9` — "Record the VNFC relabel-probe decision" |
| Source identity | assigned base `dbd85cbe98bc8705cc5dc0ea72eb20480551e167`; owned-tree aggregate `043270bca13044a7af86c4fc88553e58745f22dcd325d547990de1dfc397414b`; owned `git diff` sha256 `d0059b2f36e7e6f2f336eb8a26f45e5996bff83b5c74e5308b8ed54edd69f621` — all three **byte-identical to the base run's**, i.e. `OWNED_PRODUCTION_PATHS` is unchanged since the accepted run |
| Interpreter | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, torch intra-op threads `1` (≤ 4 as instructed) |
| Output root (gitignored) | `temp/directions/semigroup_consistent_duration_model_policy/exp/graded_order_value_diagnostic_r01_20260903/` |
| Wall | **240.79 s (4 min 1 s)** against a projected ≤ 10 min and a hard cap of 30 min |
| **Reading** | **`G-A`** — mechanism (i), with a survivable neighbour |

---

## 1. Resource admission (a launch condition, unchanged)

One fresh 4 GiB physical/effective admission was taken immediately before any measurement, before
any RNG master, any model load, any native call and any artifact.

| Field | Value |
| --- | --- |
| Receipt | `<output root>/admissions/admit-memory-20260903.json` (create-only) |
| `captured_at` / `assessed_at` | `2026-09-03T10:50:45.571457Z` / `2026-09-03T10:50:45.605647Z` |
| `available_physical_bytes` | `12,075,593,728` (11.25 GiB) |
| `effective_available_bytes` | `12,075,593,728` (11.25 GiB) |
| `minimum_available_bytes` | `4,294,967,296` |
| `physical_floor_pass` / `effective_floor_pass` / `passed` | `true` / `true` / `true` |
| `measurement_source` | `GlobalMemoryStatusEx` |
| `failure_reasons` | `[]` |

## 2. Command actually run

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_scdmp_graded_order_value_diagnostic_r01.py \
  --base-run-root .../exp/RUN-01-REPLACEMENT-01/SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01-ATTEMPT-01 \
  --output-root   .../exp/graded_order_value_diagnostic_r01_20260903 \
  --receipt       .../exp/graded_order_value_diagnostic_r01_20260903/admissions/admit-memory-20260903.json \
  --threads 1
```

with `TMPDIR`/`TEMP`/`TMP` set to `<output root>/native-tmp` (deviation **D1**, §9).

## 3. Bit-identity of the diagnostic translation unit at `(0.88, 0.25)` — verified and recorded **before** any grid row

The card requires that the diagnostic translation unit reproduce the frozen library exactly at the
frozen parameters over the whole M1 census, and that a mismatch abort the object. The runner
performs and persists this check as the step immediately after the admission and immediately before
the first grid row; `<output root>/bit-identity-check.json` is written before `m2-sweep.json` is
begun.

The diagnostic translation unit is **derived from the frozen source by four exact, unique textual
substitutions** plus two inserted blocks; the frozen file itself is never written to.

| Site | Frozen text | Diagnostic text |
| --- | --- | --- |
| `:173` | `output[6 + i] = state.z[i] / 0.25;` | `output[6 + i] = state.z[i] / mf_diag_z_limit;` |
| `:298` | `state.z[i] = 0.84 * state.z[i] + std::max(0.0, tau[i] - 0.88);` | `… std::max(0.0, tau[i] - mf_diag_tau_leak);` |
| `:307` | `state.cable_overload = *std::max_element(state.z, state.z + 4) > 0.25 ? 1 : 0;` | `… > mf_diag_z_limit ? 1 : 0;` |
| `:315` | `&& *std::max_element(state.z, state.z + 4) <= 0.25` | `&& … <= mf_diag_z_limit` |

Each of the four sites is asserted to occur **exactly once** in the frozen source before
substitution. The unrelated `0.88` at `:292` (lateral decay) is untouched, which the uniqueness
assertion on the `:298` site enforces. Two mutable globals initialised to `0.88` and `0.25` are
inserted at the unique `namespace {` anchor (`:14`), and one exported setter
`mf_diag_set_cable_parameters` is appended.

| Field | Value |
| --- | --- |
| Frozen source | 19,286 B, sha256 `94ed52b662d79aed532fa1d57ee07e7136fcbefd00f377f2b7dd6fdc48f086ed` |
| Diagnostic source | 19,985 B, sha256 `6227f171cb7dd30344d877fadc4848ad6c9020b9c62323fc996dc3d3fe07c62c` (kept at `<output root>/diagnostic-native/mf_rs_diagnostic.cpp`) |
| Compiler / flags | `cl.exe` 14.44.35207 (19.44.35228, x64) — `/nologo /std:c++20 /O2 /EHsc /LD /W4`, identical to the production build |
| Frozen DLL | 146,432 B, sha256 `961d44a9b72a5e2e6c25acab5eb01cc5013ae6028779c1a4fe605aa5cfb7fe94` |
| Diagnostic DLL | 146,432 B, sha256 `5fc85585fca55ce2f97943cded84f81b563ac787d3a80d0bfdee1d45d4cb9de6` |
| ABI | version `3`, magic `5568228507022733361`, max batch width `144`; struct sizes reset/step/output/state `48 / 320 / 336 / 552` on both libraries |
| **Frozen-library census sha256** | **`ac7828a37e1ffcc5527b9b8bf1616ec153e9f63aefb8acecc602ecc6e39b298a`** |
| **Diagnostic-library census sha256 at `(0.88, 0.25)`** | **`ac7828a37e1ffcc5527b9b8bf1616ec153e9f63aefb8acecc602ecc6e39b298a`** |
| `bit_identical` | **`true`** over all **864** census cells |

The digest is the SHA-256 of the canonical JSON of the entire 864-row census — every absorbing
transition index, constraint label, endpoint, `dock_tick`, cumulative reward, `max(z)`, the full
four-carrier `z` vector, `|phi|`, the lateral error and every count — so identity is over the
measured facts, not over a summary. The two DLL binaries differ in bytes (MSVC output is not
byte-reproducible across builds; see **D7**), which is exactly why the card defines the check over
outputs.

## 4. M1 — full first-action census at the frozen row

864 missions: 6 twin states × 2 graphs (`HR`, `RH`) × 18 catalogue actions × 4 fresh disturbance
tapes. Each mission forces the catalogue action for the state's external `k` and then hands back to
the state's own immutable update-160 foundation for the remainder (deviation **D2** on which
foundation, **D3** on lane batching).

The disturbance tapes come from RNG domain
`graded-order-value-diagnostic-r01-disturbance-sign`, which appears in no production stream
(`source-…`, `development-…`, `heldout-…`, `foundation-…`, `a-recon-…`), with five-tuple addresses
`(state_id, tape, hold, tick, channel)` that no production address shape can collide with.

**Counts (all nonzero).**

| Count | Value |
| --- | --- |
| Missions declared / actually run | 864 / **864** |
| Native transitions (ticks advanced) | **99,572** |
| Native `mf_rs_step_batch` evaluator calls | **11,394** (864 forced holds + 10,530 handback renewals) |
| Foundation policy queries | **10,530** |
| Absorbing missions | **336** — every one `cable_overload`, every one **inside** the forced hold, every one with **0** policy queries |
| Safe docks | **528** |
| Timeouts | **0** |
| Other constraints ever fired (`gantry_contact`, `attitude_loss`, `formation_loss`) | **0** |

### The census, per action × graph (aggregated over the 6 states × 4 tapes)

| `a` | share vector `r` | action | graph | absorbing / 24 | constraint | absorbing transition | inside hold | mean `U` over 24 | max `z` at termination | tape-invariant | state-invariant |
| ---: | --- | ---: | --- | ---: | --- | --- | --- | ---: | ---: | --- | --- |
| 1 | `( 0,  0,  0,  0)` | **0** | HR | 0 | none | n/a | n/a | `0.033883` | `0.0000` | yes | yes |
| 1 | `( 0,  0,  0,  0)` | **0** | RH | 0 | none | n/a | n/a | `0.035829` | `0.0000` | yes | yes |
| 1 | `( 1, -1,  0,  0)` | **1** | HR | 0 | none | n/a | n/a | `0.034570` | `0.0000` | yes | yes |
| 1 | `( 1, -1,  0,  0)` | **1** | RH | 0 | none | n/a | n/a | `0.036287` | `0.0000` | yes | yes |
| 1 | `(-1,  1,  0,  0)` | **2** | HR | 0 | none | n/a | n/a | `0.032624` | `0.0000` | yes | yes |
| 1 | `(-1,  1,  0,  0)` | **2** | RH | 0 | none | n/a | n/a | `0.034913` | `0.0000` | yes | yes |
| 1 | `( 0,  0,  1, -1)` | **3** | HR | 0 | none | n/a | n/a | `0.032624` | `0.0000` | yes | yes |
| 1 | `( 0,  0,  1, -1)` | **3** | RH | 0 | none | n/a | n/a | `0.035829` | `0.0000` | yes | yes |
| 1 | `( 0,  0, -1,  1)` | **4** | HR | 0 | none | n/a | n/a | `0.034112` | `0.0000` | yes | yes |
| 1 | `( 0,  0, -1,  1)` | **4** | RH | 0 | none | n/a | n/a | `0.035371` | `0.0000` | yes | yes |
| 1 | `( 1,  0, -1,  0)` | **5** | HR | 0 | none | n/a | n/a | `0.034455` | `0.0000` | yes | yes |
| 1 | `( 1,  0, -1,  0)` | **5** | RH | 0 | none | n/a | n/a | `0.035714` | `0.0000` | yes | yes |
| 1 | `(-1,  0,  1,  0)` | **6** | HR | 0 | none | n/a | n/a | `0.032395` | `0.0000` | yes | yes |
| 1 | `(-1,  0,  1,  0)` | **6** | RH | 0 | none | n/a | n/a | `0.035371` | `0.0000` | yes | yes |
| 1 | `( 0,  1,  0, -1)` | **7** | HR | 0 | none | n/a | n/a | `0.033310` | `0.0000` | yes | yes |
| 1 | `( 0,  1,  0, -1)` | **7** | RH | 0 | none | n/a | n/a | `0.035485` | `0.0000` | yes | yes |
| 1 | `( 0, -1,  0,  1)` | **8** | HR | 0 | none | n/a | n/a | `0.034455` | `0.0000` | yes | yes |
| 1 | `( 0, -1,  0,  1)` | **8** | RH | 0 | none | n/a | n/a | `0.035714` | `0.0000` | yes | yes |
| 2 | `( 0,  0,  0,  0)` | **9** | HR | 24 | `cable_overload` | 5,6,7 | inside | `0.000000` | `0.2716` | yes | yes |
| 2 | `( 0,  0,  0,  0)` | **9** | RH | 24 | `cable_overload` | 5,6,7 | inside | `0.000000` | `0.2716` | yes | yes |
| 2 | `( 1, -1,  0,  0)` | **10** | HR | 0 | none | n/a | n/a | `0.062157` | `0.0000` | yes | yes |
| 2 | `( 1, -1,  0,  0)` | **10** | RH | 24 | `cable_overload` | 5,6 | inside | `0.000000` | `0.2621` | yes | yes |
| 2 | `(-1,  1,  0,  0)` | **11** | HR | 24 | `cable_overload` | 2 | inside | `0.000000` | `0.3117` | yes | yes |
| 2 | `(-1,  1,  0,  0)` | **11** | RH | 24 | `cable_overload` | 5,6 | inside | `0.000000` | `0.2640` | yes | yes |
| 2 | `( 0,  0,  1, -1)` | **12** | HR | 24 | `cable_overload` | 5,6 | inside | `0.000000` | `0.2640` | yes | yes |
| 2 | `( 0,  0,  1, -1)` | **12** | RH | 0 | none | n/a | n/a | `0.063187` | `0.0000` | yes | yes |
| 2 | `( 0,  0, -1,  1)` | **13** | HR | 24 | `cable_overload` | 5,6 | inside | `0.000000` | `0.2621` | yes | yes |
| 2 | `( 0,  0, -1,  1)` | **13** | RH | 24 | `cable_overload` | 2 | inside | `0.000000` | `0.3116` | yes | yes |
| 2 | `( 1,  0, -1,  0)` | **14** | HR | 0 | none | n/a | n/a | `0.061813` | `0.0000` | yes | yes |
| 2 | `( 1,  0, -1,  0)` | **14** | RH | 24 | `cable_overload` | 2 | inside | `0.000000` | `0.3116` | yes | yes |
| 2 | `(-1,  0,  1,  0)` | **15** | HR | 24 | `cable_overload` | 2 | inside | `0.000000` | `0.3117` | yes | yes |
| 2 | `(-1,  0,  1,  0)` | **15** | RH | 0 | none | n/a | n/a | `0.063072` | `0.0000` | yes | yes |
| 2 | `( 0,  1,  0, -1)` | **16** | HR | 24 | `cable_overload` | 5,6 | inside | `0.000000` | `0.2645` | yes | yes |
| 2 | `( 0,  1,  0, -1)` | **16** | RH | 24 | `cable_overload` | 5,6,7 | inside | `0.000000` | `0.2715` | yes | yes |
| 2 | `( 0, -1,  0,  1)` | **17** | HR | 24 | `cable_overload` | 5,6,7 | inside | `0.000000` | `0.2719` | yes | yes |
| 2 | `( 0, -1,  0,  1)` | **17** | RH | 24 | `cable_overload` | 5,6 | inside | `0.000000` | `0.2626` | yes | yes |

Every row is both **tape-invariant** (the four tapes agree within each state) and
**state-invariant** (all six states agree). Absorption is therefore fully determined by
`(graph, action)` — mechanism **(i)** — on this panel.

### Reading the pattern against the host arithmetic

The census reproduces the card's §3 code-read arithmetic exactly, with no free parameters:

- **No `a = 1` row can overload.** With `a = 1`, `tau_i = 0.38 + 0.12 + 0.16·max(b_i,0) - 0.10 r_i + …`
  peaks near `0.66`, below the `0.88` leak threshold, so `max(0, tau_i - 0.88) = 0` on every tick.
  Measured: all nine `a = 1` rows survive and dock in all 24 missions on both graphs, with
  `max(z) = 0.0000` throughout.
- **On `HR` the post-event latent is `q = 1`, so `b = (1, -1, 0, 0)` and carrier 0 is the loaded
  one.** At `a = 2`, `tau_0 = 0.38 + 0.24 + 0.32 - 0.10 r_0 = 0.94 - 0.10 r_0`. Only `r_0 = +1`
  brings it to `0.84 < 0.88`. The catalogue rows with `r_0 = +1` at `a = 2` are exactly **10**
  `(1,-1,0,0)` and **14** `(1,0,-1,0)` — and those are exactly the two `a = 2` rows that survive on
  `HR`.
- **On `RH` the post-event latent is `q = 0`, so `b = (0, 0, 1, -1)` and carrier 2 is loaded.** The
  rows with `r_2 = +1` are **12** `(0,0,1,-1)` and **15** `(-1,0,1,0)` — exactly the two `a = 2`
  rows that survive on `RH`.
- **`r_i = -1` on the loaded carrier is the fastest failure.** `tau_0 = 1.04`, excess `0.16` per
  tick, `z_2 = 0.16 + 0.84·0.16 = 0.2944 > 0.25`: absorption at transition **2**. Measured: rows 11
  and 15 on `HR` and rows 13 and 14 on `RH` absorb at transition 2 with `max(z) ≈ 0.3117`.
- **`r_i = 0` on the loaded carrier** gives excess `0.06`, and `z_n = 0.06·(1 - 0.84^n)/0.16`
  crosses `0.25` at `n = 6`–`7`. Measured: absorbing transitions 5, 6 or 7 with `max(z) ≈ 0.26`–`0.27`.

So the development-selected matched action is not merely *better* on its graph: at `a = 2` it is one
of only two catalogue rows that are physically admissible at all on that graph, and the swapped
partner is one of the fourteen that are not. **Fourteen of the thirty-six `(action, graph)` pairs
are uniformly fatal, and all fourteen are `a = 2`.**

### The twelve swapped cells (the count `D` is taken from here)

| state | `k` | graph | swapped action | absorbing transition | constraint | inside the forced hold | `U` | `max(z)` over the four tapes | policy queries | tape-invariant |
| --- | ---: | --- | ---: | ---: | --- | --- | ---: | --- | ---: | --- |
| `k7-early` | 7 | HR | 12 | 6 | `cable_overload` | inside | `0.000000` | `0.2634`–`0.2640` | 0 | yes |
| `k7-early` | 7 | RH | 10 | 6 | `cable_overload` | inside | `0.000000` | `0.2615`–`0.2621` | 0 | yes |
| `k7-middle` | 7 | HR | 12 | 6 | `cable_overload` | inside | `0.000000` | `0.2631`–`0.2638` | 0 | yes |
| `k7-middle` | 7 | RH | 10 | 6 | `cable_overload` | inside | `0.000000` | `0.2612`–`0.2619` | 0 | yes |
| `k7-late` | 7 | HR | 12 | 6 | `cable_overload` | inside | `0.000000` | `0.2501`–`0.2508` | 0 | yes |
| `k7-late` | 7 | RH | 10 | 6 | `cable_overload` | inside | `0.000000` | `0.2503`–`0.2510` | 0 | yes |
| `k13-early` | 13 | HR | 12 | 6 | `cable_overload` | inside | `0.000000` | `0.2566`–`0.2571` | 0 | yes |
| `k13-early` | 13 | RH | 10 | 6 | `cable_overload` | inside | `0.000000` | `0.2547`–`0.2552` | 0 | yes |
| `k13-middle` | 13 | HR | 12 | 5 | `cable_overload` | inside | `0.000000` | `0.2520`–`0.2523` | 0 | yes |
| `k13-middle` | 13 | RH | 10 | 5 | `cable_overload` | inside | `0.000000` | `0.2508`–`0.2512` | 0 | yes |
| `k13-late` | 13 | HR | 12 | 6 | `cable_overload` | inside | `0.000000` | `0.2550`–`0.2557` | 0 | yes |
| `k13-late` | 13 | RH | 10 | 6 | `cable_overload` | inside | `0.000000` | `0.2533`–`0.2538` | 0 | yes |

`D = 12` of twelve.

Every one of the twelve cells absorbs, with `cable_overload`, inside the forced hold, at transition
5 or 6, in all four tapes, with zero policy queries — the mission ends before the foundation is ever
consulted. **`D = 12`.**

The absorbing transition index (5 or 6) never exceeds the cell's `k` (7 or 13): the count of cells
in which it does is **0 of 12**, so the alternative trigger of branch `G-D` does not fire either.

### The twelve matched cells, for contrast

| state | `k` | graph | matched action | terminal | `U` over the four tapes | mean `U` |
| --- | ---: | --- | ---: | --- | --- | ---: |
| `k7-early` | 7 | HR | 10 | safe dock | `0.046703`, `0.043956`, `0.049451`, `0.049451` | `0.047390` |
| `k7-early` | 7 | RH | 12 | safe dock | `0.057692`, `0.054945`, `0.057692`, `0.054945` | `0.056319` |
| `k7-middle` | 7 | HR | 10 | safe dock | `0.068681`, `0.068681`, `0.065934`, `0.071429` | `0.068681` |
| `k7-middle` | 7 | RH | 12 | safe dock | `0.068681`, `0.068681`, `0.065934`, `0.071429` | `0.068681` |
| `k7-late` | 7 | HR | 10 | safe dock | `0.032967`, `0.035714`, `0.032967`, `0.035714` | `0.034341` |
| `k7-late` | 7 | RH | 12 | safe dock | `0.032967`, `0.035714`, `0.032967`, `0.035714` | `0.034341` |
| `k13-early` | 13 | HR | 10 | safe dock | `0.085165`, `0.074176`, `0.082418`, `0.085165` | `0.081731` |
| `k13-early` | 13 | RH | 12 | safe dock | `0.085165`, `0.074176`, `0.082418`, `0.085165` | `0.081731` |
| `k13-middle` | 13 | HR | 10 | safe dock | `0.060440`, `0.057692`, `0.060440`, `0.060440` | `0.059753` |
| `k13-middle` | 13 | RH | 12 | safe dock | `0.057692`, `0.054945`, `0.060440`, `0.057692` | `0.057692` |
| `k13-late` | 13 | HR | 10 | safe dock | `0.079670`, `0.082418`, `0.082418`, `0.079670` | `0.081044` |
| `k13-late` | 13 | RH | 12 | safe dock | `0.079670`, `0.079670`, `0.082418`, `0.079670` | `0.080357` |

Twelve of twelve dock in all four tapes.

### Within-host survivable wrong first actions (card §7, recorded, does not change the branch)

The card asks whether M1 finds a catalogue row at `a = 1` that is a **costly but survivable** wrong
first action at the **frozen** parameters. It does, and not marginally: **all nine `a = 1` rows are
survivable on both graphs in all 24 missions each**, at a mean `U` of `0.0324`–`0.0363` against the
matched arm's `0.0622` (`HR`) and `0.0632` (`RH`) — 52% to 57% of the matched return, paid but not
fatal. This is recorded under the branch the swapped-pair census selects and does not change it.

## 5. M2 — the 7 × 7 `TAU_LEAK` × `Z_LIMIT` neighbourhood sweep

49 grid points × 6 states × 2 graphs × 2 arms × 4 tapes = **4,704 missions**, declared and actually
run. `M`, `X` and `M - X` are the parent card's `0.5 · [HR + RH]` per-state averages, then averaged
over the six states.

Every row with `Z_LIMIT != 0.25` also changes the dock predicate (`:315`) and the actor-visible
observation normaliser (`:173`), so such a row is **not the frozen host**: the base run's foundation
competence does not transfer to it and its `M - X` is not comparable to the base run's. Every row
with `TAU_LEAK != 0.88` changes the failure predicate only. Both are recorded with each row below.

| `TAU_LEAK` | `Z_LIMIT` | `S(g)` /12 | matched dock /12 | `M` | `X` | `M - X` |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0.88` **(frozen row)** | `0.25` | 0 | 12 | `0.06267170` | `0.00000000` | `0.06267170` |
| `0.88` | `0.30` | 6 | 12 | `0.06267170` | `0.02581273` | `0.03685897` |
| `0.88` | `0.35` | 6 | 12 | `0.06267170` | `0.02581273` | `0.03685897` |
| `0.88` | `0.40` | 12 | 12 | `0.06267170` | `0.06221383` | `0.00045788` |
| `0.88` | `0.45` | 12 | 12 | `0.06267170` | `0.06221383` | `0.00045788` |
| `0.88` | `0.50` | 12 | 12 | `0.06267170` | `0.06221383` | `0.00045788` |
| `0.88` | `0.60` | 12 | 12 | `0.06267170` | `0.06221383` | `0.00045788` |
| `0.90` | `0.25` | 8 | 12 | `0.06267170` | `0.04756181` | `0.01510989` |
| `0.90` | `0.30` | 12 | 12 | `0.06267170` | `0.06221383` | `0.00045788` |
| `0.90` | `0.35` | 12 | 12 | `0.06267170` | `0.06221383` | `0.00045788` |
| `0.90` | `0.40` | 12 | 12 | `0.06267170` | `0.06221383` | `0.00045788` |
| `0.90` | `0.45` | 12 | 12 | `0.06267170` | `0.06221383` | `0.00045788` |
| `0.90` | `0.50` | 12 | 12 | `0.06267170` | `0.06221383` | `0.00045788` |
| `0.90` | `0.60` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.92` | `0.25` | 12 | 12 | `0.06267170` | `0.06221383` | `0.00045788` |
| `0.92` | `0.30` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.92` | `0.35` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.92` | `0.40` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.92` | `0.45` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.92` | `0.50` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.92` | `0.60` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.94` | `0.25` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.94` | `0.30` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.94` | `0.35` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.94` | `0.40` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.94` | `0.45` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.94` | `0.50` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.94` | `0.60` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.96` | `0.25` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.96` | `0.30` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.96` | `0.35` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.96` | `0.40` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.96` | `0.45` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.96` | `0.50` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.96` | `0.60` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.98` | `0.25` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.98` | `0.30` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.98` | `0.35` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.98` | `0.40` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.98` | `0.45` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.98` | `0.50` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `0.98` | `0.60` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `1.00` | `0.25` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `1.00` | `0.30` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `1.00` | `0.35` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `1.00` | `0.40` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `1.00` | `0.45` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `1.00` | `0.50` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |
| `1.00` | `0.60` | 12 | 12 | `0.06267170` | `0.06227106` | `0.00040064` |

**Summary of the surface.** The matched arm docks in **12 of 12** cells at **all 49** grid points,
so no row is "broken" in the card's sense. `S(g)` takes exactly four values across the grid:

| `S(g)` | grid points | which |
| ---: | ---: | --- |
| 0 | 1 | the frozen row `(0.88, 0.25)` |
| 6 | 2 | `(0.88, 0.30)` and `(0.88, 0.35)` — **exactly the six `k = 7` cells survive and the six `k = 13` cells absorb** |
| 8 | 1 | `(0.90, 0.25)` — the six `k = 7` cells plus `k13-early RH` and `k13-late RH`; the only grid point anywhere in the sweep with **tape-dependent** cells (`k13-early HR`, `k13-late HR` absorb on some tapes and not others) |
| 12 | 45 | everything else |

The `S(g) = 6` rows are again exactly what the accumulator predicts: with `TAU_LEAK = 0.88` and the
swapped action's excess of `0.06` per tick, `z_n = 0.375·(1 - 0.84^n)`, giving `z_7 = 0.264` and
`z_13 = 0.336` — under `Z_LIMIT = 0.30` the `k = 7` holds finish below the limit and the `k = 13`
holds do not.

### The nearest survivable neighbour

The card fixes the survivability test (`S(g) >= 11` **and** matched dock `>= 11`) but does not
define "nearest". Defined here (deviation **D4**) as Manhattan distance in **declared grid steps**
(`TAU_LEAK` step `0.02`, `Z_LIMIT` step `0.05` over the first five values), ties broken by smaller
`TAU_LEAK` then smaller `Z_LIMIT`. No one-step neighbour is survivable; two rows tie at two steps
and have **identical** `M`, `X` and `M - X`, so the tie-break is numerically immaterial.

| Row | steps from frozen | `S(g)` | matched dock | `M` | `X` | **`M - X`** |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **`(TAU_LEAK 0.90, Z_LIMIT 0.30)`** — the named nearest survivable neighbour | 2 | **12** / 12 | 12 / 12 | `0.06267170` | `0.06221383` | **`0.00045788`** |
| `(0.92, 0.25)` — equidistant, identical values | 2 | 12 / 12 | 12 / 12 | `0.06267170` | `0.06221383` | `0.00045788` |
| `(0.88, 0.25)` — the frozen row, for comparison | 0 | 0 / 12 | 12 / 12 | `0.06267170` | `0.00000000` | `0.06267170` |

At the neighbour the swapped arm no longer absorbs in any cell (`swapped_cable_absorption_cells: 0`)
and `M - X` becomes a genuine, finite, **graded** quantity — and it is very small:

- `M - X = 0.00045788` against `0.06267170` at the frozen row: a factor of **137**, i.e. the
  neighbour's graded order value is **0.73%** of what the frozen row's `M - X` reported.
- `U = 1 - dock_tick/364`, so `0.00045788 × 364 = 0.1667` — **one sixth of one 364-tick horizon step
  per mission**. The entire graded separation at the nearest survivable row is a handful of
  individual dock ticks.
- It is **not uniformly positive across the six states**:

| state | `M` at `(0.90, 0.30)` | `X` at `(0.90, 0.30)` | `M - X` | in ticks |
| --- | ---: | ---: | ---: | ---: |
| `k7-early` | `0.05185440` | `0.05219780` | **`-0.00034341`** | `-0.125` |
| `k7-middle` | `0.06868132` | `0.06868132` | `0.00000000` | `0.000` |
| `k7-late` | `0.03434066` | `0.03399725` | `+0.00034341` | `+0.125` |
| `k13-early` | `0.08173077` | `0.08104396` | `+0.00068681` | `+0.250` |
| `k13-middle` | `0.05872253` | `0.05734890` | `+0.00137363` | `+0.500` |
| `k13-late` | `0.08070055` | `0.08001374` | `+0.00068681` | `+0.250` |
| **mean** | `0.06267170` | `0.06221383` | **`0.00045788`** | **`+0.167`** |

Four of six states positive, one exactly zero, one negative. Under the parent card's own `>= 11 of
12` style of counting this would not be a repeatable per-state ordering. Stating that is an
observation on this A/RECON panel, not a polarity on the base run.

## 6. The reading rule, applied verbatim in its stated order

Quoting §7 of the card, with the measured values substituted:

> Let `D` = the number of the twelve `(state, graph)` cells in which the swapped first action
> absorbs with `cable_overload` at the frozen row, in **all four** tapes (so `D` counts only cells
> whose outcome is tape-invariant). Let `S(g)` = the same count of cells in which the swapped action
> **survives** the forced hold at grid point `g`. Apply in order; the first branch whose condition
> holds is the reading.

**Measured: `D = 12`** (§4, Table B — twelve of twelve, `cable_overload`, all four tapes).
**Measured: `S(g) = 12` at 45 of the 49 grid points**, with `S(0.88, 0.25) = 0`, `S(0.90, 0.25) = 8`,
`S(0.88, 0.30) = S(0.88, 0.35) = 6` (§5, Table C).

| Order | Branch | Condition as written | Evaluated |
| ---: | --- | --- | --- |
| 1 | **`G-A`** | `D >= 11` **and** some `g` on the declared grid has `S(g) >= 11` with a finite, reported `M - X` at that `g` | `12 >= 11` **true**; 45 grid points have `S(g) >= 11`, the nearest being `(0.90, 0.30)` with a finite `M - X = 0.00045788` reported in §5 — **true**. **Condition holds; this is the reading.** |
| 2 | `G-B` | `D >= 11` **and** no `g` has `S(g) >= 11` | not reached (and false: 45 such `g` exist) |
| 3 | `G-C` | `D <= 8` | not reached (and false: `D = 12`) |
| 4 | `G-D` | `D >= 11` fails and `G-C` fails, **or** the absorbing transition index exceeds the cell's `k` in `>= 3` of the twelve cells | not reached (and both clauses false: `D >= 11` holds, and the index exceeds `k` in **0** of 12 cells) |
| 5 | `G-E` | anything else | not reached |

> A survivable row additionally requires that the frozen catalogue's matched action still docks at
> that `g` in `>= 11` of twelve cells; a row where nothing docks is not survivable, it is broken.

Satisfied at every grid point: matched dock `= 12` of 12 at all 49 points, including `(0.90, 0.30)`.

> If M1 finds a catalogue row at `a = 1` for which the wrong first action is costly but survivable
> at the **frozen** parameters, that is recorded as a within-host survivable action and reported
> under whichever branch the swapped-pair census selects; it does not change the branch.

Recorded in §4: all nine `a = 1` rows are costly but survivable on both graphs. The branch is
unchanged.

### **Reading: `G-A` — mechanism (i), with a survivable neighbour.**

## 7. Verdict on the predictions on record

Both predictions were recorded in card §11 before any measurement.

| Predictor | Prediction, verbatim | Verdict by the rule's wording |
| --- | --- | --- |
| Owner | "owner G-A (deterministic absorption given graph and first action, and a survivable neighbour row exists)" | **Confirmed.** The rule selects `G-A`. Both halves of the stated reason also hold as measured facts: absorption is fully determined by `(graph, action)` — tape-invariant and state-invariant in all 36 pairs — and a survivable neighbour row exists (45 of them). |
| Reviewer | "reviewer also G-A, for the card's own arithmetic" | **Confirmed.** The rule selects `G-A`, and the stated reason is confirmed in the strong form: the census reproduces the card's §3 code-read arithmetic exactly — which `a = 2` rows survive on which graph, and the transition indices 2 and 5–7 predicted by `tau_0 = 0.94 - 0.10 r_0` and `z_n = excess·(1 - 0.84^n)/0.16`. |

Neither prediction is scored on the *size* of the neighbour's `M - X`, and neither predicted one.
The measured `0.00045788` (one sixth of a tick per mission, and not uniformly signed across states)
is new information that the rule's `G-A` label does not carry, and it is reported here on its own
terms.

## 8. What the branch means for `RUN-02A` / `RUN-02B` — options for the owner; **nothing was launched**

The card's `G-A` row, verbatim:

> `RUN-02A`/`RUN-02B` **may run as frozen** — they are already bound to the valid base run and its
> realized `q_by_cell = 001110` — but added seeds strengthen only a *survival* indicator, not a
> graded order value. The direction should open a **new named B object on the survivable neighbour
> row**, declared as a parameter neighbour and not as the frozen host, to obtain a graded `M - X`.
> Priority between the two is a Portfolio decision.

Three things this run adds to that, as options, with no launch and no recommendation being acted on:

1. **`RUN-02A`/`RUN-02B` as frozen remain valid and remain a survival indicator.** Nothing measured
   here invalidates them. On the frozen row `X = 0` exactly in all twelve cells, so their `M - X`
   is `M`: the matched arm's absolute competence, under a first action that is one of only two
   physically admissible `a = 2` rows on its graph. Three or five more foundations would sharpen
   that number and would still not make it graded.
2. **A new B object on a survivable neighbour row is now specifiable with measured numbers.**
   `(TAU_LEAK 0.90, Z_LIMIT 0.30)` is the nearest such row; `(0.92, 0.25)` is equidistant, has
   identical `M`/`X`/`M - X`, and has the advantage of **leaving `Z_LIMIT` at its frozen value**, so
   the dock predicate (`:315`) and the actor-visible observation normaliser (`:173`) are unchanged
   and only the failure predicate moves. If the owner opens such an object, `(0.92, 0.25)` is the
   cleaner declaration for that reason. Either way the effect to be powered for is
   `M - X ≈ 0.00046` — a sixth of a tick per mission — not the `0.063` of the frozen row; four
   tapes and one foundation per state were enough to *observe* it and are plainly not enough to
   *establish* it, and one of the six states has it with the opposite sign.
3. **A hold-length question has appeared that was not the subject of this object.** At
   `(0.88, 0.30)` and `(0.88, 0.35)` survival splits **exactly** along `k`: all six `k = 7` cells
   survive, all six `k = 13` cells absorb, because the same per-tick excess integrates over a longer
   forced hold. That is a `k`-dependent survivability boundary inside the swept neighbourhood, and
   it bears on `flexible_skill_duration` (where SCDMP's `(z, k)` menu is comparator D8) and on the
   §11.3 `tau(1-gamma)/(1-gamma^tau)` reading in `SCDMP_B01_SECTION11_RECAST_INTAKE_20260902.md` §4.
   It is an observation, not a branch: the rule selected `G-A` before `G-D` was reached, and a
   hold-length sweep would be a separate diagnostic object with its own card.

## 9. Deviations from the science card

| # | Deviation | Effect |
| --- | --- | --- |
| **D1** | `TMPDIR`/`TEMP`/`TMP` were redirected to `<output root>/native-tmp` for the whole invocation. The default per-user temp directory holds an older `hmasd_scdmp_mf_rs_mk_native` cache that is unreadable and undeletable by the owning user, and the native loader refuses to proceed against it. Same deviation as the base run's D2. | None on values. The frozen library was rebuilt from the identical, byte-checked source with the identical compiler and flags, and its ABI facts are recorded in §3. |
| **D2** | The card says "return to the immutable foundation checkpoint" without naming which of the two. Resolved to **each state's own source foundation** (`k7-early` 1709, `k7-middle` 2903, `k7-late` 1709, `k13-early` 2903, `k13-middle` 1709, `k13-late` 2903). | This is what the card's own mission arithmetic requires (`6 × 2 × 18 × 4 = 864` and `6 × 2 × 2 × 4 = 96`, i.e. one foundation per state); the base run's development stage instead crossed both foundations into 12 units. `M` and `X` here are therefore **not** numerically identical to the base run's held-out `M`/`X` and are not presented as such. |
| **D3** | Missions are replayed **one lane at a time** (native batch width 1) rather than in the production two-lane `HR`/`RH` batch. | The host is per-lane deterministic and the production two-lane path masks inactive lanes, so no value changes; but the call sequence is not byte-for-byte the production one. |
| **D4** | The production helper `evaluate_twin_branches` could not be reused: it rejects any tape address outside the eight canonical development blocks or a held-out permit, while the card requires a **disjoint** diagnostic RNG domain. The diagnostic reimplements the same forced-hold-then-foundation loop in `census.run_mission`, and the diagnostic tape builder mirrors `rng.materialize_disturbance_tape` exactly (64 hold rows, magnitudes `0.003 / 0.002 / 0.004`, 13 ticks, Bernoulli `0.5`) under the new domain. | The identity check in §3 exercises this same replay path on both libraries, so it is self-consistent; it is not a re-derivation of the base run's numbers. |
| **D5** | "Nearest" survivable neighbour is not defined by the card. Defined post hoc as Manhattan distance in declared grid steps, ties to smaller `TAU_LEAK` then smaller `Z_LIMIT`. | Numerically immaterial here: the two rows that tie at two steps have identical `M`, `X` and `M - X`. Both are reported in §5. |
| **D6** | The M2 rows persist outcome fields only (`utility`, `safe_dock`, `constraint_fired`, `absorbing_transition`, `inside_forced_hold`), not per-mission transition and policy-query counts. | Nonzero-count evidence is reported from M1 (§4), which uses the identical replay function, together with the M2 mission inventory (49 × 96 = 4,704 declared and run). |
| **D7** | The rebuilt frozen DLL's bytes (`961d44a9…`) differ from the base run's recorded DLL sha (`c57aa75d…`), because MSVC output is not byte-reproducible across builds. | The frozen **source** sha256 is byte-identical to the base run's, and the card defines the identity check over census outputs precisely for this reason. Reported, not worked around. |
| **D8** | Resource telemetry was not instrumented: peak process-tree RSS and scratch high water were not measured. Recorded as **`resources_unmeasured: true`**. | Per the §11 recast (`SCDMP_B01_SECTION11_RECAST_INTAKE_20260902.md`, D7), missing resource telemetry is a recorded field and does not invalidate; a measured cap exceedance still would, and none was measured. Wall (`240.79 s` against a 30-minute cap) and durable bytes (`1.95 MB` against a 256 MiB ceiling) **were** measured and are within their ceilings. |

## 10. Could not verify

- **Any order-value polarity.** This is `A/RECON`. The accepted base-run branch
  `PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL` stands exactly as published; nothing here supplies,
  removes, or reverses it.
- **Whether the neighbour row's `M - X = 0.00046` is repeatable.** Four tapes, one foundation per
  state, six states, one realized `q_by_cell = 001110`. One of the six states carries it with the
  opposite sign. Establishing it is a separate B object.
- **Whether the base-run foundations are competent on any off-frozen row** in any sense beyond the
  one measured here — "the matched action still docks in 12 of 12 cells". Every `Z_LIMIT != 0.25`
  row also changes the dock predicate and the actor-visible observation, and no competence gate was
  re-run on any swept row.
- **Peak process-tree RSS and scratch high water** (deviation D8).
- **Whether other host constants produce a graded row.** Only `TAU_LEAK` (`:298`) and `Z_LIMIT`
  (`:307`, `:315`, `:173`) were swept. The accumulator decay `0.84` and the tension coefficients
  `0.38 / 0.12 / 0.16 / 0.10 / 0.04 / 0.03` were not.
- **Whether absorption behaves the same outside `k ∈ {7, 13}`.** The `k`-split observed at
  `(0.88, 0.30)` and `(0.88, 0.35)` is suggestive and untested; a hold-length sweep is a different
  object.
- **Whether any of this generalises past this simulator, this state population, this action
  catalogue, or this realized `q` vector.** None of those were varied.

## 11. Artifacts

All under `temp/directions/semigroup_consistent_duration_model_policy/exp/graded_order_value_diagnostic_r01_20260903/`
(gitignored):

| File | Bytes | Contents |
| --- | ---: | --- |
| `admissions/admit-memory-20260903.json` | 511 | the 4 GiB admission receipt (§1) |
| `bit-identity-check.json` | 7,434 | the `(0.88, 0.25)` identity verdict, both census digests, both libraries' source/DLL/ABI facts (§3) — **written before any grid row** |
| `m1-census.json` | 420,364 | all 864 M1 cells (§4) |
| `m2-sweep.json` | 1,130,570 | all 49 grid points and their 4,704 cells (§5) |
| `summary.json` | 5,434 | admission, identity, counts, wall, thread count, source identity, `scientific_polarity: null` |
| `run.log` | 13,292 | one JSON line per stage and grid point, in execution order |
| `diagnostic-native/mf_rs_diagnostic.cpp` | 19,985 | the derived diagnostic translation unit (§3) |
| `native-tmp/…` | ~168 KiB | the rebuilt frozen library and its build receipt (D1) |

Code (tracked): `experiments/candidates/scdmp_variable_k/graded_order_value_diagnostic_r01/`
(`diagnostic_library.py`, `census.py`) and `scripts/run_scdmp_graded_order_value_diagnostic_r01.py`.
This package is **not** in `OWNED_PRODUCTION_PATHS`, is imported by no result-bearing runner, and
does not change the owned-tree aggregate — which is why the source identity in the header is
byte-identical to the base run's.

## 12. Interpretation boundary

This object explains *why* the base run's `X` was zero and shows that a survivable neighbourhood
exists. It does not make the base run's `M - X` a graded order value, does not license reading the
base run as evidence of graded order value, and does not decide anything about `RUN-02A`/`RUN-02B`.
Section 8 lists options; the Portfolio decides. Nothing was launched.
