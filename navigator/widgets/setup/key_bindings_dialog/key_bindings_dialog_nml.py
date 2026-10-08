# navml: generated
"""Generated from ``key_bindings_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.events import Event as _Event
from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button    # key_bindings_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # key_bindings_dialog.nml:2
from navml.widgets.dialog.label import Label    # key_bindings_dialog.nml:3
from navml.widgets.dialog.list_viewer import ListViewer    # key_bindings_dialog.nml:4
from navml.widgets.dialog.static_text import StaticText    # key_bindings_dialog.nml:5
from navigator.widgets.setup.key_bindings_dialog.binding_list import BindingList    # key_bindings_dialog.nml:6

__navml_component__ = "KeyBindingsDialog"

__all__ = ["KeyBindingsDialog"]


class KeyBindingsDialog(Dialog, _Component):
    """Options > Configuration > Key bindings: every key table's commands and

    their keys, a table to a category, laid out as Colors lays out its groups
    and items, with the buttons down the right as Edit environment has them.
    Not DOS Navigator's, which had no key editor: a departure, by request.
    """

    #: The document this class was generated from.
    __navml_source__ = "key_bindings_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    groups_caption: Label    # key_bindings_dialog.nml:18
    groups: ListViewer    # key_bindings_dialog.nml:27
    bindings_caption: Label    # key_bindings_dialog.nml:34
    bindings: BindingList    # key_bindings_dialog.nml:43
    detail: StaticText    # key_bindings_dialog.nml:52
    rebind: Button    # key_bindings_dialog.nml:60
    append: Button    # key_bindings_dialog.nml:70
    unbind: Button    # key_bindings_dialog.nml:79
    restore: Button    # key_bindings_dialog.nml:88
    reset: Button    # key_bindings_dialog.nml:97
    pick: Button    # key_bindings_dialog.nml:105
    abandon: Button    # key_bindings_dialog.nml:113

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_rebind_click(self, event: _Event) -> bool:    # key_bindings_dialog.nml:60
        """``rebind`` raised an event whose handler is ``on_click``."""
        return False

    async def on_append_click(self, event: _Event) -> bool:    # key_bindings_dialog.nml:70
        """``append`` raised an event whose handler is ``on_click``."""
        return False

    async def on_unbind_click(self, event: _Event) -> bool:    # key_bindings_dialog.nml:79
        """``unbind`` raised an event whose handler is ``on_click``."""
        return False

    async def on_restore_click(self, event: _Event) -> bool:    # key_bindings_dialog.nml:88
        """``restore`` raised an event whose handler is ``on_click``."""
        return False

    async def on_reset_click(self, event: _Event) -> bool:    # key_bindings_dialog.nml:97
        """``reset`` raised an event whose handler is ``on_click``."""
        return False

    async def on_pick_click(self, event: _Event) -> bool:    # key_bindings_dialog.nml:105
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # key_bindings_dialog.nml:113
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.groups_caption = Label(parent=self)    # key_bindings_dialog.nml:17
        self.groups = ListViewer(parent=self)    # key_bindings_dialog.nml:26
        self.bindings_caption = Label(parent=self)    # key_bindings_dialog.nml:33
        self.bindings = BindingList(parent=self)    # key_bindings_dialog.nml:42
        self.detail = StaticText(parent=self)    # key_bindings_dialog.nml:51
        self.rebind = Button(parent=self)    # key_bindings_dialog.nml:59
        self.append = Button(parent=self)    # key_bindings_dialog.nml:69
        self.unbind = Button(parent=self)    # key_bindings_dialog.nml:78
        self.restore = Button(parent=self)    # key_bindings_dialog.nml:87
        self.reset = Button(parent=self)    # key_bindings_dialog.nml:96
        self.pick = Button(parent=self)    # key_bindings_dialog.nml:104
        self.abandon = Button(parent=self)    # key_bindings_dialog.nml:112

        self.modal_width = 78    # key_bindings_dialog.nml:13
        self.modal_height = 22    # key_bindings_dialog.nml:14
        self.title = _bind(lambda _o: _tr('Key Bindings'), yielding=True)    # key_bindings_dialog.nml:15

        self.groups_caption.x = 2    # key_bindings_dialog.nml:19
        self.groups_caption.y = 2    # key_bindings_dialog.nml:20
        self.groups_caption.width = 12    # key_bindings_dialog.nml:21
        self.groups_caption.height = 1    # key_bindings_dialog.nml:22
        self.groups_caption.text = _bind(    # key_bindings_dialog.nml:23
            lambda _o: _tr('C~a~tegory'),
            yielding=True,
        )
        self.groups_caption.link = _bind(lambda _o: self.groups)    # key_bindings_dialog.nml:24

        self.groups.x = 2    # key_bindings_dialog.nml:28
        self.groups.y = 3    # key_bindings_dialog.nml:29
        self.groups.width = 19    # key_bindings_dialog.nml:30
        self.groups.height = 15    # key_bindings_dialog.nml:31

        self.bindings_caption.x = 22    # key_bindings_dialog.nml:35
        self.bindings_caption.y = 2    # key_bindings_dialog.nml:36
        self.bindings_caption.width = 12    # key_bindings_dialog.nml:37
        self.bindings_caption.height = 1    # key_bindings_dialog.nml:38
        self.bindings_caption.text = _bind(    # key_bindings_dialog.nml:39
            lambda _o: _tr('Co~m~mands'),
            yielding=True,
        )
        self.bindings_caption.link = _bind(lambda _o: self.bindings)    # key_bindings_dialog.nml:40

        self.bindings.x = 22    # key_bindings_dialog.nml:44
        self.bindings.y = 3    # key_bindings_dialog.nml:45
        self.bindings.width = 42    # key_bindings_dialog.nml:46
        self.bindings.height = 15    # key_bindings_dialog.nml:47

        self.detail.x = 2    # key_bindings_dialog.nml:53
        self.detail.y = 18    # key_bindings_dialog.nml:54
        self.detail.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # key_bindings_dialog.nml:55
        self.detail.height = 2    # key_bindings_dialog.nml:56

        self.rebind.text = _bind(lambda _o: _tr('~R~ebind'), yielding=True)    # key_bindings_dialog.nml:61
        self.rebind.default = True    # key_bindings_dialog.nml:62
        self.rebind.x = 65    # key_bindings_dialog.nml:63
        self.rebind.y = 3    # key_bindings_dialog.nml:64
        self.rebind.width = 11    # key_bindings_dialog.nml:65
        self.rebind.height = 2    # key_bindings_dialog.nml:66
        self.rebind.on_click = self.on_rebind_click    # key_bindings_dialog.nml:60

        self.append.text = _bind(lambda _o: _tr('A~d~d'), yielding=True)    # key_bindings_dialog.nml:71
        self.append.x = 65    # key_bindings_dialog.nml:72
        self.append.y = 5    # key_bindings_dialog.nml:73
        self.append.width = 11    # key_bindings_dialog.nml:74
        self.append.height = 2    # key_bindings_dialog.nml:75
        self.append.on_click = self.on_append_click    # key_bindings_dialog.nml:70

        self.unbind.text = _bind(lambda _o: _tr('C~l~ear'), yielding=True)    # key_bindings_dialog.nml:80
        self.unbind.x = 65    # key_bindings_dialog.nml:81
        self.unbind.y = 7    # key_bindings_dialog.nml:82
        self.unbind.width = 11    # key_bindings_dialog.nml:83
        self.unbind.height = 2    # key_bindings_dialog.nml:84
        self.unbind.on_click = self.on_unbind_click    # key_bindings_dialog.nml:79

        self.restore.text = _bind(lambda _o: _tr('D~e~fault'), yielding=True)    # key_bindings_dialog.nml:89
        self.restore.x = 65    # key_bindings_dialog.nml:90
        self.restore.y = 9    # key_bindings_dialog.nml:91
        self.restore.width = 11    # key_bindings_dialog.nml:92
        self.restore.height = 2    # key_bindings_dialog.nml:93
        self.restore.on_click = self.on_restore_click    # key_bindings_dialog.nml:88

        self.reset.text = _bind(lambda _o: _tr('Re~s~et'), yielding=True)    # key_bindings_dialog.nml:98
        self.reset.x = 65    # key_bindings_dialog.nml:99
        self.reset.y = 11    # key_bindings_dialog.nml:100
        self.reset.width = 11    # key_bindings_dialog.nml:101
        self.reset.height = 2    # key_bindings_dialog.nml:102
        self.reset.on_click = self.on_reset_click    # key_bindings_dialog.nml:97

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # key_bindings_dialog.nml:106
        self.pick.x = 65    # key_bindings_dialog.nml:107
        self.pick.y = 13    # key_bindings_dialog.nml:108
        self.pick.width = 11    # key_bindings_dialog.nml:109
        self.pick.height = 2    # key_bindings_dialog.nml:110
        self.pick.on_click = self.on_pick_click    # key_bindings_dialog.nml:105

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # key_bindings_dialog.nml:114
        self.abandon.x = 65    # key_bindings_dialog.nml:115
        self.abandon.y = 15    # key_bindings_dialog.nml:116
        self.abandon.width = 11    # key_bindings_dialog.nml:117
        self.abandon.height = 2    # key_bindings_dialog.nml:118
        self.abandon.on_click = self.on_abandon_click    # key_bindings_dialog.nml:113
