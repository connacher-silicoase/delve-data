# delve-data

Charts of posting activity on [delve.town](https://delve.town), pulled from its public AT Protocol PDS.

```sh
uv run fetch_posts.py      # new snapshot: data/<timestamp>/posts.csv, posts.meta.json, avatars/
uv run plot_cumulative.py  # data/<timestamp>/cumulative_posts.png
uv run plot_top_users.py   # data/<timestamp>/top_users.png
```

Each fetch gets its own timestamped folder, so nothing is overwritten. The plot scripts
use the newest snapshot; pass a folder (e.g. `uv run plot_top_users.py data/2026-10-03T005601Z`)
to re-plot an older one.

Charts are 1600 × 900 px (16:9, for X). Shared colors and styling live in `theme.py`.
