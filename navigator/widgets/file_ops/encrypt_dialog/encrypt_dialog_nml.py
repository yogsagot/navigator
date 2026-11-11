# navml: generated
"""Generated from ``encrypt_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # encrypt_dialog.nml:1
from navml.widgets.dialog.check_boxes import CheckBoxes    # encrypt_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # encrypt_dialog.nml:3
from navml.widgets.dialog.field import Field    # encrypt_dialog.nml:4
from navml.widgets.dialog.label import Label    # encrypt_dialog.nml:5
from navml.widgets.dialog.radio_buttons import RadioButtons    # encrypt_dialog.nml:6

__navml_component__ = "EncryptDialog"

__all__ = ["EncryptDialog"]


class EncryptDialog(Dialog, _Component):
    """File > Encoding > Encryption > Encrypt.  Not DN's: a departure, asked for -- DOS

    Navigator encrypted nothing (``navigator.lib.file_ops.encrypt``).

    The program and what to encrypt to side by side, the passphrase twice or
    the recipients under them -- each greyed while the other is chosen -- and
    the two options last.
    """

    #: The document this class was generated from.
    __navml_source__ = "encrypt_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    tool_caption: Label    # encrypt_dialog.nml:20
    tool: RadioButtons    # encrypt_dialog.nml:30
    method_caption: Label    # encrypt_dialog.nml:38
    method: RadioButtons    # encrypt_dialog.nml:47
    passphrase: Field    # encrypt_dialog.nml:56
    confirm: Field    # encrypt_dialog.nml:67
    recipients: Field    # encrypt_dialog.nml:79
    choose_keys: Button    # encrypt_dialog.nml:92
    options: CheckBoxes    # encrypt_dialog.nml:102
    pick: Button    # encrypt_dialog.nml:112
    abandon: Button    # encrypt_dialog.nml:122

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_choose_keys_click(self, event: _Event) -> bool:    # encrypt_dialog.nml:92
        """``choose_keys`` raised an event whose handler is ``on_click``."""
        return False

    async def on_pick_click(self, event: _Event) -> bool:    # encrypt_dialog.nml:112
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # encrypt_dialog.nml:122
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.tool_caption = Label(parent=self)    # encrypt_dialog.nml:19
        self.tool = RadioButtons(parent=self)    # encrypt_dialog.nml:29
        self.method_caption = Label(parent=self)    # encrypt_dialog.nml:37
        self.method = RadioButtons(parent=self)    # encrypt_dialog.nml:46
        self.passphrase = Field(parent=self)    # encrypt_dialog.nml:55
        self.confirm = Field(parent=self)    # encrypt_dialog.nml:66
        self.recipients = Field(parent=self)    # encrypt_dialog.nml:78
        self.choose_keys = Button(parent=self)    # encrypt_dialog.nml:91
        self.options = CheckBoxes(parent=self)    # encrypt_dialog.nml:101
        self.pick = Button(parent=self)    # encrypt_dialog.nml:111
        self.abandon = Button(parent=self)    # encrypt_dialog.nml:121

        self.modal_width = 64    # encrypt_dialog.nml:15
        self.modal_height = 17    # encrypt_dialog.nml:16
        self.title = _bind(lambda _o: _tr('Encrypt Files'), yielding=True)    # encrypt_dialog.nml:17

        self.tool_caption.x = 2    # encrypt_dialog.nml:21
        self.tool_caption.y = 1    # encrypt_dialog.nml:22
        self.tool_caption.width = 12    # encrypt_dialog.nml:23
        self.tool_caption.height = 1    # encrypt_dialog.nml:24
        self.tool_caption.text = _bind(    # encrypt_dialog.nml:25
            lambda _o: _tr('Pr~o~gram'),
            yielding=True,
        )
        self.tool_caption.link = _bind(lambda _o: self.tool)    # encrypt_dialog.nml:26

        self.tool.x = 2    # encrypt_dialog.nml:31
        self.tool.y = 2    # encrypt_dialog.nml:32
        self.tool.width = 22    # encrypt_dialog.nml:33
        self.tool.height = 2    # encrypt_dialog.nml:34
        self.tool.items = _bind(    # encrypt_dialog.nml:35
            lambda _o: [_tr('~G~nuPG (gpg)'), _tr('ag~e~')],
            yielding=True,
        )

        self.method_caption.x = 26    # encrypt_dialog.nml:39
        self.method_caption.y = 1    # encrypt_dialog.nml:40
        self.method_caption.width = 14    # encrypt_dialog.nml:41
        self.method_caption.height = 1    # encrypt_dialog.nml:42
        self.method_caption.text = _bind(    # encrypt_dialog.nml:43
            lambda _o: _tr('Encrypt ~t~o'),
            yielding=True,
        )
        self.method_caption.link = _bind(lambda _o: self.method)    # encrypt_dialog.nml:44

        self.method.y = 2    # encrypt_dialog.nml:48
        self.method.height = 2    # encrypt_dialog.nml:49
        self.method.items = _bind(    # encrypt_dialog.nml:53
            lambda _o: [_tr('~P~assphrase'), _tr("~R~ecipients' keys")],
            yielding=True,
        )
        self.method.x = 26    # encrypt_dialog.nml:51
        self.method.width = _bind(lambda _o: max(0, _o.parent.width - 28))    # encrypt_dialog.nml:52

        self.passphrase.y = 5    # encrypt_dialog.nml:57
        self.passphrase.height = 1    # encrypt_dialog.nml:58
        self.passphrase.label_text = _bind(    # encrypt_dialog.nml:62
            lambda _o: _tr('Pa~s~sphrase'),
            yielding=True,
        )
        self.passphrase.label_width = 13    # encrypt_dialog.nml:63
        self.passphrase.disabled = _bind(lambda _o: self.method.value != 0)    # encrypt_dialog.nml:64
        self.passphrase.x = 2    # encrypt_dialog.nml:60
        self.passphrase.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # encrypt_dialog.nml:61

        self.confirm.y = 6    # encrypt_dialog.nml:68
        self.confirm.height = 1    # encrypt_dialog.nml:69
        self.confirm.label_text = _bind(    # encrypt_dialog.nml:73
            lambda _o: _tr('~C~onfirm'),
            yielding=True,
        )
        self.confirm.label_width = 13    # encrypt_dialog.nml:74
        self.confirm.disabled = _bind(lambda _o: self.method.value != 0)    # encrypt_dialog.nml:75
        self.confirm.x = 2    # encrypt_dialog.nml:71
        self.confirm.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # encrypt_dialog.nml:72

        self.recipients.y = 8    # encrypt_dialog.nml:80
        self.recipients.height = 1    # encrypt_dialog.nml:81
        self.recipients.label_text = _bind(    # encrypt_dialog.nml:85
            lambda _o: _tr('Rec~i~pients'),
            yielding=True,
        )
        self.recipients.label_width = 13    # encrypt_dialog.nml:86
        self.recipients.history_id = 'encrypt-recipients'    # encrypt_dialog.nml:87
        self.recipients.disabled = _bind(lambda _o: self.method.value != 1)    # encrypt_dialog.nml:88
        self.recipients.x = 2    # encrypt_dialog.nml:83
        self.recipients.width = _bind(lambda _o: max(0, _o.parent.width - 16))    # encrypt_dialog.nml:84

        self.choose_keys.text = _bind(    # encrypt_dialog.nml:93
            lambda _o: _tr('Ke~y~s...'),
            yielding=True,
        )
        self.choose_keys.y = 8    # encrypt_dialog.nml:94
        self.choose_keys.width = 11    # encrypt_dialog.nml:95
        self.choose_keys.height = 2    # encrypt_dialog.nml:96
        self.choose_keys.disabled = _bind(    # encrypt_dialog.nml:99
            lambda _o: self.method.value != 1 or self.tool.value != 0
        )
        self.choose_keys.x = _bind(    # encrypt_dialog.nml:98
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )
        self.choose_keys.on_click = self.on_choose_keys_click    # encrypt_dialog.nml:92

        self.options.y = 10    # encrypt_dialog.nml:103
        self.options.height = 2    # encrypt_dialog.nml:104
        self.options.items = _bind(    # encrypt_dialog.nml:108
            lambda _o: [_tr('~A~SCII armor'), _tr('~D~elete originals')],
            yielding=True,
        )
        self.options.tooltips = _bind(    # encrypt_dialog.nml:109
            lambda _o: [_tr('Write the encrypted files as text (gpg names them .asc)'), _tr('Remove each file once its encrypted copy is written')],
            yielding=True,
        )
        self.options.x = 3    # encrypt_dialog.nml:106
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # encrypt_dialog.nml:107

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # encrypt_dialog.nml:113
        self.pick.default = True    # encrypt_dialog.nml:114
        self.pick.x = 19    # encrypt_dialog.nml:115
        self.pick.width = 11    # encrypt_dialog.nml:116
        self.pick.height = 2    # encrypt_dialog.nml:117
        self.pick.y = _bind(    # encrypt_dialog.nml:119
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.pick.on_click = self.on_pick_click    # encrypt_dialog.nml:112

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # encrypt_dialog.nml:123
        self.abandon.x = 32    # encrypt_dialog.nml:124
        self.abandon.width = 11    # encrypt_dialog.nml:125
        self.abandon.height = 2    # encrypt_dialog.nml:126
        self.abandon.y = _bind(    # encrypt_dialog.nml:128
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.abandon.on_click = self.on_abandon_click    # encrypt_dialog.nml:122
