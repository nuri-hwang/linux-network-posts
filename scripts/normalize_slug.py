#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Purpose: Normalize slug for Hashnode constraints

import sys, json, re, os

def to_slug(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("_", " ")
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^a-z0-9\-]", "", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s

def derive_from_filename(name: str) -> str:
    base = os.path.splitext(os.path.basename(name or "post"))[0]
    return to_slug(base)

def main():
    if sys.stdin.isatty():
        print("Usage: parse_frontmatter.py <file> | normalize_slug.py", file=sys.stderr)
        sys.exit(1)
    data = json.load(sys.stdin)
    slug = data.get("slug")
    title = data.get("title")
    filename = data.get("filename") or data.get("sourcePath")
    if slug:
        normalized = to_slug(slug)
    elif title:
        normalized = to_slug(title)
    else:
        normalized = derive_from_filename(filename)
    data["slug"] = normalized
    print(json.dumps(data, ensure_ascii=False))

if __name__ == "__main__":
    main()
