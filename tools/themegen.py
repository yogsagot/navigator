#!/usr/bin/env python3
"""Write Navigator's modern themes from their role palettes.

The DOS themes are transcriptions of DOS Navigator's ``.PAL`` files and are
written by ``tools/palconv.py``.  These have no ``.PAL`` behind them: each is a
handful of named colours -- *roles*, such as the ground panels sit on, the
accent the cursor wears, the colour of a directory -- and one table shared by
all of them says which role every palette slot draws.  So a theme is decided
in one place, and a slot means the same thing in every modern theme::

    ./venv/bin/python tools/themegen.py            # write the sheets
    ./venv/bin/python tools/themegen.py --check    # exit 1 if any is stale

The sheets have the shape palconv gives the DOS ones -- every slot, in the
Colors dialog's groups and order, then Navigator's own entries -- so Options >
Colors, Store palette and the tests treat them alike.  Colours are exact RGB,
written once each as ``$color-<role>``: a modern theme looks as designed on a
256-colour or truecolor terminal, and with ``--colors 16`` the renderer picks
the nearest of the sixteen.

No theme paints magenta, purple or violet, at the user's request: a scheme
that has one (Nord's purple, Solarized's violet and magenta) leaves it out and
gives its job to another of its colours.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from navigator.lib.appearance.palette import DERIVED  # noqa: E402
from palconv import SLOTS  # noqa: E402 -- the slots and their comments, as the DOS themes have them

OUT = ROOT / "navigator" / "styles" / "themes"

#: Every role a theme gives a colour, with what it is for.
ROLES = {
    "desktop": "behind the windows",
    "ground": "panels, the viewer and the editor",
    "ground_alt": "the editor's current line",
    "surface": "dialogs",
    "raised": "buttons and scroll bars",
    "field": "input lines, lists and trees in a dialog",
    "field_focus": "the input line being typed in",
    "overlay": "menus, the menu bar and the key bar",
    "border": "frames",
    "border_dim": "the frame of a window without focus",
    "shadow": "a button's shadow",
    "text": "ordinary text",
    "text_dim": "secondary text: titles, totals",
    "text_faint": "disabled items",
    "text_strong": "emphasis",
    "accent": "the cursor and the focused control",
    "on_accent": "text on the accent",
    "on_accent_alt": "a hotkey or a marked file under the cursor",
    "on_accent_faint": "a disabled item under the cursor",
    "selection": "selected text, and the cursor where the focus is not",
    "on_selection": "text on the selection",
    "hotkey": "a hotkey letter",
    "marked": "a marked file",
    "dir": "directories",
    "exec": "executables",
    "archive": "archives",
    "image": "images",
    "media": "audio and video",
    "document": "documents, devices and sockets",
    "source": "source code",
    "link": "symbolic links",
    "broken": "a link that points nowhere",
    "temp": "backups and temporaries",
    "comment": "comments",
    "string": "strings",
    "number": "numbers",
    "keyword": "keywords",
    "heading": "headings, in the editor and the viewer",
    "symbol": "operators and punctuation",
    "warn": "warnings: the error box's icons",
    "error": "the error box",
    "error_shadow": "a button's shadow on the error box",
    "modified": "a changed file's title in the editor",
    "drop_shadow": "the shadow a window, a dialog or a menu casts",
    "drop_shadow_text": "what shows through a drop shadow",
    "on_error": "text on the error box",
}

#: name -> (description, credit, roles).
THEMES: dict[str, tuple[str, str, dict[str, str]]] = {
    "ember": (
        "Ember -- warm charcoal, parchment text, one amber accent",
        "An original Navigator palette.",
        {
            "desktop": "#141312", "ground": "#1c1a19", "ground_alt": "#2a2624",
            "surface": "#57504a", "raised": "#6c635b", "field": "#3e3833", "field_focus": "#161413",
            "overlay": "#2c2826", "border": "#a89c8e", "border_dim": "#655d55", "shadow": "#0c0b0a",
            "text": "#e8e2d9", "text_dim": "#b3aa9f", "text_faint": "#958b80", "text_strong": "#fff7ea",
            "accent": "#f59e42", "on_accent": "#1c1a19", "on_accent_alt": "#6b3300", "on_accent_faint": "#8a4f14",
            "selection": "#5a4630", "on_selection": "#fff3e0",
            "hotkey": "#7fd1d8", "marked": "#f2c46d",
            "dir": "#fff7ea", "exec": "#9ccf8a", "archive": "#e8846a", "image": "#6fc2c9",
            "media": "#d9a05b", "document": "#c9b99a", "source": "#9cc6e8", "link": "#86bdb1",
            "broken": "#ef6461", "temp": "#7a7168",
            "comment": "#8f8579", "string": "#b5cc7a", "number": "#e5c07b", "keyword": "#f59e42", "heading": "#f59e42",
            "symbol": "#d4c6b0",
            "warn": "#f2c46d", "error": "#9e3a32", "on_error": "#fff3e0", "error_shadow": "#0c0b0a", "modified": "#f2c46d", "drop_shadow": "#0b0a09", "drop_shadow_text": "#5a534c",
        },
    ),
    "paper": (
        "Paper -- a warm off-white page, ink text, a vermilion accent",
        "An original Navigator palette.",
        {
            "desktop": "#ddd6c8", "ground": "#f6f3ec", "ground_alt": "#ebe6db",
            "surface": "#ebe5d8", "raised": "#d2c9b8", "field": "#ddd5c6", "field_focus": "#ffffff",
            "overlay": "#e1dacb", "border": "#8a8175", "border_dim": "#aea597", "shadow": "#9e9586",
            "text": "#2b2b2b", "text_dim": "#5f5a52", "text_faint": "#857e73", "text_strong": "#000000",
            "accent": "#c2410c", "on_accent": "#ffffff", "on_accent_alt": "#ffe2b8", "on_accent_faint": "#f0a582",
            "selection": "#f2cdb5", "on_selection": "#2b2b2b",
            "hotkey": "#0e7490", "marked": "#9a6700",
            "dir": "#1d4ed8", "exec": "#15803d", "archive": "#b45309", "image": "#0e7490",
            "media": "#a16207", "document": "#57534e", "source": "#1e40af", "link": "#0f766e",
            "broken": "#b91c1c", "temp": "#9c958a",
            "comment": "#78716c", "string": "#15803d", "number": "#b45309", "keyword": "#1d4ed8", "heading": "#1d4ed8",
            "symbol": "#57534e",
            "warn": "#ffe2b8", "error": "#b91c1c", "on_error": "#ffffff", "error_shadow": "#5c1010", "modified": "#b45309", "drop_shadow": "#c6bdad", "drop_shadow_text": "#6f685d",
        },
    ),
    "nord": (
        "Nord -- arctic blue-greys, frost blues and a muted aurora",
        "Nord by Arctic Ice Studio and Sven Greb (nordtheme.com), MIT licence.  Its purple is left out:"
        " numbers take its orange, audio and video its darkest frost.",
        {
            "desktop": "#242933", "ground": "#2e3440", "ground_alt": "#3b4252",
            "surface": "#434c5e", "raised": "#5e6a82", "field": "#4c566a", "field_focus": "#2e3440",
            "overlay": "#3b4252", "border": "#7b88a1", "border_dim": "#5b667b", "shadow": "#15181e",
            "text": "#d8dee9", "text_dim": "#aeb6c4", "text_faint": "#8a95aa", "text_strong": "#eceff4",
            "accent": "#88c0d0", "on_accent": "#2e3440", "on_accent_alt": "#8f4a2c", "on_accent_faint": "#46707c",
            "selection": "#4c566a", "on_selection": "#eceff4",
            "hotkey": "#ebcb8b", "marked": "#ebcb8b",
            "dir": "#eceff4", "exec": "#a3be8c", "archive": "#d08770", "image": "#8fbcbb",
            "media": "#81a1c1", "document": "#e5e9f0", "source": "#88c0d0", "link": "#8fbcbb",
            "broken": "#bf616a", "temp": "#616e88",
            "comment": "#6d7a96", "string": "#a3be8c", "number": "#d08770", "keyword": "#81a1c1", "heading": "#88c0d0",
            "symbol": "#eceff4",
            "warn": "#ebcb8b", "error": "#bf616a", "on_error": "#eceff4", "error_shadow": "#15181e", "modified": "#ebcb8b", "drop_shadow": "#1c2028", "drop_shadow_text": "#5b667b",
        },
    ),
    "solarized-light": (
        "Solarized Light -- Solarized's cream grounds and its eight accents",
        "Solarized by Ethan Schoonover (ethanschoonover.com/solarized), MIT licence.  Violet and magenta"
        " are left out: numbers take orange, links cyan.  Keywords are its green deepened a shade, which"
        " reads on its cream (4.3:1) where its own green (2.9:1) did not.",
        {
            "desktop": "#e4ddc8", "ground": "#fdf6e3", "ground_alt": "#eee8d5",
            "surface": "#eee8d5", "raised": "#d6cfb8", "field": "#e0d9c3", "field_focus": "#ffffff",
            "overlay": "#eee8d5", "border": "#839496", "border_dim": "#a3aead", "shadow": "#93a1a1",
            "text": "#586e75", "text_dim": "#657b83", "text_faint": "#7d8f91", "text_strong": "#073642",
            "accent": "#268bd2", "on_accent": "#fdf6e3", "on_accent_alt": "#002b36", "on_accent_faint": "#c2e0f5",
            "selection": "#e2dcc6", "on_selection": "#073642",
            "hotkey": "#cb4b16", "marked": "#b58900",
            "dir": "#268bd2", "exec": "#859900", "archive": "#cb4b16", "image": "#2aa198",
            "media": "#b58900", "document": "#657b83", "source": "#073642", "link": "#2aa198",
            "broken": "#dc322f", "temp": "#93a1a1",
            "comment": "#93a1a1", "string": "#2aa198", "number": "#cb4b16", "keyword": "#6c7d00", "heading": "#268bd2",
            "symbol": "#586e75",
            "warn": "#fdf6e3", "error": "#dc322f", "on_error": "#fdf6e3", "error_shadow": "#6b1513", "modified": "#cb4b16", "drop_shadow": "#d3cbb3", "drop_shadow_text": "#657b83",
        },
    ),
}


def _menu(stem: str, ground: str = "overlay") -> dict[str, tuple[str, str]]:
    """A window's own menu: its six slots, as the menu bar's."""
    return {
        f"{stem}-normal": ("text", ground),
        f"{stem}-disabled": ("text_faint", ground),
        f"{stem}-shortcut": ("hotkey", ground),
        f"{stem}-selected": ("on_accent", "accent"),
        f"{stem}-selected-disabled": ("on_accent_faint", "accent"),
        f"{stem}-shortcut-selected": ("on_accent_alt", "accent"),
    }


def _window(stem: str, ground: str = "ground") -> dict[str, tuple[str, str]]:
    """A window's frame and scroll bar slots."""
    return {
        f"{stem}-frame-passive": ("border_dim", ground),
        f"{stem}-frame-active": ("border", ground),
        f"{stem}-frame-icons": ("accent", ground),
        f"{stem}-scroll-bar-page": ("border_dim", ground),
        f"{stem}-scroll-bar-icons": ("text_dim", ground),
    }


#: Every slot as ``(foreground role, background role)``.
SLOT_ROLES: dict[str, tuple[str, str]] = {
    "desktop": ("text_dim", "desktop"),
    # The menu bar and the key bar.
    "bar": ("text", "overlay"), "bar-disabled": ("text_faint", "overlay"), "bar-key": ("hotkey", "overlay"),
    "bar-selected": ("on_accent", "accent"), "bar-selected-disabled": ("on_accent_faint", "accent"),
    "bar-selected-key": ("on_accent_alt", "accent"),
    # Dialogs: a surface, buttons raised on it, fields sunk into it.
    "dialog-frame-background": ("border", "surface"), "dialog-frame-icons": ("accent", "surface"),
    "dialog-scroll-bar-page": ("text_dim", "raised"), "dialog-scroll-bar-icons": ("text", "raised"),
    "dialog-static-text": ("text", "surface"), "dialog-label-normal": ("text", "surface"),
    "dialog-label-selected": ("text_strong", "surface"), "dialog-label-shortcut": ("hotkey", "surface"),
    "dialog-button-normal": ("text", "raised"), "dialog-button-default": ("text_strong", "raised"),
    "dialog-button-selected": ("on_accent", "accent"), "dialog-button-disabled": ("text_faint", "surface"),
    "dialog-button-shortcut": ("hotkey", "raised"), "dialog-shortcut-selected": ("on_accent_alt", "accent"),
    "dialog-shortcut-default": ("hotkey", "raised"), "dialog-button-shadow": ("shadow", "surface"),
    "dialog-cluster-normal": ("text", "surface"), "dialog-cluster-selected": ("text_strong", "surface"),
    "dialog-cluster-shortcut": ("hotkey", "surface"),
    "dialog-input-normal": ("text", "field"), "dialog-input-selected": ("text_strong", "field_focus"),
    "dialog-input-arrow": ("accent", "field"),
    "dialog-history-button": ("text", "raised"), "dialog-history-sides": ("raised", "surface"),
    "dialog-history-bar-page": ("text_dim", "raised"), "dialog-history-bar-icons": ("text", "raised"),
    "dialog-list-normal": ("text", "field"), "dialog-list-focused": ("on_accent", "accent"),
    "dialog-list-selected": ("on_selection", "selection"), "dialog-list-divider": ("border", "field"),
    "dialog-information-pane": ("text_dim", "raised"),
    "dialog-tree-normal-tree": ("text_dim", "field"), "dialog-tree-normal-nodes": ("text", "field"),
    "dialog-tree-selected-node": ("on_accent", "accent"), "dialog-tree-default-node": ("dir", "field"),
    "dialog-tree-selected-default": ("on_accent_alt", "accent"),
    "dialog-tree-selected-passive": ("on_selection", "selection"),
    "dialog-tree-selected-def-passive": ("dir", "selection"),
    # The file manager's window and panels.
    "frame": ("border_dim", "ground"), "active-frame": ("border", "ground"), "frame-icon": ("accent", "ground"),
    "scrollbar-page": ("border_dim", "ground"), "scrollbar-arrow": ("text_dim", "ground"),
    "panel": ("text", "ground"), "marked": ("marked", "ground"),
    "cursor": ("on_accent", "accent"), "marked-cursor": ("on_accent_alt", "accent"),
    "divider": ("border_dim", "ground"), "active-title": ("on_accent", "accent"), "title": ("text_dim", "ground"),
    "column-title": ("accent", "ground"),
    "directory": ("dir", "ground"), "executable": ("exec", "ground"), "archive": ("archive", "ground"),
    "highlight-custom-1": ("image", "ground"), "highlight-custom-2": ("media", "ground"),
    "highlight-custom-3": ("document", "ground"), "highlight-custom-4": ("broken", "ground"),
    "highlight-custom-5": ("source", "ground"),
    "drive-line-drive-letters": ("text", "overlay"), "drive-line-drive-selected": ("on_accent", "accent"),
    "drive-line-frame": ("border", "overlay"),
    "info-current-file": ("text", "ground"), "info-selected-text": ("marked", "ground"),
    "info-selected-numbers": ("marked", "ground"), "info-totals-text": ("text_dim", "ground"),
    "info-totals-numbers": ("text", "ground"), "info-free-space-text": ("text_dim", "ground"),
    "info-free-space-numbers": ("text", "ground"),
    "tree-normal-tree": ("text_dim", "ground"), "tree-normal-nodes": ("text", "ground"),
    "tree-selected-node": ("on_accent", "accent"), "tree-default-node": ("dir", "ground"),
    "tree-selected-default": ("on_accent_alt", "accent"), "tree-selected-passive": ("on_selection", "selection"),
    "tree-selected-def-passive": ("dir", "selection"), "tree-info-box": ("text", "raised"),
    "quick-view-normal-text": ("text", "ground"), "quick-view-selected-text": ("on_selection", "selection"),
    "disk-info-normal-text": ("text", "ground"), "disk-info-highlighted-text": ("accent", "ground"),
    # The viewer, the editor and its highlighting.
    **_window("viewer"),
    "viewer-normal-text": ("text", "ground"), "viewer-selected-text": ("on_selection", "selection"),
    **_window("editor"),
    "editor-frame-title": ("text_strong", "ground"),
    "editor-normal-text": ("text", "ground"), "editor-selected-text": ("on_selection", "selection"),
    "editor-highlight-comments": ("comment", "ground"), "editor-highlight-symbols": ("symbol", "ground"),
    "editor-highlight-strings": ("string", "ground"), "editor-highlight-numbers": ("number", "ground"),
    "editor-highlight-current-line": ("text", "ground_alt"),
    "editor-highlight-cur-line-comments": ("comment", "ground_alt"),
    "editor-highlight-current-line-selected": ("on_selection", "selection"),
    "editor-highlight-current-column": ("text", "ground_alt"),
    **_menu("editor-menu"),
    # The disk fixer, the terminal and the dBase viewer.
    **_window("fixer"),
    "fixer-frame-title": ("text_strong", "ground"),
    "fixer-normal-text": ("text", "ground"), "fixer-selected-text": ("on_selection", "selection"),
    "fixer-sector-title": ("accent", "ground"), "fixer-edit-line": ("text_strong", "field"),
    **_menu("fixer-menu"),
    **_window("terminal"),
    "dbase-frame-passive": ("border_dim", "ground"), "dbase-frame-active": ("border", "ground"),
    "dbase-frame-icons": ("accent", "ground"), "dbase-fields-titles": ("accent", "raised"),
    "dbase-normal-text": ("text", "ground"), "dbase-cursor": ("on_accent", "accent"),
}

#: Navigator's own entries, as for the slots.
DERIVED_ROLES: dict[str, tuple[str, str]] = {
    "image": ("image", "ground"), "media": ("media", "ground"), "document": ("document", "ground"),
    "stale-link": ("broken", "ground"), "source": ("source", "ground"), "symlink": ("link", "ground"),
    "device": ("document", "ground"), "special": ("document", "ground"), "temp": ("temp", "ground"),
    "root-title": ("on_error", "error"), "error-dialog": ("on_error", "error"),
    "error-dialog-icons": ("warn", "error"), "error-dialog-shadow": ("error_shadow", "error"),
    "keyword": ("keyword", "ground"), "modified-title": ("modified", "ground"),
    "shadow": ("drop_shadow_text", "drop_shadow"), "command-line": ("text", "desktop"),
    "command-line-prompt": ("accent", "desktop"),
    "viewer-comments": ("comment", "ground"), "viewer-symbols": ("symbol", "ground"),
    "viewer-strings": ("string", "ground"), "viewer-numbers": ("number", "ground"),
    "viewer-keyword": ("keyword", "ground"), "viewer-links": ("accent", "ground"),
    "heading": ("heading", "ground"), "viewer-heading": ("heading", "ground"),
}

assert set(SLOT_ROLES) == {slot.name for slot in SLOTS}, set(SLOT_ROLES) ^ {slot.name for slot in SLOTS}
assert set(DERIVED_ROLES) == set(DERIVED), set(DERIVED_ROLES) ^ set(DERIVED)
for _name, (_description, _credit, _roles) in THEMES.items():
    assert set(_roles) == set(ROLES), (_name, set(_roles) ^ set(ROLES))


def _variable(name: str, fg: str, bg: str, comment: str) -> list[str]:
    return [f"${name}-fg: $color-{fg};".ljust(38) + f"/*{comment} */", f"${name}-bg: $color-{bg};"]


def to_nss(name: str) -> str:
    """Theme *name* as a sheet of variable definitions and nothing else."""
    description, credit, roles = THEMES[name]
    out = [
        "/*",
        f" * {description}.",
        " *",
        *(f" * {line}" for line in _wrap(credit)),
        " *",
        " * Generated by tools/themegen.py; edit that, not this.",
        " * Load it after navigator.nss, whose rules read the names below:",
        " *",
        f" *     python -m navigator --theme {name}",
        " *",
        " * Exact RGB throughout, so a 256-colour or truecolor terminal shows it",
        " * as designed; with --colors 16 the renderer picks the nearest of the",
        " * sixteen.",
        " */",
        "",
        "/* The theme's roles: every slot below takes one of them. */",
    ]
    out += [f"$color-{role}: {roles[role]};".ljust(38) + f"/* {why} */" for role, why in ROLES.items()]
    out += [
        "",
        "/* All 144 entries DOS Navigator's Colors dialog exposes, in its groups and",
        "   its order, each drawn in two of the roles above. */",
    ]
    group = None
    for slot in SLOTS:
        if slot.group != group:
            group = slot.group
            out += ["", f"/* -- {group} " + "-" * max(3, 68 - len(group)) + " */"]
        out += _variable(slot.name, *SLOT_ROLES[slot.name], slot.comment)
    out += [
        "",
        "/* -- Navigator's own: no DN slot ---------------------------------------- */",
    ]
    for variable, (_index, why) in DERIVED.items():
        out += _variable(variable, *DERIVED_ROLES[variable], f"  {why}")
    out.append("")
    return "\n".join(out)


def _wrap(text: str, width: int = 70) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 if a sheet is stale")
    args = parser.parse_args(argv)
    stale = []
    for name in THEMES:
        path = OUT / f"{name}.nss"
        text = to_nss(name)
        if args.check:
            if not path.is_file() or path.read_text() != text:
                stale.append(path.name)
        else:
            path.write_text(text)
            print(f"-> {path.relative_to(ROOT)}")
    if stale:
        print("stale: " + ", ".join(stale) + "; run tools/themegen.py", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
