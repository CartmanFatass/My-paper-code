# Existing Portfolio exchange — complete text preservation

This is the one record-only recovery requested by Root on 2026-09-14 UTC.
ACVC remains scientifically PARKED and occupies no scientific slot. No scientific
reconsideration, experiment or new provider request was performed.

Source: [Select Replacement Direction](https://chatgpt.com/c/6aa76925-4558-83e8-86e2-40c5e0a2c320).
The complete existing [prompt](archive/PROMPT.md) and [answer](archive/RESPONSE.md)
were read through the supported Codex in-app browser and saved from the actual
`Copy message` / `Copy response` clipboard strings. These files are full source
text, not an expansion of the prior local selection summary. Their wording,
Markdown, table padding and original ending-newline state are unchanged. Scoped
Git attributes prevent newline conversion of these two archival files.

| File | Characters (JavaScript UTF-16 length) | UTF-8 bytes | Ending newline |
| --- | ---: | ---: | --- |
| PROMPT.md | 573 | 573 | No |
| RESPONSE.md | 9756 | 9796 | Yes, LF |

The full page was visibly complete through its final Status paragraph and had
response controls. The complete clipboard strings were obtained; the character
counts additionally agree with Clerk's earlier observation. Counts alone were
not used to reconstruct or certify the text. [Extraction facts](archive/RECOVERY_FACTS.json)
preserve the conversation and paired DOM message identities, actual API method,
failed interface attempts, UTF-8 hashes and readback checks.

The first prompt-copy attempt showed `Message copied`, but the browser clipboard
read returned an empty string twice and an empty item list. The attempted
`tab.content.export()` returned the exact error
`Codex in-app browser does not support command "tab_content_export".`
Neither result was accepted as archived text. `Copy response`, followed by its
fresh `Response copied` state and then `clipboard.readText()`, returned the full
9756-character answer. Repeating `Copy message` and reading after its fresh
`Message copied` state returned the full 573-character prompt. Both were saved
losslessly as UTF-8 without BOM. Text retrieval used the supported browser
interface throughout; local file writing happened after retrieval.

This completes the ACVC-only missing archive identified in main's
[vacancy exchange recovery record](https://github.com/CartmanFatass/My-paper-code/blob/ba739a679b1d434277a54ef031373822b3c40b73/docs/research/portfolio/decisions/2026-09-14-vacancy-exchange-recovery.md).
It does not revise the prior re-entry decision or claim that the former DM had
read these exact provider bytes before this recovery. The old summary, its
reported limitation, scientific intakes and original request history remain
preserved.

Event: `acvc-portfolio-existing-exchange-archived-20260914-01`.
Clerk receives the committed files directly, integrates them, updates the main
recovery index to point to the full archive, and rearchives this task after its
publication turn ends. No Root acknowledgement is required.
