# delve-data

Charts of posting activity on [delve.town](https://delve.town), pulled from its public AT Protocol PDS.

```sh
uv run fetch_posts.py      # posts.csv, posts.meta.json, avatars/
uv run plot_cumulative.py  # cumulative_posts.png
uv run plot_top_users.py   # top_users.png
```

Charts are 1600 × 900 px (16:9, for X). Shared colors and styling live in `theme.py`.
