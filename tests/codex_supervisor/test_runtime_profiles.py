import pytest

from tools.codex_supervisor.runtime_profiles import (
    ALLOWED_COMMANDS,
    CommandKind,
    CommandNotAllowed,
    ProfileError,
    RuntimeProfile,
    require_command_allowed,
)


def allowed(profile: RuntimeProfile, command: CommandKind) -> bool:
    try:
        require_command_allowed(profile, command)
    except CommandNotAllowed:
        return False
    return True


def test_observer_profile_is_read_only() -> None:
    assert allowed(RuntimeProfile.OBSERVER, CommandKind.STATUS)
    assert allowed(RuntimeProfile.OBSERVER, CommandKind.INSPECT)
    assert not allowed(RuntimeProfile.OBSERVER, CommandKind.MANAGED_TURN)


def test_single_wake_profile_forbids_scheduler_serve() -> None:
    assert allowed(RuntimeProfile.SINGLE_WAKE, CommandKind.ARM_SINGLE_WAKE)
    assert "SCHEDULER_SERVE" not in {item.value for item in CommandKind}


def test_profile_matrix_is_exact() -> None:
    assert ALLOWED_COMMANDS == {
        RuntimeProfile.OBSERVER: {
            CommandKind.STATUS,
            CommandKind.STOP,
            CommandKind.INSPECT,
        },
        RuntimeProfile.MANAGED_MANUAL: {
            CommandKind.STATUS,
            CommandKind.STOP,
            CommandKind.INSPECT,
            CommandKind.MANAGED_CREATE,
            CommandKind.MANAGED_ADOPT,
            CommandKind.MANAGED_VERIFY,
            CommandKind.MANAGED_TURN,
            CommandKind.MANAGED_SUSPEND,
            CommandKind.MANAGED_REVOKE,
        },
        RuntimeProfile.MAILBOX_MANUAL: {
            CommandKind.STATUS,
            CommandKind.STOP,
            CommandKind.INSPECT,
            CommandKind.MANAGED_SUSPEND,
            CommandKind.MANAGED_REVOKE,
            CommandKind.MAILBOX_ENQUEUE,
            CommandKind.MAILBOX_LIST,
            CommandKind.MAILBOX_DELIVER_ONCE,
        },
        RuntimeProfile.SINGLE_WAKE: {
            CommandKind.STATUS,
            CommandKind.STOP,
            CommandKind.INSPECT,
            CommandKind.MAILBOX_ENQUEUE,
            CommandKind.MAILBOX_LIST,
            CommandKind.ARM_SINGLE_WAKE,
        },
    }


def test_disallowed_command_raises_typed_error() -> None:
    with pytest.raises(CommandNotAllowed, match="MANAGED_TURN.*OBSERVER"):
        require_command_allowed(RuntimeProfile.OBSERVER, CommandKind.MANAGED_TURN)


@pytest.mark.parametrize("profile", ["OBSERVER", None])
def test_invalid_profile_is_rejected(profile: object) -> None:
    with pytest.raises(ProfileError, match="invalid runtime profile"):
        require_command_allowed(profile, CommandKind.STATUS)  # type: ignore[arg-type]


def test_invalid_command_is_rejected() -> None:
    with pytest.raises(ProfileError, match="invalid command kind"):
        require_command_allowed(RuntimeProfile.OBSERVER, "STATUS")  # type: ignore[arg-type]
