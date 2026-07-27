AUDIT_DISPOSITION=MISMATCH

Frozen assertion: the authority value must be an independently established digest of the accepted G40 common fast-anchor checkpoint—or come from a validated accepted checkpoint payload. The candidate anchor must not be able to choose its own expected digest and thereby self-certify.

Remaining conflicting path: _validate_trusted_anchor_digest checks only that the caller-provided string is syntactically a lowercase SHA-256. project_post_anchor_paths then accepts any fast-phase G40 model whenever that freely supplied string equals the model’s locally computed state digest. Consequently, a caller can still compute fresh_digest = _state_digest(fresh.state_dict()), pass trusted_anchor_digest=fresh_digest, construct both paths, and serialize that same value into the projected checkpoint. The static certificate likewise treats the caller-provided value as authority, so a fully self-consistent fresh-model projection can pass.

The focused guard does not exercise that bypass. Its fresh and tampered cases are tested only against a hardcoded different digest; it never attempts projection with each candidate’s own matching digest. Moreover, the positive “trusted” state is synthesized inside the repair test by creating a new model and applying one locally executed update, rather than being loaded or validated as the independently archived accepted G40 common anchor.

Smallest in-contract correction: bind projection to an immutable accepted-G40 anchor digest obtained from the archived accepted checkpoint, or require a checkpoint payload whose source commit, checkpoint kind, phase, complete-state digest, and contents are independently validated. A free caller-selected digest must not itself confer authority. Add the exact guard:

project_post_anchor_paths(fresh, trusted_anchor_digest=digest(fresh))
    -> fail before path or optimizer construction

and make the positive guard use the independently validated accepted G40 anchor payload. Preserve every retained graph, credit equation, update kernel, tolerance, evidence bound, and authority field.