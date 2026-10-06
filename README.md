# delve-data

Charts of posting activity on [delve.town](https://delve.town), pulled from its public AT Protocol PDS.

```sh
uv run fetch_posts.py      # new snapshot: data/<timestamp>/posts.csv, posts.meta.json, avatars/
uv run plot_cumulative.py  # data/<timestamp>/cumulative_posts.png
uv run plot_top_users.py   # data/<timestamp>/top_users.png
uv run plot_network.py     # data/<timestamp>/network.png and network.json
uv run plot_top_links.py   # data/<timestamp>/top_10_links.png
```

Each fetch gets its own timestamped folder, so nothing is overwritten. The plot scripts
use the newest snapshot; pass a folder (e.g. `uv run plot_top_users.py data/2026-10-03T005601Z`)
to re-plot an older one.

Charts are 3200 × 1800 px (16:9, at 400 DPI).

Shared figure components:

- `theme.py`: colors, typography, axis styling, and comma-grouped count formatting.
- `chart_layout.py`: a constrained grid with measured header/footer content,
  content-sized columns, panel titles, and a dedicated right legend column.
- `avatars.py`: circular avatars and packed, aligned user-label components.
- `network_layout.py`: deterministic component packing and collision spacing
  measured in physical chart points, derived from the available axes area.

Plot scripts supply content rather than figure coordinates or manual offsets.
Headers and notes wrap to their measured available width. Avatar labels occupy
allocated grid rows/columns instead of relying on tick padding or offsets.

The network needs a fresh snapshot with `users.csv` and `interactions.csv`.
Each reply counts toward the immediate parent author, each like toward the liked
post's author, and each quote toward the embedded post's author (including quotes
with media). A post that both replies and quotes contributes both interactions.
Reposts, follows, mentions, and self-interactions do not contribute graph edges.
These are currently available public records, not a historical log of deleted
posts or removed likes. The download is not an atomic point-in-time snapshot.

The CSV preserves direction and target post URIs. The plotted graph combines both
directions between each pair of users and retains separate reply/like/quote counts
in `network.json`. All three weights default to 1 in `network.DEFAULT_WEIGHTS`;
`build_graph(..., weights={...})` supports future adjustments. Circular avatars
use the existing downloads, with a blue dot when an avatar is missing. Accounts
without connections are retained in the JSON but omitted from the chart.

The seeded NetworkX spring layout pulls connected users together. More interactions
make a connection more opaque and thicker, with quadratic (convex) line width.
For count `c` and the full snapshot's maximum pair count `M`, width is
`0.35 + 5.65 * (c/M)^2` points and opacity is `0.08 + 0.82 * sqrt(c/M)`.
The legend shows both encodings, and the scale stays the same across filtered views
of a snapshot. Spatial distances are layout choices, not a measured
social distance. Disconnected groups are laid out separately and avatar collisions
are relaxed. Network plots show avatars without name labels. For a less crowded view:

```sh
uv run plot_network.py --top 40 --min-interactions 3
uv run python -m unittest -v
```

`--top` ranks users by total interactions before filtering edges. The JSON always
contains the full graph regardless of display filters. Filtered charts use a
suffix such as `network_top40_min3.png`, preserving the full `network.png`.

`plot_top_links.py` ranks the top 10 bilateral connections by the combined count
in both directions, showing each user's avatar and handle next to the total.
Pass `--top N` to change the number of pairs. It uses the full snapshot,
independently of network display filters.
