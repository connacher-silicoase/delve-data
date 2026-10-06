"""Plot cumulative number of delve.town posts over time.

Usage: plot_cumulative.py [snapshot dir]  (defaults to the newest under data/)
"""

import sys

import matplotlib.dates as mdates
import pandas as pd

from snapshots import resolve_snapshot
from theme import ALL_POSTS_COLOR, TOP_LEVEL_COLOR, style_axes, format_count
from chart_layout import Chart


def main(snapshot=None):
    snapshot = resolve_snapshot(snapshot)
    in_path = snapshot / "posts.csv"
    df = pd.read_csv(in_path)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, format="ISO8601")
    df = df.sort_values("created_at")
    top = df[~df["is_reply"]]

    chart = Chart('Cumulative Delvetown Posts', in_path)
    ax = chart.axes()
    ax.plot(df["created_at"], range(1, len(df) + 1), label=f"All posts ({format_count(len(df))})", color=ALL_POSTS_COLOR)
    ax.plot(top["created_at"], range(1, len(top) + 1), label=f"Top-level posts ({format_count(len(top))})", color=TOP_LEVEL_COLOR)

    ax.set_xlabel("Date (UTC)")
    ax.set_ylabel("Posts")
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %-d"))
    ax.legend()
    style_axes(ax)
    chart.save(snapshot / "cumulative_posts.png")


if __name__ == "__main__":
    main(*sys.argv[1:])
