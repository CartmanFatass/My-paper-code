# ACVC cluster B03 — E0 result evidence

**Technically accepted B/EXPLORE; both separate frozen primary readings are UP.** Source `091c6725b149cd2dfa9665408cabee17b8f958e3`, master21937/eval31937. [Frozen card](ACVC_CLUSTER_DEPLOYMENT_B03_SCIENCE_CARD_20260914.md), [original summary](evidence/cluster_deployment_b03_20260914/summary.json), [all-row check](evidence/cluster_deployment_b03_20260914/INTAKE_ANALYSIS.json). One new unscreened C fit; no initial evaluation/checkpoint selection/scientific retry.

## Frozen rule and observed endpoints

J=S/256. Strictly >+.01J UP; inclusive [−.01,+.01] WITHIN retaining sign without equivalence; strictly <−.01J DOWN. Read both primaries separately with shared-F dependence. Dwell−C is descriptive. The original summary retains full float64 values and all64 signed differences per contrast; the table shows rounded display values.

| Contrast | Mean J difference | Sample SD | Conditional SE | Adverse / favorable / zero | Minimum | Maximum | Reading |
| --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| F−C | +0.1436987981 | 0.0893476848 | 0.0111684606 | 6 / 58 / 0 | −0.0562247788 | +0.3306456247 | UP |
| F−own-dwell | +0.1178477937 | 0.0740216398 | 0.0092527050 | 5 / 59 / 0 | −0.0568054788 | +0.2611427939 | UP |
| own-dwell−C | +0.0258510044 | 0.0658223096 | 0.0082277887 | 25 / 39 / 0 | −0.1200436498 | +0.1961046087 | UP, descriptive |

| Arm | Mean S | Mean J |
| --- | ---: | ---: |
| C | 23.211439722986206 | 0.09066968641791487 |
| F | 59.99833203395164 | 0.2343684845076236 |
| own-dwell | 29.829296847351504 | 0.11652069080996681 |

F made5,338 retraces; own-dwell made2,687 dwell interventions on its own evolving histories. These unequal exposures and every signed difference remain in original rows/summary. No dose matching or pure retrace/history attribution.

## Complete exposure and integrity

Exactly512 training episodes,256 two-episode rollouts,1024 ordered Adam/backward/update records,one fresh initialization/fit/final checkpoint,three private loads,192 final evaluation episodes. All704 episode rows and1024 ordered update rows passed identity/reset/count/finite-value checks. Team ticks131072 train+49152 evaluation=180224. Actor34902 + critic34177 =69079 parameters; evaluation learning/selector updates/gate constructions all zero. CPU FP32/intra/inter threads1, same clustered5-UAV/50-user H256 law.

Machine-produced exposure: actor displacement3.3661611080169678 relative to initial norm12.57059097290039 (ratio0.2677806568739251); critic displacement4.652736663818359 relative to initial norm9.311972618103027. This demonstrates actual learning exposure, not return improvement from an unmeasured initial policy. The stdlib recorded-byte calculation independently matched native float64 primary reductions at absolute1e-14; no new model/environment invocation.

## Native terminal, cost and preservation

Fresh adjacent admission at2026-09-14T13:14:06.230887Z passed physical/effective memory15,628,996,608bytes against4,294,967,296bytes. The sole detached invocation exited0 at13:16:49Z. Complete native runner/timeout/publication/process-exit wall **163.36s**, peak RSS548,876KiB (**0.5234489441GiB**). Supervisor rounded duration163s; monitor terminal-observation uptime185s is not runtime. Admission belongs to the surrounding supervisor boundary. Aggregate CPU was not measured. Current/historical full support/provider/agent cost remains UNKNOWN; SSH/Git preparation and independent review are not free or reset. No original owner-cap compliance is asserted. The300s native estimate was a planning reference; safeguards did not trigger.

Before launch, non-login Git network/lazy-fetch stalls and a historical tracking-ref conflict were repaired with configured login-shell exact-SHA fetch, preserving old refs. The first test batch failed module collection only; importlib correction passed21tests. Independent engineering review found and verified repair of unselected verbose telemetry. All preparation failures and timing limits remain in intake/execution facts. One original scientific invocation, no scientific retry. A local result-document serialization encountered Windows default-encoding failure after collection; explicit UTF-8/document tooling repaired the record without changing native bytes.

Verified native archive420,924bytes, SHA256 `c0bd6559406ce247c4db53727718373272e0f1175db0b7aea5fd141e446894b4`, retained at `temp/directions/acvc/retained/cluster_deployment_b03_20260914/native_output.tar.gz`. Checkpoint282,957bytes, SHA256 `b5502c21400e469a9ab667abd0821da317d5a13851231a90a858f57a836d2517`; retained inside the archive and not loaded during intake. [Member hashes](evidence/cluster_deployment_b03_20260914/NATIVE_ARCHIVE_MANIFEST.json) cover original output and supervisor artifacts. Native files are byte-preserved; analysis is separate.

## Meaning and predictions

This adds one complete independent learned-policy/evaluation programme. Three observed cluster endpoints show F increments over C and useful own-dwell; they are no retroactive confirmation study or pooled primary. Sixty-four worlds are conditional on this learned endpoint, not64 fits; train/eval roots both changed. F−C has6 adverse worlds, F−dwell5; own-dwell exceeds C on average but is adverse in25 worlds.

B03 F mean0.2343684845 is close to B02 F0.2344118691, while B03 C0.0906696864 and dwell0.1165206908 are lower than B02 C0.1298183101 and dwell0.1737028614. The larger differences therefore must be read alongside lower comparators, not as a measured increase in F absolute quality or an isolated training-variance effect. This observation cannot establish why the scores differ. No trained-policy default/stability, deployment, tuned-headroom, transfer, formal-UAV or component-causal claim. Uniform C01 and failed families remain separate.

Prospective DM forecasts scored UP/UP: multiclass Brier0.185 for F−C and0.305 for F−dwell; completion Brier0.0025. These are subjective forecast scores, not calibrated confidence or independent joint tests. Owner prediction was not taken (unattended). Full independent scientific review and DM findings response remain pending.
