Claim: one new unchanged learning pair will measure whether the learned public-event retention package's first native gain recurs across a fresh training history against event-aware RETAIN.
Binding MARL structure: agent-count scaling or roster change; physical-trip turnover under partial observation makes the useful lifetime of a survivor's own local history uncertain.

# FOLR-LEARNED-RETENTION-B02 — B / EXPLORE

## Authority and independent question

Portfolio PRO_FINAL / OWNER_DELEGATED selects option P in the response at
`41c46303f66005f74a18dccf45974d99771b155b`,
[§§1,3](../../portfolio/pro_packets/20260911_post_program_vacancies/archive/RESPONSE.md).
Root forwards conformance PASS and this complete allocation on 2026-09-11.
This is one NEW unchanged LEARNED_EVENT/RETAIN pair. The completed B01 allocation
and its seed7809/107809 are not resumed. The opened learned family, fixed-half pause,
recast count, lifecycle, priority, C and UAV status remain unchanged.

Question: with 5,000 full native training episodes and 128 final episodes per arm,
what is the fresh final mean-return difference LEARNED_EVENT minus RETAIN?
The independent unit is one matched-initialization training pair. Both arms are
preselected before observing either score. No extra panel, seed screening, pilot,
new comparator, third learned pair, scientific retry or automatic successor is allocated.

## Unchanged operation, ownership and comparator

Reuse the accepted [B01 operation and learner](FOLR_LEARNED_RETENTION_B01_SCIENCE_CARD_20260911.md)
and source `8d518ff300c13d809f8d88d0a259a3d8f6ff59d6` without implementation changes.
The shared scalar is `g = sigmoid(w_x*x + w_h*h_bar + b)`: existing64-wide local
fc2/ReLU input x and64-wide lifetime-masked own incoming state h_bar,128 weights
plus one bias. Initialize weights zero and bias log99; eligible-event retention
starts at0.99, not exact RETAIN. After a completed public birth/departure event,
only a true continuing physical trip receives g*h_bar before the ordinary GRU.
Elsewhere the GRU receives ordinary h_bar. No gate, initialization or architecture search.

Physical newcomers, departures, padding and same-slot replacements inherit neither
the departed trip's recurrent state nor previous action. A surviving physical trip,
not its storage slot, owns history; lifetime masks also prevent cross-trip gradients.
The actor uses only existing local attention, public event, own-birth and previous-action
information, with no future event, private partner history or critic-only global input.

RETAIN is the competent event-aware local attention/GRU actor with FlexQMixer. Its
ordinary gates already condition on the same input/history. The additional129 coefficients
are a same-information package change, not a capacity-matched causal contrast.
Acting and complete-episode online/target replay recompute their own law and hidden
states from their own parameters; acting gates are not stored replay constants.
Preserve constructor RNG isolation and all common actor/mixer draws, native traffic
and action RNG consumers, episode sampling, optimizer membership, target copies,
checkpoint serialization and final publication. Preserve native rewards and partner
co-adaptation. This CAMA-derived host is not original CAMA.

## Fresh bindings and complete exposure

Fresh unscreened training seed **7810** and evaluation seed **107810** advance the
prior identities once without model construction, sampling or outcome screening.
Each arm starts independently from fresh models and optimizer/RNG state; no historical
checkpoint, handle, partial episode or replay buffer is reused. Python/global NumPy/Torch
seed before construction and reset to107810 for the final fixed greedy panel.
Same initial seeds match common initialization, not action-dependent subsequent worlds.

Per arm:5000x20 training ticks,4969 RMSprop steps beginning at episode32; each update
samples32 complete episodes and unrolls21 observations through online and target actors.
Preserve lr0.0005/alpha0.99/eps0.00001, gamma0.99, clip10 and target copy every200 episodes.
One final checkpoint then128x20 evaluation ticks. Pair totals computed from these loops:
2 real fits,10000 training episodes,200000 training ticks,9938 optimizer steps,
256 final episodes/5120 final ticks,205120 total team ticks.
Dominant intrinsic factors are2x4969x32x21x5x2 =66783360 replay GRU rows and
2x5128x21x5 =1076880 acting rows. The learned arm adds33930120 gate-forward rows
plus online gradients and optimizer work. Mixer, movement and publication remain work.
Added validation: zero new learner/model/fixture/test invocations; reuse accepted checks.

## Primary, reading rule, forecast and interpretation

Primary d_LR is mean(all128 LEARNED_EVENT native returns) minus mean(all128 RETAIN
native returns), with ordered arrays, both means and conditional episode SDs preserved.
Evaluation labels do not define matched post-action worlds because actions change
traffic/RNG consumption. No episode-wise paired-world inference or128-seed interpretation.

**Reading rule, applied verbatim:** `d_LR >= 1: LEARNED_EVENT_ABOVE_MEI; d_LR <= -1:
RETAIN_ABOVE_MEI; otherwise: WITHIN_MEI. An incomplete or untrustworthy primary has
no paired performance polarity; preserve independently trustworthy facts.`

MEI is absolute1 native return, retained prospectively as one tenth of the native10-unit
collision penalty and a practical host-level decision scale. Above it, report recurrence
of a bounded package gain across two observed training pairs; inside it, report the signed
small difference without equivalence; opposite sign favors RETAIN on this pair and would
weaken an unqualified recurrence claim. None establishes stable expected superiority,
useful-memory causality, adaptation separate from initialization/capacity/co-adaptation,
tuned headroom, original-CAMA superiority or transfer. Any future investment is unselected.

DM prediction: **WITHIN_MEI, low confidence**. B01's+1.763359375 is favorable but its
RETAIN endpoint was weak and the legal GRU null is already adaptive. A second training
history can change the sign or size. Owner prediction: not taken (unattended); score
only a valid final primary. Keep B01 separate and preserve either outcome; no pooling
or uncertainty analysis is required before applying B02's own unchanged reading rule.
The historical fixed-half+1.56546875/-4.293046875 observations are different-law context,
not learned-gate replications. Tuned same-information headroom remains absent.

## L0 technical acceptance, execution and budget

Owned checkout `C:/Projects/HMASD-worktrees/codex-vap-folr`, branch `codex/vap-folr`,
starting clean HEAD `8da607b4b7fb415b4212e0e20d74f9dc9c20a32e`. Own this card,
intake/E0/summary, owner record, exact commands, execution and collection/cleanup.
Source and tests are unchanged. Acceptance compares declared source bytes against
the accepted B01 surface and checks fresh identities, paths, committed commands and
actual execution/publication. Reuse B01's independent high-risk review and all10 accepted
focused cases; no new high-risk change or repeated passing check is commissioned.
Engineering Scope Spec §4: this object needs none; no new machinery is added.

Run on configured wsl_4070 in an exact-source detached worktree, CPU FP32, Torch
compute/inter-op threads1/1, `/home/wu/.venvs/hmasd/bin/python`. Linux native publication
is required; no Windows result fallback is declared. Commit/push source, card and exact
commands before launch. For EACH arm, use destination-adjacent memory admission with
both physical/effective availability >=4GiB immediately joined by && to the exact runner,
before its scientific root/RNG/models. Detached `/usr/local/bin/agent-task` owns execution.

Fresh caps:1800s EACH complete arm,3600s native sum,300s invoked support,3900s complete.
Whole native chains include admission/startup/imports, initialization, all learning,
final evaluation, checkpoint/publication and exit. Support includes invoked preparation,
binding checks, staging, Monitor, collection/readback/reduction, publication/integration
and preservation/cleanup, counted once; unmeasured terms stay unknown. No cap transfer.
The same-recipe B01 whole835.33s RETAIN/867.79s LEARNED_EVENT are per-arm planning
anchors below1800s, not new timings or guaranteed forecasts. Current wall/RSS and full
support are unknown until measured; no timing pilot or cost experiment is needed.
Failure preserves trustworthy partial facts and stops the dependent sequence, without
replacement, altered source/device, shortened training, evaluation top-up or retry.

After each accepted handle, send MONITOR_ADD directly to the live primary Monitor
`01a087e5-2044-7301-abb6-7a1709a98197`; dispatch and adoption are distinct facts.
Stop routine polling and return pending collection. Monitor reports terminal facts to
Root, which resumes this DM. Collection checks both exit-zero complete summaries,
source/arm/seeds/counts,128 finite returns and consistent means, checkpoint arm/update/
finite gate and optimizer/target inclusion before the primary helper. No model rollout
or additional optimization is needed for readback. Full intake and Chinese brief end
the scientific unit; preserve unique evidence before exact owned cleanup and retain
the shared authoring checkout. Old policy-blocked B01 duplicates do not gate this pair.
Before each Root-action native final, publish artifacts and send exactly one
HMASD_ROOT_HANDOFF to relay `01a08456-2cf3-7f02-8595-42d84ba41a4c`, recording delivery.

## Scientific grounding and limits

Reuse current Evidence Spec §§4,11.3-11.4,11.8-11.10 and FOUNDATIONS §§2-4,6/empirical
topic. Concrete assumption: repeated same-information package training can reveal
recurrence despite adaptive null gates; one new pair changes observed evidence, not
training-population certainty. Current specifications and scientific readings match
the accepted version. Verified CAMA MARL-0409 pp2-3,16-17 (SHA256
`ee9d7b6adc209780a1bb0ad95d73332e9fe4456bfe7ed738926510f70448b20b`) supports the
recurrent legal null and host reward scale, not event-retention causality. No new
mechanism/comparator or unresolved source claim requires another literature retrieval.
