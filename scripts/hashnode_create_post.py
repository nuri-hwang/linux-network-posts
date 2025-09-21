#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Purpose: Create Hashnode post via GraphQL

import sys, json, os, requests

def endpoint_from_env_or_arg(default: str) -> str:
    if len(sys.argv) >= 4 and sys.argv[3].startswith("http"):
        return sys.argv[3]
    return os.getenv("HASHNODE_GQL_ENDPOINT", default)

GRAPHQL_ENDPOINT = endpoint_from_env_or_arg("https://gql.hashnode.com")

MUT_CREATE = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    post { id slug }
  }
}
"""

def gql(token: str, query: str, variables: dict):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}".strip()
    }
    r = requests.post(GRAPHQL_ENDPOINT, json={"query": query, "variables": variables},
                      headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def main():
    if len(sys.argv) < 3:
        print("Usage: hashnode_create_post.py <HASHNODE_TOKEN> <PUBLICATION_ID> [GQL_ENDPOINT]", file=sys.stderr)
        sys.exit(1)
    token = sys.argv[1]
    publication_id = sys.argv[2]
    payload = json.load(sys.stdin)

    title = payload.get("title")
    content = payload.get("content") or ""
    tags = payload.get("tags", [])
    slug = payload.get("slug")
    cover = payload.get("cover")
    publish_as = payload.get("publishAs")
    draft = bool(payload.get("draft", False))

    input_obj = {
        "publicationId": publication_id,
        "title": title,
        "contentMarkdown": content,
        "tags": tags,
        "slug": slug,
        "isDraft": draft
    }
    if cover: input_obj["coverImageUrl"] = cover
    if publish_as: input_obj["authorHandle"] = publish_as

    resp = gql(token, MUT_CREATE, {"input": input_obj})
    print(json.dumps(resp.get("data", {}), ensure_ascii=False))

if __name__ == "__main__":
    main()
