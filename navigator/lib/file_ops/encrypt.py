"""File > Encryption: the tagged files encrypted, and decrypted again, by
GnuPG's ``gpg`` or by ``age`` -- **a departure, asked for**: DOS Navigator
encrypted nothing.

Each file is written beside itself: ``name.gpg`` (``name.asc`` armored) or
``name.age``, and back to ``name``.  A tagged directory is walked to the bottom,
as Checksums walk one (:func:`navigator.lib.file_ops.checksum.walk`).

**Nothing goes through a temporary file.**  The file is read through its drive
and fed to the program's standard input on a second thread, and its standard
output written through the target's drive, so encrypting works as well on a
server or in an archive as on the disk, and nothing in the clear is left in
``/tmp``.

**A passphrase never goes on a command line or in the environment.**  gpg reads
it from a pipe of its own (``--passphrase-fd``, with ``--pinentry-mode
loopback`` so no pinentry fights Navigator for the terminal).  ``age`` reads one
only from ``/dev/tty``; ``age-plugin-batchpass`` (age 1.3) reads it from a pipe
named by ``AGE_PASSPHRASE_FD``, and without it ``age`` is started on a private
pty made its controlling terminal, whose prompts are answered from here.  Every
child is started in a session of its own, so neither can ever open the
terminal Navigator is drawing on.

gpg's passphrase cache is not used (``--no-symkey-cache``): a passphrase typed
into Navigator is not to go on unlocking files in other programs afterwards.
Decrypting tries each file without a passphrase first -- a public-key file's
secret key may be unlocked in the agent already -- and says which wanted one,
so the loop asks once for all of them.

Nothing here may run on the loop.
"""

from __future__ import annotations

import base64
import fcntl
import os
import select
import shutil
import subprocess
import termios
import threading
from dataclasses import dataclass, field
from typing import IO, Any, Callable, Iterable

from navigator.lib.drives import Location, drive_of
from navigator.lib.file_ops import checksum
from navigator.lib.system.job import Job, Stopped

TOOLS = ("gpg", "age")

#: The package to install for each program, as a greyed command says it.
PACKAGES = {"gpg": "gnupg", "age": "age"}

#: Every name ending Decrypt takes, and the program it means.
ENCRYPTED_SUFFIXES = {".gpg": "gpg", ".pgp": "gpg", ".asc": "gpg", ".age": "age"}

CHUNK = 1 << 16

#: How much of a file the sniffing reads.
HEAD = 4096

#: The reasons a decryption gives, translated where they are shown.
BAD_PASSPHRASE = "wrong passphrase"
NO_IDENTITY = "no age identity file: set age_identities in navigator.ini's [encryption]"
NO_SECRET_KEY = "no secret key for it"

AGE_MAGIC = b"age-encryption.org/v1"
AGE_ARMOR = b"-----BEGIN AGE ENCRYPTED FILE-----"
PGP_ARMOR = b"-----BEGIN PGP MESSAGE-----"

GPG_BASE = ("--batch", "--yes", "--no-tty", "--status-fd", "2", "--pinentry-mode", "loopback", "--no-symkey-cache")


def program(tool: str, which: Callable[[str], str | None] | None = None) -> str | None:
    """*tool*'s command, or None.  ``shutil.which`` is looked up at the call,
    as :mod:`navigator.lib.system.printing` does, so the tests can replace it."""
    return (which or shutil.which)(tool)


def batchpass(which: Callable[[str], str | None] | None = None) -> str | None:
    """``age-plugin-batchpass``, which takes a passphrase from a pipe, or None."""
    return (which or shutil.which)("age-plugin-batchpass")


def available() -> tuple[str, ...]:
    """The programs installed, in :data:`TOOLS`' order."""
    return tuple(tool for tool in TOOLS if program(tool) is not None)


def encrypted_name(name: str, tool: str, armor: bool) -> str:
    """What *name* is called encrypted by *tool*."""
    if tool == "age":
        return name + ".age"
    return name + (".asc" if armor else ".gpg")


def suffix_tool(name: str) -> str | None:
    """The program *name*'s ending says encrypted it, or None."""
    lower = name.lower()
    for suffix, tool in ENCRYPTED_SUFFIXES.items():
        if lower.endswith(suffix) and len(lower) > len(suffix):
            return tool
    return None


def plain_name(name: str) -> str:
    """*name* decrypted: without its ending, or with ``.out`` for one it does not have."""
    if suffix_tool(name) is not None:
        return name[:name.rfind(".")]
    return name + ".out"


def sniff(head: bytes) -> str | None:
    """The program the first bytes of a file say encrypted it, or None.  An
    OpenPGP packet is told by its tag: a session key (1, 3) or encrypted data
    (9, 18, 20) -- not a signature or a key, which ``.asc`` files also hold."""
    stripped = head.lstrip()
    if stripped.startswith(AGE_MAGIC) or stripped.startswith(AGE_ARMOR):
        return "age"
    if stripped.startswith(PGP_ARMOR):
        return "gpg"
    if head and head[0] & 0x80:
        tag = head[0] & 0x3F if head[0] & 0x40 else (head[0] >> 2) & 0x0F
        if tag in (1, 3, 9, 18, 20):
            return "gpg"
    return None


def tool_of(name: str, head: bytes) -> str | None:
    """The program that decrypts the file *name* beginning with *head*: by its
    ending, else by its bytes.  ``.asc`` must hold a PGP message, not a
    signature or a key."""
    by_name = suffix_tool(name)
    if by_name is not None and not name.lower().endswith(".asc"):
        return by_name
    return sniff(head)


def age_wants_passphrase(head: bytes) -> bool:
    """Whether the age file beginning with *head* was encrypted to a
    passphrase: its header holds an ``scrypt`` stanza."""
    stripped = head.lstrip()
    if stripped.startswith(AGE_ARMOR):
        body = b"".join(stripped[len(AGE_ARMOR):].split()[:8])
        try:
            stripped = base64.b64decode(body[:len(body) // 4 * 4] or b"", validate=False)
        except ValueError:
            return False
    return b"\n-> scrypt " in stripped


def gpg_keys(text: str) -> list[tuple[str, str]]:
    """``(fingerprint, user ID)`` of every key in ``gpg --list-keys
    --with-colons`` *text* that can encrypt now -- not expired, revoked or
    disabled, and with an ``e`` among its capabilities."""
    keys: list[tuple[str, str]] = []
    usable = False
    fingerprint = ""
    uid = ""

    def close() -> None:
        if usable and fingerprint:
            keys.append((fingerprint, uid))

    for line in text.splitlines():
        fields = line.split(":")
        kind = fields[0]
        if kind == "pub":
            close()
            validity = fields[1] if len(fields) > 1 else ""
            capabilities = fields[11] if len(fields) > 11 else ""
            usable = validity not in ("e", "r", "d", "i") and "E" in capabilities
            fingerprint = uid = ""
        elif kind == "fpr" and not fingerprint:
            fingerprint = fields[9] if len(fields) > 9 else ""
        elif kind == "uid" and not uid:
            uid = fields[9].replace("\\x3a", ":") if len(fields) > 9 else ""
    close()
    return keys


def list_gpg_keys() -> list[tuple[str, str]]:
    """The keys gpg can encrypt to (on a thread)."""
    command = program("gpg")
    if command is None:
        return []
    try:
        result = subprocess.run([command, "--batch", "--no-tty", "--with-colons", "--list-keys"],
                                capture_output=True, timeout=30, start_new_session=True,
                                stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return []
    return gpg_keys(result.stdout.decode("utf-8", "replace"))


def default_identities() -> list[str]:
    """Where an age identity is kept when none is set: ``age/keys.txt`` under
    ``$XDG_CONFIG_HOME``, where sops and most guides put one, if it is there."""
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    path = os.path.join(base, "age", "keys.txt")
    return [path] if os.path.isfile(path) else []


@dataclass
class Options:
    """What to encrypt with, or decrypt with."""

    tool: str = "gpg"
    #: ``"passphrase"`` or ``"recipients"`` (encrypting only).
    method: str = "passphrase"
    passphrase: str | None = None
    #: gpg key IDs or fingerprints; age's ``age1...`` keys, or files of them.
    recipients: list[str] = field(default_factory=list)
    armor: bool = False
    #: age identity files, for decrypting.
    identities: list[str] = field(default_factory=list)


class EncryptJob(Job):
    """Files being encrypted or decrypted, as the checksums box shows them:
    the one being read, the bytes read of them all, and how many are done."""

    def __init__(self) -> None:
        super().__init__()
        self.current = ""
        self.position = 0
        self.total = 0
        self.files_done = 0
        self.files_total = 0
        #: ``(name, reason)`` for every file that could not be done.
        self.errors: list[tuple[str, str]] = []
        #: Decrypting: the plans that wanted a passphrase none was given for...
        self.needs_passphrase: list[Plan] = []
        #: ... and those the passphrase given did not open.
        self.bad_passphrase: list[Plan] = []


@dataclass
class Plan:
    """One file to do: from where to where, its size, and the program."""

    source: Location
    target: Location
    size: int
    tool: str
    #: An age file encrypted to a passphrase.
    passphrase: bool = False


class ToolError(Exception):
    """The program failed; ``args[0]`` says why."""


class NeedsPassphrase(Exception):
    """gpg wanted a passphrase none was given for."""


class BadPassphrase(Exception):
    """The passphrase given did not open the file."""


def _reason(error: OSError) -> str:
    return error.strerror or str(error)


# -- planning ----------------------------------------------------------------------------------------


def plan_encrypt(sources: Iterable[Location], options: Options, job: EncryptJob) -> list[Plan]:
    """Every file *sources* name, a directory's to the bottom, with where its
    encrypted copy goes -- leaving out files already encrypted."""
    files = checksum.walk(sources, job, lambda location: suffix_tool(location.name) is not None)
    return [Plan(location, location.parent / encrypted_name(location.name, options.tool, options.armor),
                 size, options.tool) for location, size in files]


def _head(location: Location) -> bytes:
    with drive_of(location).open_read(location) as handle:
        return handle.read(HEAD)


def plan_decrypt(sources: Iterable[Location], job: EncryptJob) -> list[Plan]:
    """Every encrypted file *sources* name: a tagged file told by its ending or
    its first bytes, a directory's files by their endings (each confirmed by
    its bytes).  A file that cannot be read goes in ``job.errors``."""
    sources = list(sources)
    files = checksum.walk(sources, job)
    named = {source.normalized() for source in sources}
    plans: list[Plan] = []
    for location, size in files:
        if job.stopped:
            raise Stopped
        if location.normalized() not in named and suffix_tool(location.name) is None:
            continue
        job.current = str(location)
        try:
            head = _head(location)
        except OSError as error:
            job.errors.append((str(location), _reason(error)))
            continue
        tool = tool_of(location.name, head)
        if tool is None:
            continue
        plans.append(Plan(location, location.parent / plain_name(location.name), size, tool,
                          tool == "age" and age_wants_passphrase(head)))
    job.files_total = len(plans)
    job.total = sum(plan.size for plan in plans)
    return plans


def existing_targets(plans: list[Plan]) -> int:
    """How many of *plans*' targets are there already."""
    there = 0
    for plan in plans:
        try:
            there += drive_of(plan.target).lexists(plan.target)
        except OSError:
            pass
    return there


# -- the programs' command lines ------------------------------------------------------------------


def gpg_encrypt_args(options: Options, name: str, passphrase_fd: int | None) -> list[str]:
    """gpg's arguments for encrypting standard input named *name*."""
    args = [*GPG_BASE]
    if passphrase_fd is not None:
        args += ["--passphrase-fd", str(passphrase_fd)]
    if options.method == "passphrase":
        args += ["--symmetric", "--cipher-algo", "AES256"]
    else:
        # Keys the user chose by name: do not ask gpg's web of trust about them.
        args += ["--encrypt", "--trust-model", "always"]
        for recipient in options.recipients:
            args += ["--recipient", recipient]
    if options.armor:
        args.append("--armor")
    return args + ["--set-filename", name]


def gpg_decrypt_args(passphrase_fd: int | None) -> list[str]:
    args = [*GPG_BASE]
    if passphrase_fd is not None:
        args += ["--passphrase-fd", str(passphrase_fd)]
    return args + ["--decrypt"]


def age_encrypt_args(options: Options, plugin: bool) -> list[str]:
    """age's arguments for encrypting standard input; *plugin* names
    batchpass for a passphrase, else age prompts on its terminal."""
    args = ["-e"]
    if options.method == "passphrase":
        args += ["-j", "batchpass"] if plugin else ["-p"]
    else:
        for recipient in options.recipients:
            args += ["-R", recipient] if os.path.isfile(os.path.expanduser(recipient)) else ["-r", recipient]
    if options.armor:
        args.append("-a")
    return args


def age_decrypt_args(options: Options, passphrase: bool, plugin: bool) -> list[str]:
    args = ["-d"]
    if passphrase:
        if plugin:
            args += ["-j", "batchpass"]
    else:
        for identity in options.identities:
            args += ["-i", os.path.expanduser(identity)]
    return args


# -- running one ------------------------------------------------------------------------------------


def _passphrase_pipe(passphrase: str) -> int:
    """The read end of a pipe holding *passphrase* and a newline, its write
    end closed -- a passphrase is far smaller than a pipe's buffer."""
    read, write = os.pipe()
    try:
        os.write(write, passphrase.encode("utf-8") + b"\n")
    finally:
        os.close(write)
    return read


def _controlling(slave: int) -> Callable[[], None]:
    def become() -> None:
        os.setsid()
        fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
    return become


class _Answerer(threading.Thread):
    """Reads what age writes to its pty and answers every passphrase prompt."""

    def __init__(self, master: int, passphrase: str) -> None:
        super().__init__(daemon=True)
        self.master = master
        self.passphrase = passphrase.encode("utf-8")
        self.done = threading.Event()
        self.said = b""

    def run(self) -> None:
        seen = b""
        while not self.done.is_set():
            try:
                ready, _, _ = select.select([self.master], [], [], 0.1)
                if not ready:
                    continue
                data = os.read(self.master, 1024)
            except OSError:
                return
            if not data:
                return
            seen += data
            self.said += data
            if b":" in seen and b"passphrase" in seen.lower():
                seen = b""
                try:
                    os.write(self.master, self.passphrase + b"\n")
                except OSError:
                    return


def run_filter(argv: list[str], plan: Plan, job: EncryptJob, *, pass_fds: tuple[int, ...] = (),
               env: dict[str, str] | None = None, pty_passphrase: str | None = None) -> str:
    """*argv* run with *plan*'s source on its standard input and its standard
    output written to *plan*'s target, through their drives -- whose
    ``finish()`` is the caller's, once for the batch.  Returns what it wrote
    to its standard error.  A failure leaves no target behind and raises
    :class:`ToolError` (or ``OSError`` for a drive's); a Stop raises
    :class:`Stopped` the same way."""
    master = slave = -1
    preexec: Callable[[], None] | None = None
    if pty_passphrase is not None:
        master, slave = os.openpty()
        preexec = _controlling(slave)
    job.current = str(plan.source)
    source_drive = drive_of(plan.source)
    target_drive = drive_of(plan.target)
    start = job.position
    written = False
    try:
        with source_drive.open_read(plan.source) as source:
            try:
                process = subprocess.Popen(
                    argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    pass_fds=pass_fds + ((slave,) if slave >= 0 else ()), env=env, preexec_fn=preexec,
                    start_new_session=preexec is None)
            except OSError as error:
                raise ToolError(f"{argv[0]}: {_reason(error)}") from error
            finally:
                for fd in pass_fds:
                    os.close(fd)
                if slave >= 0:
                    os.close(slave)
                    slave = -1
            answerer = _Answerer(master, pty_passphrase) if pty_passphrase is not None else None
            if answerer is not None:
                answerer.start()
            errors: list[bytes] = []
            reader = threading.Thread(target=lambda: errors.append(process.stderr.read()), daemon=True)  # type: ignore[union-attr]
            reader.start()
            failure: list[BaseException] = []
            feeder = threading.Thread(target=_feed, args=(source, process, job, failure), daemon=True)
            feeder.start()
            try:
                written = True
                with target_drive.open_write(plan.target) as target:
                    _drain(process, target, job)
                feeder.join()
                if failure:
                    raise failure[0]
                if job.stopped:
                    raise Stopped
                code = process.wait()
                reader.join()
            except BaseException:
                _kill(process)
                feeder.join()
                raise
            finally:
                if answerer is not None:
                    answerer.done.set()
                    answerer.join()
            stderr = b"".join(errors).decode("utf-8", "replace")
            if code != 0:
                raise ToolError(stderr)
        return stderr
    except BaseException:
        job.position = start
        if written:
            try:
                target_drive.unlink(plan.target)
            except OSError:
                pass
        raise
    finally:
        if master >= 0:
            os.close(master)
        if slave >= 0:
            os.close(slave)


def _kill(process: subprocess.Popen[bytes]) -> None:
    """*process* and everything it started: it leads a session of its own, so
    a child of its holding the pipes open (gpg's helpers) goes with it."""
    import signal

    try:
        os.killpg(process.pid, signal.SIGKILL)
    except OSError:
        process.kill()
    process.wait()


def _feed(source: IO[bytes], process: subprocess.Popen[bytes], job: EncryptJob,
          failure: list[BaseException]) -> None:
    """The source into the program's standard input, counted as it goes.  A
    program that stops reading -- it failed -- ends it quietly; its own
    message says why."""
    stdin = process.stdin
    assert stdin is not None
    try:
        while not job.stopped:
            job.wait_while_paused()
            chunk = source.read(CHUNK)
            if not chunk:
                break
            stdin.write(chunk)
            job.position += len(chunk)
    except (BrokenPipeError, ValueError):
        pass
    except OSError as error:
        failure.append(error)
        _kill(process)
    finally:
        try:
            stdin.close()
        except OSError:
            pass


def _drain(process: subprocess.Popen[bytes], target: IO[bytes], job: EncryptJob) -> None:
    """The program's standard output into *target*, looking at Stop every
    tenth of a second -- a program that is quiet (age at a prompt, gpg still
    reading) must not hold a Stop up."""
    stdout = process.stdout
    assert stdout is not None
    fd = stdout.fileno()
    while True:
        if job.stopped:
            raise Stopped
        ready, _, _ = select.select([fd], [], [], 0.1)
        if not ready:
            continue
        chunk = os.read(fd, CHUNK)
        if not chunk:
            return
        target.write(chunk)


def _gpg_message(stderr: str) -> str:
    """What gpg said went wrong: its last line that is not a status line."""
    lines = [line.removeprefix("gpg: ").strip() for line in stderr.splitlines()
             if line.strip() and not line.startswith("[GNUPG:]")]
    return lines[-1] if lines else stderr.strip() or "gpg failed"


def _age_message(stderr: str) -> str:
    """What age said went wrong: its ``age: error: ...`` line, else its first."""
    lines = [line.removeprefix("age: ").strip() for line in stderr.splitlines() if line.strip()]
    for line in lines:
        if line.startswith("error: "):
            return line[len("error: "):]
    return lines[0] if lines else "age failed"


def gpg_outcome(stderr: str, passphrase_given: bool) -> Exception:
    """What a failed gpg's status lines in *stderr* mean."""
    status = [line[len("[GNUPG:] "):] for line in stderr.splitlines() if line.startswith("[GNUPG:] ")]
    if any("BAD_PASSPHRASE" in line for line in status):
        return BadPassphrase()
    if not passphrase_given and any(line.startswith("NEED_PASSPHRASE") for line in status):
        return NeedsPassphrase()
    if any(line.startswith("NO_SECKEY") for line in status) and not any(
            line.startswith("DECRYPTION_OKAY") for line in status):
        return ToolError(NO_SECRET_KEY)
    return ToolError(_gpg_message(stderr))


def _age_bad(message: str) -> bool:
    lower = message.lower()
    return "incorrect passphrase" in lower or "wrong passphrase" in lower or "failed to decrypt" in lower


def encrypt_one(plan: Plan, options: Options, job: EncryptJob) -> None:
    command = program(plan.tool)
    if command is None:
        raise ToolError(f"{plan.tool} is not installed")
    secret = options.passphrase if options.method == "passphrase" else None
    if plan.tool == "gpg":
        fds = (_passphrase_pipe(secret),) if secret is not None else ()
        argv = [command, *gpg_encrypt_args(options, plan.source.name, fds[0] if fds else None)]
        try:
            run_filter(argv, plan, job, pass_fds=fds)
        except ToolError as error:
            raise ToolError(_gpg_message(str(error))) from None
        return
    plugin = secret is not None and batchpass() is not None
    argv = [command, *age_encrypt_args(options, plugin)]
    try:
        if plugin:
            fd = _passphrase_pipe(secret or "")
            run_filter(argv, plan, job, pass_fds=(fd,), env={**os.environ, "AGE_PASSPHRASE_FD": str(fd)})
        else:
            run_filter(argv, plan, job, pty_passphrase=secret)
    except ToolError as error:
        raise ToolError(_age_message(str(error))) from None


def decrypt_one(plan: Plan, options: Options, job: EncryptJob) -> None:
    """*plan* decrypted with *options*: raises :class:`NeedsPassphrase` or
    :class:`BadPassphrase` for what the loop must ask, :class:`ToolError` else."""
    command = program(plan.tool)
    if command is None:
        raise ToolError(f"{plan.tool} is not installed")
    secret = options.passphrase
    if plan.tool == "gpg":
        fds = (_passphrase_pipe(secret),) if secret is not None else ()
        argv = [command, *gpg_decrypt_args(fds[0] if fds else None)]
        try:
            run_filter(argv, plan, job, pass_fds=fds)
        except ToolError as error:
            raise gpg_outcome(str(error), secret is not None) from None
        return
    if plan.passphrase:
        if secret is None:
            raise NeedsPassphrase()
        plugin = batchpass() is not None
        argv = [command, *age_decrypt_args(options, True, plugin)]
        try:
            if plugin:
                fd = _passphrase_pipe(secret)
                run_filter(argv, plan, job, pass_fds=(fd,), env={**os.environ, "AGE_PASSPHRASE_FD": str(fd)})
            else:
                run_filter(argv, plan, job, pty_passphrase=secret)
        except ToolError as error:
            message = _age_message(str(error))
            if _age_bad(message):
                raise BadPassphrase() from None
            raise ToolError(message) from None
        return
    if not options.identities:
        raise ToolError(NO_IDENTITY)
    argv = [command, *age_decrypt_args(options, False, False)]
    try:
        run_filter(argv, plan, job)
    except ToolError as error:
        raise ToolError(_age_message(str(error))) from None


# -- the whole run -----------------------------------------------------------------------------------


def _each(plans: list[Plan], job: EncryptJob, do: Callable[[Plan], None]) -> list[Plan]:
    """*do* each of *plans*, every target drive finished once at the end --
    an archive is rewritten once, not once a file."""
    done: list[Plan] = []
    drives: dict[int, Any] = {}
    try:
        for plan in plans:
            if job.stopped:
                raise Stopped
            start = job.position
            try:
                drive = drive_of(plan.target)
                drives[id(drive)] = drive
                do(plan)
                done.append(plan)
            except NeedsPassphrase:
                job.needs_passphrase.append(plan)
            except BadPassphrase:
                job.bad_passphrase.append(plan)
            except ToolError as error:
                job.errors.append((str(plan.source), str(error.args[0]) if error.args else ""))
            except OSError as error:
                job.errors.append((str(plan.source), _reason(error)))
            job.position = start + plan.size
            job.files_done += 1
    finally:
        for drive in drives.values():
            try:
                drive.finish()
            except OSError as error:
                job.errors.append((str(drive), _reason(error)))
    return done


def encrypt(plans: list[Plan], options: Options, job: EncryptJob) -> list[Plan]:
    """Each of *plans* encrypted; one that fails goes in ``job.errors``.
    Returns those done."""
    job.files_total = len(plans)
    job.total = sum(plan.size for plan in plans)
    return _each(plans, job, lambda plan: encrypt_one(plan, options, job))


def decrypt(plans: list[Plan], options: Options, job: EncryptJob) -> list[Plan]:
    """Each of *plans* decrypted.  Those wanting a passphrase go in
    ``job.needs_passphrase``, those the one given did not open in
    ``job.bad_passphrase``, the failed in ``job.errors``.  Returns those done."""
    job.needs_passphrase = []
    job.bad_passphrase = []
    job.files_done = job.position = 0
    job.files_total = len(plans)
    job.total = sum(plan.size for plan in plans)
    return _each(plans, job, lambda plan: decrypt_one(plan, options, job))


def remove_originals(done: list[Plan], job: EncryptJob) -> list[Plan]:
    """*Delete originals*: each source of *done* -- every one written in full
    -- removed.  One that cannot be goes in ``job.errors``.  Returns those removed."""
    removed: list[Plan] = []
    drives: dict[int, Any] = {}
    try:
        for plan in done:
            drive = drive_of(plan.source)
            drives[id(drive)] = drive
            job.current = str(plan.source)
            try:
                drive.unlink(plan.source)
                removed.append(plan)
            except OSError as error:
                job.errors.append((str(plan.source), _reason(error)))
    finally:
        for drive in drives.values():
            try:
                drive.finish()
            except OSError:
                pass
    return removed
