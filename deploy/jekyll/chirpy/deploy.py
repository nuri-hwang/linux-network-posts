#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import yaml


def clear_post_directory(path: Path) -> None:
    for post in path.iterdir():
        if post.is_file() and post.suffix == ".md":
            post.unlink()
            print(f"REMOVED: {post}")

def write_post(src: str, dst: str, frontmatter: str) -> None:
    _src = Path(src)
    _dst = Path(dst)

    if not _src.is_file():
        raise FileNotFoundError(f"post not found: {src}")

    _dst.parent.mkdir(parents=True, exist_ok=True)

    body = _src.read_text(encoding="utf-8")
    if frontmatter:
        body = frontmatter + "\n" + body

    _dst.write_text(body, encoding="utf-8")
    print(f"WRITTEN: {_dst}")

def overwrite_overlay(site_root: Path) -> None:
    overlay_dir = Path(__file__).parent / "overlay"
    for item in overlay_dir.iterdir():
        dst = site_root / item.name
        if item.is_file():
            dst.write_bytes(item.read_bytes())
            print(f"OVERWRITTEN: {dst}")
        elif item.is_dir():
            if dst.exists():
                if dst.is_file():
                    dst.unlink()
                    print(f"REMOVED: {dst}")
            else:
                dst.mkdir(parents=True)
                print(f"CREATED: {dst}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy Chirpy Jekyll")
    parser.add_argument("--site-root", default="sites/jekyll/chirpy",
                        help="Root directory of the Jekyll site")
    parser.add_argument("--plan-yaml", default="deploy-plan.yaml",
                        help="Path to the plan YAML file")
    args = parser.parse_args()
    
    site_root = Path(args.site_root)
    if not site_root.is_dir():
        print(f"Site root not found: {site_root}", file=sys.stderr)
        return 2

    plan_path = Path(__file__).parent / args.plan_yaml
    if not plan_path.is_file():
        print(f"Plan file not found: {plan_path}", file=sys.stderr)
        return 2

    clear_post_directory(site_root / "_posts")

    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))

    for post in plan["posts"]:
        write_post(post["post"], dst=post["copyto"], frontmatter=post["frontmatter"])

    overwrite_overlay(site_root)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
