"""udisks2 through ``udisksctl``: Disk > Volumes where neither GIO nor Solid is."""

from __future__ import annotations

from pathlib import Path

import pytest

from navkit.events import KeyEvent

from conftest import Until, run_app

from navigator.lib.system import desktop, gio, kio, udisks, volumes
from navigator.lib.system.volumes import Volume
from navigator.settings import SETTINGS


DRIVES = "/org/freedesktop/UDisks2/drives/"
BLOCKS = "/org/freedesktop/UDisks2/block_devices/"

#: A ``udisksctl dump`` cut down to what is read: the system's NVMe disk, a
#: USB stick with one partition mounted and one not, a DVD drive with a disc,
#: a LUKS partition opened on the stick, a snap's loop image and an ignored
#: partition.
DUMP = f"""\
/org/freedesktop/UDisks2/Manager:
  org.freedesktop.UDisks2.Manager:
    Version:                    2.10.1

{DRIVES}Samsung_SSD:
  org.freedesktop.UDisks2.Drive:
    CanPowerOff:                false
    Ejectable:                  false
    MediaRemovable:             false
    Model:                      Samsung SSD 980
    Removable:                  false
    Vendor:

{DRIVES}SanDisk_Cruzer:
  org.freedesktop.UDisks2.Drive:
    CanPowerOff:                true
    Ejectable:                  false
    MediaRemovable:             false
    Model:                      Cruzer
    Removable:                  true
    Vendor:                     SanDisk

{DRIVES}HL_DT_ST_DVD:
  org.freedesktop.UDisks2.Drive:
    CanPowerOff:                false
    Ejectable:                  true
    MediaRemovable:             true
    Model:                      DVDRAM
    Removable:                  true
    Vendor:                     HL-DT-ST

{BLOCKS}nvme0n1p1:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '/'
    Device:                     /dev/nvme0n1p1
    Drive:                      '{DRIVES}Samsung_SSD'
    HintIgnore:                 false
    HintSystem:                 true
    IdLabel:
    IdUUID:                     1111
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:        /
  org.freedesktop.UDisks2.Partition:
    Number:             1

{BLOCKS}nvme0n1p2:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '/'
    Device:                     /dev/nvme0n1p2
    Drive:                      '{DRIVES}Samsung_SSD'
    HintIgnore:                 false
    HintSystem:                 true
    IdLabel:                    Recovery
    IdUUID:                     2222
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:

{BLOCKS}nvme0n1p3:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '/'
    Device:                     /dev/nvme0n1p3
    Drive:                      '{DRIVES}Samsung_SSD'
    HintIgnore:                 true
    HintSystem:                 false
    IdLabel:                    Hidden
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:

{BLOCKS}sdc:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '/'
    Device:                     /dev/sdc
    Drive:                      '{DRIVES}SanDisk_Cruzer'
    IdUsage:
  org.freedesktop.UDisks2.PartitionTable:
    Partitions:         {BLOCKS}sdc1
                        {BLOCKS}sdc2

{BLOCKS}sdc1:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '/'
    Device:                     /dev/sdc1
    Drive:                      '{DRIVES}SanDisk_Cruzer'
    HintIgnore:                 false
    HintSystem:                 false
    IdLabel:                    STICK
    IdUUID:                     AB-CD
    IdUsage:                    filesystem
    Symlinks:                   /dev/disk/by-label/STICK
                                /dev/disk/by-uuid/AB-CD
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:        /media/me/STICK
                        /media/me/again

{BLOCKS}sdc2:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '/'
    Device:                     /dev/sdc2
    Drive:                      '{DRIVES}SanDisk_Cruzer'
    HintIgnore:                 false
    HintSystem:                 false
    IdLabel:
    IdUUID:                     EF-01
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:

{BLOCKS}sr0:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '/'
    Device:                     /dev/sr0
    Drive:                      '{DRIVES}HL_DT_ST_DVD'
    HintIgnore:                 false
    HintSystem:                 false
    IdLabel:                    MOVIE
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:        /media/me/MOVIE

{BLOCKS}dm_2d0:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '{BLOCKS}sdc2'
    Device:                     /dev/dm-0
    Drive:                      '/'
    HintIgnore:                 false
    HintSystem:                 false
    IdLabel:                    secret
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:

{BLOCKS}loop3:
  org.freedesktop.UDisks2.Block:
    CryptoBackingDevice:        '/'
    Device:                     /dev/loop3
    Drive:                      '/'
    HintIgnore:                 false
    HintSystem:                 true
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:        /snap/core/1
  org.freedesktop.UDisks2.Loop:
    BackingFile:        /var/lib/snapd/snaps/core_1.snap
"""


@pytest.fixture
def fake_udisks(monkeypatch):
    """``udisksctl`` and ``busctl`` installed, each run recorded and answered with :data:`DUMP`."""
    calls: list[list[str]] = []

    def run(argv, timeout=udisks.TIMEOUT):
        calls.append(list(argv))
        return DUMP if argv[1:] == ["dump"] else ""

    monkeypatch.setattr(udisks, "program", lambda which=None: "udisksctl")
    monkeypatch.setattr(udisks.shutil, "which", lambda name: name if name == "busctl" else None)
    monkeypatch.setattr(udisks, "run", run)
    return calls


# -- reading the dump ---------------------------------------------------------------------


def test_the_dump_is_read_by_object_interface_and_property():
    objects = udisks.parse_dump(DUMP)
    stick = objects[BLOCKS + "sdc1"]
    assert stick["Filesystem"]["MountPoints"] == ["/media/me/STICK", "/media/me/again"]
    assert stick["Block"]["Drive"] == [DRIVES + "SanDisk_Cruzer"]
    assert stick["Block"]["CryptoBackingDevice"] == []
    assert objects[BLOCKS + "nvme0n1p1"]["Filesystem"]["MountPoints"] == ["/"]
    assert objects[DRIVES + "SanDisk_Cruzer"]["Drive"]["Vendor"] == ["SanDisk"]


def test_the_file_systems_are_listed_less_loops_the_ignored_and_the_systems_unmounted():
    found = {each.device: each for each in udisks.parse_volumes(DUMP)}
    assert sorted(found) == ["/dev/dm-0", "/dev/nvme0n1p1", "/dev/sdc1", "/dev/sdc2", "/dev/sr0"]
    root = found["/dev/nvme0n1p1"]
    assert (root.name, root.local, root.mounted) == ("Samsung SSD 980", "/", True)
    assert not (root.can_mount or root.can_unmount or root.can_eject)
    stick = found["/dev/sdc1"]
    assert (stick.name, stick.local, stick.uuid) == ("STICK", "/media/me/STICK", "AB-CD")
    assert stick.can_unmount and stick.can_eject and not stick.can_mount
    assert stick.target == stick.ident == "/dev/sdc1"
    blank = found["/dev/sdc2"]
    assert (blank.name, blank.mounted, blank.can_mount) == ("SanDisk Cruzer", False, True)
    assert found["/dev/sr0"].can_eject


def test_an_opened_luks_volume_is_on_its_containers_drive():
    secret = {each.device: each for each in udisks.parse_volumes(DUMP)}["/dev/dm-0"]
    assert secret.name == "secret" and secret.drive == DRIVES + "SanDisk_Cruzer" and secret.can_eject


def test_a_failure_is_the_commands_own_reason():
    assert udisks._reason(
        "Error mounting /dev/sdc2: GDBus.Error:org.freedesktop.UDisks2.Error.NotAuthorizedCanObtain: "
        "Not authorized to perform operation\n", "x") == "Not authorized to perform operation"
    assert udisks._reason("Call failed: Device is busy\n", "x") == "Device is busy"
    assert udisks._reason("", "udisksctl failed (1)") == "udisksctl failed (1)"


# -- mount, unmount, eject ------------------------------------------------------------------


def test_mount_and_unmount_by_device_and_by_mount_point(fake_udisks):
    blank = {each.device: each for each in udisks.volumes()}["/dev/sdc2"]
    udisks.mount_device(blank)
    udisks.unmount("/dev/sdc1")
    udisks.unmount("/media/me/MOVIE")
    assert ["udisksctl", "mount", "-b", "/dev/sdc2", "--no-user-interaction"] in fake_udisks
    assert ["udisksctl", "unmount", "-b", "/dev/sdc1", "--no-user-interaction"] in fake_udisks
    assert ["udisksctl", "unmount", "-b", "/dev/sr0", "--no-user-interaction"] in fake_udisks


def test_eject_unmounts_the_drive_and_powers_a_stick_off(fake_udisks):
    udisks.eject("/dev/sdc1")
    assert fake_udisks[1:] == [
        ["udisksctl", "unmount", "-b", "/dev/sdc1", "--no-user-interaction"],
        ["udisksctl", "power-off", "-p", "drives/SanDisk_Cruzer", "--no-user-interaction"],
    ]


def test_eject_ejects_a_disc_through_busctl(fake_udisks, monkeypatch):
    udisks.eject("/media/me/MOVIE")
    assert fake_udisks[-1] == ["busctl", "--system", "--allow-interactive-authorization=no", "call",
                               "org.freedesktop.UDisks2", DRIVES + "HL_DT_ST_DVD",
                               "org.freedesktop.UDisks2.Drive", "Eject", "a{sv}", "0"]
    monkeypatch.setattr(udisks.shutil, "which", lambda name: None)
    with pytest.raises(OSError) as raised:
        udisks.eject("/dev/sr0")
    assert raised.value.strerror == udisks.NO_BUSCTL


def test_without_udisksctl_nothing_runs(monkeypatch):
    monkeypatch.setattr(udisks, "program", lambda which=None: None)
    with pytest.raises(OSError) as raised:
        udisks.volumes()
    assert raised.value.strerror == udisks.NO_UDISKS


# -- who Disk > Volumes asks -------------------------------------------------------------------


@pytest.mark.parametrize("setting, has, expected", [
    ("auto", {"gio", "udisks"}, gio),
    ("off", {"gio", "udisks"}, udisks),
    ("off", set(), None),
    ("kio", {"kio", "solid", "udisks"}, kio),
    ("kio", {"kio", "udisks"}, udisks),
    ("gio", {"udisks"}, udisks),
])
def test_volumes_fall_back_to_udisks_where_the_desktop_has_no_volume_command(setting, has, expected, monkeypatch):
    SETTINGS.system.desktop_vfs = setting
    monkeypatch.delenv("XDG_CURRENT_DESKTOP", raising=False)
    monkeypatch.setattr(gio, "program", lambda which=None: "/usr/bin/gio" if "gio" in has else None)
    monkeypatch.setattr(kio, "program", lambda which=None: "/usr/bin/kioclient" if "kio" in has else None)
    monkeypatch.setattr(kio, "command", lambda name, which=None:
                        "/usr/bin/solid-hardware6" if name == "solid-hardware" and "solid" in has else None)
    monkeypatch.setattr(udisks, "program", lambda which=None: "/usr/bin/udisksctl" if "udisks" in has else None)
    assert desktop.volume_backend() is expected
    assert (desktop.volume_program() is None) == (expected is None)


def test_gather_all_merges_what_udisks_knows(fake_udisks, monkeypatch):
    monkeypatch.setattr(volumes, "gather", lambda: [
        Volume("STICK", "vfat", "/media/me/STICK", "/dev/sdc1", 10, 5),
    ])
    found = {each.device: each for each in volumes.gather_all()}
    assert found["/dev/sdc1"].can_eject and found["/dev/sdc1"].native.device == "/dev/sdc1"
    assert not found["/dev/sdc2"].mounted and found["/dev/sdc2"].can_mount


def test_the_volumes_window_mounts_and_ejects_through_udisks(tmp_path, monkeypatch):
    from test_nav import navigator

    stick = tmp_path / "stick"
    stick.mkdir()
    state = {"mounted": False, "calls": []}

    def gather_all():
        if state["mounted"]:
            mounted = udisks.UdisksVolume("stick", device="/dev/sdc1", local=str(stick), can_unmount=True,
                                          can_eject=True)
            return [Volume("stick", "vfat", str(stick), "/dev/sdc1", 10, 5, can_unmount=True, can_eject=True,
                           native=mounted)]
        known = udisks.UdisksVolume("stick", device="/dev/sdc1", can_mount=True)
        return [Volume("stick", "", "", "/dev/sdc1", mounted=False, can_mount=True, native=known)]

    def mount_device(volume):
        state["calls"].append(("mount", volume.device))
        state["mounted"] = True

    def eject(where):
        state["calls"].append(("eject", where))
        state["mounted"] = False

    monkeypatch.setattr(volumes, "gather_all", gather_all)
    monkeypatch.setattr(udisks, "program", lambda which=None: "/usr/bin/udisksctl")
    monkeypatch.setattr(udisks, "mount_device", mount_device)
    monkeypatch.setattr(udisks, "eject", eject)
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
    assert state["calls"] == [("mount", "/dev/sdc1"), ("eject", "/dev/sdc1")]


# -- disk images -------------------------------------------------------------------------

#: The user (uid 1000) has an ISO on loop7, mounted, and a partitioned image
#: on loop8 whose two partitions are not; root has a loop of its own.
LOOPS = f"""\
{BLOCKS}loop7:
  org.freedesktop.UDisks2.Block:
    Device:                     /dev/loop7
    Drive:                      '/'
    HintIgnore:                 false
    HintSystem:                 true
    IdLabel:                    UBUNTU
    IdUsage:                    filesystem
    Size:                       52428800
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:        /media/me/UBUNTU
  org.freedesktop.UDisks2.Loop:
    BackingFile:        /home/me/ubuntu.iso
    SetupByUID:         1000

{BLOCKS}loop8:
  org.freedesktop.UDisks2.Block:
    Device:                     /dev/loop8
    Drive:                      '/'
    HintSystem:                 true
    IdUsage:
  org.freedesktop.UDisks2.Loop:
    BackingFile:        /home/me/sd card.img
    SetupByUID:         1000
  org.freedesktop.UDisks2.PartitionTable:
    Partitions:         {BLOCKS}loop8p1
                        {BLOCKS}loop8p2

{BLOCKS}loop8p1:
  org.freedesktop.UDisks2.Block:
    Device:                     /dev/loop8p1
    Drive:                      '/'
    HintSystem:                 true
    IdLabel:                    boot
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:
  org.freedesktop.UDisks2.Partition:
    Table:              '{BLOCKS}loop8'

{BLOCKS}loop8p2:
  org.freedesktop.UDisks2.Block:
    Device:                     /dev/loop8p2
    Drive:                      '/'
    HintSystem:                 true
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:
  org.freedesktop.UDisks2.Partition:
    Table:              '{BLOCKS}loop8'

{BLOCKS}loop9:
  org.freedesktop.UDisks2.Block:
    Device:                     /dev/loop9
    Drive:                      '/'
    HintSystem:                 true
    IdUsage:                    filesystem
  org.freedesktop.UDisks2.Filesystem:
    MountPoints:        /mnt/root
  org.freedesktop.UDisks2.Loop:
    BackingFile:        /root/root.iso
    SetupByUID:         0
"""


def _mounted(text: str, device: str, where: str) -> str:
    """*text* with *device*'s empty ``MountPoints`` made *where*."""
    head, _, tail = text.partition(f"    Device:                     {device}\n")
    return head + f"    Device:                     {device}\n" + tail.replace(
        "    MountPoints:\n", f"    MountPoints:        {where}\n", 1)


def test_the_users_own_loops_are_listed_and_root_s_and_snaps_are_not():
    found = {volume.device: volume for volume in udisks.parse_volumes(DUMP + "\n" + LOOPS, uid=1000)}
    assert "/dev/loop3" not in found and "/dev/loop9" not in found
    iso = found["/dev/loop7"]
    assert (iso.name, iso.local, iso.loop, iso.size) == ("UBUNTU", "/media/me/UBUNTU", BLOCKS + "loop7", 52428800)
    assert iso.can_unmount and iso.can_eject
    assert found["/dev/loop8p1"].name == "boot" and found["/dev/loop8p1"].loop == BLOCKS + "loop8"
    # No label: the image's own name.
    assert found["/dev/loop8p2"].name == "sd card.img" and not found["/dev/loop8p2"].mounted
    assert udisks.is_image_name("A.ISO") and udisks.is_image_name("x.img") and not udisks.is_image_name(".iso")


@pytest.fixture
def images(monkeypatch):
    """udisksctl and busctl answering for :data:`LOOPS`: ``loop-setup`` maps
    onto loop8, and each ``mount`` mounts in the dumps that follow."""
    state = {"dump": DUMP, "calls": [], "already": set()}

    def run(argv, timeout=udisks.TIMEOUT):
        state["calls"].append(list(argv))
        verb = argv[1]
        if verb == "dump":
            return state["dump"]
        if verb == "loop-setup":
            state["dump"] = DUMP + "\n" + LOOPS
            return "Mapped file /home/me/sd card.img as /dev/loop8.\n"
        if verb == "mount":
            device = argv[3]
            if device in state["already"]:
                raise OSError(5, f"Error mounting {device}: Device {device} is already mounted at `/media/me/x'.")
            state["dump"] = _mounted(state["dump"], device, "/media/me/" + device.rpartition("/")[2])
        return ""

    monkeypatch.setattr(udisks, "program", lambda which=None: "udisksctl")
    monkeypatch.setattr(udisks.shutil, "which", lambda name: name if name == "busctl" else None)
    monkeypatch.setattr(udisks, "run", run)
    monkeypatch.setattr(udisks.os.path, "realpath", lambda path: str(path))
    return state


def test_an_image_is_set_up_read_only_and_every_file_system_on_it_mounted(images):
    found = udisks.attach_image(Path("/home/me/sd card.img"), uid=1000)
    calls = images["calls"]
    assert ["udisksctl", "loop-setup", "-r", "-f", "/home/me/sd card.img", "--no-user-interaction"] in calls
    assert ["udisksctl", "mount", "-b", "/dev/loop8p1", "--no-user-interaction"] in calls
    assert ["udisksctl", "mount", "-b", "/dev/loop8p2", "--no-user-interaction"] in calls
    assert ["busctl", "--system", "--allow-interactive-authorization=no", "call", "org.freedesktop.UDisks2",
            BLOCKS + "loop8", "org.freedesktop.UDisks2.Loop", "SetAutoclear", "ba{sv}", "true", "0"] in calls
    assert [(each.device, each.local) for each in found] == [
        ("/dev/loop8p1", "/media/me/loop8p1"), ("/dev/loop8p2", "/media/me/loop8p2")]


def test_an_image_attached_already_is_not_set_up_again_and_its_mount_is_kept(images):
    images["dump"] = DUMP + "\n" + LOOPS
    found = udisks.attach_image(Path("/home/me/ubuntu.iso"), uid=1000)
    assert not any(call[1] in ("loop-setup", "mount") for call in images["calls"])
    assert [each.local for each in found] == ["/media/me/UBUNTU"]


def test_a_file_system_the_desktop_mounted_first_is_no_failure(images):
    images["already"].add("/dev/loop8p1")
    found = udisks.attach_image(Path("/home/me/sd card.img"), uid=1000)
    assert [each.device for each in found] == ["/dev/loop8p2"]


def test_an_image_with_no_file_system_is_detached_again(images, monkeypatch):
    monkeypatch.setattr(udisks, "PROBE_TIMEOUT", 0.0)
    bare = LOOPS.split(f"{BLOCKS}loop8p1:")[0].replace("loop7", "loop6")  # loop8 with no partitions yet

    def run(argv, timeout=udisks.TIMEOUT):
        images["calls"].append(list(argv))
        if argv[1] == "loop-setup":
            return "Mapped file /home/me/sd card.img as /dev/loop8.\n"
        return DUMP + "\n" + bare if images["calls"][1:] else DUMP

    monkeypatch.setattr(udisks, "run", run)
    with pytest.raises(OSError, match="no file system"):
        udisks.attach_image(Path("/home/me/sd card.img"), uid=1000)
    assert images["calls"][-1] == ["udisksctl", "loop-delete", "-b", "/dev/loop8", "--no-user-interaction"]


def test_eject_on_an_image_unmounts_it_and_detaches_the_loop(images, monkeypatch):
    images["dump"] = _mounted(DUMP + "\n" + LOOPS, "/dev/loop8p2", "/media/me/data")
    monkeypatch.setattr(udisks.os, "getuid", lambda: 1000)
    udisks.eject("/media/me/data")
    assert images["calls"][1:] == [
        ["udisksctl", "unmount", "-b", "/dev/loop8p2", "--no-user-interaction"],
        ["udisksctl", "dump"],
        ["udisksctl", "loop-delete", "-b", "/dev/loop8", "--no-user-interaction"],
    ]


def test_eject_leaves_a_loop_autoclear_detached_alone(images, monkeypatch):
    """udisks keeps a detached loop device, its backing file empty: no
    ``loop-delete``, which would fail *Cannot perform operation*."""
    mounted = _mounted(DUMP + "\n" + LOOPS, "/dev/loop8p2", "/media/me/data")
    detached = (DUMP + "\n" + LOOPS).replace("    BackingFile:        /home/me/sd card.img\n",
                                                "    BackingFile:        \n")
    dumps = iter([mounted, detached])
    monkeypatch.setattr(udisks.os, "getuid", lambda: 1000)

    def run(argv, timeout=udisks.TIMEOUT):
        images["calls"].append(list(argv))
        if argv[1] == "loop-delete":
            raise OSError(5, "Cannot perform operation")
        return next(dumps) if argv[1] == "dump" else ""

    monkeypatch.setattr(udisks, "run", run)
    udisks.eject("/media/me/data")
    assert ["udisksctl", "unmount", "-b", "/dev/loop8p2", "--no-user-interaction"] in images["calls"]
    assert not any(call[1] == "loop-delete" for call in images["calls"])


@pytest.fixture
def image_desk(tmp_path, monkeypatch):
    from navigator.__main__ import Navigator
    from conftest import FakeTerminal

    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "disk.iso").write_bytes(b"not a tar, nor a zip " * 200)
    for name in ("one", "two", "out"):
        (tmp_path / name).mkdir()
    monkeypatch.setattr(udisks, "program", lambda which=None: "/usr/bin/udisksctl")
    return Navigator(tmp_path, tmp_path / "out", terminal=FakeTerminal(100, 30)), tmp_path


def _toasts(app):
    from navml.widgets.toast import Toast

    return [child for child in app.root.children if isinstance(child, Toast)]


def _at_image(app):
    panel = app.manager.left
    panel.cursor = [entry.name for entry in panel.items].index("disk.iso")


def test_enter_on_an_image_mounts_it_and_goes_there(image_desk, monkeypatch):
    app, here = image_desk
    asked = []

    def attach(path, stop=None, uid=None):
        asked.append(path)
        return [udisks.UdisksVolume(name="DISK", device="/dev/loop7", local=str(here / "one"), loop="x")]

    monkeypatch.setattr(udisks, "attach_image", attach)
    said = []
    run_app(app, [_at_image, KeyEvent("enter"), Until(lambda a: a.manager.left.path == here / "one", timeout=5),
                  lambda a: said.extend((t.title, t.text) for t in _toasts(a))])
    assert asked == [here / "disk.iso"]
    assert said == [("disk.iso", f"Mounted at {here / 'one'}")]


def test_an_image_with_two_file_systems_asks_which_to_open(image_desk, monkeypatch):
    from navml.widgets.menu.popup_menu import PopupMenu

    app, here = image_desk
    said = []
    monkeypatch.setattr(udisks, "attach_image", lambda path, stop=None, uid=None: [
        udisks.UdisksVolume(name="boot", device="/dev/loop8p1", local=str(here / "one"), loop="x", size=1 << 30),
        udisks.UdisksVolume(name="data", device="/dev/loop8p2", local=str(here / "two"), loop="x"),
    ])
    run_app(app, [
        _at_image, KeyEvent("enter"), Until(lambda a: isinstance(a.modal, PopupMenu), timeout=5),
        lambda a: said.extend(t.text for t in _toasts(a)),
        KeyEvent("down"), KeyEvent("enter"), Until(lambda a: a.manager.left.path == here / "two", timeout=5),
    ])
    # Said before the box asks: Cancel there leaves both mounted.
    assert said == ["2 file systems mounted"]


@pytest.mark.parametrize("why", ["no udisksctl", "setting off"])
def test_without_udisks_or_with_the_setting_off_enter_opens_the_image_as_a_file(why, image_desk, monkeypatch):
    app, here = image_desk
    if why == "no udisksctl":
        monkeypatch.setattr(udisks, "program", lambda which=None: None)
    else:
        monkeypatch.setattr(SETTINGS.file_manager, "enter_mounts_images", False)
    monkeypatch.setattr(udisks, "attach_image", lambda *a, **k: pytest.fail("attached"))
    opened = []

    async def on_open_file(self, event):
        opened.append(event.path)
        return True

    monkeypatch.setattr("navigator.widgets.shell.shell.Shell.on_open_file", on_open_file)
    run_app(app, [_at_image, KeyEvent("enter"), Until(lambda a: opened, timeout=5)])
    assert opened == [here / "disk.iso"]


# -- Unmount image -----------------------------------------------------------------------


def test_image_mounts_are_found_in_proc_and_sysfs_partitions_and_all(tmp_path):
    block = tmp_path / "block"
    (block / "loop7" / "loop").mkdir(parents=True)
    (block / "loop7" / "loop" / "backing_file").write_text("/home/me/ubuntu.iso\n")
    (block / "loop8" / "loop").mkdir(parents=True)
    (block / "loop8" / "loop" / "backing_file").write_text("/home/me/sd card.img (deleted)\n")
    (block / "loop8" / "loop8p1").mkdir()
    (block / "loop8" / "loop8p1" / "partition").write_text("1\n")
    (block / "loop8p1").symlink_to(block / "loop8" / "loop8p1")
    (block / "loop3" / "loop").mkdir(parents=True)
    (block / "loop3" / "loop" / "backing_file").write_text("/var/lib/snapd/snaps/core_1.snap\n")
    mounts = ("/dev/nvme0n1p2 / ext4 rw 0 0\n"
              "/dev/loop3 /snap/core/1 squashfs ro 0 0\n"
              "/dev/loop7 /media/me/UBUNTU iso9660 ro 0 0\n"
              "/dev/loop8p1 /media/me/boot\\040part vfat ro 0 0\n")
    found = udisks.image_mounts(mounts, block)
    assert found == [
        udisks.ImageMount("/media/me/UBUNTU", "/dev/loop7", "/home/me/ubuntu.iso"),
        udisks.ImageMount("/media/me/boot part", "/dev/loop8p1", "/home/me/sd card.img"),
    ]
    assert udisks.image_at("/media/me/UBUNTU/casper", mounts, block) == found[:1]
    assert udisks.image_at("/home/me/sd card.img", mounts, block) == found[1:]
    assert udisks.image_at("/media/me/UBUNTUX", mounts, block) == []
    assert udisks.image_at("/snap/core/1", mounts, block) == []


@pytest.fixture
def mounted_image(image_desk, monkeypatch):
    """disk.iso mounted at ``mnt`` beside it, the left panel inside it."""
    app, here = image_desk
    mnt = here / "mnt"
    (mnt / "casper").mkdir(parents=True)
    mount = udisks.ImageMount(str(mnt), "/dev/loop7", str(here / "disk.iso"))
    monkeypatch.setattr(udisks, "image_at", lambda path, *a, **k: [mount] if str(path).startswith(
        (str(mnt), str(here / "disk.iso"))) else [])
    app.manager.left.path = mnt / "casper"
    return app, here


def test_the_context_menu_offers_unmount_in_a_mounted_image_and_on_it(mounted_image):
    from navigator.widgets.manager.commands import UnmountImage

    app, here = mounted_image
    seen = {}

    def look(name):
        def at(a):
            panel = a.manager.left
            seen[name] = panel.context_menu().item_for(UnmountImage) is not None
        return at

    def to_image(a):
        a.manager.left.go_to_file(here / "disk.iso")

    run_app(app, [look("inside"), to_image, Until(lambda a: a.manager.left.selected.name == "disk.iso"),
                  look("on it"), lambda a: setattr(a.manager.left, "cursor", 0), look("elsewhere")])
    assert seen == {"inside": True, "on it": True, "elsewhere": False}


def test_unmount_takes_the_panel_out_to_the_image_then_ejects_again_while_busy(mounted_image, monkeypatch):
    from navigator.widgets.manager.manager import manager as manager_module

    app, here = mounted_image
    monkeypatch.setattr(manager_module, "UNMOUNT_WAIT", 0.0)
    ejected = []

    def eject(where):
        ejected.append((where, app.manager.left.path))
        if len(ejected) == 1:
            raise OSError(5, "Error unmounting /dev/loop7: target is busy")

    monkeypatch.setattr(udisks, "eject", eject)
    said = []
    run_app(app, [
        lambda a: a.manager.spawn(a.manager.unmount_image(a.manager.left)),
        Until(lambda a: len(ejected) == 2 and _toasts(a), timeout=5),
        lambda a: said.extend((t.title, t.text) for t in _toasts(a)),
        Until(lambda a: a.manager.left.selected is not None and a.manager.left.selected.name == "disk.iso"),
    ])
    assert ejected == [("/dev/loop7", here), ("/dev/loop7", here)]
    assert said == [("disk.iso", "Unmounted")]


def test_an_unmount_refused_otherwise_is_said_in_a_box(mounted_image, monkeypatch):
    from navml.widgets.dialog.dialog import Dialog

    app, here = mounted_image
    calls = []

    def eject(where):
        calls.append(where)
        raise OSError(5, "Not authorized")

    monkeypatch.setattr(udisks, "eject", eject)
    seen = {}
    run_app(app, [
        lambda a: a.manager.spawn(a.manager.unmount_image(a.manager.left)),
        Until(lambda a: isinstance(a.modal, Dialog), timeout=5),
        lambda a: seen.update(prompt=a.modal.prompt),
        KeyEvent("enter"),
    ])
    assert calls == ["/dev/loop7"]
    assert seen["prompt"] == "Cannot unmount disk.iso: Not authorized"


def test_the_disk_menu_has_unmount_image_greyed_outside_one(mounted_image):
    from navigator.widgets.manager.commands import UnmountImage

    app, here = mounted_image
    seen = {}

    def look(name):
        def at(a):
            seen[name] = a.manager.enables(UnmountImage())
        return at

    run_app(app, [
        lambda a: seen.update(text=a.root.menu.disk.item_for(UnmountImage).text),
        look("inside"), lambda a: setattr(a.manager.left, "path", here / "one"),
        Until(lambda a: a.manager.left.path == here / "one"), look("outside"),
    ])
    assert seen["text"] == "~U~nmount image"
    assert seen["inside"] is True
    assert seen["outside"] is not True
