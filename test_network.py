import unittest
from unittest.mock import patch

from fetch_posts import paginate

from network import build_graph, like_interaction, post_interactions

A, B, C = 'did:plc:a', 'did:plc:b', 'did:plc:c'


def uri(did, collection='town.delve.feed.post'):
    return f'at://{did}/{collection}/123'


def record(value, did=A):
    return {'uri': uri(did), 'value': value}


class NetworkTests(unittest.TestCase):
    def test_paginated_records_are_all_retained(self):
        with patch('fetch_posts.xrpc', side_effect=[
            {'records': [{'uri': 'first'}], 'cursor': 'next'},
            {'records': [{'uri': 'last'}]},
        ]) as request:
            self.assertEqual(list(paginate('method', 'records', repo=A)), [{'uri': 'first'}, {'uri': 'last'}])
            self.assertEqual(request.call_args.kwargs['cursor'], 'next')

    def test_reply_targets_parent_not_root(self):
        rows = post_interactions(A, record({'reply': {'parent': {'uri': uri(B)}, 'root': {'uri': uri(C)}}}))
        self.assertEqual([(r['kind'], r['target']) for r in rows], [('reply', B)])

    def test_reply_and_quote_with_media_are_separate_interactions(self):
        quote = {'$type': 'town.delve.embed.record', 'record': {'uri': uri(C)}}
        for embed in [quote, {'$type': 'town.delve.embed.recordWithMedia', 'record': quote}]:
            rows = post_interactions(A, record({'reply': {'parent': {'uri': uri(B)}}, 'embed': embed}))
            self.assertEqual([(r['kind'], r['target']) for r in rows], [('reply', B), ('quote', C)])

    def test_non_post_embeds_and_invalid_targets_are_ignored(self):
        self.assertEqual(post_interactions(A, record({'embed': {'$type': 'town.delve.embed.record', 'record': {'uri': uri(B, 'town.delve.feed.generator')}}})), [])
        self.assertIsNone(like_interaction(A, record({'subject': {'uri': 'bad'}})))

    def test_aggregation_deduplication_self_edges_and_weights(self):
        rows = [like_interaction(A, record({'subject': {'uri': uri(B)}})),
                *post_interactions(B, record({'reply': {'parent': {'uri': uri(A)}}}, B)),
                like_interaction(C, record({'subject': {'uri': uri(C)}}, C))]
        users = [{'did': d, 'handle': d} for d in (A, B, C)]
        graph = build_graph(users, rows + rows)
        self.assertEqual(graph[A][B], {'reply': 1, 'like': 1, 'quote': 0, 'weight': 2.0, 'total': 2})
        self.assertEqual(graph.number_of_edges(), 1)
        self.assertEqual(build_graph(users, rows, {'like': 3})[A][B]['weight'], 4)


if __name__ == '__main__':
    unittest.main()
