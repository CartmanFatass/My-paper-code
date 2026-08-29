# SGSP short-gate Pro Innovator zero-send transport incident

## Conclusion

The required fresh Pro Innovator request was not sent. The transport leaf
correctly proved zero provider commitment, but its page-decision strategy
misclassified a page it itself recorded as `ChatGPT / GPT-5.6 Pro` because an
additional reasoning-mode menu remained ambiguous. It then opened a second
fresh pre-send operation after a claimed non-sending repair and reached the
same failure. The user directly observed the Pro text on the page. EM stopped
the leaf before another page operation.

This is a shared transport-capability defect, not scientific evidence about
SGSP and not a provider-availability conclusion.

## Frozen request and direct observation

- Cycle: `SGSP-RG2Z-RSCF-SHORT-GATE-20260829-01`
- Stage: `INNOVATOR`
- Exact prompt:
  `SGSP_RSCF_SHORT_GATE_R01_CHATGPT_PRO_INNOVATOR_PROMPT_20260829.md`
- Prompt SHA-256:
  `c56ea79cb629d2d93ac903bcdd57670bf0d3c4cdd652d760391cf3420bfee72e`
- Required visible provider/model: `ChatGPT / GPT-5.6 Pro`
- Leaf-reported provider/model preflight: `ChatGPT / GPT-5.6 Pro`
- Leaf-reported failure predicate: `reasoning_mode_menu_ambiguous`
- Replacement operation reported by the leaf:
  `d1791bd2-bb34-465c-b6ac-b04d484ead03`
- `sendCount=0`
- `sendActionCount=0`
- `newUserMessageCount=0`
- `zeroCommitPreClick=true`
- Provider conversation created: none
- Response/archive created: none
- Live Effect: none
- Final stage transport state: `ZERO_SEND_FAILED`

The user then stated in native history that the Pro indication was plainly
visible. No further browser observation was made after that statement.

## Defect statement

The returned facts show two separable transport defects:

1. **Model/mode evidence classification.** The leaf recognized and recorded
   the exact visible GPT-5.6 Pro model, yet treated a separate reasoning-mode
   menu as an unresolved prerequisite without explaining why that menu could
   override the exact visible model requirement.
2. **Unchanged-failure stopping.** After a second pre-send operation reached
   the same ambiguity and still had zero commitment, the same failure premise
   was exhausted. A further activation was not justified until a new concrete
   UI fact or repair existed.

The fail-closed refusal to send under genuine model ambiguity is correct. The
defect is the unsupported classification of already-visible exact model
evidence and the repeated page operation under an unchanged failure premise.

## Requested shared repair acceptance

Root should route a bounded shared transport repair that:

- distinguishes the provider-visible model identity from any separate
  reasoning-mode or effort control;
- records the exact visible labels and selection state used for the model
  decision, with a screenshot or equivalent page evidence when ambiguity is
  claimed;
- accepts an exact visible `GPT-5.6 Pro` model indication unless a concrete
  conflicting selection state is also visible;
- fails closed before Send when the visible model is genuinely ambiguous;
- performs no second fresh pre-send operation for the same failure without a
  new, recorded UI fact or non-sending repair that changes the premise; and
- proves the repaired positive and ambiguous branches on non-sending fixtures
  before any scientific prompt is used.

The repair must not send the SGSP prompt, edit it, create a provider
conversation, or infer a scientific or lifecycle result. After reviewed
integration, the same EM cycle may open a fresh strict Innovator operation
because the recorded operations proved zero send.
