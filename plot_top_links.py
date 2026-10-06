"""Top bilateral user links: plot_top_links.py [snapshot] [--top N]."""
import argparse
import csv


from network import build_graph
from avatars import pair_boxes
from snapshots import resolve_snapshot
from theme import style_axes, format_count, count_axis
from chart_layout import Chart, INTERACTION_NOTES, measure, place_box, panel_title


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', nargs='?')
    parser.add_argument('--top', type=int, default=10)
    args = parser.parse_args()
    if args.top < 1:
        parser.error('top must be positive')
    snapshot = resolve_snapshot(args.snapshot)
    def read(name):
        path = snapshot / f'{name}.csv'
        if not path.exists():
            parser.error('This snapshot lacks network data; run fetch_posts.py first.')
        with path.open() as f:
            return list(csv.DictReader(f))
    graph = build_graph(read('users'), read('interactions'))
    links = sorted(graph.edges(data=True), key=lambda edge: (-edge[2]['total'], *sorted(edge[:2])))[:args.top]
    if not links:
        parser.error('No bilateral links in this snapshot.')
    chart = Chart(f'Top {format_count(len(links))} Delvetown Connections', snapshot / 'posts.csv', notes=INTERACTION_NOTES)
    names = [[graph.nodes[n]['handle'] for n in sorted((a, b), key=lambda n: graph.nodes[n]['handle'])]
             for a, b, _ in links]
    pairs = pair_boxes(chart.fig, snapshot / 'avatars', names)
    pair_width = max(measure(chart.fig, box)[0] for box in pairs)
    who, ax = chart.columns([pair_width, chart.body_width - pair_width], fixed=(0,))
    who.sharey(ax)
    y = list(range(len(links)))
    counts = [edge[2]['total'] for edge in links]
    bars = ax.barh(y, counts, color='#084a91', height=0.58)
    ax.bar_label(bars, labels=[format_count(n) for n in counts], padding=5, fontsize=9)
    ax.set_xlim(0, max(counts) * 1.14)
    ax.set_xlabel('Interactions', fontsize=9)
    count_axis(ax, 'x')
    style_axes(ax)
    ax.grid(axis='y', visible=False)
    ax.grid(axis='x', visible=True, alpha=0.25)
    ax.set_yticks([])
    who.set_axis_off()
    who.set_xlim(0, 1)
    ax.set_ylim(len(links) - 0.5, -0.5)
    for row, box in enumerate(pairs):
        place_box(who, box, (0, row), coordinates=who.get_yaxis_transform(), alignment=(0, 0.5))
    panel_title(who, 'A', 'User pair')
    panel_title(ax, 'B', 'Interactions by user pair')
    chart.save(snapshot / f'top_{args.top}_links.png')



if __name__ == '__main__':
    main()
