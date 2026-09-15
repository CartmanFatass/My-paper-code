# Pre-Send nonacceptance record

Request `2026-09-14-folr-current-increment-b01-result-plan-review-01` on binding `em:vap_folr_core:convergence` first returned the exact strict-tool outcome `chatgpt_target_menu_open_unconfirmed`.

The post-failure registry observation was `state=DIRECTION_VERIFIED`, `native_state=READY_UNSENT`, with `operation=null`, `send_evidence=null`, and `send_click_count=null`; no provider user or assistant ID and no accepted effect were observed. Accordingly, the first call is recorded as a strict-call attempt with provider Send effect **not persisted**, rather than reconstructing an unobserved provider-side boolean.

After one read-only status reconciliation (`blocked=false`, prompt and Send visible, no active query, dedicated tab non-protected and strict-transport eligible), the exact same request was run once with unchanged prompt hash, conversation, model/effort, response path, and idempotency key. It produced operation `6aa65ecf-2271-468e-aeff-9ebb755a35d6`, user `6e0b45e0-b208-4711-a4c2-e5e5f9bdd93d`, assistant `6106e80a-ebe1-41a6-a3ab-4192e84a019e`, and the full response archive recorded in the sibling transport facts.

`collaboration.send_message` was unavailable; the actual parent delivery method was direct `native_final` to `/root/dm_folr_resume_20260914`.
