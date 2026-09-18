"""Research support and UAV/UE visualization suite.

A local, read-only diagnostic toolkit around the repository's existing runs, traces and
environments. Nothing here trains, schedules or launches a research fit, and importing this
package pulls in no renderer, web server or browser library: those live in submodules that
an explicit command imports.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "1.0.0"
