"""What the layout has for a reader of linked pages (F1 Help): heading
anchors, the links of a page, and pictures."""

from __future__ import annotations

from navigator.lib.viewer import markdown
from navigator.lib.viewer.layout import slug
from navkit.style import Style

SHOT = [[(char, Style(fg=(1, 2, 3), bg=(4, 5, 6))) for char in line] for line in ("╔══╗", "║ok║", "╚══╝")]


def text_of(layout, link):
    return " ".join("".join(c[0] for c in layout.rows[row].cells[start:end]) for row, start, end in link.spans)


# -- anchors ------------------------------------------------------------------


def test_a_slug_is_githubs():
    assert slug("Quick start") == "quick-start"
    assert slug("On a remote server over ssh") == "on-a-remote-server-over-ssh"
    assert slug("What `Ctrl+C` does, and why?") == "what-ctrlc-does-and-why"
    assert slug("Snake_case and kebab-case") == "snake_case-and-kebab-case"
    assert slug("Kopēšana un ielīmēšana") == "kopēšana-un-ielīmēšana"
    taken: dict[str, int] = {}
    assert [slug("Keys", taken) for _ in range(3)] == ["keys", "keys-1", "keys-2"]


def test_every_heading_has_an_anchor_at_its_first_row():
    layout = markdown.render(b"# Top\n\ntext\n\n## Copy `F5`\n\nmore\n\n## Copy `F5`\n\nlast\n", 40)
    assert list(layout.anchors) == ["top", "copy-f5", "copy-f5-1"]
    for name, row in layout.anchors.items():
        assert layout.rows[row].text.startswith(("Top", "Copy F5")), name
    assert layout.anchors["top"] == 0
    assert layout.anchors["copy-f5"] < layout.anchors["copy-f5-1"]


def test_a_heading_wrapped_has_one_anchor_reading_all_of_it():
    layout = markdown.render(b"## A heading far too long for the width\n", 12)
    assert list(layout.anchors) == ["a-heading-far-too-long-for-the-width"]


# -- links --------------------------------------------------------------------


def test_the_links_of_a_page_in_reading_order():
    layout = markdown.render(
        b"See [copying](file-operations.md#copy) and [the editor](editor.md).\n\n"
        b"- [Panels](panels.md)\n- plain\n- [Site](https://example.org)\n", 60)
    links = layout.links()
    assert [(link.href, text_of(layout, link)) for link in links] == [
        ("file-operations.md#copy", "copying"),
        ("editor.md", "the editor"),
        ("panels.md", "Panels"),
        ("https://example.org", "Site"),
    ]
    assert [link.row for link in links] == sorted(link.row for link in links)
    assert layout.links() is links  # made once


def test_a_link_wrapped_over_rows_is_one_link():
    layout = markdown.render(b"Go and read [the page about copying files](copy.md) now.\n", 20)
    (link,) = layout.links()
    assert len(link.spans) > 1
    assert text_of(layout, link) == "the page about copying files"
    assert [row for row, _, _ in link.spans] == list(range(link.row, link.row + len(link.spans)))


def test_a_wrapped_link_in_a_list_item_keeps_clear_of_the_bullet():
    layout = markdown.render(b"- [a link long enough to wrap twice over](x.md)\n", 16)
    (link,) = layout.links()
    assert text_of(layout, link) == "a link long enough to wrap twice over"
    assert all(start >= layout.rows[row].lead for row, start, _ in link.spans)


def test_two_items_linking_the_same_page_are_two_links():
    layout = markdown.render(b"- [one](x.md)\n- [one](x.md)\n\n[one](x.md)\n[one](x.md)\n", 40)
    assert [link.href for link in layout.links()] == ["x.md"] * 4


def test_an_image_among_text_is_a_link_marked_as_an_image():
    layout = markdown.render(b"Before ![a box](shots/box.svg) after [x](y.md).\n", 60)
    image, link = layout.links()
    assert (image.href, image.image, text_of(layout, image)) == ("shots/box.svg", True, "[a box]")
    assert (link.href, link.image) == ("y.md", False)


# -- pictures -----------------------------------------------------------------


def test_an_image_alone_in_a_paragraph_is_drawn_from_its_cells():
    asked = []

    def pictures(source):
        asked.append(source)
        return SHOT

    layout = markdown.render(b"Above.\n\n![A box](shots/box.svg)\n\nBelow.\n", 40, pictures=pictures)
    assert asked == ["shots/box.svg"]
    assert [row.text for row in layout.rows] == ["Above.", "", "╔══╗", "║ok║", "╚══╝", "", "Below."]
    drawn = [row for row in layout.rows if row.picture is not None]
    assert [row.picture for row in drawn] == SHOT
    assert all(cell[1] == ("picture",) for row in drawn for cell in row.cells)
    assert len({row.block for row in drawn}) == 1
    assert layout.links() == []  # a picture shown is no link


def test_a_picture_in_a_list_item_stands_after_the_bullet():
    layout = markdown.render(b"- ![A box](shots/box.svg)\n", 40, pictures=lambda source: SHOT)
    drawn = [row for row in layout.rows if row.picture is not None]
    assert [row.lead for row in drawn] == [2, 2, 2]
    assert drawn[0].text == "• ╔══╗" and drawn[1].text == "  ║ok║"


def test_a_picture_too_wide_or_unknown_or_among_text_is_its_alt_text():
    for width, pictures, source in (
        (3, lambda source: SHOT, b"![A box](shots/box.svg)\n"),  # wider than the room
        (40, lambda source: None, b"![A box](shots/box.svg)\n"),  # nothing to show
        (40, lambda source: SHOT, b"See ![A box](shots/box.svg) here.\n"),  # among text
        (40, None, b"![A box](shots/box.svg)\n"),  # the viewer, which passes none
    ):
        layout = markdown.render(source, width, pictures=pictures)
        assert all(row.picture is None for row in layout.rows)
        assert "[Abox]" in "".join(row.text for row in layout.rows).replace(" ", "")
        assert any(link.image for link in layout.links())


def test_the_viewer_is_given_no_pictures_and_nothing_else_changed():
    plain = markdown.render(b"# T\n\n![A box](shots/box.svg)\n", 40)
    assert [row.text for row in plain.rows] == ["T", "═", "", "[A box]"]
