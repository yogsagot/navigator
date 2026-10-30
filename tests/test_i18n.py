"""Translated text: ``navkit/i18n.py``, the generator's live captions, and
Navigator's choice of language (``navigator/lib/config/language.py``)."""

from __future__ import annotations

import pytest

from navkit.i18n import (
    LOCALE,
    catalogue,
    flag_emoji,
    flags,
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
"{n} byte" = ["", "", ""]
"{n} directory" = ["{n} direktorija", "", "{n} direktoriju"]
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


def test_a_plural_left_blank_stays_english(latvian):
    # What ``tools/i18n.py extract`` writes for a count nobody has translated.
    LOCALE.code = "lv"
    assert "{n} byte" not in catalogue("lv")
    assert tr_n("{n} byte", "{n} bytes", 1) == "1 byte"
    assert tr_n("{n} byte", "{n} bytes", 5) == "5 bytes"
    assert tr("{n} byte") == "{n} byte"


def test_one_form_left_blank_is_english_for_that_count(latvian):
    LOCALE.code = "lv"
    assert tr_n("{n} directory", "{n} directories", 1) == "1 direktorija"
    assert tr_n("{n} directory", "{n} directories", 2) == "2 directories"


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


def test_a_catalogue_names_its_flag(tmp_path):
    (tmp_path / "lv.toml").write_text('[meta]\nname = "Latviešu"\nflag = "lv"\n', encoding="utf-8")
    (tmp_path / "ru.toml").write_text('[meta]\nflag = "Россия"\n', encoding="utf-8")
    (tmp_path / "de.toml").write_text('[meta]\nname = "Deutsch"\n', encoding="utf-8")
    register_directory(tmp_path)
    assert flags() == {"en": "GB", "lv": "LV"}


def test_a_region_becomes_its_regional_indicators():
    assert flag_emoji("LV") == "\U0001f1f1\U0001f1fb"
    assert flag_emoji("gb") == "🇬🇧"
    assert flag_emoji("L") == flag_emoji("LVA") == flag_emoji("Ä1") == ""


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


def test_hebrew_rule():
    assert [plural_form("he", n) for n in (1, 2, 3, 10, 22)] == [0, 1, 2, 2, 2]


def test_arabic_rule():
    numbers = (0, 1, 2, 3, 10, 11, 99, 100, 102, 103, 111, 1000)
    assert [plural_form("ar", n) for n in numbers] == [0, 1, 2, 3, 3, 4, 4, 5, 5, 3, 4, 5]


def test_a_caption_is_found_without_its_hotkey(latvian):
    LOCALE.code = "lv"
    assert tr_plain("Name") == "Vārds"


def test_a_menu_s_hotkeyed_caption_wins_over_the_same_words_plain(tmp_path):
    # Japanese writes the menu's "~F~ile" with its hotkey after it and a plain
    # "File" without; a menu anchor "File" looks for the first.  Either order.
    for keys in (('"~F~ile" = "ファイル(~F~)"', '"File" = "ファイル"'),
                 ('"File" = "ファイル"', '"~F~ile" = "ファイル(~F~)"')):
        (tmp_path / "ja.toml").write_text("[strings]\n" + "\n".join(keys) + "\n", encoding="utf-8")
        register_directory(tmp_path)
        LOCALE.code = "ja"
        assert tr_plain("File") == "ファイル(F)"


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
    assert compiled.value == "_bind(lambda _o: _tr('Move') if _o.move else _tr('Copy'), yielding=True)"


def test_a_choice_between_captions_yields_but_a_property_in_the_value_does_not():
    # Dialog's OK reads ``buttons`` only to pick a caption; a derived box's
    # ``self.ok.text = tr("~S~top")`` replaces it (FindProgress raised before).
    assert compile_expression('"Yes" if self.n == 2 else "OK"', translate=True).yielding
    assert compile_expression('self.name or "Untitled"', translate=True).yielding is False
    assert compile_expression('"Yes" if self.n else self.name', translate=True).yielding is False
    assert compile_expression('["Yes", self.name]', translate=True).yielding is False


@pytest.mark.parametrize("module, name, caption", [
    ("navigator.widgets.manager.find_progress.find_progress", "FindProgress", "Cancel"),
    ("navigator.widgets.viewer.search_progress.search_progress", "SearchProgress", "~S~top"),
    ("navigator.widgets.file_ops.write_win.write_win", "WriteWin", "~C~ancel"),
    ("navigator.widgets.file_ops.delete_dialog.delete_dialog", "DeleteDialog", "~Y~es"),
    ("navigator.widgets.file_ops.count_progress.count_progress", "CountProgress", "~C~ancel"),
    ("navigator.widgets.file_ops.delete_progress.delete_progress", "DeleteProgress", "~C~ancel"),
    ("navigator.widgets.file_ops.copy_progress.copy_progress", "CopyProgress", "~S~top"),
])
def test_a_box_that_renames_its_ok_button_can_be_built(module, name, caption):
    """Dialog's OK caption reads ``buttons``; it must still yield to these.

    A progress box is only built once a job outlasts ``PROGRESS_DELAY``, so a
    suite on a fast disk never saw one raise -- a slow CI runner did.
    """
    import importlib

    box = getattr(importlib.import_module(module), name)()
    assert box.ok.text == caption


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
    from navigator.lib.config import language
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


def test_extract_adds_what_is_missing_and_keeps_what_is_written(tmp_path):
    from navml.__main__ import main
    from navml.translate import read

    package = tmp_path / "plugin"
    (package / "locales").mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (package / "locales" / "__init__.py").write_text(
        "def strings():\n    yield 'From a table', 'plugin/table.py'\n"
    )
    (package / "box.nml").write_text("Label:\n    text: \"Hello\"\n")
    (package / "code.py").write_text(
        "from navkit.i18n import tr, tr_n\n"
        "tr('Goodbye')\n"
        "tr_n('{n} file', '{n} files', 2)\n"
        "tr('Cancel')\n"  # navml's own: its catalogue answers it
    )
    (package / "locales" / "lv.toml").write_text(
        '[meta]\nname = "Latviešu"\n\n[strings]\n"Goodbye" = "Uz redzēšanos"\n"Gone" = "Prom"\n'
    )

    assert main(["extract", "lv", str(package)]) == 0
    written = read(package / "locales" / "lv.toml")
    assert written["meta"] == {"name": "Latviešu"}
    assert written["strings"] == {
        "Hello": "",
        "Goodbye": "Uz redzēšanos",
        "{n} file": ["", "", ""],
        "From a table": "",
    }
    assert written["unused"] == {"Gone": "Prom"}


# -- tools/i18n.py check -------------------------------------------------------------------


def _i18n_tool():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / "tools" / "i18n.py"
    spec = importlib.util.spec_from_file_location("i18n_tool", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_an_english_clash_is_said_and_a_translation_is_checked_all_the_same():
    tool = _i18n_tool()
    scope = ["~A~ttributes", "~A~rchives first", "~N~ame", "~E~xtension"]
    assert tool._letters(scope) == ["'~A~ttributes' and '~A~rchives first' share ~a~"]
    # The English clash is said once, by check_english, not again per language;
    # a translation's own clash is still found under it.
    strings = {"~A~ttributes": "~A~tribūti", "~A~rchives first": "A~r~hīvi", "~N~ame": "~V~ārds",
               "~E~xtension": "~V~ērsija"}
    assert tool._clashes(scope, strings) == ["'~V~ārds' and '~V~ērsija' share ~v~"]


def test_every_catalogue_and_the_english_captions_pass_the_check():
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    done = subprocess.run([sys.executable, "tools/i18n.py", "check"], cwd=root, capture_output=True, text=True)
    assert done.returncode == 0, done.stdout


# -- Chinese and Japanese: two cells to a character ---------------------------


def test_a_cjk_sentence_wraps_by_cells_between_characters():
    from navkit.bidi import display_width
    from navml.widgets.dialog.static_text.static_text import wrapped

    lines = wrapped("文件已存在。是否覆盖？这是一个很长的句子。", 16)
    assert all(display_width(line) <= 16 for line in lines)
    assert "".join(lines) == "文件已存在。是否覆盖？这是一个很长的句子。"
    assert display_width(lines[0]) == 16            # filled, not broken at a blank


def test_kinsoku_keeps_a_closing_mark_off_the_start_of_a_line():
    from navml.widgets.dialog.static_text.static_text import wrapped

    # Seven characters fill 14 cells; the full stop goes down with the 字.
    lines = wrapped("一二三四五六七。八", 14)
    assert lines == ["一二三四五六", "七。八"]


def test_a_hotkey_mark_takes_no_cells_in_a_wrapped_line():
    from navml.widgets.dialog.static_text.static_text import wrapped

    assert wrapped("名前(~N~)", 7) == ["名前(~N~)"]    # 名前(N): seven cells
    assert wrapped("名前(~N~) ファイル", 15) == ["名前(~N~) ファイ", "ル"]


def test_fit_and_pad_count_cells():
    from navkit.bidi import fit_cells, pad_cells

    assert fit_cells("ファイル", 5) == "ファ"          # the third would straddle
    assert fit_cells("Files", 3) == "Fil"
    assert pad_cells("失败", 6) == "失败  "
    assert pad_cells("失败", 6, "right") == "  失败"
    assert pad_cells("失败", 7, "center") == " 失败  "
    assert pad_cells("FAILED", 3) == "FAILED"         # never cut


def test_a_menu_box_is_as_wide_as_its_widest_cjk_caption(terminal):
    from navml.widgets.menu.menu_box import MenuBox
    from navml.widgets.menu.menu_item import MenuItem
    from navml.widgets.menu.sub_menu import SubMenu

    menu = SubMenu(text="~F~ile")
    menu.add(MenuItem(text="コピー(~C~)"))
    width, _ = MenuBox.measure(menu, title="ブックマーク")
    assert width == max(len("コピー(C)") + 3 + 6, 12 + 8)


def test_a_caption_too_wide_for_its_button_takes_the_markers_cells(terminal):
    from navml.widgets.dialog.button import Button
    from tests.conftest import settle

    button = Button(text="O~K~", x=0, y=0, width=11, height=2)
    settle()
    assert not button.crowded and (button.caption.x, button.caption.width) == (1, 8)
    button.text = "いいえ(~N~)"                  # nine cells
    settle()
    assert button.crowded and (button.caption.x, button.caption.width) == (0, 10)


def test_a_crowded_key_bar_drops_the_second_blank_between_items(monkeypatch):
    from navigator.widgets.shell.keybar.keybar import Hint, KeyBar

    bar = KeyBar(x=0, y=0, width=24, height=1)
    english = [("F1", Hint("Help")), ("F2", Hint("User"))]
    monkeypatch.setattr(bar, "_row", lambda: english)
    assert [(start, width) for _, _, start, width in bar.items()] == [(0, 9), (9, 9)]   # " F1 Help "
    wide = [("F1", Hint("帮助")), ("F2", Hint("用户")), ("F3", Hint("查看"))]
    monkeypatch.setattr(bar, "_row", lambda: wide)
    # Loose, 9 cells apiece would end the third at 25; tight, "F1 帮助 " is 8.
    assert [(start, width) for _, _, start, width in bar.items()] == [(0, 8), (8, 8), (16, 8)]


def test_a_crowded_menu_bar_keeps_one_blank_between_captions(terminal):
    from navml.widgets.menu.menu_bar import MenuBar
    from navml.widgets.menu.sub_menu import SubMenu

    bar = MenuBar(x=0, y=0, width=30, height=1)
    for text in ("~F~ile", "~D~isk"):
        bar.add(SubMenu(text=text))
    assert not bar.tight() and [bar.item_span(i) for i in (0, 1)] == [(1, 6), (7, 6)]
    bar.reserve = 20                            # ten cells left: " File  Disk " needs 13
    assert bar.tight() and [bar.item_span(i) for i in (0, 1)] == [(1, 5), (6, 5)]
