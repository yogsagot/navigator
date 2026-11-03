"""The SSH connection manager (``navigator/widgets/drives/ssh_link_dialog``):
Utilities > SSH link (SFTP) and Remote shell open it.  It opens on a one-off
connection; choosing a kept one makes the lines that connection, kept by Save
once changed (leaving it asks); New makes one at once under a placeholder
name; Delete takes one away; Connect answers where to go."""

from __future__ import annotations

from pathlib import PurePosixPath

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.lib.drives import profiles
from navigator.lib.drives.location import Location, Site
from navigator.widgets.drives.connect_dialog import ConnectRequest
from navigator.widgets.drives.ssh_link_dialog import SshLinkDialog, sftp_entries


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
    return isinstance(a.modal, SshLinkDialog)


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
                   KeyEvent(answer, alt=answer != "escape"), Until(is_manager), Until(lambda a: not a.busy),
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
    dialog = SshLinkDialog(sftp_entries())
    assert answer_of(desk, dialog, [lambda a: dialog._choose(0), KeyEvent("enter")]) == ConnectRequest(
        "sftp", "web.example", "deploy", 2222, "/srv")


def test_connect_answers_the_one_off_lines(desk):
    dialog = SshLinkDialog(sftp_entries())
    actions = [lambda a: setattr(dialog.host, "value", "eve@far.example"), KeyEvent("enter")]
    assert answer_of(desk, dialog, actions) == ConnectRequest("sftp", "far.example", "eve", 0, "")


def test_connect_with_changes_asks_then_answers_what_is_shown(desk):
    dialog = SshLinkDialog(sftp_entries())
    actions = [lambda a: dialog._choose(0), lambda a: setattr(dialog.directory, "value", "/tmp"),
               KeyEvent("enter"), Until(modal_is("Dialog")), KeyEvent("n", alt=True)]
    assert answer_of(desk, dialog, actions) == ConnectRequest("sftp", "web.example", "deploy", 2222, "/srv")


def test_cancel_answers_nothing(desk):
    dialog = SshLinkDialog(sftp_entries())
    assert answer_of(desk, dialog, [KeyEvent("escape")]) is None


def test_missing_paramiko_stops_connect_for_a_panel_but_not_a_shell(desk):
    panel = SshLinkDialog(sftp_entries(), missing="No module named 'paramiko'")
    panel._fill(0)
    assert panel.accept() is None and panel.missing.text == "No module named 'paramiko'"
    shell = SshLinkDialog(sftp_entries(), mode="shell", missing="No module named 'paramiko'")
    shell._fill(0)
    assert shell.accept() is not None and shell.title == "Remote shell"


def test_select_chooses_the_kept_link_with_the_panel_s_directory_unchanged(desk):
    dialog = SshLinkDialog(sftp_entries(), mode="shell",
                           select=Location(Site("sftp", "", "box.lan"), PurePosixPath("/var/log")))
    assert dialog.links.cursor == 1 and dialog.chosen == 1
    assert lines(dialog) == ("box.lan", "", "", "/var/log", "box")
    # The panel's directory is no change to the connection: Connect asks nothing.
    assert not dialog.changed and dialog.save.disabled


def test_select_with_no_kept_link_fills_the_one_off_lines(desk):
    dialog = SshLinkDialog(sftp_entries(), mode="shell",
                           select=Location(Site("sftp", "eve", "far.example", 2022), PurePosixPath("/tmp")))
    assert dialog.chosen is None and dialog.save.disabled
    assert lines(dialog) == ("far.example", "eve", "2022", "/tmp", "")


def test_every_line_has_a_history_kept_on_connect(desk):
    from navml.history import HISTORY

    dialog = SshLinkDialog(sftp_entries())
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
    dialog = SshLinkDialog(sftp_entries())
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


def test_a_double_click_on_a_saved_connection_connects(desk):
    dialog = SshLinkDialog(sftp_entries())
    answer = answer_of(desk, dialog, [press_on_row(dialog, 1), press_on_row(dialog, 1)])
    assert answer == ConnectRequest("sftp", "box.lan", "", 0, "")


def test_a_double_click_away_from_a_changed_connection_only_asks(desk):
    dialog = SshLinkDialog(sftp_entries())
    seen = {}
    actions = [lambda a: dialog._choose(0), lambda a: setattr(dialog.port, "value", "22"),
               press_on_row(dialog, 1), press_on_row(dialog, 1), Until(modal_is("Dialog")),
               lambda a: seen.update(asked=a.modal.prompt), KeyEvent("escape"), Until(lambda a: a.modal is dialog),
               lambda a: seen.update(chosen=dialog.chosen, port=dialog.port.value), KeyEvent("escape"),
               Until(modal_is("Dialog")), KeyEvent("n", alt=True)]
    assert answer_of(desk, dialog, actions) is None
    assert seen == {"asked": 'Save changes to "web"?', "chosen": 0, "port": "22"}
