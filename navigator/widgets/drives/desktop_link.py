"""The URI box of Utilities > *GVfs/KIO link*, shared with *Saved links*' *Add*.

Not DOS Navigator's.  A place the desktop's GVfs or KDE's KIO reaches has no
host-and-login form of its own -- ``mtp://Phone/``, ``google-drive://me@gmail.com/``
-- so it is asked as a URI, its examples the backend's
(:func:`navigator.lib.system.desktop.link_name`), and refused with the
schemes it knows when nothing reaches it.
"""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr

from navml.widgets.dialog.dialog import Dialog

from navigator.lib.drives import Location


async def ask_desktop_uri(app: Any) -> Location | None:
    """A URI asked and checked: where it goes, or None for Cancel, an empty
    line, or a place nothing reaches (said in a box first)."""
    from navigator.lib.drives import sessions
    from navigator.lib.system import desktop
    from navigator.widgets.shell.edit_line_dialog import EditLineDialog
    from navml.widgets.dialog.control import escape_caption

    kde = desktop.link_name() == "KIO"
    caption = tr("~U~RI (mtp://, webdav://, gdrive://...)") if kde else tr("~U~RI (mtp://, dav://, google-drive://...)")
    # The menu's name, whichever backend answers: the URI examples say which.
    title = tr("GVfs/KIO link")
    box = EditLineDialog("", history="gvfs_link", caption=caption)
    # After construction: the markup's own *Edit History* is bound in ``__init__``.
    box.title = title
    text = await box.execute(app)
    text = (text or "").strip()
    if not text:
        return None
    target = Location.parse(text)
    schemes = desktop.link_schemes()
    if target.is_local or (target.site.scheme not in sessions.SCHEMES and target.site.scheme not in schemes):
        known = ", ".join(f"{scheme}://" for scheme in schemes)
        prompt = (tr("{uri} is no place KIO reaches. It knows {schemes}") if kde
                  else tr("{uri} is no place GVfs reaches. It knows {schemes}"))
        await Dialog(title=title, buttons="ok", prompt=escape_caption(
            prompt.format(uri=text, schemes=known),
        )).execute(app)
        return None
    return target


__all__ = ["ask_desktop_uri"]
