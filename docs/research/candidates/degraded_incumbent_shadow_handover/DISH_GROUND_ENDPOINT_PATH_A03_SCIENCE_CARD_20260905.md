Claim: One paired ordinary native episode can locate how a declared ground-terminal geometry changes the observation, SOURCE, handover and service path at the original first B01 coordinate.
Binding MARL structure: systems / information flow. Two partially observing physical agents require actual shared SOURCE and exchanged protocol messages before a proposed owner transfer can affect native service.

# DISH ground-endpoint native path A03 — science card

Date: 2026-09-05; object `DISH-GROUND-ENDPOINT-PATH-A03`, **A / RECON**.
DM `/root/dm_amx_n3_continue`; parent decision **PRO_FINAL CONTINUE**, recorded in
`DISH_A02_HOST_CONVERGENCE_PRO_INTAKE_20260905.md`. Object selection is recorded in
`DISH_GROUND_ENDPOINT_PATH_A03_SELECTION_INTAKE_20260905.md` before implementation/output.

## 1. Question, class and non-goals

Does one explicitly defined ground-terminal host support the ordinary causal chain from
permitted observation and actual received SOURCE, through snapshot/readiness and legal
policy proposals, to a native owner/action transition and service? Compare with the
literal host on the same original coordinate and fixed retained controller. A03 is an
outcome-informed diagnostic following A01/A02, not independent confirmation. It measures
one fixture/controller pair; successful link geometry alone does not qualify the chain.

The ceiling is bounded host-path reconstruction. No new training, source intervention,
RETAIN/COPY/SHADOW effect, generic comparator competence, headroom, physical-realism claim,
family recast, R02 reopening or Portfolio change is in scope. Historical B01 FTS-B0 and
A01/A02 remain valid under their literal host. The new host changes the host-specific
information distribution and estimand; its observations cannot repair or replace B01.

Live explanations are: the endpoint convention obstructs a necessary input path; ordinary
camera/SOURCE access can recover while learned proposals or protocol timing remain a gap;
the fixed policy's motion loses useful geometry; or a complete legal chain is available
on this fixture. Gaussian radio noise and terrain can still block actual arrivals. A
changed hidden state without a competent action/native consequence is not mechanism value.

## 2. The one prospective host definition

Name the new host **GROUND-TERMINAL-LINEAR-CLEARANCE-A03**. It represents a responder
whose co-located visual marker and SOURCE antenna are two metres above its local ground.
The two-metre value describes this terminal; it is not fitted to an observed margin,
readiness, source-arm result or desired success count. No alternate height or taper is run.

Let `H_r(x,y)=H(x,r*y)` be the unchanged inherited terrain, `g_xy(t)` the unchanged route,
and `q` the fraction along a ray **from the ground terminal toward its UAV endpoint**.

- SOURCE emitter and camera target world height are both `H_r(g_x,g_y)+2.0` metres.
- Each UAV remains at `z=90.0` in the existing world datum; base stays `(-600,0,20)`.
  UAV altitude does not follow terrain. No height is clamped to ensure a clear path;
  terrain may rise above an endpoint. Ground height is exogenous terrain following,
  with no new vertical vehicle controller or energy model.
- The same 127 interior points, `q=j/128`, are used on ground-linked rays. A ground-to-UAV
  radio sample is clear iff `z(q)>H_r(x(q),y(q))+8*q`; a camera sample is clear iff
  `z(q)>H_r(x(q),y(q))+5*q`. A camera evaluated in the reverse direction uses `q=1-u`
  for its native UAV-to-ground interpolation fraction `u`. The inequalities stay strict.
- This linearly interpolates the extra terrain clearance from zero at the ground hardware
  to the original radio/camera clearance at the airborne endpoint. It introduces no
  terminal exemption radius, clipping or post hoc choice of favourable samples.
- Actual endpoint heights enter all ground-linked three-dimensional distances; the
  camera's 500-metre range and the radio distance law remain unchanged. The camera
  calculation must not retain the literal host's hard-coded `90^2` vertical distance.
- The TARGET_VISUAL_MASK camera ray uses the same actual co-located visual target
  `H_r(g_x,g_y)+2` in the new host. Its prism bounds and j=0..128 sampler remain the
  literal ones; its intersection may change because the endpoint changed. It must
  not silently keep an unrelated z=0 target. The literal host retains its z=0 mask
  endpoint. The relay-mask ray keeps the unchanged UAV/base endpoints.
- Every other hop retains its literal constant terrain clearance. Terrain, base/UAV
  heights, radio noise and 6-dB threshold, 35-dB obstruction penalty, all prism geometry,
  masks, source/payload timing, dynamics and protocol equations remain unchanged.

The **literal comparator** keeps ground `z=0`, UAV `z=90`, base `z=20`, constant
camera/radio clearances `5/8`, and all its existing native equations. It is the strongest
matching counterfactual for this host-law question because controller, available-input
rules and resources are identical; no artificial controller weakness is introduced.
The combined ground-height/clearance convention is one declared host treatment. A03
does not attribute its effect separately to antenna height versus clearance taper.

## 3. Fixed fixture, controller and protected semantics

Use `seed_master(11)` and exactly `panel()[0]` / `_reset_row` from accepted B01:
block 0, TARGET_VISUAL_MASK, K8, speed 4, within-speed slot 0, initial owner U0,
reflection +1, normal `test_mode=0`, masks enabled. The original starting horizontal
coordinates are ground `(-168,-120)`, U0 `(-88,-240)`, U1 `(-248,0)`. Do not select
another accepted slot or coordinate after looking at either host. Recreate both resets
from the same original master/address law; the host label is not an RNG substream.

Use the retained seed-11 STRUCTURED checkpoint from B01 source
`e0541d0cb3e9e63731c72f4dacb10b44d268fd39`, 2,070,711 bytes, SHA256
`0020137d98e23f06a71048daf5906d7835545fd38cc8a1399bbeee15e11df4fa`.
Accepted A01/A02 assembly is `06c05c1f52736d7f274e1e6491611b8d7d528a90`.
CM verifies this retained input before launch without adding a runner provenance gate.

For each host instantiate the existing `BatchedRecurrentPolicy(arm="STRUCTURED")`
from that checkpoint with its retained normalization and fresh zero recurrent state.
Use the existing deterministic sampler, policy thresholds, learned prediction/covariance/
service heads and ordinary proposal rule. No action uses ground truth, packet bodies
that the actor interface treats as opaque, future route, future noise or the other host's
trajectory. Actor features, snapshot inputs, role indexing and Welford numerical law
remain unchanged. Different permitted observations can cause different actions.

Each live tick follows normal preparation/arrivals, recurrent preparation, exactly one
`step_rows(... deterministic=True, recurrent_prepared=True)`, normal native completion,
then normal policy promotion synchronization. **Continue after any application-valid
boundary**, including its ordinary legal action and consequences. A01's early break at
the first valid boundary must not be reused. No source clone/fork or forced CAS is called.

The physical entities U0/U1, initial incumbent, current owner, standby and four recurrent
copies remain distinct. The degradation stays on the designated physical incumbent
after any ownership change. External K8 renewal, primitive time, reservation costs,
lineage/sequence, readiness/version checks, actuator mapping and terminal semantics are
unchanged. There is no join/leave/rejoin, roster replacement, new optimizer exposure or
new partner co-adaptation. The same SHADOW-trained retained controller is used on both
hosts; its training provenance does not establish superiority of shadow preparation.

## 4. Required observations and estimands

Keep one per-tick trace in the existing runtime output root and a compact result summary.
Instrumentation only copies existing values; it does not set state, rerun physics or
advance the learner. Record counts and first occurrence ticks for each stage, as well
as the following actual values at the stated boundaries:

1. **Observation to representation:** both actual camera flags; permitted raw actor
   observations and normalized actor inputs, snapshot delivery mask/input, and ordinary
   filter means/covariances. A pure normalization read is allowed; no extra Welford
   update or policy forward. These are inputs to the unchanged recurrent computation,
   not a privileged reconstruction substituted for the actor's inputs.
2. **SOURCE to protocol:** actual send margins for all six hops; before-prepare pending
   source tick/sequence/margins and both receiver sequence/existence/ticks; after-prepare
   receiver values. Count completed SOURCE buffer arrivals/adoptions from the actual
   receiver state update, separately from `send_margin>=6`. Record source age and common
   SOURCE, snapshot/readiness delivery and acceptance, version readiness and lineage
   locks. Source payload values remain opaque to the actor; diagnostic access grants
   the controller no additional information.
3. **Proposal to legal action:** prepare/commit outputs, ordinary renewal, preparation
   latch, existing origin-valid/intent-certificate values and actual emitted intent;
   owner/actuator owner/service epoch, application reason/CAS and invalid-commit delta;
   raw and actually held/applied motion commands. A failed proposal is retained.
4. **Action to native consequence:** actual relay emission, completed base-buffer
   arrival and source/relay age, native service indicator/count, batteries/energy,
   separation and terminal/failure event. Record any service following a legal transfer
   separately from service before a transfer. Carry the actual pending relay's sender
   and emission tick through each completed base adoption. Count a service tick as a
   **promoted-owner consequence** only when its actual adopted base packet was relayed
   by the promoted physical owner at or after the legal application tick. Already
   in-flight old-owner packets, including service at the CAS tick, do not meet this
   consequence criterion. No service is inferred from a margin.

The estimands are the candidate-minus-literal stage counts and native service ticks over
the complete bounded trajectories, plus which stage each host actually reaches. Both
denominators and stopping times are shown; do not compare unequal live counts as equal
exposure or silently discard terminal observations. Report literal support too, even if
its outcomes differ from the prediction. A single pair gives no population estimate.

## 5. Reading rule, MEI, headroom and predictions

Apply these branches in order to the **new host**, with the literal comparison printed
alongside rather than used as a favourable-outcome admission rule:

1. If either camera has no observed available tick, either receiver has no completed
   SOURCE adoption, or no common SOURCE is observed: **A03-ACCESS-NOT-RESTORED**.
2. Otherwise, if there is no delivered snapshot, no delivered readiness, no ordinary
   application-valid boundary or no applied legal owner/actuator transfer:
   **A03-DOWNSTREAM-STAGE-GAP**, naming every absent stage and the earliest absent stage.
3. Otherwise, if no valid native service occurs from an actually adopted relay emitted
   by the promoted owner at or after the legal application:
   **A03-CONSEQUENCE-NOT-REACHED**.
4. Otherwise: **A03-BOUNDED-PATH-QUALIFIED**, only for this fixture/controller and host.

Always publish service counts even when an earlier branch controls. Partial restoration
is informative; a stage gap is not general host impossibility or policy incapacity.
Missing required trace fields, wrong host/controller, uncompleted work at the time cap
or a scientific-semantic implementation breach makes an incomplete attempt, not one
of those scientific branches. CM reproduces a failure before assigning its cause.

MEI: one actually observed event at each necessary stage, including one service tick
(0.1 seconds) from the promoted owner's post-application relay, is the diagnostic
resolution of this path
qualification. Candidate-minus-literal service of at least one tick is a descriptive
host effect of interest, not a requirement for branch 4. Zero differences remain
inside that descriptive MEI; negative differences are reported without relabelling a
complete trace. The B01 five-tick source-effect MEI remains unestimated.

No matched upper-versus-tuned-generic headroom exists for either this new host or the
current B01 learner. The retained policy is reused because its observation/action/
information and no-update budget match both arms; it is not a tuned baseline for A03.

DM predicts camera and actual SOURCE support will recover on at least part of the new
trace, but **A03-DOWNSTREAM-STAGE-GAP** is more likely than full qualification because
the retained policy and temporal readiness conditions have not shown downstream
competence. Predict literal SOURCE/common-source and service remain absent. Owner:
`not taken (unattended)`; this is a diagnostic rung in the existing B01 ladder, not a
duplicate ladder-opening prediction item. At intake score both subpredictions.

Interpretation: restored inputs with a downstream gap recommends only the smallest
named stage diagnosis; full qualification makes a separately carded future B question
possible, without authorizing it here. No restoration keeps this host's access unresolved.
An inside-MEI or adverse service contrast never becomes evidence against source value.

## 6. Exposure, cost, route and stop

One seed, one original fixture, **two hosts**, at most **1,200 completed primitive ticks
per host**. Stop a host immediately after native terminal or tick 1,200, whichever is
first; record whether this was a live completion or terminal. No padded continuation,
restart, expanded panel, alternate controller, height sweep or downstream experiment.

Machine-generated exposure: two checkpoint-loaded model/policy initializations (one per
host), zero new training transitions, learner updates and optimizer initializations/steps;
at most 2,400 prepared/complete native evaluation ticks. Record actual counts separately.
Measure before/after parameter norm and L2/relative displacement per host, expected exactly
zero against retained norm 41.78517869974931. Inherited B01 exposure remains 262,144
training transitions, 64 updates, 2,048 optimizer steps and relative movement
0.42465718774783356 against initial norm 38.19731474061207; it is not new A03 compute.

Portable CPU evaluation: native float64 and retained Torch FP32, one Torch thread,
unchanged RNG/checkpoint/normalization semantics; no device or operating-system estimand.
Use current `.codex/hmasd-compute.toml` remote-first `wsl_4070`, exact committed/pushed
bytes in a detached worktree, existing `agent-task`, one ordered pair invocation.
Immediately before the invocation creates a native master/model/scientific output,
actual-node `admit-memory --out <receipt> && <runner>` must pass both physical and
effective available memory >=4 GiB. The summary records the receipt; no duplicate
in-run validator or new gate is requested.

The runner's prospective **per-host** cost law is
`1.5 * (20 s build/load + 4 * 1200 * 0.006038872852291206 s/tick + 10 s publication)`
= **88.47988453649668 seconds**, below a **300-second per-host cap**; the ordered
pair projection is **176.95976907299337 seconds**, below its **600-second total cap**.
The empirical rate is A01's complete 19,200-tick retained-controller run, with a fourfold
allowance for the wider trace; A02's point-only time is not an episode-cost estimate.
Charge build/load and output once per host in this conservative projection even when
shared. Print `project-cost` before launch, and actual elapsed wall/peak RSS and elapsed
per completed tick afterwards, including the scope/timing of publication overhead.
Missing resource telemetry is `resources_unmeasured`, not a path-validity veto.

## 7. Bounded implementation and handoff

**Engineering-scope section 4 declaration: this object needs none of the default-prohibited
machinery.** A small directly selected native variant and trace are measurement code,
not a host registry, framework, resume layer or runtime provenance validator. Preserve
the existing literal default, native ABI, checkpoint and all old B01/A01/A02 meanings.
No generic observer, forced fixture eligibility, hashes as runtime gates, extra telemetry,
capacity gate, C contract or Pro reapproval is requested.

CM owns only the small prospective compile seam in
`experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/native/rbhr_r06_production_backend.cpp`,
new A03-specific measurement code under the existing
`experiments/candidates/degraded_incumbent_shadow_handover/first_trigger_source_scout_b01/`,
`scripts/run_dish_ground_endpoint_path_a03.py`, its focused tests in the matching B01
research test directory, and technical/evidence documents. Runtime output stays in
`temp/directions/degraded_incumbent_shadow_handover/exp/ground_endpoint_path_a03_20260905/`.
No shared production Python API or old runner edit is authorized. If the existing
module-global native loader would mix hosts, use an A03-local explicit library handle
for the existing typed reset/prepare/complete operations; do not swap a global source
or loader at runtime. DM owns science/card/intake/owner items; Root owns Portfolio/audit.

Stay within 2,000 new non-test lines, 600 runner lines and orchestration <30% of the
non-test diff, with no denominator padding. Return a concrete excess before acceptance.
One focused synthetic/geometry reading check and one real tiny publication smoke after
the change suffice; tests must not run the original A03 fixture outside its admitted
result invocation. Keep ordinary-mode tests separate from legacy forced TEST fixtures.
Commit and push every change immediately. CM performs technical acceptance and gives
the unique accepted handle directly to `/root/tracker_tl_experiments`; the tracker alone
observes/reminds, CM collects, and DM independently applies the rule. No successor is
preauthorized by either technical success or this card.
