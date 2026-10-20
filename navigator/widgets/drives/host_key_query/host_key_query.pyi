# navml: generated
"""The merged surface of ``navigator.widgets.drives.host_key_query.host_key_query``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog

from typing import Any
from navkit.i18n import tr
from navkit.reactive import unbind
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.control import escape_caption


class HostKeyQuery(Dialog, _Component):
    def __init__(self, host: str = ..., key_type: str = ..., fingerprint: str = ..., **kwargs: Any) -> None: ...
    def accept(self) -> str: ...
    def close(self, result: Any = ...) -> None: ...
