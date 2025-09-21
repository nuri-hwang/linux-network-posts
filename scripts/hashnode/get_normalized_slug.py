#!/usr/bin/env python3

import argparse
import sys
import os
import re
import yaml


def normalize_slug(slug: str) -> str:
    s = (slug or "").strip().lower()
    s = s.replace("_", " ")
    s = re.sub(r"\s+", "-", s) # spaces -> hyphen
    s = re.sub(r"[^a-z0-9-]", "", s) # remove invalid chars
    s = re.sub(r"-{2,}", "-", s) # collapse multiple -
    return s.strip("-")

def get_frontmatter(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[1]
    return ""

def get_normalized_slug(md_path: str) -> tuple[str, int]:
    """
    Extract and normalize slug from markdown file's frontmatter.
    Arguments:
        md_path: Path to the markdown file.
    Returns (normalized_slug, exit_code).
    """
    if not os.path.isfile(md_path):
        return "", 1

    with open(md_path, "r", encoding="utf-8") as fd:
        raw = fd.read()

    fm_text = get_frontmatter(raw)
    if not fm_text:
        return "", 0

    try:
        fm = yaml.safe_load(fm_text)
    except Exception:
        return "", 1

    slug = fm.get("slug")
    if slug:
        return normalize_slug(slug), 0
    else:
        return "", 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get normalized slug from markdown file")
    parser.add_argument("md_path", help="Path to the markdown file")
    args = parser.parse_args()

    slug, exit_code = get_normalized_slug(args.md_path)
    print(slug)
    sys.exit(exit_code)
