"""File > Encoding > Encryption's box (``EncryptDialog``): what it refuses
OK for, what it answers, and a program not installed offered greyed with
what to install -- the programs stood in for."""

from __future__ import annotations

import pytest

from navigator.lib.file_ops import encrypt
from navigator.settings import SETTINGS, EncryptionData


@pytest.fixture
def only_gpg(monkeypatch):
    monkeypatch.setattr(encrypt, "available", lambda: ("gpg",))
    monkeypatch.setattr(SETTINGS.encryption, "tool", "age")  # the last choice, no longer installed
    monkeypatch.setattr(SETTINGS.encryption, "method", "passphrase")
    monkeypatch.setattr(SETTINGS.encryption, "recipients", "")


def dialog():
    from navigator.widgets.file_ops.encrypt_dialog import EncryptDialog

    return EncryptDialog()


def test_a_program_not_installed_is_greyed_with_what_to_install_and_not_chosen(only_gpg):
    box = dialog()
    age = EncryptionData.TOOLS.index("age")
    assert not box.tool.item_enabled(age) and box.tool.item_enabled(EncryptionData.TOOLS.index("gpg"))
    assert "install the age package" in box.tool.tooltips[age]
    assert EncryptionData.TOOLS[box.tool.value] == "gpg"  # the last choice is gone: one installed instead


def test_a_passphrase_is_needed_twice_alike(only_gpg):
    box = dialog()
    assert box.problem() == "Type a passphrase."
    box.passphrase.value, box.confirm.value = "a", "b"
    assert box.problem() == "The passphrases do not match."
    assert box.accept() is None
    box.confirm.value = "a"
    assert box.problem() == ""
    assert box.passphrase.entry.password and box.confirm.entry.password  # typed unseen


def test_recipients_are_needed_for_the_recipients_method(only_gpg):
    box = dialog()
    box.method.value = EncryptionData.METHODS.index("recipients")
    assert box.problem() == "Name at least one recipient."
    box.recipients.value = " alice  bob "
    assert box.problem() == ""


def test_the_answer_holds_only_what_its_method_uses(only_gpg):
    box = dialog()
    box.passphrase.value = box.confirm.value = "secret"
    box.recipients.value = "alice"  # left over, and not what the passphrase method uses
    box.options.value = 1 | 2
    assert box.accept() == {"tool": "gpg", "method": "passphrase", "passphrase": "secret", "recipients": [],
                            "armor": True, "delete_originals": True}
    box.method.value = EncryptionData.METHODS.index("recipients")
    box.options.value = 0
    assert box.accept() == {"tool": "gpg", "method": "recipients", "passphrase": None, "recipients": ["alice"],
                            "armor": False, "delete_originals": False}


def test_no_program_installed_refuses_ok(monkeypatch):
    monkeypatch.setattr(encrypt, "available", lambda: ())
    box = dialog()
    box.passphrase.value = box.confirm.value = "x"
    assert box.problem().endswith("is not installed")
