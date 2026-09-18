"""Figure contract and capability charts.

Importing this package selects the non-interactive ``Agg`` backend (see
:mod:`~tools.research_support.plots.figure`), which is why no shared training module may
import it. Charts are standalone functions rather than a plugin framework: one function,
one research question, one input contract.
"""

from .figure import (
    DEFAULT_SYNTHETIC_BANNER,
    MISSING_PREFIX,
    FigureResult,
    FigureSpec,
    apply_method_style,
    close_figure,
    ensure_agg_backend,
    export_figure,
    missing_panel,
    new_figure,
    read_table_csv,
    render_rgb_array,
    software_versions,
)

__all__ = [
    "DEFAULT_SYNTHETIC_BANNER",
    "MISSING_PREFIX",
    "FigureResult",
    "FigureSpec",
    "apply_method_style",
    "close_figure",
    "ensure_agg_backend",
    "export_figure",
    "missing_panel",
    "new_figure",
    "read_table_csv",
    "render_rgb_array",
    "software_versions",
]
