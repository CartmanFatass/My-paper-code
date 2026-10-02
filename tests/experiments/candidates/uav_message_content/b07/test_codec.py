import numpy as np
import pytest
import torch

from experiments.candidates.uav_message_content.b07.codec import (
    fit_ordinary, metric_scales, reconstruct, validate_book,
)
from experiments.candidates.uav_message_content.b07.transport import (
    ByteChannel, ByteCodec, beacon, header, parse_header,
)


def test_hard_forward_and_independent_soft_backward():
    rng = torch.Generator().manual_seed(81)
    book = torch.rand(256, 6, generator=rng, requires_grad=True)
    source = torch.rand(7, 6, generator=rng, requires_grad=True)
    scales = torch.tensor([1., 2., 4., 1., 3., 2.])
    output, indices = reconstruct(source, book, scales, .08)
    assert torch.equal(output, book.detach()[indices])
    weight = torch.randn(7, 6, generator=rng)
    (output * weight).sum().backward()
    independent_book = book.detach().clone().requires_grad_()
    independent_source = source.detach().clone().requires_grad_()
    distance = torch.stack([((independent_source - row) * scales).square().sum(-1)
                            for row in independent_book], -1)
    soft = torch.softmax(-distance / .08, -1) @ independent_book
    expected = torch.autograd.grad((soft * weight).sum(), (independent_book, independent_source))
    torch.testing.assert_close(book.grad, expected[0], atol=2e-6, rtol=2e-6)
    torch.testing.assert_close(source.grad, expected[1], atol=2e-6, rtol=2e-6)
    assert torch.count_nonzero(book.grad) > 6  # gradient through cells, not only selected lookup.


def test_ties_sd_empty_clusters_and_rng_isolation():
    samples = torch.full((256, 6), .3)
    assert torch.equal(metric_scales(samples, "inverse_sd"), torch.full((6,), 20.))
    torch_state = torch.random.get_rng_state().clone()
    numpy_state = np.random.get_state()
    counts = {}
    book, initial, history, distortion = fit_ordinary(samples, torch.ones(6), 19811, counts)
    assert torch.equal(initial, samples)
    assert len(history) == 25 and all(r["empty_clusters"] == 255 for r in history)
    assert counts["nearest_center_comparisons"] == 256 * (256 + 25 * 256 + 256)
    assert distortion < 1e-12
    assert torch.equal(torch_state, torch.random.get_rng_state())
    assert all(np.array_equal(a, b) for a, b in zip(numpy_state, np.random.get_state()))
    duplicate = torch.zeros(256, 6)
    _, indices = reconstruct(torch.zeros(6), duplicate, torch.ones(6))
    assert int(indices) == 0
    with pytest.raises(ValueError):
        validate_book(torch.full((256, 6), float("nan")), torch.ones(6))


@pytest.mark.parametrize("sender", range(5))
@pytest.mark.parametrize("tick", [0, 255])
def test_exact_bytes_header_and_lossless(sender, tick):
    values = np.array([0., .2, .4, .6, .8, 1.], dtype=np.float32)
    book = torch.from_numpy(np.tile(values, (256, 1)))
    for codec in (ByteCodec(book, torch.ones(6)), ByteCodec()):
        packet = codec.encode(values, sender, tick)
        assert len(packet) == (3 if codec.book is not None else 26)
        assert parse_header(packet) == (sender, tick)
        s, t, decoded = codec.decode(packet)
        assert (s, t) == (sender, tick)
        np.testing.assert_array_equal(decoded, np.insert(values, 5, 0))
    assert beacon(tick, True) == bytes([tick, 1])


@pytest.mark.parametrize("packet", [b"", b"\x00\x00\x00", b"\x05\x08\x00", b"\x00\x18\x00", bytearray(3)])
def test_malformed_packets(packet):
    with pytest.raises(ValueError):
        parse_header(packet)
    with pytest.raises(ValueError):
        header(5, 0)
    with pytest.raises(ValueError):
        header(0, 256)


def test_delay_delivery_decoder_self_age_and_no_ack(monkeypatch):
    raw = np.zeros((5, 104), dtype=np.float32)
    raw[:, :3] = .4
    book = torch.full((256, 6), .2)
    codec = ByteCodec(book, torch.ones(6))
    channel = ByteChannel(19811, codec)
    channel.good = False
    channel.begin_tick()
    packet, due = channel.send(raw)
    assert due == 5 and channel.inflight == [(5, packet)] and len(packet) == 3
    assert not channel.records.any()
    # Only the bytes survive in-flight; decoder dictionary is consulted at delivery.
    book[:] = .7
    for _ in range(4):
        channel.advance()
        channel.begin_tick()
        assert not channel.records.any() and channel.pending[0]
    channel.advance()
    channel.begin_tick()
    assert not channel.pending[0]
    np.testing.assert_array_equal(channel.records[1:, 0, :5], np.full((4, 5), .7, dtype=np.float32))
    assert not channel.records[np.arange(5), np.arange(5)].any()
    assert np.all(channel.records[1:, 0, 9] == np.float32(5 / 256))
    # Deadline-derived pending works even if an external receiver delivery is suppressed.
    channel.pending_until[0] = channel.t + 1
    channel.pending[0] = True
    channel.advance()
    channel.begin_tick()
    assert not channel.pending[0]


def test_rr_every_tick_and_terminal_censor():
    raw = np.zeros((5, 104), dtype=np.float32)
    counts = {}
    channel = ByteChannel(77, ByteCodec(torch.zeros(256, 6), torch.ones(6), counts))
    for _ in range(256):
        channel.begin_tick()
        assert not channel.pending[channel.t % 5]
        channel.send(raw)
        channel.advance()
    assert channel.delivered + len(channel.inflight) == 256
    assert counts == {"nearest_center_comparisons": 65536, "packets": 256, "packet_bytes": 768, "beacon_bytes": 512}
