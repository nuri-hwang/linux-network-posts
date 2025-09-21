#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Purpose: Resolve Hashnode articleId by slug using GraphQL

import sys, json, os, requests

def endpoint_from_env_or_arg(default: str) -> str:
    if len(sys.argv) >= 4 and sys.argv[3].startswith("http"):
        return sys.argv[3]
    return os.getenv("HASHNODE_GQL_ENDPOINT", default)

GRAPHQL_ENDPOINT = endpoint_from_env_or_arg("https://gql.hashnode.com")

def gql(token: str, query: str, variables: dict):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}".strip()
    }
    r = requests.post(GRAPHQL_ENDPOINT, json={"query": query, "variables": variables},
                      headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

QUERY_POST = """
query ResolvePost($publicationId: ID!, $slug: String!) {
  publication(id: $publicationId) {
    post(slug: $slug) { id slug }
    redirectedPost(slug: $slug) { id slug }
  }
}
"""

def main():
    if len(sys.argv) < 3:
        print("Usage: hashnode_resolve_article_id.py <HASHNODE_TOKEN> <PUBLICATION_ID> [GQL_ENDPOINT]", file=sys.stderr)
        sys.exit(1)
    token = sys.argv[1]
    publication_id = sys.argv[2]
    data = json.load(sys.stdin)
    slug = data.get("slug")
    candidates = []
    if slug: candidates.append(slug)
    candidates = list(dict.fromkeys(candidates))
    found = None
    for s in candidates:
        resp = gql(token, QUERY_POST, {"publicationId": publication_id, "slug": s})
        pub = (resp.get("data") or {}).get("publication") or {}
        post = pub.get("post")
        if post and post.get("id"):
            found = post; break
        redir = pub.get("redirectedPost")
        if redir and redir.get("id"):
            found = redir; break
    out = {
        "found": bool(found),
        "articleId": found["id"] if found else None,
        "resolvedSlug": found["slug"] if found else None
    }
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()
    