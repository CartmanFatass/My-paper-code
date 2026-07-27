AUDIT_DISPOSITION=MISMATCH

Frozen assertion: formal execution at target 6b8ea82d8fdbc76c14a414ff2b042a126f945dfb must be authorized by a code-science alignment bound to that exact target. The prior e21a1464… implementation and 9dc84d3… review stage may serve only as prior evidence; they may not substitute for target-6b alignment authority.

Conflicting path: the code-science index still declares:

aligned_g42_implementation_commit=e21a1464e186260878649ad170bc3f32b8b9496d
alignment_recheck_stage_commit=9dc84d3372a8e41ead9a5a349689586dc8e772b5

and describes the formal runner as binding that earlier aligned implementation rather than 6b8ea82d….

The runner hard-codes the same earlier identities as ALIGNED_IMPLEMENTATION_COMMIT and ALIGNMENT_STAGE_COMMIT. Its formal-preflight validator accepts only those values and requires the preflight train, evaluation, and analysis manifests to serialize aligned_source_commit=e21a1464…, even when their actual source_commit is 6b8ea82d…. Thus source-6b formal execution can pass using an earlier alignment while no target-bound source-6b authority is required.

The focused authority test encodes this same route by supplying the earlier implementation and stage constants as the successful formal-alignment identity.

Smallest in-contract correction: after archiving this source-6b audit, bind the index and runner’s formal admission to:

aligned_implementation_commit=6b8ea82d8fdbc76c14a414ff2b042a126f945dfb
alignment_stage_commit=<archived source-6b alignment stage>

Require the bounded-preflight and later formal manifests to carry that same target-bound identity, and add a focused guard proving that the prior e21a1464…/9dc84d3… pair fails formal admission for source 6b8ea82d…. No actor graph, credit rule, source, seed, threshold, inventory, confidence procedure, or first-match branch requires modification.
