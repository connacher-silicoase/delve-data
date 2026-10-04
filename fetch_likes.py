"""Fetch public likes and the three most liked posts into the latest snapshot."""

import csv
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import sys
from urllib.error import HTTPError

from fetch_posts import fetch_avatar, paginate, xrpc
from snapshots import resolve_snapshot


def repo_likes(repo):
    return [
        {"uri": record["uri"], "did": repo["did"], "subject": record["value"]["subject"]["uri"]}
        for record in paginate(
            "com.atproto.repo.listRecords", "records",
            repo=repo["did"], collection="town.delve.feed.like",
        )
    ]


def main(snapshot=None):
    snapshot = resolve_snapshot(snapshot)
    accessed_at = datetime.now(timezone.utc)
    repos = list(paginate("com.atproto.sync.listRepos", "repos"))
    with ThreadPoolExecutor(max_workers=6) as pool:
        likes = [like for group in pool.map(repo_likes, repos) for like in group]
    # Count unique accounts liking a post, even if duplicate records exist.
    counts = Counter(subject for _, subject in {(like["did"], like["subject"]) for like in likes})
    ranked = []
    for uri, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        did, collection, rkey = uri.removeprefix("at://").split("/")
        try:
            record = xrpc("com.atproto.repo.getRecord", repo=did, collection=collection, rkey=rkey)
        except HTTPError as exc:
            # Deleted posts can retain references in other accounts' like records.
            if exc.code == 400:
                print(f"unavailable post {uri}: {exc}", file=sys.stderr)
                continue
            raise
        handle = xrpc("com.atproto.repo.describeRepo", repo=did)["handle"]
        fetch_avatar(did, handle, snapshot / "avatars")
        ranked.append({"uri": uri, "handle": handle, "likes": count, **record["value"]})
        if len(ranked) == 3:
            break
    with (snapshot / "likes.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["uri", "did", "subject"])
        writer.writeheader()
        writer.writerows(sorted(likes, key=lambda like: like["uri"]))
    meta = {"accessed_at": accessed_at.isoformat(), "accounts": len(repos), "like_records": len(likes)}
    (snapshot / "likes.meta.json").write_text(json.dumps(meta) + "\n")
    (snapshot / "top_liked_posts.json").write_text(json.dumps(ranked, indent=2, ensure_ascii=False) + "\n")
    print(f"Fetched {len(likes)} likes from {len(repos)} accounts; saved {len(ranked)} top posts to {snapshot}")


if __name__ == "__main__":
    main(*sys.argv[1:])
