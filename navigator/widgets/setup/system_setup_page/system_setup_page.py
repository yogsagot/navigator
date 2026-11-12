"""*System Setup*: DN's ``TSystemData`` -- every control says which ``[system]``
setting it edits (``key:``), and :class:`SettingsPage` seeds and collects them."""

from __future__ import annotations

from navigator.widgets.setup.settings_page import SettingsPage


class SystemSetupPage(SettingsPage):
    """DN's ``TSystemData``: its *Options* word and its temporary directory, *Unexpected failures*, *Report a stall after*, *Root access* and *Keep root open while idle*."""
