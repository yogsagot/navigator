"""Other drives: Navigator Link, the link managers, connecting, remote shells, hanging up, and
root access.

A mixin of :class:`Shell` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``shell.py``.
"""

from __future__ import annotations

import asyncio
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any

from navkit.i18n import tr

from navml.widgets.dialog.dialog import Dialog

from navigator.lib.drives import DriveGone, Location, Site, drive_of
from navigator.widgets.shell.commands import (
    EditLinks,
    S3Link,
    GvfsLink,
    DockerLink,
    PodmanLink,
    AdbLink,
    RcloneLink,
    FtpLink,
    NavyLink,
    SmbLink,
)
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager import Manager

if TYPE_CHECKING:
    from navigator.widgets.shell.shell import Shell as _Base
else:
    from navkit.widget import Mixin as _Base


class Links(_Base):
    """Other drives: Navigator Link, the link managers, connecting, remote shells, hanging up, and"""

    # -- other drives: Navigator Link ------------------------------------------

    async def on_navy_link(self, event: NavyLink) -> bool:
        return self._link_command("sftp")

    async def on_ftp_link(self, event: FtpLink) -> bool:
        return self._link_command("ftp")

    async def on_smb_link(self, event: SmbLink) -> bool:
        return self._link_command("smb")

    async def on_s3_link(self, event: S3Link) -> bool:
        return self._link_command("s3")

    async def on_gvfs_link(self, event: GvfsLink) -> bool:
        return self._link_command("gvfs")

    async def on_docker_link(self, event: DockerLink) -> bool:
        return self._link_command("docker")

    async def on_podman_link(self, event: PodmanLink) -> bool:
        return self._link_command("podman")

    async def on_adb_link(self, event: AdbLink) -> bool:
        return self._link_command("adb")

    async def on_rclone_link(self, event: RcloneLink) -> bool:
        return self._link_command("rclone")

    def _link_command(self, scheme: str) -> bool:
        manager = self.active_manager
        if manager is not None:
            self.spawn(self.navy_link(manager.active_panel, scheme=scheme))
        return True

    async def navy_link(self, panel: Any, request: Any = None, *, scheme: str = "sftp") -> bool:
        """Utilities > *Navigator Link*: ``cmNavyLink`` -- where to connect,
        asked; *panel* sent there once connected, and the place kept by name
        if *Keep* was ticked.  True once the panel is there."""
        from navigator.lib.drives import profiles, recent, sessions
        from navigator.widgets.drives.connect_dialog import ConnectDialog

        app = self.application
        if request is not None:
            scheme = request.scheme
        if scheme == "gvfs":
            return await self.gvfs_link(panel)
        if request is None:
            # Every protocol's menu item, and the Link box's *New ... link*:
            # its connection manager.  A *request* (filled in from elsewhere)
            # still goes to the one-shot box below.
            from navigator.widgets.drives.link_manager import family_of

            return await self.link_manager(panel, family_of(scheme))
        family = (("ftp", "ftps") if scheme in ("ftp", "ftps") else ("s3", "s3+http") if scheme in ("s3", "s3+http")
                  else (scheme,))
        missing = sessions.available(scheme)
        request = await ConnectDialog(request, missing=missing, recent=recent.recent(family),
                                      scheme=scheme).execute(app)
        if request is None:
            return False
        site = Site(request.scheme, request.user, request.host, request.port)
        path = PurePosixPath(request.path) if request.path else profiles.HOME
        if request.keep and request.name:
            await asyncio.to_thread(profiles.save, request.name, request.scheme, request.host,
                                    request.user, request.port, request.path)
        if not await self.go_remote(panel, Location(site, path)):
            return False
        # Remembered once it worked, every line of it together: a mistyped
        # host that never answered does not come back to be picked.
        await asyncio.to_thread(recent.remember, recent.Recent(
            request.scheme, request.host, request.user, request.port, request.path))
        return True

    async def link_manager(self, panel: Any, family: str) -> bool:
        """Utilities > *SSH link*, *FTP link*, *SMB link*, *S3 link* and
        *GVfs/KIO link*: *family*'s connection manager (``LinkManagerDialog``),
        and *panel* sent where *Connect* says.  True once the panel is there."""
        from navigator.lib.drives import recent, sessions
        from navigator.widgets.drives.link_manager import FAMILIES, LinkManagerDialog, entries_for, location_of

        entries = await asyncio.to_thread(entries_for, family)
        schemes = FAMILIES[family].schemes
        missing = sessions.available(schemes[0]) if schemes else None
        request = await LinkManagerDialog(entries, family=family, mode="panel",
                                          missing=missing).execute(self.application)
        if request is None:
            return False
        if request.copy_key:
            self.copy_ssh_key(request)
            return False
        if request.configure:
            self.configure_rclone()
            return False
        target = location_of(request)
        if family == "gvfs" and target.path == PurePosixPath("."):
            # A desktop place opens at its root: GVfs and KIO have no home there.
            target = Location(target.site, PurePosixPath("/"))
        from navigator.lib.drives import forwards

        wanted = forwards.parse(request.forwards, strict=False) if family == "sftp" else None
        if not await self.go_remote(panel, target, wanted):
            return False
        if family != "gvfs":
            # Remembered once it worked, as ``navy_link`` does.
            await asyncio.to_thread(recent.remember, recent.Recent(
                request.scheme, request.host, request.user, request.port, request.path))
        return True

    async def gvfs_link(self, panel: Any) -> bool:
        """Utilities > *GVfs/KIO link*: its connection manager, the places
        kept by URI -- ``mtp://``, ``dav://``, ``google-drive://``... -- and
        *panel* sent there, mounted through GVfs (:mod:`navigator.lib.drives.gvfs`)
        or, where the desktop's plumbing is KDE's, kio-fuse
        (:mod:`navigator.lib.drives.kio`).  True once the panel is there."""
        return await self.link_manager(panel, "gvfs")

    async def go_remote(self, panel: Any, target: Location, forwards: list[Any] | None = None) -> bool:
        """*panel* to *target* on another drive, connected first -- asking
        what the connection needs, *forwards* opened with it (:meth:`reach`).
        A *target* whose path is ``.`` opens on the home directory there.
        True once the panel is there."""
        from navigator.lib.drives import profiles

        if not await self.reach(target, forwards):
            return False
        if target.path == profiles.HOME:
            try:
                home = getattr(drive_of(target), "home", PurePosixPath("/"))
            except DriveGone:
                return False
            target = Location(target.site, home)
        if panel.parent is None:
            return False  # closed while it connected
        panel.leave_found()
        panel.location = target
        return True

    async def reach(self, target: Location, forwards: list[Any] | None = None) -> bool:
        """*target*'s drive connected, if it is not already: the host key, a
        password or a passphrase asked as the connection needs them, and
        tried again with each answer.  False if it could not be, which is
        said, or was cancelled.  *forwards* are SSH's port forwards to open
        with a new connection; None, the ones a profile for the place keeps."""
        from navigator.lib.drives import credentials, sessions
        from navigator.lib.drives.sessions import (
            SESSIONS, Answers, NeedPassphrase, NeedPassword, UnknownHostKey,
        )
        from navigator.lib.system.job import Job
        from navigator.lib.system.progress import run_with_progress
        from navigator.widgets.drives.host_key_query import HostKeyQuery
        from navigator.widgets.drives.password_dialog import PasswordDialog
        from navigator.widgets.editor.loading import progress_box
        from navml.widgets.dialog.control import escape_caption

        site = target.site
        from navigator.lib.drives import root

        if site == root.ROOT_SITE and target.outer is None:
            # Not a connection: root access, asked for (a departure;
            # :mod:`navigator.lib.system.elevate`).
            from navigator.widgets.file_ops.as_root import reach_root

            return await reach_root(self.application, target)
        if target.is_local or SESSIONS.is_open(site) or site.scheme == "trash":
            # The Trash is no connection either (:mod:`navigator.lib.drives.trash`).
            return True
        app = self.application
        if target.outer is not None:
            # A place in an archive: the archive opened -- made, if named and
            # not there -- on the drive it is on, reached first.
            from navigator.lib.drives import archive

            if not target.outer.is_local and not await self.reach(target.outer):
                return False
            try:
                await asyncio.to_thread(archive.open_archive, target.outer, None, create=True)
            except (OSError, archive.NotAnArchive) as error:
                await Dialog(title=tr("Error"), prompt=tr("Cannot read {path}: {error}").format(
                    path=str(target.outer), error=getattr(error, "strerror", None) or error),
                    buttons="ok").execute(app)
                return False
            return True
        protocol = sessions.protocol_name(site.scheme)
        title = tr("{protocol} link").format(protocol=protocol)
        reason = sessions.available(site.scheme)
        if reason is not None:
            await Dialog(title=title, prompt=escape_caption(reason), buttons="ok").execute(app)
            return False
        lock = self._reaching.setdefault(site, asyncio.Lock())
        async with lock:
            if SESSIONS.is_open(site):
                return True
            answers = Answers(start=str(target.path), interactive=self._interactive_asker(protocol))
            if site.scheme == "sftp":
                # The port forwards to open with it: the link manager's, or
                # those kept with the place (the Link box, a saved desktop,
                # the command line) -- read on a thread, from the database.
                from navigator.lib.drives import profiles

                answers.forwards = (forwards if forwards is not None
                                    else await asyncio.to_thread(profiles.forwards_for, site))
            while True:
                job = Job()
                job.position = job.total = 0
                job.cancellable = True
                try:
                    await run_with_progress(
                        app, lambda: SESSIONS.connect(site, answers), job,
                        lambda: progress_box(job, tr("Connecting to {host} over {protocol}").format(
                            host=site.host, protocol=protocol)),
                    )
                    # *Save in keyring* ticked and refused: connected all the
                    # same, and the user told why the password will be asked again.
                    refused = [each.keyring_refused for each in (answers, *answers.hops.values())
                               if each.keyring_refused]
                    if refused:
                        self.toast(tr("The password was not saved in the keyring: {reason}").format(
                            reason=escape_caption(refused[0])), title=protocol)
                    return True
                except UnknownHostKey as unknown:
                    choice = await HostKeyQuery(unknown.hostname, unknown.key_type,
                                                unknown.fingerprint).execute(app)
                    if choice is None:
                        return False
                    answers.for_hop(unknown.hop).host_key = choice
                except NeedPassword as needed:
                    # GVfs keeps its own passwords (the desktop's keyring), not ours.
                    can_keep = (sessions.module_name(site.scheme) != sessions.GVFS
                                 and await asyncio.to_thread(credentials.keyring_available))
                    who = f"{needed.user}@{needed.host}" if needed.user else needed.host
                    if site.scheme in ("s3", "s3+http"):
                        # S3's password is the access key's secret.
                        prompt = (tr("Wrong secret key for {who}. Try again:") if needed.wrong
                                  else tr("Secret key for {who}:")).format(
                            who=escape_caption(who))
                    elif site.scheme == "rclone":
                        # rclone's password is its encrypted configuration's, not the remote's.
                        prompt = (tr("Wrong password for rclone's configuration. Try again:") if needed.wrong
                                  else tr("Password for rclone's configuration:"))
                    else:
                        prompt = (tr("Wrong {protocol} password for {who}. Try again:") if needed.wrong
                                  else tr("{protocol} password for {who}:")).format(
                            protocol=protocol, who=escape_caption(who))
                    answer = await PasswordDialog(prompt, can_keep=can_keep).execute(app)
                    if answer is None:
                        return False
                    asked = answers.for_hop(needed.hop)
                    asked.password, asked.save_password = answer
                except NeedPassphrase as needed:
                    prompt = (tr("Wrong passphrase for {key}. Try again:") if needed.wrong
                              else tr("Passphrase for {key}:")).format(key=escape_caption(needed.key_file))
                    answer = await PasswordDialog(prompt).execute(app)
                    if answer is None:
                        return False
                    answers.for_hop(needed.hop).passphrase = answer[0]
                except OSError as error:
                    if job.stopped:
                        return False
                    await Dialog(title=title,
                                 prompt=escape_caption(error.strerror or str(error)),
                                 buttons="ok").execute(app)
                    return False

    def _interactive_asker(self, protocol: str) -> Any:
        """What a connecting thread calls with a server's own questions
        (SSH's keyboard-interactive: a one-time code, a PIN): each put in a
        box on the loop, the thread waiting for the replies -- None if one was
        cancelled -- as a copy's worker waits for its questions."""
        import concurrent.futures

        loop = asyncio.get_running_loop()

        def ask(title: str, instructions: str, prompts: list[tuple[str, bool]]) -> list[str] | None:
            future: concurrent.futures.Future[Any] = concurrent.futures.Future()
            loop.call_soon_threadsafe(
                lambda: self.spawn(self._answer_prompts(protocol, title, instructions, prompts, future)))
            return future.result()

        return ask

    async def _answer_prompts(self, protocol: str, title: str, instructions: str,
                              prompts: list[tuple[str, bool]], future: Any) -> None:
        from navml.widgets.dialog.control import escape_caption

        from navigator.widgets.drives.password_dialog import PasswordDialog

        replies: list[str] = []
        try:
            for prompt, echo in prompts:
                text = f"{instructions.strip()}\n{prompt}" if instructions and instructions.strip() else prompt
                box = PasswordDialog(escape_caption(text.strip()))
                box.title = f"{protocol}: {title}" if title else protocol
                box.entry.entry.password = not echo
                answer = await box.execute(self.application)
                if answer is None:
                    future.set_result(None)
                    return
                replies.append(answer[0])
            future.set_result(replies)
        except BaseException as error:
            if not future.done():
                future.set_result(None)
            if not isinstance(error, Exception):
                raise

    async def on_edit_links(self, event: EditLinks) -> bool:
        manager = self.active_manager
        self.spawn(self.edit_links(manager.active_panel if manager is not None else None))
        return True

    async def edit_links(self, panel: Any) -> None:
        """Utilities > *Saved links*: the profiles read on a thread, edited in
        one box, written back on OK in one transaction -- and, for *Connect*,
        *panel* sent to the one chosen."""
        from navigator.lib.drives import profiles
        from navigator.widgets.drives.links_dialog import LinksDialog

        entries = await asyncio.to_thread(profiles.entries)
        answer = await LinksDialog(entries).execute(self.application)
        if answer is None:
            return
        entries = answer[1]
        await asyncio.to_thread(profiles.store, entries)
        if answer[0] == "connect" and panel is not None:
            chosen = entries[answer[2]]
            row = await asyncio.to_thread(profiles.find, chosen.name)
            if row is not None:
                await self.go_remote(panel, profiles.location_of(row))

    def _running_remote_shell(self, site: Site) -> Any:
        """The command window still logged in to *site* by Remote shell, brought
        forward -- DN's ``OpenTerminal`` selecting its one terminal -- or None."""
        from navigator.widgets.shell.terminal_window import TerminalWindow

        for window in reversed(self.desktop.windows()):
            if isinstance(window, TerminalWindow) and window.remote_site == site and window.view.busy:
                if self.console_visible:
                    self.toggle_console()
                self.desktop.activate(window)
                return window
        return None

    async def open_remote_shell(self, family: str = "sftp") -> Any:
        """Utilities > *Remote shell* > *SSH*, *Docker container*, *Podman
        container*, *Android device*: ``cmTerminal``'s ``OpenTerminal``.
        *family*'s link manager (``LinkManagerDialog``) in its shell mode, and
        *Connect* runs ``ssh -t``, ``docker exec -it`` or ``adb shell`` there
        in a command window (:mod:`navigator.lib.drives.remote_shell`) -- or
        brings forward the one still running for that place.  Nothing is
        taken from the panel: where is chosen in the box.  Returns the
        window, or None when cancelled."""
        from navigator.lib.drives import recent, remote_shell
        from navigator.widgets.drives.link_manager import LinkManagerDialog, entries_for, location_of

        entries = await asyncio.to_thread(entries_for, family)
        request = await LinkManagerDialog(entries, family=family, mode="shell").execute(self.application)
        if request is None:
            return None
        if request.copy_key:
            return self.copy_ssh_key(request)
        location = location_of(request)
        window = self._running_remote_shell(location.site)
        if window is None:
            # Gone when the shell ends -- Ctrl+D, ``exit`` -- however its last
            # command did; kept to show the program's own failure (refused,
            # unreachable, not let in, no such container).
            from navigator.lib.drives import forwards

            window = self.run_in_window(remote_shell.command(location, request.options,
                                                             forwards.parse(request.forwards, strict=False)),
                                        closes=remote_shell.closes(location.site.scheme),
                                        title=remote_shell.title(location.site))
            if window is None:
                return None
            window.remote_site = location.site
        await asyncio.to_thread(recent.remember, recent.Recent(
            request.scheme, request.host, request.user, request.port, request.path))
        return window

    def copy_ssh_key(self, request: Any) -> Any:
        """The SSH link manager's *Copy key...*: ``ssh-copy-id`` putting
        *request*'s public key on its server, in a command window that stays
        to show how it went (``ssh`` asks the password there, ``ssh-keygen``
        a passphrase first when the key is being made).  Returns the window."""
        from navigator.lib.drives import remote_shell

        site = Site(request.scheme, request.user, request.host, request.port)
        return self.run_in_window(
            remote_shell.copy_id_command(site, request.copy_key, request.options, generate=request.generate_key),
            closes=False, title=f"ssh-copy-id {remote_shell.login(site)}")

    def configure_rclone(self) -> Any:
        """The rclone link manager's *Configure...*: ``rclone config``, rclone's
        own interactive setup, in a command window that stays to show how it
        went.  Returns the window."""
        import shlex

        from navigator.lib.drives import rclone

        return self.run_in_window(shlex.join(rclone.configure_command()), closes=False, title="rclone config")

    async def hang_up(self) -> None:
        """Utilities > *Disconnect*: ``cmHangUp`` -- the one connection closed
        once agreed to, or one chosen of several (or all); its panels go back
        to the disk (:meth:`close_linked`)."""
        from navml.widgets.dialog.control import escape_caption
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        from navigator.lib.drives import mounted, sessions
        from navigator.lib.drives.sessions import SESSIONS

        app = self.application
        drives = [drive for drive in mounted() if sessions.is_connection(drive.site.scheme)]
        if not drives:
            return
        if len(drives) == 1:
            site = drives[0].site
            prompt = tr("Close the {protocol} connection to {host}?").format(
                protocol=sessions.protocol_name(site.scheme), host=escape_caption(site.host))
            if await Dialog(title=tr("Disconnect"), prompt=prompt, buttons="yes-no").execute(app) is True:
                await asyncio.to_thread(SESSIONS.close, site)
            return
        menu = SubMenu()
        items = {id(menu.add_item(escape_caption(str(drive.site)))): [drive.site] for drive in drives}
        menu.add_line()
        items[id(menu.add_item(tr("~A~ll")))] = [drive.site for drive in drives]
        title = tr("Disconnect")
        box = PopupMenu(menu, behind=self, title=title)
        width, height = PopupMenu.measure(menu, app, self, title)
        box.at = ((app.root.width - width) // 2, (app.root.height - height) // 2)
        chosen = await box.execute(app)
        for site in items.get(id(chosen), []):
            await asyncio.to_thread(SESSIONS.close, site)

    def _heard_closed(self, site: Any, why: str) -> None:
        """A connection closed, on whatever thread closed it: the loop told."""
        app = self.application
        if app is not None and app.is_running:
            app.call_from_thread(lambda: self.close_linked(site, why))

    def close_linked(self, site: Any, why: str = "closed") -> None:
        """DN's ``cmCloseLinked``: every panel on *site* back on the disk, where
        it last was there; *why* ``"lost"`` says so once."""
        moved = False
        for window in self.desktop.windows():
            if isinstance(window, Manager):
                for panel in window.all_panels:
                    if panel.location.site == site:
                        panel.leave_found()
                        panel.location = panel.local_anchor
                        moved = True
        if why == "lost" and moved:
            from navml.widgets.dialog.control import escape_caption
            from navigator.lib.drives.sessions import SESSIONS, protocol_name, protocol_sign

            name = f"{protocol_sign(site.scheme)}:{site.host}"
            # And why, when the reconnect said (``Drive.lost_reason``).
            reason = SESSIONS.reason(site)
            if reason:
                prompt = tr("Remote drive {name} is not accessible: {reason}").format(
                    name=name, reason=escape_caption(reason))
            else:
                prompt = tr("Remote drive {name} is not accessible").format(name=name)
            self.spawn(Dialog(
                title=tr("{protocol} link").format(protocol=protocol_name(site.scheme)),
                prompt=prompt, buttons="ok").execute(self.application))

    def connections_in_use(self) -> set[Any]:
        """The sites some panel is on now: those no idle timer closes."""
        used = set()
        for window in self.desktop.windows():
            if isinstance(window, Manager):
                for panel in window.all_panels:
                    if not panel.location.is_local:
                        used.add(panel.location.site)
        return used

    async def follow_root(self) -> None:
        """Whether root access is open, looked at once a second: the helper
        starts and ends on threads, the reaper's among them."""
        from navigator.lib.system.elevate import ELEVATION

        self.root_mark.open = ELEVATION.running
        if not ELEVATION.running and self.console.is_root:
            # Closed from elsewhere -- its helper ended: the user's shell back.
            self._back_to_user_shell()

    def _back_to_user_shell(self) -> None:
        """The console's own shell back from root's, where the panel is now."""
        self.console.go_user()
        where = self._front_directory()
        if where is not None:
            self.console.subshell.sync(where)

    def _name_root_access(self) -> None:
        """Utilities' one root entry says what it would do: *Elevate root
        access* while root access is closed, *Close root access* while open."""
        item = self.menu.root_access
        if self.root_mark.open:
            item.text = tr("Close ~r~oot access")
            item.tooltip = tr("End root access now; the console goes back to your own shell")
        else:
            item.text = tr("Elevate ~r~oot access")
            item.tooltip = tr("Open root access now: the console's shell and a step refused permission run as root")

    def _root_reachable(self) -> bool:
        from navigator.lib.system.elevate import ELEVATION

        if ELEVATION.command is not None:  # the tests' helper
            return True
        chosen = SETTINGS.system.elevate
        if chosen not in self._reachable:
            self._reachable[chosen] = ELEVATION.available()
        return self._reachable[chosen]

    async def open_root_access(self) -> None:
        """Utilities > *Elevate root access*: the root helper started, asking
        for the password as *As root* does; the ROOT mark up at once, and the
        console's shell root's too (:meth:`Console.go_root`), the user's own
        parked until root access closes."""
        from navml.widgets.dialog.control import escape_caption

        from navigator.widgets.file_ops.as_root import open_root

        app = self.application
        if app is None or not await open_root(app):
            return
        self.root_mark.open = True
        self.console.on_root_ended = self._root_shell_ended
        try:
            await self.console.go_root(self._command_directory())
        except OSError as error:
            await Dialog(title=tr("Error"), buttons="ok", prompt=tr(
                "The console could not be made root's: {reason}").format(
                    reason=escape_caption(error.strerror or str(error)))).execute(app)

    def _root_shell_ended(self) -> None:
        """``exit`` typed at the root shell: the user's back, root access left open."""
        where = self._front_directory()
        if where is not None:
            self.console.subshell.sync(where)

    async def close_root_access(self) -> None:
        """Utilities > *Close root access*: the panels at ``root:`` back on
        the disk (:meth:`close_linked`), then the helper closed -- a window
        still reading a file as root reads no more of it."""
        from navigator.lib.drives import root
        from navigator.lib.system.elevate import ELEVATION

        if self.console.is_root:
            self._back_to_user_shell()
        self.close_linked(root.ROOT_SITE)
        await asyncio.to_thread(ELEVATION.close)
        self.root_mark.open = False

    async def reap_connections(self) -> None:
        """*Communications*' *Close an idle connection after*, looked at once a minute."""
        from navigator.lib.drives.sessions import SESSIONS

        idle = SETTINGS.remote.idle_disconnect * 60
        if idle > 0:
            await asyncio.to_thread(SESSIONS.reap, self.connections_in_use(), idle)
