# Exploration and publication calibration — evidence and proposed amendment

Status: Root proposal for complete Portfolio Pro review; not yet an applied specification.
Owner instructions, September 5: investigate excessive numerical/exact reproduction demands,
distinguish exploration from paper-claim validation, and relax engineering/scientific rules where
they are too strict. A clear single experimental improvement should support further investment,
followed by independent training seeds. Standing specification delegation remains applicable.
Owner further clarifies that universal extreme tolerance, cross-platform element equality,
exhaustive root-cause-first training and line-ratio rejection are not general publication norms
either. Do not merely postpone these gates until paper writing: remove them as defaults at both
stages, retaining only checks actually entailed by a specific claim or reachable correctness risk.

## What the sources support

These are primary-source paraphrases, not universal community mandates or empirical speed claims.

1. PyTorch, Reproducibility, official stable documentation accessed September 5 (resolved to 2.14):
   https://docs.pytorch.org/docs/2.14/notes/randomness.html
   The framework does not guarantee identical results across releases/platforms or CPU/GPU even
   with the same seed. Deterministic algorithms can cost performance and help debugging. This
   supports separating fixed-stack repeatability from scientific reproducibility; it does not
   establish that every deterministic simulation is unreproducible or excuse corrupt outputs.
2. Patterson, Neumann, White and White, Empirical Design in Reinforcement Learning (2023),
   sections 1, 2, 3 and 6: https://arxiv.org/html/2304.01315v1
   The authors distinguish exploratory demonstrations from deeper empirical studies, discuss
   training variability, uncertainty and selection bias, and note that simulation control can
   distract from empirical goals. Exploratory observations can motivate later work; they do not
   by themselves estimate stable superiority. The paper supplies no universal one/three/five-seed
   guarantee, and its published-claim cautions must not become a pre-exploration test battery.
3. Agarwal et al., Deep Reinforcement Learning at the Edge of the Statistical Precipice,
   NeurIPS 2021: https://proceedings.neurips.cc/paper/2021/hash/f514cec81cb148559cf475e7426eed5e-Abstract.html
   Few training runs make performance estimates uncertain. The authors advocate interval
   estimates, performance profiles and robust aggregates. The relevant reproducibility is the
   evidence for the performance claim, not equality of floating-point traces. This does not
   prescribe every seed winning or require statistical significance before another exploratory run.
4. Henderson et al., Deep Reinforcement Learning that Matters (2017):
   https://arxiv.org/abs/1709.06560
   Environment nondeterminism and algorithm variance complicate comparisons; implementation and
   reporting matter. Honest reporting and controlled comparisons remain necessary at every stage.
5. Colas et al., How Many Random Seeds? (2018): https://arxiv.org/abs/1806.08295
   Required runs depend on variability, effect and statistical error assumptions. Independent
   training seeds, rather than repeated evaluations of one checkpoint, are the relevant units
   for training variability. No fixed count guarantees a paper-level conclusion.

## Actual internal source of the overconstraint

Evidence spec sections 5.2 and 11 already permit adaptive one-to-three-seed B exploration and
prohibit bit identity, exact equality/support census and C-time contracts as B launch gates.
Section 4 says exact analysis must not delay a ready algorithm experiment as a ritual.
This is not an absence of exploratory policy; its application drifted.

ENGINEERING_SCOPE_SPEC section 3.5 nevertheless defines reproducibility as rerunning the recorded
command/SHA to the same numbers within tolerance, without distinguishing statistical learners
from deterministic replay diagnostics. Section 5 returns research diffs solely for orchestration
above 30 percent, and section 7 checks these budgets before correctness. DM instructions first
require every object to fix an extensive card, then disclaim C-like gates. These conflicting
instructions encourage excessive pre-run work and card proliferation.

UCOPE's root-target-vs-fit A/RECON was a specific same-draw mechanism localization, not a new
algorithm experiment. It required numerical reconstruction of historical references. Attempt02
had eight errors around1.01e-12 to1.18e-12 against absolute1e-12; no actual solver cause or native
decision impact was established. The subsequent byte comparisons were to isolate inputs versus
solver differences. Neither is a field-wide MARL condition. A diagnostic can justify such checks
for its limited claim, but its unresolved status must not automatically exclude fresh B work.

The UCOPE direct-reuse diagnostic draft had219 nonblank source lines,92 computing/evaluating and
127 orchestration (57.99 percent). Its total size and runner size passed; the ratio alone caused
return before runtime/semantic acceptance. Required array I/O and publication dominated the ratio.
No generic new machinery was found. This does not prove the draft correct or minimal, but exposes
a mismatch between the anti-overengineering purpose and a mechanical rejection criterion.

Positive UCOPE facts: paid acquisition5/6; three-witness tail agreement6/6 versus4/6 at matched
dose. Contrary facts: complete competence3/6 in both and two adverse new root probes. These do
not establish complete native performance improvement. A new exploratory question must name
whether it seeks local tail benefit, full return, or a repair of the root harm; do not rename
surrogate improvement as native improvement. Old quarantined attempt02 stays historical no-science.

## Proposed normative text for refinement and adoption

### Exploration is an investment decision; confirmation supports a claim

B exploration needs a concise question, actual runnable learner/comparator, meaningful metric,
actual exposure and a bounded compute plan. One credible improvement on a named metric is enough
to justify a bounded follow-up under existing object-tier delegation; it is not proof of stable
advantage or a mandatory unlimited investment. Preserve all tried configurations/results and any
native harms. Non-improvement may motivate a justified new exploratory change.

After a promising run, prefer independent training-seed follow-up of the same comparison before
expensive causal localization when learning performance is the question. Use the existing1–3 B
range as an economical starting point, not a statistical guarantee. Paired treatment/control
seeds are useful when the design supports them; separate evaluation randomness from training
randomness. Do not require every seed positive, discard adverse seeds, or count multiple rollouts
of one trained policy as independent training. Record adaptive changes as exploration.

Paper/conclusion-stage comparisons require design-appropriate independent runs, credible and
fairly tuned comparisons, declared selection/evaluation, uncertainty, ablations or transfer only
where the actual public claim needs them. Neither3–5 seeds nor all seeds positive alone proves
a strong claim. Publication rigor is not a precondition for exploratory investment.

### Reproducibility and numerical checks follow the claim

Default empirical reproducibility means sufficiently documented code/configuration and a
statistically supported performance conclusion on the stated population. Fixed-stack numerical
repeatability is useful for debugging; cross-platform/bitwise trajectory equality is not a
default A/B/C-BENCH condition. Exact source-byte Git provenance is not exact output equality.
Deterministic kernels, discrete invariants, semantic-preserving optimizations and numerical
diagnostics may need exact checks where their own observable requires them; this exception is
local and may not be inherited by unrelated learning experiments.

No universal1e-12 or bit-identity tolerance. Select prospective checks from dtype, scale,
conditioning, accumulation and material metric/action consequences. Use absolute/relative or
decision-level checks as appropriate, without mandating a new tolerance calibration experiment.
Small differences are not presumed harmless or important merely from magnitude. Uncertain
numerical details limit the specific dependent claim; they do not automatically invalidate
independently measured performance. Preserve historical failures; revised criteria belong to a
new clearly labelled analysis or experiment, never silently to the original record.

### Minimal verification and engineering

For disposable research code,30 percent orchestration is a review signal, not automatic rejection.
Keep existing2000-source/600-runner boundaries and ordinary resource budgets unless explicitly
changed. Reviewer identifies concrete unnecessary machinery or correctness risk; required I/O,
evaluation and result serialization are judged for necessity/readability. No detailed line-range
census or ratio exception round is required solely to approve ordinary necessary plumbing.
Do not pad computation, compress code or move wrappers to meet a cosmetic denominator.

Run one proportionate focused verification covering the changed behavior and usable primary
measurement output. Reuse checks on unchanged relevant bytes; do not duplicate smoke before launch
solely because a launch boundary occurred. Follow-up training seeds are scientific observations,
not duplicate smoke tests. Extend tests only for actual changed/risky paths or observed failures.
No automatic exhaustive support census, all-intermediate-array publication, cross-platform solve,
full historical replay, framework, or chained diagnostic before a B learning observation.

A bug that threatens reward, information access, treatment/comparator, training or primary
measurement needs targeted repair/checking. Not every historical exception needs a fully located
root cause before a different trustworthy path is used. Error-text diagnosis remains provisional;
do not claim an unreproduced cause. Distinguish unusable primary measurement from optional diagnostic
or resource output gaps, retaining all directly usable facts at their actual ceiling.

### Transition and exact files

Apply final clauses in evidence spec sections4/5/6/11 (new short11.8 if useful), engineering scope
sections3/5/7, AGENTS sections1/5/8, and instruction bodies of DM, CM, semantic/routine implementers,
reviewer and relevant verifier/critic roles. Preserve runtime model/effort/permission settings.
Synchronize runtime spec generic validation guidance if needed, keeping its exact VNFC appendix
explicitly distinct. Do not create a new approval service, mandatory checklist or audit framework.

Portfolio should show this applied correction and direction follow-up ownership, not change
lifecycle/priority automatically. Ask UCOPE DM to compare a minimal new B with independent training
seeds against optional bounded numerical investigation at the proper direction node; prior narrow
PARK and old attempts remain intact until a new scoped decision. The prospective proposal is
authorized preparation, not acceptance of the rejected UCOPE code or automatic old run retry.

N3/CBSC/K1/K4 unsent packets are being corrected to include direct B where actual execution and
measurement integrity permit it; missing exact upper or causal explanation is not a prerequisite.
Root applies the complete Pro specification plan under standing owner delegation, records exact
before/after scope and P1/P2 trace, then DMs execute within the corrected evidence burden.
