"""Reusable figure regions and content-sized headings, footers, and legends."""
import json
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnnotationBbox, TextArea, VPacker

from theme import FIGSIZE, DPI, TITLE_COLOR, set_theme

GAP_PT = 8
INTERACTION_NOTES = 'interactions = replies + quotes + likes.'


def measure(fig, artist):
    """Return a content box's physical width and height in points."""
    artist.set_figure(fig)
    bounds = artist.get_window_extent(fig.canvas.get_renderer())
    return bounds.width * 72 / fig.dpi, bounds.height * 72 / fig.dpi


def text_box(text, size=9, color=TITLE_COLOR):
    return TextArea(text, textprops={'fontsize': size, 'color': color})


def wrapped_text(fig, text, size, width, color=TITLE_COLOR):
    """Wrap text against its rendered width, including unusually long tokens."""
    lines, current = [], ''
    for word in text.split():
        candidate = f'{current} {word}'.strip()
        if current and measure(fig, text_box(candidate, size, color))[0] > width:
            lines.append(current)
            current = ''
        if measure(fig, text_box(word, size, color))[0] > width:
            for char in word:
                if current and measure(fig, text_box(current + char, size, color))[0] > width:
                    lines.append(current)
                    current = ''
                current += char
        else:
            current = f'{current} {word}'.strip()
    lines.append(current)
    return text_box('\n'.join(lines), size, color)


def place_box(ax, box, xy, *, coordinates='axes fraction', alignment=(0, 1)):
    artist = AnnotationBbox(box, xy, xycoords=coordinates,
                            box_alignment=alignment, frameon=False, pad=0)
    # The grid allocates room for the box; it must not also expand its own cell.
    artist.set_in_layout(False)
    ax.add_artist(artist)
    return artist


class Chart:
    """Three grid rows: measured header, flexible body, measured source/footer.

    Content boxes are in physical points; constrained layout reserves tick/axis
    labels. No chart script places text in figure coordinates or adjusts axes.
    """
    def __init__(self, title, data_path, *, subtitle=None, notes=None):
        set_theme()
        self.fig = plt.figure(figsize=FIGSIZE, layout='constrained')
        self.fig.get_layout_engine().set(w_pad=GAP_PT / 72, h_pad=GAP_PT / 72,
                                         hspace=0, wspace=0)
        width = FIGSIZE[0] * 72 - 2 * GAP_PT
        lines = [wrapped_text(self.fig, title, 16, width)]
        if subtitle:
            lines.append(wrapped_text(self.fig, subtitle, 9, width))
        header = VPacker(children=lines, align='left', pad=0, sep=4)
        meta = json.loads(data_path.with_suffix('.meta.json').read_text())
        accessed = datetime.fromisoformat(meta['accessed_at'])
        source = f'Source: delve.town, accessed {accessed:%b %-d, %Y %H:%M} UTC'
        if notes:
            source += f' | Notes: {notes}'
        footer = wrapped_text(self.fig, source, 7, width, '0.4')
        header_height = measure(self.fig, header)[1]
        footer_height = measure(self.fig, footer)[1]
        self.body_height = FIGSIZE[1] * 72 - header_height - footer_height - 6 * GAP_PT
        self.body_width = width
        self._column_groups = []
        grid = self.fig.add_gridspec(3, 1, height_ratios=[header_height, self.body_height, footer_height])
        self.body = grid[1]
        for cell, content in [(grid[0], header), (grid[2], footer)]:
            ax = self.fig.add_subplot(cell)
            ax.set_axis_off()
            place_box(ax, content, (0, 1))

    def axes(self):
        return self.fig.add_subplot(self.body.subgridspec(1, 1)[0])

    def columns(self, widths, *, fixed=()):
        """Allocate body columns by measured physical widths, not label offsets."""
        grid = self.body.subgridspec(1, len(widths), width_ratios=widths, wspace=0)
        axes = [self.fig.add_subplot(cell) for cell in grid]
        self._column_groups.append((grid, axes, widths, fixed))
        return axes

    def with_legend(self, handles, title):
        # Measure the actual legend before allocating its dedicated column.
        probe = self.fig.legend(handles=handles, title=title, frameon=False,
                                fontsize=7, title_fontsize=8, handlelength=3)
        self.fig.canvas.draw()
        legend_width = probe.get_window_extent().width * 72 / self.fig.dpi
        probe.remove()
        ax, legend_ax = self.columns([self.body_width - legend_width - GAP_PT, legend_width], fixed=(1,))
        legend_ax.set_axis_off()
        legend_ax.legend(handles=handles, title=title, loc='center', ncol=1,
                         frameon=False, fontsize=7, title_fontsize=8, handlelength=3)
        return ax

    def finalize(self):
        # Axes decorations consume some cell width. Reconcile fixed content
        # columns against the actual remaining space after constrained layout.
        for _ in range(2):
            self.fig.canvas.draw()
            for grid, axes, widths, fixed in self._column_groups:
                if not fixed:
                    continue
                available = sum(ax.get_window_extent().width * 72 / self.fig.dpi for ax in axes)
                flexible = [i for i in range(len(axes)) if i not in fixed]
                remaining = available - sum(widths[i] for i in fixed)
                if remaining <= 0:
                    raise ValueError('Figure is too narrow for its content columns')
                total = sum(widths[i] for i in flexible)
                grid.set_width_ratios([widths[i] if i in fixed else remaining * widths[i] / total
                                       for i in range(len(axes))])
        self.fig.canvas.draw()

    def save(self, path):
        self.finalize()
        self.fig.savefig(path, dpi=DPI)
        plt.close(self.fig)
        print(f'wrote {path}')


def panel_title(ax, letter, title):
    ax.set_title(f'Panel {letter}. {title}', loc='left', fontsize=9,
                 color=TITLE_COLOR, pad=GAP_PT)
