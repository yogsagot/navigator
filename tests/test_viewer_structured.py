"""F3's structured view: a JSON, YAML, TOML or XML file's data as a tree (a
departure, asked for) -- the model in ``navigator/lib/viewer/structured.py``
and ``StructWindow``."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, IDLE, run_app, settle, Until
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

from navigator.__main__ import Navigator
from navigator.lib.viewer.structured import ParseFailed, find, kind_by_name, parse, path, walk


def keys(node):
    return [(child.key, child.kind, child.text) for child in node.children()]


# -- the model ---------------------------------------------------------------------


def test_json_keeps_order_and_duplicate_keys():
    root = parse(b'{"b": 1, "a": true, "b": null, "s": "x", "f": 1.5}', "json")
    assert keys(root) == [("b", "number", "1"), ("a", "bool", "true"), ("b", "null", "null"),
                          ("s", "string", "x"), ("f", "number", "1.5")]


def test_json_with_a_bom_and_json_lines():
    assert parse(b'\xef\xbb\xbf[1, 2]', "json").count == 2
    root = parse(b'{"a": 1}\n\n{"a": 2}\n', "jsonl")
    assert root.kind == "array" and [c.children()[0].text for c in root.children()] == ["1", "2"]


def test_toml_tables_and_dates():
    root = parse(b'[server]\nport = 8080\nwhen = 1979-05-27\n', "toml")
    assert keys(root.children()[0]) == [("port", "number", "8080"), ("when", "date", "1979-05-27")]


def test_yaml_keeps_tags_places_and_aliases():
    root = parse(b"base: &b\n  x: 1\ncopy: *b\nref: !Ref thing\n", "yaml")
    base, copy, ref = root.children()
    assert keys(base) == [("x", "number", "1")] and keys(copy) == [("x", "number", "1")]
    assert (ref.kind, ref.text) == ("tagged", "!Ref thing")
    assert ref.offset == len(b"base: &b\n  x: 1\ncopy: *b\n")
    # The alias is the node it names: a walk passes it, and does not open it again.
    assert len(list(walk(root))) == 5


def test_yaml_documents_become_a_list():
    root = parse(b"a: 1\n---\n- 2\n", "yaml")
    assert root.kind == "array" and root.count == 2


def test_a_yaml_alias_holding_itself_ends():
    root = parse(b"a: &a\n  - *a\n", "yaml")
    assert len(list(walk(root))) == 3


def test_xml_attributes_text_and_elements():
    root = parse(b'<cfg xmlns="urn:x"><s port="1">hi</s><s/><!-- no --></cfg>', "xml")
    assert root.key == "cfg" and root.count == 2
    first = root.children()[0]
    assert keys(first) == [("port", "attribute", "1"), ("#text", "text", "hi")]
    assert path(first.children()[0]) == "/cfg/s[1]/@port"
    assert path(root.children()[1]) == "/cfg/s[2]"


def test_paths_quote_what_is_not_a_name():
    root = parse(b'{"servers": [{"odd key": {"host": 1}}]}', "json")
    host = root.children()[0].children()[0].children()[0].children()[0]
    assert path(host) == '.servers[0]."odd key".host'
    assert path(root) == "."


def test_values_copy_as_their_formats_text():
    root = parse(b'{"a": {"b": [1, 2]}}', "json")
    assert root.children()[0].value().replace(" ", "").replace("\n", "") == '{"b":[1,2]}'
    xml = parse(b"<a><b x='1'/></a>", "xml")
    assert xml.children()[0].value() == '<b x="1" />'


@pytest.mark.parametrize("data, kind, line, column", [
    (b'{\n  "a": ,\n}', "json", 2, 8),
    (b"a: [1,\n", "yaml", 2, 1),
    (b"a = 1\nb = \n", "toml", 2, 5),
    (b"<a>\n<b></a>", "xml", 2, 6),
])
def test_parse_errors_say_where(data, kind, line, column):
    with pytest.raises(ParseFailed) as caught:
        parse(data, kind)
    assert (caught.value.line, caught.value.column) == (line, column)
    assert caught.value.offset == data.index(b"\n") + 1


def test_the_masks_and_the_extension_say_the_format():
    masks = "*.json;*.yml;*.toml;*.xml;*.svg;*.jsonl"
    assert [kind_by_name(n, masks) for n in ("a.JSON", "b.yml", "c.toml", "d.svg", "e.jsonl", "f.txt")] == [
        "json", "yaml", "toml", "xml", "jsonl", None]


def test_find_looks_in_keys_and_values_both_ways():
    root = parse(b'{"Host": "a", "list": ["myhost", {"host": 2}]}', "json")
    first = find(root, None, "host")
    assert path(first) == ".Host"
    second = find(root, first, "host")
    assert path(second) == ".list[0]"
    assert path(find(root, second, "host")) == ".list[1].host"
    assert path(find(root, None, "Host", case=True)) == ".Host"
    assert find(root, find(root, None, "Host", case=True), "Host", case=True) is None
    assert path(find(root, None, "host", backward=True)) == ".list[1].host"


# -- the window ----------------------------------------------------------------------


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "a.json").write_text('{"servers": [{"host": "alpha", "port": 22}], "debug": false}\n')
    return tmp_path


def screen_text(app) -> str:
    buffer = ScreenBuffer(80, 24)
    app.shell.layout(80, 24)
    settle()
    app.shell.render_tree(buffer)
    return "\n".join("".join(buffer.get(x, y)[0] or " " for x in range(80)) for y in range(24))


def active(app):
    return app.shell.desktop.active_window


def test_shift_f4_shows_the_tree_and_back(data_dir):
    from navigator.widgets.viewer.file_window import FileWindow
    from navigator.widgets.viewer.struct_window import StructWindow

    app = Navigator(data_dir, data_dir, terminal=FakeTerminal(80, 24))
    copied = []
    app.copy_to_clipboard = copied.append
    seen = {}
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE,
        lambda a: seen.update(mark=screen_text(a)),
        KeyEvent("shift+f4"),
        Until(lambda a: isinstance(active(a), StructWindow)),
        lambda a: seen.update(tree=screen_text(a)),
        KeyEvent("down"), KeyEvent("right"), KeyEvent("right"),
        KeyEvent("ctrl+insert"),
        lambda a: seen.update(path=screen_text(a)),
        KeyEvent("shift+f4"),
        Until(lambda a: isinstance(active(a), FileWindow)),
    ])
    assert "{Tree}" in seen["mark"]
    tree = seen["tree"]
    assert "servers [1]" in tree and 'debug: false' in tree
    assert copied == [".servers[0].host"]
    assert '.servers[0].host' in seen["path"] and 'host: "alpha"' in seen["path"]


def test_a_file_that_is_not_what_it_says_stays_text(data_dir):
    from navigator.widgets.viewer.file_window import FileWindow

    (data_dir / "a.json").write_text('{"a":\n  oops}\n')
    app = Navigator(data_dir, data_dir, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE, KeyEvent("shift+f4"),
        Until(lambda a: a.modal is not None),
        lambda a: seen.update(prompt=screen_text(a), window=active(a)),
    ])
    assert isinstance(seen["window"], FileWindow)
    assert "Line 2, column 3" in seen["prompt"]


# -- HTML, through View > Data tree ------------------------------------------------------


def tags(node, depth=0):
    """The tree as ``depth tag`` and ``depth #text`` lines, attributes left out."""
    lines = []
    for child in node.children():
        if child.kind == "element":
            lines.append(f"{depth} {child.key}")
            lines.extend(tags(child, depth + 1))
        elif child.kind == "text":
            lines.append(f"{depth} '{child.text}'")
    return lines


def test_html_is_built_as_a_browser_forgives_it():
    root = parse(b"<!doctype html><html><body><ul><li>one<li>two <b>bold</b> tail</ul>"
                 b"<p>a<p>b<br>c<table><tr><td>1<td>2<tr><td>3</table></body></html>", "html")
    assert root.key == "html"
    assert tags(root) == [
        "0 body",
        "1 ul", "2 li", "3 'one'", "2 li", "3 'two'", "3 b", "4 'bold'", "3 'tail'",
        "1 p", "2 'a'",
        "1 p", "2 'b'", "2 br", "2 'c'",
        "1 table", "2 tr", "3 td", "4 '1'", "3 td", "4 '2'", "2 tr", "3 td", "4 '3'",
    ]


def test_html_attributes_entities_and_stray_end_tags():
    root = parse(b'<div id="x" hidden>a &amp; b</span></div>', "html")
    assert [(c.key, c.kind, c.text) for c in root.children()] == [
        ("id", "attribute", "x"), ("hidden", "attribute", ""), ("#text", "text", "a & b")]
    assert path(root.children()[0]) == "/div/@id"


def test_what_data_tree_reads_a_file_as():
    from navigator.lib.viewer.structured import kind_for

    assert kind_for("page.html") == "html" and kind_for("page.HTM") == "html"
    assert kind_for("notes", b"  {\"a\": 1}") == "json"
    assert kind_for("notes", b"<?xml version='1.0'?>") == "xml"
    assert kind_for("notes", b"<!DOCTYPE html>") == "html"
    assert kind_for("notes", b"key: value") == "yaml"


def test_the_view_menu_opens_an_html_page_as_a_tree(data_dir):
    from navigator.widgets.viewer.commands import ViewAsTree
    from navigator.widgets.viewer.file_window import FileWindow
    from navigator.widgets.viewer.struct_window import StructWindow

    (data_dir / "a.json").unlink()
    (data_dir / "page.html").write_text("<html><body><h1>Title</h1><p>text</body></html>")
    app = Navigator(data_dir, data_dir, terminal=FakeTerminal(80, 24))
    seen = {}

    def menu(a):
        window = active(a)
        assert isinstance(window, FileWindow)
        seen["enabled"] = a.command_enabled(ViewAsTree(), a.focused)
        a.spawn(window.viewer.emit(ViewAsTree()))

    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE, menu,
        Until(lambda a: isinstance(active(a), StructWindow)),
        lambda a: seen.update(screen=screen_text(a), kind=active(a).kind),
    ])
    assert seen["enabled"] and seen["kind"] == "html"
    assert "html <1>" in seen["screen"] and "body <2>" in seen["screen"]
