# navml: generated
"""The merged surface of ``navigator.widgets.setup.communications_page.communications_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.masked_field import MaskedField
from navml.widgets.dialog.radio_buttons import RadioButtons
from navml.widgets.dialog.static_text import StaticText

from typing import Any
from navkit.widget import Widget
from navigator.settings import DESKTOP_VFS, SETTINGS, RemoteData, SystemData


class CommunicationsPage(_Component):
    title: str
    keepalive: MaskedField
    keepalive_unit: StaticText
    timeout: MaskedField
    timeout_unit: StaticText
    idle_disconnect: MaskedField
    idle_unit: StaticText
    refresh: MaskedField
    refresh_unit: StaticText
    upload_caption: Label
    upload_changed: RadioButtons
    desktop_vfs_caption: Label
    desktop_vfs: RadioButtons
    def __init__(self, section: RemoteData | None = ..., system: SystemData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, dict[str, Any]]: ...
