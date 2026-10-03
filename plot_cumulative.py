"""Plot cumulative number of delve.town posts over time.

Usage: plot_cumulative.py [snapshot dir]  (defaults to the newest under data/)
"""

import sys

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from snapshots import resolve_snapshot
from theme import FIGSIZE, ALL_POSTS_COLOR, TOP_LEVEL_COLOR, save_figure, set_theme, style_axes


def main(snapshot=None):
    snapshot = resolve_snapshot(snapshot)
    in_path = snapshot / "posts.csv"
    set_theme()
    df = pd.read_csv(in_path)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, format="ISO8601")
    df = df.sort_values("created_at")
    top = df[~df["is_reply"]]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(df["created_at"], range(1, len(df) + 1), label=f"All posts ({len(df):,})", color=ALL_POSTS_COLOR)
    ax.plot(top["created_at"], range(1, len(top) + 1), label=f"Top-level posts ({len(top):,})", color=TOP_LEVEL_COLOR)

    ax.set_title("Cumulative Delvetown Posts")
    ax.set_xlabel("Date (UTC)")
    ax.set_ylabel("Posts")
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %-d"))
    ax.legend()
    style_axes(ax)
    save_figure(fig, in_path, snapshot / "cumulative_posts.png")


if __name__ == "__main__":
    main(*sys.argv[1:])
