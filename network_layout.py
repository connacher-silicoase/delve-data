"""Deterministic component packing and avatar spacing in physical chart units."""
import math

import networkx as nx
import numpy as np


def component_rectangles(components, rectangle):
    """Partition by square-root component size, giving small groups usable space."""
    if len(components) == 1:
        return [(components[0], rectangle)]
    weights = [math.sqrt(len(component)) for component in components]
    total = sum(weights)
    split = min(range(1, len(components)), key=lambda i: abs(sum(weights[:i]) - total / 2))
    fraction = sum(weights[:split]) / total
    x, y, width, height = rectangle
    if width >= height:
        first = (x, y, width * fraction, height)
        second = (x + width * fraction, y, width * (1 - fraction), height)
    else:
        first = (x, y, width, height * fraction)
        second = (x, y + height * fraction, width, height * (1 - fraction))
    return component_rectangles(components[:split], first) + component_rectangles(components[split:], second)


def network_positions(graph, width, height, diameter):
    components = sorted(nx.connected_components(graph), key=lambda c: (-len(c), sorted(c)))
    positions = {}
    for component, (x, y, w, h) in component_rectangles(components, (0, 0, width, height)):
        core = nx.Graph()
        core.add_nodes_from(sorted(component))
        core.add_edges_from((a, b, {'layout_weight': math.log1p(d['weight'])})
                            for a, b, d in graph.subgraph(component).edges(data=True))
        local = nx.spring_layout(core, seed=42, iterations=400,
                                 weight='layout_weight', k=2 / math.sqrt(len(core)), method='force')
        nodes = list(core)
        points = np.array([local[n] for n in nodes])
        # Pad by the real avatar radius plus one shared gap.
        inset = min(diameter / 2 + 4, w / 4, h / 4)
        lower, upper = np.array([x + inset, y + inset]), np.array([x + w - inset, y + h - inset])
        extent = np.maximum(np.ptp(points, axis=0), 1e-9)
        points = lower + (points - points.min(axis=0)) / extent * (upper - lower)
        spacing = diameter + 4
        for _ in range(300):
            delta = points[:, None, :] - points[None, :, :]
            distance = np.linalg.norm(delta, axis=2)
            np.fill_diagonal(distance, np.inf)
            force = delta / np.maximum(distance[:, :, None], 1e-9)
            force *= np.maximum(spacing - distance, 0)[:, :, None] * 0.3
            shift = force.sum(axis=1)
            points = np.clip(points + shift, lower, upper)
            if np.max(np.abs(shift)) < 0.01:
                break
        positions.update(zip(nodes, points))
    return positions
