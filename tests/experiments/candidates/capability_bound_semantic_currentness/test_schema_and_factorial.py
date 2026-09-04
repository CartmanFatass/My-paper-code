from dataclasses import replace
import json
from pathlib import Path

import pytest

from experiments.candidates.capability_bound_semantic_currentness.factorial import (
    construct_world,
    nuisance_coordinates,
    whole_carrier_reassociation_is_valid,
)
from experiments.candidates.capability_bound_semantic_currentness.registered import (
    registered_spec,
    validate_registered_spec,
)
from experiments.candidates.capability_bound_semantic_currentness.schema import (
    AccessState,
    BindingState,
    NuisanceCoordinate,
    OwnerState,
    PayloadState,
    SemanticState,
    to_jsonable,
)


def _world(binding=BindingState.AUTHENTIC, payload=PayloadState.RECEIVER_CORRECT, receiver=0):
    return construct_world(
        OwnerState.LIVE,
        SemanticState.PERSIST,
        binding,
        AccessState.BINDING_GATED,
        payload,
        NuisanceCoordinate(receiver, 0, 1, 1, 0, 1, 0),
    )


def test_registered_cardinality_without_registered_enumeration():
    audit = validate_registered_spec(registered_spec())
    assert audit.valid
    assert (audit.scientific_cell_count, audit.nuisance_count_per_cell, audit.world_count_per_arm) == (48, 128, 6144)
    assert len(nuisance_coordinates()) == 128
    assert len({coordinate.address() for coordinate in nuisance_coordinates()}) == 128
    assert not validate_registered_spec(replace(registered_spec(), material_margin=registered_spec().material_margin * 2)).valid
    assert not validate_registered_spec(replace(registered_spec(), protocol_order=("TAMPERED",))).valid
    assert not validate_registered_spec(replace(registered_spec(), cbsc_fixed_rule=(("OTHERWISE", "SERVE"),))).valid
    assert not validate_registered_spec(replace(registered_spec(), reset_law=("KEEP_CACHE",))).valid
    assert not validate_registered_spec(replace(registered_spec(), delta_comparator="GREATER_THAN_ZERO")).valid


def test_physical_key_truth_payload_twins_and_whole_carrier_derangement():
    correct = _world(payload=PayloadState.RECEIVER_CORRECT, receiver=0)
    swapped = _world(payload=PayloadState.SWAPPED, receiver=0)
    reassociated = _world(binding=BindingState.WHOLE_CARRIER_REASSOCIATED, receiver=0)
    assert correct.routed_carrier.body.payload_source_receiver == 0
    assert correct.routed_carrier.body.content_bit == 0
    assert swapped.routed_carrier.body.payload_source_receiver == 1
    assert swapped.routed_carrier.body.content_bit == (1 ^ 1)  # donor bit under receiver-1 phase
    assert correct.issued_inventory == swapped.issued_inventory
    assert whole_carrier_reassociation_is_valid(reassociated)
    assert reassociated.carriers_by_physical_receiver == tuple(reversed(reassociated.issued_carriers))
    assert sorted(reassociated.carriers_by_physical_receiver, key=lambda carrier: carrier.issued_to_receiver) == sorted(
        reassociated.issued_carriers, key=lambda carrier: carrier.issued_to_receiver
    )
    assert all(
        reassociated.carriers_by_physical_receiver[index].carrier_id
        != reassociated.issued_carriers[index].carrier_id
        for index in (0, 1)
    )
    assert correct.world_id.startswith('world:{"access":"BINDING_GATED"')
    assert correct.routed_carrier.carrier_id.startswith('carrier:{"body":')


def test_controller_visible_carrier_identities_contain_only_primitive_body_fields():
    forbidden = ("payload_role", "RECEIVER_CORRECT", "SWAPPED", "NATIVE_NEUTRAL")
    for payload in PayloadState:
        world = _world(payload=payload)
        for carrier in world.presented_carriers:
            assert not any(token in carrier.carrier_id for token in forbidden)
            assert not any(token in carrier.body.body_id for token in forbidden)


def test_draft_2020_12_host_schema_and_identity_tamper():
    jsonschema = pytest.importorskip("jsonschema")
    schema_path = Path("experiments/candidates/capability_bound_semantic_currentness/schemas/cbsc_host_spec_v1.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    payload = to_jsonable(registered_spec())
    jsonschema.validate(payload, schema)
    cost_tamper = json.loads(json.dumps(payload))
    cost_tamper["costs"][0][1] = [1, 4]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(cost_tamper, schema)
    law_tamper = json.loads(json.dumps(payload))
    law_tamper["protocol_order"][0] = "TAMPERED"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(law_tamper, schema)
    machine_law_tamper = json.loads(json.dumps(payload))
    machine_law_tamper["policy_capability_law"][3][1] = "GATED_CAPABILITY"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(machine_law_tamper, schema)
    ledger_tamper = json.loads(json.dumps(payload))
    ledger_tamper["action_ledger_incidence"][0][1].append("EXTRA_CHARGE")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(ledger_tamper, schema)
    payload["protocol_id"] = "TAMPERED"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)
