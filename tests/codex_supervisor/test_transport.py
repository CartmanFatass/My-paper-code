from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tools.codex_supervisor.protocol import ProtocolError, ProtocolLineTooLarge, encode_jsonl
from tools.codex_supervisor.transport import AppServerTransport, TransportClosed, process_exec_argv


def _run(coro):
    return asyncio.run(coro)


def _transport(tmp_path: Path, mode: str, extra_env: dict[str, str] | None = None, **config_overrides: object) -> AppServerTransport:
    binary = write_fake_codex(tmp_path)
    config = make_observer_config(tmp_path, **config_overrides)
    env = {"FAKE_APP_SERVER_MODE": mode}
    if extra_env:
        env.update(extra_env)
    return AppServerTransport(
        binary,
        config,
        process_cwd=tmp_path,
        stderr_path=tmp_path / "stderr.log",
        stdin_close_timeout=0.4,
        terminate_timeout=0.4,
        extra_env=env,
    )


def test_transport_writes_and_reads_jsonl(tmp_path: Path) -> None:
    async def body() -> None:
        transport = _transport(tmp_path, "handshake_ok")
        await transport.start()
        assert transport.process_id is not None
        sent = {"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "t", "version": "0"}}}
        encoded = await transport.send(sent)
        assert b"jsonrpc" not in encoded
        assert encoded == encode_jsonl(sent)
        message = await transport.recv()
        assert message.transport_seq == 1
        assert message.payload["id"] == 1
        assert "result" in message.payload
        await transport.stop()

    _run(body())


@pytest.mark.skipif(os.name != "nt", reason="Windows command-processor shape")
def test_process_exec_argv_uses_one_exact_spaced_batch_command(tmp_path: Path) -> None:
    binary = tmp_path / "directory with spaces" / "codex app shim.cmd"
    argv = process_exec_argv(binary)
    assert argv == [
        os.environ.get("COMSPEC") or "cmd.exe",
        "/d",
        "/s",
        "/c",
        "call",
        str(binary),
        "app-server",
    ]
    assert argv.count("app-server") == 1
    assert subprocess.list2cmdline(argv).endswith(f'call "{binary}" app-server')


@pytest.mark.skipif(os.name != "nt", reason="Windows command-processor shape")
def test_transport_runs_spaced_batch_path_end_to_end(tmp_path: Path) -> None:
    async def body() -> None:
        binary_directory = tmp_path / "Codex (ordinary) directory with spaces"
        binary_directory.mkdir()
        generated = write_fake_codex(binary_directory)
        binary = generated.with_name("codex app shim.cmd")
        generated.rename(binary)
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            binary,
            config,
            process_cwd=tmp_path,
            stderr_path=tmp_path / "spaced-stderr.log",
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
            extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok"},
        )
        await transport.start()
        assert transport.process_id is not None
        await transport.send(
            {"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "t", "version": "0"}}}
        )
        message = await transport.recv()
        assert message.payload["id"] == 1
        assert "result" in message.payload
        await transport.stop()

    _run(body())


@pytest.mark.skipif(os.name != "nt", reason="Windows command-processor shape")
def test_process_exec_argv_rejects_batch_shell_metacharacters(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="metacharacters"):
        process_exec_argv(tmp_path / "unsafe&codex.cmd")
    with pytest.raises(ValueError, match="metacharacters"):
        process_exec_argv(tmp_path / "unsafe %name%" / "codex.cmd")


def test_transport_records_stderr_separately(tmp_path: Path) -> None:
    async def body() -> None:
        transport = _transport(tmp_path, "stderr_then_exit")
        await transport.start()
        with pytest.raises(TransportClosed, match="stdout EOF"):
            await transport.recv()
        await transport.stop()
        text = (tmp_path / "stderr.log").read_text(encoding="utf-8")
        assert "diagnostic only" in text

    _run(body())


def test_transport_reports_eof(tmp_path: Path) -> None:
    async def body() -> None:
        transport = _transport(tmp_path, "stderr_then_exit")
        await transport.start()
        with pytest.raises(TransportClosed, match="stdout EOF"):
            await transport.recv()
        assert transport.end_action == "eof"
        action = await transport.stop()
        assert action == "eof"

    _run(body())


def test_transport_rejects_oversized_line(tmp_path: Path) -> None:
    async def body() -> None:
        transport = _transport(
            tmp_path,
            "oversized_line",
            extra_env={"FAKE_OVERSIZE_BYTES": "8192"},
            max_jsonl_line_bytes=4096,
        )
        await transport.start()
        with pytest.raises(ProtocolLineTooLarge):
            await transport.recv()
        assert transport.end_action == "line_too_large"
        await transport.stop()

    _run(body())


def test_transport_rejects_malformed_line(tmp_path: Path) -> None:
    async def body() -> None:
        transport = _transport(tmp_path, "malformed_line")
        await transport.start()
        with pytest.raises(ProtocolError):
            await transport.recv()
        assert transport.end_action == "malformed"
        await transport.stop()

    _run(body())


def test_stop_terminates_then_kills_after_timeout(tmp_path: Path) -> None:
    async def body() -> None:
        transport = _transport(tmp_path, "hang")
        await transport.start()
        pid = transport.process_id
        assert pid is not None
        action = await transport.stop()
        assert action in {"terminated", "killed"}
        assert transport._process is not None
        assert transport._process.returncode is not None

    _run(body())
