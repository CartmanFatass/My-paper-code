"""Hidden reference used only to validate the benchmark scorer."""


def assess(contract, certificate, lease, manifest, packets):
    reasons = []
    direction, revision = contract.get("direction"), contract.get("revision")
    expected = set(contract.get("frozen_seeds", []))
    arms = set(contract.get("arms", []))
    updates = contract.get("updates")

    for label, item in (("certificate", certificate), ("lease", lease), ("manifest", manifest)):
        if item.get("direction") != direction or item.get("revision") != revision:
            reasons.append(f"{label} binding mismatch")
    if certificate.get("passed") is not True or certificate.get("registered_stochastic_object_materialized") is not False:
        reasons.append("preactivity certificate is not exact and clean")
    if lease.get("production_authorized") is not True or lease.get("max_workers") != 1:
        reasons.append("lease is not exact single-worker authority")
    if set(lease.get("authorized_seeds", [])) != expected or len(lease.get("authorized_seeds", [])) != len(expected):
        reasons.append("lease seed registry mismatch")
    if not manifest.get("fresh_result_root"):
        reasons.append("result root is not fresh")
    if manifest.get("valid_calibration_cells") != contract.get("calibration_cells"):
        reasons.append("calibration cell count mismatch")
    if manifest.get("trace_rows") != contract.get("trace_rows"):
        reasons.append("trace row count mismatch")
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
        observed_arms = packet.get("arms", {})
        if set(observed_arms) != arms or any(observed_arms.get(arm) != updates for arm in arms):
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
