# Gemini Local Source Manifest

access_mode: local_read_only_allowlist

Gemini must read the shared brief and all Git-visible sources listed in
`01_SHARED_SOURCE_MANIFEST.md`. It may additionally inspect only the local
sources below. Do not edit, install dependencies, run training or browse the
web. Read-only PDF extraction and read-only archive member inspection are
allowed.

## Original papers

- `docs/research/literature/n_k_many_agent_deep_dive/papers/P01_ACE_AAMAS2023.pdf`
- `docs/research/literature/n_k_many_agent_deep_dive/papers/P02_ACAC_ICML2025.pdf`
- `docs/research/literature/n_k_many_agent_deep_dive/papers/P03_InforMARL_ICML2023.pdf`
- `docs/research/literature/n_k_many_agent_deep_dive/papers/P04_Sable_ICML2025.pdf`
- `docs/research/literature/n_k_many_agent_deep_dive/papers/P05_ExpoComm_ICLR2025.pdf`
- `docs/research/literature/n_k_many_agent_deep_dive/papers/P06_SafeM3UCRL_AAMAS2024.pdf`
- `docs/research/literature/n_k_many_agent_deep_dive/papers/P07_CTMARL_ICLR2026.pdf`
- `docs/research/literature/n_k_many_agent_deep_dive/papers/P08_IARO_ICLR2026.pdf`

Read all eight local paper analyses. Consult the original PDFs for the method,
assumptions and limitations that materially support your claims. Cite the local
PDF path and page or section whenever an original paper changes your judgment.

## Original HMASD and OPT source archives

- `ref/hmasd.tar`
  - `hmasd/algorithms/mat/algorithm/ma_transformer.py`
  - `hmasd/algorithms/mat/algorithm/transformer_policy.py`
  - `hmasd/algorithms/discriminator/d_trainer.py`
  - `hmasd/utils/h_shared_buffer.py`
  - `hmasd/utils/l_shared_buffer.py`
  - `hmasd/runner/shared/base_runner.py`
- `ref/OPT-main.zip`
  - `OPT-main/README.md`
  - `OPT-main/src/controllers/entity_controller.py`
  - `OPT-main/src/controllers/token_controller.py`
  - `OPT-main/src/config/algs/entity_opt.yaml`
  - `OPT-main/src/config/algs/token_opt.yaml`

Inspect only those members when checking whether a proposal preserves or
replaces HMASD autoregressive semantics and whether OPT supplies a reusable
representation idea. The archives are references, not modules to copy wholesale.
