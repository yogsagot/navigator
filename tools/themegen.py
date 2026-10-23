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
    "gruvbox": (
        "Gruvbox -- warm retro browns, cream text and its earthy accents",
        "Gruvbox by Pavel Pertsev (github.com/morhetz/gruvbox), MIT licence. Its purple, a dusty pink, "
        "is left out: numbers take its orange.",
        {
            "desktop": "#1d2021", "ground": "#282828", "ground_alt": "#32302f", "surface": "#504945",
            "raised": "#665c54", "field": "#5a524c", "field_focus": "#1d2021", "overlay": "#32302f",
            "border": "#a89984", "border_dim": "#665c54", "shadow": "#141414", "text": "#ebdbb2",
            "text_dim": "#bdae93", "text_faint": "#928374", "text_strong": "#fbf1c7", "accent": "#fabd2f",
            "on_accent": "#282828", "on_accent_alt": "#9d0006", "on_accent_faint": "#7c6f64", "selection": "#504945",
            "on_selection": "#fbf1c7", "hotkey": "#fe8019", "marked": "#fabd2f", "dir": "#fbf1c7",
            "exec": "#b8bb26", "archive": "#fe8019", "image": "#8ec07c", "media": "#fabd2f",
            "document": "#d5c4a1", "source": "#83a598", "link": "#8ec07c", "broken": "#fb4934",
            "temp": "#7c6f64", "comment": "#928374", "string": "#b8bb26", "number": "#fe8019",
            "keyword": "#fb4934", "heading": "#fabd2f", "symbol": "#ebdbb2", "warn": "#fabd2f",
            "error": "#9d0006", "error_shadow": "#141414", "modified": "#fabd2f", "drop_shadow": "#141414",
            "drop_shadow_text": "#665c54", "on_error": "#fbf1c7",
        },
    ),
    "gruvbox-light": (
        "Gruvbox Light -- Gruvbox's cream page and the dark forms of its accents",
        "Gruvbox by Pavel Pertsev (github.com/morhetz/gruvbox), MIT licence. Its purple is left out: "
        "numbers take its orange.",
        {
            "desktop": "#ebdbb2", "ground": "#fbf1c7", "ground_alt": "#f2e5bc", "surface": "#ebdbb2",
            "raised": "#c9b994", "field": "#d5c4a1", "field_focus": "#ffffff", "overlay": "#ebdbb2",
            "border": "#7c6f64", "border_dim": "#a89984", "shadow": "#a89984", "text": "#3c3836",
            "text_dim": "#504945", "text_faint": "#7c6f64", "text_strong": "#282828", "accent": "#076678",
            "on_accent": "#fbf1c7", "on_accent_alt": "#fabd2f", "on_accent_faint": "#83a598", "selection": "#d5c4a1",
            "on_selection": "#282828", "hotkey": "#af3a03", "marked": "#b57614", "dir": "#076678",
            "exec": "#79740e", "archive": "#af3a03", "image": "#427b58", "media": "#b57614",
            "document": "#504945", "source": "#076678", "link": "#427b58", "broken": "#9d0006",
            "temp": "#928374", "comment": "#7c6f64", "string": "#79740e", "number": "#af3a03",
            "keyword": "#9d0006", "heading": "#076678", "symbol": "#504945", "warn": "#fbf1c7",
            "error": "#9d0006", "error_shadow": "#1d0000", "modified": "#af3a03", "drop_shadow": "#d5c4a1",
            "drop_shadow_text": "#7c6f64", "on_error": "#fbf1c7",
        },
    ),
    "tokyo-night": (
        "Tokyo Night -- deep navy, soft lavender-blue text, neon blues and teals",
        "Tokyo Night by enkia (github.com/enkia/tokyo-night-vscode-theme), MIT licence. Its magenta and "
        "purple, which colour its keywords, are left out: keywords take its cyan; and its pink-red gives "
        "way to its deeper red.",
        {
            "desktop": "#16161e", "ground": "#1a1b26", "ground_alt": "#292e42", "surface": "#414868",
            "raised": "#565f89", "field": "#363c5a", "field_focus": "#16161e", "overlay": "#1f2335",
            "border": "#737aa2", "border_dim": "#545c7e", "shadow": "#0d0d12", "text": "#c0caf5",
            "text_dim": "#a9b1d6", "text_faint": "#737aa2", "text_strong": "#e1e6ff", "accent": "#7aa2f7",
            "on_accent": "#1a1b26", "on_accent_alt": "#8c2b2b", "on_accent_faint": "#3d59a1", "selection": "#33467c",
            "on_selection": "#e1e6ff", "hotkey": "#e0af68", "marked": "#e0af68", "dir": "#e1e6ff",
            "exec": "#9ece6a", "archive": "#ff9e64", "image": "#73daca", "media": "#e0af68",
            "document": "#a9b1d6", "source": "#7aa2f7", "link": "#2ac3de", "broken": "#db4b4b",
            "temp": "#565f89", "comment": "#6b74a0", "string": "#9ece6a", "number": "#ff9e64",
            "keyword": "#7dcfff", "heading": "#7aa2f7", "symbol": "#89ddff", "warn": "#e0af68",
            "error": "#a33a3a", "error_shadow": "#0d0d12", "modified": "#e0af68", "drop_shadow": "#0d0d12",
            "drop_shadow_text": "#545c7e", "on_error": "#e1e6ff",
        },
    ),
    "everforest-light": (
        "Everforest Light -- a warm, low-contrast paper with muted forest greens",
        "Everforest by sainnhe (github.com/sainnhe/everforest), MIT licence. Its purple is left out: "
        "keywords take its red. Its yellow, green, orange and aqua are deepened a shade, as on its cream "
        "they fell short of the contrast floor.",
        {
            "desktop": "#e6e2cc", "ground": "#fdf6e3", "ground_alt": "#f4f0d9", "surface": "#efebd4",
            "raised": "#d8d3ba", "field": "#e0dcc7", "field_focus": "#ffffff", "overlay": "#efebd4",
            "border": "#829181", "border_dim": "#a6b0a0", "shadow": "#9aa28c", "text": "#5c6a72",
            "text_dim": "#6c7a80", "text_faint": "#829181", "text_strong": "#3a464c", "accent": "#6b7a00",
            "on_accent": "#fdf6e3", "on_accent_alt": "#ffd666", "on_accent_faint": "#b4bf6e", "selection": "#e6e2cc",
            "on_selection": "#3a464c", "hotkey": "#c45f12", "marked": "#9a6f00", "dir": "#2f7aa8",
            "exec": "#5f7000", "archive": "#c45f12", "image": "#268a65", "media": "#9a6f00",
            "document": "#6c7a80", "source": "#2f7aa8", "link": "#268a65", "broken": "#d63c39",
            "temp": "#a6b0a0", "comment": "#939f91", "string": "#5f7000", "number": "#c45f12",
            "keyword": "#d63c39", "heading": "#2f7aa8", "symbol": "#6c7a80", "warn": "#fdf6e3",
            "error": "#d63c39", "error_shadow": "#7a1f1d", "modified": "#c45f12", "drop_shadow": "#dedac3",
            "drop_shadow_text": "#829181", "on_error": "#fdf6e3",
        },
    ),
    "catppuccin-latte": (
        "Catppuccin Latte -- soft pastels on a cool, airy light page",
        "Catppuccin by the Catppuccin organisation (catppuccin.com), MIT licence. Its mauve, pink and "
        "flamingo are left out: keywords take its blue, numbers its peach. Its yellow is deepened a "
        "shade, as on its page it fell short of the contrast floor.",
        {
            "desktop": "#dce0e8", "ground": "#eff1f5", "ground_alt": "#e6e9ef", "surface": "#e6e9ef",
            "raised": "#bcc0cc", "field": "#ccd0da", "field_focus": "#ffffff", "overlay": "#e6e9ef",
            "border": "#7c7f93", "border_dim": "#9ca0b0", "shadow": "#9ca0b0", "text": "#4c4f69",
            "text_dim": "#5c5f77", "text_faint": "#7c7f93", "text_strong": "#303446", "accent": "#1e66f5",
            "on_accent": "#eff1f5", "on_accent_alt": "#ffd479", "on_accent_faint": "#9bb9f7", "selection": "#ccd0da",
            "on_selection": "#303446", "hotkey": "#d20f39", "marked": "#a86b0c", "dir": "#1e66f5",
            "exec": "#40a02b", "archive": "#fe640b", "image": "#179299", "media": "#a86b0c",
            "document": "#5c5f77", "source": "#1e66f5", "link": "#179299", "broken": "#d20f39",
            "temp": "#9ca0b0", "comment": "#7c7f93", "string": "#40a02b", "number": "#d4500a",
            "keyword": "#1e66f5", "heading": "#1e66f5", "symbol": "#5c5f77", "warn": "#eff1f5",
            "error": "#d20f39", "error_shadow": "#6b0a1f", "modified": "#d4500a", "drop_shadow": "#ccd0da",
            "drop_shadow_text": "#7c7f93", "on_error": "#eff1f5",
        },
    ),
    "one-dark": (
        "One Dark -- Atom's neutral charcoal with clear blue, green and orange",
        "One Dark by GitHub, from the Atom editor (github.com/atom/one-dark-syntax), MIT licence. Its "
        "purple, the keywords' colour, is left out: keywords take its blue.",
        {
            "desktop": "#1b1e23", "ground": "#282c34", "ground_alt": "#2c313a", "surface": "#454c5a",
            "raised": "#4b5263", "field": "#3e4451", "field_focus": "#1b1e23", "overlay": "#21252b",
            "border": "#7f848e", "border_dim": "#565c64", "shadow": "#111317", "text": "#abb2bf",
            "text_dim": "#9da5b4", "text_faint": "#7f848e", "text_strong": "#e6e9ef", "accent": "#61afef",
            "on_accent": "#282c34", "on_accent_alt": "#8b2f36", "on_accent_faint": "#3a6d99", "selection": "#3e4451",
            "on_selection": "#e6e9ef", "hotkey": "#e5c07b", "marked": "#e5c07b", "dir": "#e6e9ef",
            "exec": "#98c379", "archive": "#d19a66", "image": "#56b6c2", "media": "#e5c07b",
            "document": "#9da5b4", "source": "#61afef", "link": "#56b6c2", "broken": "#e06c75",
            "temp": "#5c6370", "comment": "#7f848e", "string": "#98c379", "number": "#d19a66",
            "keyword": "#61afef", "heading": "#61afef", "symbol": "#56b6c2", "warn": "#e5c07b",
            "error": "#a33a42", "error_shadow": "#111317", "modified": "#e5c07b", "drop_shadow": "#111317",
            "drop_shadow_text": "#565c64", "on_error": "#e6e9ef",
        },
    ),
    "one-light": (
        "One Light -- Atom's bright neutral page with deep blue, green and amber",
        "One Light by GitHub, from the Atom editor (github.com/atom/one-light-syntax), MIT licence. Its "
        "purple, the keywords' colour, is left out: keywords take its blue. Its comment grey and amber "
        "are deepened a shade, for the contrast floor.",
        {
            "desktop": "#e5e5e6", "ground": "#fafafa", "ground_alt": "#f0f0f1", "surface": "#f0f0f1",
            "raised": "#c6c6c9", "field": "#d4d4d6", "field_focus": "#ffffff", "overlay": "#f0f0f1",
            "border": "#82848b", "border_dim": "#a0a1a7", "shadow": "#9a9ba1", "text": "#383a42",
            "text_dim": "#4f525d", "text_faint": "#7a7c84", "text_strong": "#1e2027", "accent": "#4078f2",
            "on_accent": "#fafafa", "on_accent_alt": "#ffe08a", "on_accent_faint": "#a8c1f8", "selection": "#dcdcdd",
            "on_selection": "#1e2027", "hotkey": "#e45649", "marked": "#986801", "dir": "#4078f2",
            "exec": "#50a14f", "archive": "#c45f12", "image": "#0184bc", "media": "#986801",
            "document": "#4f525d", "source": "#4078f2", "link": "#0184bc", "broken": "#e45649",
            "temp": "#a0a1a7", "comment": "#82848b", "string": "#50a14f", "number": "#986801",
            "keyword": "#4078f2", "heading": "#4078f2", "symbol": "#4f525d", "warn": "#fafafa",
            "error": "#ca1243", "error_shadow": "#5e0820", "modified": "#c45f12", "drop_shadow": "#dcdcdd",
            "drop_shadow_text": "#82848b", "on_error": "#fafafa",
        },
    ),
    "kanagawa": (
        "Kanagawa -- deep sumi ink with the muted wave and autumn colours of Hokusai's print",
        "Kanagawa by Tommaso Laurenzi (github.com/rebelot/kanagawa.nvim), MIT licence. Its oniViolet, "
        "the keywords' colour, and its sakuraPink are left out: keywords take its springBlue.",
        {
            "desktop": "#16161d", "ground": "#1f1f28", "ground_alt": "#2a2a37", "surface": "#4a4a5e",
            "raised": "#5f5f7a", "field": "#363646", "field_focus": "#16161d", "overlay": "#2a2a37",
            "border": "#9a9a8e", "border_dim": "#54546d", "shadow": "#0d0d12", "text": "#dcd7ba",
            "text_dim": "#c8c093", "text_faint": "#828077", "text_strong": "#f2ecbc", "accent": "#7e9cd8",
            "on_accent": "#1f1f28", "on_accent_alt": "#8a2f33", "on_accent_faint": "#4a5f8a", "selection": "#2d4f67",
            "on_selection": "#f2ecbc", "hotkey": "#ffa066", "marked": "#e6c384", "dir": "#f2ecbc",
            "exec": "#98bb6c", "archive": "#ffa066", "image": "#7aa89f", "media": "#e6c384",
            "document": "#c8c093", "source": "#7fb4ca", "link": "#6a9589", "broken": "#ff5d62",
            "temp": "#727169", "comment": "#8a897e", "string": "#98bb6c", "number": "#ffa066",
            "keyword": "#7fb4ca", "heading": "#7e9cd8", "symbol": "#c0a36e", "warn": "#e6c384",
            "error": "#a33a3e", "error_shadow": "#0d0d12", "modified": "#e6c384", "drop_shadow": "#0d0d12",
            "drop_shadow_text": "#54546d", "on_error": "#f2ecbc",
        },
    ),
    "phosphor": (
        "Phosphor -- a green-screen terminal, glowing text on a dark tube, with one amber note",
        "An original Navigator palette.",
        {
            "desktop": "#060c07", "ground": "#0b140d", "ground_alt": "#13241a", "surface": "#2a5236",
            "raised": "#3a6a46", "field": "#1d3a26", "field_focus": "#060c07", "overlay": "#102018",
            "border": "#4fae68", "border_dim": "#2f6b3f", "shadow": "#020403", "text": "#7cf29a",
            "text_dim": "#5fc97c", "text_faint": "#3f8a52", "text_strong": "#c8ffd6", "accent": "#b6ffc8",
            "on_accent": "#0b140d", "on_accent_alt": "#8a4b00", "on_accent_faint": "#4f8a5e", "selection": "#1f4a2c",
            "on_selection": "#c8ffd6", "hotkey": "#ffb347", "marked": "#ffb347", "dir": "#c8ffd6",
            "exec": "#b6ffc8", "archive": "#ffb347", "image": "#6fe0d0", "media": "#d8e98a",
            "document": "#5fc97c", "source": "#8ef0e0", "link": "#6fe0d0", "broken": "#ff7a5a",
            "temp": "#3a7a4a", "comment": "#4f9e63", "string": "#d8e98a", "number": "#ffb347",
            "keyword": "#c8ffd6", "heading": "#b6ffc8", "symbol": "#5fc97c", "warn": "#ffb347",
            "error": "#8a2a1a", "error_shadow": "#020403", "modified": "#ffb347", "drop_shadow": "#020403",
            "drop_shadow_text": "#2f6b3f", "on_error": "#ffd2c4",
        },
    ),
    "sepia": (
        "Sepia -- an old printed page: brown-black ink on warm paper, an oxblood accent",
        "An original Navigator palette.",
        {
            "desktop": "#d9c9a3", "ground": "#f1e7d0", "ground_alt": "#e8dcc0", "surface": "#e6d8b8",
            "raised": "#d3c19a", "field": "#ddcca6", "field_focus": "#fbf5e6", "overlay": "#e6d8b8",
            "border": "#7a6548", "border_dim": "#a8946f", "shadow": "#a8946f", "text": "#3b2f22",
            "text_dim": "#5a4a36", "text_faint": "#7f6c52", "text_strong": "#1f170e", "accent": "#7b2d26",
            "on_accent": "#f8f0dc", "on_accent_alt": "#f2c46d", "on_accent_faint": "#c98f88", "selection": "#d3c19a",
            "on_selection": "#1f170e", "hotkey": "#9a4a1c", "marked": "#8a6a12", "dir": "#2f5577",
            "exec": "#3d6b35", "archive": "#9a4a1c", "image": "#2c6e6a", "media": "#8a6a12",
            "document": "#5a4a36", "source": "#2f5577", "link": "#2c6e6a", "broken": "#a52a1e",
            "temp": "#a8946f", "comment": "#7f6c52", "string": "#3d6b35", "number": "#9a4a1c",
            "keyword": "#7b2d26", "heading": "#2f5577", "symbol": "#5a4a36", "warn": "#f8f0dc",
            "error": "#a63a2c", "error_shadow": "#1a0806", "modified": "#9a4a1c", "drop_shadow": "#d3c19a",
            "drop_shadow_text": "#7f6c52", "on_error": "#f8f0dc",
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
    "git-modified": ("number", "ground"), "git-added": ("string", "ground"),
    "git-deleted": ("broken", "ground"), "git-renamed": ("number", "ground"),
    "git-untracked": ("link", "ground"), "git-ignored": ("temp", "ground"),
    "git-conflict": ("broken", "ground"),
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
