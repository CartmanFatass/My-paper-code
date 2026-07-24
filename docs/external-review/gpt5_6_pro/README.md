# GPT-5.6 Pro Research Exchange

This directory stores the exact material exchanged with GPT-5.6 Pro. Each
consultation has one dated folder containing a review entry, the submitted
question/evidence, the raw response, and the later PM reconciliation or
mechanical intake.
The preferred transfer is direct read access to the GitHub repository;
legacy ZIP packages are not required for new consultations.

Current web transport runs under `$hmasd-review-round` with browser work through
the `claude-in-chrome` skill, using the exact conversation registered in
`docs/external-review/REVIEWER_CONVERSATIONS.json`. It executes in the Project
Manager directly or in the registered `hmasd-review-exchanger` subagent. Either
inspects for an accepted matching fence before any submission, archives the
completed raw exactly, and returns transport facts to the Project Manager
without scientific interpretation. Create no other exchange task or relay.

Do not summarize over a missing raw response. Git and the registered
round/commit/question fence define identity.
