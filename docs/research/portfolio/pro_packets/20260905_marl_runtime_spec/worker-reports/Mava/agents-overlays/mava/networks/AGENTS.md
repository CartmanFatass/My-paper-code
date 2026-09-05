# `mava/networks/` navigation overlay

Network modules consume the observation contracts assembled by `mava/wrappers/`.

## Navigation and boundary

`base.py` defines feed-forward actor/value/Q networks and `ScannedRNN`; recurrent modules use
time-major scans and reset hidden state from done flags. `sable_network.py` and its helpers add
agent chunking/retention behavior. Preserve agent axis, observation/global-state selection,
action masks, recurrent carry shape, and key use. Network batching is compatible with outer JAX
transforms but does not itself establish a benchmark result.
