"""File > Encoding > Encryption: files encrypted and decrypted by gpg or age
(:mod:`navigator.lib.file_ops.encrypt`), on the disk and on another drive."""

from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.drives import Location, mount, unmount
from navigator.lib.drives.memory import MemoryDrive
from navigator.lib.file_ops import encrypt
from navigator.lib.file_ops.encrypt import EncryptJob, Options, Plan
from navigator.lib.system.job import Stopped
from navigator.settings import SETTINGS
from navigator.widgets.manager.commands import DecryptFiles, EncryptFiles

HAVE_GPG = encrypt.program("gpg") is not None
HAVE_AGE = encrypt.program("age") is not None and encrypt.program("age-keygen") is not None
needs_gpg = pytest.mark.skipif(not HAVE_GPG, reason="gpg is not installed")
needs_age = pytest.mark.skipif(not HAVE_AGE, reason="age is not installed")


# -- names and sniffing ------------------------------------------------------------------------------


def test_names_go_and_come_back():
    assert encrypt.encrypted_name("a.txt", "gpg", False) == "a.txt.gpg"
    assert encrypt.encrypted_name("a.txt", "gpg", True) == "a.txt.asc"
    assert encrypt.encrypted_name("a.txt", "age", True) == "a.txt.age"
    assert encrypt.plain_name("a.txt.gpg") == "a.txt"
    assert encrypt.plain_name("A.TXT.AGE") == "A.TXT"
    assert encrypt.plain_name("secret") == "secret.out"
    assert encrypt.suffix_tool(".gpg") is None


def test_the_program_is_told_by_the_first_bytes():
    assert encrypt.sniff(b"age-encryption.org/v1\n-> X25519 abc\n") == "age"
    assert encrypt.sniff(b"-----BEGIN AGE ENCRYPTED FILE-----\n") == "age"
    assert encrypt.sniff(b"-----BEGIN PGP MESSAGE-----\n") == "gpg"
    assert encrypt.sniff(bytes([0x8C, 0x0D])) == "gpg"         # old format, tag 3: a passphrase's session key
    assert encrypt.sniff(bytes([0xC1, 0x10])) == "gpg"         # new format, tag 1: a public key's
    assert encrypt.sniff(bytes([0x89, 0x01])) is None          # tag 2: a signature
    assert encrypt.sniff(b"plain text") is None


def test_an_asc_file_must_hold_a_message_not_a_signature():
    assert encrypt.tool_of("x.asc", b"-----BEGIN PGP MESSAGE-----\n") == "gpg"
    assert encrypt.tool_of("x.asc", b"-----BEGIN PGP SIGNATURE-----\n") is None
    assert encrypt.tool_of("x.gpg", b"anything") == "gpg"
    assert encrypt.tool_of("noname", b"age-encryption.org/v1\n") == "age"


def test_an_age_file_encrypted_to_a_passphrase_is_told_by_its_header():
    assert encrypt.age_wants_passphrase(b"age-encryption.org/v1\n-> scrypt salt 18\nbody\n")
    assert not encrypt.age_wants_passphrase(b"age-encryption.org/v1\n-> X25519 key\nbody\n")
    import base64

    armored = (b"-----BEGIN AGE ENCRYPTED FILE-----\n"
               + base64.b64encode(b"age-encryption.org/v1\n-> scrypt salt 18\nxxxxxxxxxxxxxxxx\n") + b"\n")
    assert encrypt.age_wants_passphrase(armored)


def test_gpg_keys_that_can_encrypt_are_listed():
    text = "\n".join([
        "tru::1:1700000000:0:3:1:5",
        "pub:u:255:22:AAAA1111:1700000000:::u:::scESC:::::ed25519:::0:",
        "fpr:::::::::FINGERPRINTAAAA1111:",
        "uid:u::::1700000000::HASH::Alice \\x3a A <alice@example.org>::::::::::0:",
        "sub:u:255:18:BBBB:1700000000::::::e:::::cv25519::",
        "pub:e:255:22:CCCC2222:1600000000:1650000000::u:::scESC:::::ed25519:::0:",
        "fpr:::::::::FINGERPRINTCCCC2222:",
        "uid:e::::1600000000::HASH::Expired <old@example.org>::::::::::0:",
        "pub:u:255:22:DDDD3333:1700000000:::u:::scSC:::::ed25519:::0:",
        "fpr:::::::::FINGERPRINTDDDD3333:",
        "uid:u::::1700000000::HASH::Signs only <s@example.org>::::::::::0:",
    ])
    assert encrypt.gpg_keys(text) == [("FINGERPRINTAAAA1111", "Alice : A <alice@example.org>")]


def test_a_passphrase_is_never_on_the_command_line():
    options = Options(tool="gpg", method="passphrase", passphrase="hunter2", armor=True)
    args = encrypt.gpg_encrypt_args(options, "a.txt", 7)
    assert "hunter2" not in args and args[args.index("--passphrase-fd") + 1] == "7"
    assert "--symmetric" in args and "--armor" in args and "--no-symkey-cache" in args
    assert "hunter2" not in encrypt.age_encrypt_args(Options(tool="age", passphrase="hunter2"), True)
    recipients = encrypt.gpg_encrypt_args(Options(method="recipients", recipients=["A", "B"]), "a", None)
    assert recipients.count("--recipient") == 2 and "--passphrase-fd" not in recipients


def test_gpg_status_lines_say_what_went_wrong():
    need = "[GNUPG:] NEED_PASSPHRASE_SYM 9 3 10\ngpg: Sorry, we are in batchmode - can't get input\n"
    assert isinstance(encrypt.gpg_outcome(need, False), encrypt.NeedsPassphrase)
    bad = "[GNUPG:] ERROR symkey_decrypt.maybe_error 11_BAD_PASSPHRASE\ngpg: decryption failed: Bad session key\n"
    assert isinstance(encrypt.gpg_outcome(bad, True), encrypt.BadPassphrase)
    junk = "gpg: no valid OpenPGP data found.\n[GNUPG:] NODATA 1\ngpg: decrypt_message failed: Unknown system error\n"
    outcome = encrypt.gpg_outcome(junk, False)
    assert isinstance(outcome, encrypt.ToolError) and outcome.args[0] == "decrypt_message failed: Unknown system error"


# -- running a program ---------------------------------------------------------------------------------


def test_a_stop_kills_the_program_and_leaves_no_target(tmp_path):
    source = tmp_path / "big"
    source.write_bytes(os.urandom(1 << 20))
    plan = Plan(Location.of(source), Location.of(tmp_path / "big.out"), 1 << 20, "gpg")
    job = EncryptJob()
    threading.Timer(0.3, job.stop).start()
    started = time.monotonic()
    with pytest.raises(Stopped):
        encrypt.run_filter(["sh", "-c", "sleep 10; cat"], plan, job)
    assert time.monotonic() - started < 5
    assert not (tmp_path / "big.out").exists()


def test_a_failing_program_says_why_and_leaves_no_target(tmp_path):
    (tmp_path / "a").write_text("x")
    plan = Plan(Location.of(tmp_path / "a"), Location.of(tmp_path / "a.out"), 1, "gpg")
    with pytest.raises(encrypt.ToolError) as caught:
        encrypt.run_filter(["sh", "-c", "cat >/dev/null; echo broken >&2; exit 3"], plan, EncryptJob())
    assert "broken" in caught.value.args[0]
    assert not (tmp_path / "a.out").exists()


# -- gpg -----------------------------------------------------------------------------------------------


@pytest.fixture
def gnupg(tmp_path_factory, monkeypatch):
    home = tmp_path_factory.mktemp("gnupg")
    home.chmod(0o700)
    monkeypatch.setenv("GNUPGHOME", str(home))
    yield home
    subprocess.run(["gpgconf", "--kill", "all"], capture_output=True, check=False)


@pytest.fixture
def tree(tmp_path):
    here = tmp_path / "files"
    (here / "d").mkdir(parents=True)
    (here / "a.txt").write_text("alpha\n")
    (here / "d" / "b.bin").write_bytes(os.urandom(200_000))
    return here


def _strip(plans):
    """Each source moved aside, so decrypting writes where it was."""
    for plan in plans:
        path = Path(str(plan.source.path))
        path.rename(path.with_name(path.name + ".orig"))


@needs_gpg
def test_gpg_passphrase_round_trip_asks_once_and_refuses_a_wrong_one(gnupg, tree):
    job = EncryptJob()
    options = Options(tool="gpg", passphrase="pw")
    plans = encrypt.plan_encrypt([Location.of(tree)], options, job)
    assert sorted(plan.target.name for plan in plans) == ["a.txt.gpg", "b.bin.gpg"]
    done = encrypt.encrypt(plans, options, job)
    assert len(done) == 2 and not job.errors
    _strip(done)
    job = EncryptJob()
    decrypting = encrypt.plan_decrypt([Location.of(tree)], job)
    assert sorted(plan.target.name for plan in decrypting) == ["a.txt", "b.bin"]
    assert encrypt.decrypt(decrypting, Options(), job) == [] and len(job.needs_passphrase) == 2
    assert encrypt.decrypt(job.needs_passphrase, Options(passphrase="nope"), job) == []
    assert len(job.bad_passphrase) == 2
    assert len(encrypt.decrypt(job.bad_passphrase, Options(passphrase="pw"), job)) == 2 and not job.errors
    assert (tree / "a.txt").read_text() == "alpha\n"
    assert (tree / "d" / "b.bin").read_bytes() == (tree / "d" / "b.bin.orig").read_bytes()


@needs_gpg
def test_gpg_recipients_decrypt_with_no_passphrase_and_armor_writes_asc(gnupg, tree):
    subprocess.run(["gpg", "--batch", "--pinentry-mode", "loopback", "--passphrase", "", "--quick-gen-key",
                    "Test <test@example.org>", "default", "default", "never"], capture_output=True, check=True)
    keys = encrypt.list_gpg_keys()
    assert len(keys) == 1 and keys[0][1] == "Test <test@example.org>"
    options = Options(tool="gpg", method="recipients", recipients=[keys[0][0]], armor=True)
    job = EncryptJob()
    plans = encrypt.plan_encrypt([Location.of(tree / "a.txt")], options, job)
    done = encrypt.encrypt(plans, options, job)
    assert not job.errors and (tree / "a.txt.asc").read_bytes().startswith(encrypt.PGP_ARMOR)
    _strip(done)
    job = EncryptJob()
    assert len(encrypt.decrypt(encrypt.plan_decrypt([Location.of(tree / "a.txt.asc")], job), Options(), job)) == 1
    assert not job.needs_passphrase and (tree / "a.txt").read_text() == "alpha\n"


@pytest.fixture
def memory():
    drive = mount(MemoryDrive("crypt"))
    drive.make("/files/one.txt", "first")
    yield drive
    unmount(drive.site)


@needs_gpg
def test_files_on_another_drive_are_streamed_through_it(gnupg, memory):
    base = memory.location("/files")
    options = Options(tool="gpg", passphrase="pw")
    job = EncryptJob()
    done = encrypt.encrypt(encrypt.plan_encrypt([base / "one.txt"], options, job), options, job)
    assert [plan.target.name for plan in done] == ["one.txt.gpg"] and not job.errors
    memory.unlink(base / "one.txt")
    job = EncryptJob()
    done = encrypt.decrypt(encrypt.plan_decrypt([base / "one.txt.gpg"], job), Options(passphrase="pw"), job)
    assert len(done) == 1 and not job.errors
    with memory.open_read(base / "one.txt") as handle:
        assert handle.read() == b"first"


@needs_gpg
def test_delete_originals_removes_only_what_was_written(gnupg, tree):
    options = Options(tool="gpg", passphrase="pw")
    job = EncryptJob()
    plans = encrypt.plan_encrypt([Location.of(tree)], options, job)
    (tree / "d" / "b.bin.gpg").mkdir()     # nowhere to write this one
    done = encrypt.encrypt(plans, options, job)
    assert [plan.source.name for plan in done] == ["a.txt"] and len(job.errors) == 1
    encrypt.remove_originals(done, job)
    assert not (tree / "a.txt").exists() and (tree / "d" / "b.bin").exists()


# -- age -----------------------------------------------------------------------------------------------


@needs_age
def test_age_recipients_round_trip(tmp_path, tree):
    identity = tmp_path / "keys.txt"
    subprocess.run(["age-keygen", "-o", str(identity)], capture_output=True, check=True)
    public = next(line.split(": ", 1)[1] for line in identity.read_text().splitlines()
                  if line.startswith("# public key: "))
    options = Options(tool="age", method="recipients", recipients=[public])
    job = EncryptJob()
    done = encrypt.encrypt(encrypt.plan_encrypt([Location.of(tree / "a.txt")], options, job), options, job)
    assert not job.errors
    _strip(done)
    job = EncryptJob()
    plans = encrypt.plan_decrypt([Location.of(tree / "a.txt.age")], job)
    assert len(encrypt.decrypt(plans, Options(identities=[str(identity)]), job)) == 1, job.errors
    assert (tree / "a.txt").read_text() == "alpha\n"


@needs_age
def test_age_passphrase_round_trip(tree):
    options = Options(tool="age", passphrase="pw")
    job = EncryptJob()
    done = encrypt.encrypt(encrypt.plan_encrypt([Location.of(tree / "a.txt")], options, job), options, job)
    assert not job.errors, job.errors
    _strip(done)
    job = EncryptJob()
    plans = encrypt.plan_decrypt([Location.of(tree / "a.txt.age")], job)
    assert plans[0].passphrase
    assert encrypt.decrypt(plans, Options(), job) == [] and len(job.needs_passphrase) == 1
    assert encrypt.decrypt(plans, Options(passphrase="wrong"), job) == [] and len(job.bad_passphrase) == 1
    assert len(encrypt.decrypt(plans, Options(passphrase="pw"), job)) == 1, job.errors
    assert (tree / "a.txt").read_text() == "alpha\n"


# -- the file manager ----------------------------------------------------------------------------------


@pytest.fixture
def place(tree, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    return tree


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def test_the_commands_are_greyed_without_gpg_or_age(place, monkeypatch):
    monkeypatch.setattr("navigator.lib.file_ops.encrypt.shutil.which", lambda name: None)
    app = navigator(place)
    seen = {}

    def look(a):
        seen["encrypt"] = a.manager.refusal(EncryptFiles())
        seen["decrypt"] = a.manager.refusal(DecryptFiles())

    run_app(app, [look])
    assert seen == {"encrypt": "Neither gpg nor age is installed", "decrypt": "Neither gpg nor age is installed"}


@needs_gpg
def test_decrypt_waits_for_an_encrypted_file(place):
    app = navigator(place)
    seen = {}

    def look(a):
        panel = a.manager.left
        panel.cursor = [entry.name for entry in panel.items].index("a.txt")
        seen["encrypt"] = a.manager.enables(EncryptFiles())
        seen["decrypt"] = a.manager.refusal(DecryptFiles())

    run_app(app, [look])
    assert seen == {"encrypt": True, "decrypt": "No encrypted file is tagged or at the cursor"}


def _fill(passphrase: str, confirm: str | None = None):
    def fill(a):
        dialog = a.modal
        dialog.tool.value = 0
        dialog.method.value = 0
        dialog.passphrase.value = passphrase
        dialog.confirm.value = passphrase if confirm is None else confirm
    return fill


@needs_gpg
def test_encrypt_writes_beside_each_file_keeps_them_and_untags(gnupg, place):
    app = navigator(place)
    seen = {}

    def start(a):
        a.manager.left.marked = frozenset({"a.txt", "d"})
        a.manager.spawn(a.manager.encrypt_files(a.manager.left))

    run_app(app, [start, Until(lambda a: a.modal is not None),
                  lambda a: seen.update(title=a.modal.title), _fill("pw"), KeyEvent("enter"),
                  Until(lambda a: (place / "d" / "b.bin.gpg").exists() and not a.manager.left.marked, timeout=10)])
    assert seen["title"] == "Encrypt Files"
    assert (place / "a.txt.gpg").exists() and (place / "a.txt").exists() and (place / "d" / "b.bin").exists()
    assert SETTINGS.encryption.tool == "gpg" and SETTINGS.encryption.method == "passphrase"
    assert "pw" not in vars(SETTINGS.encryption).values()


def left_on(name: str):
    return Until(lambda a: a.manager.left.selected is not None and a.manager.left.selected.name == name, timeout=10)


@needs_gpg
def test_encrypt_and_decrypt_put_the_cursor_on_what_they_wrote(gnupg, place):
    """As F5 lands on what it made: ``a.txt.gpg`` after Encrypt, and -- the
    original moved aside -- ``a.txt`` again after Decrypt."""
    app = navigator(place)
    seen = {}

    def on(name):
        def act(a):
            panel = a.manager.left
            panel.cursor = [entry.name for entry in panel.items].index(name)
        return act

    def answer(a):
        a.modal.entry.value = "pw"

    run_app(app, [
        on("a.txt"), lambda a: a.manager.spawn(a.manager.encrypt_files(a.manager.left)),
        Until(lambda a: a.modal is not None), _fill("pw"), KeyEvent("enter"),
        Until(lambda a: (place / "a.txt.gpg").exists()), left_on("a.txt.gpg"),
        lambda a: seen.update(encrypted=a.manager.left.selected.name),
        lambda a: (place / "a.txt").rename(place / "a.txt.orig"), KeyEvent("r", ctrl=True),
        Until(lambda a: "a.txt.orig" in [entry.name for entry in a.manager.left.items]),
        on("a.txt.gpg"), lambda a: a.manager.spawn(a.manager.decrypt_files(a.manager.left)),
        Until(lambda a: a.modal is not None and a.modal.title == "Passphrase", timeout=10), answer, KeyEvent("enter"),
        Until(lambda a: (place / "a.txt").exists(), timeout=10), left_on("a.txt"),
        lambda a: seen.update(decrypted=a.manager.left.selected.name),
    ])
    assert seen == {"encrypted": "a.txt.gpg", "decrypted": "a.txt"}


@needs_gpg
def test_mismatched_passphrases_keep_the_dialog_up(gnupg, place):
    app = navigator(place)
    seen = {}

    def start(a):
        a.manager.left.cursor = [entry.name for entry in a.manager.left.items].index("a.txt")
        a.manager.spawn(a.manager.encrypt_files(a.manager.left))

    def look(a):
        seen.update(title=a.modal.title, prompt=a.modal.prompt)

    run_app(app, [start, Until(lambda a: a.modal is not None), _fill("pw", "pX"), KeyEvent("enter"),
                  Until(lambda a: a.modal is not None and a.modal.title == "Error"), look,
                  KeyEvent("enter"), Until(lambda a: a.modal is not None and a.modal.title == "Encrypt Files"),
                  KeyEvent("escape")])
    assert seen == {"title": "Error", "prompt": "The passphrases do not match."}
    assert not (place / "a.txt.gpg").exists()


@needs_gpg
def test_delete_originals_and_the_overwrite_question(gnupg, place):
    (place / "a.txt.gpg").write_text("old")
    app = navigator(place)
    seen = {}

    def start(a):
        a.manager.left.cursor = [entry.name for entry in a.manager.left.items].index("a.txt")
        a.manager.spawn(a.manager.encrypt_files(a.manager.left))

    def fill(a):
        _fill("pw")(a)
        a.modal.options.value = 2

    run_app(app, [start, Until(lambda a: a.modal is not None), fill, KeyEvent("enter"),
                  Until(lambda a: a.modal is not None and a.modal.title == "Warning"),
                  lambda a: seen.update(prompt=a.modal.prompt), KeyEvent("enter"),
                  Until(lambda a: not (place / "a.txt").exists(), timeout=10)])
    assert seen["prompt"] == "1 file already exists.\nOK to overwrite it?"
    assert (place / "a.txt.gpg").read_bytes() != b"old"


@needs_gpg
def test_decrypt_asks_the_passphrase_once_for_every_file(gnupg, place):
    options = Options(tool="gpg", passphrase="pw")
    job = EncryptJob()
    _strip(encrypt.encrypt(encrypt.plan_encrypt([Location.of(place)], options, job), options, job))
    app = navigator(place)
    seen = {}

    def start(a):
        a.manager.left.marked = frozenset({"a.txt.gpg", "d"})
        a.manager.spawn(a.manager.decrypt_files(a.manager.left))

    def answer(a):
        seen.update(title=a.modal.title, prompt=a.modal.prompt)
        a.modal.entry.value = "pw"

    run_app(app, [start, Until(lambda a: a.modal is not None and a.modal.title == "Passphrase", timeout=10), answer,
                  KeyEvent("enter"),
                  Until(lambda a: (place / "d" / "b.bin").exists() and not a.manager.left.marked, timeout=10)])
    assert seen == {"title": "Passphrase", "prompt": "2 files need a passphrase:"}
    assert (place / "a.txt").read_text() == "alpha\n" and (place / "a.txt.gpg").exists()
