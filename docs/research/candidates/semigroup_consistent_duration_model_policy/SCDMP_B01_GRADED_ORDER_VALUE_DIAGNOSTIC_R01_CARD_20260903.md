# SCDMP graded-order-value diagnostic R01 — science card (2026-09-03)

- Direction: `semigroup_consistent_duration_model_policy`
- Object: `SCDMP-A-GRADED-ORDER-VALUE-DIAGNOSTIC-R01`
- Evidence class: **`A/RECON`**. No learner runs, no learner polarity, no order-value polarity.
- Status at freeze: **written, not run.** No measurement in this card has been taken.
- Owner decision that opens it: compliance note Part C.4 (commit `917866cd6`); the base-run
  acceptance is Part C (commit `a42f28e26`)
- Parent result: `SCDMP_B01_RUN_01_REPLACEMENT_01_RESULT_EVIDENCE_20260902.md`
- Parent contract: `SCDMP_MF_RS_MK_ORDER_VALUE_B01_SCIENCE_CARD_20260901.md`
- Recast in force: `SCDMP_B01_SECTION11_RECAST_INTAKE_20260902.md`; evidence spec §11 controlling

## 1. Why this object exists

The accepted base run `SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01-ATTEMPT-01` published
`PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL` with `delta_swap` `0.06109776` / `0.06468922` per
foundation. Its §8 records that this separation is not graded:

> the SWAPPED arm returned `U = 0.0` in every one of its 384 raw cells, always terminating with
> `cable_overload` after 6 transitions and 0 policy queries. So `delta_swap` equals `M`
> identically, and the matched-versus-swapped separation is entirely the swapped control's
> immediate absorption rather than a graded return difference. The COMMON arm absorbed the same way
> in exactly the 80 cells whose common action was `10` or `12` evaluated under the graph it is not
> matched to (5 units × 16 tapes × 1 graph).

§13 of the same document lists the first thing it could not verify:

> **Nothing about why the swapped arm is uniformly zero.** Every swapped cell absorbed with
> `cable_overload` after 6 transitions. Whether that is a property of this six-state population, of
> the two selected actions (`10` and `12`), or of the host's cable dynamics at a forced first hold
> is untested here and would need a different object.

This card is that object.

**Question.** On the frozen host `QUAD-UAV-PALLET-GANTRY-24P5M-v1`, is the observed value of event
order dominated by an *absorbing failure of the wrong first action* — a cable-dynamics property of
the host rather than a graded return difference — and is there a host row in a frozen family, or
(stated as such) a nearest parameter neighbour of the single frozen row, at which the wrong first
action is costly but survivable?

**Non-goals.** This object measures the host, not the algorithm. It produces no order-value
polarity, no competence claim, no duration or semigroup claim, no `q` statement, and no lifecycle
recommendation. It cannot rescue, weaken or reinterpret the accepted base-run result; that result
stands exactly as published.

## 2. Host and catalogue as frozen (parent card, "Host, information and endpoint")

Real native `QUAD-UAV-PALLET-GANTRY-24P5M-v1`, primitive tick `0.1 s`, horizon `364`
(`mf_rs_native.cpp:19`, `kHorizon = 364`), maximum hold `13` (`:20`, `kMaxHold = 13`), endpoint

```text
U = 1{safe dock} * (1 - dock_tick / 364),
```

failure or timeout equal to zero. The complete first-action catalogue is the eighteen rows of
`kActions` at `mf_rs_native.cpp:106-113`: forward command `a in {1,2}` crossed with nine integer
load-share vectors `r`. The two actions the base run selected are

```text
kActions[10] = {2,  1, -1,  0,  0}
kActions[12] = {2,  0,  0,  1, -1}
```

HR overwrites latent state to `p_post=(4,2,1,3), q_post=1`; RH to `p_post=(1,4,2,3), q_post=0`.

**There is no frozen family of host rows.** `QUAD-UAV-PALLET-GANTRY-24P5M-v1` is a single row whose
constants are compiled literals in `mf_rs_native.cpp`; a search of this direction's documents finds
the name used only as one fixed plant. Every non-frozen row this card measures is therefore a
**parameter neighbour of the single frozen row, stated as such**, and is a member of no registered
family. Nothing measured off the frozen row may be reported as the frozen host.

## 3. The constraint that fires, quoted from the host

`cable_overload` is raised at `mf_rs_native.cpp:307`:

```cpp
state.cable_overload = *std::max_element(state.z, state.z + 4) > 0.25 ? 1 : 0;
```

The `z` it reads is a leaky accumulator of per-carrier tension excess,
`mf_rs_native.cpp:297-299`:

```cpp
    for (std::size_t i = 0; i < 4; ++i) {
        state.z[i] = 0.84 * state.z[i] + std::max(0.0, tau[i] - 0.88);
    }
```

`tau` is the per-carrier tension, `mf_rs_native.cpp:280-283`:

```cpp
    for (std::size_t i = 0; i < 4; ++i) {
        tau[i] = 0.38 + 0.12 * a + 0.16 * a * std::max(b[i], 0.0)
            - 0.10 * r[i] + 0.04 * std::fabs(state.phi) + 0.03 * std::fabs(e);
    }
```

and `b` — the carrier-loading pattern — is selected by the **post-event latent** `q`,
`mf_rs_native.cpp:274-276`:

```cpp
    const std::array<double, 4> b = state.q == 1
        ? std::array<double, 4>{{1.0, -1.0, 0.0, 0.0}}
        : std::array<double, 4>{{0.0, 0.0, 1.0, -1.0}};
```

So `b(q=1) = (1,-1,0,0)` is exactly `kActions[10]`'s share vector and `b(q=0) = (0,0,1,-1)` is
exactly `kActions[12]`'s. "Matched" means the forced share vector equals the post-event loading
pattern; "swapped" means it is the other one. The `-0.10 * r[i]` term is the only channel by which
the first action offloads the carrier that `b` loads.

Three further code facts bear on the design below.

1. **The failure threshold is also the dock threshold.** The literal `0.25` at `:307` reappears in
   the `safe_dock` predicate at `mf_rs_native.cpp:315`,
   `*std::max_element(state.z, state.z + 4) <= 0.25`, and again as the observation normaliser at
   `mf_rs_native.cpp:173`, `output[6 + i] = state.z[i] / 0.25`. Sweeping `0.25` therefore changes
   the failure predicate, the endpoint predicate **and** the actor-visible observation at once.
2. **The tension threshold `0.88` is not the only `0.88` in the file.** `mf_rs_native.cpp:292` uses
   the same literal as the lateral-velocity decay, `state.w = 0.88 * state.w - ...`. A sweep must
   change only the occurrence at `:298`.
3. **The forced hold does not return control early.** The hold loop at `mf_rs_native.cpp:344-349`
   runs `planned = min(held_k, kHorizon - n)` primitive ticks and breaks only on `state.terminal`,
   so a first action that absorbs at transition 6 with `k in {7,13}` never hands back to the
   foundation — consistent with the `policy_queries: 0` recorded in every swapped cell.

### Code-read expectation, to be confirmed or refuted by measurement, not assumed

For a forward command `a = 2` on the single carrier with `b[i] = +1`,
`tau[i] = 0.94 - 0.10 * r[i] + 0.04|phi| + 0.03|e|`. Matched (`r[i] = +1`) gives `0.84 + small`,
below the `0.88` leak threshold; swapped (`r[i] = 0` on that carrier) gives `0.94 + small`, an
excess of at least `0.06` every tick. With decay `0.84`, `z_n = excess * (1 - 0.84^n) / 0.16`, whose
`0.06` fixed point is `0.375`; it first exceeds `0.25` at `n = 7` for a bare `0.06` excess and
earlier once the `|phi|` and `|e|` terms are added — bracketing the observed absorption at
transition 6. For `a = 1` the same carrier gives `tau[i] = 0.66 - 0.10 r[i] + small`, which cannot
plausibly reach `0.88` before `attitude_loss` fires at `|phi| > 0.32` (`:310`). If that holds, the
whole phenomenon is confined to the nine `a = 2` rows of the catalogue and a survivable row may
already exist **inside** the frozen catalogue at `a = 1`. Measurement M1 decides this; the card
asserts nothing.

## 4. Candidate mechanisms

- **(i) Deterministic constraint violation.** The swapped first action violates a hard cable
  constraint during the forced first hold regardless of policy, so absorption is deterministic
  given `(graph, first action)` and independent of the state twin and of the disturbance tape.
- **(ii) State-population property.** Absorption depends on the six retained twins — their `phi`,
  `e` and accumulated `z` at the first legal boundary — and would not occur from other reachable
  states.
- **(iii) Timing artefact of the forced hold.** Absorption is an artefact of holding for
  `k in {7,13}` ticks: the absorbing transition index and the hold length interact, and a shorter
  hold would return control to the foundation before `z` crosses `0.25`.

These are not exclusive; the reading rule in §7 resolves them by measured effect size.

## 5. Measurements (outcome-free)

Both measurements replay the frozen host directly. **No learner is trained, no learner is queried
for a selection, no checkpoint is written, and no result-bearing artifact is produced.** The
foundation checkpoints and the six twin states are read from the *accepted, published* base-run
root `temp/directions/semigroup_consistent_duration_model_policy/exp/RUN-01-REPLACEMENT-01/SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01-ATTEMPT-01`.
The quarantined old root `SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01` is not opened, traversed, read,
hashed, copied or referred to for any value; only its already recorded external terminal facts
exist.

### M1 — full first-action census at the frozen row

From each of the six twin states, under each graph `HR` and `RH`, force each of the eighteen
catalogue actions as the first action for the state's external `k`, then return to the immutable
foundation checkpoint for the remainder of the mission, exactly as the parent card's development
stage does. Repeat over `T = 4` fresh disturbance tape blocks drawn from a diagnostic RNG domain
disjoint from every training, source, development and held-out domain of the base run.

Grid: `6 states x 2 graphs x 18 actions x 4 tapes = 864 missions`.

Record per cell: the transition index of absorption (or `null` if the mission reaches a terminal
dock or timeout), **which of the four constraints fired** (`cable_overload`, `gantry_contact`,
`attitude_loss`, `formation_loss`), the endpoint `U`, `dock_tick`, `max(z)` at absorption or at
termination, the per-carrier `z` vector, `|phi|` and `|e|` at the first hold's first tick, the
number of policy queries, and whether absorption occurred at a transition index `<= k` (inside the
forced hold) or `> k` (after handback).

This census answers, without any parameter change: whether absorption is deterministic given
`(graph, action)` across all six states and all four tapes (mechanism i), whether it varies by
state (mechanism ii), whether the absorbing transition index sits inside or outside the forced hold
(mechanism iii), and whether any of the eighteen catalogue rows is a *costly but survivable* wrong
first action already inside the frozen host.

### M2 — two-parameter neighbourhood sweep

Only the two constants the `cable_overload` constraint reads are swept:

| Symbol | Frozen value | Site | Grid |
| --- | ---: | --- | --- |
| `TAU_LEAK` | `0.88` | `mf_rs_native.cpp:298`, inside `max(0.0, tau[i] - 0.88)` — **not** the unrelated `0.88` at `:292` | `{0.88, 0.90, 0.92, 0.94, 0.96, 0.98, 1.00}` |
| `Z_LIMIT` | `0.25` | `mf_rs_native.cpp:307` and, coupled, `:315` and `:173` | `{0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60}` |

`7 x 7 = 49` grid points, the frozen row `(0.88, 0.25)` included as the identity check.

At each grid point run only the matched and swapped arms:
`6 states x 2 graphs x 2 arms x 4 tapes = 96 missions`, `4,704` missions over the sweep. Record per
grid point: whether the swapped first action survives the forced hold in each of the twelve
`(state, graph)` cells, the absorbing transition index where it does not, and the resulting `M`,
`X` and `M - X` computed exactly as the parent card defines them.

**Sweep implementation, and the integrity items that go with it.** `mf_rs_native.cpp` is byte-frozen
and is not edited. The sweep uses a **separate diagnostic translation unit** that takes `TAU_LEAK`
and `Z_LIMIT` as runtime inputs, is never imported by any result-bearing runner, and is not added to
`OWNED_PRODUCTION_PATHS`. Before any sweep point is measured, the diagnostic library must reproduce
the frozen library's outputs **exactly, bit for bit**, at `(0.88, 0.25)` over the whole M1 census; a
mismatch aborts the object and produces no reading. Because `Z_LIMIT` is read by the dock predicate
at `:315` and the observation normaliser at `:173`, every `Z_LIMIT != 0.25` row changes the endpoint
definition and the actor-visible observation as well as the failure predicate: such a row is **not**
the frozen host, the base-run foundation's competence does not transfer to it, and `M - X` measured
there is not comparable to the base run's. All of this is recorded with each row.

### Common integrity items (spec §4, unchanged)

Report nonzero transition and native evaluator counts; declared versus actual missions per stage;
process-tree peak RSS, scratch high water, durable bytes and wall; the exact source identity and
native ABI of both libraries; and the diagnostic RNG domain addresses. One fresh `4 GiB`
physical/effective admission immediately before the invocation is a launch condition
(`python scripts/hmasd_resource_preflight.py admit-memory --out <receipt.json>`). Per the §11
recast, missing resource telemetry is recorded as `resources_unmeasured: true` and does not
invalidate; a measured cap exceedance and any learner-side instrumentation failure still do.

## 6. Budget

| Stage | Missions | Basis | Projected wall |
| --- | ---: | --- | ---: |
| Native build, frozen + diagnostic library | — | MSVC, measured ~6 s per library on 2026-09-02 | ≤ 1 min |
| Bit-identity check at `(0.88, 0.25)` | 864 | re-run of M1 on the diagnostic library | ≤ 1 min |
| M1 census | 864 | base-run held-out stage measured 72 missions/s | ≤ 1 min |
| M2 sweep | 4,704 | same rate, 49 grid points | ≤ 3 min |
| Artifact write and publication | — | base-run publication tail | ≤ 2 min |

**Projected total ≤ 10 minutes. Hard wall cap 30 minutes**, one foreground process,
`torch.set_num_threads(1)`, peak RSS ≤ 2 GiB, scratch ≤ 256 MiB, durable ≤ 256 MiB — the parent
card's engineering ceilings, unchanged. Exceeding the wall cap stops the object with no reading.

## 7. Reading rule — ordered by effect size, thresholds fixed before any data

Let `D` = the number of the twelve `(state, graph)` cells in which the swapped first action absorbs
with `cable_overload` at the frozen row, in **all four** tapes (so `D` counts only cells whose
outcome is tape-invariant). Let `S(g)` = the same count of cells in which the swapped action
**survives** the forced hold at grid point `g`. Apply in order; the first branch whose condition
holds is the reading.

| Branch | Condition, fixed now | Mechanism it supports |
| --- | --- | --- |
| **G-A** | `D >= 11` **and** some `g` on the declared grid has `S(g) >= 11` with a finite, reported `M - X` at that `g` | (i) with a survivable neighbour |
| **G-B** | `D >= 11` **and** no `g` on the declared grid has `S(g) >= 11` | (i) with no survivable neighbour on this grid |
| **G-C** | `D <= 8` | (ii) absorption is state-dependent |
| **G-D** | `D >= 11` fails and `G-C` fails (`D` is 9 or 10), **or** the absorbing transition index exceeds the cell's `k` in `>= 3` of the twelve cells | (iii) timing artefact of the forced hold |
| **G-E** | anything else | no reading; record the census and stop |

A survivable row additionally requires that the frozen catalogue's matched action still docks at
that `g` in `>= 11` of twelve cells; a row where nothing docks is not survivable, it is broken.
If M1 finds a catalogue row at `a = 1` for which the wrong first action is costly but survivable at
the **frozen** parameters, that is recorded as a within-host survivable action and reported under
whichever branch the swapped-pair census selects; it does not change the branch.

### What each branch means for `RUN-02A` / `RUN-02B`

| Branch | Consequence |
| --- | --- |
| **G-A** | `RUN-02A`/`RUN-02B` **may run as frozen** — they are already bound to the valid base run and its realized `q_by_cell = 001110` — but added seeds strengthen only a *survival* indicator, not a graded order value. The direction should open a **new named B object on the survivable neighbour row**, declared as a parameter neighbour and not as the frozen host, to obtain a graded `M - X`. Priority between the two is a Portfolio decision. |
| **G-B** | The frozen row cannot produce a graded `M - X` at all. `RUN-02A`/`RUN-02B` as frozen would add three or five foundations to a survival indicator. Recommend **holding both** and recasting the host row first as a new object with its own card; the base-run result stands unchanged. |
| **G-C** | Absorption is a property of these six twins, not of the host. `RUN-02A`/`RUN-02B` **run as frozen** — they reuse exactly these six states and this realized `q_by_cell`, which is what the expansion law requires — and every claim must name the state dependence. A new state population is a separate later object. |
| **G-D** | The absorption is produced by the `k in {7,13}` menu itself. `RUN-02A`/`RUN-02B` **run as frozen**, and a hold-length sweep becomes the next diagnostic. This is the branch that bears directly on `flexible_skill_duration`, where SCDMP's `(z, k)` menu is comparator D8, and on the §11.3 `tau(1-gamma)/(1-gamma^tau)` reading recorded in `SCDMP_B01_SECTION11_RECAST_INTAKE_20260902.md` §4. |
| **G-E** | No reading. Record the census, change nothing, and return the question to the owner. |

In every branch the accepted base-run result and its published branch
`PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL` are unchanged. This is an `A/RECON` object: it can bound
how that result is *read*, and it cannot supply, remove or reverse any polarity.

## 8. Invalidity

The following produce no reading: any opening, traversal, read, hash or copy of the quarantined
`SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01` root or any descendant; any edit to `mf_rs_native.cpp` or to
any file in `OWNED_PRODUCTION_PATHS`; use of the diagnostic library by any result-bearing runner; a
failed bit-identity check at `(0.88, 0.25)`; any learner training, optimizer step or
outcome-informed action selection; any overlap between the diagnostic RNG domain and the base run's
training, source, development or held-out domains; a failed `4 GiB` admission; a measured resource
cap exceedance; a changed grid, threshold or reading rule after any measurement; and any statement
of order-value polarity.

## 9. Prediction requested from the owner

Before this object is run, the owner is asked to record one prediction, and the reason for it, so
the reading is scored against a prospective statement:

- **(i)** the swapped first action violates a hard cable constraint at the first hold regardless of
  policy — absorption is deterministic given `(graph, first action)`;
- **(ii)** absorption depends on the six twin states and would not occur from other reachable
  states;
- **(iii)** absorption is a timing artefact of the forced first-hold length `k in {7,13}`;
- **unclear** — no prediction.

A second, optional prediction: whether a survivable neighbour exists on the declared
`TAU_LEAK x Z_LIMIT` grid (yes / no / unclear).

## 10. Evidence

- `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_B01_RUN_01_REPLACEMENT_01_RESULT_EVIDENCE_20260902.md` (§8, §13)
- `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_MF_RS_MK_ORDER_VALUE_B01_SCIENCE_CARD_20260901.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_B01_SECTION11_RECAST_INTAKE_20260902.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md`
- `experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/native/mf_rs_native.cpp` (`:19-20`, `:106-113`, `:165-175`, `:271-283`, `:292`, `:296-320`, `:338-352`)
- `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` (§4, §5.1, §6.2, §11)
- `docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md` (Part C, Part C.4)

## 11. Predictions on record — 2026-09-03

Recorded before any measurement of this object, from compliance note C.4 (commit `19eeb9338`). The
body of this card and the reading rule in §7 are unchanged by this section; it exists only so the
reading in §7 is scored against prospective statements.

**Owner, verbatim:**

> owner G-A (deterministic absorption given graph and first action, and a survivable neighbour row
> exists)

**Reviewer, verbatim:**

> reviewer also G-A, for the card's own arithmetic

Both predictions name branch **G-A** of the §7 table: `D >= 11` **and** some `g` on the declared
grid has `S(g) >= 11` with a finite, reported `M - X` at that `g`. The owner's stated reason is
mechanism (i) — absorption deterministic given `(graph, first action)` — together with a "yes" to
the optional second prediction of §9 (a survivable neighbour exists on the declared
`TAU_LEAK x Z_LIMIT` grid). The reviewer's stated reason is the card's own arithmetic in §3
("Code-read expectation, to be confirmed or refuted by measurement, not assumed").

The verdict is decided by the §7 wording alone, applied in the stated order to the measured `D` and
`S(g)`; agreement of the two predictions carries no weight in that decision.
