"""Translated text: ``navkit/i18n.py``, the generator's live captions, and
Navigator's choice of language (``navigator/language.py``)."""

from __future__ import annotations

import pytest

from navkit.i18n import (
    LOCALE,
    catalogue,
    languages,
    plural_form,
    register_directory,
    tr,
    tr_n,
    tr_plain,
)
from navkit.reactive import ReactiveError, bind, is_bound, reactive
from navml.expression import compile_expression
from navml.generator import generate
from navml.parser import parse
from navml.resolve import resolve

from tests.conftest import settle

LV = """
[meta]
name = "Latviešu"

[strings]
"Make directory" = "Izveidot direktoriju"
"~N~ame" = "~V~ārds"
"Cancel" = "Atcelt"
"{n} file" = ["{n} fails", "{n} faili", "{n} failu"]
"Unfinished" = ""
"""


@pytest.fixture
def latvian(tmp_path):
    (tmp_path / "lv.toml").write_text(LV, encoding="utf-8")
    register_directory(tmp_path)
    return tmp_path


# -- looking text up ---------------------------------------------------------


def test_english_needs_no_catalogue():
    assert tr("Make directory") == "Make directory"


def test_a_known_string_is_translated(latvian):
    LOCALE.code = "lv"
    assert tr("Make directory") == "Izveidot direktoriju"
    assert tr("~N~ame") == "~V~ārds"


def test_an_unknown_or_empty_one_stays_english(latvian):
    LOCALE.code = "lv"
    assert tr("Quit") == "Quit"
    assert tr("Unfinished") == "Unfinished"


def test_a_later_directory_wins_entry_by_entry(latvian, tmp_path_factory):
    mine = tmp_path_factory.mktemp("mine")
    (mine / "lv.toml").write_text('[strings]\n"Cancel" = "Atsaukt"\n', encoding="utf-8")
    register_directory(mine)
    LOCALE.code = "lv"
    assert tr("Cancel") == "Atsaukt"
    assert tr("Make directory") == "Izveidot direktoriju"


def test_a_broken_catalogue_is_english(tmp_path):
    (tmp_path / "lv.toml").write_text("[strings\n", encoding="utf-8")
    register_directory(tmp_path)
    LOCALE.code = "lv"
    assert catalogue("lv") == {}
    assert tr("Cancel") == "Cancel"


def test_languages_name_themselves(latvian):
    assert languages() == {"en": "English", "lv": "Latviešu"}


# -- counts ------------------------------------------------------------------


def test_english_counts_one_and_the_rest():
    assert tr_n("{n} file", "{n} files", 1) == "1 file"
    assert tr_n("{n} file", "{n} files", 0) == "0 files"


@pytest.mark.parametrize(
    "n, text", [(1, "1 fails"), (21, "21 fails"), (2, "2 faili"), (0, "0 failu"),
                (11, "11 failu"), (10, "10 failu"), (111, "111 failu")],
)
def test_latvian_has_three_forms(latvian, n, text):
    LOCALE.code = "lv"
    assert tr_n("{n} file", "{n} files", n) == text


def test_russian_rule():
    assert [plural_form("ru", n) for n in (1, 2, 5, 11, 21, 22, 25)] == [0, 1, 2, 2, 0, 1, 2]


def test_a_caption_is_found_without_its_hotkey(latvian):
    LOCALE.code = "lv"
    assert tr_plain("Name") == "Vārds"


# -- following the language --------------------------------------------------


class Holder:
    text: str = reactive("")


def test_a_binding_through_tr_follows_the_language(latvian):
    holder = Holder()
    holder.text = bind(lambda _o: tr("Cancel"))
    assert holder.text == "Cancel"
    LOCALE.code = "lv"
    settle()
    assert holder.text == "Atcelt"


def test_a_yielding_binding_gives_way_to_a_value():
    holder = Holder()
    holder.text = bind(lambda _o: tr("Cancel"), yielding=True)
    holder.text = "~Y~es"
    assert holder.text == "~Y~es"
    assert not is_bound(holder, Holder.text)


def test_an_ordinary_binding_still_refuses_one():
    holder = Holder()
    holder.text = bind(lambda _o: tr("Cancel"))
    with pytest.raises(ReactiveError):
        holder.text = "~Y~es"


# -- the compiler ------------------------------------------------------------


def test_a_caption_literal_becomes_a_yielding_binding():
    compiled = compile_expression('"Cancel"', translate=True)
    assert compiled.value == "_bind(lambda _o: _tr('Cancel'), yielding=True)"


def test_every_caption_of_a_list_and_a_conditional_is_wrapped():
    compiled = compile_expression('["~Y~es", "~N~o"]', translate=True)
    assert compiled.expression == "[_tr('~Y~es'), _tr('~N~o')]"
    compiled = compile_expression('"Move" if self.move else "Copy"', translate=True)
    assert compiled.value == "_bind(lambda _o: _tr('Move') if _o.move else _tr('Copy'))"


def test_a_fragment_or_a_letterless_literal_is_not():
    assert compile_expression('"~" + self.name', translate=True).translated is False
    assert compile_expression('"─"', translate=True).value == "'─'"
    assert compile_expression('"%d files" % self.n', translate=True).translated is False


def test_an_explicit_tr_call_is_followed():
    assert compile_expression('tr("Copy")').value == "_bind(lambda _o: tr('Copy'), yielding=True)"


def test_untranslated_properties_are_left_alone():
    assert compile_expression('"mkdir"').value == "'mkdir'"


def test_generated_captions_follow_the_language(latvian):
    document = parse(
        "from navml.widgets.dialog.button import Button\n"
        "from navml.widgets.dialog.dialog import Dialog\n"
        "Box(Dialog):\n"
        '    title: "Make directory"\n'
        "    Button:\n"
        "        id: no\n"
        '        text: "Cancel"\n',
        filename="box.nml",
    )
    source = generate(resolve(document))
    namespace: dict = {"__name__": "generated"}
    exec(compile(source, "box_nml.py", "exec"), namespace)
    box = namespace["Box"]()
    assert (box.title, box.no.text) == ("Make directory", "Cancel")
    LOCALE.code = "lv"
    settle()
    assert (box.title, box.no.text) == ("Izveidot direktoriju", "Atcelt")


# -- Navigator's choice -------------------------------------------------------


def test_the_environment_picks_a_known_language(latvian, monkeypatch):
    from navigator import language

    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.delenv("LC_MESSAGES", raising=False)
    monkeypatch.setenv("LANG", "lv_LV.UTF-8")
    assert language.resolve("") == "lv"
    monkeypatch.setenv("LANG", "de_DE.UTF-8")
    assert language.resolve("") == "en"
    assert language.resolve("lv") == "lv"
    assert language.resolve("xx") == "en"


def test_menu_anchors_are_english_whatever_is_shown(latvian):
    from navml.widgets.menu.menu_item import MenuItem
    from navml.widgets.menu.sub_menu import SubMenu

    menu = SubMenu()
    item = menu.add(MenuItem())
    item.text = bind(lambda _o: tr("~N~ame"), yielding=True)
    LOCALE.code = "lv"
    settle()
    assert menu.entry("Name") is item
    assert menu.entry("Vārds") is item
