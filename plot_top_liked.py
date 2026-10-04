"""Three post cards with full text and public like counts, at 1600 × 900 px.

Usage: plot_top_liked.py [snapshot dir]
Run fetch_likes.py first. Edit the layout here to experiment with the format.
"""

import json
import sys
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch

from plot_top_users import load_avatar
from snapshots import resolve_snapshot
from theme import DPI, FIGSIZE, TOP_LEVEL_COLOR, add_source_footer, set_theme


def wrap_text(text, renderer, width, fontsize):
    font = FontProperties(size=fontsize)
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}".strip()
            if line and renderer.get_text_width_height_descent(candidate, font, False)[0] > width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return "\n".join(lines), len(lines)


def main(snapshot=None):
    snapshot = resolve_snapshot(snapshot)
    posts = json.loads((snapshot / "top_liked_posts.json").read_text())
    set_theme()
    fig = plt.figure(figsize=FIGSIZE, dpi=DPI, facecolor="white")
    fig.text(.5, .96, "Most Liked Delvetown Posts", ha="center", va="top",
             fontsize=plt.rcParams["axes.titlesize"], weight=plt.rcParams["axes.titleweight"])
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    for i, post in enumerate(posts):
        x = .04 + i * .315
        width = .29
        fig.add_artist(FancyBboxPatch(
            (x, .15), width, .63, boxstyle="round,pad=0.008,rounding_size=0.012",
            transform=fig.transFigure, facecolor="#f3f7fb", edgecolor="#dce5ef", linewidth=.8,
        ))
        rank = 1 + sum(other["likes"] > post["likes"] for other in posts)
        tied = sum(other["likes"] == post["likes"] for other in posts) > 1
        fig.text(x + .018, .735, f"{'TIED ' if tied else ''}#{rank}", fontsize=10,
                 color=TOP_LEVEL_COLOR)
        avatar = load_avatar(snapshot / "avatars", post["handle"])
        if avatar is not None:
            ax = fig.add_axes([x + .018, .649, .037, .066], zorder=3)
            ax.imshow(avatar)
            ax.axis("off")
        fig.text(x + .067, .686, post["handle"].removesuffix(".delve.town"),
                 fontsize=12, color="0.15")
        created = datetime.fromisoformat(post["createdAt"].replace("Z", "+00:00"))
        fig.text(x + .067, .658, f"{created:%b %-d, %H:%M} UTC", fontsize=8, color="0.45")

        # Fit full text without clipping or truncating; short posts get larger type.
        for fontsize in [18, 16, 14, 12, 11, 10, 9, 8]:
            quote, line_count = wrap_text(post["text"], renderer,
                                          (width - .036) * fig.bbox.width, fontsize)
            if line_count * fontsize * 1.3 / 72 <= .315 * FIGSIZE[1]:
                break
        fig.text(x + .018, .605, quote, fontsize=fontsize, linespacing=1.3,
                 va="top", color="0.18")
        fig.text(x + .018, .205, str(post["likes"]), fontsize=27, color=TOP_LEVEL_COLOR)
        fig.text(x + .078, .208, "likes", fontsize=12, color=TOP_LEVEL_COLOR)

    add_source_footer(fig, snapshot / "likes.csv")
    out_path = snapshot / "top_liked_posts.png"
    fig.savefig(out_path, dpi=DPI)
    plt.close(fig)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main(*sys.argv[1:])
