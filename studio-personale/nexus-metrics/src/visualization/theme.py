from typing import Any, Dict, List

import plotly.graph_objects as go
import plotly.io as pio

CYBER_PALETTE: List[str] = [
    "#B3F3F6",
    "#FF5500",
    "#FFFF00",
    "#FF0000",
    "#74EE15",
    "#FF007F",
    "#8A2BE2",
]
BACKGROUND_COLOR = "#0D0E15"
PANEL_COLOR = "#141521"
GRID_COLOR = "#1E2035"
TEXT_COLOR = "#E6F7FF"
MUTED_TEXT_COLOR = "#8A94A8"
ACCENT_COLOR = "#00E5FF"


def plotly_layout() -> Dict[str, Any]:
    return {
        "paper_bgcolor": "rgba(0, 0, 0, 0)",
        "plot_bgcolor": "rgba(0, 0, 0, 0)",
        "font": {"color": TEXT_COLOR, "family": "Inter, Segoe UI, sans-serif"},
        "colorway": CYBER_PALETTE,
        "margin": {"l": 24, "r": 24, "t": 64, "b": 24},
        "xaxis": {
            "gridcolor": GRID_COLOR,
            "linecolor": GRID_COLOR,
            "zerolinecolor": GRID_COLOR,
            "title": {"font": {"color": MUTED_TEXT_COLOR}},
        },
        "yaxis": {
            "gridcolor": GRID_COLOR,
            "linecolor": GRID_COLOR,
            "zerolinecolor": GRID_COLOR,
            "title": {"font": {"color": MUTED_TEXT_COLOR}},
        },
        "legend": {"bgcolor": "rgba(0, 0, 0, 0)"},
        "hoverlabel": {
            "bgcolor": PANEL_COLOR,
            "bordercolor": ACCENT_COLOR,
            "font": {"color": TEXT_COLOR},
        },
    }


def register_plotly_template() -> None:
    pio.templates["nexus_neon"] = go.layout.Template(
        layout={
            **plotly_layout(),
            "paper_bgcolor": BACKGROUND_COLOR,
            "plot_bgcolor": PANEL_COLOR,
        }
    )
    pio.templates.default = "nexus_neon"
