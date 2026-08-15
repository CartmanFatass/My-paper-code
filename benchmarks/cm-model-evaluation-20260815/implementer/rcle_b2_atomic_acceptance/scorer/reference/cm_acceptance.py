"""Hidden reference used only to validate the benchmark scorer."""


def assess(contract, certificate, lease, manifest, packets):
    reasons = []
    direction = contract.get("direction")
    revision = contract.get("revision")
    expected = set(contract.get("frozen_seeds", []))

    for label, item in (("certificate", certificate), ("lease", lease), ("manifest", manifest)):
        if item.get("direction") != direction or item.get("revision") != revision:
            reasons.append(f"{label} binding mismatch")
    if certificate.get("passed") is not True:
        reasons.append("preactivity certificate did not pass")
    if certificate.get("registered_stochastic_object_materialized") is not False:
        reasons.append("preactivity materialized a stochastic object")
    if lease.get("production_authorized") is not True or lease.get("max_workers") != 1:
        reasons.append("lease is not exact single-worker production authority")
    if set(lease.get("authorized_seeds", [])) != expected or len(lease.get("authorized_seeds", [])) != len(expected):
        reasons.append("lease seed registry mismatch")
    if not manifest.get("fresh_result_root"):
        reasons.append("result root is not fresh")
    if not manifest.get("source_revision_and_hyperparameters_exact"):
        reasons.append("source binding is not exact")
    if manifest.get("atomic_seed_packets") != len(expected):
        reasons.append("manifest atomic seed count mismatch")
    if manifest.get("arms_per_seed") != contract.get("arms_per_seed") or manifest.get("updates_per_arm_seed") != contract.get("updates_per_arm_seed"):
        reasons.append("manifest arm/update contract mismatch")
    if manifest.get("partial_result_selection_or_exposure") is not False:
        reasons.append("partial result exposure")

    seen = set()
    for packet in packets:
        seed = packet.get("seed")
        if seed in seen:
            reasons.append(f"duplicate seed {seed}")
        seen.add(seed)
        if seed not in expected:
            reasons.append(f"unknown seed {seed}")
        if packet.get("direction") != direction or packet.get("revision") != revision:
            reasons.append(f"packet binding mismatch for seed {seed}")
        if packet.get("atomic_complete") is not True:
            reasons.append(f"non-atomic packet for seed {seed}")
        if packet.get("arms") != contract.get("arms_per_seed") or packet.get("updates_per_arm") != contract.get("updates_per_arm_seed"):
            reasons.append(f"arm/update mismatch for seed {seed}")
    if seen != expected:
        reasons.append("exact frozen seed panel is incomplete")
    accepted = not reasons
    return {
        "technical_acceptance": accepted,
        "result_complete": accepted,
        "accepted_seed_count": len(seen & expected),
        "rejection_reasons": reasons,
        "scientific_interpretation_performed_by_cm": False,
    }
