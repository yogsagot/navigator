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

#: The repository's root, so ``navigator`` imports when this is run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from navigator.palette import DERIVED, DOS_COLORS, ENTRIES  # noqa: E402 -- the tables the app reads too

#: The IBM default DAC, as the six-bit values a ``.PAL`` stores.  A palette
#: matching this one is emitted as colour names, and a name still carries these
#: values: ``navkit.capabilities.VGA_PALETTE`` is this table widened to eight
#: bits per channel, and is what Navigator resolves a name through by default.
#: A palette that does *not* match has reprogrammed the adapter, and is emitted
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
LIVE = frozenset({1, 2, 4, 85, 88, 90, 91, 165, 172, 173, 174, 175, 176, 177, 180, 181})

#: Where Navigator deliberately draws a slot other than as the palette says:
#: theme name -> slot index -> ``(fg, bg, why)``, each colour a DOS colour
#: index, a ``#rrggbb`` a VGA never had, or ``None`` to keep the palette's.  Applied when the theme is
#: written, and marked in its comment, so a regeneration keeps the departure
#: and a reader of the theme sees it was one.
#:
#: * ``default`` [117], the viewer's *Normal text*: ``$87`` in DEFAULT.PAL,
#:   light grey on dark grey -- #AAAAAA on #555555, a contrast of 2.6:1 that
#:   is barely legible on a modern screen.  #D8D8D8 is between light grey
#:   and white, keeps the ground DN chose, and is the dimmest grey that a
#:   sixteen-colour terminal rounds to white rather than back to light grey.
#: * ``default`` [85], the file panel's *Normal text*: the same light grey on
#:   dark grey in DEFAULT.PAL, lifted to the viewer's #D8D8D8 so a file
#:   listing reads as the viewer does.
#: * ``default`` [76], the editor's *Normal text*: likewise, so an edit
#:   window reads as the viewer does.
DEPARTURES: dict[str, dict[int, tuple[int | str | None, int | str | None, str]]] = {
    "default": {
        76: ("#d8d8d8", None, "lighter text, as the viewer's [117]"),
        85: ("#d8d8d8", None, "lighter text, as the viewer's [117]"),
        117: ("#d8d8d8", None, "lighter text, for contrast"),
    },
}

#: Where a theme draws a :data:`DERIVED` variable other than as its alias:
#: theme name -> name -> ``(fg, bg, why)``, as :data:`DEPARTURES`.
#:
#: * ``default`` ``symlink``: light grey, Midnight Commander's own colour for
#:   a link, a step down from the #D8D8D8 of an ordinary row -- the alias
#:   would make every link look like an image.
#: * ``default`` ``temp``: black on the dark grey ground, faint, as MC's
#:   temporaries are: a file to overlook.
#: * ``default`` ``source``: #87AFFF rather than Custom 5's light blue, which
#:   is #5555FF on #555555 -- barely there at all.
#: * ``default`` ``image``: #40C8C8, a step up from Custom 1's cyan (#00AAAA)
#:   and still short of the executables' light cyan (#55FFFF).
#: * ``default`` ``document``, ``device``, ``special``: amber #E5B567 rather
#:   than Custom 3's light magenta, at the user's request.  Devices and
#:   sockets share it as they share the slot; they are rare outside ``/dev``.
DERIVED_DEPARTURES: dict[str, dict[str, tuple[int | str | None, int | str | None, str]]] = {
    "default": {
        "symlink": (7, None, "MC's link colour; the alias would match images"),
        "temp": (0, None, "faint, as MC draws temporaries"),
        "source": ("#87afff", None, "lighter than light blue, which is barely visible"),
        "image": ("#40c8c8", None, "brighter than cyan, short of light cyan"),
        "document": ("#e5b567", None, "amber rather than magenta"),
        "device": ("#e5b567", None, "amber rather than magenta, as documents"),
        "special": ("#e5b567", None, "amber rather than magenta, as documents"),
    },
}

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

    departures = DEPARTURES.get(name, {})

    def spell(value: int | str) -> str:
        if isinstance(value, str):
            return value
        return f"$dn-{DOS_COLORS[value]}" if custom else DOS_COLORS[value]

    def color(index: int) -> tuple[str, str]:
        fg, bg = palette.split(index)
        if index in departures:
            new_fg, new_bg, _why = departures[index]
            fg = fg if new_fg is None else new_fg
            bg = bg if new_bg is None else new_bg
        return spell(fg), spell(bg)

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
            " * colours below are named rather than pinned -- a name meaning the",
            " * value the standard IBM DAC held, which is what Navigator paints",
            " * unless `--palette terminal' hands the question to the terminal's",
            " * own theme.",
            " */",
            "",
        ]

    out += [
        "/* All 144 entries DOS Navigator's Colors dialog exposes, in its groups and",
        "   its order. `>' marks the ones navigator.nss reads today; the rest are one",
        "   rule away from being live, and are carried rather than dropped. */",
    ]
    group = None
    for slot in SLOTS:
        if slot.group != group:
            group = slot.group
            out += ["", f"/* -- {group} " + "-" * max(3, 68 - len(group)) + " */"]
        fg, bg = color(slot.index)
        comment = slot.comment
        if slot.index in departures:
            was_fg, was_bg = palette.split(slot.index)
            was = DOS_COLORS[was_fg] + " on " + DOS_COLORS[was_bg]
            comment += f" -- Navigator: {departures[slot.index][2]}; the .PAL has {was}"
        out.append(f"${slot.name}-fg: {fg};".ljust(38) + f"/*{comment} */")
        out.append(f"${slot.name}-bg: {bg};")

    slots = {slot.index: slot for slot in SLOTS}
    derived_departures = DERIVED_DEPARTURES.get(name, {})
    out += [
        "",
        "/* -- Navigator's own: no DN slot ---------------------------------------- */",
        "/* Each is an alias of the slot it names, so this palette colours it too. */",
    ]
    for variable, (index, why) in DERIVED.items():
        if isinstance(index, tuple):
            fg, bg = spell(index[0]), spell(index[1])
            comment = f"  {why}"
        else:
            stem = slots[index].name
            fg, bg = f"${stem}-fg", f"${stem}-bg"
            comment = f"  {why} [{index}]"
        if variable in derived_departures:
            new_fg, new_bg, reason = derived_departures[variable]
            fg = fg if new_fg is None else spell(new_fg)
            bg = bg if new_bg is None else spell(new_bg)
            comment += f" -- Navigator: {reason}"
        out.append(f"${variable}-fg: {fg};".ljust(38) + f"/*{comment} */")
        out.append(f"${variable}-bg: {bg};")

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
