# Pro research answers in natural language

Authority: OWNER_DIRECT, 2026-09-05. The owner requested:

> 以及transport中我发现pro6的回复携带大量的如id等信息 我们应该保证transport发送的prompt得到的是自然语言, 不要涉及到这些id 等envlope类的信息

Root implements this presentation change directly. New provider-visible prompt bodies
use prose for the question, requested conclusion, claim ceiling, constraints and evidence
list. They do not include request IDs, routing, conversation bindings or machine envelopes,
and request natural-language answers instead of echoed identifiers or status blocks.
Reproducible source paths and fixed source versions stay in the evidence list.

Internal HANDOFF/registry/transport facts retain identifiers and hashes. The existing
response-identity check now compares the independently recorded provider conversation and
user/assistant pair with the captured node. Missing DOM identities require documented
manual pairing; a mismatched capture is re-inspected without another Send. Accepted prompts
and exact archived responses remain historical evidence and are not reformatted or resent.

Changed surfaces: Prompt Author renderer and SKILL; Transport response identity helper,
SKILL and state-schema; their existing focused tests. No research object, evidence class,
provider selection, dispatch destination, source-access scope or send semantics changed.

Validation: the Python 3.10 research interpreter cannot collect these existing control-plane
tests because their existing transport validator imports Python 3.11 `tomllib`. Retried
with the installed Python 3.11.9 control-plane interpreter: both focused skill suites passed,
93 tests in 1.41 seconds. No dependency installation or experiment was performed.

scope: none
