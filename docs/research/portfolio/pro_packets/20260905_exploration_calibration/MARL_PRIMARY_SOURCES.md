# MARL-specific primary evidence

Read-only Luna/max source investigation by /root/scout_lmx_mappo_performance, September5.
Full working report: C:/Projects/ref-lib/reports/on-policy/EMPIRICAL_REPRODUCIBILITY_REVIEW.md.
Root retains the compact source findings here and distinguishes source practice from policy.

## MAPPO: actual protocols, not one universal seed count

Yu et al., The Surprising Effectiveness of PPO in Cooperative, Multi-Agent Games, NeurIPS2022:
https://arxiv.org/html/2103.01955v4
Sections4.2–4.5 report ten training seeds for MPE, six for SMAC and GRF, and at least three for
Hanabi. SMAC uses32 evaluation games per evaluation; GRF uses100 games and aggregates late
evaluations. These evaluation episodes are not additional independent training seeds. Protocols
aggregate across runs, rather than require every run to win or reproduce identical traces.
Official code at de66d7a4b23fac2513f56f96f73b3f5cb96695ac contains one-seed example scripts and
optional deterministic cuDNN settings. Script defaults demonstrate runnable small experiments,
not statistical sufficiency. No universal extreme numeric tolerance follows from this paper.

## MARL evaluation protocol proposal

Gorsane et al., Towards a Standardised Performance Evaluation Protocol for Cooperative MARL,
NeurIPS2022:
https://papers.nips.cc/paper_files/paper/2022/file/249f73e01f0a2bb6c8d971b565f159a7-Paper-Conference.pdf
The75-paper meta-analysis discusses inconsistent run counts, implementation effects and
uncertainty. Its proposed protocol uses10 independent training runs,32 evaluation episodes
and95 percent intervals as defaults, with task-specific choices and computational limits.
This is methodological guidance, not a universal publication requirement. The standardization
target is interpretable performance evaluation; not cross-platform element equality.

## Published lower-run example

Bettini et al., BenchMARL, JMLR2024:
https://www.jmlr.org/papers/volume25/23-1612/23-1612.pdf
The VMAS appendix reports mean/IQM and95 percent stratified-bootstrap intervals across three
random seeds. This is an observed benchmark protocol, not evidence that three seeds always
suffice. Together the sources show that seed counts depend on task, claim and uncertainty.

## Root interpretation and limits

An observed single-run treatment difference can be a preliminary B signal and justify bounded
follow-up. It is not an established population effect or stable superiority. The scout's phrase
"cannot establish an algorithm effect" is interpreted at that population-claim ceiling; it must
not erase an honestly labelled observed B effect. Mixed-sign seeds may support a positive aggregate;
all-positive few seeds need not support a reliable population estimate. Neither pattern is an
automatic launch or acceptance gate. These sources do not justify exhaustive debugging before
every learner, universal1e-12, or an engineering line-ratio rejection rule. Their absence in the
inspected protocols is not proof that no specialized paper ever needs exact numerical validation.
