# `benchmarl/models/` overlay

`common.py:50-163` defines the TensorDict model contract. Models are instantiated per agent group,
receive input/output specs and a device, and must write one declared output key. Agent dimensions
depend on `input_has_agent_dim`, `centralised` and `share_params`; a centralized parameter-shared
model can intentionally omit the output agent dimension. Treat the spec checks and group shape as
the semantic boundary.

The MLP path concatenates and flattens trailing feature dimensions, then uses TorchRL
`MultiAgentMLP` or one module per agent (`mlp.py:55-84`, `124-154`). GRU/LSTM paths unbind their
time dimension in Python, use `torch.vmap` for some multi-agent cases, and expose an opt-in
`torch.compile(..., mode="reduce-overhead")` wrapper (`lstm.py:57-96`, `241-280`; `gru.py:57-96`).
The default YAML sets `compile: False`; compilation has no measured speedup in this packet and can
alter warm-up/shape behavior.

The GNN path turns all leading batch dimensions into a PyG graph batch, repeats edge indices for
each graph, and optionally builds radius edges and Cartesian/distance features
(`gnn.py:269-371`, `411-461`). This is Python glue around external PyG/native kernels, not a
BenchMARL C++ implementation. C++ or CUDA code in an external dependency is not evidence that
the end-to-end MARL runner is efficient; measure the complete collection, transfer, model and
logging path.

