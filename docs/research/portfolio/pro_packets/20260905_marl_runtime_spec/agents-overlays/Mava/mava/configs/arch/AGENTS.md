# `mava/configs/arch/` navigation overlay

`anakin.yaml` and `sebulba.yaml` select distinct execution contracts.

Anakin `num_envs` is per device and evaluation is device-parallel. Sebulba `num_envs` is per
actor thread; actor/learner device ids, thread count, and bounded rollout queue define the host
pipeline. Keep this distinction explicit in performance comparisons.
