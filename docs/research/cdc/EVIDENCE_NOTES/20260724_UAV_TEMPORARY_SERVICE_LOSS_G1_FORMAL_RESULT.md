# UAV temporary-service-loss G1 formal result

Date: 2026-07-24

```text
scientific_source_commit=2f8e47c16f0563ed1144e370fff787c22508a14d
analysis_execution_repair_commit=a7e8329d2a4429211c7cd2303dafbb75273c10db
run=logs/formal_uav_temp_loss_g1_cpu_20260724_2f8e47c_r1
formal=true
operational_valid=true
result=SOURCE_NON_IDENTIFIABLE_UAV_TEMP_LOSS_G1
iteration=22
iterations_remaining=5
```

## Evidence closure

The frozen validator accepts the complete formal artifact set. The run contains
192 committed source-control chunks and 6,144 paired evaluation rows across
three replicates, four registered cells, two controls, two duplicated action
mode labels and 128 episodes. Source law and exact pairing pass. There are zero
learned training rows, zero optimizer updates and zero checkpoint references.

The source screen reports:

```text
constructive_J_event_CI95=[0.8481144031424884,0.8566158002220255,0.8652400915167487]
constructive_minus_no_reallocation_CI95=[-0.1181600466991233,-0.10589235342821492,-0.092091265773473]
constructive_feasibility_pass=false
disturbed_load_bearing_pass=false
source_law_and_pairing_pass=true
```

The constructive mean is below the frozen `0.90` feasibility floor, and the
load-bearing interval is entirely negative rather than above `0.10`. The
registered first-match function independently reproduces
`SOURCE_NON_IDENTIFIABLE_UAV_TEMP_LOSS_G1` exactly. Learned access, gain and
lifecycle gates were not evaluated.

## Operational repair

The immutable source screen required three foreground tool windows because the
192 heavy UAV chunks exceeded the two-hour tool-call limit. Each continuation
used the same source, run root, token and runner-validated chunk identity; no
episode was added or relabelled.

After train and evaluation closed, a fresh analyzer process initially rejected
the evaluation identity because it reconstructed runtime identity before
setting Torch to one thread. Commit `a7e8329d2a4429211c7cd2303dafbb75273c10db`
adds the existing runtime initializer to analyzer and validator entrypoints.
A focused fresh-process regression fails before and passes after the repair.
No estimator, bootstrap, threshold, branch or stored evidence changed. Terminal
train/evaluate replay wrote no environment chunks, and the repaired analyzer
then closed successfully.

## Scientific disposition

Close this exact temporary-service-loss G1 source without rerun, tuning,
renaming or rescue. It cannot identify a learned lifecycle advantage because
the registered constructive control is both infeasible and worse than the
no-reallocation control. This is not negative evidence about G31: the learner
was never initialized. Formal G31 remains a usable paired-toy algorithm.

The valid non-`INVALID` G1 terminal satisfies the admission prerequisite for
the independently frozen UAV charge-rotation G2 source. The next boundary is
`UAV_CHARGE_ROTATION_ROSTER_G2_EXECUTABLE_REALIZATION`; it must retain its own
source-first pruning and may not reuse G1 as positive transport evidence.
