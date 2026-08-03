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
``u8``       length of the file-highlight index block, ``0`` or
             ``2 + ColorIndexes^.ColorSize`` -- always 24 here
``24 x u8``  that block: which highlight group each of the five
             user-defined file masks paints in.  Not decoded; the
             masks it indexes live in the configuration, not here
``4 x u8``   the literal ``VGAP``
``48 x u8``  the VGA DAC: ``R[16]``, then ``G[16]``, then ``B[16]``,
             planar rather than interleaved, six bits per channel
``4 x u8``   the literal ``BLNK``
``u8``       ``CurrentBlink`` -- ``0`` in every shipped palette
===========  ======================================================

Every shipped palette is exactly 311 bytes and ends flush with the blink byte.
The two trailing blocks are optional on read: ``LoadPalFromFile`` stops if the
``VGAP`` tag is not where it expects it, so a palette may legally end after the
highlight indexes.

``CurrentBlink`` matters for reading an attribute.  It is ``False`` by default
(``DRIVERS.PAS``) and ``False`` in all eleven shipped palettes, meaning DOS
Navigator asks the adapter for sixteen background colours rather than eight
plus blink.  So bit 7 is the background's intensity bit, not a blink flag, and
an attribute decodes as ``bg = attr >> 4``, ``fg = attr & 0x0F`` -- both in DOS
colour order, which is not ANSI's: blue and red are swapped, as are their
bright forms.  Naming the colours rather than numbering them is what keeps that
straight on the way out.


Which byte is which
===================

The 228 bytes are one flat array, and nothing in the file says what any of them
is for.  Turbo Vision resolves a colour by walking the view tree: each view
publishes a palette string that maps its own local colour numbers into its
owner's, and the application's palette -- ``CColor`` in ``DNAPP.PAS`` -- is
where the walk ends.  So a slot's meaning is the composition of the strings
along one path, and :data:`SLOTS` below is that composition worked out by hand
for the paths this application currently paints.  Each entry cites the chain it
came from; ``COLORSEL.PAS`` builds the same table at runtime from the
``dlgColors`` resource in ``DN.DLG``, which is where the names DOS Navigator
itself shows the user live.
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

    *index* is one-based, as Turbo Vision indexes it.  *chain* records how the
    number was arrived at, and is written into the generated sheet so the next
    person to doubt it can follow the same path through the Pascal.
    """

    name: str
    index: int
    chain: str
    live: bool = True


#: The chains, once, so the citations below stay short:
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
SLOTS: tuple[Slot, ...] = (
    # -- what the sheet's rules use today ------------------------------------
    Slot("desktop", 1, "CBackground[1]"),
    Slot("bar", 2, "CMenuView/CStatusLine[1] normal text"),
    Slot("bar-key", 4, "CMenuView/CStatusLine[3] shortcut"),
    Slot("panel", 85, "CDoubleWindow[6] -> CPanel[1] normal text"),
    Slot("cursor", 88, "CDoubleWindow[9] -> CPanel[4] cursor"),
    Slot("active-title", 90, "CDoubleWindow[11] -> CTopView[1] focused"),
    Slot("title", 91, "CDoubleWindow[12] -> CTopView[2] unfocused"),
    Slot("directory", 172, "CDoubleWindow[33] -> CPanel[7] ttDirectory"),
    # -- decoded, and waiting for the widget that paints it ------------------
    Slot("bar-disabled", 3, "CMenuView/CStatusLine[2]", live=False),
    Slot("bar-selected", 5, "CMenuView/CStatusLine[4]", live=False),
    Slot("bar-selected-disabled", 6, "CMenuView/CStatusLine[5]", live=False),
    Slot("bar-selected-key", 7, "CMenuView/CStatusLine[6]", live=False),
    Slot("frame", 80, "CDoubleWindow[1] -> CFrame[1,2] passive", live=False),
    Slot("active-frame", 81, "CDoubleWindow[2] -> CFrame[3,4] active", live=False),
    Slot("frame-icon", 82, "CDoubleWindow[3] -> CFrame[5]", live=False),
    Slot("scrollbar-page", 83, "CDoubleWindow[4] -> CScrollBar[1]", live=False),
    Slot("scrollbar-arrow", 84, "CDoubleWindow[5] -> CScrollBar[2,3]", live=False),
    Slot("divider", 86, "CDoubleWindow[7] -> CPanel[2] column divider", live=False),
    Slot("marked", 87, "CDoubleWindow[8] -> CPanel[3] tagged file", live=False),
    Slot("marked-cursor", 89, "CDoubleWindow[10] -> CPanel[5]", live=False),
    Slot("executable", 173, "CDoubleWindow[34] -> CPanel[8] ttExec", live=False),
    Slot("archive", 174, "CDoubleWindow[35] -> CPanel[9] ttArc", live=False),
)


class PaletteError(Exception):
    """A ``.PAL`` file did not decode."""


@dataclass(frozen=True)
class Palette:
    """One decoded ``.PAL``."""

    #: The application palette, one-based: ``attrs[0]`` is a filler so that
    #: ``attrs[85]`` is what Turbo Vision calls entry 85.
    attrs: tuple[int, ...]
    #: The file-highlight index block, kept verbatim and otherwise unread.
    indexes: bytes
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
        raise PaletteError("file ends before the highlight index block")
    index_size = data[offset]
    offset += 1
    indexes = data[offset : offset + index_size]
    if len(indexes) != index_size:
        raise PaletteError("file ends inside the highlight index block")
    offset += index_size

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

    return Palette((0, *attrs), indexes, dac, blink)


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
        " * Load it after navigator.nss, which declares every name below:",
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

    for live in (True, False):
        if live:
            out.append("/* What the rules in navigator.nss read. */")
        else:
            out += [
                "",
                "/* Decoded from the same palette, and read by nothing yet.  Each is one",
                "   rule away from being live, so they are carried rather than dropped. */",
            ]
        for slot in SLOTS:
            if slot.live is not live:
                continue
            fg, bg = color(slot.index)
            out.append(f"/* [{slot.index:>3}] {slot.chain} */")
            out.append(f"${slot.name}-fg: {fg};")
            out.append(f"${slot.name}-bg: {bg};")
    out.append("")
    return "\n".join(out)


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
          f"{len(palette.indexes)} index bytes, "
          f"blink={palette.blink}, "
          f"DAC={'custom' if palette.custom_dac else 'standard'}")
    for slot in SLOTS:
        fg, bg = palette.split(slot.index)
        mark = " " if slot.live else "-"
        print(f" {mark} [{slot.index:>3}] {slot.name:<22} "
              f"{palette.attrs[slot.index]:02X}  "
              f"{DOS_COLORS[fg]:<14} on {DOS_COLORS[bg]:<14} {slot.chain}")


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
    args = parser.parse_args(argv)

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
