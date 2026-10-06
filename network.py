"""Extract directed interactions; aggregate equal-weight connections for plotting."""
from urllib.parse import urlsplit

KINDS = ('reply', 'like', 'quote')
DEFAULT_WEIGHTS = dict.fromkeys(KINDS, 1.0)


def interaction(source, rec, kind, subject):
    parts = urlsplit(subject or '')
    if parts.scheme != 'at' or not parts.netloc.startswith('did:') or not parts.path.startswith('/town.delve.feed.post/'):
        return None
    return dict(uri=rec['uri'], source=source, target=parts.netloc, kind=kind,
                subject_uri=subject, created_at=rec['value'].get('createdAt', ''))


def post_interactions(source, rec):
    value = rec['value']
    refs = [('reply', value.get('reply', {}).get('parent', {}).get('uri'))]
    embed = value.get('embed', {})
    if embed.get('$type') == 'town.delve.embed.recordWithMedia':
        embed = embed.get('record', {})
    if embed.get('$type') == 'town.delve.embed.record':
        refs.append(('quote', embed.get('record', {}).get('uri')))
    return [row for kind, uri in refs if (row := interaction(source, rec, kind, uri))]


def like_interaction(source, rec):
    return interaction(source, rec, 'like', rec['value'].get('subject', {}).get('uri'))


def build_graph(users, interactions, weights=None):
    import networkx as nx
    weights = DEFAULT_WEIGHTS | (weights or {})
    graph = nx.Graph()
    graph.add_nodes_from((u['did'], {'handle': u['handle'] or u['did']}) for u in users)
    seen = set()
    for row in interactions:
        key = (row['uri'], row['kind'])
        if key in seen:
            continue
        seen.add(key)
        source, target, kind = row['source'], row['target'], row['kind']
        if source == target or kind not in KINDS:
            continue
        for did in (source, target):
            if did not in graph:
                graph.add_node(did, handle=did)
        if not graph.has_edge(source, target):
            graph.add_edge(source, target, **dict.fromkeys(KINDS, 0), weight=0.0, total=0)
        edge = graph[source][target]
        edge[kind] += 1
        edge['total'] += 1
        edge['weight'] += weights[kind]
    return graph
