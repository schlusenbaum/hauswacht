"""Die Dokumentation muss in sich stimmig sein: keine toten Links, keine fehlenden Anker."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP = {".git", ".venv", "node_modules"}


def _markdown_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*.md")
        if not SKIP.intersection(path.relative_to(ROOT).parts)
        and "custom_components" not in path.parts
    ]


def _slug(heading: str) -> str:
    text = re.sub(r"[`*_]", "", heading.strip().lower())
    return "".join(ch for ch in text if ch.isalnum() or ch in "- ").replace(" ", "-")


def _without_code(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def _anchors(path: Path) -> set[str]:
    seen: dict[str, int] = {}
    result: set[str] = set()
    for line in _without_code(path.read_text(encoding="utf-8")).splitlines():
        if match := re.match(r"^#{1,6} (.*)", line):
            slug = _slug(match.group(1))
            count = seen.get(slug, 0)
            seen[slug] = count + 1
            result.add(slug if count == 0 else f"{slug}-{count}")
    return result


def test_internal_links_and_anchors_exist() -> None:
    problems: list[str] = []
    for path in _markdown_files():
        text = _without_code(path.read_text(encoding="utf-8"))
        for url in re.findall(r"\]\(([^)\s]+)\)", text):
            if url.startswith(("http://", "https://", "mailto:")):
                continue
            target_part, _, anchor = url.partition("#")
            target = (path.parent / target_part).resolve() if target_part else path
            name = path.relative_to(ROOT)
            if not target.exists():
                problems.append(f"{name}: {url} fehlt")
            elif anchor and target.suffix == ".md" and anchor not in _anchors(target):
                problems.append(f"{name}: Anker {url} fehlt")
    assert problems == []


def test_every_doc_page_is_linked_from_the_index() -> None:
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    pages = [p.name for p in (ROOT / "docs").glob("*.md") if p.name != "README.md"]
    missing = [page for page in pages if f"({page}" not in index]
    assert missing == []
