"""Shared theme and series colors so the delve.town charts match."""

import json
from datetime import datetime
from pathlib import Path

import seaborn as sns
from matplotlib.ticker import StrMethodFormatter

# 16:9 at 1600x900 px, which X shows uncropped in the timeline.
FIGSIZE = (8, 4.5)
DPI = 200

# Two blues from seaborn's "Blues": dark for top-level posts, light for the all-posts total they're part of.
TOP_LEVEL_COLOR = "#084a91"
# Replies stack on top of top-level posts to reach the all-posts total, so they share a color.
ALL_POSTS_COLOR = REPLIES_COLOR = "#6baed6"


def set_theme():
    sns.set_theme(style="whitegrid", rc={"axes.titlesize": 16})


def style_axes(ax):
    """Comma thousands on y, horizontal gridlines only, no surrounding box."""
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.grid(axis="x", visible=False)
    sns.despine(ax=ax, left=True, bottom=True)


def add_source_footer(fig, data_path):
    """Add the shared source line using the data file's access time."""
    meta = json.loads(Path(data_path).with_suffix(".meta.json").read_text())
    accessed_at = datetime.fromisoformat(meta["accessed_at"])
    fig.text(
        0.01, 0.01,
        f"Source: delve.town, accessed {accessed_at:%b %-d, %Y %H:%M} UTC",
        ha="left", va="bottom", fontsize=9, color="0.4",
    )


def save_figure(fig, data_path, out_path):
    """Lay out the figure, add a "Source:" line with the access time, and save it."""
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    add_source_footer(fig, data_path)
    fig.savefig(out_path, dpi=DPI)
    print(f"wrote {out_path}")
