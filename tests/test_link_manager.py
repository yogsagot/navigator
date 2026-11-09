"""The link managers (``navigator/widgets/drives/link_manager``), SSH's first:
Utilities > SSH link (SFTP) and Remote shell open it.  It opens on a one-off
connection; choosing a kept one makes the lines that connection, kept by Save
once changed (leaving it asks); New makes one at once under a placeholder
name; Delete takes one away; Connect answers where to go."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.lib.drives import profiles
from navigator.widgets.drives.connect_dialog import ConnectRequest
from navigator.widgets.drives.link_manager import LinkManagerDialog, sftp_entries


@pytest.fixture
def saved():
    profiles.save("web", "sftp", "web.example", "deploy", 2222, "/srv")
    profiles.save("nas", "smb", "nas", "alice", 0, "/public")
    profiles.save("box", "sftp", "box.lan")


@pytest.fixture
def desk(saved, tmp_path, monkeypatch):
    from navigator.__main__ import Navigator

    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    return Navigator(tmp_path, tmp_path, terminal=FakeTerminal(100, 30))


def names():
    return [row.name for row in profiles.profiles()]


def is_manager(a):
    return isinstance(a.modal, LinkManagerDialog)


def modal_is(name):
    return lambda a: type(a.modal).__name__ == name


def open_manager(a):
    from navigator.widgets.shell.commands import NavyLink

    a.spawn(a.run_command(NavyLink))


def lines(dialog):
    return (dialog.host.value, dialog.user.value, dialog.port.value, dialog.directory.value, dialog.label.value)


def state(a):
    d = a.modal
    focus = next((name for name in ("label", "host", "links") if getattr(d, name)._holds(a.focused)), None)
    return dict(lines=lines(d), items=list(d.links.items), chosen=d.chosen, save=d.save.disabled,
                delete=d.delete.disabled, said=d.missing.text, focus=focus)


def test_it_opens_on_a_one_off_connection(desk):
    seen = {}
    run_app(desk, [KeyEvent("f11", alt=True), Until(is_manager), lambda a: seen.update(state(a), title=a.modal.title),
                   KeyEvent("escape")])
    assert seen["title"] == "SSH link (SFTP)" and seen["items"] == ["web", "box"]
    assert seen["lines"] == ("", "", "", "", "") and seen["chosen"] is None
    assert seen["save"] and seen["delete"] and seen["focus"] == "label"
    assert seen["said"] == "Not saved — New keeps it"


def test_the_cursor_a_click_or_space_chooses_a_connection(desk):
    from navkit.events import MouseClickEvent

    seen = {}

    def click_first(a):
        links = a.modal.links
        ox, oy = links.offset()
        a.post_event(MouseClickEvent(x=ox + links.x + 3, y=oy + links.y + 1, button="left", action="press"))

    run_app(desk, [open_manager, Until(is_manager), click_first, Until(lambda a: a.modal.chosen == 0),
                   lambda a: seen.update(first=state(a)), lambda a: a.modal.links.focus(), KeyEvent("down"),
                   lambda a: seen.update(second=state(a)), KeyEvent("escape")])
    assert seen["first"]["lines"] == ("web.example", "deploy", "2222", "/srv", "web")
    assert seen["first"]["save"] and not seen["first"]["delete"] and seen["first"]["said"] == ""
    assert seen["second"]["lines"] == ("box.lan", "", "", "", "box")


def test_new_makes_an_empty_connection_under_a_placeholder_ready_to_rename(desk):
    seen = {}

    def look(key):
        def take(a):
            d = a.modal
            seen[key] = dict(state(a), selected=d.label.entry.selected_text)
        return take

    run_app(desk, [open_manager, Until(is_manager), KeyEvent("insert"),
                   Until(lambda a: is_manager(a) and "New connection" in a.modal.links.items), look("one"),
                   lambda a: a.spawn(a.modal.new_link()),
                   Until(lambda a: is_manager(a) and "New connection 2" in a.modal.links.items), look("two"),
                   KeyEvent("escape")])
    assert seen["one"]["chosen"] == 2 and seen["one"]["lines"] == ("", "", "", "", "New connection")
    # Name has the keyboard with the placeholder selected: typing replaces it.
    assert seen["one"]["focus"] == "label" and seen["one"]["selected"] == "New connection" and seen["one"]["save"]
    assert seen["two"]["chosen"] == 3
    assert names() == ["web", "nas", "box", "New connection", "New connection 2"]


def test_new_keeps_the_one_off_lines_typed(desk):
    def type_new(a):
        a.modal.host.value = "alice@new.example:2200"
        a.modal.directory.value = "/home/alice"

    run_app(desk, [open_manager, Until(is_manager), type_new, lambda a: a.spawn(a.modal.new_link()),
                   Until(lambda a: is_manager(a) and "new.example" in a.modal.links.items), KeyEvent("escape")])
    row = profiles.find("new.example")
    assert (row.host, row.user, row.port, row.path) == ("new.example", "alice", 2200, "/home/alice")


def test_an_edit_marks_the_row_and_save_keeps_it_renamed_in_place(desk):
    seen = {}

    def edit(a):
        a.modal.label.value = "website"
        a.modal.port.value = "22"

    # A key after the edit, as typing is: effects flush between batches.
    run_app(desk, [open_manager, Until(is_manager), lambda a: a.modal._choose(0), edit,
                   lambda a: a.modal.label.entry.focus(), KeyEvent("end"),
                   Until(lambda a: a.modal.links.items[0] == "web *"),
                   lambda a: seen.update(edited=state(a)), KeyEvent("f2"),
                   Until(lambda a: is_manager(a) and "website" in a.modal.links.items),
                   lambda a: seen.update(saved=state(a)), KeyEvent("escape")])
    assert seen["edited"]["items"][0] == "web *" and not seen["edited"]["save"]
    assert seen["edited"]["said"] == "Changed — Save keeps it"
    assert seen["saved"]["items"] == ["website", "box"] and seen["saved"]["save"]
    assert seen["saved"]["said"] == '"website" saved'
    assert names() == ["website", "nas", "box"] and profiles.find("website").port == 22


def test_save_refuses_another_connection_s_name(desk):
    seen = {}
    run_app(desk, [open_manager, Until(is_manager), lambda a: a.modal._choose(1),
                   lambda a: setattr(a.modal.label, "value", "web"), lambda a: a.spawn(a.modal.save_link()),
                   lambda a: seen.update(state(a)), KeyEvent("escape"), Until(modal_is("Dialog")),
                   KeyEvent("n", alt=True), Until(lambda a: a.modal is None)])
    assert seen["said"] == 'Another connection is named "web"'
    assert names() == ["web", "nas", "box"]


@pytest.mark.parametrize("answer, saved_port, stays", [("y", 22, False), ("n", 2222, False), ("escape", 2222, True)])
def test_leaving_a_changed_connection_asks(desk, answer, saved_port, stays):
    seen = {}

    run_app(desk, [open_manager, Until(is_manager), lambda a: a.modal._choose(0),
                   lambda a: setattr(a.modal.port, "value", "22"), lambda a: a.modal.links.focus(),
                   KeyEvent("down"), Until(modal_is("Dialog")), lambda a: seen.update(prompt=a.modal.prompt),
                   KeyEvent(answer, alt=answer != "escape"),
                   # Yes saves on a thread and only then moves on (``_settle``,
                   # ``save_link``, ``_reread``): wait for the move, which an idle
                   # queue does not mean.  Cancel stays, so there is none to wait for.
                   Until(lambda a: is_manager(a) and (stays or a.modal.chosen == 1)), Until(lambda a: not a.busy),
                   lambda a: seen.update(state(a), cursor=a.modal.links.cursor), KeyEvent("escape"),
                   *([Until(modal_is("Dialog")), KeyEvent("n", alt=True)] if stays else [])])
    assert seen["prompt"] == 'Save changes to "web"?'
    assert profiles.find("web").port == saved_port
    if stays:
        assert seen["chosen"] == 0 and seen["cursor"] == 0 and seen["lines"][2] == "22"
    else:
        assert seen["chosen"] == 1 and seen["lines"][0] == "box.lan"


def test_esc_on_a_changed_connection_asks(desk):
    seen = {}
    run_app(desk, [open_manager, Until(is_manager), lambda a: a.modal._choose(0),
                   lambda a: setattr(a.modal.user, "value", "root"), KeyEvent("escape"),
                   Until(modal_is("Dialog")), lambda a: seen.update(prompt=a.modal.prompt), KeyEvent("y", alt=True),
                   Until(lambda a: a.modal is None)])
    assert seen["prompt"] == 'Save changes to "web"?' and profiles.find("web").user == "root"


def test_delete_asks_then_goes_back_to_a_one_off(desk):
    seen = {}
    run_app(desk, [open_manager, Until(is_manager), lambda a: a.modal._choose(0), KeyEvent("tab"),
                   lambda a: a.spawn(a.modal.delete_link()), Until(modal_is("Dialog")),
                   lambda a: seen.update(prompt=a.modal.prompt), KeyEvent("enter"),
                   Until(lambda a: is_manager(a) and a.modal.links.items == ["box"]),
                   lambda a: seen.update(state(a)), KeyEvent("escape")])
    assert seen["prompt"] == 'Delete the link "web"?'
    assert names() == ["nas", "box"]
    assert seen["lines"] == ("", "", "", "", "") and seen["chosen"] is None and seen["delete"]


def answer_of(app, dialog, actions):
    seen = {}

    async def show(a):
        seen["answer"] = await dialog.execute(a)

    run_app(app, [lambda a: a.spawn(show(a)), Until(lambda a: a.modal is dialog), *actions,
                  Until(lambda a: "answer" in seen)])
    return seen["answer"]


def test_connect_answers_the_chosen_connection(desk):
    dialog = LinkManagerDialog(sftp_entries())
    assert answer_of(desk, dialog, [lambda a: dialog._choose(0), KeyEvent("enter")]) == ConnectRequest(
        "sftp", "web.example", "deploy", 2222, "/srv")


def test_connect_answers_the_one_off_lines(desk):
    dialog = LinkManagerDialog(sftp_entries())
    actions = [lambda a: setattr(dialog.host, "value", "eve@far.example"), KeyEvent("enter")]
    assert answer_of(desk, dialog, actions) == ConnectRequest("sftp", "far.example", "eve", 0, "")


def test_connect_with_changes_asks_then_answers_what_is_shown(desk):
    dialog = LinkManagerDialog(sftp_entries())
    actions = [lambda a: dialog._choose(0), lambda a: setattr(dialog.directory, "value", "/tmp"),
               KeyEvent("enter"), Until(modal_is("Dialog")), KeyEvent("n", alt=True)]
    assert answer_of(desk, dialog, actions) == ConnectRequest("sftp", "web.example", "deploy", 2222, "/srv")


def test_cancel_answers_nothing(desk):
    dialog = LinkManagerDialog(sftp_entries())
    assert answer_of(desk, dialog, [KeyEvent("escape")]) is None


def test_missing_paramiko_stops_connect_for_a_panel_but_not_a_shell(desk):
    panel = LinkManagerDialog(sftp_entries(), missing="No module named 'paramiko'")
    panel._fill(0)
    assert panel.accept() is None and panel.missing.text == "No module named 'paramiko'"
    shell = LinkManagerDialog(sftp_entries(), mode="shell", missing="No module named 'paramiko'")
    shell._fill(0)
    assert shell.accept() is not None and shell.title == "Remote shell"


def test_every_line_has_a_history_kept_on_connect(desk):
    from navml.history import HISTORY

    dialog = LinkManagerDialog(sftp_entries())
    seen = {}

    def fill(a):
        dialog.label.value = "temp"
        dialog.host.value = "far.example"
        dialog.user.value = "eve"
        dialog.port.value = "2022"
        dialog.directory.value = "/tmp"
        seen.update(buttons={name: getattr(dialog, name).history.visible
                             for name in ("label", "host", "user", "port", "directory")})

    answer_of(desk, dialog, [fill, KeyEvent("enter")])
    assert all(seen["buttons"].values())
    assert [HISTORY.entries(f"ssh_{name}")[:1] for name in ("name", "host", "login", "port", "directory")] == [
        ["temp"], ["far.example"], ["eve"], ["2022"], ["/tmp"]]


def test_host_remembers_only_its_own_value(desk):
    from navml.history import HISTORY
    from navigator.lib.drives import recent

    recent.remember(recent.Recent("sftp", "old.example", "bob", 22, "/srv"))
    HISTORY.add("ssh_host", "typed.example")
    dialog = LinkManagerDialog(sftp_entries())
    seen = {}

    async def pick(a):
        seen["listed"] = HISTORY.entries("ssh_host")
        dialog.host.history.choose("typed.example")
        seen["lines"] = lines(dialog)

    answer_of(desk, dialog, [lambda a: a.spawn(pick(a)), Until(lambda a: "lines" in seen), KeyEvent("escape")])
    assert dialog.host.choices == []
    assert seen["listed"] == ["typed.example"]
    assert seen["lines"] == ("typed.example", "", "", "", "")


def press_on_row(dialog, row):
    from navkit.events import MouseClickEvent

    def press(a):
        ox, oy = dialog.links.offset()
        a.post_event(MouseClickEvent(x=ox + dialog.links.x + 3, y=oy + dialog.links.y + 1 + row,
                                     button="left", action="press"))
    return press


def double_press_on_row(dialog, row):
    """Both presses posted at once, so they are one batch apart: as two
    actions, ``run_app`` paints between them, and a slow runner outlasts
    ``DOUBLE_CLICK_TIMEOUT`` and sees two single clicks."""
    first, second = press_on_row(dialog, row), press_on_row(dialog, row)

    def press(a):
        first(a)
        second(a)
    return press


def test_a_double_click_on_a_saved_connection_connects(desk):
    dialog = LinkManagerDialog(sftp_entries())
    answer = answer_of(desk, dialog, [double_press_on_row(dialog, 1)])
    assert answer == ConnectRequest("sftp", "box.lan", "", 0, "")


def test_a_double_click_away_from_a_changed_connection_only_asks(desk):
    dialog = LinkManagerDialog(sftp_entries())
    seen = {}
    actions = [lambda a: dialog._choose(0), lambda a: setattr(dialog.port, "value", "22"),
               press_on_row(dialog, 1), press_on_row(dialog, 1), Until(modal_is("Dialog")),
               lambda a: seen.update(asked=a.modal.prompt), KeyEvent("escape"), Until(lambda a: a.modal is dialog),
               lambda a: seen.update(chosen=dialog.chosen, port=dialog.port.value), KeyEvent("escape"),
               Until(modal_is("Dialog")), KeyEvent("n", alt=True)]
    assert answer_of(desk, dialog, actions) is None
    assert seen == {"asked": 'Save changes to "web"?', "chosen": 0, "port": "22"}


# -- the other protocols -----------------------------------------------------------------------


@pytest.fixture
def every_protocol(saved):
    profiles.save("mirror", "ftp", "ftp.example")
    profiles.save("vault", "ftps", "secure.example", "eve", 990, "/pub")
    profiles.save("bucket", "s3+http", "minio.lan", "key", 9000, "/photos")
    profiles.save("phone", "mtp", "Pixel", "", 0, "/DCIM")


def test_each_manager_lists_its_own_protocol(every_protocol, monkeypatch):
    from navigator.widgets.drives.link_manager import entries_for

    monkeypatch.setattr("navigator.widgets.drives.link_manager.link_manager.schemes_of",
                        lambda family: ("mtp", "dav") if family == "gvfs" else
                        __import__("navigator.widgets.drives.link_manager.link_manager",
                                   fromlist=["FAMILIES"]).FAMILIES[family].schemes)
    assert [e.name for e in entries_for("sftp")] == ["web", "box"]
    assert [e.name for e in entries_for("ftp")] == ["mirror", "vault"]
    assert [e.name for e in entries_for("smb")] == ["nas"]
    assert [e.name for e in entries_for("s3")] == ["bucket"]
    assert [e.name for e in entries_for("gvfs")] == ["phone"]


def test_ftp_s_tls_box_is_its_scheme(every_protocol, desk):
    from navigator.widgets.drives.link_manager import entries_for

    dialog = LinkManagerDialog(entries_for("ftp"), family="ftp")
    assert dialog.title == "FTP link" and dialog.secure.visible and dialog.secure.value == 0
    dialog._fill(1)
    assert dialog.secure.value == 1 and lines(dialog) == ("secure.example", "eve", "990", "/pub", "vault")
    dialog.secure.value = 0
    assert dialog.changed
    dialog.secure.value = 1
    dialog.host.value = "other.example"
    assert dialog.accept() == ConnectRequest("ftps", "other.example", "eve", 990, "/pub")


def test_ftp_saves_the_scheme_its_box_says(every_protocol, desk):
    from navigator.widgets.drives.link_manager import entries_for

    dialog = LinkManagerDialog(entries_for("ftp"), family="ftp")
    run_app(desk, [lambda a: a.spawn(dialog.execute(a)), Until(lambda a: a.modal is dialog),
                   lambda a: dialog._fill(0), lambda a: setattr(dialog.secure, "value", 1),
                   lambda a: a.spawn(dialog.save_link()), Until(lambda a: "saved" in dialog.missing.text),
                   KeyEvent("escape")])
    assert profiles.find("mirror").scheme == "ftps"


def test_smb_s_share_is_the_directory_s_first_name(desk):
    dialog = LinkManagerDialog([], family="smb")
    assert dialog.title == "SMB link (Windows share)" and dialog.directory.label_text == "Sh~a~re/dir"
    assert not dialog.secure.visible
    dialog.host.value = "alice@nas"
    dialog.directory.value = "public/docs"
    assert dialog.accept() == ConnectRequest("smb", "nas", "alice", 0, "/public/docs")


def test_s3_starts_at_aws_with_tls_and_unticked_is_plain_http(desk):
    from navigator.lib.drives.s3 import AWS_HOST

    dialog = LinkManagerDialog([], family="s3")
    assert dialog.title == "S3 link (Amazon S3)"
    assert (dialog.host.label_text, dialog.user.label_text, dialog.directory.label_text) == (
        "End~p~oint", "Access ~k~ey", "~B~ucket/dir")
    assert dialog.host.value == AWS_HOST and dialog.secure.value == 1
    dialog.directory.value = "photos"
    assert dialog.accept() == ConnectRequest("s3", AWS_HOST, "", 0, "/photos")
    dialog.secure.value = 0
    assert dialog.accept().scheme == "s3+http"


@pytest.fixture
def gvfs_schemes(monkeypatch):
    monkeypatch.setattr("navigator.lib.system.desktop.link_schemes", lambda: {"mtp": "", "dav": "", "sftp": ""})


def test_gvfs_shows_name_and_uri_alone(every_protocol, gvfs_schemes, desk):
    from navigator.widgets.drives.link_manager import entries_for

    dialog = LinkManagerDialog(entries_for("gvfs"), family="gvfs")
    assert dialog.title == "GVfs/KIO link" and dialog.links.items == ["phone"]
    assert dialog.uri.visible and not any(line.visible for line in (dialog.host, dialog.user, dialog.port,
                                                                       dialog.directory))
    dialog._fill(0)
    assert dialog.uri.value == "mtp://Pixel/DCIM"
    dialog.uri.value = "dav://alice@files.lan/share"
    assert dialog.accept() == ConnectRequest("dav", "files.lan", "alice", 0, "/share")


def test_gvfs_new_keeps_the_uri_typed(gvfs_schemes, desk):
    dialog = LinkManagerDialog([], family="gvfs")
    run_app(desk, [lambda a: a.spawn(dialog.execute(a)), Until(lambda a: a.modal is dialog),
                   lambda a: setattr(dialog.uri, "value", "mtp://Pixel/DCIM"), lambda a: a.spawn(dialog.new_link()),
                   Until(lambda a: dialog.links.items == ["Pixel"]), KeyEvent("escape")])
    row = profiles.find("Pixel")
    assert (row.scheme, row.host, row.path) == ("mtp", "Pixel", "/DCIM")


def test_gvfs_refuses_what_it_does_not_reach(gvfs_schemes, desk):
    dialog = LinkManagerDialog([], family="gvfs")
    run_app(desk, [lambda a: a.spawn(dialog.execute(a)), Until(lambda a: a.modal is dialog),
                   lambda a: setattr(dialog.uri, "value", "sftp://host/"), lambda a: a.spawn(dialog.connect_to()),
                   lambda a: None, KeyEvent("escape")])
    assert dialog.result is None
    assert "sftp://host/ is no place" in dialog.missing.text and "mtp://, dav://" in dialog.missing.text



# -- ssh options -------------------------------------------------------------------------------


def test_ssh_options_are_ssh_s_alone_and_kept_with_the_connection(desk):
    dialog = LinkManagerDialog(sftp_entries())
    assert dialog.options.visible
    assert not LinkManagerDialog([], family="ftp").options.visible
    run_app(desk, [lambda a: a.spawn(dialog.execute(a)), Until(lambda a: a.modal is dialog),
                   lambda a: dialog._fill(0), lambda a: setattr(dialog.options, "value", "-A -J jump"),
                   lambda a: a.spawn(dialog.save_link()), Until(lambda a: "saved" in dialog.missing.text),
                   KeyEvent("escape")])
    assert profiles.find("web").options == "-A -J jump"
    assert dialog.accept().options == "-A -J jump"


def test_an_edit_elsewhere_keeps_a_connection_s_ssh_options(saved):
    profiles.save("web", "sftp", "web.example", "deploy", 2222, "/srv", "-A")
    # The Link box's F2 (``ConnectDialog``, no such line) replaces without them.
    profiles.replace("web", "web", "sftp", "web.example", "root", 22, "/srv")
    assert profiles.find("web").options == "-A"
    # Saved links writes every entry back, theirs carried over.
    entries = profiles.entries()
    profiles.store(entries)
    assert profiles.find("web").options == "-A"


# -- SSH's port forwards and Copy key -----------------------------------------------------------


def test_forwards_are_ssh_s_and_edited_in_their_own_box_then_kept_by_save(desk):
    from navigator.lib.drives.forwards import Forward
    from navigator.widgets.drives.forwards_dialog import ForwardDialog, ForwardsDialog

    assert not LinkManagerDialog([], family="ftp").forwards_button.visible
    assert not LinkManagerDialog([], family="ftp").copy_key.visible
    seen = {}

    def fill(a):
        d = a.modal
        d.port.value, d.host.value, d.host_port.value = "8080", "db", "5432"

    def dynamic(a):
        d = a.modal
        d.kind.value = d.kind.sel = 2
        d.port.value = "1080"

    run_app(desk, [open_manager, Until(is_manager), lambda a: a.modal._choose(0),
                   lambda a: seen.update(caption=a.modal.forwards_button.text),
                   lambda a: a.modal.spawn(a.modal.edit_forwards()), Until(modal_is("ForwardsDialog")),
                   KeyEvent("insert"), Until(modal_is("ForwardDialog")),
                   # OK with no port: refused, said, still up.
                   lambda a: a.spawn(a.modal.on_ok_click(None)),
                   lambda a: seen.update(refused=a.modal.problem.text, still=type(a.modal).__name__),
                   fill, lambda a: a.spawn(a.modal.on_ok_click(None)), Until(modal_is("ForwardsDialog")),
                   KeyEvent("insert"), Until(modal_is("ForwardDialog")), dynamic,
                   lambda a: seen.update(greyed=a.modal.host.disabled),
                   lambda a: a.spawn(a.modal.on_ok_click(None)), Until(modal_is("ForwardsDialog")),
                   lambda a: seen.update(rows=list(a.modal.forwards.items)),
                   lambda a: a.spawn(a.modal.on_ok_click(None)), Until(is_manager),
                   Until(lambda a: a.modal.links.items[0] == "web *"),
                   lambda a: seen.update(counted=a.modal.forwards_button.text, request=a.modal.accept()),
                   KeyEvent("f2"), Until(lambda a: "saved" in a.modal.missing.text), KeyEvent("escape")])
    assert seen["caption"] == "~F~orwards..."
    assert seen["refused"] == "Type the port to listen on" and seen["still"] == "ForwardDialog"
    assert seen["greyed"]
    assert seen["rows"] == ["L 127.0.0.1:8080 → db:5432", "D 127.0.0.1:1080 (SOCKS)"]
    assert seen["counted"] == "~F~orwards (2)..."
    assert seen["request"].forwards == "L 8080:db:5432\nD 1080"
    assert profiles.find("web").forwards == "L 8080:db:5432\nD 1080"
    assert profiles.forwards_for(profiles.site_of(profiles.find("web"))) == [
        Forward("L", 8080, "", "db", 5432), Forward("D", 1080)]
    assert ForwardDialog and ForwardsDialog


def test_connect_hands_a_saved_connection_s_forwards_to_the_panel_s_connection(desk, monkeypatch):
    from navigator.lib.drives.forwards import Forward

    profiles.save("web", "sftp", "web.example", "deploy", 2222, "/srv", forwards="L 8080:db:5432")
    asked = {}

    async def go_remote(self, panel, target, forwards=None):
        asked.update(target=target, forwards=forwards)
        return False

    monkeypatch.setattr("navigator.widgets.shell.shell.Shell.go_remote", go_remote)
    monkeypatch.setattr("navigator.lib.drives.sessions.available", lambda scheme: None)
    run_app(desk, [open_manager, Until(is_manager), lambda a: a.modal._choose(0), KeyEvent("enter"),
                   Until(lambda a: "forwards" in asked)])
    assert asked["forwards"] == [Forward("L", 8080, "", "db", 5432)]


@pytest.fixture
def keys_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr("navigator.lib.drives.remote_shell.copy_id_program", lambda: "/usr/bin/ssh-copy-id")
    ran = []
    monkeypatch.setattr("navigator.widgets.shell.shell.Shell.run_in_window",
                        lambda self, command, **kwargs: ran.append((command, kwargs)) or object())
    return home, ran


def test_copy_key_runs_ssh_copy_id_with_the_one_key_there(desk, keys_home):
    home, ran = keys_home
    (home / ".ssh" / "id_ed25519.pub").write_text("ssh-ed25519 AAAA me@here")
    run_app(desk, [open_manager, Until(is_manager), lambda a: a.modal._choose(0),
                   lambda a: a.modal.spawn(a.modal.copy_key_to_server()), Until(lambda a: ran)])
    command, kwargs = ran[0]
    assert command == f"ssh-copy-id -i {home}/.ssh/id_ed25519.pub -p 2222 deploy@web.example"
    assert kwargs["closes"] is False and kwargs["title"] == "ssh-copy-id deploy@web.example:2222"


def test_copy_key_with_no_key_offers_to_make_one(desk, keys_home):
    home, ran = keys_home
    run_app(desk, [open_manager, Until(is_manager), lambda a: setattr(a.modal.host, "value", "box.lan"),
                   lambda a: a.modal.spawn(a.modal.copy_key_to_server()), Until(modal_is("Dialog")),
                   KeyEvent("enter"), Until(lambda a: ran)])
    assert ran[0][0] == (f"ssh-keygen -t ed25519 -f {home}/.ssh/id_ed25519 && "
                         f"ssh-copy-id -i {home}/.ssh/id_ed25519.pub box.lan")


def test_copy_key_needs_a_host_and_ssh_copy_id(desk, keys_home, monkeypatch):
    _, ran = keys_home
    seen = {}
    run_app(desk, [open_manager, Until(is_manager), lambda a: a.modal.spawn(a.modal.copy_key_to_server()),
                   lambda a: seen.update(no_host=a.modal.missing.text),
                   lambda a: setattr(a.modal.host, "value", "box.lan"),
                   lambda a: monkeypatch.setattr("navigator.lib.drives.remote_shell.copy_id_program", lambda: None),
                   lambda a: a.modal.spawn(a.modal.copy_key_to_server()),
                   lambda a: seen.update(no_tool=a.modal.missing.text), KeyEvent("escape")])
    assert seen["no_host"] == "Type a host to connect to"
    assert "ssh-copy-id is not installed" in seen["no_tool"] and not ran
