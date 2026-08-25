# GPT-5.6 Pro R38/R39 Disposition

Date: 2026-07-15

Source model: GPT-5.6 Pro (`Pro` web conversation)

Reviewed question commit: `ffa18c3`

Controller implementation correction: `aaba845`

## Verdict

- **Accept** the corrected response's withdrawal of ordinary recurrent MAPPO as
  an S7 prerequisite. R35--R38 are valid benchmark-access failures and do not
  make HMASD temporal decoupling fail.
- **Accept** the causal structure of returning to S7 with a current fixed-`k`
  HMASD positive anchor and a same-substrate per-agent KEEP/SET treatment.
- **Modify and block** the proposed direct R39 launch. The response assumes a
  compatible final HMASD checkpoint and an exact R30 warm start; neither exists.
- **Reject** partial loading of the historical checkpoint and reject use of the
  standalone `ha_ctse_process` R30 model as the matched treatment. Either choice
  would change the environment interface, high network, critic, optimizer,
  semantic loop, and trainer together with the temporal mechanism.

The initial response and its correction are one review sequence. The correction
supersedes the initial ordinary-MAPPO proposal; they are not two independent
votes.

## Repository Findings

The useful historical run contains only `best_model.pt` saved at 1.760M steps,
where its old final-episode coverage metric was `0.9250`. Training later stopped
at 2.112M steps, but no 2.112M checkpoint was written. The reported `0.9639` is
the mean of the last three evaluation points, not the checkpoint's score and not
R39's proposed primitive-step `C_mean` or `C_full`.

That checkpoint belongs to the former six-agent, three-action S7 interface. The
current S7 preset is an eight-agent, four-action interface-v3 environment. The
checkpoint also lacks the current `policy_interface` and `training_interface`
metadata and depends on a removed configuration class. Current loading correctly
rejects it. `strict=False` cannot turn this into an exact warm start.

The existing `FixedClockAREditPolicy` is also not a wrapper around HMASD's
Transformer `SkillCoordinator`: it has a different MLP input, value function,
optimizer, checkpoint schema, and training loop. Its `force_refresh_every_check`
mode emits R30 SET tokens; it does not execute the original HMASD joint policy.

## Accepted Immediate Correction

Standard HMASD PPO previously evaluated a stored joint skill action while
conditioning individual logits on newly sampled team and prefix skills. Commit
`aaba845` changes `SkillCoordinator.evaluate_training_batch` to teacher-force
the stored `Z,z_{<i}`. This closes a real probability-contract defect needed by
both the future fixed control and treatment; it does not itself authorize R39.

## Required R39 Preconditions

1. With explicit user authorization, first produce or locate a positive
   current-interface fixed-`k` HMASD checkpoint. No such checkpoint is currently
   registered.
2. Keep both experimental arms in the original `hmasd` trainer and collector.
   They must share the coordinator, discoverer, critics, `q_D/q_d`, normalizers,
   optimizer-update order, environment, and checkpoint schema.
3. Define the lifetime of team skill `Z`, the exact partial-roster probability,
   the KEEP/SET initialization, the high-level credit boundary, and the
   recurrent-state behavior before implementing the treatment.
4. `full_refresh_compat` must directly execute the original full-refresh path.
   It cannot approximate that path through the standalone R30 network.
5. Preserve the environment-agnostic intrinsic-reward contract. R39 may not add
   S7-specific intrinsic signals, reward shaping, task predicates, or a new
   latent/classifier route.

Until these preconditions close, R39 has no valid experiment contract and no
scientific outcome branch. The next external question is limited to correcting
the source-anchor and native HMASD partial-roster design; it does not reopen the
retired toy environments or intrinsic-reward families.
