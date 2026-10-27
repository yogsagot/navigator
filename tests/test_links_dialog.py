"""Utilities > Saved links (``navigator/widgets/drives/links_dialog``): the
connection profiles edited in one box -- deleted, moved, edited, added --
written back on OK in one transaction (``profiles.store``), left alone on
Cancel, and one connected to."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.lib.drives import profiles
from navigator.lib.drives.profiles import Entry


@pytest.fixture
def saved():
    profiles.save("web", "sftp", "web.example", "deploy", 2222, "/srv")
    profiles.save("nas", "smb", "nas", "alice", 0, "/public")
    profiles.save("mirror", "ftp", "ftp.example")


@pytest.fixture
def desk(saved, tmp_path, monkeypatch):
    from navigator.__main__ import Navigator

    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    return Navigator(tmp_path, tmp_path, terminal=FakeTerminal(100, 30))


def names():
    return [row.name for row in profiles.profiles()]


def modal_is(name):
    return lambda a: type(a.modal).__name__ == name


def open_links(app):
    from navigator.widgets.shell.commands import EditLinks

    app.spawn(app.run_command(EditLinks))


def test_store_renames_deletes_and_reorders_in_one_go(saved):
    entries = profiles.entries()
    assert [entry.name for entry in entries] == ["web", "nas", "mirror"]
    entries[0].name = "www"
    profiles.store([entries[2], entries[0], Entry("new", "sftp", "h")])
    assert names() == ["mirror", "www", "new"]
    www = profiles.find("www")
    assert (www.host, www.user, www.port, www.path) == ("web.example", "deploy", 2222, "/srv")
    assert profiles.find("nas") is None


def test_the_box_lists_each_link_with_its_protocol(saved):
    from navigator.widgets.drives.links_dialog import LinksDialog

    dialog = LinksDialog(profiles.entries())
    rows = dialog.links.items
    assert rows[0].startswith("web ") and rows[0].endswith("SFTP deploy@web.example:2222")
    assert rows[1].endswith("SMB alice@nas") and rows[2].endswith("FTP ftp.example")


def test_delete_move_and_edit_are_kept_on_ok(desk):
    def answer_edit(a):
        dialog = a.modal
        dialog.host.value = "files.example"
        dialog.label.value = "files"

    run_app(desk, [
        open_links, Until(modal_is("LinksDialog")),
        KeyEvent("delete"), Until(modal_is("Dialog")), KeyEvent("enter"),  # Yes: web goes
        Until(modal_is("LinksDialog")),
        KeyEvent("down", ctrl=True),  # nas below mirror
        lambda a: setattr(a.modal.links, "cursor", 1),
        KeyEvent("f2"), Until(modal_is("ConnectDialog")), answer_edit, KeyEvent("enter"),
        Until(modal_is("LinksDialog")),
        lambda a: a.modal.close(a.modal.accept()),
        Until(lambda a: names() == ["mirror", "files"], timeout=3),
    ])
    files = profiles.find("files")
    assert (files.scheme, files.host, files.user, files.path) == ("smb", "files.example", "alice", "/public")


def test_cancel_changes_nothing(desk):
    run_app(desk, [
        open_links, Until(modal_is("LinksDialog")),
        KeyEvent("down", ctrl=True), KeyEvent("escape"), Until(lambda a: a.modal is None),
    ])
    assert names() == ["web", "nas", "mirror"]


def test_add_asks_the_protocol_then_its_box(desk):
    def answer_add(a):
        a.modal.host.value = "box.example"
        a.modal.label.value = "box"

    run_app(desk, [
        open_links, Until(modal_is("LinksDialog")),
        KeyEvent("insert"), Until(modal_is("PopupMenu")), KeyEvent("down"), KeyEvent("enter"),  # FTP
        Until(modal_is("ConnectDialog")), answer_add, KeyEvent("enter"),
        Until(modal_is("LinksDialog")),
        lambda a: a.modal.close(a.modal.accept()),
        Until(lambda a: "box" in names(), timeout=3),
    ])
    assert names() == ["web", "box", "nas", "mirror"]
    assert profiles.find("box").scheme == "ftp"


def test_add_takes_a_gvfs_or_kio_link_by_its_uri(desk, monkeypatch):
    from navigator.lib.system import gio
    from navigator.settings import SETTINGS

    SETTINGS.system.desktop_vfs = "gio"
    monkeypatch.setattr(gio, "program", lambda which=None: "/usr/bin/gio")
    seen = {}

    def type_uri(a):
        seen["uri_title"] = a.modal.title
        a.modal.line.value = "dav://bob@box.example/remote.php/webdav"

    def name_it(a):
        seen.update(title=a.modal.title, host=a.modal.host.value, user=a.modal.user.value,
                    path=a.modal.directory.value)
        a.modal.label.value = "cloud"

    run_app(desk, [
        open_links, Until(modal_is("LinksDialog")),
        KeyEvent("insert"), Until(modal_is("PopupMenu")), KeyEvent("end"), KeyEvent("enter"),
        Until(modal_is("EditLineDialog")), type_uri, KeyEvent("enter"),
        Until(modal_is("ConnectDialog")), name_it, KeyEvent("enter"),
        Until(modal_is("LinksDialog")),
        lambda a: a.modal.close(a.modal.accept()),
        Until(lambda a: "cloud" in names(), timeout=3),
    ])
    assert seen == {"uri_title": "GVfs/KIO link", "title": "Edit GVfs/KIO link (WebDAV)", "host": "box.example",
                    "user": "bob", "path": "/remote.php/webdav"}
    cloud = profiles.find("cloud")
    assert (cloud.scheme, cloud.host, cloud.user, cloud.path) == ("dav", "box.example", "bob", "/remote.php/webdav")


def test_connect_sends_the_active_panel_to_the_link(desk, monkeypatch):
    went = []

    async def go_remote(self, panel, target):
        went.append((panel, target))
        return True

    monkeypatch.setattr("navigator.widgets.shell.shell.Shell.go_remote", go_remote)
    run_app(desk, [
        open_links, Until(modal_is("LinksDialog")),
        lambda a: setattr(a.modal.links, "cursor", 1), KeyEvent("enter"),
        Until(lambda a: went, timeout=3),
    ])
    panel, target = went[0]
    assert panel is desk.manager.active_panel
    assert target == profiles.location_of(profiles.find("nas"))


def test_utilities_and_the_link_list_open_it(desk):
    from navigator.widgets.manager.manager.manager import EDIT_LINKS, link_section
    from navml.widgets.menu.sub_menu import SubMenu

    found = link_section(SubMenu())
    assert EDIT_LINKS in found.values()
    seen = {}
    run_app(desk, [lambda a: seen.update(on=a.shell.enables(__import__(
        "navigator.widgets.shell.commands", fromlist=["EditLinks"]).EditLinks()))])
    assert seen["on"] is not False
