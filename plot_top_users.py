"""Stacked bar chart of the top delve.town users by total post count, labeled with avatars.

Reads posts.csv and avatars/ (both written by fetch_posts.py).
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from PIL import Image

from theme import FIGSIZE, REPLIES_COLOR, TOP_LEVEL_COLOR, save_figure, set_theme, style_axes

AVATAR_DIR = Path("avatars")
AVATAR_PX = 128  # source resolution; displayed at AVATAR_PX * AVATAR_ZOOM points
AVATAR_ZOOM = 0.24
HANDLE_FONTSIZE = 9
AVATAR_PT = AVATAR_PX * AVATAR_ZOOM

# Rows below the x-axis, in points: avatar, then handle (tick label), then % replies.
AVATAR_GAP = 4
HANDLE_PAD = AVATAR_GAP + AVATAR_PT + 4
PCT_OFFSET = HANDLE_PAD + 16


def load_avatar(handle):
    path = next(AVATAR_DIR.glob(f"{handle}.*"), None)
    if path is None:
        return None
    img = Image.open(path).convert("RGB")
    side = min(img.size)
    left, top = (img.width - side) // 2, (img.height - side) // 2
    return img.crop((left, top, left + side, top + side)).resize((AVATAR_PX, AVATAR_PX))


def main(in_path="posts.csv", out_path="top_users.png", n="10"):
    set_theme()
    n = int(n)
    df = pd.read_csv(in_path)
    counts = (
        df.groupby("handle")["is_reply"]
        .agg(total="size", replies="sum")
        .nlargest(n, "total")
    )
    counts["top_level"] = counts["total"] - counts["replies"]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    x = range(len(counts))
    ax.bar(x, counts["top_level"], label="Top-level posts", color=TOP_LEVEL_COLOR)
    replies = ax.bar(x, counts["replies"], bottom=counts["top_level"], label="Replies", color=REPLIES_COLOR)
    ax.bar_label(replies, labels=[f"{t:,}" for t in counts["total"]])
    ax.set_title("Top Delvetown Posters")
    ax.set_ylabel("Posts")
    ax.legend()
    style_axes(ax)

    # Avatar row, then handles as tick labels, then a % replies row.
    ax.set_xticks(x, [h.removesuffix(".delve.town") for h in counts.index])
    ax.tick_params(axis="x", length=0, pad=HANDLE_PAD, labelsize=HANDLE_FONTSIZE)
    for i, (handle, row) in enumerate(counts.iterrows()):
        avatar = load_avatar(handle)
        if avatar is not None:
            ax.add_artist(AnnotationBbox(
                OffsetImage(avatar, zoom=AVATAR_ZOOM),
                (i, 0),
                xycoords=("data", "axes fraction"),
                xybox=(0, -AVATAR_GAP),
                boxcoords="offset points",
                box_alignment=(0.5, 1),
                frameon=False,
            ))
        ax.annotate(
            f"{row['replies'] / row['total']:.0%}",
            (i, 0),
            xycoords=("data", "axes fraction"),
            xytext=(0, -PCT_OFFSET),
            textcoords="offset points",
            ha="center",
            va="top",
        )
    ax.annotate(
        "% replies",
        (0, 0),
        xycoords="axes fraction",
        xytext=(-8, -PCT_OFFSET),
        textcoords="offset points",
        ha="right",
        va="top",
    )

    save_figure(fig, in_path, out_path)


if __name__ == "__main__":
    main(*sys.argv[1:])
