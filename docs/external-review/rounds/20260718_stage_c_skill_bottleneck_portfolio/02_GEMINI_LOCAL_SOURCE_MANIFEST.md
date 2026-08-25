# Gemini Local Source Manifest

access_mode: local_read_only_allowlist

Gemini reads the shared Git-visible manifest and may additionally inspect only
the local sources below. It must not edit files, install dependencies, run code,
launch training or browse the web.

## Original-source anchors

- `ref/hmasd.tar`
  - original coordinator, skill-conditioned low actor, training order,
    Alice--Bob environment and `q_d/q_D` intrinsic reward boundary;
- `ref/OPT-main.zip`
  - original OPT observation/action compact representation only where it affects
    the current deterministic bridge or bypass risk.

## Allowlisted paper PDFs

- `docs/research/literature/n_k_many_agent_deep_dive/papers/P01_ACE_AAMAS2023.pdf`
- `docs/research/literature/n_k_many_agent_deep_dive/papers/P02_ACAC_ICML2025.pdf`
- `docs/research/literature/n_k_many_agent_deep_dive/papers/P03_InforMARL_ICML2023.pdf`
- `docs/research/literature/n_k_many_agent_deep_dive/papers/P04_Sable_ICML2025.pdf`
- `docs/research/literature/n_k_many_agent_deep_dive/papers/P05_ExpoComm_ICLR2025.pdf`

Use a paper only when a precise mechanism changes a candidate. Cite its page or
section. The literature is for replacement principles, not a module menu.

## Source-completeness rule

Before answering, confirm inspection of the exact Stage C result, the original
HMASD low-policy/intrinsic path, and every local paper claim actually relied on.
Do not inspect current-round Pro output or controller synthesis.
