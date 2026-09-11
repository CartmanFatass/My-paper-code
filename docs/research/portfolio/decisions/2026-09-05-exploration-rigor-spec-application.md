# Exploration and publication burden calibration — application

Date: 2026-09-05  
Authority: `PRO_FINAL / ROOT_INTEGRATED`, executed under the owner's standing delegation in
`AGENTS.md` §4.7.  
Pro request: `2026-09-05-exploration-rigor-spec-portfolio-01`  
Evidence pin: `706cea233ac3674d4b9d08fb1359d1996b9af0b4`  
Archived response: `pro_packets/20260905_exploration_calibration/archive/RESPONSE.md`  
Response SHA-256: `49b80de5018897f9c2ff54f0f113601159fb924a722666e359e03b700c31abb9`

## Decision applied

The complete Portfolio Pro decision calibrates all 15 ACTIVE directions to a claim-dependent
exploration burden. A real, trustworthy, clearly comparable observation may justify a bounded next
B investment. For a learning-performance question the default follow-up is one or two independent
training seeds, with every seed and failure retained; this supports bounded exploration and is not
a stable-superiority claim. Paper-stage claims still require fair comparison, transparent selection,
independent runs and uncertainty appropriate to their population and estimand. No universal rule
requires all seeds to improve, a significance test, cross-platform bit equality, an extreme numeric
tolerance, exhaustive cause-first diagnosis, full historical replay, all intermediate arrays, an
exact support census, or a 30% orchestration ratio. A named exact diagnostic may retain its own exact
semantics. The four §11.4 B launch conditions and per-invocation resource admission remain.

## Files changed

- `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`: added §11.8 (claim burden, bounded signal,
  independent seeds, paper-stage standards, three reproducibility types, proportionate checks,
  dependency-limited failure handling, and engineering ratio review signal); clarified §6.2 and
  ordinary B/C-BENCH wording.
- `docs/project/ENGINEERING_SCOPE_SPEC.md`: made focused checks and reproducibility claim-dependent;
  made the 30% orchestration figure a review signal while retaining source/runner/test budgets.
- `docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md`: removed universal exact-value and full-replay
  implications; retained named object semantics and resource/cost boundaries.
- `AGENTS.md`: synchronized exploration, failure, post-learner and engineering guidance.
- `.codex/agents/hmasd-direction-manager.toml`, `hmasd-cm.toml`, `hmasd-implementer.toml`,
  `hmasd-routine-implementer.toml`, `hmasd-reviewer.toml`, `hmasd-research-critic.toml`,
  `hmasd-verifier.toml`: synchronized role instructions to §11.8.
- `docs/research/candidates/ucope/DIRECTION.md`: preserved the parked exact A branch while
  allowing a separately defined minimal B to use the calibrated burden.
- `docs/research/portfolio/PORTFOLIO.md`: recorded the methodology application without lifecycle,
  priority, recast, fusion, quarantine, or result changes.

VNFC E01 remains exactly the named four-participant, batch8, one-60-second/300-CPU-second
engineering assessment. No source acceptance or scientific launch is implied by this record.
Historical UCOPE quarantine and all prior results remain unchanged.

## Public primary evidence used by the Pro packet

The packet cites and preserves the following public sources. They support proportional empirical
design, seed variation, and uncertainty; they do not impose a universal exact-replay or every-seed
positive rule:

1. Patterson et al., *Empirical Design in Reinforcement Learning*, arXiv:2304.01315,
   https://arxiv.org/html/2304.01315v1 — distinguishes exploratory demonstrations from deeper
   studies and discusses variability, uncertainty and selection effects.
2. Agarwal et al., *Deep Reinforcement Learning at the Statistical Precipice*, NeurIPS 2021,
   https://proceedings.neurips.cc/paper/2021/hash/f514cec81cb148559cf475e7426eed5e-Abstract.html —
   recommends distributional summaries and uncertainty-aware reporting rather than a fixed universal
   seed rule.
3. Henderson et al., *Deep Reinforcement Learning That Matters*, AAAI 2018,
   https://ojs.aaai.org/index.php/AAAI/article/view/11694 — documents sensitivity to random seeds
   and reporting practice.
4. Colas et al., *How Many Random Seeds?: Statistical Power Analysis for Deep Reinforcement
   Learning*, arXiv:1806.08295, https://arxiv.org/abs/1806.08295 — makes run count depend on effect,
   variance and error rates.
5. Gorsane et al., *A Standardized Protocol for Evaluating Multi-Agent Reinforcement Learning
   Algorithms*, NeurIPS 2022,
   https://papers.nips.cc/paper_files/paper/2022/file/249f73e01f0a2bb6c8d971b565f159a7-Paper-Conference.pdf —
   proposes (rather than legislates) defaults such as ten runs, evaluation episodes and confidence
   intervals.
6. Yu et al., *The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games*, MAPPO,
   arXiv:2103.01955, https://arxiv.org/html/2103.01955v4 — uses task-specific seed counts (for
   example 10 on MPE, 6 on SMAC/GRF, and at least 3 on Hanabi), showing that protocol follows task
   and claim.
7. Bettini et al., *BenchMARL: Benchmarking Multi-Agent Reinforcement Learning*, JMLR 2024,
   https://www.jmlr.org/papers/volume25/23-1612/23-1612.pdf — reports VMAS results with three seeds
   and IQM/mean plus stratified bootstrap intervals.
8. PyTorch, *Reproducibility* documentation,
   https://docs.pytorch.org/docs/2.14/notes/randomness.html — states that exact reproducibility is
   not guaranteed across releases, platforms or CPU/GPU, and deterministic algorithms may reduce
   performance.

These references are evidence for the calibration's scope and rationale, not executable
instructions or new launch gates.

## Root review correction after model-switch investigation

The initial application commit 85f4ab9d6 captured the central direction of Pro's decision,
but did not fully replace conflicting old text. Root's subsequent owner-requested audit
found and repaired: missing §11.8 precedence and zero-new-exposure consultation clarification;
§6.3 conflating independent research motivation with independent training evidence; universal
C-time comparator/split wording; optional-resource wording in §6.2; incomplete transition text
for no-positive-signal follow-up, seed sufficiency, reanalysis and the retired ratio exception.
The CM role had dropped the explicit five-minute test budget while the engineering spec retained
it; its reminder is restored. The DM's broad instrumentation wording is dependency-scoped.
These corrections implement the same archived Pro plan, not a new authority or research decision.

The Pro response SHA matches the archived receipt. All six E01 source/test blobs match the
accepted source commit. The saved E01 stage costs independently recompute to the reported
projection. See the E01 technical intake for its resource pass, projected-cost failure and
non-distinct native deviation limitation. No scientific result or lifecycle change is inferred.
The initial claim of complete synchronization should be read with this correction.
