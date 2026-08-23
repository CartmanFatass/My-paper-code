"""Explicit, immutable-per-process supervisor runtime profiles.

Profiles are an allowlist for the long-lived supervisor host command channel.
They do not grant semantic authority and do not create managed actors, turns,
or mailbox delivery by themselves.
"""

from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import Final, FrozenSet, Mapping


class RuntimeProfile(str, Enum):
    """The fixed command surface selected when a supervisor host starts."""

    OBSERVER = "OBSERVER"
    MANAGED_MANUAL = "MANAGED_MANUAL"
    MAILBOX_MANUAL = "MAILBOX_MANUAL"
    SINGLE_WAKE = "SINGLE_WAKE"


class CommandKind(str, Enum):
    """Typed commands accepted by the supervisor host control channel."""

    STATUS = "STATUS"
    STOP = "STOP"
    INSPECT = "INSPECT"
    MANAGED_CREATE = "MANAGED_CREATE"
    MANAGED_ADOPT = "MANAGED_ADOPT"
    MANAGED_VERIFY = "MANAGED_VERIFY"
    MANAGED_TURN = "MANAGED_TURN"
    MANAGED_SUSPEND = "MANAGED_SUSPEND"
    MANAGED_REVOKE = "MANAGED_REVOKE"
    MAILBOX_ENQUEUE = "MAILBOX_ENQUEUE"
    MAILBOX_LIST = "MAILBOX_LIST"
    MAILBOX_DELIVER_ONCE = "MAILBOX_DELIVER_ONCE"
    ARM_SINGLE_WAKE = "ARM_SINGLE_WAKE"


class ProfileError(ValueError):
    """Raised when a host command is invalid for its fixed runtime profile."""


class CommandNotAllowed(ProfileError):
    """Raised when a profile's command allowlist excludes a command."""

    def __init__(self, profile: RuntimeProfile, command: CommandKind) -> None:
        self.profile = profile
        self.command = command
        super().__init__(
            f"command {command.value} is not allowed for profile {profile.value}"
        )


ALLOWED_COMMANDS: Final[Mapping[RuntimeProfile, FrozenSet[CommandKind]]] = MappingProxyType(
    {
        RuntimeProfile.OBSERVER: frozenset(
            {
                CommandKind.STATUS,
                CommandKind.STOP,
                CommandKind.INSPECT,
            }
        ),
        RuntimeProfile.MANAGED_MANUAL: frozenset(
            {
                CommandKind.STATUS,
                CommandKind.STOP,
                CommandKind.INSPECT,
                CommandKind.MANAGED_CREATE,
                CommandKind.MANAGED_ADOPT,
                CommandKind.MANAGED_VERIFY,
                CommandKind.MANAGED_TURN,
                CommandKind.MANAGED_SUSPEND,
                CommandKind.MANAGED_REVOKE,
            }
        ),
        RuntimeProfile.MAILBOX_MANUAL: frozenset(
            {
                CommandKind.STATUS,
                CommandKind.STOP,
                CommandKind.INSPECT,
                CommandKind.MANAGED_SUSPEND,
                CommandKind.MANAGED_REVOKE,
                CommandKind.MAILBOX_ENQUEUE,
                CommandKind.MAILBOX_LIST,
                CommandKind.MAILBOX_DELIVER_ONCE,
            }
        ),
        RuntimeProfile.SINGLE_WAKE: frozenset(
            {
                CommandKind.STATUS,
                CommandKind.STOP,
                CommandKind.INSPECT,
                CommandKind.MAILBOX_ENQUEUE,
                CommandKind.MAILBOX_LIST,
                CommandKind.ARM_SINGLE_WAKE,
            }
        ),
    }
)


def require_command_allowed(profile: RuntimeProfile, command: CommandKind) -> None:
    """Require ``command`` to be in the host's fixed profile allowlist.

    A caller changing profiles must stop the current host and start another
    process; this function only evaluates the already-selected profile.
    """

    if not isinstance(profile, RuntimeProfile):
        raise ProfileError(f"invalid runtime profile: {profile!r}")
    if not isinstance(command, CommandKind):
        raise ProfileError(f"invalid command kind: {command!r}")
    if command not in ALLOWED_COMMANDS[profile]:
        raise CommandNotAllowed(profile, command)
