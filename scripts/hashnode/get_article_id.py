#!/usr/bin/env python3

import argparse
import requests
import sys


def get_hashnode_article_id():
    parser = argparse.ArgumentParser(description="Get Hashnode articleId by host and slug")
    parser.add_argument("--host", required=True, help="Publication host")
    parser.add_argument("--slug", required=True, help="Post slug")
    parser.add_argument("--endpoint", default="https://gql.hashnode.com", help="Endpoint URL")
    args = parser.parse_args()

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "hashnode-post-id/1.0"
    }
    payload = {
        "query": """
            query GetPostBySlug($host: String!, $slug: String!) {
                publication(host: $host) {
                    post(slug: $slug) { id }
                }
            }
            """,
        "variables": {"host": args.host, "slug": args.slug}
    }

    try:
        resp = requests.post(args.endpoint, json=payload, headers=headers, timeout=20)
    except requests.RequestException as e:
        print(f"ERROR: network error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        output = resp.json()
    except ValueError:
        print(f"ERROR: non-JSON response (HTTP {resp.status_code})", file=sys.stderr)
        sys.exit(1)

    # Extract id
    post_id = ""
    if output:
        post_id = output.get("data", {}).get("publication", {}).get("post", {}).get("id")
    
    if post_id:
        print(post_id)
    else:
        print("")  # Not found

if __name__ == "__main__":
    get_hashnode_article_id()
