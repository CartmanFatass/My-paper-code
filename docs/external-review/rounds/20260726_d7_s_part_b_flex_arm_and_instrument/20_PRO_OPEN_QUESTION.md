# D7.S part B: the number is decisive and the gate still cannot fire

You ordered the main-scenario persistence audit (D7.S) with constructive
controls and the frozen margins `U*_stable,src / B_H <= -0.10`,
`U*_flex,src / B_H >= +0.10`. Part A settled structurally: full-sync role
permutation preserves none of return-relevant state, so the toy failure does
not transfer. Part B is now measured at the episode budget the intervals
demanded — **64 episodes at H=1500, stage S3, topology-seed 20260725** — and
the result is sharp in one half and structurally void in the other. Four
coupled questions below are yours; none of them is answerable by more compute.

## A. What 64 episodes established

All eight shards ran to completion on one pinned topology; the first four
episodes reproduce the 2026-07-25 four-episode run's `arm_means` exactly
across days and process layouts (the ep4 JSON predates the per-episode echo,
so artifact-level verification is at arm-mean, not per-episode, resolution);
energy binds in every arm (`charge_steps` 480–822, `dock_events` 6–30).

```text
B_H          +65.965    CI95 [+29.073, +103.515]   excludes zero
U*_stable    -40.602    CI95 [-76.111,  -4.736]    excludes zero
norm_stable  -0.6155    against the -0.10 ceiling  (point; clears ~6x)
U*_flex       -9.528    norm_flex -0.144           against the +0.10 floor: FAILS
branch       SOURCE_NECESSITY_UNRESOLVED
required n for B_H to exclude zero, back-solved from per-episode: 21
```

The stable half sharpened from `-0.147` (four episodes, no interval) to
`-0.616`, and the un-normalized margin's interval excludes zero. **But at 95%
the diagnostic intervals do not establish threshold clearance:** the
normalized-stable interval reaches `-0.0566`, above the `-0.10` ceiling, and
`u_star_stable`'s upper end `-4.736` is above `-0.10·B_H = -6.596`. "Excludes
zero" is true and is not the gate's proposition. The gate as you froze it is a
point condition and the point clears ~6x; whether a close may rest on that
point while its own diagnostic interval reaches `-0.057` is asked explicitly
in Q1.3 and Q6.

The flex half **flipped sign**: `+0.152` at four episodes, `-0.144` at 64.
That four-episode clearance — the number that made the ep4 run fire
`PERSISTENCE_NECESSARY_SOURCE` — was noise on an arm that cannot carry its
estimand (§B). The gate as frozen can therefore never legitimately fire on
this instrument, at any budget.

## B. The four defects, all frozen-design-level, none mine to correct

**B1 — `set_flex` is definitionally `constructive`.** The frozen design
(`D7_S_MAIN_SCENARIO_PERSISTENCE_NECESSITY.md:215`) defines it as "that
service UAV re-decides each check", which is what `constructive` already does
for every UAV. No `set_flex` branch exists in the audit code (grep-confirmed),
and the runs prove it: `set_flex == constructive` per episode, exactly, at all
64 episodes. So `U*_flex = constructive - keep_flex` while
`B_H = constructive - null` — treatment and normalizer share a term, which D0
forbids outright (`D0_CARRIER_AND_ESTIMAND.md:248-250`: `B_H` "is never
estimated from the treatment outcome"). There is also an asymmetry you have
not yet ruled on: `set_stable` is a *forced exchange* while any repaired
`set_flex` would be a *forced re-decision*, yet both are judged on symmetric
±0.10 thresholds. One registration fact matters for who may repair this: the
Part B freeze (design §114–197) defines the controllers abstractly and never
enumerates a six-arm table; the quoted `set_flex` sentence sits at line 215
inside the **superseded S1 results table**, and the arm realization otherwise
lives only in `audit_d7_s_persistence_margin.py:196-208`. Q1 therefore also
asks you to rule the arm table's registration status explicitly — whether a
repair renegotiates a freeze or fixes an unfrozen realization.

Two further realization facts no prior round has put in front of you: the
realized instrument can emit only two of the three registered branches —
`ZERO_COST_ROLE_EXCHANGE_SOURCE` is unreachable in code (no arm reassigns
every duty per check), justified so far only by part A's structural ruling —
confirm or order otherwise.

**B2 — Δ mismatch.** D0 freezes `Δ` = one check interval
(`D0_CARRIER_AND_ESTIMAND.md:198`). The realized keep arms freeze the focal
duty for the **whole window** — at H=1500 that is 150 check intervals. The
audit measures "hold for H" vs "exchange once", not "hold for Δ". This applies
identically to every prior sweep point; it is a realization-of-estimand
question, not a new defect in this run.

**B3 — horizon structure.** Your per-mechanism `H` rule
(`D0_CARRIER_AND_ESTIMAND.md:211`) gives this source two windows: exchange
~139 steps, energy ~1500 (time-to-first-dock ~1071 dominates the ~403 s
charge). The data now says: at H=139 and H=450, `B_H` is statistically
indistinguishable from zero at four episodes (H=450 CI: −26.6..+46.9; the
back-solve projects ~52 episodes for its interval to exclude zero — a normal
approximation from a 4-episode point, a projection rather than a
measurement). Note the cost honestly: 52 episodes at H=450 is roughly a
quarter of the arm-steps of the ep64 H=1500 run just paid. At H=1500, margin
and normalizer are **both** well behaved for the first time. Renewal value
appears to live on the energy window here.

**B4 — topology is drawn at construction, ignoring every seed.**
`ground_bs_positions` and `charging_station_positions` are drawn from
`np_random` at construction (`scenario_base.py:650-666`,
`scenario7_energy_aware.py:313`) and `reset(seed=)` never regenerates them.
The audit pins them via `--topology-seed 20260725`; the ep64 claim is
therefore a **single-topology** claim. The defect is wider than this audit
and has not been assessed for other experiments in the repository.

Two instrument caveats measured this run: (i) the saturation probe returned
1.0 at 7 of 8 shard probe seeds (0.667 at one) — yet the arms separated
decisively, and the return in use is the *unclipped* form precisely because
the clipped one saturated; the probe may be measuring the retired instrument.
(ii) `ratio_sign_stable = false` on the normalized-stable interval: `B_H`'s
own CI excludes zero, but far-tail bootstrap resamples flip the denominator's
sign, so the *ratio* interval is diagnostic-only. The gate stays on point
estimates as you froze it; nothing here changes that without your ruling.

## Q1 — the `set_flex` arm: repair, drop, or re-scope?

**If (a) repair:** specify the replacement realization exactly. What must a
forced re-decision of the flexible duty *do beyond what `constructive` already
does* — forced reassignment to the next-best target? focal re-decision under
frozen non-focal duties? something else? Then also answer:
**Q1.1** does the repaired arm keep CRN pairing and fresh-env-per-arm
unchanged; **Q1.2** do the symmetric ±0.10 thresholds survive the
forced-exchange vs forced-re-decision asymmetry, or do the two halves need
separately justified thresholds?

**If (b) drop the flex half** and gate on the stable margin alone: state what
claim a stable-only gate licenses — "persistence of the stable duty is
necessary" is weaker than "persistence is necessary on this source". Then
answer **Q1.3**: does the ep64 stable result, under that re-scoped gate, close
part B's branch as `PERSISTENCE_NECESSARY_SOURCE` at the re-scoped meaning, or
does a re-registered gate require a fresh run even though the arms and numbers
would be identical?

**If (c) retire the two-sided gate for this source class**, name the successor
estimand.

**Q1.4 — the realized history class.** The freeze (design §117–122) requires
stable/flexible to be "determined in the evaluator only, from realized user
motion and link state, never from a role name". The instrument hardcodes
`focal_stable = 0` (a relay) and `focal_flex = n_relay` (first service UAV) —
selection by role index at reset, no evaluator predicate ever evaluated, and
every window starts at reset where no incumbent commitment exists. Rule
whether role-anchored selection on this source is an acceptable realization
of the frozen history class (the relay duty's target is provably static,
design §127–131), or whether the class must be certified per-episode from
realized motion — and if the latter, whether the ep64 record is evidence
about the frozen estimand at all.

**Q1.5 — the SET term is one fixed partner, not `max over z`.** D0 defines
`U*` with `max_{z != z_i}` over joint continuations and requires split-sample
discipline for the selection (`D0_CARRIER_AND_ESTIMAND.md:133-135, 191-194`).
Both SET arms realize a single fixed alternative — `set_stable` is one swap
with the focal-flex UAV specifically, no max, no split-sample. A realized SET
is a lower bound on the maxed SET term, so `-0.6155` can overstate necessity
if some other substitute exchanges cheaply. Rule whether single-partner
forced exchange realizes the estimand (and a stable-only gate under Q1(b)
may close on it), or whether the SET term must maximize over replacement
duties on a selection sample independent of the evaluation sample. Note the
project record currently classifies the stable arm "sound" — that
classification was mine and is exactly what this question submits to you.

## Q2 — Δ: is the whole-window hold the estimand, or must the arms hold one Δ?

**If (a) accept and re-register** the realized quantity (hold-for-H vs
exchange-once) as the persistence margin: say so explicitly so D0 and the
design stop disagreeing with the code.
**If (b) the arms must hold exactly one Δ** then resume constructive: rule
whether the ep64 evidence retains any standing (my reading: none of the margin
numbers survive, only the reproducibility and energy-window facts), and
whether the repaired arms re-run at 64 episodes or at a budget you set from
the recorded per-episode variance.

**Q2.3 — the `B_H` window realization.** The design freeze says `B_H` is
"averaged over windows starting at check boundaries — **never** from a
step-0 window" (design §183–185). The instrument realizes one window per
episode starting at reset step 0 (`audit_d7_s_persistence_margin.py:273,317`),
never averaged over later check-boundary starts; at H=1500 the episode admits
no other full window. `B_H` is the denominator of both gated margins. Rule
whether the whole-episode step-0 window is the frozen quantity here, or
whether `B_H` must be recomputed on later-start windows — and if the latter,
whether any ep64 margin survives. If both Q2(b) and Q2.3 come out adverse,
specify the **joint** re-run once, not one re-run per defect.

## Q3 — horizon: may H=1500 be registered as this source's gate horizon?

**If yes:** the exchange-window margin at H=139 becomes a separately reported
descriptive quantity with a degenerate normalizer, never gated. Confirm.
**If no:** name the alternative — an intermediate-H search (state the
selection rule so it is not post-hoc), or a different normalizer for the
short window (naming it), or **ordering H=450 at ≥52 episodes** (≈¼ of the
ep64 cost; 52 is a projection from a 4-episode point, so state the stopping
rule if the projection proves short), or treating this source as unable to
support the normalized margin at all.

## Q4 — single-topology scope and the wider seed defect

**Q4.1** Is the pinned-topology instrument acceptable for the part B record,
with the claim scoped to topology 20260725? If replication across topologies
is required before any paper-level use: how many topologies, and is the gate
per-topology or on pooled margins?
**Q4.2** The construction-time draw affects the whole repository, unassessed
beyond D7.S. Does anything else need to be audited *before* further claims
are built on existing results, or is it handled per-experiment as each is
touched?

## Q5 — the two instrument caveats

**Q5.1** Saturation probe: the probe is a single reset-state snapshot at the
shard's probe seed, before any arm rolls, measuring `fraction(rate ≥ target)`
— the clipped-form diagnostic, not window-averaged, not on the oracle layout
(`audit_d7_s_persistence_margin.py:475-480`). Given the return in use is
unclipped, is the probe (a) obsolete and retired, (b) to be re-specified
against the unclipped instrument, or (c) evidence that arm separation at
these probe seeds is suspect despite `B_H`'s interval? If (c), state what
additional measurement would settle it.
**Q5.2** `ratio_sign_stable=false` with a CI-positive `B_H`: confirm the
ratio interval stays diagnostic-only under the frozen point-condition gate,
or order a change (which would be renegotiating a frozen threshold — flagged
as such).

## Q6 — smallest supported claim, and D8

As the record stands (before any Q1/Q2 repair): what is the smallest claim
part B supports for publication? My inference, marked as inference: "on this
source and topology, forced exchange of the stable duty costs 0.62×B_H at
H=1500, un-normalized CI excluding zero; the flexible-duty half is
unmeasured." In weighing it, note §A's interval facts: the point clears the
ceiling ~6x but the normalized diagnostic interval reaches −0.057 — say
explicitly whether any close or claim may rest on the point condition alone.
Does any branch of your Q1–Q3 rulings unblock `D8`, or does it stay blocked
until a repaired gate closes?

## Q7 — anything above you would reorder

If a later answer changes an earlier one, state the dependency explicitly
rather than leaving it implicit. Known dependencies I am declaring: a
stable-only close under Q1(b)/Q1.3 is **triple-gated** on Q1.4 (history
class), Q1.5 (max-over-z), and the §A interval facts; Q2(b) or an adverse
Q2.3 voids Q1.3 and folds into one joint re-run ruling; Q3's answer scopes
which window any re-run uses.

## Evidence to read

Repository at the stage commit, paths only:

- `docs/research/designs/D7_S_MAIN_SCENARIO_PERSISTENCE_NECESSITY.md` — the
  frozen design; §arm table around line 215.
- `docs/research/designs/D0_CARRIER_AND_ESTIMAND.md` — margins (line ~140),
  `Δ` (line ~198), per-mechanism `H` (line ~211), `B_H` independence
  (lines ~248–250).
- `scripts/audit_d7_s_persistence_margin.py` — the instrument: arms,
  fresh-env-per-arm, topology pinning, unclipped return, saturation probe,
  provenance echo, bootstrap.
- `scripts/pool_d7_s_persistence_shards.py` — loss-free pooling: identity
  assertions, seed tiling, monolithic-equivalent recomputation.
- `logs/nonformal_d7_s_persistence_margin_20260726_ci_h1500_ep64/d7_s_persistence_margin.json`
  — the pooled ep64 result, including `per_episode` and `pooled_from`.
- `logs/nonformal_d7_s_persistence_margin_20260726_ci_h1500_ep64_shard0/d7_s_persistence_margin.json`
  — one shard, for the provenance echo and shard-level structure.
- `logs/nonformal_d7_s_persistence_margin_20260725_g2_s3_repro_h1500/d7_s_persistence_margin.json`
  — the ep4 point the ep64 run reproduces bit-exactly on its first four
  episodes.
- `logs/nonformal_d7_s_persistence_margin_20260726_ci_h139_ep4/d7_s_persistence_margin.json`
  and `logs/nonformal_d7_s_persistence_margin_20260726_ci_h450_ep4/d7_s_persistence_margin.json`
  — the short-horizon `B_H` degeneracy with intervals. These two predate the
  provenance echo and carry no `seed`/`topology_seed` fields; their topology
  identity rests on this chain: their `arm_means` equal the 2026-07-25 repro
  runs' exactly, and those ran at `--topology-seed 20260725`.
- `logs/nonformal_d7_s_persistence_margin_20260725_g2_s3_repro_h139/d7_s_persistence_margin.json`
  and `logs/nonformal_d7_s_persistence_margin_20260725_g2_s3_repro_h450/d7_s_persistence_margin.json`
  — the chain's anchor points.
- `docs/research/designs/UAV_CHARGE_ROTATION_ROSTER_G2.md` — the registration
  source of H=1500, stage S7-S3 and the energy multiset the run applied
  (bears on Q3).
- `docs/project/ALGORITHM_PRINCIPLES.md` and
  `docs/external-review/OPEN_REVIEW_PRINCIPLES.md` — standing context the
  transport contract requires in every round.
- `envs/pettingzoo/scenario_base.py` (lines ~650–666) and
  `envs/pettingzoo/scenario7_energy_aware.py` (line ~313) — the
  construction-time topology draw.
- `tests/audit_d7_s_persistence_margin_test.py` and
  `tests/pool_d7_s_persistence_shards_test.py` — the pinned `set_flex`
  degeneracy test and the pooling contract.
