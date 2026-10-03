"""Timestamped snapshot folders, so each fetch and its charts are kept side by side.

data/<YYYY-MM-DDTHHMMSSZ>/
    posts.csv, posts.meta.json, avatars/   <- fetch_posts.py
    cumulative_posts.png, top_users.png    <- plot_*.py
"""

from pathlib import Path

DATA_DIR = Path("data")


def new_snapshot(accessed_at):
    """Create and return the folder for a fetch made at `accessed_at` (UTC)."""
    path = DATA_DIR / f"{accessed_at:%Y-%m-%dT%H%M%SZ}"
    path.mkdir(parents=True)
    return path


def resolve_snapshot(snapshot=None):
    """Return the given snapshot folder, or the newest one under data/."""
    if snapshot:
        return Path(snapshot)
    snapshots = sorted(p for p in DATA_DIR.glob("*") if (p / "posts.csv").exists())
    if not snapshots:
        raise SystemExit(f"no snapshots in {DATA_DIR}/ — run fetch_posts.py first")
    return snapshots[-1]
