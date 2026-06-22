#!/usr/bin/env python3
"""Replace one already-inlined figure in an HTML file by matching its <img> alt text.
Usage: python update_fig.py <html> <alt-text> <figures/relpath.png>"""
import base64, os, re, sys

HTML, ALT, REL = sys.argv[1], sys.argv[2], sys.argv[3]
PAPER = os.path.dirname(os.path.abspath(HTML))

with open(HTML, encoding="utf-8") as f:
    html = f.read()
with open(os.path.join(PAPER, REL), "rb") as fp:
    b64 = "data:image/png;base64," + base64.b64encode(fp.read()).decode("ascii")

# replace the src="..." of the <img ... alt="ALT"> (src has no quotes inside, so [^"]* is safe)
pat = re.compile(r'(<img class="figimg" src=")[^"]*(" alt="' + re.escape(ALT) + r'")')
new, n = pat.subn(lambda m: m.group(1) + b64 + m.group(2), html)
if n == 0:
    print("NO MATCH for alt:", ALT); sys.exit(1)
with open(HTML, "w", encoding="utf-8") as f:
    f.write(new)
print(f"updated {n} image(s) for alt '{ALT}'  ({os.path.getsize(HTML)/1024:.0f} KB)")
