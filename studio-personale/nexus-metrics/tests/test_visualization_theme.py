import unittest

import plotly.graph_objects as go
import plotly.io as pio

from src.visualization.theme import (
    BACKGROUND_COLOR,
    CYBER_PALETTE,
    GRID_COLOR,
    PANEL_COLOR,
    register_plotly_template,
)


class VisualizationThemeTests(unittest.TestCase):
    def test_registers_neon_dark_plotly_template(self):
        register_plotly_template()
        template = pio.templates["nexus_neon"]

        self.assertEqual(template.layout.paper_bgcolor, BACKGROUND_COLOR)
        self.assertEqual(template.layout.plot_bgcolor, PANEL_COLOR)
        self.assertEqual(list(template.layout.colorway), CYBER_PALETTE)
        self.assertEqual(template.layout.xaxis.gridcolor, GRID_COLOR)
        self.assertEqual(template.layout.yaxis.gridcolor, GRID_COLOR)

    def test_registered_theme_can_render_a_plotly_figure(self):
        register_plotly_template()
        figure = go.Figure(
            data=[go.Scatter(x=["2026-01", "2026-02"], y=[40, 55])],
            layout={"template": "nexus_neon"},
        )

        self.assertEqual(len(figure.data), 1)
        self.assertEqual(
            figure.layout.template.layout.paper_bgcolor, BACKGROUND_COLOR)


if __name__ == "__main__":
    unittest.main()
