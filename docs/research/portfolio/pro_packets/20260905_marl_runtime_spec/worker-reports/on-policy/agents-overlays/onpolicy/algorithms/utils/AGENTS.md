# Local HMASD navigation overlay

`util.py:check` wraps NumPy arrays with `torch.from_numpy`; actor/critic modules then call
`.to(dtype, device)`. `rnn.py` handles flattened `(T*N, feature)` sequences and reset-mask
boundaries. `mlp.py`, `cnn.py`, and `act.py` define feature extraction and action distributions.
This local navigation file does not change the fixed upstream implementation.
