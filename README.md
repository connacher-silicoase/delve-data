# delve-data

Charts of posting activity on [delve.town](https://delve.town), pulled from its public AT Protocol PDS.

```sh
uv run fetch_posts.py      # new snapshot: data/<timestamp>/posts.csv, posts.meta.json, avatars/
uv run plot_cumulative.py  # data/<timestamp>/cumulative_posts.png
uv run plot_top_users.py   # data/<timestamp>/top_users.png
uv run fetch_likes.py      # latest snapshot: likes.csv, likes.meta.json, top_liked_posts.json
uv run plot_top_liked.py   # data/<timestamp>/top_liked_posts.png (three post cards)
```

Each fetch gets its own timestamped folder, so nothing is overwritten. The plot scripts
use the newest snapshot; pass a folder (e.g. `uv run plot_top_users.py data/2026-10-03T005601Z`)
to re-plot an older one.

Charts are 1600 × 900 px (16:9, for X). Shared colors and styling live in `theme.py`.

The most-liked figure counts unique liking accounts across the public PDS, includes
replies, and shows full text. Equal counts share a rank; URI order breaks ties for
selection. Like data has its own access time and can be refreshed independently.
Use `MPLBACKEND=Agg` for rendering without a display.
