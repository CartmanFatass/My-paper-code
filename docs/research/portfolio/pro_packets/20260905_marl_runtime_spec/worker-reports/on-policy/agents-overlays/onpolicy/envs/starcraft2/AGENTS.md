# Local HMASD navigation overlay

`StarCraft2_Env.py` is the SMAC adapter used by `train_smac.py`; each environment instance starts
and controls a StarCraft II process through pysc2. `SMACv2.py` and `SMACv2_modified.py` adapt the
SMAC v2 wrappers and expose per-agent spaces and available actions. The nested `StarCraft2v2/`
directory contains the capability wrapper and underlying controller. This is local navigation for
the fixed snapshot; do not edit the upstream Python implementation during the survey.
