# Q-learning utility navigation

`fast_attention.py` is a specialized attention implementation used by transformer Q-learning
variants. Its recurrent attention paths use JAX `lax.scan`; inspect sequence length and `unroll`
before attributing cost to the environment.

Keep key threading and dtype casts intact. Python permutation/formatting code in this utility is
outside the compiled steady-state path unless called from a traced function. No dependency install,
training, or benchmark was performed.
