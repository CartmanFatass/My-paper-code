"""Compatibility entrypoint for the unified HMASD configuration.

Use ``config_1.Config`` as the single source of truth. This module exists so
older commands using ``--config config`` load the same configuration instead
of the obsolete standalone Config class.
"""

from config_1 import Config

