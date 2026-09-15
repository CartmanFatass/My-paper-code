# TRDL-A01 — static result evidence

Class **A/RECON**, complete preparation, zero new experiment exposure. Read with the [A01 card](TRDL_A01_SCIENCE_CARD_20260914.md) and [intake](TRDL_A01_INTAKE_20260914.md). This document is E0 evidence of a source/design path, not evidence of learner efficacy or accepted executable code.

## Reading rule, observation and receipts

Rule applied verbatim:

> If the registered host and actor path exist and both distinct baseline updates can be specified under one common tail objective, return a concrete prospective B card and minimal implementation/work outline. Otherwise return the exact incompatibility and smallest correction. In either branch, report zero new experimental exposure and no efficacy or measured-feasibility claim.

Observed branch: the reusable host/actor/replay paths exist; a common tail-score actor objective with two genuinely distinct fitted baselines is specifiable. The [prospective B01 card](TRDL_B01_SCIENCE_CARD_20260914.md) completes that definition and minimum implementation outline. The TRDL candidate code directory **does not exist** at inspected source `05a8dc01560e99b867a36b0414058a251b24453c`; only `DIRECTION.md` existed under its direction record at assignment entry. The map was a designated ownership surface, not an executable implementation.

Actual command evidence: `git status --short` was empty at entry; branch `codex/trdl`, HEAD `d9be8ec9bd8077f6f5751c9606e3fa62e18f8118`. A clean fast-forward incorporated Root's `05a8dc01560e99b867a36b0414058a251b24453c` control repair. Source investigation used `rg`, text reads and standard-library Python (`json`, `sqlite3`, `pathlib`, arithmetic). No candidate module was imported. There is no run handle, checkpoint, environment reset/step, optimizer or resource-admission receipt to claim.

Machine-generated actual exposure: **fits=0; model constructions=0; native calls=0; evaluation calls=0; optimizer updates=0; cost pilots=0; historical numerical reruns=0**. [Counts JSON](TRDL_A01_COUNTS_20260914.json) separates these observed activity counts from prospective configuration arithmetic. Literature retrieval and preparation consumed control-plane labor; no wall/peak-memory affordability measurement was made.

## Source facts that determine the design

Paths below are rooted in the inspected checkout at `05a8dc01560e99b867a36b0414058a251b24453c`.

| Source and locator | Direct static fact | Consequence |
| --- | --- | --- |
| `experiments/candidates/ucope/uav_motion_prefix_b01/environment.py:8–24` | `make_real` constructs MultiUAVEnv with five UAVs, fifty users, H256, homogeneous motion and native vectorized channel, then the array adapter. | Use this existing host; no synthetic substitute or new task needed. |
| `envs/pettingzoo/uav_env.py:194,353–365,1463–1487` and `env_adapter.py:172–186,251–285` | One constructor reset; native state has 116 entries including time; team reward is distributed across agents, while adapter scalar averages it again. | Count constructor reset separately; use sum of rewards_dict and append only cumulative reward to existing 136 critic inputs. |
| `environment.py:27–50` and native observation `uav_env.py:382–433` | Actor108 = native104 + own last command3 + remaining1; current actor already sees elapsed time. Critic136 = state116 + joint commitments20. | Preserve actor information, ordering and padding. Shared critic context is137, including pre-action accumulated reward/H. |
| `experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/geometry.py:52–64,104–148` | DENSE residual path, GRU64 and motion/log-std components are available; duration=None. | Reuse intact execution actor, no duration or geometry intervention. |
| `ucope/uav_motion_prefix_b01/learner.py:12–26,208–268` | Existing update uses return-to-go, standardized advantages, entropy=.01 by default, four epochs and per-agent compound clipping when requested. | **This update cannot be reused as the TRDL learner.** Reuse replay/density/clipping primitives; replace target/baseline/loss handling locally. |
| `learner.py:29–44,158–204` and `policy.py:116–133` | Collector keeps full native episode, current state and detached hidden starts; source J is reward_sum/H; policy draws CPU Gaussian velocity per active UAV. | A small local collector retains native collection but stores full-G context and no incompatible scalar value call. Final evaluation can be actor-only. |
| `mgtap_conditional_pooling_b01/study.py:108–161` | Its actual fit uses batch2, 1,024 Adam calls and 32 final episodes with the expected-return update. | Existing DENSE fits are not a same-objective trained null; do not reuse those checkpoints or pretend its time law covers the TRDL pair. |

The mismatch is in the source update, not in the registered scientific comparison. Its smallest correction is a direction-owned tail learner/collector and own-tail reducer, retaining the host and DENSE actor. No shared scientific source edit is necessary. No such code was written in A01.

## Knowledge use and exact limits

Question: does a distributional training baseline supply a coherent finite contrast against a scalar baseline aimed at the same lower-tail score, and which information/uncertainty restrictions matter?

Foundations §§2–4/6 and topic notes `02_MARL.md` (CTDE, credit) and `04_EMPIRICAL.md` (units, selection) were read. They change the assessment in three ways: a critic may use extra training information without changing actor legality; expressive conditional predictors need not be Markov-sufficient or better after finite learning; 256 final episodes estimate one fitted policy's conditional performance, not a training population. Hence keep current pre-action critic context separate from actor history, make no ideal-baseline advantage theorem, and retain the one-pair ceiling.

Verified local-library coverage: Inst-sci formal `C:/Projects/Inst-sci/papers/MyLib/llm-index/catalog.v2.jsonl` contained **190** records. A bounded risk/CVaR/quantile title/abstract search returned MARL-0189 and MARL-0563. My-lib's read-only `.local-index/knowledge.sqlite3` metadata reported two mechanisms, coverage date 2026-07-26; their `registry/mechanisms.yaml` collections are `synthetic-core`. Those fixtures were excluded. No real unified My-lib mechanism coverage was asserted, no index built, and no paper acquisition performed.

Verified primary passage: RiskQ (Shen et al., NeurIPS2023), `C:/Projects/Inst-sci/papers/MyLib/json/MARL-0563.json`, page2 paragraph IDs395–397; identity/asset record in `metadata/v2/papers.v2.jsonl` had official-title match, JSON ready and no quality warnings. Paragraph397 defines weighted quantile utilities with greedy risk-sensitive decentralized actions. It supports taking risk criteria seriously; it **does not supply or validate** TRDL's PPO baseline estimator. [Official RiskQ source](https://papers.neurips.cc/paper_files/paper/2023/hash/6d3040941a2d57ead4043556a70dd728-Abstract-Conference.html).

The local search did not supply the specific CVaR score identity or quantile loss, so the following official primary PDFs were read for that gap:

- Tamar, Glassner and Mannor, *Optimizing the CVaR via Sampling* (AAAI2015), §2.1 Proposition1 and following baseline discussion (PDF pages2–3). The quantile term is part of the tail score and cannot be replaced by an arbitrary constant inside its indicator. Its smoothness/continuous-return assumptions and estimator analysis do not establish TRDL's finite empirical-threshold/PPO claims. This preserves W's threshold term and labels the package approximate. [PDF](https://cdn.aaai.org/ojs/9561/9561-13-13089-1-2-20201228.pdf).
- Dabney et al., *Distributional Reinforcement Learning with Quantile Regression* (AAAI2018), quantile-regression section, Eq.(8) (PDF page4). It provides the pinball residual sign and midpoint-quantile construction. TRDL uses factual complete-G targets; it does not copy QR-DQN's Bellman target cross-product or its convergence claim. This avoids accidentally multiplying the proposed loss by 32 extra targets. [PDF](https://ojs.aaai.org/index.php/AAAI/article/download/11791/11650).

No source establishes TRDL efficacy, priority dominance or universal novelty. The new calculation is configuration arithmetic only. Ordinary scalar-target sufficiency remains the strongest scientific alternative.

## Counts, resource scope and deviations

Prospective pair: 1 fresh paired training instance, 2 arms, 512train+256final episodes/arm, H256; 393,216 scored team ticks, 256 joint Adam calls. Q32's 16,777,216 scalar loss terms derive from `512*256*4*32`; SCALAR's 524,288 from `512*256*4`. Neither counts independent evidence units. Exact formulas and component byte counts are in the JSON; complete rates and peak RSS stay unknown.

Baseline inventory check: only `scenario_1` and `relay_corridor` packages were present. `scenario_1/baseline_set.json` describes a different six-UAV/H500 host and incomplete exposure-only results. It cannot provide matching lower-tail headroom or the B01 null. No historical values were recomputed or used as TRDL performance.

No scientific-meaning change, source implementation, invocation-cap consumption or engineering §5 code-budget breach occurred. The empirical quantile convention, critic input137, pinball loss, precise seed partition and frozen baseline placement are prospective details of the registered design, disclosed in B01. In particular, the nominal four tail observations per16 do not imply four nonzero W scores. No cost or performance diagnostic was introduced to remove this uncertainty.

Final documentation self-check: all local file-link targets resolved; both cards begin with claim/binding lines; arithmetic record preserves 393,216 prospective ticks/256 updates and zero actual A exposure; Chinese brief is372 characters. Four reused Python source files parsed through `ast.parse` without imports/execution. `git diff --check` passed. These are static checks, not runtime or scientific-source acceptance.
