# Post-A05 alternatives — read-only source feasibility

This is preparation for the DM's Direction question, not an A05 extension, card,
option selection or implementation authorization. No source edit, model load,
autograd, helper, test, native episode or new result was performed. Scope: none.

Pins: current main read at 5f1ec0cc8dc6132557877d967e20ffca36cdb84d (AGENTS and
MARL_RUNTIME_ENGINEERING_SPEC, plus accepted A05 intake). Source read in CM at
a27991f88; the relevant R06 directory, direction study/path modules and A03 runner
have no diff to that main pin. A05's executed source is d3884812a; four protected
R06 surfaces remain818b2566. Historical source references below use these unchanged
bytes, not an assumed new implementation. All paths below are repository-relative.

## What the accepted evidence does and does not supply

A03 intake: ground host restores inputs and299 incumbent service ticks but four
intents have certificate0 and zero legal transfer. A04 intake: all four recorded
calls fail both Mahalanobis and q95 while other reconstructed predicates pass;
Mahalanobis1056.9–6694.0 is far above5.99. Four origins are one trajectory, not seeds.
A05 accepted intake: synthetic actual boundary is raw, Cholesky absent from its
synthetic training-head scalar with connected positive control, and linked helper
inputs can change q95. No A05 output measures a changed real origin, calibration,
old loss-mask support or improved transfer. B01 C04 remains valid FTS-B0, with
three seeds and zero usable trigger support; source value remains unidentified.

## Exact existing chain and reusable consumers

Under `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/`:

- `production_training_engine.py:54` heads and `:66` training_heads expose different
  tensors. Formal training uses the latter through replay at:539–544. The objective
  at:577–598 contains mean MSE, link Gaussian term, missingness BCE and service BCE
  with logits, with effective0.025 coefficient each. There is no direct Cholesky or
  prediction-covariance objective/label in this chain. Link sigma is a separate head,
  not prediction covariance. Shared hidden representations can still change.
- `production_recurrent_trainer.py:285` step_rows uses normal recurrent preparation
  and one batched forward; :343–360 maps owner active2*owner and standby shadow
  2*(1-owner)+1 to means/covariances. Cholesky diagonal is log1p(exp(raw))+1e-3,
  covariance lower@lower.T+1e-4I, then native binary64. Service-Q passes raw from
  standby shadow. Actor Welford normalization is an input transform, not an inverse
  prediction-coordinate transform. No covariance calibration follows from positivity.
- Native `native/rbhr_r06_production_backend.cpp:356–358` predictive_q95 clamps
  probabilities; mahalanobis_position compares two mean blocks using summed position
  covariance; native_origin_certificate combines dm<=5.99, q95>=0.60, support and
  physical/action predicates. `:481` stores the actual certificate in an emitted
  intent. `:488` computes ordinary packet service. Snapshot serialization at:478
  also consumes prediction mean/covariance: changing covariance has more than one
  downstream consumer.
- Native `:731–746` passive_labels_one first steps a private future copy for target,
  links, missing and next_mask. q_copy_index is standby shadow. q_mask stays0 unless
  the explicit source/snapshot/readiness/battery/time/separation eligibility holds.
  When eligible, a private clone holds actions for two ticks, explicitly changes
  owner/promotes state, then records20 service labels. These are the existing
  supervised counterfactual labels, not evidence of an ordinary legal transfer.
- `production_backend.py:792–803` calls real C++ passive_labels_batch; native:837
  loops lanes within that one batch call. `production_recurrent_trainer.py:406–455`
  collect_update produces32×128 transitions and requests labels before real step;
  `:459–517` preserves native masks, q-copy identity, owners, recurrent initial
  state, normalized/raw observations and behavior probabilities in fragments.

## Alternative (a): qualify a prospectively changed interface

Existing reusable ordinary path is `experiments/candidates/degraded_incumbent_shadow_handover/`
`first_trigger_source_scout_b01/path_a03.py:197–278`: one checkpoint-loaded policy,
real prepare/step_rows/complete, native promotion, full trace and PathCounts. Its
`:128–171` distinguishes legal transfer, promoted sender and post-transfer packet
service from incumbent or stale/other-packet service. `native_a03.py:13–22` selects
the actual literal or declared ground-endpoint library; PointBatch is width1 with
explicit per-state library ownership. No synthetic bypass is needed to observe
ordinary consequences, but a prospective treatment/comparator must first be fixed.

The retained seed11 checkpoint has recorded SHA256
0020137d98e23f06a71048daf5906d7835545fd38cc8a1399bbeee15e11df4fa,2070711bytes.
A03 collection records the full39,140,340byte trace and exact local/remote roots.
This note relies on that accepted identity record; it does not load or newly check
the payload. Existing traces provide baseline facts, not a fresh paired treatment.

Applying sigmoid at the service boundary preserves learner/checkpoint bytes but
changes real protocol input, hence is a scientific treatment, not pure reporting.
Changing covariance mapping, substituting fixed covariance, adding a calibration
law or changing thresholds is another scientific choice; no unique calibrated law
is implied by A05. A link-only change cannot logically cure the unchanged failed
Mahalanobis predicate at a fixed recorded boundary. An actual new trajectory may
also change state through messages/actions, so that fixed-boundary fact cannot be
promoted into a complete new-trajectory prediction. Joint changes confound their
separate contributions unless the intended estimand explicitly accepts that package.
Native consequence observation is feasible in existing code, but success is not
demonstrated; forced transfer or borrowed passive-label clone is not a substitute.

## Alternative (b): observe actual loss/mask support before correction

Native masks and fragments are explicit reusable inputs if the exact needed data
were retained. `first_trigger_source_scout_b01/study.py:244–311` collects fragments
and immediately applies64 updates, then returns summary and final checkpoint. It
does not publish full fragments or per-head historical gradients/mask counts in
that path. A03 trace is deterministic evaluation, not those training fragments.
No complete historical fragment artifact inventory was verified here; availability
remains a concrete gap, not permission to fabricate/reconstruct missing tensors.

`production_training.py:58–78` PersistentTrainer.run_update invokes the retained
full update. `production_training_engine.py:475–629` constructs model AND AdamW,
restores state, performs4epochs×8minibatches, backward/clipping/optimizer.step and
serializes a new checkpoint. Its dry/test labels do not make invocation read-only.
`arm_mask_inventory` and synthetic fixtures also cannot report historical support.

A future observation must distinguish static loss existence, observed native mask
coverage, actual masked scalar gradient connection, and realized parameter movement.
Loading recorded fragments for one fixed loss/backward without stepping needs a
prospective observation boundary; calling the whole existing update is extra learner
work. If fragments are absent, generating fresh training data or replaying training
is new exposure requiring explicit input/checkpoint/RNG/exposure/stop definition.
Current A05 scalar supplies neither of those data. Adding covariance loss/labels
or altering masks changes training meaning and does not belong to observation-only.

## Alternative (c), costs and current implementation constraints

The node may judge neither next investment justified from current evidence. Source
facts do not decide that choice. No native qualification, covariance calibration,
historical gradient coverage or fresh matched generic headroom is established.

Measured scopes: A03 complete pair runner3.969379171s, supervisor5s; A04 data-only
runner0.292995485s; A05 runner2.233209421s/external2.40s plus separate smoke3.29s.
These are different work types; A05 allowance25.5s was not measured. A new changed
interface full trajectory has no measured projection here; neither does a full
historical-fragment collection/replay/gradient observation. Existing32lane collection
has hidden label work: every label request steps a future copy and eligible rows
add two-delay plus up-to20 clone steps. Plain transition counts omit this work.

Torch policy/replay operates tensor batches; recurrent time remains sequential.
Native batch exports loop independent lanes in C++; width1 A03 and width2 A05 are
their actual observed configurations, not proof of parallel scaling. Current main
runtime spec permits ordinary batching and a named fixed native team within a
defined task, but does not override card threads/precision/RNG or confer a new N3
budget. It requires full invocation/cost scopes and applies investigation thresholds,
not a new launch gate. Any new observation must state its own complete workload
and projection; no speculative core-count division or inherited A05 exception.

No option is selected, no new limit proposed and no implementation started.
