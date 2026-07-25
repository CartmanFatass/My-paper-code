# UAV charge-rotation roster G2 formal result

Date: 2026-07-25

```text
scientific_source_commit=8350263ef73b15f10b6d2bcac2583687aad7cade
run=logs/formal_uav_charge_rotation_g2_cpu_20260724_8350263_r1
formal=true
conclusion_bearing=true
operational_valid=true
result=SOURCE_NON_IDENTIFIABLE_UAV_CHARGE_ROTATION_G2
iteration=23
iterations_remaining=4
```

## Evidence closure

The frozen validator accepts the complete formal artifact set. The source
screen contains 2,304 committed rows: three replicates, three registered energy
profiles, two controls and 128 episodes. Runtime identity is CPU-only PyTorch
2.7.0 with one torch thread. Same-root continuation preserved the source,
authorization token, seeds, budgets and committed-row identity.

The source predicates are:

```text
constructive_feasibility_pass=false
load_bearing_pass=true
support_pass=false
source_identifiable=false
```

Constructive `Phi` means and CI95 intervals are:

```text
IID=[0.21189212024563056,0.24667093068618562,0.27980500970999295]
LOW_ENERGY=[0.0500493398089602,0.09826835335168371,0.1419985424821098]
SYNCHRONIZED_PRESSURE=[0.07482772467663794,0.11206333402768569,0.14769697863033243]
```

All means are below the frozen `0.90` feasibility floor. The corresponding
constructive-minus-no-rotation lower bounds are `0.7910515`, `0.9083408` and
`0.8333915`, so proactive rotation is load-bearing but the registered
constructive policy is not a feasible service controller. Eleven constructive
cutoff events and eight constructive depletion events also prevent complete
support.

The training manifest is `TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE`; it contains
zero training results and zero checkpoint references. Evaluation is complete
and operationally valid with no learned rows. The analyzer sets
`learned_gates_evaluated=false`. Frozen first-match recomputation selects
`SOURCE_NON_IDENTIFIABLE_UAV_CHARGE_ROTATION_G2` before every learned branch.

## Scientific disposition

Close the exact G2 source without rerun, threshold/budget/seed changes,
controller enhancement or learned-arm rescue. The result says that rotation is
important relative to no rotation but that this source/controller pair cannot
identify a learned lifecycle advantage. It is not negative evidence about G31,
FIXED_MASK_REC or PREFIX_NORMALIZED_OPEN_ROSTER because no learned model was
initialized.

Both promoted UAV sources have now closed at source-first pruning. The next
boundary returns to toy-first algorithm discovery and separates within-capacity
active-count support from same-checkpoint transport across configured maximum
capacities: `CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32_DERIVATION`.
