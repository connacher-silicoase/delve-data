"""Download every post and avatar on the delve.town PDS into a new snapshot folder.

Writes posts.csv, posts.meta.json, users.csv, interactions.csv and avatars/
inside data/<timestamp>/.

delve.town is an AT Protocol fork. Its PDS exposes public XRPC endpoints:
  - com.atproto.sync.listRepos   -> every account (DID) hosted on the PDS
  - com.atproto.repo.listRecords -> records in one account's collection
  - com.atproto.sync.getBlob     -> raw blobs, e.g. avatar images
Posts live in the custom collection `town.delve.feed.post` (not app.bsky.feed.post),
and profiles in `town.delve.actor.profile`.
"""

import csv
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

from snapshots import new_snapshot
from network import post_interactions, like_interaction

PDS = "https://pds.delve.town"
COLLECTION = "town.delve.feed.post"
PROFILE_COLLECTION = "town.delve.actor.profile"
AVATAR_EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def xrpc_raw(method, **params):
    url = f"{PDS}/xrpc/{method}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read()


def xrpc(method, **params):
    return json.loads(xrpc_raw(method, **params))


def fetch_avatar(did, handle, avatar_dir):
    """Save the account's avatar to <avatar_dir>/<handle>.<ext>, if it has one."""
    records = xrpc("com.atproto.repo.listRecords", repo=did, collection=PROFILE_COLLECTION)["records"]
    avatar = records[0]["value"].get("avatar") if records else None
    if not avatar:
        return
    ext = AVATAR_EXT.get(avatar.get("mimeType"), ".img")
    data = xrpc_raw("com.atproto.sync.getBlob", did=did, cid=avatar["ref"]["$link"])
    (avatar_dir / f"{handle}{ext}").write_bytes(data)


def paginate(method, key, **params):
    cursor = None
    while True:
        page = xrpc(method, limit=100, **params, **({"cursor": cursor} if cursor else {}))
        items = page.get(key, [])
        yield from items
        cursor = page.get("cursor")
        if not cursor or not items:
            break


def main():
    accessed_at = datetime.now(timezone.utc)
    snapshot = new_snapshot(accessed_at)
    avatar_dir = snapshot / "avatars"
    avatar_dir.mkdir()
    repos = list(paginate("com.atproto.sync.listRepos", "repos"))
    inactive = [repo["did"] for repo in repos if not repo.get("active", True)]
    repos = [repo for repo in repos if repo.get("active", True)]
    print(f"{len(repos)} accounts", file=sys.stderr)
    if inactive:
        print(f"Skipping {len(inactive)} inactive accounts", file=sys.stderr)

    rows = []
    interactions = []
    users = []
    def fetch_repo(repo):
        rows, interactions = [], []
        did = repo["did"]
        handle = xrpc("com.atproto.repo.describeRepo", repo=did).get("handle", "")
        fetch_avatar(did, handle or did, avatar_dir)
        n = 0
        for rec in paginate("com.atproto.repo.listRecords", "records", repo=did, collection=COLLECTION):
            v = rec["value"]
            interactions.extend(post_interactions(did, rec))
            rows.append({
                "uri": rec["uri"],
                "did": did,
                "handle": handle,
                "created_at": v.get("createdAt", ""),
                "is_reply": "reply" in v,
                "text": v.get("text", ""),
            })
            n += 1
        for rec in paginate("com.atproto.repo.listRecords", "records", repo=did, collection="town.delve.feed.like"):
            interaction = like_interaction(did, rec)
            if interaction:
                interactions.append(interaction)
        print(f"  {handle or did}: {n}", file=sys.stderr)

        return {"did": did, "handle": handle}, rows, interactions

    with ThreadPoolExecutor(max_workers=4) as pool:
        for user, posts, events in pool.map(fetch_repo, repos):
            users.append(user)
            rows.extend(posts)
            interactions.extend(events)

    rows.sort(key=lambda r: r["created_at"])
    out_path = snapshot / "posts.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["uri"])
        writer.writeheader()
        writer.writerows(rows)
    for name, data, fields in [
        ("users", users, ["did", "handle"]),
        ("interactions", interactions, ["uri", "source", "target", "kind", "subject_uri", "created_at"]),
    ]:
        with (snapshot / f"{name}.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)
    (snapshot / "posts.meta.json").write_text(json.dumps({
        "accessed_at": accessed_at.isoformat(), "inactive_accounts": inactive,
    }) + "\n")
    print(f"wrote {len(rows)} posts to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
