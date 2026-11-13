"""The rules Help's pages keep (the ``navigator-help`` skill): the tree under
``docs/``, the Markdown both GitHub and Navigator render, links and pictures
that lead somewhere."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from markdown_it import MarkdownIt

from navigator.lib.help import ansi
from navigator.lib.viewer import markdown

DOCS = Path(__file__).resolve().parent.parent / "docs"
ENGLISH = DOCS / "en"
PAGES = sorted(DOCS.glob("*/**/*.md"))


def tokens_of(page: Path) -> list:
    """Every token of *page*, inline children included."""
    parser = MarkdownIt("commonmark").enable("table").enable("strikethrough")
    found = []
    for token in parser.parse(page.read_text(encoding="utf-8")):
        found.append(token)
        found.extend(token.children or ())
    return found


def slugs_of(page: Path) -> set[str]:
    """The anchors of *page*'s headings, as Help finds them."""
    return set(markdown.render(page.read_bytes(), 80).anchors)


def test_docs_holds_language_directories_and_the_readme_picture_only():
    names = {path.name for path in DOCS.iterdir()}
    files = {name for name in names if (DOCS / name).is_file()}
    assert all(name.startswith("screenshot") and name.endswith(".svg") for name in files), files
    assert "en" in names and (ENGLISH / "README.md").is_file()


def test_every_language_has_the_english_tree_and_nothing_else():
    english = {path.relative_to(ENGLISH) for path in ENGLISH.rglob("*")}
    for language in DOCS.iterdir():
        if language.is_dir() and language != ENGLISH:
            extra = {path.relative_to(language) for path in language.rglob("*")} - english
            assert not extra, f"docs/{language.name} has what docs/en does not: {sorted(map(str, extra))}"


@pytest.mark.parametrize("page", PAGES, ids=lambda page: str(page.relative_to(DOCS)))
def test_a_page_has_no_raw_html(page):
    for token in tokens_of(page):
        if token.type in ("html_block", "html_inline"):
            html = token.content.strip()
            assert html.startswith("<!--") and html.endswith("-->"), f"{page.name}: raw HTML {html[:40]!r}"


@pytest.mark.parametrize("page", PAGES, ids=lambda page: str(page.relative_to(DOCS)))
def test_a_page_links_only_to_what_is_there(page):
    root = page.relative_to(DOCS).parts[0]
    for token in tokens_of(page):
        if token.type != "link_open":
            continue
        href = token.attrGet("href") or ""
        if re.match(r"[a-z][a-z0-9+.-]*:", href):
            continue  # another site's
        target, _, anchor = href.partition("#")
        other = (page.parent / target).resolve() if target else page
        assert other.is_file(), f"{page.name}: {href} leads nowhere"
        assert other.relative_to(DOCS).parts[0] == root, f"{page.name}: {href} leaves docs/{root}"
        if anchor:
            assert anchor in slugs_of(other), f"{page.name}: no heading for {href}"


@pytest.mark.parametrize("page", PAGES, ids=lambda page: str(page.relative_to(DOCS)))
def test_a_picture_has_alt_text_and_both_files(page):
    for token in tokens_of(page):
        if token.type != "image":
            continue
        source = token.attrGet("src") or ""
        assert token.content.strip(), f"{page.name}: {source} has no alt text"
        svg = (page.parent / source).resolve()
        assert svg.suffix == ".svg" and svg.parent.name == "shots" and svg.is_file(), f"{page.name}: {source}"
        ansi.read(svg.with_suffix(".ans").read_text(encoding="utf-8"))


def declared_topics() -> list[tuple[str, str]]:
    """Every ``help_topic`` a document or a module declares, with where."""
    root = DOCS.parent
    found = []
    pattern = re.compile(r"""help_topic\s*[:=]\s*["']([^"']+)["']""")
    for package in ("navkit", "navml", "navigator"):
        for path in sorted((root / package).rglob("*")):
            if path.suffix not in (".nml", ".py") or path.name.endswith("_nml.py"):
                continue
            for topic in pattern.findall(path.read_text(encoding="utf-8")):
                found.append((str(path.relative_to(root)), topic))
    return found


def test_every_help_topic_a_dialog_or_window_names_is_a_page_and_a_heading():
    for where, topic in declared_topics():
        name, _, anchor = topic.partition("#")
        page = ENGLISH / name
        assert page.is_file(), f"{where}: no help page {name}"
        assert not anchor or anchor in slugs_of(page), f"{where}: no heading #{anchor} in {name}"
