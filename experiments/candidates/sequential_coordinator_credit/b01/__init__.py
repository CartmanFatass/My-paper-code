"""sequential_coordinator_credit B01: chain_bandit first cell at K = 4 (NumPy only).

Modules: ``chain_bandit`` (host, exact enumeration), ``estimators`` (E1, E3, E4, E3*, E4*,
Shapley readings), ``learner`` (tabular joint-PPO coordinator), ``readings`` (exact gradient
readings at snapshots), ``calibration`` (host-matched sweep), ``first_cell`` (orchestration).
Entry: ``scripts/run_sequential_coordinator_credit_b01.py {calibrate | first-cell}``.
"""
