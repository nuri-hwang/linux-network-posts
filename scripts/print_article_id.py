#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Purpose: Extract articleId from various Hashnode GraphQL responses

import sys, json

def find_id(obj):
    if obj is None:
        return None
    if isinstance(obj, dict):
        for k in ("post", "createPost", "updatePost"):
            if k in obj:
                found = find_id(obj[k])
                if found: return found
        if "id" in obj and isinstance(obj["id"], str):
            return obj["id"]
        for v in obj.values():
            found = find_id(v)
            if found: return found
    elif isinstance(obj, list):
        for it in obj:
            found = find_id(it)
            if found: return found
    return None

def main():
    raw = sys.stdin.read().strip()
    if not raw:
        print("")
        return
    try:
        data = json.loads(raw)
    except Exception:
        print("")
        return
    root = data.get("data", data)
    aid = find_id(root)
    print(aid or "")

if __name__ == "__main__":
    main()
