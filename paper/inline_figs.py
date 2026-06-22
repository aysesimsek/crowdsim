#!/usr/bin/env python3
"""Inline every figures/*.png referenced in a given HTML file as a base64 data URI (self-contained).
Idempotent: already-inlined data: URIs are not re-matched. Usage: python inline_figs.py <file.html>"""
import base64, os, re, sys

HTML = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "story.html")
PAPER = os.path.dirname(os.path.abspath(HTML))


def main():
    with open(HTML, encoding="utf-8") as f:
        html = f.read()
    inlined, missing = [], []

    def repl(m):
        rel = m.group(1)
        p = os.path.join(PAPER, rel)
        if not os.path.exists(p):
            missing.append(rel); return m.group(0)
        with open(p, "rb") as fp:
            b64 = base64.b64encode(fp.read()).decode("ascii")
        inlined.append(rel)
        return 'src="data:image/png;base64,' + b64 + '"'

    html = re.sub(r'src="(figures/[^"]+\.png)"', repl, html)
    with open(HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"inlined {len(inlined)}: " + ", ".join(os.path.basename(x) for x in inlined))
    if missing:
        print("MISSING: " + ", ".join(missing))
    print(f"{os.path.basename(HTML)}: {os.path.getsize(HTML)/1024:.0f} KB (self-contained)")


if __name__ == "__main__":
    main()
