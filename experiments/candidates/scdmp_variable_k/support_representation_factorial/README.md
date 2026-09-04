# SCDMP-TBOV support-representation factorial r03

This isolated package implements only the Pro-closed
`SCDMP-TBOV-SRF-CHECKPOINT-SCIENCE-20260820-03` composite direct checkpoint
factorial. Revision 03 preserves the revision 02 HMAC namespace and domain
labels and changes only the closed count semantics.
It imports the immutable r07 deterministic task/word/truth primitives but no
r07 observed data or downstream inference. It contains no Stage-B path.

The preactivity command performs source/constant/static-contract checks only.
It does not instantiate a model, sample identity, materialize a coordinate or
scale, train, or evaluate:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.scdmp_variable_k.support_representation_factorial --mode preactivity
```

Production requires a later exact Root lease plus explicit create-only result,
blinded frontier, create-only manifest-root and activity-sidecar identities.
The accepted lease interface is frozen by `run._validate_lease`; it binds the
exact direction, candidate, result object, revision, ten seeds, four cells,
single-worker CPU resource, result root, expiry and no-Stage-B boundary.
Production retains a blinded resumable frontier and requires `--resume` to
continue it.

The active prospective expected direct-example accounting is `204697600`.
The exact realized total is `202854400 + 90*sum_n10`, lies on a step-90 lattice
in `[202854400,206540800]`, and counts registered row-segment/direct evaluation
examples rather than framework calls. The historical `224604160` assertion is
retained only as superseded revision-02 provenance. Realized counts and `n10`
are published only with the complete atomic result and have no scientific or
routing role.
