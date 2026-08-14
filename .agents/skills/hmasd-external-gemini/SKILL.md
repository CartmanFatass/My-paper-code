---
name: hmasd-external-gemini
description: Thin provider adapter for one already frozen HMASD Gemini divergent-innovation request. Use only from the registered External Gemini transport leaf; all send, incident, archive, cleanup, exact-one, and no-resend mechanics come from the canonical hmasd-agentify-transport skill and manual.
---

# HMASD External Gemini adapter

Use `.agents/skills/hmasd-agentify-transport/SKILL.md` and
`docs/project/AGENTIFY_TRANSPORT_INSTRUCTIONS.md` as the sole transport
procedure and result schema. This adapter adds only:

```text
provider=gemini
root=https://gemini.google.com/app
strict_model=Gemini 3.1 Pro extended
visible_model=selected 3.1 Pro
visible_mode=selected Extended thinking
scientific_use=divergent_innovation_only
```

Reject convergence, causal-closure, result/code acceptance, portfolio selection,
or replacement of the direction's ChatGPT External Pro conversation. Preserve
separate question, conversation, archive and EM intake.

Do not define another `ERROR`, terminal, retry, archive, tab, or status protocol.
Return the canonical `COMPLETE|INCIDENT_REPORTED` transport result as mechanical
evidence only. A later send after `SEND_NOT_COMMITTED` is an EM-owned prospective
decision allowed only when the prior record proves zero provider turns, no
conversation identity and no active generation. No fixed attempt count can
pause the scientific direction. Any ambiguous commitment or existing provider
turn/identity is permanently observe-only and must never be resent.
