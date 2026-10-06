"""Stacked bar chart of the top delve.town users by total post count, labeled with avatars.

Usage: plot_top_users.py [snapshot dir] [n]  (defaults: newest under data/, 10)
"""

import sys

import pandas as pd

from snapshots import resolve_snapshot
from theme import REPLIES_COLOR, TOP_LEVEL_COLOR, style_axes, format_count
from chart_layout import Chart, measure, place_box
from avatars import poster_box


def main(snapshot=None, n="10"):
    snapshot = resolve_snapshot(snapshot)
    in_path = snapshot / "posts.csv"
    n = int(n)
    df = pd.read_csv(in_path)
    counts = (
        df.groupby("handle")["is_reply"]
        .agg(total="size", replies="sum")
        .nlargest(n, "total")
    )
    counts["top_level"] = counts["total"] - counts["replies"]

    chart = Chart('Top Delvetown Posters', in_path)
    identities = [poster_box(snapshot / 'avatars', handle, row['replies'] / row['total'])
                  for handle, row in counts.iterrows()]
    label_height = max(measure(chart.fig, box)[1] for box in identities)
    grid = chart.body.subgridspec(2, 1, height_ratios=[chart.body_height - label_height, label_height], hspace=0)
    ax = chart.fig.add_subplot(grid[0])
    labels = chart.fig.add_subplot(grid[1], sharex=ax)
    labels.set_axis_off()
    x = range(len(counts))
    ax.bar(x, counts["top_level"], label="Top-level posts", color=TOP_LEVEL_COLOR)
    replies = ax.bar(x, counts["replies"], bottom=counts["top_level"], label="Replies", color=REPLIES_COLOR)
    ax.bar_label(replies, labels=[format_count(t) for t in counts["total"]])
    ax.set_ylabel("Posts")
    ax.legend()
    style_axes(ax)

    ax.set_xticks(x)
    ax.tick_params(axis='x', bottom=False, labelbottom=False)
    for i, box in enumerate(identities):
        place_box(labels, box, (i, 1), coordinates=labels.get_xaxis_transform(), alignment=(0.5, 1))
    chart.save(snapshot / 'top_users.png')



if __name__ == "__main__":
    main(*sys.argv[1:])
