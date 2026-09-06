# Overall GitHub delivery cutover

OWNER_DIRECT: “不能整体搬迁吗 似乎已经完成验证了 我们需要整体搬迁 并且transport和起草发送prompt也要做相应的改变”.
The owner authorizes overall cutover now. This supersedes the intermediate
VNFC-first/one-more-intake rollout condition. No workflow Pro review is requested.

All newly authored Root/Portfolio and DM/EM requests default to github_delivery.
The Author entrypoint and renderer now prepare committed TASK + scoped response
branch/path + Issue comment, bind full task SHA, and dispatch a short task link.
Transport reads this route without upload/read-only preambles or text copying and
archives short links; Root/DM retrieves the full original response for existing
scientific intake. Legacy instructions moved to an explicit fallback reference.
New attachment fallback requires explicit mode and reason. Accepted in-flight
requests and historical evidence remain intact; no duplicate provider Send.

Updated root AGENTS, DM role, Author skill/renderer/references, Transport skill and
collaboration workflow. Local checks passed: omitted mode defaults to GitHub,
unpublished task cannot dispatch, missing fallback reason rejected, explicit legacy
fallback retains attachment payload, all role TOMLs parse, git diff --check clean.
Previous normal/duplicate-existing/conflict remote test evidence remains applicable.
No extra scientific test, permission gate, lifecycle change, webhook or service.

This completes configuration and instructions cutover for all new requests. It is
not a claim that every idle provider node has independently executed another test.
Existing running agents receive this change directly; the research heartbeat uses
this current decision rather than older staged-migration notes.
