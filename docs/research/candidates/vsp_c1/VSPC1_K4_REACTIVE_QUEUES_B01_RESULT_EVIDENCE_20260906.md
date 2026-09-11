# VSPC1-K4-REACTIVE-QUEUES-B01 — result evidence, 2026-09-06

**B/EXPLORE, complete and technically accepted.** One paired training instance (seed 401)
gives FACTOR minus GENERIC endpoint **−0.000325520833**, inside the frozen absolute MEI
0.025. Full-curve AUC has the opposite sign, **+0.000254313151**. Both observations stand;
neither is a stable superiority or equivalence result. No additional invocation is selected.

## Question and rule applied verbatim

The [frozen card](VSPC1_K4_REACTIVE_QUEUES_B01_SCIENCE_CARD_20260906.md) asks whether
multiplicative duration-conditioned Q values improve completed service over a fully conditioned,
same-information generic Q learner on the reactive two-queue host, after 256 updates. It holds
the actual 48-tick native return, periods 2/6, fixed reactive partner and equal period weighting.
Card §5 supplies the applicable observation and reading:

> abs(Delta) < 0.025, or evaluation precision leaves the MEI boundary unresolved
>
> Insufficient practical-gain reason from this comparison; preserve small effects/uncertainty, no equivalence or automatic longer training/evaluation. A specific new question must justify further work.

The first condition applies directly. The endpoint/full-curve row also applies:

> Endpoint and full-curve readings differ
>
> Report both, with endpoint primary. No winner selected from AUC, best checkpoint or initial-value gain.

The pair is complete; there is no damaged primary or missing comparator. Neither period has a
material loss at −0.025, nor a gain at +0.025. The conditional evaluation SE is 0.000111872298,
and the observed endpoint is 0.024674479167 from the nearest MEI boundary. This describes noise
for the fixed models on paired evaluation episodes; it is not training-instance uncertainty.

## Source, receipts and engineering conformance

Both calls used integrated source `47674883572bbe078ede037cbb8f99b8cd54c159`, configured
node wsl_4070 and detached cwd `/home/wu/hmasd-worktrees/vspc1-reactive-queues-b01-476748835`.
Interpreter `/home/wu/.venvs/hmasd/bin/python`, NumPy 1.26.3, Torch 2.7.0+cu118 with CPU
float32 tensors, one compute thread and batch 16. Root dispatched each corrected handle once.
CM collected the exact artifacts and accepted FACTOR at `02caf76d514f1dfc2d807964141e3e980336caa1`,
then the pair at `a738645e0c1c57d558ccc175280b43fb4c7db7a4`;
[complete technical record](https://github.com/CartmanFatass/My-paper-code/blob/a738645e0c1c57d558ccc175280b43fb4c7db7a4/docs/research/candidates/vsp_c1/VSPC1_K4_REACTIVE_QUEUES_B01_CM_RECORD_20260906.md).
Root integrated the latter at `64b20f7ca`. Root owned observation; CM retained collection and
technical acceptance. Both handles are terminal and there is no remaining process to observe.

| Receipt | FACTOR | GENERIC |
| --- | --- | --- |
| Handle | vspc1-reactive-b01-factor-run02 | vspc1-reactive-b01-generic-run02 |
| Admission UTC | 2026-09-07 06:09:30.788337 | 2026-09-07 06:17:09.434040 |
| Physical/effective available bytes | 15,668,547,584 | 15,669,395,456 |
| Rounded supervisor start/end UTC | 06:09:30 / 06:09:35 | 06:17:09 / 06:17:14 |
| Terminal status / exit | finished / 0 | finished / 0 |
| Whole invocation wall seconds | 4.84 | 5.48 |
| Whole user / system CPU seconds | 3.73 / 0.39 | 4.38 / 0.43 |
| Main-process peak RSS bytes | 478,375,936 | 477,904,896 |

Each node-local admission passed the 4,294,967,296-byte physical and effective floors, adjacent
to its actual invocation. Cgroup readings are unavailable, not unlimited capacity. Each complete
arm was below its original 2,700-second cap. GENERIC's timer includes subsequent paired-report
publication and exit inside the same timeout; FACTOR's includes its publication and exit.
Sum of invocation wall is **10.32 seconds**, CPU **8.93 seconds**. The rounded first-start to
last-end interval is **464 seconds**, including serial control and collection gaps; it is not
sum of compute wall. Git/SSH preparation and agent reasoning cost are unmeasured. These timings
do not establish algorithm speed or replace the preserved prospective cost assumption.

Source acceptance used seven focused semantic checks and one repaired paired publication fixture,
plus independent scientific/numerical/RNG review. The source was 390 non-test lines, including
a 79-line runner; no engineering-scope §4 machinery or §5 budget breach was found. The ordinary
source/check record remains in the [preceding intake §6](VSPC1_K4_REACTIVE_QUEUES_CONVERGENCE_INTAKE_20260906.md).
DM inspected relevant artifacts and performed arithmetic over stored outputs; no source test,
rollout, model evaluation, replay or publication invocation was repeated during this intake.

## Attempts and actual exposure

The original accepted FACTOR run01 was a **technical no-op**: finished/exit 0 in the same
second, two supervisor log lines, no output root, and stored execution `eval 'bash -lc  cd '`.
The accepted command therefore ran only cd, with neither resource admission nor learner.
[Preserved run01 witnesses](results/k4_reactive_queues_b01_seed401_20260906/run01_noop/accepted_runner.txt)
support zero selected-experiment exposure from that handle. The upstream interpolation
mechanism was not uniquely reconstructed. CM repaired command transport, checked literal
stdin/argv syntax without execution, and Root used new run02 handles. This failure has no
scientific polarity, creates no retry allowance and is not retroactively called a result.

| Actual quantity | FACTOR | GENERIC | Pair |
| --- | ---: | ---: | ---: |
| Trainable online parameters | 300 | 309 | two models |
| Training episodes | 4,096 | 4,096 | 8,192 |
| Training joint ticks | 196,608 | 196,608 | 393,216 |
| Real renewal TD rows | 65,536 | 65,536 | 131,072 |
| Nonterminal rows | 61,440 | 61,440 | 122,880 |
| Adam steps | 256 | 256 | 512 |
| Evaluation episodes | 2,304 | 2,304 | 4,608 |
| Evaluation joint ticks | 110,592 | 110,592 | 221,184 |
| Evaluation decisions | 36,864 | 36,864 | 73,728 |
| All episodes / joint ticks | 6,400 / 307,200 | 6,400 / 307,200 | 12,800 / 614,400 |
| Scalar Q predictions | 454,656 | 454,656 | 909,312 |
| Target copies, including initial | 17 | 17 | 34 |
| Model-selection steps | 0 | 0 | 0 |
| Initial parameter norm | 4.527723789 | 3.685532808 | — |
| Final parameter displacement | 1.455944419 | 1.503602028 | — |

Each summary contains all nine fixed checkpoints, 256 per-period TD-loss rows and 128 indexed
endpoint episodes per period. Counts match the fixed budget. Real movement and updates are
observed; they establish learner exposure, not learning benefit. The separately recorded seed-9401
engineering fixtures used 9,216 training ticks, 48 Adam steps and 1,152 evaluation ticks in three
arm fixtures; host-rule fixtures add 244 ticks and a synthetic zero-lr loss check. That exposure
is not another independent selected B01 instance. Preparation/transport/reanalysis added none.

## Every selected performance observation

| Update | FACTOR d2 | GENERIC d2 | FACTOR d6 | GENERIC d6 | FACTOR mean | GENERIC mean | Mean difference |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.726643880 | 0.726643880 | 0.723795573 | 0.723795573 | 0.725219727 | 0.725219727 | 0.000000000 |
| 32 | 0.720377604 | 0.726643880 | 0.723795573 | 0.723795573 | 0.722086589 | 0.725219727 | −0.003133138 |
| 64 | 0.725179036 | 0.726643880 | 0.723551432 | 0.723795573 | 0.724365234 | 0.725219727 | −0.000854492 |
| 96 | 0.725585938 | 0.724609375 | 0.723795573 | 0.723795573 | 0.724690755 | 0.724202474 | +0.000488281 |
| 128 | 0.708658854 | 0.724609375 | 0.722900391 | 0.723795573 | 0.715779622 | 0.724202474 | −0.008422852 |
| 160 | 0.725341797 | 0.715087891 | 0.723551432 | 0.723714193 | 0.724446615 | 0.719401042 | +0.005045573 |
| 192 | 0.723225911 | 0.715413411 | 0.722981771 | 0.723632812 | 0.723103841 | 0.719523112 | +0.003580729 |
| 224 | 0.726481120 | 0.714762370 | 0.722900391 | 0.723632812 | 0.724690755 | 0.719197591 | +0.005493164 |
| 256 | 0.726643880 | 0.726643880 | 0.723144531 | 0.723795573 | 0.724894206 | 0.725219727 | −0.000325521 |

Endpoint d2 difference is 0; d6 is −0.000651041667. All 128 d2 episode returns match.
At d6, 120 match and eight have one fewer job served by FACTOR; none favors FACTOR. These
are paired evaluation observations, not 256 training replications or proof of equal policies.
The endpoint mean deficit is **0.03125 jobs per episode**. Both endpoints have zero overflow;
d6 final backlog is 1.4140625 for FACTOR versus 1.3515625 for GENERIC, while d2 is 1.3359375
for both. Shared arriving work and these final backlogs account for the service difference;
this accounting does not identify the learning cause or action at which it arose.

Normalized AUC: FACTOR **0.723027547201**, GENERIC **0.722773234049**. Period AUC differences
are +0.000885009766 (d2) and −0.000376383464 (d6). FACTOR's retained transient leads at
96/160/192/224 coexist with its endpoint loss. FACTOR ends 0.000325520833 below initialization;
GENERIC returns to its initial mean. Both initial return profiles are already high on this
host; equal initial returns do not assert equal parameters, Q values or policies. There is no
checkpoint substitution or claim that TD-loss reduction implies improved service.

## Outcome-informed A/RECON from existing job counts

Question: does the recorded available work leave an MEI-sized improvement above this observed
GENERIC endpoint on the same evaluation tapes? The measurement is an arithmetic reading of
existing endpoint sums, selected after seeing the result; no new environment/model/learner is
used. Work is linear in the 2 arms × 2 periods × 128 retained endpoint rows, with zero added
training/evaluation exposure and no engineering-scope §4 item. It does not modify the B rule.

Queue conservation gives total available jobs = served + overflow + final backlog. For any
policy on that same initial state and arrival tape, served jobs cannot exceed
min(96, available jobs). This is a **loose supply upper**: it even includes final-tick arrivals
that cannot be served. The two arms' recovered available-job totals agree episode by episode.

| Recorded diagnostic | d2 | d6 | Equal-period mean |
| --- | ---: | ---: | ---: |
| Supply upper J | 0.740559895833 | 0.737874348958 | 0.739217122396 |
| Upper minus observed GENERIC | 0.013916015625 | 0.014078776042 | **0.013997395833** |

Thus a +0.025 improvement over this fixed observed baseline is impossible on these evaluation
tapes even under this generous upper. The 1.34375-job mean gap is below the card's 2.4-job MEI.
This bounds the current endpoint opportunity; it is not a tuned-headroom record, attainable
optimal value, population bound, reason to erase the tiny adverse result, or license to search
for a positive host. Different training instances and the transient/sample-efficiency question
remain outside this diagnostic. Old A01's missing terms and old-host references are untouched.

## Evidence and analysis paths

Exact copied [FACTOR summary](results/k4_reactive_queues_b01_seed401_20260906/FACTOR/summary.json),
[GENERIC summary](results/k4_reactive_queues_b01_seed401_20260906/GENERIC/summary.json) and
[paired publication](results/k4_reactive_queues_b01_seed401_20260906/paired_summary.json)
retain primary arrays, all curve points, TD losses and native consequences. Admission, timing,
supervisor status/log and accepted commands are alongside each arm. Original runtime artifacts
remain under `temp/directions/vsp_c1/exp/k4_reactive_queues_b01_run02/` in the CM repair worktree
and the bound remote cwd. Archived primary summary SHA256 values:

- FACTOR: `0e7014506bfe2d19c4f9b7c8ce66eb29a1974ccbed9441a488a2170de6e5d04f`.
- GENERIC: `b5866d68ef0b0ae2f3e57548d6522b1f809d2a3499b803f13b330e16ee1e6a93`.

The scientific-tools run summarizer reads [one endpoint per arm/seed](results/k4_reactive_queues_b01_seed401_20260906/endpoint_scores.csv)
and reports [one paired instance, no sample SD or interval](results/k4_reactive_queues_b01_seed401_20260906/endpoint_summary.json).
Separate standard-library arithmetic over the collected records gives
[full curves, conditional SE, AUC and supply diagnostic](results/k4_reactive_queues_b01_seed401_20260906/computed_observations.json).
Floating summation order changes only trailing digits, not any scientific reading. No extra
interpreter dependency or new experiment was introduced. The
[DM intake](VSPC1_K4_REACTIVE_QUEUES_B01_INTAKE_20260906.md) records the bounded interpretation,
prediction check and executed object-tier consequence.
