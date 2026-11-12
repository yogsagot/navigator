"""What *Replace this occurence?* answers: ``"yes"``, ``"all"``, ``"no"`` or None for Cancel.

DN placed the box above or below the line found so as not to hide it; a navml
dialog is centred.  It dims nothing behind it (DN dimmed nothing at all): faint,
the match it asks about was grey on grey.
"""

from __future__ import annotations



from navml.widgets.dialog.dialog import Dialog


class ReplaceQuery(Dialog):
    """``MessageBoxRect(dlQueryReplace, mfQuery + mfYesButton + mfAllButton + mfNoButton + mfCancelButton)``:
    *Query*, the buttons in their flags' order -- Yes, No, All, Cancel."""

    #: The match it asks about stays at full strength.
    dims_behind = False
