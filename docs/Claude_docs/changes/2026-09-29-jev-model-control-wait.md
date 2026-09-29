# 2026-09-29 — Jev Pro transport: bounded wait for the composer's model control

**Change.** `tools/pro_transport/jev_send.py` `command_send`: after the message box appears (and the
fixed 2 s pause), poll `MODEL_CONTROL_PRESENT` (an `[aria-haspopup="menu"]` element inside the
composer form) for up to 30 s before Jev's first observation. `ensure_effort`'s proof is unchanged
and still decides; a missing control after 30 s raises the same pre-send failure as before.
`tests/skills/test_jev_transport.py`: the send-path browser stub answers the new poll (94 passed).

**Why.** Two sends of `replan-timing-next-question` (key `hmasd:fcef9c02…`, same conversation as the
earlier round-boundary questions) failed pre-send with "no reasoning-effort control in the composer".
A timing probe on that three-turn conversation showed the composer at 2.4 s and the model trigger
(`选择 ChatGPT 模型`, text `Pro`) only at ≈ 5.6 s after navigation, i.e. ≈ 3 s after the box; the driver
observed at 2 s. Earlier sends on shorter threads fell inside the pause.

**Scope.** Control-plane tool only; no research code, record type, role or policy change. Traceable
in Git (commit on main, 2026-09-29). Owner's lifted control-plane restriction (2026-09-15) applies.
