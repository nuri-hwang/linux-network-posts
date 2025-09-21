#! /usr/bin/env python3

import argparse
import sys
import os
import re
import yaml


def parse_frontmatter(text: str, key: str = "") -> dict:
    """
    Parse YAML frontmatter from a markdown text.
    Arguments:
        text: The full markdown text.
        key: Optional specific key to extract from frontmatter.
    Returns:
        A dictionary of frontmatter key-value pairs.
    """
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            try:
                fm = yaml.safe_load(fm_text)
                if isinstance(fm, dict):
                    if key:
                        return fm.get(key, {})
                    return fm
            except Exception:
                pass

    return {}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse frontmatter from markdown file")
    parser.add_argument("md_path", help="Path to the markdown file")
    parser.add_argument("--key", help="Specific frontmatter key to extract", default="")
    args = parser.parse_args()

    if not os.path.isfile(args.md_path):
        print(f"Error: File '{args.md_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    with open(args.md_path, "r", encoding="utf-8") as fd:
        raw = fd.read()

    fm = parse_frontmatter(raw, key=args.key)
    if isinstance(fm, dict):
        for key, value in fm.items():
            print(f"{key}: {value}")
    else:
        print(fm)
