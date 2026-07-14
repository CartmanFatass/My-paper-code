# GPT-5.6 Pro Sparse-Exploration Review Entry

Repository: `CartmanFatass/My-paper-code` (private)

Branch: `aggressive`

Review target: the exact commit supplied by the user that contains this file.

Historical Alice--Bob run commit:
`cbf504729ac4e14f8195bd0c7714e73f9e667474`.

## Read In This Order

1. `QUESTION.md` and `RESULT_SUMMARY.md` in this directory.
2. `r30_alice_bob_shaped_pair.json` in this directory as the raw machine
   summary of the completed 64K paired screen.
3. Existing background, without asking the user to upload it again:
   - `docs/external-review/gpt5_6_pro/20260713_r29_action_information/RESEARCH_BACKGROUND.md`
   - `docs/external-review/gpt5_6_pro/20260714_r30_algorithm_code_review/RESEARCH_BACKGROUND.md`
   - `docs/external-review/gpt5_6_pro/20260714_r30_algorithm_code_review/DISPOSITION.md`
   - `docs/research/R30_FIXED_CLOCK_AR_EDIT_DESIGN_20260714.md`
   - `memory/ALGORITHM_PRINCIPLES.md`
   - `memory/CURRENT_WORK.md`
4. Inspect the current implementation at the review-target commit:
   - `envs/pettingzoo/alice_bob_asymmetric_cycles.py`
   - `ha_ctse_process/config_alice_bob_asymmetric.py`
   - `ha_ctse_process/config_alice_bob_shared_k.py`
   - `ha_ctse_process/intrinsic_rewards.py`
   - `ha_ctse_process/process_posterior.py`
   - `ha_ctse_process/r30_fixed_clock.py`
   - `ha_ctse_process/standalone_agent.py`
   - `ha_ctse_process/train.py`
5. Use the original HMASD implementation only as a paper-grounded reference
   for the discoverer/discriminator/entropy and autoregressive-assignment
   functions:
   - `hmasd/networks.py`
   - `hmasd/agent.py`

Use class and function names rather than trusting historical line numbers.

## Critical Version Boundary

The historical run used an environment progress term:

```text
0.20 * (Phi(s_next) - Phi(s))
```

It is therefore `controller-reward-pure, environment-shaped`. It is not a
sparse-exploration experiment and cannot support an HMASD-parity claim.

At the review-target commit, Alice--Bob has been changed to a genuinely sparse
external reward: the only environment reward is the shared collection event
when different agents simultaneously occupy the active button and active
target. Distance/contact/potential fields do not enter reward or advantage.

The algorithmic transition-skill intrinsic reward remains a separate low-level
signal. The review must keep environment shaping, algorithmic intrinsic reward,
and external task reward distinct.

## Transfer And Return

The GitHub connector is the only package-transfer path for this consultation.
No ZIP, hash, or checksum is needed. Return the answer verbatim; it will be
stored later as `RESPONSE_RAW.md` before controller disposition.
