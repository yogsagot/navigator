# navml: generated
"""Generated from ``palette_file_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes    # palette_file_dialog.nml:1
from navml.widgets.dialog.file_dialog import FileDialog    # palette_file_dialog.nml:2

__navml_component__ = "PaletteFileDialog"

__all__ = ["PaletteFileDialog"]


class PaletteFileDialog(FileDialog, _Component):
    """Options > Load palette's file box: DN's ``TFileDialog``, wider, with a box

    that paints the palette under the *Files* cursor while it is ticked.

    Not DN's: ``LoadColors`` opened the plain 47-column ``GetFileNameDialog``,
    whose 15-column lists cut off most theme names (``solarized-light.nss``),
    and it showed nothing before the file was loaded.  The hand-written half
    moves the base's controls to make the room; this adds the box.
    """

    #: The document this class was generated from.
    __navml_source__ = "palette_file_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    preview: CheckBoxes    # palette_file_dialog.nml:16

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.preview = CheckBoxes(parent=self)    # palette_file_dialog.nml:15

        self.modal_width = 59    # palette_file_dialog.nml:12
        self.modal_height = 20    # palette_file_dialog.nml:13

        self.preview.x = 3    # palette_file_dialog.nml:17
        self.preview.y = 16    # palette_file_dialog.nml:18
        self.preview.width = 30    # palette_file_dialog.nml:19
        self.preview.height = 1    # palette_file_dialog.nml:20
        self.preview.items = _bind(    # palette_file_dialog.nml:21
            lambda _o: [_tr('~P~review palette')],
            yielding=True,
        )
        self.preview.tooltips = _bind(    # palette_file_dialog.nml:22
            lambda _o: [_tr('Paint the palette under the cursor in the box beside the list')],
            yielding=True,
        )
