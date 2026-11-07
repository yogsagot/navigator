#!/usr/bin/env python3
"""A stand-in ``rclone`` for the rclone drive's tests (``tests/test_rclone.py``).

``rclone rcd --rc-addr=unix://PATH ...`` serves the remote control on that
socket the way rclone does for what the drive asks -- ``operations/list``,
``stat``, ``mkdir``, ``rmdir``, ``deletefile``, ``movefile``, ``uploadfile``
(multipart, chunked), ``about``, ``fsinfo``, ``sync/move``,
``config/listremotes``, ``config/get``, ``core/version``, ``core/quit`` -- and
``--rc-serve``'s objects at ``/[REMOTE:]/path`` with ranges, answering a
refusal in rclone's shape (``{"error", "status", "path"}``).
``rclone listremotes --long`` prints them; ``rclone config`` says it ran.

``$FAKE_RCLONE_STATE/config.json`` says what is set up:
``{"remotes": {"name": {"type": "drive", "dirmove": true, "about": true}},
"password": null}`` -- a password there is the configuration's, wanted in
``RCLONE_CONFIG_PASS``.  Each remote's files are ``$FAKE_RCLONE_STATE/remotes/NAME``.
Every rc call is appended to ``calls.log`` there, one JSON line.
``"old": true`` there is an rclone before 1.63: ``unix://`` refused in its words,
``--rc-addr=127.0.0.1:0`` served on a port of the system's, said on standard
error, with ``RCLONE_RC_USER``/``RCLONE_RC_PASS`` wanted as basic authentication.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import socketserver
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

STATE = Path(os.environ.get("FAKE_RCLONE_STATE", "."))


def _config() -> dict:
    try:
        return json.loads((STATE / "config.json").read_text())
    except (OSError, ValueError):
        return {"remotes": {}}


def _check_password() -> None:
    wanted = _config().get("password")
    if wanted is None:
        return
    given = os.environ.get("RCLONE_CONFIG_PASS")
    if given is None:
        sys.stderr.write("Failed to load config file: unable to decrypt configuration and not allowed to ask "
                         "for password: set RCLONE_CONFIG_PASS to your configuration password\n")
        sys.exit(1)
    if given != wanted:
        sys.stderr.write("Failed to load config file: couldn't decrypt configuration, most likely wrong "
                         "password\n")
        sys.exit(1)


class Refused(Exception):
    def __init__(self, text: str, status: int = 500) -> None:
        super().__init__(text)
        self.text, self.status = text, status


def _root(fs: str) -> Path:
    name, colon, rest = fs.partition(":")
    remotes = _config().get("remotes", {})
    if not colon or name not in remotes:
        raise Refused(f'didn\'t find section in config file ("{name}")', 500)
    return STATE / "remotes" / name / rest.lstrip("/")


def _place(fs: str, remote: str) -> Path:
    path = _root(fs)
    for part in remote.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise Refused("bad path", 400)
        path = path / part
    return path


def _item(path: Path, remote: str) -> dict:
    info = path.stat()
    when = datetime.fromtimestamp(info.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")
    is_dir = path.is_dir()
    return {"Path": remote, "Name": path.name, "Size": -1 if is_dir else info.st_size, "ModTime": when,
            "IsDir": is_dir, "MimeType": "inode/directory" if is_dir else "application/octet-stream"}


def _rc(method: str, params: dict, handler: BaseHTTPRequestHandler) -> dict:
    remotes = _config().get("remotes", {})
    if method == "core/version":
        return {"version": "v1.68.0-fake"}
    if method == "core/quit":
        threading.Thread(target=lambda: os._exit(0), daemon=True).start()
        return {}
    if method == "config/listremotes":
        return {"remotes": list(remotes)}
    if method == "config/get":
        return {"type": remotes.get(params.get("name"), {}).get("type", "")}
    fs, remote = params.get("fs", ""), params.get("remote", "")
    if method == "operations/fsinfo":
        name = fs.partition(":")[0]
        setup = remotes.get(name, {})
        _root(fs)
        return {"Name": name, "Root": "", "String": fs, "Precision": 1000000000, "Hashes": ["md5"],
                "Features": {"About": setup.get("about", True), "DirMove": setup.get("dirmove", True),
                             "Move": True, "Copy": True}}
    if method == "operations/about":
        if not remotes.get(fs.partition(":")[0], {}).get("about", True):
            raise Refused("doesn't support about", 500)
        return {"total": 1 << 40, "used": 1 << 30, "free": (1 << 40) - (1 << 30)}
    if method == "operations/list":
        path = _place(fs, remote)
        if not path.is_dir():
            raise Refused("error listing: directory not found", 404)
        return {"list": [_item(each, f"{remote}/{each.name}".lstrip("/")) for each in sorted(path.iterdir())]}
    if method == "operations/stat":
        path = _place(fs, remote)
        return {"item": _item(path, remote) if path.exists() else None}
    if method == "operations/mkdir":
        _place(fs, remote).mkdir(parents=True, exist_ok=True)
        return {}
    if method == "operations/rmdir":
        path = _place(fs, remote)
        if not path.is_dir():
            raise Refused("directory not found", 404)
        try:
            path.rmdir()
        except OSError:
            raise Refused("rmdir failed: directory not empty", 500) from None
        return {}
    if method == "operations/deletefile":
        path = _place(fs, remote)
        if not path.is_file():
            raise Refused("object not found", 404)
        path.unlink()
        return {}
    if method == "operations/movefile":
        source = _place(params["srcFs"], params["srcRemote"])
        dest = _place(params["dstFs"], params["dstRemote"])
        if not source.is_file():
            raise Refused("object not found", 404)
        dest.parent.mkdir(parents=True, exist_ok=True)
        os.replace(source, dest)
        return {}
    if method == "sync/move":
        source, dest = _root(params["srcFs"]), _root(params["dstFs"])
        if not source.is_dir():
            raise Refused("directory not found", 404)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))
        return {}
    if method == "operations/uploadfile":
        directory = _place(fs, remote)
        directory.mkdir(parents=True, exist_ok=True)
        _receive(handler, directory)
        return {}
    raise Refused(f"couldn't find method \"{method}\"", 404)


def _body_lines(handler: BaseHTTPRequestHandler):
    """The request's body, chunked or not, as it comes."""
    stream = handler.rfile
    if handler.headers.get("Transfer-Encoding", "").lower() == "chunked":
        while True:
            size = int(stream.readline().strip().split(b";")[0] or b"0", 16)
            if size == 0:
                stream.readline()
                return
            data = stream.read(size)
            stream.readline()
            yield data
    else:
        left = int(handler.headers.get("Content-Length") or 0)
        while left > 0:
            data = stream.read(min(left, 65536))
            if not data:
                return
            left -= len(data)
            yield data


def _receive(handler: BaseHTTPRequestHandler, directory: Path) -> None:
    boundary = re.search(r"boundary=([^;]+)", handler.headers.get("Content-Type", ""))
    if boundary is None:
        raise Refused("no multipart boundary", 400)
    body = b"".join(_body_lines(handler))
    mark = b"--" + boundary.group(1).strip().encode()
    for part in body.split(mark)[1:]:
        if part.startswith(b"--"):
            break
        head, _, data = part.lstrip(b"\r\n").partition(b"\r\n\r\n")
        data = data[:-2] if data.endswith(b"\r\n") else data
        text = head.decode("utf-8", "replace")
        star = re.search(r"filename\*=UTF-8''([^;\r\n]+)", text)
        plain = re.search(r'filename="([^"]*)"', text)
        name = unquote(star.group(1)) if star else (plain.group(1) if plain else "")
        if not name:
            continue
        (directory / os.path.basename(name)).write_bytes(data)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args) -> None:
        pass

    def address_string(self) -> str:
        return "unix"

    def _send(self, status: int, body: bytes, kind: str = "application/json", extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _refused_auth(self) -> bool:
        wanted = getattr(self.server, "auth", None)
        if wanted is None or self.headers.get("Authorization") == wanted:
            return False
        self._send(401, b"Unauthorized", "text/plain")
        return True

    def do_POST(self) -> None:
        if self._refused_auth():
            return
        parts = urlsplit(self.path)
        method = parts.path.lstrip("/")
        params = {key: values[0] for key, values in parse_qs(parts.query).items()}
        if self.headers.get("Content-Type", "").startswith("application/json"):
            data = b"".join(_body_lines(self))
            if data:
                params.update(json.loads(data))
        try:
            with open(STATE / "calls.log", "a") as log:
                log.write(json.dumps([method, params]) + "\n")
        except OSError:
            pass
        try:
            answer = _rc(method, params, self)
        except Refused as refused:
            answer = {"error": refused.text, "input": params, "path": method, "status": refused.status}
            self._send(refused.status, json.dumps(answer).encode())
            return
        except Exception as error:  # what rclone would say
            answer = {"error": str(error), "input": params, "path": method, "status": 500}
            self._send(500, json.dumps(answer).encode())
            return
        self._send(200, json.dumps(answer).encode())

    def do_GET(self) -> None:
        if self._refused_auth():
            return
        found = re.match(r"^/\[([^\]]*)\]/(.*)$", self.path)
        if found is None:
            self._send(404, b'{"error": "not found", "status": 404}')
            return
        fs, remote = unquote(found.group(1)), unquote(found.group(2))
        try:
            path = _place(fs, remote)
        except Refused as refused:
            self._send(refused.status, json.dumps({"error": refused.text, "status": refused.status}).encode())
            return
        if not path.is_file():
            self._send(404, b'{"error": "object not found", "status": 404}')
            return
        data = path.read_bytes()
        wanted = re.match(r"bytes=(\d+)-(\d*)", self.headers.get("Range", ""))
        if wanted is None:
            self._send(200, data, "application/octet-stream")
            return
        start = int(wanted.group(1))
        end = int(wanted.group(2)) if wanted.group(2) else len(data) - 1
        if start >= len(data):
            self._send(416, b'{"error": "range not satisfiable", "status": 416}')
            return
        end = min(end, len(data) - 1)
        self._send(206, data[start:end + 1], "application/octet-stream",
                   {"Content-Range": f"bytes {start}-{end}/{len(data)}"})


class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


class TcpServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True


def rcd(argv: list[str]) -> None:
    _check_password()
    address = next((each.split("=", 1)[1] for each in argv if each.startswith("--rc-addr=")), "")
    old = bool(_config().get("old"))
    (STATE / "rcd.pid").write_text(str(os.getpid()))
    if address.startswith("unix://") and not old:
        Server(address[len("unix://"):], Handler).serve_forever()
        return
    if address.startswith("unix://"):
        sys.stderr.write("2026/01/01 00:00:00 Failed to start remote control: start server failed: listen tcp: "
                         f"lookup tcp///{address[len('unix://'):]}: unknown port\n")
        sys.exit(1)
    if not old:
        sys.stderr.write("fake rclone: only --rc-addr=unix:// is served\n")
        sys.exit(2)
    host, _, port = address.rpartition(":")
    server = TcpServer((host, int(port)), Handler)
    user, password = os.environ.get("RCLONE_RC_USER"), os.environ.get("RCLONE_RC_PASS")
    if user and password:
        server.auth = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()
    sys.stderr.write(f"2026/01/01 00:00:00 NOTICE: Serving remote control on "
                     f"http://{host}:{server.server_address[1]}/\n")
    sys.stderr.flush()
    server.serve_forever()


def main() -> None:
    argv = sys.argv[1:]
    with open(STATE / "argv.log", "a") as log:
        log.write(json.dumps(argv) + "\n")
    if not argv:
        sys.exit(1)
    if argv[0] == "rcd":
        rcd(argv[1:])
    elif argv[0] == "listremotes":
        _check_password()
        for name, setup in _config().get("remotes", {}).items():
            print(f"{name + ':':<16} {setup.get('type', '')}")
    elif argv[0] == "config":
        print("fake rclone config ran")
    else:
        sys.stderr.write(f"fake rclone: {argv[0]} is not faked\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
