# Is REPLAY_TOLERANCE = 1e-6 Device- And Shape-Portable In float32?

Sent to GPT-5.6 Pro on 2026-07-21, before any formal run. This is a
pre-registration engineering question about a registered constant, not a
post-result adjustment. No result has been observed.

---

```
Use the GitHub connector on private repository CartmanFatass/My-paper-code,
branch `aggressive`. The registered constant is REPLAY_TOLERANCE = 1e-6 in
ha_ctse_process/noncalendar_commitment_testbed.py; it is enforced in
validate_replay in ha_ctse_process/event_held_commitment_link.py and emitted in
registered_contract().

CLAIM UNDER TEST. The registered replay tolerance appears to be calibrated to
one device and one batch width rather than to float32 arithmetic, and it is
currently blocking two unrelated engineering improvements.

EVIDENCE 1 - THE SAME COMPUTATION EXCEEDS IT ON CPU.
Collecting and replaying the same trajectory entirely on CPU, with no code
change, yields:

  categorical_component   1.19e-07
  mark_component          9.54e-07
  event_joint             1.91e-06     <-- exceeds 1e-6

On CUDA the identical code path yields event_joint at roughly 4.8e-07. The
difference is summation order and vectorization, not a semantic difference:
mark_component is a sum over 8 transformed-normal components and event_joint
adds the categorical term on top, so the joint accumulates the component error.

EVIDENCE 2 - THE SAME QUANTITY IS MARGINAL UNDER A BATCH-WIDTH CHANGE.
Independently, an internal review reconstructing a trajectory at width 1 against
a factual collection at the registered width 16 measured, on CUDA:

  observations             0
  hidden_before/after      1.79e-07
  event_inputs             2.68e-07
  old_log_probs            1.79e-07 - 2.38e-07
  event_old_joint_logp     7.15e-07 - 1.19e-06   <-- exceeds 1e-6 on one episode

So event_joint sits within a factor of about two of the tolerance under any
change to reduction order, whether that change comes from the device or from the
batch width. Every other recorded quantity is an order of magnitude below it.

WHAT IT BLOCKS.

(a) Device choice. This workload is launch-bound, not compute-bound: the model
    has 14,980 base parameters and the recurrent replay performs roughly 480
    sequential tiny kernel calls per epoch at batch 16. Measured on the target
    machine, CPU single-thread is 2.70x faster than CUDA on replay and 2.90x
    faster on collection. torch.compile gives no speedup (1.00x). With 20 cores
    and one single-thread worker per (arm, replicate) cell, the 15 cells run
    concurrently rather than at the roughly 2.0x ceiling measured for concurrent
    CUDA processes on one card. The projected effect on registered formal
    training is hours to tens of minutes. The CPU path is blocked solely by this
    constant.

(b) Fork prefix reconstruction. The counterfactual fork engine reconstructs the
    pre-fork prefix at width 1 while the factual collection ran at width 16. The
    clean fix is to reconstruct at the factual width, which makes the
    reconstruction bitwise exact. Whether the current width-1 reconstruction is
    admissible at all depends on the same constant.

QUESTIONS.

1. Is 1e-6 defensible as a device- and width-portable bound for a float32 joint
   log-likelihood that sums 8 transformed-normal components plus a categorical
   term, or was it implicitly calibrated on one device at one width? If it is
   too tight, what bound is principled for this quantity in float32, and how
   should it be justified rather than fitted to the observed numbers?

2. Should the tolerance be one scalar, or per-factor? The categorical and
   per-component mark errors are an order of magnitude below the joint, because
   the joint is a sum of them. A single scalar applied to a derived quantity
   with more accumulated terms seems to be what creates the marginality.

3. Does relaxing this constant weaken any scientific guarantee? Our reading is
   that replay exactness protects the PPO importance ratio and the event
   likelihood factorization, and that a bound at the level of float32
   accumulation noise for a summed log-likelihood still protects both. We would
   rather be told we are wrong about that now than discover it later.

4. If the constant changes, does the checkpoint contract need to change with it?
   load_checkpoint rejects on registered_contract() inequality, and the
   thresholds dict carries the tolerance, so any change invalidates checkpoints
   written under the old value. Nothing is trained yet, so the cost is zero
   today and nonzero after training starts.

CONSTRAINT. No result has been observed. We are asking whether a registered
numerical constant is correctly specified, not seeking room to pass a gate.
```
