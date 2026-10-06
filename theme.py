"""Shared theme and series colors so the delve.town charts match."""

import seaborn as sns
from matplotlib.ticker import FuncFormatter

# 16:9 at 3200x1800 px, preserving the chart proportions at higher resolution.
FIGSIZE = (8, 4.5)
DPI = 400
TITLE_COLOR = "0.15"

# Two blues from seaborn's "Blues": dark for top-level posts, light for the all-posts total they're part of.
TOP_LEVEL_COLOR = "#084a91"
# Replies stack on top of top-level posts to reach the all-posts total, so they share a color.
ALL_POSTS_COLOR = REPLIES_COLOR = "#6baed6"


def set_theme():
    sns.set_theme(style="whitegrid", rc={"axes.titlesize": 16,
                                        "axes.titlecolor": TITLE_COLOR,
                                        "text.color": TITLE_COLOR})


def format_count(value):
    """Whole-number counts with comma grouping, everywhere in a chart."""
    return f'{value:,.0f}'


def count_axis(ax, axis='y'):
    getattr(ax, f'{axis}axis').set_major_formatter(FuncFormatter(lambda value, _: format_count(value)))


def style_axes(ax):
    """Comma thousands on y, horizontal gridlines only, no surrounding box."""
    count_axis(ax)
    ax.grid(axis="x", visible=False)
    sns.despine(ax=ax, left=True, bottom=True)
