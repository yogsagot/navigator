"""KDE's KIO and Solid through their commands (navigator/lib/system/kio.py),
the facade that picks it or GIO (navigator/lib/system/desktop.py), and what
uses them: Disk > Volumes' Mount/Unmount/Eject, Enter and *Open with*, KIO
drives through kio-fuse, and the trash's fallback.

Nothing here runs KDE: one fake script -- installed on a temporary ``PATH``
as ``kioclient``, ``kmimetypefinder``, ``ktraderclient6``, ``kstart``,
``solid-hardware6`` and ``dbus-send`` -- answers as each does and records
what it was asked.
"""

from __future__ import annotations

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
from navigator.lib.system import desktop, gio, kio, volumes
from navigator.lib.system.volumes import Volume
from navigator.settings import SETTINGS

#: ``solid-hardware6 list details``, cut down: a mounted stick, a partition
#: not mounted on a fixed disk, the root file system, swap, a DVD.
SOLID = """\
udi = '/org/freedesktop/UDisks2/drives/SanDisk_Cruzer'
  parent = '/org/freedesktop/UDisks2'  (string)
  vendor = 'SanDisk'  (string)
  product = 'Cruzer'  (string)
  StorageDrive.bus = 'Usb'  (0x1)  (enum)
  StorageDrive.removable = true  (bool)
  StorageDrive.hotpluggable = true  (bool)

udi = '/org/freedesktop/UDisks2/block_devices/sdc1'
  parent = '/org/freedesktop/UDisks2/drives/SanDisk_Cruzer'  (string)
  product = 'STICK'  (string)
  Block.device = '/dev/sdc1'  (string)
  StorageAccess.accessible = true  (bool)
  StorageAccess.filePath = '/media/me/STICK'  (string)
  StorageVolume.ignored = false  (bool)
  StorageVolume.usage = 'FileSystem'  (0x1)  (enum)
  StorageVolume.fsType = 'vfat'  (string)
  StorageVolume.label = 'STICK'  (string)
  StorageVolume.uuid = '1234-ABCD'  (string)

udi = '/org/freedesktop/UDisks2/drives/Samsung_SSD'
  product = 'Samsung SSD'  (string)
  StorageDrive.removable = false  (bool)
  StorageDrive.hotpluggable = false  (bool)

udi = '/org/freedesktop/UDisks2/block_devices/sda1'
  parent = '/org/freedesktop/UDisks2/drives/Samsung_SSD'  (string)
  Block.device = '/dev/sda1'  (string)
  StorageAccess.accessible = true  (bool)
  StorageAccess.filePath = '/'  (string)
  StorageVolume.ignored = false  (bool)
  StorageVolume.usage = 'FileSystem'  (0x1)  (enum)
  StorageVolume.label = ''  (string)
  StorageVolume.uuid = 'root-uuid'  (string)

udi = '/org/freedesktop/UDisks2/block_devices/sda2'
  parent = '/org/freedesktop/UDisks2/drives/Samsung_SSD'  (string)
  Block.device = '/dev/sda2'  (string)
  StorageAccess.accessible = false  (bool)
  StorageAccess.filePath = ''  (string)
  StorageVolume.ignored = false  (bool)
  StorageVolume.usage = 'FileSystem'  (0x1)  (enum)
  StorageVolume.label = 'Windows'  (string)
  StorageVolume.uuid = 'win-uuid'  (string)

udi = '/org/freedesktop/UDisks2/block_devices/sda3'
  parent = '/org/freedesktop/UDisks2/drives/Samsung_SSD'  (string)
  Block.device = '/dev/sda3'  (string)
  StorageVolume.ignored = true  (bool)
  StorageVolume.usage = 'Other'  (0x3)  (enum)

udi = '/org/freedesktop/UDisks2/block_devices/sr0'
  product = 'DVD'  (string)
  Block.device = '/dev/sr0'  (string)
  StorageAccess.accessible = true  (bool)
  StorageAccess.filePath = '/run/media/me/FILM'  (string)
  StorageVolume.usage = 'FileSystem'  (0x1)  (enum)
  StorageVolume.label = 'FILM'  (string)
  OpticalDisc.discType = 'DvdRom'  (0x4)  (enum)
"""

#: ``ktraderclient6 --mimetype image/png --servicetype Application``, cut down.
TRADER = """\
mimetype is : image/png
servicetype is : Application
constraint is :
got 3 offers.
---- Offer 0 ----
DesktopEntryName : 'org.kde.gwenview'
DesktopEntryPath : 'org.kde.gwenview.desktop'
Name : 'Gwenview'
---- Offer 1 ----
DesktopEntryName : 'gimp'
DesktopEntryPath : '/usr/share/applications/gimp.desktop'
Name : 'GNU Image Manipulation Program'
---- Offer 2 ----
DesktopEntryName : 'org.kde.gwenview'
DesktopEntryPath : 'org.kde.gwenview.desktop'
Name : 'Gwenview'
"""


@pytest.fixture(autouse=True)
def use_kio():
    """``[system] desktop_vfs`` set to KIO -- the suite's ``conftest`` turns it off."""
    SETTINGS.system.desktop_vfs = "kio"


# -- the fake KDE ---------------------------------------------------------------------

FAKE = r'''
import json, os, sys
state_path = os.environ["FAKE_KDE_STATE"]
state = json.load(open(state_path)) if os.path.exists(state_path) else {"calls": []}
name = os.path.basename(sys.argv[0])
args = sys.argv[1:]
state["calls"].append([name, *args])
code = 0

def save():
    json.dump(state, open(state_path, "w"))

if name == "kioclient":
    if args[1] == "move":
        if os.environ.get("FAKE_KDE_TRASH_FAILS"):
            sys.stderr.write("kioclient: The file or folder trash:/ does not exist.\n")
            code = 1
        else:
            os.remove(args[2])
elif name == "kmimetypefinder":
    print("image/png")
elif name == "ktraderclient6":
    print(open(os.environ["FAKE_KDE_TRADER"]).read())
elif name == "solid-hardware6":
    if args[0] == "list":
        print(open(os.environ["FAKE_KDE_SOLID"]).read())
elif name == "dbus-send":
    url = args[-1].partition(":")[2]
    if "secret" not in url and os.environ.get("FAKE_KDE_PASSWORD"):
        sys.stderr.write("Error org.freedesktop.DBus.Error.Failed: Authentication failed.\n")
        code = 1
    else:
        scheme, _, rest = url.partition(":")
        rest = rest.lstrip("/")
        authority = rest.split("/")[0].rpartition("@")[2]
        path = os.path.join(os.environ["FAKE_KDE_FUSE"], scheme, authority, *rest.split("/")[1:])
        os.makedirs(path, exist_ok=True)
        print("method return time=1 sender=:1.2 -> destination=:1.3 serial=4 reply_serial=2")
        print(f'   string "{path}"')
save()
sys.exit(code)
'''

NAMES = ("kioclient", "kmimetypefinder", "ktraderclient6", "kstart", "solid-hardware6", "dbus-send")


@pytest.fixture
def fake_kde(tmp_path, monkeypatch):
    """KDE's commands on ``PATH``, recording their calls in a JSON file;
    kio-fuse's bridge is a directory under *tmp_path*.  Answers the state's reader."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name in NAMES:
        script = bin_dir / name
        script.write_text(f"#!{sys.executable}\n{FAKE}")
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
    fuse = tmp_path / "run" / "kio-fuse-AbCdEf"
    fuse.mkdir(parents=True)
    (tmp_path / "solid.txt").write_text(SOLID)
    (tmp_path / "trader.txt").write_text(TRADER)
    state = tmp_path / "kde.json"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_KDE_STATE", str(state))
    monkeypatch.setenv("FAKE_KDE_FUSE", str(fuse))
    monkeypatch.setenv("FAKE_KDE_SOLID", str(tmp_path / "solid.txt"))
    monkeypatch.setenv("FAKE_KDE_TRADER", str(tmp_path / "trader.txt"))

    def read() -> dict:
        return json.loads(state.read_text()) if state.exists() else {"calls": []}

    read.fuse = fuse  # type: ignore[attr-defined]
    return read


# -- choosing the backend ---------------------------------------------------------------


@pytest.mark.parametrize("setting, session, has, expected", [
    ("auto", "KDE", ("gio", "kio"), kio),
    ("auto", "XFCE", ("gio", "kio"), gio),
    ("auto", "KDE", ("gio",), gio),
    ("auto", "GNOME", ("kio",), kio),
    ("gio", "KDE", ("gio", "kio"), gio),
    ("kio", "GNOME", ("gio",), None),
    ("off", "KDE", ("gio", "kio"), None),
    ("auto", "KDE", (), None),
])
def test_the_backend_is_kio_under_kde_and_gio_elsewhere(monkeypatch, setting, session, has, expected):
    SETTINGS.system.desktop_vfs = setting
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", session)
    monkeypatch.setattr(gio, "program", lambda which=None: "/usr/bin/gio" if "gio" in has else None)
    monkeypatch.setattr(kio, "program", lambda which=None: "/usr/bin/kioclient" if "kio" in has else None)
    assert desktop.backend() is expected


def test_an_old_use_gio_false_reads_as_off(tmp_path):
    ini = tmp_path / "navigator.ini"
    ini.write_text("[system]\nuse_gio = false\n")
    SETTINGS.load(ini)
    assert SETTINGS.system.desktop_vfs == "off"
    ini.write_text("[system]\nuse_gio = false\ndesktop_vfs = kio\n")
    SETTINGS.load(ini)
    assert SETTINGS.system.desktop_vfs == "kio"


def test_kf5s_names_are_found_where_kf6s_are_not():
    present = {"kioclient5", "solid-hardware5", "kstart5"}

    def which(name):
        return f"/usr/bin/{name}" if name in present else None

    assert kio.program(which) == "/usr/bin/kioclient5"
    assert kio.command("solid-hardware", which) == "/usr/bin/solid-hardware5"
    assert kio.command("ktraderclient", which) is None


# -- parsers ------------------------------------------------------------------------------


def test_solid_gives_file_systems_with_what_can_be_done_to_each():
    found = {each.name: each for each in kio.parse_solid(SOLID)}
    assert sorted(found) == ["/dev/sda1", "FILM", "STICK", "Windows"]
    stick = found["STICK"]
    assert (stick.local, stick.device, stick.ident, stick.target) == (
        "/media/me/STICK", "/dev/sdc1", "1234-ABCD", "/org/freedesktop/UDisks2/block_devices/sdc1")
    assert stick.mounted and stick.can_unmount and stick.can_eject and not stick.can_mount
    windows = found["Windows"]
    assert not windows.mounted and windows.can_mount and not windows.can_unmount and not windows.can_eject
    root = found["/dev/sda1"]
    assert root.mounted and not root.can_unmount and not root.can_eject
    film = found["FILM"]
    assert film.can_eject and film.can_unmount


def test_solid_volumes_merge_as_gios_do():
    found = [Volume("sdc1", "vfat", "/media/me/STICK", "/dev/sdc1", 100, 50)]
    merged = volumes.merge(found, kio.parse_solid(SOLID))
    by_name = {volume.name: volume for volume in merged}
    assert by_name["sdc1"].can_eject and by_name["sdc1"].target == "/org/freedesktop/UDisks2/block_devices/sdc1"
    assert [v.name for v in merged if not v.mounted] == ["Windows"]


def test_the_trader_gives_each_application_once_in_its_order():
    assert kio.parse_trader(TRADER) == [("org.kde.gwenview.desktop", "Gwenview"),
                                        ("gimp.desktop", "GNU Image Manipulation Program")]


def test_a_dbus_reply_gives_its_string_and_a_failure_its_reason():
    assert kio.parse_reply('method return time=1\n   string "/run/user/1/kio-fuse-x/mtp/a b"\n') == \
        "/run/user/1/kio-fuse-x/mtp/a b"
    assert kio._reason("Error org.freedesktop.DBus.Error.Failed: Authentication failed.\n", "") == \
        "Authentication failed."
    assert kio._reason("kioclient: The file does not exist.\n", "") == "The file does not exist."


def test_hostless_schemes_lose_their_host_for_kio():
    assert kio.kio_url("mtp://Pixel/Internal") == "mtp:/Pixel/Internal"
    assert kio.kio_url("webdav://box/dav") == "webdav://box/dav"


def test_kio_schemes_are_the_installed_workers(tmp_path):
    plugins = tmp_path / "kf6" / "kio"
    plugins.mkdir(parents=True)
    (plugins / "mtp.so").write_bytes(b"")
    (plugins / "http.so").write_bytes(b"")
    assert kio.kio_schemes([plugins]) == ("mtp", "webdav", "webdavs")


# -- the commands -----------------------------------------------------------------------------


def test_applications_open_and_launch_through_kde(fake_kde, tmp_path):
    apps = kio.applications("image/png", [])
    assert [(app.id, app.name) for app in apps] == [("org.kde.gwenview.desktop", "Gwenview"),
                                                   ("gimp.desktop", "GNU Image Manipulation Program")]
    picture = tmp_path / "p.png"
    assert kio.content_type(picture) == "image/png"
    kio.open_file(picture)
    assert ["kioclient", "--noninteractive", "exec", str(picture)] in fake_kde()["calls"]


def test_volumes_mount_and_eject_by_udi(fake_kde):
    found = {each.name: each for each in desktop.volumes()}
    desktop.mount_device(found["Windows"])
    desktop.eject("/media/me/STICK")
    calls = fake_kde()["calls"]
    assert ["solid-hardware6", "mount", "/org/freedesktop/UDisks2/block_devices/sda2"] in calls
    assert ["solid-hardware6", "eject", "/org/freedesktop/UDisks2/block_devices/sdc1"] in calls


def test_a_failure_is_the_commands_own_reason(fake_kde, tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_KDE_TRASH_FAILS", "1")
    (tmp_path / "a").write_text("a")
    with pytest.raises(OSError) as raised:
        kio.trash(tmp_path / "a")
    assert raised.value.strerror == "The file or folder trash:/ does not exist."


# -- the KIO drive ------------------------------------------------------------------------------


def test_kio_schemes_go_to_kio_and_shared_ones_to_the_backend_in_use(monkeypatch):
    from navigator.lib.drives import sessions

    monkeypatch.setattr(kio, "program", lambda which=None: "/usr/bin/kioclient")
    assert sessions.module_name("webdav") == sessions.KIO and sessions.module_name("mtp") == sessions.KIO
    SETTINGS.system.desktop_vfs = "gio"
    assert sessions.module_name("mtp") == sessions.GVFS and sessions.module_name("fish") == sessions.KIO
    assert sessions.protocol_sign("fish") == "FISH"


def test_a_kio_place_is_reached_through_kio_fuse(fake_kde, monkeypatch):
    monkeypatch.setenv("FAKE_KDE_PASSWORD", "secret")
    site = Site("webdav", "bob", "box")
    with pytest.raises(NeedPassword) as raised:
        SESSIONS.connect(site, Answers(start="/"))
    assert not raised.value.wrong
    with pytest.raises(NeedPassword) as raised:
        SESSIONS.connect(site, Answers(start="/", password="nope"))
    assert raised.value.wrong
    try:
        drive = SESSIONS.connect(site, Answers(start="/dav", password="secret"))
        root = fake_kde.fuse / "webdav" / "box"
        assert drive.root == root and drive.prefix == PurePosixPath("/")
        (root / "dav" / "a.txt").write_text("hello")
        here = Location(site, PurePosixPath("/dav"))
        assert [name for name, _ in drive.children(here)] == ["a.txt"]
        drive.mkdir(Location(site, PurePosixPath("/dav/new")))
        assert (root / "dav" / "new").is_dir()
        assert drive.get_dir(here) == "DAV:box:/dav"
        assert ("Kind", "KIO") in drive.describe()
    finally:
        SESSIONS.close(site)
    assert "dbus-send" in [call[0] for call in fake_kde()["calls"]]


def test_a_phone_keeps_its_name_and_loses_the_host_for_kio(fake_kde):
    site = Location.parse("mtp://Pixel_7/").site
    assert site.host == "Pixel_7"
    try:
        drive = SESSIONS.connect(site, Answers(start="/Internal"))
        assert drive.root == fake_kde.fuse / "mtp" / "Pixel_7"
    finally:
        SESSIONS.close(site)
    assert any(call[-1] == "string:mtp:/Pixel_7/Internal" for call in fake_kde()["calls"])


# -- Volumes window, Enter, Open with, trash ---------------------------------------------------


def test_the_volumes_window_mounts_through_solid(tmp_path, monkeypatch):
    from test_nav import navigator

    stick = tmp_path / "stick"
    stick.mkdir()
    state = {"mounted": False, "calls": []}
    known = kio.KioVolume("stick", udi="/u/sdc1", device="/dev/sdc1", can_mount=True)

    def gather_all():
        if state["mounted"]:
            mounted = kio.KioVolume("stick", udi="/u/sdc1", local=str(stick), can_unmount=True, can_eject=True)
            return [Volume("stick", "vfat", str(stick), "/dev/sdc1", 10, 5, can_unmount=True, can_eject=True,
                           native=mounted)]
        return [Volume("stick", "", "", "/dev/sdc1", mounted=False, can_mount=True, native=known)]

    def mount_device(volume):
        state["calls"].append(("mount", volume.udi))
        state["mounted"] = True

    def eject(where):
        state["calls"].append(("eject", where))
        state["mounted"] = False

    monkeypatch.setattr(volumes, "gather_all", gather_all)
    monkeypatch.setattr(kio, "program", lambda which=None: "/usr/bin/kioclient")
    monkeypatch.setattr(kio, "command", lambda name, which=None: f"/usr/bin/{name}")
    monkeypatch.setattr(kio, "mount_device", mount_device)
    monkeypatch.setattr(kio, "eject", eject)
    app = navigator(tmp_path)

    def open_it(a):
        from navigator.widgets.shell.commands import OpenVolumesWindow

        a.spawn(a.run_command(OpenVolumesWindow))

    def listed(a):
        window = a.shell.desktop.active_window
        return getattr(window, "volumes", None) is not None and bool(window.volumes.items)

    def mounted(a):
        return a.shell.desktop.active_window.volumes.items[0].mounted

    run_app(app, [open_it, Until(listed), KeyEvent("f5"), Until(mounted), KeyEvent("f7"),
                  Until(lambda a: not mounted(a)), lambda a: None])
    assert state["calls"] == [("mount", "/u/sdc1"), ("eject", "/u/sdc1")]


def test_enter_and_open_with_go_through_kio(tmp_path, monkeypatch):
    from test_associations import navigator, popup, to
    from navigator.widgets.manager.commands import OpenWith

    (tmp_path / "picture.png").write_bytes(b"\x89PNG")
    opened, launched = [], []
    monkeypatch.setattr(kio, "program", lambda which=None: "/usr/bin/kioclient")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr(kio, "open_file", lambda path: opened.append(Path(path)))
    monkeypatch.setattr(kio, "content_type", lambda path: "image/png")
    monkeypatch.setattr(kio, "applications", lambda mime: [kio.App("gimp.desktop", "GIMP", None)])
    monkeypatch.setattr(kio, "launch", lambda app, path: launched.append((app.id, Path(path))))
    app = navigator(tmp_path)
    run_app(app, [to("picture.png"), KeyEvent("enter"), Until(lambda a: opened),
                  lambda a: a.spawn(a.run_command(OpenWith)), Until(lambda a: popup(a)), KeyEvent("enter"),
                  Until(lambda a: launched)])
    assert opened == [tmp_path / "picture.png"]
    assert launched == [("gimp.desktop", tmp_path / "picture.png")]


def test_where_the_trash_has_no_directory_kio_takes_it(tmp_path, monkeypatch, fake_kde):
    from navigator.lib.file_ops import fileerase, trash

    place = tmp_path / "work"
    place.mkdir()
    (place / "a.txt").write_text("a")
    monkeypatch.setattr(trash, "trash_for", lambda path, mounts=None: None)
    job = fileerase.EraseJob(asker=lambda question: pytest.fail(f"asked {question}"))
    done = fileerase.run(fileerase.EraseRequest([place / "a.txt"], trash=True), job)
    assert done == [place / "a.txt"] and not (place / "a.txt").exists()
    assert ["kioclient", "--noninteractive", "move", str(place / "a.txt"), "trash:/"] in fake_kde()["calls"]


def test_the_link_box_is_kios_under_kio(tmp_path, monkeypatch):
    from test_nav import navigator
    from navigator.widgets.shell.commands import GvfsLink

    monkeypatch.setattr(kio, "program", lambda which=None: "/usr/bin/kioclient")
    seen = {}
    app = navigator(tmp_path)
    run_app(app, [lambda a: a.spawn(a.run_command(GvfsLink)), Until(lambda a: a.modal is not None),
                  lambda a: seen.update(title=a.modal.title, caption=a.modal.caption), KeyEvent("escape")])
    assert seen == {"title": "GVfs/KIO link", "caption": "~U~RI (mtp://, webdav://, gdrive://...)"}
