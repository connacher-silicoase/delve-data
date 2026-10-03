"""Download every post on the delve.town PDS to posts.csv, and avatars to avatars/.

Also writes posts.meta.json with the time the data were accessed.

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
from pathlib import Path

PDS = "https://pds.delve.town"
COLLECTION = "town.delve.feed.post"
PROFILE_COLLECTION = "town.delve.actor.profile"
AVATAR_DIR = Path("avatars")
AVATAR_EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def xrpc_raw(method, **params):
    url = f"{PDS}/xrpc/{method}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read()


def xrpc(method, **params):
    return json.loads(xrpc_raw(method, **params))


def fetch_avatar(did, handle):
    """Save the account's avatar to avatars/<handle>.<ext>, if it has one."""
    records = xrpc("com.atproto.repo.listRecords", repo=did, collection=PROFILE_COLLECTION)["records"]
    avatar = records[0]["value"].get("avatar") if records else None
    if not avatar:
        return
    ext = AVATAR_EXT.get(avatar.get("mimeType"), ".img")
    data = xrpc_raw("com.atproto.sync.getBlob", did=did, cid=avatar["ref"]["$link"])
    (AVATAR_DIR / f"{handle}{ext}").write_bytes(data)


def paginate(method, key, **params):
    cursor = None
    while True:
        page = xrpc(method, limit=100, **params, **({"cursor": cursor} if cursor else {}))
        items = page.get(key, [])
        yield from items
        cursor = page.get("cursor")
        if not cursor or not items:
            break


def main(out_path="posts.csv"):
    accessed_at = datetime.now(timezone.utc)
    repos = list(paginate("com.atproto.sync.listRepos", "repos"))
    print(f"{len(repos)} accounts", file=sys.stderr)
    AVATAR_DIR.mkdir(exist_ok=True)

    rows = []
    for repo in repos:
        did = repo["did"]
        handle = xrpc("com.atproto.repo.describeRepo", repo=did).get("handle", "")
        fetch_avatar(did, handle or did)
        n = 0
        for rec in paginate("com.atproto.repo.listRecords", "records", repo=did, collection=COLLECTION):
            v = rec["value"]
            rows.append({
                "uri": rec["uri"],
                "did": did,
                "handle": handle,
                "created_at": v.get("createdAt", ""),
                "is_reply": "reply" in v,
                "text": v.get("text", ""),
            })
            n += 1
        print(f"  {handle or did}: {n}", file=sys.stderr)

    rows.sort(key=lambda r: r["created_at"])
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["uri"])
        writer.writeheader()
        writer.writerows(rows)
    meta_path = Path(out_path).with_suffix(".meta.json")
    meta_path.write_text(json.dumps({"accessed_at": accessed_at.isoformat()}) + "\n")
    print(f"wrote {len(rows)} posts to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
