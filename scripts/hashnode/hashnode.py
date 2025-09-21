#!/usr/bin/env python3

import argparse
import json
import sys
import requests


class Hashnode():
    POST_FIELDS = [
        "id",
        "slug",
        "previousSlugs",
        "title",
        "subtitle",
        "author",
        "coAuthors",
        "tags",
        "url",
        "canonicalUrl",
        "publication",
        "cuid",
        "coverImage",
        "bannerImage",
        "brief",
        "readTimeInMinutes",
        "views",
        "series",
        "reactionCount",
        "replyCount",
        "responseCount",
        "featured",
        "commenters",
        "comments",
        "bookmarked",
        "content",
        "likedBy",
        "featuredAt",
        "publishedAt",
        "updatedAt",
        "preferences",
        "seo",
        "ogMetaData",
        "hasLatexInPost",
        "isFollowed",
        "isAutoPublishedFromRSS",
        "features",
        "sourcedFromGithub"
    ]

    def __init__(self, host: str, endpoint: str = "https://gql.hashnode.com", token: str = "") -> None:
        self.host = host
        self.endpoint = endpoint
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def query(self, query: str, variables: dict = {}) -> dict:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            rsp = requests.post(self.endpoint, json=payload, headers=self.headers, timeout=20)
            rsp.raise_for_status()
        except requests.RequestException as e:
            print(f"ERROR: network error: {e}", file=sys.stderr)
            print(rsp.json())
            sys.exit(1)

        try:
            output = rsp.json()
        except ValueError:
            print(f"ERROR: non-JSON response (HTTP {rsp.status_code})", file=sys.stderr)
            sys.exit(1)

        if "errors" in output:
            print(f"GraphQL Error: {output['errors']}", file=sys.stderr)
            sys.exit(1)

        return output
    
    def __type(self, type_name: str) -> dict:
        query = f"""
        query {{
            __type(name: "{type_name}") {{
                name
                fields {{
                    name
                    type {{
                        name
                        ofType {{
                            name
                            kind
                        }}
                    }}
                }}
            }}
        }}
        """

        output = self.query(query)
        return output.get("data", {}).get("__type", {})
    
    def get_fields(self, type_name: str) -> list[str]:
        """Retrieve available fields for a given Hashnode type.
        Args:
            type_name (str): The GraphQL type name (e.g., "Post").
        Returns:
            list[str]: List of field names.
        """

        output = self.__type(type_name)
        return output.get("fields", [])

    def get_post(self, slug: str, fields: list[str] = None) -> dict:
        """Retrieve a Hashnode post by its slug.
        Args:
            endpoint (str): The GraphQL endpoint URL.
            host (str): The publication host.
            slug (str): The article slug.
            fields (list[str]): List of fields to retrieve from the post.
        Returns:
            dict: The JSON response from the API.
        """
        if not fields:
            fields = ["title", "id"]

        query = f"""
        query GetPostBySlug($host: String!, $slug: String!) {{
          publication(host: $host) {{
            post(slug: $slug) {{
              {" ".join(fields)}
            }}
          }}
        }}
        """

        variables = {
            "host": self.host,
            "slug": slug
        }

        output = self.query(query, variables)

        return output["data"]["publication"]["post"]

    def get_posts(self, fields: list[str] = None, first: int = 10,
                  live_check: bool = True) -> dict:
        """Retrieve a list of posts from a Hashnode publication.
        Args:
            endpoint (str): The GraphQL endpoint URL.
            host (str): The publication host (e.g., myblog.hashnode.dev)
            fields (list[str]): List of fields to retrieve from each post.
            first (int): Number of posts to retrieve.
        Returns:
            dict: The JSON response from the API.
        """

        total_posts = self.get_num_posts()
        print(f"Total posts in publication '{self.host}': {total_posts}")

        if live_check:
            available_fields = [f["name"] for f in self.get_fields("Post")]
            print(json.dumps(available_fields, indent=2))
        else:
            available_fields = self.POST_FIELDS

        if not fields:
            fields = ["id", "slug", "title"]
        elif set(fields) - set(available_fields):
            print("ERROR: one or more requested fields are not available in the publication type.", file=sys.stderr)
            sys.exit(1)
        
        query = f"""
        query GetPublicationPosts($host: String!, $first: Int!) {{
            publication(host: $host) {{
                posts(first: $first) {{
                    edges {{
                        node {{
                        {" ".join(fields)}
                        }}
                    }}
                }}
            }}
        }}
        """

        variables = {
            "host": self.host,
            "first": first
        }

        output = self.query(query, variables)

        return output["data"]["publication"]["posts"]["edges"]
    
    def update_post_title(self, id: str, new_title: str) -> dict:
        """Update the title of a Hashnode post.
        Args:
            id (str): The ID of the post to update.
            new_title (str): The new title for the post.
        Returns:
            dict: The JSON response from the API.
        """
        mutation = """
        mutation UpdatePostTitle($input: UpdatePostInput!) {
            updatePost(input: $input) {
                post {
                    id
                    slug
                    title
                }
            }
        }
        """

        variables = {
            "input": {
                "id": id,
                "title": new_title
            }
        }

        output = self.query(mutation, variables)

        return output["data"]["updatePost"]["post"]

    def get_num_posts(self) -> int:
        query = """
        query GetPublicationPostCount($host: String!) {
            publication(host: $host) {
                posts (first: 0) {
                    totalDocuments
                }
            }
        }
        """

        variables = {
            "host": self.host
        }

        output = self.query(query, variables)

        return output["data"]["publication"]["posts"]["totalDocuments"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get list of posts from a Hashnode publication")
    subparser = parser.add_subparsers(dest="command")

    # Create a subparser for the "get_posts" command
    p = subparser.add_parser("get_posts", help="Get posts from a Hashnode publication")
    p.add_argument("--host", required=True, help="Hashnode publication host (e.g., yourblog.hashnode.dev)")
    p.add_argument("--endpoint", default="https://gql.hashnode.com", help="GraphQL endpoint URL")
    p.add_argument("--fields", help="Comma-separated fields to retrieve (default: title,slug,id,brief,url)")
    p.add_argument("--first", type=int, default=10, help="Number of posts to fetch (default: 10)")
    p.add_argument("--token", help="Hashnode API token")

    p = subparser.add_parser("get_post", help="Get a Hashnode post by its slug")
    p.add_argument("--slug", required=True, help="Slug of the post to retrieve")
    p.add_argument("--fields", help="Comma-separated fields to retrieve (default: title,slug,id,brief,url)")
    p.add_argument("--host", required=True, help="Hashnode publication host (e.g., yourblog.hashnode.dev)")
    p.add_argument("--endpoint", default="https://gql.hashnode.com", help="GraphQL endpoint URL")
    p.add_argument("--token", help="Hashnode API token")

    p = subparser.add_parser("update_post", help="Update a Hashnode post")
    p.add_argument("--slug", required=True, help="Slug of the post to update")
    p.add_argument("--new_title", required=True, help="New title for the post")
    p.add_argument("--host", required=True, help="Hashnode publication host (e.g., yourblog.hashnode.dev)")
    p.add_argument("--endpoint", default="https://gql.hashnode.com", help="GraphQL endpoint URL")
    p.add_argument("--token", required=True, help="Hashnode API token")

    args = parser.parse_args()
    if args.command == "get_posts":

        fields = args.fields.split(",") if args.fields else None
        output = Hashnode(args.host, args.endpoint, token=args.token).get_posts(fields, args.first)

        if output:
            posts = output
            print(json.dumps(output, indent=2))

            if not posts:
                print("No posts found or publication not found.")
                sys.exit(0)
    elif args.command == "get_post":
        fields = args.fields.split(",") if args.fields else None
        output = Hashnode(args.host, args.endpoint, token=args.token).get_post(args.slug, fields)

        if output:
            print(json.dumps(output, indent=2))
    elif args.command == "update_post":
        id = Hashnode(args.host, args.endpoint, token=args.token).get_post(args.slug, ["id"])["id"]
        output = Hashnode(args.host, args.endpoint, token=args.token).update_post_title(id, args.new_title)

        if output:
            print("Post updated successfully:")
            print(json.dumps(output, indent=2))
    else:
        parser.print_help()
