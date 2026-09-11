# GitHub delivery workflow — owner-direct application

The owner approved completing the workflow and then explicitly instructed:
“这次不再需要pro审阅 得到我的授权饿了”. No Pro review request was sent.
This direct instruction supersedes the proposed Pro review for this change only.
Overall migration still follows the previously authorized validation-first boundary.

Applied: operational delivery/recovery/migration design, root AGENTS, Author skill
and GitHub references, Transport mode guidance, existing renderer scoped delivery
and fixed-commit binding. Default attachment behavior is unchanged. No new scheduler,
GitHub service, experiment gate or blanket Pro source/main/PR authority was added.

Local validation passed with temporary Git repositories: legacy read-only attachment,
new unpublished task isolation, four invalid output-scope cases, existing packet
preservation, changed task bytes rejected, correct immutable task binding and paste
request, duplicate binding rejected, caller-direct no-dispatch preservation. The
first test attempt failed in the test harness because Windows default cp1252 could
not decode Chinese; rerun with explicit UTF-8 passed. No provider Send or external
GitHub write was used for these local checks.

Remote normal path already passed, archived under the GitHub write probe. Live
existing-file recovery and conflicting-target behavior remain untested. The design
specifies isolated cases and a next naturally needed VNFC scientific intake before
broader adoption; no new scientific question is created just for migration.
Current status: workflow and mode implementation applied, overall migration not started.

Affected paths: docs/project/GITHUB_RESEARCH_COLLABORATION.md and its linked design;
AGENTS.md; .agents/skills/hmasd-pro-research-prompt-author/{SKILL.md,references/github-delivery.md,
references/github-connector-contract.md,scripts/render_packet.py};
.agents/skills/hmasd-chatgpt-pro-transport/SKILL.md. Transport validator already accepts
the existing paste-mode request, so it requires no new transport protocol.
