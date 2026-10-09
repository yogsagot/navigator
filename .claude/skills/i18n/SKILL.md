---
name: i18n
description: Translating Navigator -- navkit/i18n.py (tr, tr_n, tr_plain, LOCALE, catalogues, plural rules), the generator's live captions (`_tr` and yielding bindings for text/title/label_text/items/prompt literals), navigator/language.py (--language, [interface] language, $LANG, the user's locales/ beside navigator.ini), Options > Interface's Language choice, and tools/i18n.py extract/check. Use when adding user-visible text, adding a language, or when a caption does not follow a language change.
---

# Translation

**English text is the key; one TOML catalogue per language and layer.** DN fetched captions with
`GetString(dlTopName)` from one resource set per language (`RESOURCE/ENGLISH`, `RESOURCE/RUSSIAN`); this keeps the
file-per-language shape and drops the numbered ids. gettext was rejected on purpose (`.po`/`.mo`, extraction tooling).

## Pieces

- **`navkit/i18n.py`**: `tr(text)`, `tr_n(singular, plural, n, **values)` (formats `{n}` and the values),
  `tr_plain(text)` (lookup ignoring `~` hotkey marks -- what menu anchors use), `LOCALE.code` (reactive),
  `register_package()`/`register_directory()` (later wins, entry by entry), `languages()` (`{code: [meta] name}`),
  `PLURAL_RULES` (en, lv, ru/uk/be, ja/zh/ko; anything else counts like English).
- **Catalogues**: `navml/locales/<code>.toml` (the library's captions) and `navigator/locales/<code>.toml` (the
  application's), plus the user's `locales/` beside `navigator.ini`, read last. `[strings]` is read; `[unused]` is
  where `extract` parks translations nothing shows any more. An empty value means untranslated (English shows).
  A plural entry is a list of forms in the language's rule order (lv: one, other, zero -- `1 fails`, `2 faili`,
  `10 failu`).
- **`navigator/language.py`**: `install(config_dir)` registers the three places; `resolve(code)` takes a code, its
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
caption. An ordinary binding still refuses.

An explicit `tr(...)` in a markup expression makes the line a binding too (it reads the language).

## Rules for new text

- **Wrap every user-visible literal** in Python: `tr("Error")`. The key must be a literal so `tools/i18n.py` sees it.
- **Whole sentences with named placeholders**: `tr("File {name}\nalready exists.").format(name=path.name)`. Never
  glue translated fragments.
- **Counts**: `tr_n("{n} file", "{n} files", n)`, never `"s" if n != 1`.
- **Live**: text drawn in `render()` is live by itself. Text assigned once to a long-lived widget must be
  `bind(lambda _o: tr("..."), yielding=True)`; a message box built per use can take a plain `tr()`.
- **The hotkey belongs to the translator**: `"~N~ame" = "~V~ārds"`.
- **Not translated**: `Command.title` stays English in the class (the key bar calls `tr` at render), key specs, ini
  keys and comments, history ids, paths, encoding names, stderr/log text, programmer exceptions, `strerror`.
- **Never compare a shown caption with an English literal**; menu anchors already go through `tr_plain`.

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
dialog or menu whose translated hotkeys clash where the English did not. `packaging/linux/build.sh` asserts every
catalogue is packaged.

## Tests

`tests/conftest.py`'s autouse `_english` empties the registered places and sets `LOCALE.code = "en"` around every
test; `tests/test_i18n.py` registers a temporary `lv.toml` with `register_directory`.
