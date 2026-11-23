---
name: i18n
description: Translating Navigator -- navkit/i18n.py (tr, tr_n, tr_plain, LOCALE, catalogues, plural rules), the generator's live captions (`_tr` and yielding bindings for text/title/label_text/items/prompt literals), navigator/lib/config/language.py (--language, [interface] language, $LANG, the user's locales/ beside navigator.ini), Options > Interface's Language choice, and tools/i18n.py extract/check. Use when adding user-visible text, adding a language, or when a caption does not follow a language change.
---

# Translation

**English text is the key; one TOML catalogue per language and layer.** DN fetched captions with
`GetString(dlTopName)` from one resource set per language (`RESOURCE/ENGLISH`, `RESOURCE/RUSSIAN`); this keeps the
file-per-language shape and drops the numbered ids. gettext was rejected on purpose (`.po`/`.mo`, extraction tooling).

## Pieces

- **`navkit/i18n.py`**: `tr(text)`, `tr_n(singular, plural, n, **values)` (formats `{n}` and the values),
  `tr_plain(text)` (lookup ignoring `~` hotkey marks -- what menu anchors use), `LOCALE.code` (reactive),
  `register_package()`/`register_directory()` (later wins, entry by entry), `languages()` (`{code: [meta] name}`),
  `flags()` (`{code: [meta] flag}`, two letters, English `GB`) and `flag_emoji(region)`; Options > Interface puts
  the flag before each language's name at the Nerd glyph tier only (a departure, beside the icon gutter),
  `PLURAL_RULES` (en, lv, ru/uk/be, pl, cs, fr/pt, he, ar, ja/zh/ko; anything else -- de, es, it, tr -- counts
  like English; Turkish writes both forms the same, a noun after a number staying singular).
- **Catalogues**: `navml/locales/<code>.toml` (the library's captions) and `navigator/locales/<code>.toml` (the
  application's), plus the user's `locales/` beside `navigator.ini`, read last. `[strings]` is read; `[unused]` is
  where `extract` parks translations nothing shows any more. An empty value means untranslated (English shows).
  A plural entry is a list of forms in the language's rule order (lv: one, other, zero -- `1 fails`, `2 faili`,
  `10 failu`; ru/uk: one, few, many; pl: one (1 only), few, many -- `1 plik`, `22 pliki`, `5 plików`; cs: one,
  few (2-4), other; fr/pt: one (0 and 1), other; he: one, two, other; ar: zero, one, two, few, many, other, CLDR's).
  A catalogue named for a region (`zh_TW.toml`, Traditional Chinese) is found before its bare language
  (`language.resolve`), and takes the bare language's plural rule. `[meta] direction = "rtl"` (he,
  ar) mirrors the screen (`i18n.is_rtl`, the `navkit-bidi` skill).
- **`navigator/lib/config/language.py`**: `install(config_dir)` registers the three places; `resolve(code)` takes a code, its
  bare language (`lv_LV` to `lv`), or English; empty means the environment (`$LC_ALL`, `$LC_MESSAGES`, `$LANG`).
  Precedence: `--language`, `[interface] language`, environment, English. `main()` applies it before the app starts.
- **Options > Interface** has a *Language* `ChoiceField`; `Shell._interface_setup` applies a *changed* choice live
  (Cancel or the same choice leaves a session's `--language` standing).

## Markup is translated by the generator

A string literal of `text`, `title`, `label_text`, `items` or `prompt` (`navml.expression.TRANSLATED`) compiles to
`_bind(lambda _o: _tr('...'), yielding=True)`. Only literals that *are* the value are wrapped -- the whole
expression, a list item, a conditional's branch, an `or` -- never a fragment (`"~" + name`) or a format; a literal
with no letter is left alone. A target that is not reactive gets `_tr('...')` once, at construction.

**A yielding binding** (`bind(..., yielding=True)`, `navkit/reactive.py`) is a default: a plain assignment replaces
it instead of raising. That is what lets hand-written code keep setting `self.ok.text = tr("~Y~es")` over a markup
caption. A binding that reads properties only to *choose* between caption literals (a conditional whose branches,
or an `or` whose operands, are all literals -- Dialog's `"~Y~es" if root.buttons ... else "O~K~"`) yields too
(`_captions_only` in `navml/expression.py`); without that every progress box's `self.ok.text = ...` raised. An
ordinary binding still refuses.

An explicit `tr(...)` in a markup expression makes the line a binding too (it reads the language).

- **Extraction:** `tr()`/`tr_n()`/`tr_plain()`/`tr_noop()` calls with a literal first argument in any markup line are
  extracted like Python's. That covers property, set-once, `when`, declaration, handler and `commands:` lines.
- **No helper method needed:** a caption with a placeholder no longer needs a method in the `.py` half just to be
  seen (`compare_progress.nml`, `country_page.nml`).
- **`verbatim("X")`** keeps a symbol that has a letter in it (`"X"`, `"Aa"`) out of both translation and the
  catalogue.

## Rules for new text

- **Wrap every user-visible literal** in Python: `tr("Error")`. The key must be a literal so `tools/i18n.py` sees it.
- **Whole sentences with named placeholders**: `tr("File {name}\nalready exists.").format(name=path.name)`. Never
  glue translated fragments.
- **Counts**: `tr_n("{n} file", "{n} files", n)`, never `"s" if n != 1`.
- **One English caption meaning two things** gets a context: `tr("~B~ackground", context="job")` (the progress
  boxes' button) beside the Colors box's plain `"~B~ackground"`. The catalogue key is `"job|~B~ackground"`
  (`CONTEXT_SEPARATOR`, gettext's `msgctxt`), extracted from a literal `context=`; untranslated, it is English,
  never the other meaning's words. Markup captions have no context: a caption that needs one is set from Python.
- **An error a user is shown is translated where it is raised**: `raise OSError(errno.ENOENT, tr("Where it came
  from is not known"))`, `DriveGone(host, tr("Cannot connect to {host}: {reason}").format(...))` -- the raising thread
  reads the shared `LOCALE`. A module constant raised by name is `tr_noop("...")` and raised as `tr(CONST)`; a
  marker compared in code (`encrypt.BAD_PASSPHRASE`) stays English and is translated where shown. Text the code
  compares goes through one helper on both sides (`base.not_accessible`). **The root helper** (a process of its own,
  no catalogues) raises English; `elevate._helper_text` translates what arrives, every sentence listed in
  `elevate.HELPER_TEXTS`. `tests/test_i18n_raised.py` walks `navigator/` with `ast` and fails on any sentence raised
  as `OSError`/`DriveGone`/`ToolError`/`SplitError`... unwrapped (literal, f-string, `or`/`if` branch, or module
  constant), and on a helper sentence missing from the table -- `tools/i18n.py check` cannot see these, having no key
  to miss. Reuse a key's placeholder names (`{host}`, `{reason}`, `{name}`) so one sentence is one key.
- **Live**: text drawn in `render()` is live by itself. Text assigned once to a long-lived widget must be
  `bind(lambda _o: tr("..."), yielding=True)`; a message box built per use can take a plain `tr()`.
- **The hotkey belongs to the translator**: `"~N~ame" = "~V~ārds"`. Chinese, Japanese and Korean (`zh`, `zh_TW`,
  `ja`, `ko`) keep the
  English letter in ASCII parentheses after the caption, `"~N~ame" = "名前(~N~)"`, as CJK Windows and DOS
  programs did: nobody presses a kanji with Alt, an IME sits in the way. Turkish avoids `I`/`İ`/`ı` as a hotkey: `MenuBar.hotkey`
  compares `.lower()`, and `"İ".lower()` is two characters.
- **Measure in cells, never `len()`**: a CJK character is two cells. `navkit.bidi.display_width` measures,
  `fit_cells` cuts and `pad_cells` pads (ljust/rjust/center); StaticText's `wrapped()` breaks Chinese and Japanese
  between characters (with kinsoku: no closing mark at a line's start). Whatever sizes, aligns or cuts a
  translated caption goes through them. A Button whose caption is wider than its room takes the `▶◀` cells
  (`Button.crowded`); the key bar goes tight (one blank between items) when it would otherwise lose an F-key,
  and tighter still (no blank between a key and its caption, `F2Saglab.`) when tight is not enough --
  the editor's nine in Latvian; a command whose title is long for the bar gives a `key_title` (`Command.key_title`,
  extracted like `title`: the editor's F5 is DN's *Block*, F4 *Draw*),
  and the menu bar (`MenuBar.tight`) when its captions would reach `reserve`, the clock's cells the shell
  binds.
  At 80 columns DN's English key row is exactly full, so a CJK key-bar title must be two characters; three
  are fine only where the rest are two.
- **Not translated**: `Command.title` stays English in the class (the key bar calls `tr` at render), key specs, ini
  keys and comments, history ids, paths, encoding names, stderr/log text, programmer exceptions, `strerror`.
- **Never compare a shown caption with an English literal**; menu anchors already go through `tr_plain`. Where a
  catalogue has both `"~F~ile"` and a plain `"File"`, `tr_plain("File")` is the hotkeyed one's (the menu's):
  Japanese and Chinese translate them `ファイル(~F~)` and `ファイル`, and a window menu's `after: 'File'`
  raised `LookupError` while the plain one won.
- **Japanese's *Window* menu is `窓(~W~)` on purpose**, not `ウィンドウ(~W~)`: the 80-column bar is already
  crowded (`MenuBar.tight`), and a window's own menu joining it (`エディタ(E)`, `カレンダー(C)`) would push the
  longer caption under the clock. A menu-bar caption in a wide script is chosen for width first.

## Adding a language

**`python -m navml extract CODE [PACKAGE ...]`** (`navml/translate.py`) is the extractor, beside `navml build`: it
scans one package (a directory or a dotted name; the installed navml by default) and rewrites its
`locales/CODE.toml`, adding what is missing. A package other than navml is never asked for a key navml has. Text no
scan can see -- captions kept English in a table and passed to `tr()` where shown -- is named by a `strings()`
function in the package's `locales/__init__.py`, yielding `(key, where)`; Navigator's lists the palette's and the key
tables' captions. `tools/i18n.py` is that module run over both layers, plus `check`.

`./venv/bin/python tools/i18n.py extract de --name Deutsch` writes `navml/locales/de.toml` and
`navigator/locales/de.toml` with every key (`""`, each with where it is used). Fill them in; `extract` again keeps
what is written and adds what is new. `tools/i18n.py check [code]` exits 1 on untranslated or unused keys and on a
dialog or menu whose hotkeys clash: in English (`check_english`, said once) and in each catalogue, which is checked
even where the English clashes (it once skipped such a scope, and clashes hid behind it for a whole session). A scope
is a `.nml` block's direct children's captions, or one `items` list; menus and lists built in Python (context menus,
the Sort by box, the Columns dialog's list) are not seen and are checked by hand. `test_i18n` runs it. `packaging/linux/build.sh` asserts every
catalogue is packaged.

## Tests

`tests/conftest.py`'s autouse `_english` empties the registered places and sets `LOCALE.code = "en"` around every
test; `tests/test_i18n.py` registers a temporary `lv.toml` with `register_directory`.

**A translation must fit where it is shown.** `tests/test_settings_fit.py` opens Options > Settings in every shipped
language and fails on a check box or radio caption, a label, or a drop-down choice wider than its control (the
cut was silent: *Return to last cursor position* lost its end in English itself). `tests/test_dialog_fit.py` does the
same for every dialog and window that can be made with no arguments, and `tools/fitcheck.py --check` for all of them,
the screenshot scenes opening the ones that need arguments (`clipped()` lives there: a cluster's caption from its
column's start, a choice against its line, a button's caption against its whole face -- `Button.crowded` drops the
markers first -- and a one-row label). A finding is fixed by giving the control the room where the box has it, else
by a shorter translation -- never by cutting the English.
