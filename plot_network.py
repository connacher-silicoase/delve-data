"""Avatar network: plot_network.py [snapshot] [--min-interactions N] [--top N]."""
import argparse
import csv
import json
import math

import networkx as nx
from matplotlib.lines import Line2D
from matplotlib.colors import to_rgba

from theme import format_count
from network import build_graph
from snapshots import resolve_snapshot
from chart_layout import Chart, INTERACTION_NOTES, place_box
from avatars import avatar_box
from network_layout import network_positions


def connection_style(count, maximum):
    """Shared scale for edges and legend; quadratic width and increasing opacity."""
    fraction = count / maximum
    return 0.35 + 5.65 * fraction ** 2, 0.08 + 0.82 * math.sqrt(fraction)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', nargs='?')
    parser.add_argument('--min-interactions', type=int, default=1)
    parser.add_argument('--top', type=int, help='Show the N users with the most interactions')
    args = parser.parse_args()
    if args.min_interactions < 1 or (args.top is not None and args.top < 1):
        parser.error('threshold and top must be positive')
    snapshot = resolve_snapshot(args.snapshot)
    def read(name):
        path = snapshot / f'{name}.csv'
        if not path.exists():
            parser.error('This snapshot lacks network data; run fetch_posts.py for a new snapshot.')
        with path.open() as f:
            return list(csv.DictReader(f))
    graph = build_graph(read('users'), read('interactions'))
    # Export the complete graph, retaining per-kind counts for future weighting.
    (snapshot / 'network.json').write_text(json.dumps(nx.node_link_data(graph), indent=2) + '\n')
    active = {n for n, degree in graph.degree() if degree}
    if args.top:
        active = set(sorted(active, key=lambda n: (-graph.degree(n, weight='weight'), n))[:args.top])
    displayed = graph.subgraph(active).copy()
    displayed.remove_edges_from([(a, b) for a, b, d in displayed.edges(data=True) if d['total'] < args.min_interactions])
    displayed.remove_nodes_from(list(nx.isolates(displayed)))
    if not displayed:
        parser.error('No connections match these filters.')
    # Anchor the scale to the full snapshot so filtered views remain comparable.
    maximum = max(d['total'] for _, _, d in graph.edges(data=True))
    rounding = -int(math.log10(maximum))
    examples = sorted({1, max(1, round(maximum / 3, rounding)),
                       max(1, round(2 * maximum / 3, rounding)), maximum})
    handles = []
    for count in examples:
        width, alpha = connection_style(count, maximum)
        handles.append(Line2D([], [], color='#084a91', linewidth=width,
                              alpha=alpha, label=format_count(count)))
    total = sum(d['total'] for _, _, d in displayed.edges(data=True))
    scope = f'{format_count(args.top)} Top-Connected Users' if args.top else 'All Users'
    chart = Chart(f'Delvetown Connections | {scope}', snapshot / 'posts.csv',
                  subtitle=f'{format_count(len(displayed))} users | {format_count(displayed.number_of_edges())} connections | {format_count(total)} interactions',
                  notes=INTERACTION_NOTES)
    ax = chart.with_legend(handles, 'Interactions')
    ax.set_axis_off()
    chart.finalize()
    bounds = ax.get_window_extent()
    width, height = bounds.width * 72 / chart.fig.dpi, bounds.height * 72 / chart.fig.dpi
    diameter = 10 if len(displayed) > 60 else 18
    positions = network_positions(displayed, width, height, diameter)
    styles = [connection_style(d['total'], maximum) for _, _, d in displayed.edges(data=True)]
    nx.draw_networkx_edges(displayed, positions, ax=ax,
                           width=[w for w, _ in styles],
                           edge_color=[to_rgba('#084a91', alpha) for _, alpha in styles])
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    for did, point in positions.items():
        place_box(ax, avatar_box(snapshot / 'avatars', displayed.nodes[did]['handle'], diameter),
                  point, coordinates='data', alignment=(0.5, 0.5))
    suffix = (f'_top{args.top}' if args.top else '') + (f'_min{args.min_interactions}' if args.min_interactions > 1 else '')
    chart.save(snapshot / f'network{suffix}.png')


if __name__ == '__main__':
    main()
