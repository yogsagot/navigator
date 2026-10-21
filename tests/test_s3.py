"""The S3 drive (``navigator/lib/drives/s3.py``) against moto's S3 server in a
thread, reached as an endpoint of its own over plain HTTP (``s3+http``,
path-style, as MinIO is): the credentials, the buckets at the root,
prefixes as directories, copying both ways -- past a part, so a multipart
upload -- erasing, renaming, ranged reads, and Utilities > S3 link."""

from __future__ import annotations

import os
from pathlib import PurePosixPath

import pytest

moto_server = pytest.importorskip("moto.server")

from conftest import FakeTerminal, Until, run_app  # noqa: E402
from navkit.events import KeyEvent  # noqa: E402
from navigator.lib.drives import Location, Site, drive_of, s3  # noqa: E402
from navigator.lib.drives.sessions import SESSIONS, Answers, NeedPassword  # noqa: E402
from navigator.lib.file_ops.fileerase import ALL, EraseJob, EraseRequest, run as erase_run  # noqa: E402
from navigator.lib.file_ops.filecopy import MOVE, OVERWRITE, PRESERVE, CopyJob, CopyRequest, run as copy_run  # noqa: E402


@pytest.fixture(scope="module")
def endpoint():
    server = moto_server.ThreadedMotoServer(ip_address="127.0.0.1", port=0, verbose=False)
    server.start()
    yield server.get_host_and_port()
    server.stop()


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """No ~/.aws and no keyring of the user's own; the environment's keys moto takes."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    for name in ("AWS_PROFILE", "AWS_DEFAULT_PROFILE", "AWS_SESSION_TOKEN", "AWS_REGION", "AWS_DEFAULT_REGION"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setattr("navigator.lib.drives.credentials.keyring_available", lambda: False)
    return home


@pytest.fixture
def drive(endpoint, isolated):
    host, port = endpoint
    site = Site("s3+http", "", host, port)
    found = SESSIONS.connect(site, Answers())
    bucket = f"b{os.urandom(4).hex()}"
    found.mkdir(at(found, f"/{bucket}"))
    found.test_bucket = bucket
    yield found
    SESSIONS.close_all()


def at(drive, path: str) -> Location:
    return Location(drive.site, PurePosixPath(path))


def test_a_location_names_its_endpoint_and_transport():
    place = Location.parse("s3+http://minio.local:9000/photos/2024")
    assert place.site == Site("s3+http", "", "minio.local", 9000) and str(place.path) == "/photos/2024"
    assert str(Location.parse("s3://AKIA1@s3.amazonaws.com/b/k")) == "s3://AKIA1@s3.amazonaws.com/b/k"
    assert s3.is_aws("s3.amazonaws.com") and s3.is_aws("s3.eu-west-1.amazonaws.com")
    assert not s3.is_aws("minio.local")


def test_an_access_key_has_its_secret_asked_for(endpoint, isolated):
    host, port = endpoint
    site = Site("s3+http", "AKIATEST", host, port)
    answers = Answers()
    with pytest.raises(NeedPassword) as needed:
        SESSIONS.connect(site, answers)
    assert needed.value.user == "AKIATEST" and not needed.value.wrong
    answers.password = "secret"
    try:
        connected = SESSIONS.connect(site, answers)
        assert drive_of(Location(site, PurePosixPath("/"))) is connected
    finally:
        SESSIONS.close_all()


def test_a_secret_the_endpoint_refuses_is_asked_again(endpoint, isolated, monkeypatch):
    from botocore.exceptions import ClientError

    class Refusing:
        def list_buckets(self, **kwargs):
            raise ClientError({"Error": {"Code": "InvalidAccessKeyId", "Message": "no such key"}}, "ListBuckets")

        def close(self):
            pass

    monkeypatch.setattr(s3, "make_client", lambda *args: Refusing())
    host, port = endpoint
    with pytest.raises(NeedPassword) as needed:
        SESSIONS.connect(Site("s3+http", "AKIATEST", host, port), Answers(password="wrong"))
    assert needed.value.wrong


def test_the_root_lists_buckets_and_prefixes_are_directories(drive):
    bucket = drive.test_bucket
    assert bucket in drive.names(at(drive, "/"))
    drive.mkdir(at(drive, f"/{bucket}/docs"))
    with drive.open_write(at(drive, f"/{bucket}/docs/a.txt")) as writer:
        writer.write(b"alpha")
    entries, error, _ = drive.scan(at(drive, f"/{bucket}"), True, "name", free=False)
    assert error is None and [(e.name, e.is_dir) for e in entries] == [("..", True), ("docs", True)]
    assert drive.names(at(drive, f"/{bucket}/docs")) == ["a.txt"]  # the marker not among them
    assert drive.stat(at(drive, f"/{bucket}/docs/a.txt")).st_size == 5
    with pytest.raises(FileNotFoundError):
        drive.stat(at(drive, f"/{bucket}/nothing"))
    assert drive.get_dir(at(drive, f"/{bucket}/docs")) == f"S3:{drive.site.host}:/{bucket}/docs"
    assert drive.open_random(at(drive, f"/{bucket}/docs/a.txt")).read_at(1, 3) == b"lph"


def test_copies_go_both_ways_a_big_file_in_parts(drive, tmp_path, monkeypatch):
    monkeypatch.setattr(s3, "PART_SIZE", 5 * 1024 * 1024)
    bucket = drive.test_bucket
    here = tmp_path / "here"
    (here / "tree" / "sub").mkdir(parents=True)
    (here / "tree" / "sub" / "b.txt").write_text("beta")
    big = os.urandom(11 * 1024 * 1024)
    (here / "tree" / "big.bin").write_bytes(big)
    target = at(drive, f"/{bucket}")
    done = copy_run(CopyRequest([here / "tree"], str(target) + "/", OVERWRITE, PRESERVE), CopyJob(), here)
    assert done == [here / "tree"]
    assert sorted(drive.names(at(drive, f"/{bucket}/tree"))) == ["big.bin", "sub"]
    back = tmp_path / "back"
    back.mkdir()
    copy_run(CopyRequest([at(drive, f"/{bucket}/tree")], str(back), OVERWRITE, PRESERVE), CopyJob(), back)
    assert (back / "tree" / "big.bin").read_bytes() == big
    assert (back / "tree" / "sub" / "b.txt").read_text() == "beta"
    erase_run(EraseRequest([at(drive, f"/{bucket}/tree")]), EraseJob(asker=lambda question: ALL))
    assert drive.names(at(drive, f"/{bucket}")) == []


def test_a_failed_write_leaves_nothing(drive):
    bucket = drive.test_bucket
    with pytest.raises(RuntimeError):
        with drive.open_write(at(drive, f"/{bucket}/half")) as writer:
            writer.write(b"half")
            raise RuntimeError
    assert not drive.exists(at(drive, f"/{bucket}/half"))
    with pytest.raises(OSError):
        drive.open_write(at(drive, f"/{bucket}/x"), append=True)


def test_a_file_renames_on_the_server_and_a_directory_moves_by_copying(drive, tmp_path):
    import errno

    bucket = drive.test_bucket
    drive.mkdir(at(drive, f"/{bucket}/d"))
    with drive.open_write(at(drive, f"/{bucket}/d/f.txt")) as writer:
        writer.write(b"f")
    drive.rename(at(drive, f"/{bucket}/d/f.txt"), at(drive, f"/{bucket}/g.txt"))
    assert drive.names(at(drive, f"/{bucket}")) == ["d", "g.txt"]
    with pytest.raises(OSError) as refused:
        drive.rename(at(drive, f"/{bucket}/d"), at(drive, f"/{bucket}/e"))
    assert refused.value.errno == errno.EXDEV
    # F6's move: the copier copies and deletes what EXDEV refused.
    request = CopyRequest([at(drive, f"/{bucket}/d")], str(at(drive, f"/{bucket}/e")), OVERWRITE, PRESERVE | MOVE)
    copy_run(request, CopyJob(), tmp_path)
    assert drive.names(at(drive, f"/{bucket}")) == ["e", "g.txt"]
    with pytest.raises(OSError) as busy:
        drive.rmdir(at(drive, f"/{bucket}"))
    assert busy.value.errno == errno.ENOTEMPTY


def test_utilities_s3_link_sends_the_panel_into_a_bucket(endpoint, isolated, tmp_path, monkeypatch):
    from navigator.__main__ import Navigator
    from navigator.widgets.shell.commands import S3Link

    host, port = endpoint
    setup = SESSIONS.connect(Site("s3+http", "", host, port), Answers())
    setup.mkdir(Location(setup.site, PurePosixPath("/panel-bucket")))
    with setup.open_write(Location(setup.site, PurePosixPath("/panel-bucket/a.txt"))) as writer:
        writer.write(b"a")
    SESSIONS.close_all()
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    here = tmp_path / "here"
    here.mkdir()
    app = Navigator(here, here, terminal=FakeTerminal(100, 30))
    seen = {}

    def fill(a):
        seen.update(title=a.modal.title, endpoint=a.modal.host.value, tls=a.modal.secure.value)
        a.modal.host.value = f"{host}:{port}"
        a.modal.secure.value = 0
        a.modal.directory.value = "panel-bucket"

    try:
        run_app(app, [
            lambda a: a.spawn(a.run_command(S3Link)), Until(lambda a: type(a.modal).__name__ == "ConnectDialog"),
            fill, KeyEvent("enter"),
            Until(lambda a: [e.name for e in a.manager.left.items] == ["..", "a.txt"], timeout=10),
            lambda a: seen.update(where=a.manager.left.title_location),
        ], timeout=30)
    finally:
        SESSIONS.close_all()
    assert seen["title"] == "S3 link (Amazon S3)" and seen["endpoint"] == "s3.amazonaws.com" and seen["tls"] == 1
    assert seen["where"] == f"S3:{host}:/panel-bucket"
