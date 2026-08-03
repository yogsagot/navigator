#!/usr/bin/env python3
"""Convert DOS Navigator ``.PAL`` colour palettes into navkit ``.nss`` sheets.

Run it against the ``COLORS`` directory of a DOS Navigator 1.51 distribution::

    ./venv/bin/python tools/palconv.py ~/Downloads/DN/COLORS \\
        --out navigator/styles/themes

``--dump FILE.PAL`` prints one palette instead, as a table of decoded slots,
which is how the mapping below was checked against the Pascal source.

This is an asset pipeline, not part of the application: nothing under
``navigator/`` or ``navkit/`` imports it, and the sheets it writes are checked
in, so a build does not need a copy of DOS Navigator lying around.


The file format
===============

``.PAL`` is not a documented format; it is whatever ``TDOSStream`` happened to
write.  ``DNUTIL.PAS:StoreColors`` is the whole of it, and ``LoadPalFromFile``
in the same unit reads it back::

    Pal := PString(GetPalette);
    S.WriteStr(Pal);                        { length byte, then that many bytes }
    StoreIndexes(S);                        { DNUTIL.PAS:288 }
    vID := $50414756; S.Write(vID, 4);      { 'VGAP' }
    S.Write(VGA_Palette, SizeOf(VGA_Palette));
    vID := $4B4E4C42; S.Write(vID, 4);      { 'BLNK' }
    S.Write(CurrentBlink, SizeOf(CurrentBlink));

which lays out as, little-endian and unaligned throughout:

===========  ======================================================
``u8``       length of the application palette -- always 228, being
             ``Length(CColor)``
``228 x u8`` the application palette, one DOS attribute byte each,
             indexed from **one** because it came out of a Pascal
             string
``u8``       size of the dialog-cursor block, ``0`` or
             ``2 + ColorIndexes^.ColorSize`` -- always 24 here
``24 x u8``  that block: a ``TColorIndex`` record, below
``4 x u8``   the literal ``VGAP``
``48 x u8``  the VGA DAC: ``R[16]``, then ``G[16]``, then ``B[16]``,
             planar rather than interleaved, six bits per channel
``4 x u8``   the literal ``BLNK``
``u8``       ``CurrentBlink`` -- ``0`` in every shipped palette
===========  ======================================================

Every shipped palette is exactly 311 bytes and ends flush with the blink byte.
The two trailing blocks are optional on read: ``LoadPalFromFile`` stops if the
``VGAP`` tag is not where it expects it, so a palette may legally end after the
dialog-cursor block.

``CurrentBlink`` matters for reading an attribute.  It is ``False`` by default
(``DRIVERS.PAS``) and ``False`` in all eleven shipped palettes, meaning DOS
Navigator asks the adapter for sixteen background colours rather than eight
plus blink.  So bit 7 is the background's intensity bit, not a blink flag, and
an attribute decodes as ``bg = attr >> 4``, ``fg = attr & 0x0F`` -- both in DOS
colour order, which is not ANSI's: blue and red are swapped, as are their
bright forms.  Naming the colours rather than numbering them is what keeps that
straight on the way out.


The dialog-cursor block
=======================

The block in the middle is not colour at all.  ``ADVANCE.PAS`` declares it::

    TColorIndex = record
      GroupIndex: byte;
      ColorSize:  byte;
      ColorIndex: array[0..255] of byte;
    end;

and ``COLORSEL.PAS:TColorDialog.GetIndexes`` is what fills it: ``ColorSize`` is
``Groups^.GetNumGroups``, a plain count of the group chain; ``GroupIndex`` is
which group the Colors dialog's cursor was on; and ``ColorIndex[g]`` is
``Group[g]^.Index``, which item was highlighted inside group *g*.  Only
``2 + ColorSize`` bytes of it are ever written, so the 24 bytes here are one
group number, one count of 22, and 22 item numbers.  It is where the dialog
had got to when somebody pressed Save -- window state, not appearance, and
nothing an ``.nss`` can act on.  :func:`decode` reads it anyway, because a
format is not decoded until all of it is.

Note the 22.  These palettes are dated 1997 and the source here is 1.51, whose
``RESOURCE/ENGLISH/DN.DNR`` defines **20** groups; the data agrees that they
disagree, since most palettes select item 3 or 5 of group 0 and 1.51's group 0
holds a single item.  So the block decodes structurally but its group numbers
cannot be named: they index a group list that this source no longer has.

They could not be named even with the right version, because the numbering is
per *resource*, not per program.  ``RESOURCE/RUSSIAN/DN.DNR`` carries the same
144 palette indices as the English one but orders the items inside a group
differently -- the first divergence is the 42nd item, entry 107 against 108 --
so the same ``ColorIndex[g]`` denotes a different entry depending on which
language resource was loaded when Save was pressed.  Ordinals into a
translatable list are not a thing a palette file can carry portably, which is
the strongest argument that this block is window state and nothing more.


Which byte is which
===================

The 228 bytes are one flat array, and nothing in the file says what any of them
is for.  Turbo Vision resolves a colour by walking the view tree: each view
publishes a palette string that maps its own local colour numbers into its
owner's, and the application's palette -- ``CColor`` in ``DNAPP.PAS`` -- is
where the walk ends.  So a slot's meaning is the composition of the strings
along one path.

Working that out by hand scales badly, and it does not have to be done at all.
``RESOURCE/ENGLISH/DN.DNR`` is the script the resource compiler (``RCP.PAS``)
turns into the ``dlgColors`` resource, and it names **all 144 entries** the
Colors dialog exposes -- 144 distinct indices, no duplicates -- as a tree of
``COLORGROUP`` and ``COLORITEM <name>, <index>`` lines.  That is DOS
Navigator's own answer, the one it shows the user, and :data:`ENTRIES` is it,
transcribed.  Regenerate with ``--names path/to/DN.DNR``.

Twenty-three of those were also derived independently, by composing the palette
strings; :data:`CHAINS` records the compositions and they agree with ``DN.DNR``
on every one.  Two routes to the same table is the reason to trust the other
121, for which only ``DN.DNR`` speaks.

Nesting matters when reading that file, because group names repeat: box-drawing
prefixes make a tree, and ``Tree``, ``Highlight`` and ``Menu`` each name two
different groups at different depths.  The parser reconstructs the tree from
the prefix, and :data:`GROUP_SLUGS` gives each path a short unique stem so that
``Editor/Spreadsheet/Menu`` yields ``$editor-menu-normal`` while ``Menus``
yields ``$bar`` -- a variable name, once published, is API.

``DN.DNR`` exposes 144 of the 228 entries.  The other 84 are ones DOS Navigator
never let the user set: the Turbo Vision window palettes it does not use, and
the tail of ``CColor``.  They are decoded by index or not at all.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

#: DOS attribute nibble to colour name, in DOS order.  navkit names all sixteen
#: and its own integer constants are in ANSI order, where 1 is red and 4 is
#: blue -- the reverse of this.  Emitting the *name* is what makes that a
#: non-issue: ``blue`` means blue at both ends.
DOS_COLORS = (
    "black", "blue", "green", "cyan",
    "red", "magenta", "brown", "light_gray",
    "dark_gray", "light_blue", "light_green", "light_cyan",
    "light_red", "light_magenta", "yellow", "white",
)

#: The IBM default DAC, as the six-bit values a ``.PAL`` stores.  A palette
#: matching this one is emitted as colour names, so the terminal's own theme
#: still applies; one that does not has reprogrammed the adapter and is emitted
#: as the exact ``#rrggbb`` it asked for.
STANDARD_DAC = (
    (0, 0, 0), (0, 0, 42), (0, 42, 0), (0, 42, 42),
    (42, 0, 0), (42, 0, 42), (42, 21, 0), (42, 42, 42),
    (21, 21, 21), (21, 21, 63), (21, 63, 21), (21, 63, 63),
    (63, 21, 21), (63, 21, 63), (63, 63, 21), (63, 63, 63),
)


@dataclass(frozen=True)
class Slot:
    """One named entry of the application palette.

    *index* is one-based, as Turbo Vision indexes it.  *group* and *item* are
    what DOS Navigator's own Colors dialog calls it, out of ``DN.DNR``.
    *chain* is the palette-string composition that arrives at the same number,
    where one has been worked out -- empty for the majority, which ``DN.DNR``
    names and nothing here re-derives.
    """

    name: str
    index: int
    group: str
    item: str
    chain: str = ""
    live: bool = False

    @property
    def comment(self) -> str:
        mark = ">" if self.live else " "
        tail = f" -- {self.chain}" if self.chain else ""
        return f"{mark} [{self.index:>3}] {self.item}{tail}"


#: The full path of each Colors-dialog group to the stem its variables use.
#: Group names repeat across the tree -- there are two ``Tree``s, two
#: ``Highlight``s and two ``Menu``s -- so the path is the key, not the name.
GROUP_SLUGS = {
    "Timer": "timer",
    "Menus": "menu",
    "Dialogs": "dialog",
    "Dialogs/Tree": "dialog-tree",
    "File Manager": "manager",
    "File Manager/File Panel": "panel",
    "File Manager/File Panel/Highlight": "highlight",
    "File Manager/File Panel/Drive Line": "drive-line",
    "File Manager/File Panel/Info": "info",
    "File Manager/Tree": "tree",
    "File Manager/Quick View": "quick-view",
    "File Manager/Disk Info": "disk-info",
    "File Viewer": "viewer",
    "Editor/Spreadsheet": "editor",
    "Editor/Spreadsheet/Highlight": "editor-highlight",
    "Editor/Spreadsheet/Menu": "editor-menu",
    "Disk Fixer": "fixer",
    "Disk Fixer/Menu": "fixer-menu",
    "Terminal": "terminal",
    "dBase viewer": "dbase",
}

#: Entries whose variable is named by hand rather than from the group and item.
#: These are the ones ``navigator.nss`` reads or is closest to reading, and a
#: published variable name is API: ``$panel-fg`` may not silently become
#: ``$panel-normal-text-fg`` because a transcription convention changed.
HAND_NAMED = {
    1: "desktop", 2: "bar", 3: "bar-disabled", 4: "bar-key", 5: "bar-selected",
    6: "bar-selected-disabled", 7: "bar-selected-key",
    80: "frame", 81: "active-frame", 82: "frame-icon",
    83: "scrollbar-page", 84: "scrollbar-arrow",
    85: "panel", 86: "divider", 87: "marked", 88: "cursor", 89: "marked-cursor",
    90: "active-title", 91: "title", 165: "column-title",
    172: "directory", 173: "executable", 174: "archive",
}

#: The indices ``navigator/styles/navigator.nss`` actually reads today.  Only
#: a marker in the generated comments; everything else is carried inert.
LIVE = frozenset({1, 2, 4, 85, 88, 90, 91, 172})

#: The palette-string compositions, for the entries where one was worked out.
#:
#: ``CColor`` (DNAPP.PAS:74) is the application palette, and a view inserted
#: straight into the desktop indexes it directly -- ``TGroup`` publishes no
#: palette of its own.
#:
#: * ``TBackground``  -> ``CBackground = #1``                    (DNAPP.PAS)
#: * ``TMenuView``, ``TStatusLine`` -> ``#2#3#4#5#6#7``          (MENUS.PAS:63)
#: * ``TDoubleWindow`` -> ``CDoubleWindow``                      (DBLWND.PAS)
#:   which is the two-panel window, and everything inside a panel reaches
#:   ``CColor`` through it:
#:   ``TFrame`` -> ``CFrame = #1#1#2#2#3``                       (VIEWS.PAS)
#:   ``TScrollBar`` -> ``CScrollBar = #4#5#5``                   (VIEWS.PAS)
#:   ``TFilePanel`` -> ``CPanel``                                (FLPANEL.PAS)
#:   ``TTopView`` -> ``CTopView = #11#12``                       (FLPANEL.PAS)
CHAINS = {
    1: "CBackground[1]",
    2: "CMenuView, CStatusLine[1]",
    3: "CMenuView, CStatusLine[2]",
    4: "CMenuView, CStatusLine[3]",
    5: "CMenuView, CStatusLine[4]",
    6: "CMenuView, CStatusLine[5]",
    7: "CMenuView, CStatusLine[6]",
    80: "CDoubleWindow[1] -> CFrame[1,2]",
    81: "CDoubleWindow[2] -> CFrame[3,4]",
    82: "CDoubleWindow[3] -> CFrame[5]",
    83: "CDoubleWindow[4] -> CScrollBar[1]",
    84: "CDoubleWindow[5] -> CScrollBar[2,3]",
    85: "CDoubleWindow[6] -> CPanel[1]",
    86: "CDoubleWindow[7] -> CPanel[2]",
    87: "CDoubleWindow[8] -> CPanel[3]",
    88: "CDoubleWindow[9] -> CPanel[4]",
    89: "CDoubleWindow[10] -> CPanel[5]",
    90: "CDoubleWindow[11] -> CTopView[1]",
    91: "CDoubleWindow[12] -> CTopView[2]",
    # The one entry `TFilePanel.Draw' never reads: the column-titles row is
    # drawn separately, and only when fmsColumnTitles is on.
    165: "CDoubleWindow[32] -> CPanel[6]",
    172: "CDoubleWindow[33] -> CPanel[7], ttDirectory",
    173: "CDoubleWindow[34] -> CPanel[8], ttExec",
    174: "CDoubleWindow[35] -> CPanel[9], ttArc",
}

#: Every entry DOS Navigator's Colors dialog exposes, in the dialog's own
#: order, as ``(variable stem, palette index, group, item)``.  Transcribed
#: from ``RESOURCE/ENGLISH/DN.DNR``; regenerate with ``--names``.
ENTRIES = (
    # -- Timer -------------------------------------------------------------
    ("desktop", 1, "Timer", "Color"),
    # -- Menus -------------------------------------------------------------
    ("bar", 2, "Menus", "Normal"),
    ("bar-disabled", 3, "Menus", "Disabled"),
    ("bar-key", 4, "Menus", "Shortcut"),
    ("bar-selected", 5, "Menus", "Selected"),
    ("bar-selected-disabled", 6, "Menus", "Selected disabled"),
    ("bar-selected-key", 7, "Menus", "Shortcut selected"),
    # -- Dialogs -----------------------------------------------------------
    ("dialog-frame-background", 33, "Dialogs", "Frame/background"),
    ("dialog-frame-icons", 34, "Dialogs", "Frame icons"),
    ("dialog-scroll-bar-page", 35, "Dialogs", "Scroll bar page"),
    ("dialog-scroll-bar-icons", 36, "Dialogs", "Scroll bar icons"),
    ("dialog-static-text", 37, "Dialogs", "Static text"),
    ("dialog-label-normal", 38, "Dialogs", "Label normal"),
    ("dialog-label-selected", 39, "Dialogs", "Label selected"),
    ("dialog-label-shortcut", 40, "Dialogs", "Label shortcut"),
    ("dialog-button-normal", 41, "Dialogs", "Button normal"),
    ("dialog-button-default", 42, "Dialogs", "Button default"),
    ("dialog-button-selected", 43, "Dialogs", "Button selected"),
    ("dialog-button-disabled", 44, "Dialogs", "Button disabled"),
    ("dialog-button-shortcut", 45, "Dialogs", "Button shortcut"),
    ("dialog-shortcut-selected", 178, "Dialogs", "Shortcut selected"),
    ("dialog-shortcut-default", 179, "Dialogs", "Shortcut default"),
    ("dialog-button-shadow", 46, "Dialogs", "Button shadow"),
    ("dialog-cluster-normal", 47, "Dialogs", "Cluster normal"),
    ("dialog-cluster-selected", 48, "Dialogs", "Cluster selected"),
    ("dialog-cluster-shortcut", 49, "Dialogs", "Cluster shortcut"),
    ("dialog-input-normal", 50, "Dialogs", "Input normal"),
    ("dialog-input-selected", 51, "Dialogs", "Input selected"),
    ("dialog-input-arrow", 52, "Dialogs", "Input arrow"),
    ("dialog-history-button", 53, "Dialogs", "History button"),
    ("dialog-history-sides", 54, "Dialogs", "History sides"),
    ("dialog-history-bar-page", 55, "Dialogs", "History bar page"),
    ("dialog-history-bar-icons", 56, "Dialogs", "History bar icons"),
    ("dialog-list-normal", 57, "Dialogs", "List normal"),
    ("dialog-list-focused", 58, "Dialogs", "List focused"),
    ("dialog-list-selected", 59, "Dialogs", "List selected"),
    ("dialog-list-divider", 60, "Dialogs", "List divider"),
    ("dialog-information-pane", 61, "Dialogs", "Information pane"),
    # -- Tree --------------------------------------------------------------
    ("dialog-tree-normal-tree", 104, "Tree", "Normal tree"),
    ("dialog-tree-normal-nodes", 105, "Tree", "Normal nodes"),
    ("dialog-tree-selected-node", 106, "Tree", "Selected node"),
    ("dialog-tree-default-node", 107, "Tree", "Default node"),
    ("dialog-tree-selected-default", 108, "Tree", "Selected default"),
    ("dialog-tree-selected-passive", 109, "Tree", "Selected passive"),
    ("dialog-tree-selected-def-passive", 110, "Tree", "Selected def. passive"),
    # -- File Manager ------------------------------------------------------
    ("frame", 80, "File Manager", "Frame passive"),
    ("active-frame", 81, "File Manager", "Frame active"),
    ("frame-icon", 82, "File Manager", "Frame icons"),
    ("scrollbar-page", 83, "File Manager", "Scroll bar page"),
    ("scrollbar-arrow", 84, "File Manager", "Scroll bar icons"),
    # -- File Panel --------------------------------------------------------
    ("panel", 85, "File Panel", "Normal text"),
    ("marked", 87, "File Panel", "Selected text"),
    ("cursor", 88, "File Panel", "Normal cursor"),
    ("marked-cursor", 89, "File Panel", "Selected cursor"),
    ("divider", 86, "File Panel", "List divider"),
    ("active-title", 90, "File Panel", "Directory active"),
    ("title", 91, "File Panel", "Directory passive"),
    ("column-title", 165, "File Panel", "Column title"),
    # -- Highlight ---------------------------------------------------------
    ("directory", 172, "Highlight", "Directories"),
    ("executable", 173, "Highlight", "Executables"),
    ("archive", 174, "Highlight", "Archives"),
    ("highlight-custom-1", 175, "Highlight", "Custom 1"),
    ("highlight-custom-2", 176, "Highlight", "Custom 2"),
    ("highlight-custom-3", 177, "Highlight", "Custom 3"),
    ("highlight-custom-4", 180, "Highlight", "Custom 4"),
    ("highlight-custom-5", 181, "Highlight", "Custom 5"),
    # -- Drive Line --------------------------------------------------------
    ("drive-line-drive-letters", 186, "Drive Line", "Drive letters"),
    ("drive-line-drive-selected", 188, "Drive Line", "Drive selected"),
    ("drive-line-frame", 187, "Drive Line", "Frame"),
    # -- Info --------------------------------------------------------------
    ("info-current-file", 119, "Info", "Current file"),
    ("info-selected-text", 120, "Info", "Selected text"),
    ("info-selected-numbers", 121, "Info", "Selected numbers"),
    ("info-totals-text", 122, "Info", "Totals text"),
    ("info-totals-numbers", 123, "Info", "Totals numbers"),
    ("info-free-space-text", 124, "Info", "Free space text"),
    ("info-free-space-numbers", 125, "Info", "Free space numbers"),
    # -- Tree --------------------------------------------------------------
    ("tree-normal-tree", 94, "Tree", "Normal tree"),
    ("tree-normal-nodes", 95, "Tree", "Normal nodes"),
    ("tree-selected-node", 96, "Tree", "Selected node"),
    ("tree-default-node", 97, "Tree", "Default node"),
    ("tree-selected-default", 98, "Tree", "Selected default"),
    ("tree-selected-passive", 99, "Tree", "Selected passive"),
    ("tree-selected-def-passive", 100, "Tree", "Selected def. passive"),
    ("tree-info-box", 101, "Tree", "Info box"),
    # -- Quick View --------------------------------------------------------
    ("quick-view-normal-text", 92, "Quick View", "Normal text"),
    ("quick-view-selected-text", 93, "Quick View", "Selected text"),
    # -- Disk Info ---------------------------------------------------------
    ("disk-info-normal-text", 103, "Disk Info", "Normal text"),
    ("disk-info-highlighted-text", 102, "Disk Info", "Highlighted text"),
    # -- File Viewer -------------------------------------------------------
    ("viewer-frame-passive", 112, "File Viewer", "Frame passive"),
    ("viewer-frame-active", 113, "File Viewer", "Frame active"),
    ("viewer-frame-icons", 114, "File Viewer", "Frame icons"),
    ("viewer-scroll-bar-page", 115, "File Viewer", "Scroll bar page"),
    ("viewer-scroll-bar-icons", 116, "File Viewer", "Scroll bar icons"),
    ("viewer-normal-text", 117, "File Viewer", "Normal text"),
    ("viewer-selected-text", 118, "File Viewer", "Selected text"),
    # -- Editor/Spreadsheet ------------------------------------------------
    ("editor-frame-passive", 70, "Editor/Spreadsheet", "Frame passive"),
    ("editor-frame-active", 71, "Editor/Spreadsheet", "Frame active"),
    ("editor-frame-icons", 73, "Editor/Spreadsheet", "Frame icons"),
    ("editor-frame-title", 72, "Editor/Spreadsheet", "Frame title"),
    ("editor-scroll-bar-page", 74, "Editor/Spreadsheet", "Scroll bar page"),
    ("editor-scroll-bar-icons", 75, "Editor/Spreadsheet", "Scroll bar icons"),
    ("editor-normal-text", 76, "Editor/Spreadsheet", "Normal text"),
    ("editor-selected-text", 77, "Editor/Spreadsheet", "Selected text"),
    # -- Highlight ---------------------------------------------------------
    ("editor-highlight-comments", 164, "Highlight", "Comments"),
    ("editor-highlight-symbols", 189, "Highlight", "Symbols"),
    ("editor-highlight-strings", 190, "Highlight", "Strings"),
    ("editor-highlight-numbers", 191, "Highlight", "Numbers"),
    ("editor-highlight-current-line", 182, "Highlight", "Current line"),
    ("editor-highlight-cur-line-comments", 184, "Highlight", "Cur. line comments"),
    ("editor-highlight-current-line-selected", 183, "Highlight", "Current line selected"),
    ("editor-highlight-current-column", 185, "Highlight", "Current column"),
    # -- Menu --------------------------------------------------------------
    ("editor-menu-normal", 64, "Menu", "Normal"),
    ("editor-menu-disabled", 65, "Menu", "Disabled"),
    ("editor-menu-shortcut", 66, "Menu", "Shortcut"),
    ("editor-menu-selected", 67, "Menu", "Selected"),
    ("editor-menu-selected-disabled", 68, "Menu", "Selected disabled"),
    ("editor-menu-shortcut-selected", 69, "Menu", "Shortcut selected"),
    # -- Disk Fixer --------------------------------------------------------
    ("fixer-frame-passive", 153, "Disk Fixer", "Frame passive"),
    ("fixer-frame-active", 154, "Disk Fixer", "Frame active"),
    ("fixer-frame-icons", 156, "Disk Fixer", "Frame icons"),
    ("fixer-frame-title", 155, "Disk Fixer", "Frame title"),
    ("fixer-scroll-bar-page", 157, "Disk Fixer", "Scroll bar page"),
    ("fixer-scroll-bar-icons", 158, "Disk Fixer", "Scroll bar icons"),
    ("fixer-normal-text", 159, "Disk Fixer", "Normal text"),
    ("fixer-selected-text", 160, "Disk Fixer", "Selected text"),
    ("fixer-sector-title", 161, "Disk Fixer", "Sector title"),
    ("fixer-edit-line", 162, "Disk Fixer", "Edit line"),
    # -- Menu --------------------------------------------------------------
    ("fixer-menu-normal", 147, "Menu", "Normal"),
    ("fixer-menu-disabled", 148, "Menu", "Disabled"),
    ("fixer-menu-shortcut", 149, "Menu", "Shortcut"),
    ("fixer-menu-selected", 150, "Menu", "Selected"),
    ("fixer-menu-selected-disabled", 151, "Menu", "Selected disabled"),
    ("fixer-menu-shortcut-selected", 152, "Menu", "Shortcut selected"),
    # -- Terminal ----------------------------------------------------------
    ("terminal-frame-passive", 8, "Terminal", "Frame passive"),
    ("terminal-frame-active", 9, "Terminal", "Frame active"),
    ("terminal-frame-icons", 10, "Terminal", "Frame icons"),
    ("terminal-scroll-bar-page", 11, "Terminal", "Scroll bar page"),
    ("terminal-scroll-bar-icons", 12, "Terminal", "Scroll bar icons"),
    # -- dBase viewer ------------------------------------------------------
    ("dbase-frame-passive", 166, "dBase viewer", "Frame passive"),
    ("dbase-frame-active", 167, "dBase viewer", "Frame active"),
    ("dbase-frame-icons", 168, "dBase viewer", "Frame icons"),
    ("dbase-fields-titles", 169, "dBase viewer", "Fields titles"),
    ("dbase-normal-text", 170, "dBase viewer", "Normal text"),
    ("dbase-cursor", 171, "dBase viewer", "Cursor"),
)


SLOTS: tuple[Slot, ...] = tuple(
    Slot(name, index, group, item, CHAINS.get(index, ""), index in LIVE)
    for name, index, group, item in ENTRIES
)

assert len({slot.name for slot in SLOTS}) == len(SLOTS), "duplicate variable name"
assert len({slot.index for slot in SLOTS}) == len(SLOTS), "duplicate palette index"
assert set(HAND_NAMED) | set(CHAINS) | LIVE <= {slot.index for slot in SLOTS}


class PaletteError(Exception):
    """A ``.PAL`` file did not decode."""


@dataclass(frozen=True)
class DialogCursor:
    """Where the cursor sat in DOS Navigator's Colors dialog when this was saved.

    The ``TColorIndex`` record, decoded.  Window state rather than appearance,
    and the group numbers cannot be named -- see the module docstring -- but it
    is the rest of the file, so it is read rather than skipped.
    """

    #: Which group the dialog's cursor was on.
    group: int
    #: Which item was highlighted inside each group, one entry per group.
    items: tuple[int, ...]

    @property
    def groups(self) -> int:
        """How many colour groups the writing version's dialog had."""
        return len(self.items)

    def __str__(self) -> str:
        return (f"group {self.group} of {self.groups}, items "
                + " ".join(str(item) for item in self.items))


def _decode_cursor(block: bytes) -> DialogCursor | None:
    """The ``TColorIndex`` record, or ``None`` if the palette carried none."""
    if not block:
        return None
    if len(block) < 2:
        raise PaletteError("dialog-cursor block is too short for its header")
    group, count = block[0], block[1]
    items = block[2:]
    # `ColorSize' is written from memory, where it holds the group count, and
    # LoadIndexes recomputes it as the block size less the two header bytes.
    # The two agreeing is what says the block was framed as it claims.
    if count != len(items):
        raise PaletteError(
            f"dialog-cursor block says {count} groups but carries {len(items)}"
        )
    return DialogCursor(group, tuple(items))


@dataclass(frozen=True)
class Palette:
    """One decoded ``.PAL``."""

    #: The application palette, one-based: ``attrs[0]`` is a filler so that
    #: ``attrs[85]`` is what Turbo Vision calls entry 85.
    attrs: tuple[int, ...]
    #: The Colors dialog's cursor, or ``None`` if the palette carried none.
    cursor: DialogCursor | None
    #: Sixteen ``(r, g, b)`` triples, six bits per channel, or ``None`` if the
    #: palette carried no ``VGAP`` block.
    dac: tuple[tuple[int, int, int], ...] | None
    #: ``True`` if bit 7 of an attribute means blink rather than a bright
    #: background.  ``None`` if the palette carried no ``BLNK`` block, which
    #: `LoadPalFromFile` leaves at whatever was already in effect -- ``False``.
    blink: bool | None

    @property
    def blinking(self) -> bool:
        return bool(self.blink)

    @property
    def custom_dac(self) -> bool:
        """True if this palette reprograms the adapter's sixteen colours."""
        return self.dac is not None and self.dac != STANDARD_DAC

    def split(self, index: int) -> tuple[int, int]:
        """Entry *index* as ``(foreground, background)`` DOS colour numbers.

        With blinking on, only eight backgrounds exist and bit 7 is the blink
        flag, which navkit's :class:`~navkit.style.Style` has no field for and
        this drops.  No shipped palette takes that branch.
        """
        attr = self.attrs[index]
        high = attr >> 4
        return attr & 0x0F, (high & 0x07) if self.blinking else high


def decode(data: bytes) -> Palette:
    """Decode the bytes of a ``.PAL`` file."""
    if not data:
        raise PaletteError("file is empty")

    size = data[0]
    attrs = data[1 : 1 + size]
    if len(attrs) != size:
        raise PaletteError(f"palette claims {size} bytes, {len(attrs)} present")
    if size < max(slot.index for slot in SLOTS):
        raise PaletteError(f"palette has only {size} entries; too short to map")
    offset = 1 + size

    if offset >= len(data):
        raise PaletteError("file ends before the dialog-cursor block")
    block_size = data[offset]
    offset += 1
    block = data[offset : offset + block_size]
    if len(block) != block_size:
        raise PaletteError("file ends inside the dialog-cursor block")
    offset += block_size

    # Both trailing blocks are optional: LoadPalFromFile reads a longint and
    # gives up quietly unless it spells VGAP, so a truncated palette is a valid
    # one rather than an error.
    dac = None
    blink = None
    if data[offset : offset + 4] == b"VGAP":
        offset += 4
        raw = data[offset : offset + 48]
        if len(raw) != 48:
            raise PaletteError("file ends inside the VGAP block")
        dac = tuple((raw[i], raw[16 + i], raw[32 + i]) for i in range(16))
        offset += 48
        if data[offset : offset + 4] == b"BLNK":
            offset += 4
            if offset >= len(data):
                raise PaletteError("file ends inside the BLNK block")
            blink = bool(data[offset])
            offset += 1

    if offset != len(data):
        raise PaletteError(f"{len(data) - offset} trailing bytes not accounted for")

    return Palette((0, *attrs), _decode_cursor(block), dac, blink)


# -- emitting ---------------------------------------------------------------


def _hex(channel_triple: tuple[int, int, int]) -> str:
    """A six-bit DAC triple as ``#rrggbb``."""
    return "#" + "".join(f"{round(v * 255 / 63):02x}" for v in channel_triple)


def _palette_variables(palette: Palette) -> list[str]:
    """The ``$dn-*`` colour definitions a custom-DAC palette needs."""
    assert palette.dac is not None
    return [f"$dn-{DOS_COLORS[i]}: {_hex(palette.dac[i])};" for i in range(16)]


def to_nss(palette: Palette, *, name: str, source: str, description: str) -> str:
    """Render *palette* as a theme sheet: variable definitions and nothing else.

    A theme redefines the names ``navigator.nss`` already declares and is
    loaded after it, so it needs no rules of its own -- which is also why a
    slot no rule reads yet can be carried along at no cost.
    """
    custom = palette.custom_dac

    def color(index: int) -> tuple[str, str]:
        fg, bg = palette.split(index)
        if custom:
            return f"$dn-{DOS_COLORS[fg]}", f"$dn-{DOS_COLORS[bg]}"
        return DOS_COLORS[fg], DOS_COLORS[bg]

    out = [
        "/*",
        f" * {description} -- DOS Navigator's {source}.",
        " *",
        " * Generated by tools/palconv.py; edit that, or the .PAL, not this.",
        " * Load it after navigator.nss, whose rules read the names below:",
        " *",
        f" *     python -m navigator --theme {name}",
        " *",
    ]
    if custom:
        out += [
            " * This palette reprograms the sixteen VGA colour registers, so the",
            " * sixteen names are pinned to the values it asks for rather than",
            " * left to the terminal's own theme.  That is the whole difference",
            " * between it and a palette that only rearranges attributes.",
            " */",
            "",
            "/* The adapter's colour registers, six bits per channel widened to eight. */",
            *_palette_variables(palette),
            "",
        ]
    else:
        out += [
            " * The palette leaves the sixteen VGA colour registers alone, so the",
            " * colours below are named rather than pinned and the terminal's own",
            " * theme still decides what, say, `cyan' looks like.",
            " */",
            "",
        ]

    out += [
        "/* All 144 entries DOS Navigator's Colors dialog exposes, in its groups and",
        "   its order. `>' marks the eight navigator.nss reads today; the rest are one",
        "   rule away from being live, and are carried rather than dropped. */",
    ]
    group = None
    for slot in SLOTS:
        if slot.group != group:
            group = slot.group
            out += ["", f"/* -- {group} " + "-" * max(3, 68 - len(group)) + " */"]
        fg, bg = color(slot.index)
        out.append(f"${slot.name}-fg: {fg};".ljust(38) + f"/*{slot.comment} */")
        out.append(f"${slot.name}-bg: {bg};")

    if palette.cursor is not None:
        out += [
            "",
            "/* The rest of the .PAL, for the record. Every palette also stores where",
            "   the cursor was in DOS Navigator's own Colors dialog when it was saved:",
            f"   {palette.cursor}.",
            "   Window state rather than colour, and the group numbers name a group",
            "   list no surviving source has -- these palettes were written by a build",
            f"   with {palette.cursor.groups} colour groups, and 1.51's DN.DNR defines 20. Carried as a",
            "   comment so that decoding the file is not the same as discarding it. */",
        ]
    out.append("")
    return "\n".join(out)


# -- re-deriving the name table ---------------------------------------------

#: The box-drawing characters DN.DNR indents nested group names with, in both
#: the Unicode the file is usually read as and the CP437 bytes it holds.
_BOX = "│├└─ \xb3\xc3\xc0\xc4"


def _slug(text: str) -> str:
    """``'Cur. line comments'`` -> ``'cur-line-comments'``."""
    import re
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def parse_dnr(text: str) -> list[tuple[str, int, str, str]]:
    """The ``COLORDIALOG`` section of a ``DN.DNR``, as :data:`ENTRIES` rows.

    The group tree is reconstructed from the box-drawing prefix, because the
    names alone are ambiguous -- depth is one per leading ``|`` plus one if the
    prefix has a corner in it at all.
    """
    import re

    start = text.upper().find("COLORDIALOG")
    if start < 0:
        raise PaletteError("no COLORDIALOG section")
    section = text[start : text.upper().find("\nEND", start)]

    stack: list[str] = []
    rows: list[tuple[str, int, str, str]] = []
    for line in section.splitlines():
        line = line.strip()
        upper = line.upper()
        if upper.startswith("COLORGROUP"):
            name = line[len("ColorGroup") :].strip().strip(",").strip().strip("'")
            prefix = name[: len(name) - len(name.lstrip(_BOX))]
            depth = prefix.count("│") + prefix.count("\xb3")
            if any(corner in prefix for corner in "├└\xc3\xc0"):
                depth += 1
            del stack[depth:]
            stack.append(name.lstrip(_BOX))
        elif upper.startswith("COLORITEM"):
            rest = line[len("ColorItem") :].strip()
            match = re.match(r"'((?:[^']|'')*)'\s*,\s*(\d+)", rest)
            if match is None:
                raise PaletteError(f"cannot read COLORITEM: {line!r}")
            if not stack:
                raise PaletteError("COLORITEM before any COLORGROUP")
            item = match.group(1).replace("''", "'")
            index = int(match.group(2))
            path = "/".join(stack)
            if path not in GROUP_SLUGS:
                raise PaletteError(f"no stem for group {path!r}; add one to GROUP_SLUGS")
            name = HAND_NAMED.get(index) or f"{GROUP_SLUGS[path]}-{_slug(item)}"
            rows.append((name, index, stack[-1], item))
    return rows


def _print_entries(path: Path) -> None:
    """Print an :data:`ENTRIES` literal for pasting back into this file."""
    rows = parse_dnr(path.read_text(encoding="cp437"))
    names = [row[0] for row in rows]
    indices = [row[1] for row in rows]
    for label, values in (("name", names), ("index", indices)):
        if len(set(values)) != len(values):
            raise PaletteError(f"duplicate {label} in {path}")

    print(f"# {len(rows)} entries from {path}")
    print("ENTRIES = (")
    group = None
    for name, index, group_label, item in rows:
        if group_label != group:
            group = group_label
            print(f"    # -- {group_label} " + "-" * max(3, 66 - len(group_label)))
        print(f'    ("{name}", {index}, "{group_label}", "{item}"),')
    print(")")


# -- the command line -------------------------------------------------------


def _theme_name(stem: str) -> str:
    """``_SPRING`` -> ``vga-spring``; ``NORTON`` -> ``norton``.

    The three palettes DESCRIPT.ION calls "VGA" are exactly the three whose
    names start with an underscore, and they are the ones that reprogram the
    colour registers.  Keeping that in the filename keeps the set readable.
    """
    stem = stem.lower()
    return f"vga-{stem[1:]}" if stem.startswith("_") else stem


def _descriptions(source: Path) -> dict[str, str]:
    """DOS Navigator's own one-line description of each palette, if shipped."""
    ion = source / "DESCRIPT.ION"
    if not ion.is_file():
        return {}
    found = {}
    for line in ion.read_text(encoding="cp437").splitlines():
        filename, _, text = line.partition(" ")
        if filename.upper().endswith(".PAL") and text.strip():
            found[filename.upper()] = " ".join(text.split())
    return found


def _dump(path: Path) -> None:
    palette = decode(path.read_bytes())
    print(f"{path.name}: {len(palette.attrs) - 1} entries, "
          f"blink={palette.blink}, "
          f"DAC={'custom' if palette.custom_dac else 'standard'}")
    group = None
    for slot in SLOTS:
        if slot.group != group:
            group = slot.group
            print(f"  -- {group} " + "-" * max(3, 60 - len(group)))
        fg, bg = palette.split(slot.index)
        print(f" {'>' if slot.live else ' '} [{slot.index:>3}] {slot.name:<28} "
              f"{palette.attrs[slot.index]:02X}  "
              f"{DOS_COLORS[fg]:<14} on {DOS_COLORS[bg]:<14} {slot.item}")
    print(f"\n  Colors dialog cursor: {palette.cursor}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "source", type=Path, nargs="?",
        help="the COLORS directory of a DOS Navigator distribution",
    )
    parser.add_argument(
        "--out", type=Path, help="where to write the generated .nss sheets",
    )
    parser.add_argument(
        "--dump", type=Path, help="print one .PAL's decoded slots and stop",
    )
    parser.add_argument(
        "--names", type=Path, metavar="DN.DNR",
        help="re-derive the ENTRIES table from a resource script and stop",
    )
    args = parser.parse_args(argv)

    if args.names is not None:
        _print_entries(args.names)
        return 0
    if args.dump is not None:
        _dump(args.dump)
        return 0
    if args.source is None or args.out is None:
        parser.error("a source directory and --out are both required")

    palettes = sorted(args.source.glob("*.PAL")) + sorted(args.source.glob("*.pal"))
    if not palettes:
        parser.error(f"no .PAL files under {args.source}")

    descriptions = _descriptions(args.source)
    args.out.mkdir(parents=True, exist_ok=True)
    for path in palettes:
        try:
            palette = decode(path.read_bytes())
        except PaletteError as exc:
            print(f"{path.name}: {exc}", file=sys.stderr)
            return 1
        name = _theme_name(path.stem)
        target = args.out / f"{name}.nss"
        target.write_text(to_nss(
            palette,
            name=name,
            source=path.name,
            description=descriptions.get(path.name.upper(), path.stem.title()),
        ))
        print(f"{path.name} -> {target}"
              + ("  (custom VGA registers)" if palette.custom_dac else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
