"""``SettingsPage`` and the ``built()`` hook it seeds from.

A setup page's controls say which setting each edits (``key:``); the page
seeds them -- value and tooltip -- once the tree exists, and answers their
values, converted back, from ``accept()``.  Each conversion is read off the
control's kind and the setting's declaration.
"""

from __future__ import annotations

import pytest

from navml.checks import check
from navml.generator import generate
from navml.parser import parse
from navml.resolve import resolve

from navigator.settings import SystemData, RemoteData


def built_class(text: str):
    resolved = resolve(parse(text, filename="widget.nml"))
    check(resolved)
    namespace: dict = {"__name__": "generated"}
    exec(compile(generate(resolved), "widget_nml.py", "exec"), namespace)
    return namespace["Page_"]


IMPORTS = (
    "from navml.widgets.dialog.check_boxes import CheckBoxes\n"
    "from navml.widgets.dialog.field import Field\n"
    "from navml.widgets.dialog.masked_field import MaskedField\n"
    "from navml.widgets.dialog.radio_buttons import RadioButtons\n"
    "from navigator.widgets.setup.settings_page import SettingsPage\n\n"
)

PAGE = IMPORTS + (
    "Page_(SettingsPage):\n"
    "    class section_name: \"system\"\n"
    "    CheckBoxes:\n"
    "        id: options\n"
    "        key: \"OPTIONS\"\n"
    "        items: ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']\n"
    "    Field:\n"
    "        id: temp_dir\n"
    "        key: \"temp_dir\"\n"
    "    RadioButtons:\n"
    "        id: on_error\n"
    "        key: \"on_error\"\n"
    "        items: ['dialog', 'crash']\n"
    "    MaskedField:\n"
    "        id: stall_report\n"
    "        key: \"stall_report\"\n"
    "        mask: \"999\"\n"
    "    RadioButtons:\n"
    "        id: upload\n"
    "        key: \"remote.upload_changed\"\n"
    "        items: ['ask', 'always', 'never']\n"
)


def sections():
    system, remote = SystemData(), RemoteData()
    system.temp_dir = "/scratch"
    system.on_error = "crash"
    system.stall_report = 7
    system.show_hidden = False
    remote.upload_changed = "never"
    return system, remote


def test_each_kind_of_control_is_seeded_from_its_setting():
    system, remote = sections()
    page = built_class(PAGE)(section=system, sections={"remote": remote})
    assert page.options.value == system.to_bits(SystemData.OPTIONS)
    assert page.options.tooltips == SystemData.tooltips(SystemData.OPTIONS)
    assert page.temp_dir.value == "/scratch"
    assert page.on_error.value == 1
    assert page.stall_report.value == "007"
    assert page.upload.value == 2
    assert page.temp_dir.tooltip == SystemData.tooltip("temp_dir")


def test_accept_converts_back_and_answers_each_section_by_name():
    system, remote = sections()
    page = built_class(PAGE)(section=system, sections={"remote": remote})
    page.temp_dir.value = "  /tmp/x  "
    page.on_error.value = 0
    page.stall_report.value = " 12"
    page.upload.value = 0
    answer = page.accept()
    assert answer["system"]["temp_dir"] == "/tmp/x"
    assert answer["system"]["on_error"] == "dialog"
    assert answer["system"]["stall_report"] == 12
    assert answer["system"]["show_hidden"] is False
    assert answer["remote"] == {"upload_changed": "ask"}


def test_a_page_of_one_section_answers_it_flat():
    page = built_class(PAGE.split("    RadioButtons:\n        id: upload")[0])(section=sections()[0])
    answer = page.accept()
    assert answer["temp_dir"] == "/scratch"
    assert "system" not in answer


def test_a_number_that_will_not_read_keeps_the_setting():
    system, remote = sections()
    page = built_class(PAGE)(section=system, sections={"remote": remote})
    page.stall_report.value = "x1"
    assert page.accept()["system"]["stall_report"] == 7


def test_a_control_it_cannot_convert_says_so():
    text = IMPORTS + (
        "Page_(SettingsPage):\n"
        "    class section_name: \"system\"\n"
        "    Field:\n"
        "        id: on_error\n"
        "        key: \"stall_report\"\n"
    )
    with pytest.raises(TypeError, match="no conversion"):
        built_class(text)()


def test_built_runs_once_after_a_derived_documents_children_exist():
    base = built_class(IMPORTS + (
        "Page_(SettingsPage):\n"
        "    class section_name: \"system\"\n"
        "    Field:\n"
        "        id: temp_dir\n"
        "        key: \"temp_dir\"\n"
    ))
    calls = []

    class Counting(base):
        def built(self):
            calls.append(hasattr(self, "temp_dir"))
            super().built()

    Counting(section=sections()[0])
    assert calls == [True]
