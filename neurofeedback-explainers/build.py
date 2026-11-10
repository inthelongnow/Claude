#!/usr/bin/env python3
"""Assemble src/ into one self-contained page.

  python3 build.py

Writes dist/neurofeedback-guide.html, which opens directly in a browser.
To add a section, drop a new file in src/modules/; files are included in name order.

  python3 build.py --fragment some/path.html

additionally writes the page without its <html> wrapper, for hosts that supply their own.
"""
import sys
from pathlib import Path

here = Path(__file__).parent
src = here / "src"
shell = (src / "shell.html").read_text(encoding="utf-8")
modules = "\n".join(p.read_text(encoding="utf-8") for p in sorted((src / "modules").glob("*.html")))
page = (shell
        .replace("/*{{CSS}}*/", (src / "app.css").read_text(encoding="utf-8"))
        .replace("/*{{CORE}}*/", (src / "core.js").read_text(encoding="utf-8"))
        .replace("<!--{{MODULES}}-->", modules))

head_end = page.index('<div class="app">')
head, body = page[:head_end], page[head_end:]
full = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        + head + "</head>\n<body>\n" + body + "</body>\n</html>\n")

dist = here / "dist"
dist.mkdir(exist_ok=True)
(dist / "neurofeedback-guide.html").write_text(full, encoding="utf-8")
if "--fragment" in sys.argv:
    Path(sys.argv[sys.argv.index("--fragment") + 1]).write_text(page, encoding="utf-8")
print(f"built {len(full) // 1024} KB, {modules.count('<section class=')} sections")
