# Preflight rejection fixture — not a real round

This directory exists so `tests/review_round_contract_test.ps1` can prove the
round preflight rejects a question that carries no `## Evidence to read`
allow-list. It is not science, was never sent, and must keep NOT carrying that
section. The `00000000_` prefix keeps it sorted apart from real rounds.

A question body with no evidence allow-list follows; the preflight must refuse
to send it.
