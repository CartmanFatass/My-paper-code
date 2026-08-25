# External Pro Open Question

CURRENT_REVIEW_ASSIGNMENT
repository=CartmanFatass/My-paper-code
branch=aggressive
round=20260729_g31_reusable_nn_rl_base_maintenance_alignment
stage_commit=ebf2db1d05645c66055e259f8927ecfacddc0f2f
question=docs/external-review/rounds/20260729_g31_reusable_nn_rl_base_maintenance_alignment/20_PRO_OPEN_QUESTION.md
instruction=Ignore earlier rounds and refs. Read only this question and its listed evidence from stage_commit.

This is one focused zero-compute maintenance alignment adjudication. Do not redesign
the algorithm, introduce a new model/loss/reward/optimizer, run any experiment,
perform formal or nonformal compute, interpret the portfolio, or advance an
iteration. Read only the allow-listed files and the exact initialize_weights
call-site excerpts named below.

Does commit `ebf2db1d05645c66055e259f8927ecfacddc0f2f` remain aligned with the
existing reusable NN initialization contract when it:

1. applies `last_layer_gain` to a directly passed `nn.Linear`, matching the helper
   documentation and active call sites that explicitly pass `0.01` for the
   code/term/skill/duration/value/ar_context heads; and
2. actually orthogonally initializes explicitly passed `nn.Embedding` modules
   while preserving the `padding_idx` row as exact zero,

despite both operations having been ineffective in the previous implementation?

Treat the vectorized, arbitrary-dimension, max-shifted sparsemax and removal of
`.data` writes as mathematical/correctness repairs. Decide only whether the
Linear/Embedding initialization corrections should remain or be restricted to
preserving the prior effective initialization behavior.

Allow-list:
- `hmasd/networks.py`
- `tests/hmasd_network_foundation_test.py`
- read-only exact `initialize_weights` call-site excerpts from `hmasd/ha_ctse.py`

Return exactly one token:

`MAINTENANCE_ALIGNMENT_DISPOSITION=ALIGNED_INITIALIZATION_CONTRACT_CORRECTION`

or

`MAINTENANCE_ALIGNMENT_DISPOSITION=RESTRICT_TO_PRIOR_EFFECTIVE_INITIALIZATION`

If and only if the second token is selected, name the exact conflicting
initialization field or call-site contract; do not propose a new architecture.
