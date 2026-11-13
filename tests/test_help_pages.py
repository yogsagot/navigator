"""``navigator/lib/help/pages.py``: finding Help's pages and pictures."""

from __future__ import annotations

from pathlib import Path

import pytest

from navigator.lib.help import pages

RUN = "\x1b[0;38;2;1;2;3;48;2;4;5;6m"


@pytest.fixture
def docs(tmp_path, monkeypatch):
    """A small tree: English whole, Latvian with one page and one picture."""
    for name, text in {
        "en/README.md": "# Contents\n",
        "en/clipboard.md": "# Copy and paste\n",
        "en/editor/macros.md": "# Macros\n",
        "en/shots/box.ans": f"{RUN}en\x1b[0m\n",
        "en/shots/box.svg": "<svg/>",
        "en/shots/only-svg.svg": "<svg/>",
        "en/shots/broken.ans": "not what the tool writes\n",
        "en/shots/broken.svg": "<svg/>",
        "lv/README.md": "# Saturs\n",
        "lv/shots/box.ans": f"{RUN}lv\x1b[0m\n",
        "screenshot.svg": "<svg/>",
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    monkeypatch.setattr(pages, "root", lambda: tmp_path)
    return tmp_path


def test_the_shipped_pages_are_found_from_a_checkout():
    assert (pages.root() / "en" / "README.md").is_file()
    assert pages.read(pages.CONTENTS, "en").data.startswith(b"# Navigator help")
    cells = pages.shot("README.md", "shots/make-directory.svg", "en")
    assert cells is not None and len(cells) == 9 and len(cells[0]) == 50


def test_a_page_is_read_in_its_language_or_else_in_english(docs):
    assert pages.read("README.md", "lv") == pages.Page("README.md", b"# Saturs\n", "lv")
    assert pages.read("clipboard.md", "lv") == pages.Page("clipboard.md", b"# Copy and paste\n", "en")
    assert pages.read("editor/macros.md", "en").language == "en"
    # A regional code falls back to its language before English.
    assert pages.read("README.md", "lv_LV").language == "lv"
    # A language there is no directory for, or no language at all, is English.
    assert pages.read("README.md", "de").language == "en"
    assert pages.read("README.md", "../en").language == "en"


@pytest.mark.parametrize("name", ["nothing.md", "", "../screenshot.svg", "/etc/passwd", "editor", "."])
def test_a_page_that_is_not_there_is_not_found(docs, name):
    with pytest.raises(pages.PageNotFound):
        pages.read(name, "en")
    assert not pages.exists(name)


def test_a_topic_is_a_page_and_an_anchor(docs):
    assert pages.split("clipboard.md#quick-start") == ("clipboard.md", "quick-start")
    assert pages.split("clipboard.md") == ("clipboard.md", "")
    assert pages.exists("clipboard.md#quick-start") and pages.exists("README.md", "lv")


@pytest.mark.parametrize(
    "page, href, topic",
    [
        ("README.md", "clipboard.md", "clipboard.md"),
        ("README.md", "editor/macros.md#record", "editor/macros.md#record"),
        ("editor/macros.md", "../clipboard.md#keys", "clipboard.md#keys"),
        ("editor/macros.md", "find.md", "editor/find.md"),
        ("editor/macros.md", "#record", "editor/macros.md#record"),
        ("README.md", "./clipboard.md", "clipboard.md"),
        # Out of Help: other sites, and anything above the language's directory.
        ("README.md", "https://example.org/x.md", None),
        ("README.md", "mailto:someone@example.org", None),
        ("README.md", "../lv/README.md", None),
        ("editor/macros.md", "../../README.md", None),
        ("README.md", "/etc/passwd", None),
    ],
)
def test_a_link_leads_to_a_topic_or_out_of_help(page, href, topic):
    assert pages.follow(page, href) == topic


def test_a_picture_is_its_ans_file_in_the_language_or_else_english(docs):
    assert [char for char, _ in pages.shot("README.md", "shots/box.svg", "lv")[0]] == ["l", "v"]
    assert [char for char, _ in pages.shot("README.md", "shots/box.svg", "de")[0]] == ["e", "n"]
    # Named from a page in a subdirectory.
    assert pages.shot("editor/macros.md", "../shots/box.svg", "en") is not None


@pytest.mark.parametrize(
    "source",
    [
        "shots/only-svg.svg",  # no .ans beside it
        "shots/broken.svg",  # an .ans the tool did not write
        "shots/nothing.svg",
        "shots/box.png",  # not a screenshot of ours
        "https://example.org/shots/box.svg",
        "../screenshot.svg",  # the README's picture, above the language
    ],
)
def test_a_picture_that_cannot_be_shown_is_none(docs, source):
    assert pages.shot("README.md", source, "en") is None


def test_the_packaging_takes_the_pages_and_the_ans_files_only():
    root = Path(__file__).resolve().parent.parent
    assert 'package_dir={"navigator.docs": "docs"}' in (root / "setup.py").read_text(encoding="utf-8")
    assert '"navigator.docs" = ["**/*.md", "**/*.ans"]' in (root / "pyproject.toml").read_text(encoding="utf-8")
