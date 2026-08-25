---
name: hmasd-portfolio-task
description: Bootstrap or resume the independent HMASD Portfolio top-level task for cross-direction decisions.
---

# HMASD Portfolio Task

Use only in a user-facing Portfolio task. Recommended model: GPT-5.6 Sol at
max reasoning for material decisions.

At start or resume:

1. Set logical identity Portfolio, load `hmasd-portfolio-control`, and
   reconcile once.
2. Use responsibility-relevant genuine direct leaves when useful; every child
   is a leaf and may not delegate.
3. Write Portfolio authorities through their existing CAS contract. Send
   follow-on work as an immutable Work Packet with authority refs, not a
   separate Decision Packet protocol. Delivery may repeat the same `work_id`;
   receivers intake it idempotently.
4. Portfolio does not own task runtime. Root creates or reuses EM/CM when the
   durable Portfolio decision requires it.
5. Stop after one bounded decision; do not poll.
