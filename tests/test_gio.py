"""The desktop's GIO through its ``gio`` command (navigator/lib/system/gio.py),
and what uses it: Disk > Volumes' Mount/Unmount/Eject, Enter and *Open with*
in the desktop's applications, GVfs drives, and ``gio trash``.

Nothing here runs the real ``gio``: a fake one -- a Python script on a
temporary ``PATH`` -- answers as it does, prompts included, and records what
it was asked.
"""

from __future__ import annotations

import errno
import json
import os
import stat
import sys
from pathlib import Path, PurePosixPath

import pytest

from navkit.events import KeyEvent

from conftest import Until, run_app

from navigator.lib.drives import Location, Site
from navigator.lib.drives.sessions import SESSIONS, Answers, NeedPassword
from navigator.lib.system import gio, volumes
from navigator.lib.system.volumes import Volume
from navigator.settings import SETTINGS


MOUNT_LIST = """\
Drive(0): TOSHIBA MQ04UBB400
  Type: GProxyDrive (GProxyVolumeMonitorUDisks2)
  ids:
   unix-device: '/dev/sdb'
  is_removable=1
  can_eject=1
  Volume(0): external
    Type: GProxyVolume (GProxyVolumeMonitorUDisks2)
    ids:
     class: 'device'
     unix-device: '/dev/sdb2'
     uuid: '590D4FA25E520CA6'
     label: 'external'
    uuid=590D4FA25E520CA6
    themed icons:  [drive-harddisk-usb]  [drive-harddisk]
    can_mount=1
    can_eject=0
    should_automount=1
  Volume(1): backup
    Type: GProxyVolume (GProxyVolumeMonitorUDisks2)
    ids:
     unix-device: '/dev/sdb1'
    can_mount=1
    can_eject=1
    Mount(0): backup -> file:///media/me/backup
      Type: GProxyMount (GProxyVolumeMonitorUDisks2)
      default_location=file:///media/me/backup
      can_unmount=1
      can_eject=1
      is_shadowed=0
Volume(0): Pixel 7
  Type: GProxyVolume (GProxyVolumeMonitorMTP)
  ids:
  activation_root=mtp://Google_Pixel_7_2B14/
  can_mount=1
  can_eject=0
Mount(0): share on server -> smb://server/share/
  Type: GDaemonMount
  default_location=smb://server/share/
  can_unmount=1
  can_eject=0
"""


@pytest.fixture
def use_gio():
    """``[system] use_gio`` on, as it is by default -- the suite's ``conftest`` turns it off."""
    SETTINGS.system.use_gio = True


# -- the fake gio -----------------------------------------------------------------

FAKE = r'''
import json, os, sys
state_path = os.environ["FAKE_GIO_STATE"]
state = json.load(open(state_path)) if os.path.exists(state_path) else {"mounted": [], "calls": []}
args = sys.argv[1:]
state["calls"].append(args)
def save():
    json.dump(state, open(state_path, "w"))
def uri_root(uri):
    scheme, _, rest = uri.partition("://")
    host = rest.partition("/")[0].rpartition("@")[2]
    return scheme + "://" + host
bridge = os.environ["FAKE_GIO_BRIDGE"]
code = 0
if args[:1] == ["info"]:
    where = args[-1]
    root = uri_root(where)
    if root in state["mounted"]:
        scheme, host = root.split("://")
        rest = where.split("://", 1)[1].partition("/")[2].strip("/")
        local = os.path.join(bridge, f"{scheme}:host={host}", rest).rstrip("/")
        print(f"uri: {where}")
        print(f"local path: {local}")
        print("attributes:")
        print("  standard::type: 2")
    elif where.startswith("/"):
        print(f"uri: file://{where}")
        print(f"local path: {where}")
    else:
        sys.stderr.write(f"gio: {where}: The specified location is not mounted\n")
        code = 2
elif args[:2] == ["mount", "--"]:
    uri = args[2]
    password = os.environ.get("FAKE_GIO_PASSWORD")
    if password is not None:
        # As GVfs does: asked again after a wrong password, until it is
        # right or the asking stops.
        sys.stdout.write("Authentication Required\nEnter user and password for share on server:\n")
        while True:
            sys.stdout.write("User [me]: "); sys.stdout.flush()
            user = sys.stdin.readline()
            sys.stdout.write("Domain [WORKGROUP]: "); sys.stdout.flush()
            sys.stdin.readline()
            sys.stdout.write("Password: "); sys.stdout.flush()
            given = sys.stdin.readline()
            if not given:
                sys.stderr.write(f"gio: {uri}: Password dialog cancelled\n")
                code = 2
                break
            state.setdefault("users", []).append(user.strip())
            if given.rstrip("\n") == password:
                break
    if code == 0:
        root = uri_root(uri)
        state["mounted"].append(root)
        scheme, host = root.split("://")
        os.makedirs(os.path.join(bridge, f"{scheme}:host={host}"), exist_ok=True)
elif args[:2] == ["mount", "-u"]:
    root = uri_root(args[-1])
    if root in state["mounted"]:
        state["mounted"].remove(root)
elif args[:1] == ["trash"]:
    if os.environ.get("FAKE_GIO_TRASH_FAILS"):
        sys.stderr.write(f"gio: file://{args[-1]}: Trashing not supported\n")
        code = 1
    else:
        os.remove(args[-1])
save()
sys.exit(code)
'''


@pytest.fixture
def fake_gio(tmp_path, monkeypatch, use_gio):
    """A ``gio`` on ``PATH`` that keeps its mounts in a JSON file; its FUSE
    bridge is a directory under *tmp_path*.  Answers the state's reader."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "gio"
    script.write_text(f"#!{sys.executable}\n{FAKE}")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    bridge = tmp_path / "run" / "gvfs"
    bridge.mkdir(parents=True)
    state = tmp_path / "gio.json"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_GIO_STATE", str(state))
    monkeypatch.setenv("FAKE_GIO_BRIDGE", str(bridge))

    def read() -> dict:
        return json.loads(state.read_text()) if state.exists() else {"mounted": [], "calls": []}

    read.bridge = bridge  # type: ignore[attr-defined]
    return read


# -- gio.py -------------------------------------------------------------------------


def test_program_is_none_without_gio_or_with_use_gio_off(use_gio):
    assert gio.program(lambda name: None) is None
    assert gio.program(lambda name: f"/usr/bin/{name}") == "/usr/bin/gio"
    SETTINGS.system.use_gio = False
    assert gio.program(lambda name: f"/usr/bin/{name}") is None


def test_the_mount_list_gives_volumes_and_mounts_without_one_but_no_drives():
    found = {each.name: each for each in gio.parse_mount_list(MOUNT_LIST)}
    assert sorted(found) == ["Pixel 7", "backup", "external", "share on server"]
    external = found["external"]
    assert (external.device, external.uuid, external.mounted, external.can_mount) == (
        "/dev/sdb2", "590D4FA25E520CA6", False, True)
    backup = found["backup"]
    assert backup.uri == "file:///media/me/backup" and backup.local == "/media/me/backup"
    assert backup.can_unmount and backup.can_eject and backup.mounted
    phone = found["Pixel 7"]
    assert phone.activation_root == "mtp://Google_Pixel_7_2B14/" and phone.ident == "" and not phone.mounted
    share = found["share on server"]
    assert share.uri == "smb://server/share/" and share.can_unmount and share.local == ""


def test_mime_lists_the_default_first_and_each_application_once(tmp_path):
    text = ("Default application for “text/plain”: geany.desktop\n"
            "Registered applications:\n\tgeany.desktop\n\torg.gnome.TextEditor.desktop\n"
            "Recommended applications:\n\tgeany.desktop\n")
    assert gio.parse_mime(text) == ["geany.desktop", "org.gnome.TextEditor.desktop"]
    apps = tmp_path / "applications"
    (apps / "kde4").mkdir(parents=True)
    (apps / "kde4" / "kate.desktop").write_text("[Desktop Entry]\nName=Kate\n[Desktop Action x]\nName=No\n")
    assert gio.desktop_file("kde4-kate.desktop", [apps]) == apps / "kde4" / "kate.desktop"
    assert gio.desktop_name(apps / "kde4" / "kate.desktop") == "Kate"


def test_the_gvfs_schemes_are_those_whose_backend_is_installed(tmp_path):
    (tmp_path / "mtp.mount").write_text("[Mount]\nType=mtp\n")
    (tmp_path / "dav.mount").write_text("[Mount]\nType=dav;davs\n")
    assert gio.gvfs_schemes([tmp_path]) == ("mtp", "dav", "davs")


def test_a_failure_is_gios_reason_without_the_uri(fake_gio):
    with pytest.raises(OSError) as raised:
        gio.run("info", "-a", "standard::type", "--", "mtp://nothing/")
    assert raised.value.strerror == "The specified location is not mounted"


def test_mount_uri_answers_the_prompts_and_stops_at_one_with_no_answer(fake_gio, monkeypatch):
    monkeypatch.setenv("FAKE_GIO_PASSWORD", "secret")
    with pytest.raises(gio.Prompted) as raised:
        gio.mount_uri("dav://box/", {"User": "bob", "Domain": ""})
    assert raised.value.what == "Password" and "Authentication Required" in raised.value.message
    assert not raised.value.again
    with pytest.raises(gio.Prompted) as raised:
        gio.mount_uri("dav://box/", {"User": "bob", "Domain": "", "Password": "wrong"})
    assert raised.value.what == "Password" and raised.value.again
    gio.mount_uri("dav://box/", {"User": "bob", "Domain": "", "Password": "secret"})
    assert fake_gio()["mounted"] == ["dav://box"] and fake_gio()["users"][-1] == "bob"


# -- Location: a GVfs host keeps its case -----------------------------------------------


def test_a_gvfs_host_keeps_its_case_and_a_dns_one_does_not():
    assert Location.parse("mtp://Google_Pixel_7/DCIM").site == Site("mtp", "", "Google_Pixel_7")
    assert str(Location.parse("mtp://Google_Pixel_7/DCIM")) == "mtp://Google_Pixel_7/DCIM"
    assert Location.parse("dav://u@Box:8080/a").site == Site("dav", "u", "Box", 8080)
    assert Location.parse("sftp://Host/x").site.host == "host"


# -- the GVfs drive --------------------------------------------------------------------


def test_a_gvfs_place_is_mounted_read_and_unmounted_when_closed(fake_gio, monkeypatch):
    monkeypatch.setenv("FAKE_GIO_PASSWORD", "secret")
    site = Site("dav", "bob", "box")
    with pytest.raises(NeedPassword) as raised:
        SESSIONS.connect(site, Answers(start="/"))
    assert not raised.value.wrong
    with pytest.raises(NeedPassword) as raised:
        SESSIONS.connect(site, Answers(start="/", password="nope"))
    assert raised.value.wrong
    try:
        drive = SESSIONS.connect(site, Answers(start="/", password="secret"))
        root = fake_gio.bridge / "dav:host=box"
        (root / "docs").mkdir()
        (root / "docs" / "a.txt").write_text("hello")
        here = Location(site, PurePosixPath("/docs"))
        assert [name for name, _ in drive.children(here)] == ["a.txt"]
        with drive.open_read(Location(site, PurePosixPath("/docs/a.txt"))) as reader:
            assert reader.read() == b"hello"
        drive.mkdir(Location(site, PurePosixPath("/docs/new")))
        assert (root / "docs" / "new").is_dir()
        assert drive.get_dir(here) == "DAV:box:/docs"
    finally:
        SESSIONS.close(site)
    assert fake_gio()["mounted"] == []
    assert ["mount", "-u", "--", "dav://bob@box/"] in fake_gio()["calls"]


def test_a_place_mounted_already_is_used_and_left_mounted(fake_gio):
    gio.mount_uri("mtp://Pixel/")
    site = Site("mtp", "", "Pixel")
    try:
        drive = SESSIONS.connect(site, Answers(start="/"))
        assert drive.root == fake_gio.bridge / "mtp:host=Pixel" and not drive.ours
    finally:
        SESSIONS.close(site)
    assert fake_gio()["mounted"] == ["mtp://Pixel"]


def test_where_the_mount_starts_is_found_from_the_place_asked_for(tmp_path):
    from navigator.lib.drives.gvfs import GvfsDrive, bridge_top

    top = tmp_path / "gvfs" / "dav:host=box,prefix=%2Fdav"
    assert bridge_top(top / "a" / "b") == top
    drive = GvfsDrive(Site("dav", "", "box"), top, PurePosixPath("/dav"), ours=False)
    assert drive.disk(Location(drive.site, PurePosixPath("/dav/a"))).local == top / "a"
    with pytest.raises(OSError) as raised:
        drive.disk(Location(drive.site, PurePosixPath("/")))
    assert raised.value.errno == errno.ENOENT


def test_gvfs_schemes_are_connections_without_being_navigators_own():
    from navigator.lib.drives import sessions

    assert sessions.module_name("mtp") == sessions.GVFS and sessions.is_connection("google-drive")
    assert "mtp" not in sessions.SCHEMES and not sessions.is_connection("http")
    assert sessions.protocol_sign("mtp") == "MTP"


def test_without_gio_a_gvfs_scheme_says_what_to_install():
    from navigator.lib.drives import sessions

    assert sessions.available("mtp") == gio.NO_GIO


# -- Volumes --------------------------------------------------------------------------


def test_gio_adds_what_is_not_mounted_and_flags_what_is():
    found = [Volume("sdb1", "ext4", "/media/me/backup", "/dev/sdb1", 100, 50)]
    merged = volumes.merge(found, gio.parse_mount_list(MOUNT_LIST),
                           lambda uri: "" if uri.startswith("smb") else uri)
    by_name = {volume.name: volume for volume in merged}
    backup = by_name["sdb1"]
    assert backup.can_unmount and backup.can_eject and not backup.can_mount
    assert backup.target == "file:///media/me/backup"
    assert [v.name for v in merged if not v.mounted] == ["external", "Pixel 7"]
    external = by_name["external"]
    assert external.mount == "" and external.can_mount and external.device == "/dev/sdb2"
    # A GVfs mount with no FUSE path has nowhere to go: not listed.
    assert "share on server" not in by_name


def gio_volumes_run(tmp_path, monkeypatch, *actions):
    """The Volumes window over a stick that is mounted on *tmp_path*/stick
    once ``gio.mount_device`` has been called for it."""
    from test_nav import navigator

    stick = tmp_path / "stick"
    stick.mkdir()
    state = {"mounted": False, "calls": []}
    known = gio.GioVolume("stick", device="/dev/sdc1", can_mount=True)

    def gather_all():
        if state["mounted"]:
            mounted = gio.GioVolume("stick", device="/dev/sdc1", uri=f"file://{stick}", can_unmount=True,
                                    can_eject=True)
            return [Volume("stick", "vfat", str(stick), "/dev/sdc1", 10, 5, can_unmount=True, can_eject=True,
                           gio=mounted)]
        return [Volume("stick", "", "", "/dev/sdc1", mounted=False, can_mount=True, gio=known)]

    def mount_device(volume):
        state["calls"].append(("mount", volume.device))
        state["mounted"] = True

    def eject(where):
        state["calls"].append(("eject", where))
        state["mounted"] = False

    monkeypatch.setattr(volumes, "gather_all", gather_all)
    monkeypatch.setattr(gio, "program", lambda which=None: "/usr/bin/gio")
    monkeypatch.setattr(gio, "mount_device", mount_device)
    monkeypatch.setattr(gio, "eject", eject)
    app = navigator(tmp_path)

    def open_it(a):
        from navigator.widgets.shell.commands import OpenVolumesWindow

        a.spawn(a.run_command(OpenVolumesWindow))

    def listed(a):
        window = a.shell.desktop.active_window
        return getattr(window, "volumes", None) is not None and bool(window.volumes.items)

    run_app(app, [open_it, Until(listed), *actions, lambda a: None])
    return state, stick


def test_a_volume_not_mounted_is_listed_so_and_enter_mounts_it_and_goes_there(tmp_path, monkeypatch):
    seen = {}

    def look(a):
        listing = a.shell.desktop.active_window.volumes
        seen["cells"] = listing.cells(listing.items[0])

    state, stick = gio_volumes_run(
        tmp_path, monkeypatch, look, KeyEvent("enter"),
        Until(lambda a: a.shell.active_manager.active_panel.path == tmp_path / "stick"))
    assert seen["cells"][2][0] == "(not mounted)" and seen["cells"][4][0] == ""
    assert state["calls"] == [("mount", "/dev/sdc1")]


def test_mount_and_eject_are_offered_as_gio_says_they_can_be(tmp_path, monkeypatch):
    from navigator.widgets.shell.commands import EjectVolume, MountVolume, UnmountVolume

    seen = []

    def look(a):
        window = a.shell.desktop.active_window
        seen.append(tuple(window.enables(command()) for command in (MountVolume, UnmountVolume, EjectVolume)))

    def mounted(a):
        return a.shell.desktop.active_window.volumes.items[0].mounted

    state, _ = gio_volumes_run(
        tmp_path, monkeypatch, look, KeyEvent("n", ctrl=True), Until(mounted), look,
        KeyEvent("e", ctrl=True), Until(lambda a: not mounted(a)), look)
    assert seen == [(True, False, False), (False, True, True), (True, False, False)]
    assert state["calls"] == [("mount", "/dev/sdc1"), ("eject", f"file://{tmp_path / 'stick'}")]


def test_without_gio_nothing_can_be_mounted(tmp_path, monkeypatch):
    from navigator.widgets.shell.commands import MountVolume

    seen = []
    gio_volumes_run(tmp_path, monkeypatch,
                    lambda a: monkeypatch.setattr(gio, "program", lambda which=None: None),
                    lambda a: seen.append(a.shell.desktop.active_window.enables(MountVolume())))
    assert seen == [False]


# -- Enter and Open with --------------------------------------------------------------


@pytest.fixture
def desktop(tmp_path, monkeypatch):
    """A directory with a file nothing is associated with, and a desktop to open it on."""
    from test_associations import navigator

    (tmp_path / "picture.png").write_bytes(b"\x89PNG")
    opened = []
    monkeypatch.setattr(gio, "program", lambda which=None: "/usr/bin/gio")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr(gio, "open_file", lambda path: opened.append(Path(path)))
    return navigator(tmp_path), opened


def test_enter_on_a_file_with_no_association_opens_it_on_the_desktop(desktop, tmp_path):
    from test_associations import to

    app, opened = desktop
    run_app(app, [to("picture.png"), KeyEvent("enter"), Until(lambda a: opened)])
    assert opened == [tmp_path / "picture.png"]


@pytest.mark.parametrize("why", ["setting", "display", "gio"])
def test_enter_leaves_it_alone_without_the_setting_a_display_or_gio(desktop, monkeypatch, why):
    from test_associations import to

    app, opened = desktop
    if why == "setting":
        SETTINGS.file_manager.open_unassociated = False
    elif why == "display":
        monkeypatch.delenv("DISPLAY")
        monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    else:
        monkeypatch.setattr(gio, "program", lambda which=None: None)
    run_app(app, [to("picture.png"), KeyEvent("enter"), lambda a: None, lambda a: None])
    assert opened == [] and app.modal is None


def test_open_with_lists_the_applications_and_launches_the_one_chosen(desktop, tmp_path, monkeypatch):
    from test_associations import popup, to
    from navml.widgets.dialog.control.control import parse_shortcut
    from navigator.widgets.manager.commands import OpenWith

    app, _ = desktop
    apps = [gio.App("eog.desktop", "Image Viewer", Path("/x/eog.desktop")),
            gio.App("gimp.desktop", "GNU Image Manipulation Program", Path("/x/gimp.desktop"))]
    launched = []
    monkeypatch.setattr(gio, "content_type", lambda path: "image/png")
    monkeypatch.setattr(gio, "applications", lambda mime: apps if mime == "image/png" else [])
    monkeypatch.setattr(gio, "launch", lambda app, path: launched.append((app.id, Path(path))))
    seen = {}

    def look(a):
        seen["captions"] = [parse_shortcut(entry.text)[0] for entry in popup(a).box.entries()
                            if hasattr(entry, "text")]

    run_app(app, [to("picture.png"), lambda a: seen.update(enabled=a.command_enabled(OpenWith(), a.focused)),
                  lambda a: a.spawn(a.run_command(OpenWith)), Until(lambda a: popup(a)), look, KeyEvent("down"), KeyEvent("enter"), Until(lambda a: launched)])
    assert seen["enabled"] and seen["captions"] == ["Image Viewer", "GNU Image Manipulation Program", "Command..."]
    assert launched == [("gimp.desktop", tmp_path / "picture.png")]


# -- gio trash ----------------------------------------------------------------------------


@pytest.fixture
def untrashable(tmp_path, monkeypatch, fake_gio):
    from navigator.lib.file_ops import trash

    place = tmp_path / "work"
    place.mkdir()
    (place / "a.txt").write_text("a")
    monkeypatch.setattr(trash, "trash_for", lambda path, mounts=None: None)
    return place


def test_where_the_trash_has_no_directory_gio_trash_takes_it(untrashable, fake_gio):
    from navigator.lib.file_ops import fileerase

    job = fileerase.EraseJob(asker=lambda question: pytest.fail(f"asked {question}"))
    done = fileerase.run(fileerase.EraseRequest([untrashable / "a.txt"], trash=True), job)
    assert done == [untrashable / "a.txt"] and not (untrashable / "a.txt").exists()
    assert ["trash", "--", str(untrashable / "a.txt")] in fake_gio()["calls"]


def test_where_gio_trash_fails_too_its_reason_is_asked_about(untrashable, monkeypatch):
    from navigator.lib.file_ops import fileerase

    monkeypatch.setenv("FAKE_GIO_TRASH_FAILS", "1")
    asked = []
    job = fileerase.EraseJob(asker=lambda question: asked.append(question) or fileerase.NO)
    assert fileerase.run(fileerase.EraseRequest([untrashable / "a.txt"], trash=True), job) == []
    assert isinstance(asked[0], fileerase.NoTrash) and "Trashing not supported" in str(asked[0])
    assert (untrashable / "a.txt").exists()


def test_the_gvfs_link_box_is_titled_so_and_asks_for_a_uri(tmp_path, monkeypatch):
    from test_nav import navigator
    from navigator.widgets.shell.commands import GvfsLink

    monkeypatch.setattr(gio, "program", lambda which=None: "/usr/bin/gio")
    seen = {}
    app = navigator(tmp_path)
    run_app(app, [lambda a: a.spawn(a.run_command(GvfsLink)), Until(lambda a: a.modal is not None),
                  lambda a: seen.update(title=a.modal.title, caption=a.modal.caption), KeyEvent("escape")])
    assert seen == {"title": "GVfs link", "caption": "~U~RI (mtp://, dav://, google-drive://...)"}


def test_mount_unmount_and_eject_are_buttons_and_on_the_key_bar_greyed_as_the_volume_says(tmp_path, monkeypatch):
    seen = []

    def look(a):
        window = a.shell.desktop.active_window
        bar = {key: (item.title, a.command_enabled(item)) for key, item, _, _ in a.shell.keybar.items()
               if key in ("f5", "f6", "f7")}
        seen.append(([button.disabled for button in (window.mount_button, window.unmount_button,
                                                      window.eject_button)], bar))

    def mounted(a):
        return a.shell.desktop.active_window.volumes.items[0].mounted

    def click(name):
        return lambda a: a.spawn(getattr(a.shell.desktop.active_window, name).press())

    state, stick = gio_volumes_run(tmp_path, monkeypatch, look, click("mount_button"), Until(mounted), look,
                                   click("eject_button"), Until(lambda a: not mounted(a)))
    assert seen[0] == ([False, True, True], {"f5": ("Mount", True), "f6": ("Unmount", False),
                                             "f7": ("Eject", False)})
    assert seen[1] == ([True, False, False], {"f5": ("Mount", False), "f6": ("Unmount", True),
                                              "f7": ("Eject", True)})
    assert state["calls"] == [("mount", "/dev/sdc1"), ("eject", f"file://{stick}")]


def test_the_f_keys_mount_and_unmount(tmp_path, monkeypatch):
    state, _ = gio_volumes_run(tmp_path, monkeypatch, KeyEvent("f5"),
                               Until(lambda a: a.shell.desktop.active_window.volumes.items[0].mounted))
    assert state["calls"] == [("mount", "/dev/sdc1")]


def test_open_with_commands_are_remembered_per_extension_and_take_the_file_at_the_end():
    from navigator.widgets.shell.shell.shell import Shell

    assert Shell.open_with_history("Photo.PNG") == "open_with.png"
    assert Shell.open_with_history("Makefile") == "open_with"
    assert Shell.open_with_line("gimp") == "gimp !.!"
    assert Shell.open_with_line("convert !.! out.jpg") == "convert !.! out.jpg"


def test_open_with_runs_a_command_typed_in_the_console_and_keeps_it_for_the_extension(desktop, tmp_path,
                                                                                         monkeypatch):
    from test_associations import capture, popup, script_of, to
    from navml.history import HISTORY
    from navigator.widgets.manager.commands import OpenWith

    app, _ = desktop
    monkeypatch.setattr(gio, "content_type", lambda path: "image/png")
    monkeypatch.setattr(gio, "applications", lambda mime: [gio.App("eog.desktop", "Image Viewer", None)])
    ran: list[str] = []
    seen = {}

    def typed(a):
        seen.update(title=a.modal.title, history=a.modal.line.history_id)
        a.modal.line.value = "gimp -n"

    run_app(app, [lambda a: capture(a, ran), to("picture.png"), lambda a: a.spawn(a.run_command(OpenWith)),
                  Until(lambda a: popup(a)), KeyEvent("end"), KeyEvent("enter"),
                  Until(lambda a: a.modal is not None and hasattr(a.modal, "line")), typed, KeyEvent("enter"),
                  Until(lambda a: ran)])
    assert seen == {"title": "Open with", "history": "open_with.png"}
    assert script_of(ran) == "gimp -n picture.png\n"
    assert "gimp -n" in HISTORY.entries("open_with.png")
