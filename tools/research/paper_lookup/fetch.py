"""Explicit, credential-free network boundary for named paper endpoints.

Adapted from K-Dense Inc.'s MIT-licensed
skills/paper-lookup/scripts/paginate.py and _common.py at commit
f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f.

Copyright (c) 2025 K-Dense Inc.
MIT License: permission is hereby granted, free of charge, to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies, subject
to inclusion of this copyright and permission notice in copies or substantial
portions. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    from .normalizers import PaperLookupInputError
except ImportError:  # Direct CLI execution has no package context.
    from normalizers import PaperLookupInputError

_ENDPOINTS = {
    "arxiv": "https://export.arxiv.org/api/query",
    "openalex": "https://api.openalex.org/works",
}
_FORBIDDEN_PARAMETER_NAMES = frozenset({"api_key", "apikey", "key", "email", "mailto", "token", "authorization"})
_MAX_TIMEOUT_SECONDS = 30


def fetch_named_endpoint(
    endpoint: str,
    parameters: object,
    *,
    allow_network: bool = False,
    timeout_seconds: int = 10,
) -> dict[str, Any]:
    """Fetch one named public endpoint only after explicit opt-in.

    This boundary never reads environment variables, accepts credentials, or
    accepts arbitrary URLs. Callers retain the raw response for normalization.
    """
    if not allow_network:
        raise PaperLookupInputError("network access is disabled; pass explicit allow_network=True")
    if endpoint not in _ENDPOINTS:
        raise PaperLookupInputError(f"endpoint must be one of {sorted(_ENDPOINTS)}, not {endpoint!r}")
    if not isinstance(timeout_seconds, int) or isinstance(timeout_seconds, bool) or not 1 <= timeout_seconds <= _MAX_TIMEOUT_SECONDS:
        raise PaperLookupInputError(f"timeout_seconds must be an integer from 1 to {_MAX_TIMEOUT_SECONDS}")
    if not isinstance(parameters, Mapping):
        raise PaperLookupInputError("parameters must be an object of string values")
    normalized_parameters: dict[str, str] = {}
    for name, value in parameters.items():
        if not isinstance(name, str) or not isinstance(value, str):
            raise PaperLookupInputError("parameters must contain only string names and values")
        if name.lower() in _FORBIDDEN_PARAMETER_NAMES:
            raise PaperLookupInputError(f"credentials and personal contact values are not accepted: {name}")
        normalized_parameters[name] = value

    url = f"{_ENDPOINTS[endpoint]}?{urlencode(sorted(normalized_parameters.items()))}"
    request = Request(url, headers={"Accept": "application/atom+xml, application/json", "User-Agent": "hmasd-paper-lookup/1"})
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - URL is fixed above.
        body = response.read().decode("utf-8", errors="replace")
        status = response.status
    return {
        "endpoint": endpoint,
        "endpoint_parameters": dict(sorted(normalized_parameters.items())),
        "http_status": status,
        "response_body": body,
    }


def parse_parameter_json(text: str) -> Mapping[str, str]:
    try:
        payload: Any = json.loads(text)
    except json.JSONDecodeError as error:
        raise PaperLookupInputError(f"parameters JSON is invalid: {error}") from error
    if not isinstance(payload, Mapping):
        raise PaperLookupInputError("parameters JSON must be an object")
    return payload
