#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Purpose: Parse YAML frontmatter and markdown body, print JSON to stdout

import sys, re, json, os
import yaml

def split_frontmatter(text: str):
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)\Z', text, re.S)
    if m:
        return m.group(1), m.group(2)
    return None, text

def main():
    if len(sys.argv) < 2:
        print("Usage: parse_frontmatter.py <markdown_file>", file=sys.stderr)
        sys.exit(1)
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    fm_text, body = split_frontmatter(raw)
    meta = {}
    if fm_text:
        meta = yaml.safe_load(fm_text) or {}
    title = meta.get("title")
    tags = meta.get("tags") or meta.get("categories") or []
    slug = meta.get("slug")
    cover = meta.get("cover") or meta.get("coverImage")
    publish_as = meta.get("publishAs") or meta.get("author")
    draft = bool(meta.get("draft")) if "draft" in meta else False

    out = {
        "sourcePath": path,
        "filename": os.path.basename(path),
        "title": title,
        "tags": tags if isinstance(tags, list) else [tags] if tags else [],
        "slug": slug,
        "cover": cover,
        "publishAs": publish_as,
        "draft": draft,
        "content": (body or "").strip()
    }
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()