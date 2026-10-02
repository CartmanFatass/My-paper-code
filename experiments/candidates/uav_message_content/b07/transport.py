"""Actual byte packets; send-time pending facts and delivery-time decoding."""

import struct
import time

import numpy as np
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.channel import Channel, payloads
from .codec import reconstruct, validate_book
from .contract import FIELDS, increment, require


def header(sender, tick):
    require(isinstance(sender, int) and 0 <= sender < 5 and isinstance(tick, int) and 0 <= tick < 256,
            "header bounds")
    # Little-endian: sender[0:3], tick[3:11], valid[11], reserved[12:16]=0.
    return struct.pack("<H", sender | (tick << 3) | (1 << 11))


def parse_header(packet):
    require(isinstance(packet, bytes) and len(packet) in (3, 26), "packet length/type")
    word = struct.unpack("<H", packet[:2])[0]
    sender, tick = word & 7, (word >> 3) & 255
    require(sender < 5 and word & (1 << 11) and word >> 12 == 0, "invalid header")
    return sender, tick


def beacon(tick, good):
    require(0 <= tick < 256 and good in (False, True), "beacon bounds")
    return bytes((tick, int(good)))


def source_for(raw, sender):
    return payloads(raw)[sender, list(FIELDS)].copy()


class ByteCodec:
    def __init__(self, book=None, scales=None, counts=None):
        require((book is None) == (scales is None), "book/scales pair required")
        if book is not None:
            validate_book(book, scales)
        self.book, self.scales, self.counts = book, scales, counts
        self.encode_cpu_seconds = self.decode_cpu_seconds = 0.

    def encode(self, source, sender, tick):
        started = time.process_time()
        source = np.asarray(source)
        require(source.shape == (6,) and source.dtype == np.float32 and np.isfinite(source).all()
                and ((source >= 0) & (source <= 1)).all(), "source six FP32 unit values")
        if self.book is None:
            body = source.astype("<f4").tobytes()
        else:
            with torch.no_grad():
                _, index = reconstruct(torch.from_numpy(source), self.book, self.scales, counts=self.counts)
            body = bytes((int(index),))
        packet = header(sender, tick) + body
        self.encode_cpu_seconds += time.process_time() - started
        return packet

    def decode(self, packet):
        started = time.process_time()
        sender, tick = parse_header(packet)
        require(len(packet) == (26 if self.book is None else 3), "codec packet length")
        source = np.frombuffer(packet[2:], dtype="<f4").copy() if self.book is None else self.book[packet[2]].detach().numpy().copy()
        require(np.isfinite(source).all() and ((source >= 0) & (source <= 1)).all(), "decoded values")
        geometry = np.zeros(7, dtype=np.float32)
        geometry[list(FIELDS)] = source
        self.decode_cpu_seconds += time.process_time() - started
        return sender, tick, geometry


class ByteChannel(Channel):
    def __init__(self, seed, codec):
        super().__init__(seed)
        self.codec = codec
        self.pending_until = np.full(5, -1, dtype=np.int32)

    def begin_tick(self):
        # Own pending clears by the known deterministic deadline, never receiver ACK.
        self.pending = self.pending_until > self.t
        later, self.delivered_events = [], []
        for due, packet in self.inflight:
            if due <= self.t:
                sender, sent, geometry = self.codec.decode(packet)
                peers = np.arange(5) != sender
                self.records[peers, sender, :7] = geometry
                self.records[peers, sender, 7] = 1
                self.records[peers, sender, 8] = sent / 256
                self.delivered += 1
                self.delivered_events.append((sender, sent, due))
            else:
                later.append((due, packet))
        self.inflight = later
        valid = self.records[..., 7] > 0
        self.records[..., 9] = np.where(valid, self.t / 256 - self.records[..., 8], 0)
        self.age_sum += float(self.records[..., 9].sum() * 256)
        self.age_count += int(valid.sum())

    def send(self, raw):
        sender = self.t % 5
        require(not self.pending[sender], "RR sender pending")
        packet = self.codec.encode(source_for(raw, sender), sender, self.t)
        due = self.t + (1 if self.good else 5)
        self.inflight.append((due, packet))
        self.pending_until[sender] = due
        self.pending[sender] = True
        self.attempts += 1
        self.accepted += 1
        self.max_pending = max(self.max_pending, int(self.pending.sum()))
        if self.codec.counts is not None:
            increment(self.codec.counts, "packets")
            increment(self.codec.counts, "packet_bytes", len(packet))
            increment(self.codec.counts, "beacon_bytes", 2)
        return packet, due
