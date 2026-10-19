#!/usr/bin/env python3
"""Build a single-file HTML from a report markdown source.

Features:
  - :::details Summary ... ::: blocks -> collapsed <details> sections
    (closed by default, expandable; works in any browser)
  - all local images inlined as base64 data URIs -> one self-contained file
  - clean typography, light/dark themes

CLI (from repo root):
    ~/ds_env/bin/python farit/src/analysis/build_report_html.py \
        farit/docs/next-directions-2026-10.md
"""
from __future__ import annotations

import argparse
import base64
import re
import sys
from pathlib import Path

import markdown

DETAILS_RE = re.compile(r"^:::details ([^\n]+)\n(.*?)^:::[ \t]*$", re.M | re.S)
IMG_RE = re.compile(r'src="([^"]+)"')

MD_EXTENSIONS = ["tables", "fenced_code", "sane_lists"]

CSS = """
:root { --fg:#1f2328; --muted:#59636e; --bg:#ffffff; --border:#d1d9e0; --code:#f6f8fa;
        --link:#0969da; --details:#f6f8fa; }
@media (prefers-color-scheme: dark) {
  :root { --fg:#e6edf3; --muted:#9198a1; --bg:#0d1117; --border:#3d444d; --code:#151b23;
          --link:#4493f8; --details:#151b23; }
}
body { font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
       color: var(--fg); background: var(--bg); max-width: 48rem;
       margin: 0 auto; padding: 2.5rem 1.4rem 4rem; line-height: 1.62; font-size: 16px; }
h1 { font-size: 1.65rem; line-height: 1.3; border-bottom: 1px solid var(--border); padding-bottom: .45rem; }
h2 { font-size: 1.28rem; margin-top: 2.2rem; border-bottom: 1px solid var(--border); padding-bottom: .3rem; }
h3 { font-size: 1.08rem; margin-top: 1.6rem; }
a { color: var(--link); }
strong { font-weight: 650; }
img { max-width: 100%; height: auto; display: block; margin: .9rem auto; }
table { border-collapse: collapse; margin: 1rem 0; font-size: .92rem; width: 100%; }
th, td { border: 1px solid var(--border); padding: .38rem .6rem; text-align: left; }
th { background: var(--code); }
code { background: var(--code); padding: .12rem .3rem; border-radius: 4px; font-size: .88em; }
blockquote { border-left: 3px solid var(--border); margin: 0; padding: 0 0 0 1rem; color: var(--muted); }
details { border: 1px solid var(--border); border-radius: 8px; background: var(--details);
          margin: 1rem 0; padding: 0 .9rem; }
summary { cursor: pointer; font-weight: 600; padding: .55rem 0; user-select: none; }
details[open] { padding-bottom: .6rem; }
hr { border: none; border-top: 1px solid var(--border); margin: 2rem 0; }
"""


def build(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")

    # 1. pull out :::details blocks, replace with placeholders
    chunks: list[str] = []

    def stash(m: re.Match) -> str:
        summary, content = m.group(1).strip(), m.group(2)
        html = markdown.markdown(content, extensions=MD_EXTENSIONS)
        chunks.append(f"<details><summary>{summary}</summary>\n{html}\n</details>")
        return f"@@DETAILS_{len(chunks) - 1}@@"

    text = DETAILS_RE.sub(stash, text)

    # 2. convert the rest
    body = markdown.markdown(text, extensions=MD_EXTENSIONS)

    # 3. restore details (placeholder sits inside its own <p>)
    for i, html in enumerate(chunks):
        body = body.replace(f"<p>@@DETAILS_{i}@@</p>", html)
        body = body.replace(f"@@DETAILS_{i}@@", html)  # safety: bare occurrence

    # 4. inline images as base64
    def embed(m: re.Match) -> str:
        src = m.group(1)
        if src.startswith("data:"):
            return m.group(0)
        p = (md_path.parent / src).resolve()
        if not p.exists():
            print(f"WARNING: image not found: {p}", file=sys.stderr)
            return m.group(0)
        b64 = base64.b64encode(p.read_bytes()).decode()
        return f'src="data:image/png;base64,{b64}"'

    body = IMG_RE.sub(embed, body)

    # 5. title from first h1
    tm = re.search(r"<h1>(.*?)</h1>", body)
    title = re.sub(r"<[^>]+>", "", tm.group(1)) if tm else md_path.stem

    return (
        "<!DOCTYPE html>\n<html><head><meta charset='utf-8'>\n"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>\n"
        f"<title>{title}</title>\n<style>{CSS}</style></head>\n<body>\n{body}\n</body></html>\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("md", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    out = args.out or args.md.with_suffix(".html")
    html = build(args.md)
    out.write_text(html, encoding="utf-8")
    ok = sum(1 for _ in re.finditer(r"<details>", html))
    imgs = sum(1 for _ in re.finditer(r'src="data:image', html))
    missing = html.count("image not found")
    print(f"wrote {out} ({out.stat().st_size/1024:.0f} KB, {imgs} embedded images, {ok} details blocks)")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
