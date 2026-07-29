# The full-sync arm can hand a duty straight back — verified against source

Pro's ruling on the R4 formal result rests on two claims about the
implementation. Both are load-bearing: if either were wrong, the instrument
verdict would not follow. Both are **confirmed**, and both are sharper than Pro
stated them.

Verified at `d7c0d52e` against `scripts/audit_d7_s_event_aligned.py`.

## Claim 1 — `full_sync_SET` does not exclude the incumbent. CONFIRMED.

`full_sync_set_update` (`scripts/audit_d7_s_event_aligned.py:941`) has exactly
two parameters:

```python
def full_sync_set_update(*, duty_positions: dict[int, np.ndarray],
                          airborne_positions: dict[int, np.ndarray]) -> dict[int, int]:
```

No incumbent map is passed in, so none can be excluded. The body walks duties in
ascending id and takes `min(remaining, key=distance to duty d)`, deleting each
chosen UAV from `remaining`. There is no constraint of any kind relating the new
assignment to the old one.

The docstring at `:2394` says the schedule "never preserves any incumbent, locked
or not." That is false as written. What the code guarantees is that no incumbent
is *protected*; it does not prevent an incumbent from being *reselected*.

**The sharpening: retention is not merely possible, it is the geometrically
favoured outcome.** `scripted_source_actions` flies each assigned UAV toward its
own duty's live target. A UAV that has been servicing duty `d` is therefore
converging on `d` and is, in the ordinary case, the airborne UAV *nearest* to
`d` — which is precisely the one greedy nearest-assignment selects. So the
control's expected behaviour is to reproduce much of the incumbent map, not to
disturb it.

`[INFERENCE]` This is the mechanism that would make `D_A ≈ 0` for a reason that
has nothing to do with persistence being unnecessary: an arm that mostly returns
the map it was given is close to a no-op, and comparing a near-no-op against
`constructive_mixed` measures almost nothing. This is stated as inference, not
measurement — the retention rate was never recorded, which is the whole defect.

> **Correction, after Pro's R5 ruling.** "Geometrically favoured" is **plausible
> but not established**, and this note leaned on it too hard. Reasons it need not
> hold: service centroids move with users; a LEAVE/REJOIN may have just rematched
> incumbents; another UAV can be nearer after motion; an airborne UAV may be
> travelling to a charging station rather than its duty; nearest-duty geometry can
> change between checks. No retention data were serialized, so this explanation of
> `D_A ≈ 0` is unmeasured and stays unmeasured.
>
> **The finding does not depend on it.** The durable reason R4 is non-identifying
> is that retention was *neither prohibited nor recorded* — which holds whether
> retention was frequent or rare. Appended rather than substituted, so the record
> shows the claim and what it became.
> Ruling: `docs/external-review/rounds/20260729_d7_s_r5_derangement_control/21_PRO_OPEN_RAW.md`.

## Claim 2 — the recomputed map is applied one step late. CONFIRMED, and it is not confined to step 0.

`step_once` (`:2485`) in execution order:

```text
:2494  actions = scripted_source_actions(..., duty_map=duty_map, ...)   <- INCOMING map
:2507  step_return = env.step(actions)
:2510  new_map, ... = update_duty_map_on_transitions(..., step_index=step_index)
```

Actions are synthesized and executed from the incoming map, and the duty map is
updated only afterwards.

**The sharpening: Pro described this at `step_index=0`; it is a uniform one-step
lag at every check boundary.** `update_duty_map_on_transitions` recomputes when
`int(step_index) % int(DELTA) == 0` (`:2413`) and otherwise carries the map
forward. Because the recomputation happens after that step's action has already
been executed, the newly recomputed map governs steps `1..DELTA` of the window
rather than `0..DELTA-1`. Every check is shifted, not just the first.

This does not by itself explain the equivalence — Pro's judgement, and nothing
here contradicts it. It does mean the executed arm is not an exact realization of
"reassign every active commitment at the check boundary."

## What this does and does not change

Unchanged: the branch, the numbers, the bit-exact re-derivations, the sentinel,
and `MATERIALITY_MARGIN = 5.0`.

Changed: the docstring at `:2394` is a false statement about the code and is the
proximate reason the gap survived review. Every adversarial pass over this
instrument read that line and had no way to falsify it, because the exposure it
asserts was never measured anywhere in the artifact.

**The general lesson, which is the part worth keeping.** A comparator's claim
about itself is not a gate. `conformance.ok` checked that `constructive_mixed`
rematched a vacancy — a real check on the arm that did not need one — while the
arm whose semantics carried `D_A` was certified by a comment. A control must
report the exposure it claims to create, or it is asserting its own validity.

## The exposure quantities the successor control must record

Pre-registered here so the successor cannot pass on an assertion again:
incumbent-retention count, assignment Hamming distance, per-agent target
displacement, action-vector divergence from `constructive_mixed`, and realized
assignment run lengths. The exposure predicate is exact — zero retained eligible
incumbents — and an infeasible derangement is an explicit instrument failure,
never a silent accept.

The R4 artifact records none of these, so the retention rate on run
`30403322062` cannot be recovered from it. Measuring it needs a re-run on the
observed topologies, which Pro permits only as a labelled conditional
diagnostic — never pooled with a successor's confirmatory population.
