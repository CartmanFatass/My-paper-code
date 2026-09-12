"""Owned public rows and projection for the selected CBSC public-stream B.

This changes only DynamicHost._finish and the named public/output boundaries.
The original generator, learner, state/ledger and their runtime remain shared.
"""
from collections import Counter
from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib

import torch

from ..omrc_b01.adapters import AdapterWorkReceipt
from ..omrc_b01.contract import Action, EventKind
from ..omrc_b01.host import DynamicHost
from ..omrc_b01.tapes import EpisodeEvaluator, TapeGenerationAudit, TapeIdentity
from ..omrc_b01.token import PrimitiveToken, _validate_kind_clock

# Literal scientific masks from omrc_b01/token.py; no Enum-field reflection.
PUBLIC_MASKS = {
    0x01: (0x8043, 0x00), 0x02: (0x8103, 0x02),
    0x03: (0xA011, 0x00), 0x04: (0x9E19, 0x0C),
    0x10: (0xC063, 0x00), 0x11: (0xC183, 0x03),
    0x12: (0xE011, 0x00), 0x13: (0xDE19, 0x0C),
    0x14: (0xC001, 0x00), 0x15: (0xC001, 0x00),
    0x16: (0xC001, 0x00), 0x17: (0xC001, 0x00),
    0x20: (0xFE1D, 0x7C), 0x21: (0xC001, 0x00),
}


def pack_public(token):
    """Copy the explicit legal public fields once, retaining literal meaning."""
    values = (
        token.event_kind, token.subject_receiver, token.target_receiver,
        token.slot, token.carrier, token.owner_old, token.owner_new,
        token.epoch_old, token.epoch_new, token.body_owner, token.body_epoch,
        token.body_addressed_receiver, token.payload_source_receiver,
        token.capability_receiver, token.opportunity_index, token.event_order_position,
    )
    flags = (
        token.old_need, token.new_need, token.body_content, token.body_native_neutral,
        token.access_gated, token.request_active, token.request_need, token.reserved_zero,
    )
    row = bytes((*values, sum(int(flag) << bit for bit, flag in enumerate(flags))))
    bmask, fmask = PUBLIC_MASKS[row[0]]
    for index in range(1, 16):
        if bool(bmask & (1 << index)) == (row[index] == 255):
            raise ValueError("public field presence differs from the literal event law")
    if row[16] & ~fmask:
        raise ValueError("public flag is illegal for the literal event kind")
    _validate_kind_clock(EventKind(row[0]), token)
    return row


@dataclass(frozen=True)
class DirectPublicEpisode:
    identity: TapeIdentity
    public_rows: tuple[bytes, ...]
    _decision_truth: tuple
    generation_audit: TapeGenerationAudit

    def __post_init__(self):
        if len(self.public_rows) != 152 or any(
            not isinstance(row, bytes) or len(row) != 17 for row in self.public_rows
        ):
            raise ValueError("direct episode requires 152 immutable 17-byte public rows")
        if len(self._decision_truth) != 24:
            raise ValueError("direct episode requires 24 separate evaluator decisions")
        if any(self.public_rows[12 + 6*q][0] != 0x20 or
               self.public_rows[13 + 6*q][0] != 0x21 for q in range(24)):
            raise ValueError("decision and settlement positions changed")

    def evaluator(self):
        return EpisodeEvaluator(self._decision_truth, None)

    @property
    def primitive_digest(self):
        return hashlib.sha256(b"".join(self.public_rows)).hexdigest()

    @property
    def transition_count(self):
        return len(self.public_rows)

    @property
    def decision_count(self):
        return len(self._decision_truth)


class DirectPublicHost(DynamicHost):
    def _finish(self, split, episode_id, tokens, truth, pools, prf, motif=None):
        if motif is not None:
            raise ValueError("this selected B has only TRAIN/EVAL_STOCHASTIC tapes")
        rows = tuple(pack_public(token) for token in tokens)
        audit = TapeGenerationAudit(
            owner_tokens_consumed=pools.owner_cursor,
            epoch_tokens_consumed=pools.epoch_cursor,
            draw_count=len(prf.addresses),
            draw_digest=prf.audit_digest(),
            draw_addresses=prf.addresses,
        )
        return DirectPublicEpisode(
            TapeIdentity(self.run_name, self.seed, split, episode_id),
            rows, tuple(truth), audit,
        )


def adapter_rows(public_rows, arm):
    """The existing RAW4/STRUCT4 laws over public bytes, reset per episode."""
    registers = [255] * 4
    emissions = []
    work = AdapterWorkReceipt()
    if arm not in ("RAW-GRU", "STRUCT-CURRENTNESS-GRU"):
        raise ValueError("only the selected RAW/STRUCT arms are defined")
    for row in public_rows:
        kind = row[0]
        bmask, fmask = PUBLIC_MASKS[kind]
        if arm == "RAW-GRU":
            appended = [row[index] for index in range(16) if bmask & (1 << index)]
            if fmask:
                appended.append(row[16])
            for value in appended:
                registers[:] = (*registers[1:], value)
            emitted = bytes(registers)
            work += AdapterWorkReceipt(appended_bytes=len(appended))
        else:
            writes = 0
            if kind in (0x01, 0x10):
                registers[row[1]] = row[6]
                writes = 1
            elif kind in (0x02, 0x11):
                registers[2 + row[1]] = row[8]
                writes = 1
            if kind == 0x20:
                owner, epoch = registers[row[2]], registers[2 + row[2]]
                emitted = bytes((owner, epoch, owner ^ row[9], epoch ^ row[10]))
                work += AdapterWorkReceipt(byte_reads=4, byte_writes=writes, uint8_xors=2)
            else:
                emitted = bytes(registers)
                work += AdapterWorkReceipt(byte_reads=4, byte_writes=writes)
        emissions.append(emitted)
    return tuple(emissions), work


def project_panel(tapes, arm):
    observations = []
    total = AdapterWorkReceipt()
    for tape in tapes:
        emissions, work = adapter_rows(tape.public_rows, arm)
        rows = [[(byte >> bit) & 1 for byte in public + emitted for bit in range(8)]
                for public, emitted in zip(tape.public_rows, emissions, strict=True)]
        observations.append(torch.tensor(rows, dtype=torch.float32, device="cpu"))
        total += work
    return torch.stack(observations), total


def request_only(public_rows):
    return ["REFRESH" if row[16] & (1 << 5) else "SAFE_FALLBACK"
            for row in public_rows[12::6]]


def _fraction_record(value):
    return {"numerator": value.numerator, "denominator": value.denominator,
            "float": float(value)}


def native_record(tape, names):
    """Score already-chosen actions using only the original evaluator ledger."""
    if len(names) != 24:
        raise ValueError("native primary requires all 24 chosen actions")
    evaluator = tape.evaluator()
    decision = Fraction(0)
    settlement = Fraction(0)
    contributions = []
    counts = Counter(names)
    for opportunity, name in enumerate(names):
        action = Action[name]
        ledger = evaluator.ledger(opportunity, action)
        decision += ledger.decision_reward
        settlement += ledger.settlement_reward
        contributions.append({
            "opportunity_index": opportunity, "action": name,
            "decision_reward": _fraction_record(ledger.decision_reward),
            "settlement_reward": _fraction_record(ledger.settlement_reward),
        })
    return {
        "identity": asdict(tape.identity), "actions": list(names),
        "native_return": _fraction_record(decision + settlement),
        "decision_sum": _fraction_record(decision),
        "settlement_sum": _fraction_record(settlement),
        "action_counts": {action.name: counts[action.name] for action in
                          (Action.SERVE, Action.REFRESH, Action.SAFE_FALLBACK)},
        "contributions": contributions,
    }
