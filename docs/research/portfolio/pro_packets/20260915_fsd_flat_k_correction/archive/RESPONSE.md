**Confirm option 1: retain FLAT at `k = 10` within the existing S allocation. The four already purchased FLAT originals may proceed, one per allocated block, using the recorded launch source `dc4dbdfcdb20ca29a47c1187e9ebf6787483d21b`.** This supersedes only my earlier requirement to retain the switch-selected long k; it neither re-decides S nor creates additional exposure. [Card §8][S1]; [prior decision, FLAT/application][S2]; [execution, launch record][S4].

## Reason and comparator meaning

The decisive reason is matching the discoverer actor/critic gradient-truncation law, **not** an inability to run long k. The inspected MAPPO switch sets `k = rollout_length + 1`; `get_discoverer_sampler` explicitly falls back to one full-rollout chunk when no chunk fits. Thus the earlier intake's “not runnable” explanation is incorrect, as its appended correction acknowledges. At H500, the proposed long-k FLAT would use 500-step chunks against the D arms' ten-step chunks. Preserving the stock switch would preserve a reproducible but additionally confounded package comparison. The recorded k-to-update linkage and review favor removing that difference. Neither full-host memory failure nor a numerical speedup has been measured. [Switch][S6]; [sampler][S7]; [intake, appended review][S3].

Keep the implemented `off → mappo → k=10` construction, single constant team/individual skills, disabled high-level collection/training and discriminator training/rewards, and learning actor/critic. Coordinator forward calls still occur; zero coordinator optimizer calls does not mean zero coordinator computation. Leave the switch-computed high-level buffer fields unchanged as documented inert configuration differences. Matching low-level chunking does not establish identical total optimization work or long-k/short-k trajectory/RNG equivalence. This is the explicitly corrected flat recipe, not unmodified switch reproduction. [Runner, `make_config`, `FLAT_K`, `PLANNED_CONFIG_DIFFERENCES`][S5]; [card §§2/8][S1].

`GAP_D = J15(D1280) − J15(FLAT_k10)` and `GAP_I = J15(I1280) − J15(FLAT_k10)` retain their arithmetic and no MEI, now with the corrected comparator. Their eventual values may differ from a hypothetical long-k comparison. They remain **untuned cross-information package gaps, not §11.7 headroom**. Hierarchical skills still carry central information absent from FLAT's execution input; matched truncation does not identify pure hierarchy/duration value or tuned baseline competence. Preserve the prior decision's narrower labels, not the request's residual “headroom record” wording. [Prior decision][S2]; [specification §§11.7/11.11][S8].

## Unaffected work and finite application

**The D1280/I1280 work and rollout-15 SI1280 primary are unaffected.** Neither operand uses FLAT. Do not stop, restart, reconfigure or repeat those originals for this correction. The .05 J importance reading, separate uncertainty reporting, four blocks, fifteen rollouts, three 32-world H500 panels and qualified four-new-plus-two-historical rollout-5 accumulation all remain unchanged. No completed factorial result is rescored. [Prior decision][S2]; [intake/execution][S3][S4].

The next action is the four remaining FLAT originals—not a k sweep, ablation or pilot. Retain existing focused review/check evidence, same-source pairing, per-original fresh memory admission, remote CPU FP32/four-thread execution and observation. Record actual learner counts/motion and complete costs; ordinary wall plans remain adjustable, not new caps. No replacement, retry, extra panel, extension, new grant, specification exception, lifecycle/default or peer change follows. No further Root ratification is needed. [S2][S4]; [specification §§11.4/11.8–11.11][S8].

## Access limits

All eight manifest paths were read at the linked fixed versions: card §§2/8, prior decision, intake/execution, named runner configuration surfaces, MAPPO switch, discoverer sampler and required specification sections. Agent-caller and reviewer-probe findings remain attributed to the records; unlisted `agent.py`, raw tests and live processes were not audited. No code, models, tests, profiling or experiments were executed here. No decision-critical source gap remains.

[S1]: https://github.com/CartmanFatass/My-paper-code/blob/7a34308e311ccec0d2c6b9fcbb949359b4bb85f5/docs/research/candidates/flexible_skill_duration/FSD_BASELINE_INTERRUPTION_B01_PROSPECTIVE_CARD_20260915.md
[S2]: https://github.com/CartmanFatass/My-paper-code/blob/7a34308e311ccec0d2c6b9fcbb949359b4bb85f5/docs/research/portfolio/pro_packets/20260915_fsd_baseline_interruption_investment/archive/RESPONSE.md
[S3]: https://github.com/CartmanFatass/My-paper-code/blob/7a34308e311ccec0d2c6b9fcbb949359b4bb85f5/docs/research/portfolio/pro_packets/20260915_fsd_baseline_interruption_investment/INTAKE.md
[S4]: https://github.com/CartmanFatass/My-paper-code/blob/7a34308e311ccec0d2c6b9fcbb949359b4bb85f5/docs/research/candidates/flexible_skill_duration/baseline_interruption_b01_20260915/EXECUTION.md
[S5]: https://github.com/CartmanFatass/My-paper-code/blob/7a34308e311ccec0d2c6b9fcbb949359b4bb85f5/scripts/run_fsd_baseline_interruption_b01.py
[S6]: https://github.com/CartmanFatass/My-paper-code/blob/7a34308e311ccec0d2c6b9fcbb949359b4bb85f5/hmasd/baselines.py
[S7]: https://github.com/CartmanFatass/My-paper-code/blob/7a34308e311ccec0d2c6b9fcbb949359b4bb85f5/hmasd/utils.py
[S8]: https://github.com/CartmanFatass/My-paper-code/blob/969fac75a04379c4ea0741b9ced0234aa8079323/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
