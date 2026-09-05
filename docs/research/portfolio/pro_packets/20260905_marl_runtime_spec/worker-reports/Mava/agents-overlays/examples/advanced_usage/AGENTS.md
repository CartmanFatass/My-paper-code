# `examples/advanced_usage/` navigation overlay

`ff_ippo_store_experience.py` mirrors Anakin FF-IPPO and optionally reshapes
`(D,NU,UB,T,NE,...)` to a Flashbax flat buffer. It is useful evidence for explicit rollout
storage, but vault writing and optional buffer instrumentation add work outside the core training
loop. Keep those side effects separate from a core throughput measurement.


