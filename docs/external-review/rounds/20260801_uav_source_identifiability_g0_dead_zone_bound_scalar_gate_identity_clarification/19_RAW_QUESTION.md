# UAV G0 dead-zone bound details

Treat `ARRIVAL_SEMANTICS=DEAD_ZONE_BOUND` as fixed. Do not reopen or replace
that choice. The remaining question is to freeze its exact executable bound
and the linked gate identity and counting rules.

The unchanged tracker computes, component-wise,

```text
q = float32((g_xy - p_xy) / (max_speed * time_step))
max_speed=30.0 m/s
time_step=1.0 s
```

and unchanged S7-S1 produces zero horizontal velocity exactly when
`norm(float64(q)) <= 1e-8`. Two scientifically different meter bounds are
therefore mechanically possible:

```text
LITERAL_PHYSICAL_RADIUS:
B = 30.0 * 1.0 * 1e-8 = 3.0e-7 metres

FLOAT32_ROUNDING_EXPANDED:
B = nextafter(
      30.0 * (1e-8 + sqrt(2) * 0.5 * spacing(float32(1e-8))),
      +infinity)
  = 3.0000001884110954e-7 metres
```

The expanded formula is the conservative two-component round-to-nearest bound
for every true displacement whose serialized float32 action falls inside the
S7 dead zone. The literal formula treats `3.0e-7 m` as the scientific inclusion
boundary even though float32 component rounding can map a slightly larger true
displacement into the dead zone. The observed counterexamples fall below both;
choosing between them remains result-sensitive.

Please freeze the exact executable rule for all sources, not only the observed
counterexamples, and also close these linked identity and counting points:

1. Is the authoritative gate for both candidate qualification and `n_gate`
   exactly
   `g_owner = concat(source.geometry.gate(source.event.owner_target), 50.0)`,
   with the candidate-specific dead-zone fixed point only an arrival witness
   and never a replacement target?
2. Is `n_gate[r]` the minimum number of unchanged tracker/S7 transitions from
   reserve `r`'s exact source-owned stage state to the first pre-action state
   satisfying the registered gate bound, with the zero-motion no-op not counted
   as an additional travel step, and
   `latest_departure[r] = event.onset - n_gate[r]`?
3. At the onset row, where the behavioral schedule changes from gate to primary,
   may the validator recompute the unchanged float32 action toward the exact
   owner gate from the serialized pre-action state as the gate fixed-point
   witness, while retaining the actual gate-target transition bytes from the
   preceding row? No environment transition or future source is added by this
   reconstruction.
4. Must qualification fail closed when no row in
   `latest_departure <= t <= event.onset` satisfies the chosen bound, exact
   vertical identity and gate-target dead-zone witness, so an `H+1` fallback
   cannot pass Oracle qualification or enter a conclusion-bearing ranking?

Return the exact chosen bound name, formula and decimal meter value, then state
the gate identity, `n_gate`/latest-departure rule, onset-row witness rule and
unreached behavior. Exact punctuation or a single-line format is not required;
scientific content is. Do not design code, change geometry, controller or
dynamics, authorize runtime, or select a G0 result. Stop after this bounded
clarification.
