# Gemini Local Source Manifest

access_mode: local_read_only_allowlist

Gemini must read the shared manifest and may additionally inspect only these
local sources. Do not edit files, install dependencies, run training or browse
the web.

## Original-source anchors

- `ref/hmasd.tar`
  - original Alice--Bob environment and training configuration;
  - original skill-conditioned low actor, high assignment and q_d/q_D reward
    paths needed to distinguish a task reward from an algorithmic intrinsic
    term.
- `docs/research/literature/n_k_many_agent_deep_dive/papers/P01_ACE_AAMAS2023.pdf`
- `docs/research/literature/n_k_many_agent_deep_dive/papers/P02_ACAC_ICML2025.pdf`

Revisit ACE only for independent agent-event execution and ACAC only for
physical-time versus event-depth credit. Neither paper defines this testbed or
authorizes a new module. Cite a PDF page/section only when it changes the
design verdict.

## Source-completeness rule

Before the final divergent answer, explicitly confirm inspection of:

1. the current F0/F1 implementation and focused test;
2. all four retired R51--R54 dispositions and their result JSONs;
3. the original HMASD reward/low-policy boundary in `ref/hmasd.tar`;
4. the two allowlisted paper claims actually relied upon.

Do not inspect unlisted local literature, current-round Pro output or a Codex
synthesis.
