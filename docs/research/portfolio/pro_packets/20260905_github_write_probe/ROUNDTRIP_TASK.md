# Owner-authorized link-only roundtrip test

This is the second isolated connectivity test authorized by the owner on2026-09-05:
validate the complete workflow before migration. It is not a research decision.

## Read scope

Use your actual GitHub connector to read this task file and these sources:

- Issue3 body and its existing comment5555607897:
  https://github.com/CartmanFatass/My-paper-code/issues/3#issuecomment-5555607897
- Commit b86b9f71ea22291b3a664249f93a14abaa2a8968, its changed-file list/diff,
  and docs/research/portfolio/collaboration_probe/pro-write-check.md at that commit.
- At commit cd2695866, read .agents/skills/hmasd-scientific-tools/SKILL.md and
  .agents/skills/hmasd-scientific-tools/scripts/summarize_runs.py.

Read no unrelated science or PR2. Report any unavailable source specifically.

## Substantive output

Write a Chinese review of approximately500–800 Chinese characters, using headings
and short paragraphs. Explain what the previous direct-write test establishes,
what the actual run-summary script computes, why evaluation episodes are not
independent training seeds, and what remains unverified about full migration.
Cite the actual file versions and discussion URL. Separate observation from inference.
Do not claim new science, benchmarks or performance results. Include a fenced
example CSV header `task,seed,arm,score` to test literal code formatting.

## Exact write scope

Repository CartmanFatass/My-paper-code. Existing test branch only:
codex/pro-github-write-probe-20260905.
Create only docs/research/portfolio/collaboration_probe/ROUNDTRIP_REVIEW.md there,
in UTF-8, retaining Unicode and Markdown. Parent should be existing test commit
b86b9f71ea22291b3a664249f93a14abaa2a8968 unless your read finds a concurrent change;
in that case report the state rather than overwrite it. Do not edit the earlier
test file, main, any other branch, settings, source or scientific decisions.

Before writing, check whether this target already exists. If so, read and return
its existing link without another write. After a successful write, read it back
through GitHub and append one comment to Issue3 beginning
“Pro 往返验证交付：”, containing its immutable file link and the statement that it
is a connectivity test, not a scientific conclusion. Search for that comment/link
before adding it; do not duplicate it after an uncertain response.

## Notification

Reply in chat with only the immutable file URL, actual commit SHA and comment
permalink, plus a short missing-capability statement if needed. Do not copy the
review into chat. Root will fetch the file directly from GitHub and independently
validate its bytes, meaning, changed paths and source links. Transport must not
create either deliverable on your behalf. No credentials or new services needed.
