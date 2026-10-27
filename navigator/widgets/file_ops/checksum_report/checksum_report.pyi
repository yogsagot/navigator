# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.checksum_report.checksum_report``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.static_text import StaticText

from typing import Any
from navkit.i18n import tr, tr_n
from navigator.lib.file_ops.checksum import NO_CHECKSUMS, VerifyResult


class ChecksumReport(Dialog, _Component):
    summary: StaticText
    bad_caption: Label
    bad: ListViewer
    def __init__(self, result: VerifyResult | None = ..., **kwargs: Any) -> None: ...
