# Local HMASD navigation overlay

`wrapper.py` exposes the capability environment, while `starcraft2.py` owns the StarCraft II
controller lifecycle, reset/restart behavior, action stepping, and observation/state production.
The wrapper is reached through `SMACv2_modified.py` or `SMACv2.py`. This additive file documents
the fixed snapshot only; upstream source is read-only and no prior navigation file existed.
