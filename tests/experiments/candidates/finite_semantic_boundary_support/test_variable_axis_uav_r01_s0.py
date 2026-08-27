from __future__ import annotations

import json
import itertools
import hashlib
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
MODULE = (
    "experiments.candidates.finite_semantic_boundary_support."
    "variable_axis_uav_r01"
)


def _run_cli(tmp_path: Path) -> dict[str, object]:
    output = tmp_path / "fsbs-r01-s0-evidence.json"
    completed = subprocess.run(
        [sys.executable, "-m", MODULE, "--output", str(output)],
        cwd=REPO,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert output.is_file()
    assert not list(tmp_path.glob("*.tmp"))
    evidence = json.loads(output.read_text(encoding="utf-8"))
    if "technical_measurements" in evidence:
        assert evidence["technical_measurements"]["io"]["output_bytes"] == output.stat().st_size
    return evidence


def _address(seed: int, family: str, coordinates: tuple[object, ...], rejection: int = 0) -> bytes:
    return "\0".join(
        ["FSBS-VN1-R01", str(seed), family, *(str(value) for value in coordinates), str(rejection)]
    ).encode("utf-8")


def _draw(domain_size: int, seed: int, family: str, coordinates: tuple[object, ...]) -> int:
    limit = ((1 << 256) // domain_size) * domain_size
    rejection = 0
    while True:
        value = int.from_bytes(hashlib.sha256(_address(seed, family, coordinates, rejection)).digest(), "big")
        if value < limit:
            return value % domain_size
        rejection += 1


def _permutation(size: int, seed: int, family: str, coordinates: tuple[object, ...]) -> list[int]:
    values = list(range(size))
    for swap_position in range(size - 1, 0, -1):
        selected = _draw(
            swap_position + 1,
            seed,
            family,
            (*coordinates, swap_position),
        )
        values[swap_position], values[selected] = values[selected], values[swap_position]
    return values


def test_cli_emits_atomic_learner_free_support_gate_counts(tmp_path: Path) -> None:
    evidence = _run_cli(tmp_path)

    assert evidence["schema"] == "FSBS_R01_S0_HOST_SUPPORT_FIREWALL_V1"
    assert evidence["mode"] == "TECHNICAL_ONLY_RESULT_BLIND_LEARNER_FREE"
    assert evidence["namespace"] == "FSBS-VN1-R01"
    assert evidence["counts"] == {
        "outer_strata": 384,
        "worlds_per_stratum": 8,
        "accepted_per_world": 4,
        "denied_per_world": 1,
        "accepted_transactions": 12_288,
        "denied_transactions": 3_072,
        "total_transactions": 15_360,
    }
    assert evidence["firewall"] == {
        "learner_initialized": False,
        "model_created": False,
        "checkpoint_created": False,
        "registered_paired_effects_emitted": False,
        "partial_scientific_value_emitted": False,
        "formal_compute_executed": False,
        "external_effect_executed": False,
        "operator_requested": False,
        "provider_contacted": False,
        "deployment_or_flight_executed": False,
    }
    assert evidence["effect_refs"] == []
    assert evidence["atomic_write"]["single_final_replace"] is True
    assert evidence["next_boundary"] == (
        "FSBS-R01-S1-LEARNER-FREE-TECHNICAL-BINDING-ONLY"
    )


def test_all_strata_recompute_host_mapping_and_resource_receipts(tmp_path: Path) -> None:
    evidence = _run_cli(tmp_path)
    strata = evidence["strata"]
    presentations = [
        (11, 0, 0, 0),
        (23, 0, 0, 1),
        (37, 0, 1, 0),
        (53, 0, 1, 1),
        (71, 1, 0, 0),
        (89, 1, 0, 1),
        (107, 1, 1, 0),
        (127, 1, 1, 1),
    ]
    expected_keys = set(
        itertools.product(
            (6, 8, 10),
            ("FULL", "REDUCED"),
            (0, 1),
            (0, 1),
            presentations,
            ("AUTHENTIC", "REASSOCIATED"),
        )
    )
    registered_permutations = {
        (1, 2, 3, 0),
        (1, 3, 0, 2),
        (2, 0, 3, 1),
        (3, 0, 1, 2),
    }
    observed_keys = set()
    accepted = denied = 0
    accepted_work_by_arm = {"AUTHENTIC": [0, 0], "REASSOCIATED": [0, 0]}

    assert len(strata) == 384
    for stratum in strata:
        key = stratum["key"]
        presentation = (
            key["seed"],
            key["kappa"],
            key["mu"],
            key["lambda"],
        )
        observed_keys.add(
            (
                key["M"],
                key["occupancy"],
                key["i"],
                key["r"],
                presentation,
                key["arm"],
            )
        )
        worlds = stratum["worlds"]
        assert len(worlds) == 8
        assert {
            (world["relevant_slot"], world["relevant_reservation"], world["decoy_reservation"])
            for world in worlds
        } == set(itertools.product((0, 1), repeat=3))

        for block_start in (0, 4):
            block = worlds[block_start : block_start + 4]
            if key["arm"] == "AUTHENTIC":
                assert all(
                    world["semantic_bit"] == world["relevant_slot"]
                    and world["donor_world"] == world["world"]
                    for world in block
                )
            else:
                donor = tuple(world["donor_world"] - block_start for world in block)
                assert donor in registered_permutations
                assert {
                    (world["relevant_slot"], world["semantic_bit"])
                    for world in block
                } == set(itertools.product((0, 1), repeat=2))

        for world in worlds:
            assert world["surface_bit"] == world["semantic_bit"] ^ key["kappa"]
            records = {row["slot"]: row["payload_bit"] for row in world["records"]}
            assert records == {
                world["relevant_slot"]: world["relevant_reservation"] ^ key["mu"],
                1 - world["relevant_slot"]: world["decoy_reservation"] ^ key["mu"],
            }
            accepted_rows = [row for row in world["transactions"] if row["accepted"]]
            denied_rows = [row for row in world["transactions"] if not row["accepted"]]
            assert {(row["open_slot"], row["lane_action"]) for row in accepted_rows} == set(
                itertools.product((0, 1), repeat=2)
            )
            assert len(denied_rows) == 1
            for row in accepted_rows:
                assert row["resource_receipt"] == {
                    "payload_reads": 1,
                    "reservation_services": 1,
                }
                assert row["payload_bit"] == records[row["open_slot"]]
                assert row["oracle_payload_match"] is True
                accepted_work_by_arm[key["arm"]][0] += 1
                accepted_work_by_arm[key["arm"]][1] += 1
            denied_row = denied_rows[0]
            assert denied_row == {
                "accepted": False,
                "request": "OPEN_BOTH",
                "required_resources": {
                    "payload_reads": 2,
                    "reservation_services": 1,
                },
                "resource_cap": {
                    "payload_reads": 1,
                    "reservation_services": 1,
                },
                "payload_exposed": False,
                "score_exposed": False,
            }
            accepted += len(accepted_rows)
            denied += 1

    assert observed_keys == expected_keys
    assert accepted == 12_288
    assert denied == 3_072
    assert accepted_work_by_arm["AUTHENTIC"] == accepted_work_by_arm["REASSOCIATED"]


def test_current_bytes_churn_addresses_firewall_and_evidence_tree(tmp_path: Path) -> None:
    first = _run_cli(tmp_path)
    second = _run_cli(tmp_path)

    authority = REPO / first["authority_ref"]["path"]
    assert first["authority_ref"]["sha256"] == hashlib.sha256(authority.read_bytes()).hexdigest()
    for source_ref in first["source_manifest"]:
        source = REPO / source_ref["path"]
        assert source_ref["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()

    proof = first["counter_proof"]
    proof_address = _address(
        proof["seed"], proof["family"], tuple(proof["coordinates"]), proof["rejection_counter"]
    )
    assert proof["address_hex"] == proof_address.hex()
    assert proof["sha256"] == hashlib.sha256(proof_address).hexdigest()
    assert proof["categorical_result"] == _draw(
        proof["domain_size"], proof["seed"], proof["family"], tuple(proof["coordinates"])
    )

    paired_addresses: dict[tuple[object, ...], set[str]] = {}
    for stratum in first["strata"]:
        key = stratum["key"]
        pair_key = (
            key["M"], key["occupancy"], key["i"], key["r"], key["seed"],
            key["kappa"], key["mu"], key["lambda"],
        )
        expected_address = hashlib.sha256(
            _address(key["seed"], "paired-exogenous-world", pair_key[:4] + pair_key[5:])
        ).hexdigest()
        assert stratum["paired_address_sha256"] == expected_address
        paired_addresses.setdefault(pair_key, set()).add(stratum["paired_address_sha256"])
        assert stratum["churn_fixture_id"] == f"M{key['M']}-seed{key['seed']}"
        for world in stratum["worlds"]:
            assert set(world["selector_view"]) == {"i", "r", "surface_bit", "auth_ok"}
            assert world["selector_view"] == {
                "i": key["i"],
                "r": key["r"],
                "surface_bit": world["surface_bit"],
                "auth_ok": 1,
            }
    assert len(paired_addresses) == 192
    assert all(len(addresses) == 1 for addresses in paired_addresses.values())

    fixtures = {fixture["fixture_id"]: fixture for fixture in first["churn_fixtures"]}
    assert len(fixtures) == 24
    for fixture in fixtures.values():
        M = fixture["M"]
        seed = fixture["seed"]
        hidden = _permutation(M, seed, "churn-hidden-permutation", (M,))
        assert fixture["hidden_permutation"] == hidden
        expected_active = [
            set(range(M)),
            set(range(M)) - {hidden[0], hidden[1]},
            set(range(M)),
            set(range(M)) - {hidden[2], hidden[3]},
            set(range(M)),
        ]
        state = {lineage: 0 for lineage in range(M)}
        prior_tokens: dict[int, str] = {}
        role_peer_history: dict[int, list[tuple[str, int]]] = {lineage: [] for lineage in range(M)}
        for window_index, window in enumerate(fixture["windows"]):
            active = set(window["active_lineages"])
            assert active == expected_active[window_index]
            assert window["active_mask"] == [lineage in active for lineage in range(M)]
            before = {int(lineage): value for lineage, value in window["state_before"].items()}
            after = {int(lineage): value for lineage, value in window["state_after"].items()}
            assert before == {lineage: state[lineage] for lineage in active}
            assert after == {lineage: state[lineage] + 1 for lineage in active}
            for lineage in active:
                state[lineage] += 1
            tokens = {int(lineage): token for lineage, token in window["slot_tokens"].items()}
            assert set(tokens) == active
            for lineage, token in tokens.items():
                if lineage in prior_tokens and lineage in expected_active[max(0, window_index - 1)]:
                    assert token == prior_tokens[lineage]
                elif lineage in prior_tokens:
                    assert token != prior_tokens[lineage]
                prior_tokens[lineage] = token
            for publisher, subscriber in window["ordered_pairs"]:
                role_peer_history[publisher].append(("publisher", subscriber))
                role_peer_history[subscriber].append(("subscriber", publisher))
        assert any(
            len({role for role, _ in history}) == 2 and len({peer for _, peer in history}) > 1
            for history in role_peer_history.values()
        )

    info = first["information_path_firewall"]
    assert info["selector_visible_fields"] == ["i", "r", "surface_bit", "auth_ok"]
    assert info["unopened_payload_exposed"] is False
    assert info["pair_score_exposed"] is False
    assert info["future_return_exposed"] is False
    assert not set(info["selector_visible_fields"]) & set(info["forbidden_selector_fields"])

    core = {
        key: value
        for key, value in first.items()
        if key not in {"technical_measurements", "deterministic_core_sha256"}
    }
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert first["deterministic_core_sha256"] == hashlib.sha256(canonical).hexdigest()
    assert second["deterministic_core_sha256"] == first["deterministic_core_sha256"]

    measurements = first["technical_measurements"]
    assert measurements["scope"] == "build-validate-canonicalize-before-atomic-replace"
    assert measurements["cpu_ns"] > 0
    assert measurements["wall_ns"] > 0
    assert measurements["peak_memory_bytes"] > 0
    assert measurements["peak_memory_method"] == "tracemalloc-python-allocations"
    assert measurements["io"]["authority_bytes_read"] == authority.stat().st_size
    assert measurements["io"]["source_bytes_read"] == sum(
        (REPO / row["path"]).stat().st_size for row in first["source_manifest"]
    )
    assert measurements["io"]["atomic_replace_count"] == 1

    nodes = {node["id"]: node["status"] for node in first["evidence_tree"]["nodes"]}
    assert nodes == {
        "authority-current-bytes": "PASS",
        "counter-address-equality": "PASS",
        "host-eight-cell-support": "PASS",
        "registered-reassociation": "PASS",
        "resource-work-equality": "PASS",
        "churn-state-ownership": "PASS",
        "information-path-firewall": "PASS",
        "atomic-complete-output": "PASS",
    }
    assert first["evidence_tree"]["terminal_status"] == "TECHNICALLY_ACCEPTED"
