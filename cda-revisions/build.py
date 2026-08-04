#!/usr/bin/env python3
"""Construit les fiches HTML de revision a partir des sources Markdown de _src/.

Usage : python3 build.py   (depuis le dossier cda-revisions/)

Dependances : markdown, pygments
    python3 -m venv venv && ./venv/bin/pip install markdown pygments
"""

import re
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "_src"
TEMPLATE = (ROOT / "template.html").read_text(encoding="utf-8")

EXTENSIONS = [
    "extra",          # tables, fenced_code, attr_list, def_list, abbr, footnotes
    "toc",
    "sane_lists",
    "admonition",
    "codehilite",
]
EXTENSION_CONFIGS = {
    "toc": {"toc_depth": "2-3", "anchorlink": False, "permalink": False},
    "codehilite": {"guess_lang": False, "css_class": "codehilite"},
}


MERMAID_RE = re.compile(r"^```mermaid\n(.*?)^```", re.MULTILINE | re.DOTALL)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_one(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")

    # Premier titre de niveau 1 = titre de la page (onglet navigateur).
    m = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    title = m.group(1).strip() if m else md_path.stem

    # Les blocs mermaid sont sortis du flux Markdown : codehilite les traiterait
    # comme du code source et Mermaid ne les verrait jamais.
    diagrams: list[str] = []

    def _stash(match: re.Match) -> str:
        diagrams.append(match.group(1))
        return f"\n<!--MERMAID{len(diagrams) - 1}-->\n"

    text = MERMAID_RE.sub(_stash, text)

    md = markdown.Markdown(extensions=EXTENSIONS, extension_configs=EXTENSION_CONFIGS)
    body = md.convert(text)
    toc = md.toc

    for i, src in enumerate(diagrams):
        body = body.replace(
            f"<!--MERMAID{i}-->", f'<pre class="mermaid">{_escape(src)}</pre>'
        )

    html = (
        TEMPLATE.replace("{{TITLE}}", title)
        .replace("{{TOC}}", toc)
        .replace("{{BODY}}", body)
    )
    out = ROOT / (md_path.stem + ".html")
    out.write_text(html, encoding="utf-8")
    return out.name


def main() -> int:
    if not SRC.is_dir():
        print(f"Dossier introuvable : {SRC}", file=sys.stderr)
        return 1
    sources = sorted(SRC.glob("*.md"))
    if not sources:
        print(f"Aucun .md dans {SRC}", file=sys.stderr)
        return 1
    for md_path in sources:
        print(f"  {md_path.name} -> {build_one(md_path)}")
    print(f"{len(sources)} fiche(s) construite(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
