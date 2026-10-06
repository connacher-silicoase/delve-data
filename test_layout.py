"""Geometry regressions: text edits and graph filters must not break layout."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx
import numpy as np

from chart_layout import Chart, place_box
from avatars import pair_boxes
from network_layout import network_positions


class LayoutTests(unittest.TestCase):
    def test_pair_columns_do_not_overlap_at_export_resolution(self):
        with TemporaryDirectory() as folder:
            fig, ax = plt.subplots()
            ax.set_axis_off()
            boxes = pair_boxes(fig, Path(folder), [('short', 'other'), ('longer-user-name', 'second-user')])
            for y, box in zip((0.7, 0.3), boxes):
                place_box(ax, box, (0, y), alignment=(0, 0.5))
            for dpi in (100, 400):
                fig.set_dpi(dpi)
                fig.canvas.draw()
                renderer = fig.canvas.get_renderer()
                for box in boxes:
                    left, arrow, right = box.get_children()
                    self.assertLess(left.get_children()[0].get_window_extent(renderer).x1,
                                    arrow.get_window_extent(renderer).x0)
                    self.assertLess(arrow.get_window_extent(renderer).x1,
                                    right.get_children()[0].get_window_extent(renderer).x0)
            plt.close(fig)

    def test_long_header_footer_and_legend_stay_in_separate_regions(self):
        with TemporaryDirectory() as folder:
            data = Path(folder) / 'posts.csv'
            data.with_suffix('.meta.json').write_text(json.dumps({'accessed_at': '2026-10-06T22:26:56+00:00'}))
            chart = Chart('A longer chart title that wraps into multiple lines ' * 2, data,
                          subtitle='A subtitle that can grow without manual coordinate changes',
                          notes='Longer notes that wrap automatically. ' * 8)
            ax = chart.with_legend([Line2D([], [], label='611,000 interactions')], 'Interactions')
            ax.plot([0, 1], [0, 1])
            ax.set_xlabel('An axis label')
            chart.finalize()
            renderer = chart.fig.canvas.get_renderer()
            header, footer = chart.fig.axes[:2]
            hbox = header.artists[0].get_window_extent(renderer)
            fbox = footer.artists[0].get_window_extent(renderer)
            chart_box = ax.get_tightbbox(renderer)
            self.assertGreater(hbox.y0, chart_box.y1)
            self.assertLess(fbox.y1, chart_box.y0)
            legend_box = chart.fig.axes[-1].get_legend().get_window_extent(renderer)
            self.assertGreater(legend_box.x0, ax.get_window_extent(renderer).x1)
            for box in (hbox, fbox, legend_box):
                self.assertGreaterEqual(box.x0, 0)
                self.assertGreaterEqual(box.y0, 0)
                self.assertLessEqual(box.x1, chart.fig.bbox.width)
                self.assertLessEqual(box.y1, chart.fig.bbox.height)
            plt.close(chart.fig)

    def test_disconnected_layout_is_bounded_and_reproducible(self):
        graph = nx.Graph()
        graph.add_edges_from([(0, 1), (1, 2), (2, 3), (4, 5)])
        nx.set_edge_attributes(graph, 1, 'weight')
        first = network_positions(graph, 400, 220, 18)
        second = network_positions(graph, 400, 220, 18)
        self.assertEqual(set(first), set(graph))
        for node, point in first.items():
            np.testing.assert_allclose(point, second[node])
            self.assertTrue(9 <= point[0] <= 391)
            self.assertTrue(9 <= point[1] <= 211)
        points = np.array(list(first.values()))
        distance = np.linalg.norm(points[:, None] - points[None, :], axis=2)
        np.fill_diagonal(distance, np.inf)
        self.assertGreaterEqual(distance.min(), 18)


if __name__ == '__main__':
    unittest.main()
