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
            "desktop": "#c4bdaf", "ground": "#dad7d0", "ground_alt": "#d0cbc0",
            "surface": "#d0cabd", "raised": "#bab1a1", "field": "#c4bcad", "field_focus": "#f0f0f0",
            "overlay": "#c7c0b2", "border": "#6d6559", "border_dim": "#9e9588", "shadow": "#8a8172",
            "text": "#262626", "text_dim": "#443f38", "text_faint": "#6e685d", "text_strong": "#000000",
            "accent": "#a32100", "on_accent": "#ffffff", "on_accent_alt": "#ffe2b8", "on_accent_faint": "#f0a582",
            "selection": "#d8b49c", "on_selection": "#2b2b2b",
            "hotkey": "#006682", "marked": "#845200",
            "dir": "#1d4ed8", "exec": "#006d2b", "archive": "#a04000", "image": "#006682",
            "media": "#8c4f00", "document": "#57534e", "source": "#1e40af", "link": "#006a62",
            "broken": "#b91c1c", "temp": "#7e776c",
            "comment": "#6e6763", "string": "#006d2b", "number": "#a04000", "keyword": "#1d4ed8", "heading": "#1d4ed8",
            "symbol": "#57534e",
            "warn": "#ffe2b8", "error": "#b91c1c", "on_error": "#ffffff", "error_shadow": "#5c1010", "modified": "#a04000", "drop_shadow": "#afa697", "drop_shadow_text": "#6f685d",
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
        " are left out: numbers take orange, links cyan.  Its creams are dimmed from near-white, and its"
        " accents deepened to keep their contrast on them (its own cyan and green read 2.9:1 on base3).",
        {
            "desktop": "#c8c1ac", "ground": "#ded7c4", "ground_alt": "#d0cab8",
            "surface": "#d0cab8", "raised": "#bbb49e", "field": "#c4bda8", "field_focus": "#efefef",
            "overlay": "#d0cab8", "border": "#596a6b", "border_dim": "#8f9998", "shadow": "#788585",
            "text": "#172c32", "text_dim": "#32464d", "text_faint": "#617375", "text_strong": "#002e3a",
            "accent": "#00599c", "on_accent": "#fdf6e3", "on_accent_alt": "#002b36", "on_accent_faint": "#c2e0f5",
            "selection": "#c6c0aa", "on_selection": "#073642",
            "hotkey": "#b13100", "marked": "#805600",
            "dir": "#0060a4", "exec": "#546400", "archive": "#af2f00", "image": "#006a63",
            "media": "#805600", "document": "#4b6168", "source": "#073642", "link": "#006a63",
            "broken": "#be0011", "temp": "#6e7b7b",
            "comment": "#5e6b6b", "string": "#006a63", "number": "#af2f00", "keyword": "#556400", "heading": "#0060a4",
            "symbol": "#4b6167",
            "warn": "#fdf6e3", "error": "#dc322f", "on_error": "#fdf6e3", "error_shadow": "#6b1513", "modified": "#af2f00", "drop_shadow": "#b9b199", "drop_shadow_text": "#60767e",
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
        "numbers take its orange. Its creams are dimmed, and its inks deepened to keep their contrast "
        "on them.",
        {
            "desktop": "#d3c49b", "ground": "#e1d8ae", "ground_alt": "#d9cda4", "surface": "#d3c49b",
            "raised": "#b5a581", "field": "#bfaf8c", "field_focus": "#f1f1f1", "overlay": "#d3c49b",
            "border": "#675b50", "border_dim": "#a49580", "shadow": "#8a7c68", "text": "#2f2b29",
            "text_dim": "#4a4440", "text_faint": "#776a5f", "text_strong": "#282828", "accent": "#005f71",
            "on_accent": "#fbf1c7", "on_accent_alt": "#fabd2f", "on_accent_faint": "#83a598", "selection": "#bfaf8c",
            "on_selection": "#282828", "hotkey": "#a12c00", "marked": "#8a4e00", "dir": "#076678",
            "exec": "#655f00", "archive": "#aa3500", "image": "#2f6846", "media": "#8a4e00",
            "document": "#504945", "source": "#076678", "link": "#2f6846", "broken": "#9d0006",
            "temp": "#857667", "comment": "#74675c", "string": "#655f00", "number": "#aa3500",
            "keyword": "#9d0006", "heading": "#076678", "symbol": "#504945", "warn": "#fbf1c7",
            "error": "#9d0006", "error_shadow": "#1d0000", "modified": "#aa3500", "drop_shadow": "#bfaf8c",
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
        "keywords take its red. Its creams are dimmed from near-white, and its inks deepened to keep "
        "their contrast on them.",
        {
            "desktop": "#c9c5b0", "ground": "#ded7c4", "ground_alt": "#d5d1bb", "surface": "#d1cdb7",
            "raised": "#bdb8a0", "field": "#c4c0ab", "field_focus": "#efefef", "overlay": "#d1cdb7",
            "border": "#5d6b5c", "border_dim": "#919b8c", "shadow": "#818873", "text": "#222e35",
            "text_dim": "#3a474c", "text_faint": "#667465", "text_strong": "#202b31", "accent": "#515f00",
            "on_accent": "#fdf6e3", "on_accent_alt": "#ffd666", "on_accent_faint": "#b4bf6e", "selection": "#c9c5b0",
            "on_selection": "#3a464c", "hotkey": "#a64300", "marked": "#805600", "dir": "#106390",
            "exec": "#556500", "archive": "#a03e00", "image": "#006b49", "media": "#805600",
            "document": "#526066", "source": "#106390", "link": "#006b49", "broken": "#b91920",
            "temp": "#727c6d", "comment": "#606c5f", "string": "#556500", "number": "#a03e00",
            "keyword": "#b91920", "heading": "#106390", "symbol": "#526066", "warn": "#fdf6e3",
            "error": "#d63c39", "error_shadow": "#7a1f1d", "modified": "#a03e00", "drop_shadow": "#c2bea8",
            "drop_shadow_text": "#718070", "on_error": "#fdf6e3",
        },
    ),
    "catppuccin-latte": (
        "Catppuccin Latte -- soft pastels on a cool, airy light page",
        "Catppuccin by the Catppuccin organisation (catppuccin.com), MIT licence. Its mauve, pink and "
        "flamingo are left out: keywords take its blue, numbers its peach. Its page is dimmed from "
        "near-white, and its inks deepened to keep their contrast on it.",
        {
            "desktop": "#c4c8d0", "ground": "#d6d7db", "ground_alt": "#cdd0d6", "surface": "#cdd0d6",
            "raised": "#a7abb7", "field": "#b6bac4", "field_focus": "#f1f1f1", "overlay": "#cdd0d6",
            "border": "#606376", "border_dim": "#9397a7", "shadow": "#828696", "text": "#2a2d44",
            "text_dim": "#43455c", "text_faint": "#707386", "text_strong": "#25293b", "accent": "#004cd9",
            "on_accent": "#eff1f5", "on_accent_alt": "#ffd479", "on_accent_faint": "#9bb9f7", "selection": "#b6bac4",
            "on_selection": "#303446", "hotkey": "#b60023", "marked": "#894e00", "dir": "#034fdd",
            "exec": "#006e00", "archive": "#b91900", "image": "#006870", "media": "#894e00",
            "document": "#595c74", "source": "#034fdd", "link": "#006870", "broken": "#be0029",
            "temp": "#747887", "comment": "#65687c", "string": "#006e00", "number": "#b02d00",
            "keyword": "#034fdd", "heading": "#034fdd", "symbol": "#595c74", "warn": "#eff1f5",
            "error": "#d20f39", "error_shadow": "#6b0a1f", "modified": "#b02d00", "drop_shadow": "#b6bac4",
            "drop_shadow_text": "#75788c", "on_error": "#eff1f5",
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
        "purple, the keywords' colour, is left out: keywords take its blue. Its page is dimmed from "
        "near-white, and its inks deepened to keep their contrast on it.",
        {
            "desktop": "#c5c5c6", "ground": "#d7d7d7", "ground_alt": "#cfcfd0", "surface": "#cfcfd0",
            "raised": "#aaaaad", "field": "#b6b6b8", "field_focus": "#ededed", "overlay": "#cfcfd0",
            "border": "#606269", "border_dim": "#95969c", "shadow": "#85868c", "text": "#2a2c33",
            "text_dim": "#424550", "text_faint": "#71737b", "text_strong": "#1e2027", "accent": "#1c50c6",
            "on_accent": "#fafafa", "on_accent_alt": "#ffe08a", "on_accent_faint": "#a8c1f8", "selection": "#bdbdbe",
            "on_selection": "#1e2027", "hotkey": "#ae1e19", "marked": "#825300", "dir": "#2054cb",
            "exec": "#146c19", "archive": "#a03e00", "image": "#006197", "media": "#825300",
            "document": "#4f525d", "source": "#2054cb", "link": "#006197", "broken": "#b2241e",
            "temp": "#77787e", "comment": "#676970", "string": "#146c19", "number": "#825300",
            "keyword": "#2054cb", "heading": "#2054cb", "symbol": "#4f525d", "warn": "#fafafa",
            "error": "#ca1243", "error_shadow": "#5e0820", "modified": "#a03e00", "drop_shadow": "#bdbdbe",
            "drop_shadow_text": "#797b82", "on_error": "#fafafa",
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
            "desktop": "#caba95", "ground": "#e0d7c0", "ground_alt": "#d8ccb1", "surface": "#d6c8a9",
            "raised": "#c5b38c", "field": "#cebd98", "field_focus": "#f2ecdd", "overlay": "#d6c8a9",
            "border": "#7a6548", "border_dim": "#a8946f", "shadow": "#93805b", "text": "#2e2316",
            "text_dim": "#4b3b28", "text_faint": "#7f6c52", "text_strong": "#1f170e", "accent": "#7b2d26",
            "on_accent": "#f8f0dc", "on_accent_alt": "#f2c46d", "on_accent_faint": "#c98f88", "selection": "#c5b38c",
            "on_selection": "#1f170e", "hotkey": "#9a4a1c", "marked": "#785900", "dir": "#2f5577",
            "exec": "#3a6832", "archive": "#974718", "image": "#256864", "media": "#785900",
            "document": "#5a4a36", "source": "#2f5577", "link": "#256864", "broken": "#a52a1e",
            "temp": "#897652", "comment": "#79664c", "string": "#3a6832", "number": "#974718",
            "keyword": "#7b2d26", "heading": "#2f5577", "symbol": "#5a4a36", "warn": "#f8f0dc",
            "error": "#a63a2c", "error_shadow": "#1a0806", "modified": "#974718", "drop_shadow": "#c5b38c",
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
