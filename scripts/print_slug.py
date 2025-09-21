#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Purpose: Print "slug" field from stdin JSON

import sys, json

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
    print(data.get("slug", "") or "")

if __name__ == "__main__":
    main()
