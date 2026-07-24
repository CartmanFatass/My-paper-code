# Slot-layout invariance G11 formal result

Date: 2026-07-23

The exact source `5713af3d477f10c41cb3f1925a2b920dfdc7dd74`
completed at `logs/formal_slot_layout_g11_cpu_20260723_5713af3_r1`.

```text
formal=true
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_g8_replicates=3
optimizer_steps=0
evaluation_cells=24
utility_values=1536
operational_valid=true
operational_errors=[]
branch=SLOT_LAYOUT_INVARIANT_G11
```

The Project Manager independently closed all three imported checkpoints, all
24 replicate/layout/mode cells and all 1,536 serialized utility values. Source
controls cover four injective mappings, mapped priorities, equal waves, exact
roster schedules, lifecycle freeze/restore and constructive utility one. Every
cell kept the model state bitwise unchanged and every checkpoint copy had
maximum difference zero.

```text
dense48_deterministic_utility_ci95=[0.92529296875,0.9513706931089744,0.9991316105769231]
reverse48_deterministic_utility_ci95=[0.92529296875,0.9513706931089744,0.9991316105769231]
sparse96_deterministic_utility_ci95=[0.92529296875,0.9513706931089744,0.9991316105769231]
affine_padded128_deterministic_utility_ci95=[0.92529296875,0.9513706931089744,0.9991316105769231]
reverse48_paired_outcome_mismatch_count=0
sparse96_paired_outcome_mismatch_count=0
affine_padded128_paired_outcome_mismatch_count=0
layout_min_replicate_mean=0.92529296875
layout_stochastic_mean=0.8969245793269232
```

An independent first-match evaluation reproduced
`SLOT_LAYOUT_INVARIANT_G11`. The exact same persistent, short and utility
outcomes survive reverse keys, odd sparse keys and an affine scatter into
capacity 128. Thus the G8--G10 success does not depend on dense low-numbered
lifecycle slots or nearby padding under the registered logical source.

This does not establish arbitrary key transforms, arbitrary N, arbitrary event
schedules, skill/lifetime competence or comparative advantage. With layout
dependence removed as the nearest structural counterexample, the smallest next
question is zero-training transport above N=40 using the same frozen G8 finals.

```text
next_boundary=ULTRA_SCALE_OPEN_ROSTER_G12_DERIVATION
conclusion_bearing_iteration=12
iterations_remaining_after_run=5
```
