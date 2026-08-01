from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 in the registered CPU environment.
    import tomli as tomllib


ROLE_REF = re.compile(r"(?<![\w.])\.agents/roles/[A-Za-z0-9_.-]+\.md")
BACKTICK = re.compile(r"`([^`\r\n]+)`")
DEFAULT_ACTIVE_PATHS = (
    "AGENTS.md",
    ".agents/roles",
    ".agents/skills",
    ".codex/config.toml",
    ".codex/agents",
)
DEFAULT_FORBIDDEN = (
    "superpowers_execution=enabled",
    "workflow_hash_validation=enabled",
    "global_write_lease=enabled",
    "path_hash_source_status",
    "hmasd-dispatch-task",
)
CONTROL_PLANE_LINE_BUDGET = 1000
CONTROL_PLANE_BUDGET_PATHS = (
    "AGENTS.md",
    ".agents/roles/WORKFLOW_DESIGN_MANAGER.md",
    ".agents/skills/hmasd-collaborative-workflow-design/SKILL.md",
    ".agents/skills/hmasd-workflow-change-audit/SKILL.md",
    ".agents/skills/hmasd-cross-task-routing/SKILL.md",
    "docs/project/SESSION_WORKSPACE_CONTRACT.md",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_toml(path: Path, errors: list[str]) -> dict:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        errors.append(f"invalid TOML {path}: {exc}")
        return {}


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
    elif path.is_dir():
        yield from sorted(item for item in path.rglob("*") if item.is_file())


def _repo_refs(text: str) -> set[str]:
    refs: set[str] = set()
    for value in BACKTICK.findall(text):
        value = value.replace("\\", "/")
        if not value.startswith((".agents/", ".codex/", "docs/", "scripts/")):
            continue
        if any(char in value for char in "*<>|") or " " in value:
            continue
        refs.add(value.rstrip(".,:;"))
    return refs


def _developer_instruction_bytes(path: Path) -> bytes | None:
    match = re.search(
        br'(?s)developer_instructions\s*=\s*"""(.*?)"""', path.read_bytes()
    )
    return match.group(1) if match else None


def _check_benchmark_fairness(
    profiles: dict[str, tuple[Path, dict]], errors: list[str]
) -> None:
    identity_fields = {
        "name",
        "description",
        "model",
        "model_reasoning_effort",
        "nickname_candidates",
    }
    for benchmark_class in ("implementer", "reviewer"):
        prefix = f"hmasd-benchmark-{benchmark_class}-"
        members = sorted(
            (name, path, profile)
            for name, (path, profile) in profiles.items()
            if name.startswith(prefix)
        )
        if not members:
            continue
        if len(members) != 3:
            errors.append(
                f"benchmark {benchmark_class} profile count must be 3; "
                f"found {len(members)}"
            )
            continue
        instruction_blocks = [_developer_instruction_bytes(path) for _, path, _ in members]
        if any(block is None for block in instruction_blocks):
            errors.append(
                f"benchmark {benchmark_class} developer_instructions cannot be parsed"
            )
        elif instruction_blocks[0] != instruction_blocks[1] or instruction_blocks[0] != instruction_blocks[2]:
            errors.append(
                f"benchmark {benchmark_class} developer_instructions differ byte-for-byte"
            )
        invariant_payloads = [
            {key: value for key, value in profile.items() if key not in identity_fields}
            for _, _, profile in members
        ]
        if invariant_payloads[0] != invariant_payloads[1] or invariant_payloads[0] != invariant_payloads[2]:
            errors.append(
                f"benchmark {benchmark_class} varies a non-identity field other than "
                "model or model_reasoning_effort"
            )


def _check_control_plane_line_budget(repo: Path, errors: list[str]) -> None:
    total = 0
    for raw_path in CONTROL_PLANE_BUDGET_PATHS:
        path = (repo / raw_path).resolve()
        if not _within(path, repo) or not path.is_file():
            errors.append(f"missing control-plane budget path: {raw_path}")
            continue
        try:
            total += len(_read(path).splitlines())
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"unreadable control-plane budget path {raw_path}: {exc}")
    if total > CONTROL_PLANE_LINE_BUDGET:
        errors.append(
            "control-plane line budget exceeded: "
            f"{total}>{CONTROL_PLANE_LINE_BUDGET}"
        )


def audit_repo(
    repo: Path,
    extra_active_paths: Iterable[str] = (),
    extra_forbidden: Iterable[str] = (),
) -> list[str]:
    repo = repo.resolve()
    errors: list[str] = []
    config_path = repo / ".codex/config.toml"
    profile_root = repo / ".codex/agents"
    role_root = repo / ".agents/roles"
    skill_root = repo / ".agents/skills"
    agents_path = repo / "AGENTS.md"

    for required in (config_path, profile_root, role_root, skill_root, agents_path):
        if not required.exists():
            errors.append(f"missing harness surface: {required}")
    if errors:
        return errors

    _check_control_plane_line_budget(repo, errors)

    config = _load_toml(config_path, errors)
    agents_table = config.get("agents", {})
    registry = {
        name: value
        for name, value in agents_table.items()
        if isinstance(value, dict) and "config_file" in value
    }
    if not registry:
        errors.append("native agent registry is empty")

    registered_paths: dict[Path, str] = {}
    routed_roles: set[Path] = set()
    profile_names: dict[str, Path] = {}
    profile_records: dict[str, tuple[Path, dict]] = {}
    for registry_name, entry in sorted(registry.items()):
        raw_config_file = entry.get("config_file")
        if not isinstance(raw_config_file, str):
            errors.append(f"registry entry {registry_name} has no string config_file")
            continue
        profile_path = (config_path.parent / raw_config_file).resolve()
        if not _within(profile_path, repo):
            errors.append(f"registry entry {registry_name} escapes repository: {raw_config_file}")
            continue
        if profile_path in registered_paths:
            errors.append(
                f"profile registered more than once: {profile_path} "
                f"({registered_paths[profile_path]}, {registry_name})"
            )
        registered_paths[profile_path] = registry_name
        if not profile_path.is_file():
            errors.append(f"registered profile is missing: {profile_path}")
            continue

        profile = _load_toml(profile_path, errors)
        for field in (
            "name",
            "model",
            "model_reasoning_effort",
            "sandbox_mode",
            "approval_policy",
            "developer_instructions",
        ):
            if not isinstance(profile.get(field), str) or not profile[field].strip():
                errors.append(f"profile {profile_path.name} missing string field: {field}")
        name = profile.get("name")
        if isinstance(name, str):
            if name != profile_path.stem:
                errors.append(
                    f"profile name/path mismatch: {profile_path.name} declares {name}"
                )
            if name in profile_names:
                errors.append(
                    f"duplicate profile name {name}: {profile_names[name]} and {profile_path}"
                )
            profile_names[name] = profile_path
            profile_records[name] = (profile_path, profile)

        instructions = profile.get("developer_instructions", "")
        role_refs = sorted(set(ROLE_REF.findall(instructions)))
        if len(role_refs) != 1:
            errors.append(
                f"profile {profile_path.name} must name exactly one role charter; "
                f"found {len(role_refs)}"
            )
            continue
        role_path = (repo / role_refs[0]).resolve()
        routed_roles.add(role_path)
        if not role_path.is_file():
            errors.append(f"profile {profile_path.name} references missing role: {role_refs[0]}")
            continue
        role_text = _read(role_path)
        if not re.search(r"(?m)^role=[a-z0-9_]+\s*$", role_text):
            errors.append(f"role charter has no role identity: {role_path}")
        callable_match = re.search(
            r"(?m)^callable_agent_type=([a-z0-9_.-]+)\s*$", role_text
        )
        if callable_match and isinstance(name, str):
            callable_name = callable_match.group(1)
            if name != callable_name and not name.startswith(callable_name + "-"):
                errors.append(
                    f"profile/role callable mismatch: {name} vs {callable_name}"
                )
        for role_key, profile_key in (
            ("model", "model"),
            ("reasoning_effort", "model_reasoning_effort"),
        ):
            match = re.search(rf"(?m)^{role_key}=([^\s]+)\s*$", role_text)
            if match and match.group(1) != profile.get(profile_key):
                errors.append(
                    f"profile/role {role_key} mismatch for {profile_path.name}: "
                    f"{profile.get(profile_key)} vs {match.group(1)}"
                )

    disk_profiles = {path.resolve() for path in profile_root.glob("*.toml")}
    for path in sorted(disk_profiles - set(registered_paths)):
        errors.append(f"unregistered profile: {path}")
    for path in sorted(set(registered_paths) - disk_profiles):
        errors.append(f"registry path is not an agent profile: {path}")
    _check_benchmark_fairness(profile_records, errors)

    agents_text = _read(agents_path)
    for ref in ROLE_REF.findall(agents_text):
        routed_roles.add((repo / ref).resolve())
    disk_roles = {path.resolve() for path in role_root.glob("*.md")}
    for path in sorted(disk_roles - routed_roles):
        errors.append(f"unrouted role charter: {path}")
    for path in sorted(routed_roles - disk_roles):
        errors.append(f"routed role charter is missing: {path}")

    skill_docs = {
        path.parent.name: path.resolve() for path in skill_root.glob("*/SKILL.md")
    }
    route_texts = [agents_text]
    manager_roles = (role_root / "CODE_PROJECT_MANAGER.md",)
    route_texts.extend(_read(path) for path in manager_roles if path.is_file())
    route_texts.extend(_read(path) for path in skill_docs.values())
    route_blob = "\n".join(route_texts)
    for name, path in sorted(skill_docs.items()):
        if name not in route_blob:
            errors.append(f"unrouted Skill: {path}")
    for directory in sorted(path for path in skill_root.iterdir() if path.is_dir()):
        contains_files = any(path.is_file() for path in directory.rglob("*"))
        if contains_files and not (directory / "SKILL.md").is_file():
            errors.append(f"Skill directory has no SKILL.md: {directory}")

    for route_path in (agents_path, *manager_roles):
        if not route_path.is_file():
            continue
        for ref in sorted(_repo_refs(_read(route_path))):
            if not (repo / ref).exists():
                errors.append(f"broken active path reference in {route_path}: {ref}")

    active_paths = list(DEFAULT_ACTIVE_PATHS) + list(extra_active_paths)
    forbidden = tuple(DEFAULT_FORBIDDEN) + tuple(extra_forbidden)
    for raw_path in active_paths:
        path = (repo / raw_path).resolve()
        if not _within(path, repo):
            errors.append(f"active path escapes repository: {raw_path}")
            continue
        if not path.exists():
            errors.append(f"active path is missing: {raw_path}")
            continue
        for file_path in _files(path):
            if file_path.suffix.lower() not in {".md", ".toml"}:
                continue
            try:
                text = _read(file_path)
            except UnicodeDecodeError:
                continue
            for marker in forbidden:
                if marker and marker in text:
                    errors.append(f"forbidden active marker {marker!r} in {file_path}")

    return errors


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check dynamic closure of the HMASD agent/workflow harness."
    )
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--active-path", action="append", default=[])
    parser.add_argument("--forbid", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    errors = audit_repo(args.repo, args.active_path, args.forbid)
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    repo = args.repo.resolve()
    profiles = len(list((repo / ".codex/agents").glob("*.toml")))
    roles = len(list((repo / ".agents/roles").glob("*.md")))
    skills = len(list((repo / ".agents/skills").glob("*/SKILL.md")))
    print(f"HMASD_AGENT_HARNESS_OK profiles={profiles} roles={roles} skills={skills}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
