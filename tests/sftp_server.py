"""An SFTP server in a thread, for the SFTP drive's tests: paramiko's own
server side, serving one directory, password ``secret`` for anyone.

Modelled on paramiko's ``tests/_stub_sftp.py``.  Not a fixture itself --
``tests/test_sftp.py`` makes one of it -- so that importing it costs nothing
where paramiko is missing.
"""

from __future__ import annotations

import os
import socket
import threading
from pathlib import Path
from typing import Any

import paramiko
from paramiko import SFTP_OK, SFTPAttributes, SFTPHandle, SFTPServer, SFTPServerInterface

PASSWORD = "secret"


#: What keyboard-interactive mode asks, and the answer it takes.
CODE_PROMPT, CODE = "Verification code: ", "123456"


class _Server(paramiko.ServerInterface):
    def __init__(self, interactive: bool = False) -> None:
        self.interactive = interactive

    def check_auth_password(self, username: str, password: str) -> int:
        if self.interactive:
            return paramiko.AUTH_FAILED
        return paramiko.AUTH_SUCCESSFUL if password == PASSWORD else paramiko.AUTH_FAILED

    def get_allowed_auths(self, username: str) -> str:
        return "keyboard-interactive" if self.interactive else "password"

    def check_auth_interactive(self, username: str, submethods: str) -> Any:
        if not self.interactive:
            return paramiko.AUTH_FAILED
        return paramiko.InteractiveQuery("Two-factor", "Look at your phone", (CODE_PROMPT, False))

    def check_auth_interactive_response(self, responses: Any) -> int:
        return paramiko.AUTH_SUCCESSFUL if list(responses) == [CODE] else paramiko.AUTH_FAILED

    def check_channel_request(self, kind: str, chanid: int) -> int:
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED


class _Handle(SFTPHandle):
    def stat(self):
        try:
            return SFTPAttributes.from_stat(os.fstat(self.readfile.fileno()))
        except OSError as error:
            return SFTPServer.convert_errno(error.errno)

    def chattr(self, attr):
        try:
            SFTPServer.set_file_attr(self.filename, attr)
            return SFTP_OK
        except OSError as error:
            return SFTPServer.convert_errno(error.errno)


def _interface(root: Path) -> type:
    class Interface(SFTPServerInterface):
        ROOT = str(root)

        def _real(self, path: str) -> str:
            return self.ROOT + self.canonicalize(path)

        def canonicalize(self, path: str) -> str:
            # "/" is the served directory; the home is too.
            return os.path.normpath("/" + path.lstrip("/")) if path not in ("", ".") else "/"

        def list_folder(self, path):
            path = self._real(path)
            try:
                out = []
                for name in os.listdir(path):
                    attr = SFTPAttributes.from_stat(os.lstat(os.path.join(path, name)))
                    attr.filename = name
                    out.append(attr)
                return out
            except OSError as error:
                return SFTPServer.convert_errno(error.errno)

        def stat(self, path):
            try:
                return SFTPAttributes.from_stat(os.stat(self._real(path)))
            except OSError as error:
                return SFTPServer.convert_errno(error.errno)

        def lstat(self, path):
            try:
                return SFTPAttributes.from_stat(os.lstat(self._real(path)))
            except OSError as error:
                return SFTPServer.convert_errno(error.errno)

        def open(self, path, flags, attr):
            path = self._real(path)
            try:
                binary_flag = getattr(os, "O_BINARY", 0)
                flags |= binary_flag
                mode = getattr(attr, "st_mode", None) or 0o666
                fd = os.open(path, flags, mode)
            except OSError as error:
                return SFTPServer.convert_errno(error.errno)
            if (flags & os.O_CREAT) and attr is not None:
                attr._flags &= ~attr.FLAG_PERMISSIONS
                SFTPServer.set_file_attr(path, attr)
            if flags & os.O_WRONLY:
                fstr = "ab" if flags & os.O_APPEND else "wb"
            elif flags & os.O_RDWR:
                fstr = "a+b" if flags & os.O_APPEND else "r+b"
            else:
                fstr = "rb"
            try:
                f = os.fdopen(fd, fstr)
            except OSError as error:
                return SFTPServer.convert_errno(error.errno)
            handle = _Handle(flags)
            handle.filename = path
            handle.readfile = f
            handle.writefile = f
            return handle

        def remove(self, path):
            try:
                os.remove(self._real(path))
            except OSError as error:
                return SFTPServer.convert_errno(error.errno)
            return SFTP_OK

        def rename(self, oldpath, newpath):
            new = self._real(newpath)
            if os.path.lexists(new):
                return paramiko.SFTP_FAILURE
            try:
                os.rename(self._real(oldpath), new)
            except OSError as error:
                return SFTPServer.convert_errno(error.errno)
            return SFTP_OK

        def posix_rename(self, oldpath, newpath):
            try:
                os.replace(self._real(oldpath), self._real(newpath))
            except OSError as error:
                return SFTPServer.convert_errno(error.errno)
            return SFTP_OK

        def mkdir(self, path, attr):
            try:
                os.mkdir(self._real(path))
                if attr is not None:
                    SFTPServer.set_file_attr(self._real(path), attr)
            except OSError as error:
                return paramiko.SFTP_FAILURE if error.errno == 17 else SFTPServer.convert_errno(error.errno)
            return SFTP_OK

        def rmdir(self, path):
            try:
                os.rmdir(self._real(path))
            except OSError as error:
                return SFTPServer.convert_errno(error.errno)
            return SFTP_OK

        def chattr(self, path, attr):
            try:
                SFTPServer.set_file_attr(self._real(path), attr)
            except OSError as error:
                return SFTPServer.convert_errno(error.errno)
            return SFTP_OK

        def symlink(self, target_path, path):
            try:
                os.symlink(target_path, self._real(path))
            except OSError as error:
                return SFTPServer.convert_errno(error.errno)
            return SFTP_OK

        def readlink(self, path):
            try:
                return os.readlink(self._real(path))
            except OSError as error:
                return SFTPServer.convert_errno(error.errno)

    return Interface


class SftpServer:
    """Serving *root* on ``127.0.0.1``: :attr:`port`, :meth:`drop` to cut
    every connection as a network would, :meth:`stop` for good."""

    def __init__(self, root: Path, *, interactive: bool = False) -> None:
        self.root = root
        self.interactive = interactive
        self.host_key = paramiko.RSAKey.generate(2048)
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(8)
        self.port = self.listener.getsockname()[1]
        self.transports: list[paramiko.Transport] = []
        self.connections = 0
        self._interface = _interface(root)
        self._running = True
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        while self._running:
            try:
                sock, _ = self.listener.accept()
            except OSError:
                return
            transport = paramiko.Transport(sock)
            transport.add_server_key(self.host_key)
            transport.set_subsystem_handler("sftp", SFTPServer, self._interface)
            try:
                transport.start_server(server=_Server(self.interactive))
            except (paramiko.SSHException, EOFError, OSError):
                continue
            self.connections += 1
            self.transports.append(transport)

    def drop(self) -> None:
        for transport in self.transports:
            transport.close()
        self.transports = []

    def stop(self) -> None:
        self._running = False
        self.drop()
        try:
            # Closing alone leaves a thread blocked in accept() listening.
            self.listener.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.listener.close()
        except OSError:
            pass
