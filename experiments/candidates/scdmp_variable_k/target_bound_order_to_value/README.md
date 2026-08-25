# SCDMP-TBOV r07 Stage A

This package implements only the Pro-closed `SCDMP-TBOV-SCIENCE-20260815-07`
Stage-A selector. It deliberately contains no Stage-B implementation.

The preactivity command performs static checks without sampling a master,
materializing coordinates, evaluating scale atoms, training, or evaluating:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.scdmp_variable_k.target_bound_order_to_value --mode preactivity
```

Production requires a later exact Root lease and explicit result, frontier and
create-only manifest paths. The runner retains a blinded same-coordinate
frontier and will not resume it without `--resume`.
