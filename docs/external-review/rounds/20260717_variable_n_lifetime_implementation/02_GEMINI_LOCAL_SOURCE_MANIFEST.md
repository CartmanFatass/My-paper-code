# Gemini Local Source Manifest

access_mode: local_read_only_allowlist

Gemini must read the shared manifest and may additionally inspect only these
local sources. Do not edit files, install dependencies, run training or browse
the web.

## Original papers to revisit only where the plan depends on them

- `docs/research/literature/n_k_many_agent_deep_dive/papers/P01_ACE_AAMAS2023.pdf`
- `docs/research/literature/n_k_many_agent_deep_dive/papers/P02_ACAC_ICML2025.pdf`
- `docs/research/literature/n_k_many_agent_deep_dive/papers/P03_InforMARL_ICML2023.pdf`
- `docs/research/literature/n_k_many_agent_deep_dive/papers/P04_Sable_ICML2025.pdf`

The previous round already audited all eight papers. Do not reread unrelated
PDFs merely to enlarge context. Revisit the four above only for claims about
asynchronous action ownership, physical-time discount/event-depth trace,
active-set invariant aggregation and many-agent recurrent storage. Cite the
local PDF page or section for any claim that changes your plan verdict.

## Original HMASD and OPT source archives

- `ref/hmasd.tar`
  - `hmasd/algorithms/mat/algorithm/ma_transformer.py`
  - `hmasd/algorithms/mat/algorithm/transformer_policy.py`
  - `hmasd/utils/h_shared_buffer.py`
  - `hmasd/utils/l_shared_buffer.py`
  - `hmasd/runner/shared/base_runner.py`
- `ref/OPT-main.zip`
  - `OPT-main/src/controllers/entity_controller.py`
  - `OPT-main/src/controllers/token_controller.py`

Inspect these members only to test whether the plan preserves the intended
skill-conditioned low actor and autoregressive cooperative function or wrongly
copies fixed-roster assumptions. They are references, not code to transplant.
