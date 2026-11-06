"""Every legacy code page Navigator reads and writes text in, grouped as the
menus show them -- one table for the viewer, the editor and Convert text.

DOS Navigator's ``*.XLT`` tables translated a handful of code pages; the
viewer began with those (CP437/850/852/866, Windows-1250/1251/1252,
ISO-8859-1/2/5, KOI8-R/U).  This is what Python's codecs offer beyond them
that a text can safely be in, **a departure, asked for**.

A code page is here only when, checked by ``tests/test_editor_encodings.py``:

- the 128 ASCII bytes are ASCII (CP864's ``%`` and Shift_JIS-2004's ``\\``
  are not, so neither is here);
- no character encodes to a CR or LF byte, so a reader may cut the bytes at
  line breaks before decoding (the stateful ISO-2022 family, HZ and UTF-7,
  and EBCDIC, fail this);
- any bytes decode and encode back to themselves through ``surrogateescape``,
  so a file the editor did not change is written back as it was (CP932,
  CP950, Big5-HKSCS and Johab map some sequences two ways, so they are left
  out -- Shift_JIS, Big5 and EUC-KR stand for them).

``one_byte`` marks the code pages a byte at a time: only those can be the
viewer's, which draws a file byte by byte (:func:`navigator.lib.viewer.byte_table`).
The Unicode encodings are not here: :mod:`navigator.lib.editor.encodings`
puts them first.
"""

from __future__ import annotations

from typing import Callable, NamedTuple

from navkit.i18n import tr


class CodePage(NamedTuple):
    #: The codec's name, as Python looks it up and ``navigator.ini`` keeps it.
    key: str
    #: The short name the bottom frame and the option strip show.
    label: str
    #: What a menu shows: the label and what it is for.
    caption: str
    #: The submenu it is under (:data:`GROUPS`).
    group: str
    #: A byte a character: the viewer can show it.
    one_byte: bool = True


#: Each group's caption, in the order the menus list them.
GROUPS: dict[str, Callable[[], str]] = {
    "western": lambda: tr("~W~estern European"),
    "central": lambda: tr("~C~entral European"),
    "southern": lambda: tr("~S~outhern and Northern European"),
    "baltic": lambda: tr("~B~altic"),
    "cyrillic": lambda: tr("C~y~rillic"),
    "greek": lambda: tr("~G~reek"),
    "turkish": lambda: tr("~T~urkish"),
    "hebrew": lambda: tr("~H~ebrew and Yiddish"),
    "arabic": lambda: tr("~A~rabic"),
    "southeast_asian": lambda: tr("Thai and ~V~ietnamese"),
    "japanese": lambda: tr("~J~apanese"),
    "chinese": lambda: tr("Ch~i~nese"),
    "korean": lambda: tr("~K~orean Hangul"),
}

CODEPAGES: tuple[CodePage, ...] = (
    CodePage("cp1252", "Windows-1252", "Windows-1252 Western", "western"),
    CodePage("iso8859-1", "ISO-8859-1", "ISO-8859-1 Latin 1", "western"),
    CodePage("iso8859-15", "ISO-8859-15", "ISO-8859-15 Latin 9", "western"),
    CodePage("cp437", "CP437", "CP437 DOS Latin US", "western"),
    CodePage("cp850", "CP850", "CP850 DOS Latin 1", "western"),
    CodePage("cp858", "CP858", "CP858 DOS Latin 1 with euro", "western"),
    CodePage("mac-roman", "MacRoman", "MacRoman Mac Western", "western"),
    CodePage("hp-roman8", "HP-Roman8", "HP-Roman8 HP Western", "western"),

    CodePage("cp1250", "Windows-1250", "Windows-1250 Central European", "central"),
    CodePage("iso8859-2", "ISO-8859-2", "ISO-8859-2 Latin 2", "central"),
    CodePage("iso8859-16", "ISO-8859-16", "ISO-8859-16 Latin 10, South-Eastern", "central"),
    CodePage("cp852", "CP852", "CP852 DOS Latin 2", "central"),
    CodePage("mac-latin2", "MacCentralEurope", "MacCentralEurope Mac Central European", "central"),

    CodePage("iso8859-3", "ISO-8859-3", "ISO-8859-3 Latin 3, South European", "southern"),
    CodePage("iso8859-10", "ISO-8859-10", "ISO-8859-10 Latin 6, Nordic", "southern"),
    CodePage("iso8859-14", "ISO-8859-14", "ISO-8859-14 Latin 8, Celtic", "southern"),
    CodePage("cp860", "CP860", "CP860 DOS Portuguese", "southern"),
    CodePage("cp861", "CP861", "CP861 DOS Icelandic", "southern"),
    CodePage("cp863", "CP863", "CP863 DOS Canadian French", "southern"),
    CodePage("cp865", "CP865", "CP865 DOS Nordic", "southern"),
    CodePage("mac-iceland", "MacIcelandic", "MacIcelandic Mac Icelandic", "southern"),

    CodePage("cp1257", "Windows-1257", "Windows-1257 Baltic", "baltic"),
    CodePage("iso8859-4", "ISO-8859-4", "ISO-8859-4 Latin 4, Baltic", "baltic"),
    CodePage("iso8859-13", "ISO-8859-13", "ISO-8859-13 Latin 7, Baltic Rim", "baltic"),
    CodePage("cp775", "CP775", "CP775 DOS Baltic", "baltic"),

    CodePage("cp1251", "Windows-1251", "Windows-1251 Cyrillic", "cyrillic"),
    CodePage("koi8-r", "KOI8-R", "KOI8-R Russian", "cyrillic"),
    CodePage("koi8-u", "KOI8-U", "KOI8-U Ukrainian", "cyrillic"),
    CodePage("koi8-t", "KOI8-T", "KOI8-T Tajik", "cyrillic"),
    CodePage("iso8859-5", "ISO-8859-5", "ISO-8859-5 Cyrillic", "cyrillic"),
    CodePage("cp866", "CP866", "CP866 DOS Cyrillic", "cyrillic"),
    CodePage("cp855", "CP855", "CP855 DOS Cyrillic", "cyrillic"),
    CodePage("cp1125", "CP1125", "CP1125 DOS Ukrainian", "cyrillic"),
    CodePage("mac-cyrillic", "MacCyrillic", "MacCyrillic Mac Cyrillic", "cyrillic"),
    CodePage("kz1048", "KZ-1048", "KZ-1048 Kazakh", "cyrillic"),
    CodePage("ptcp154", "PT154", "PT154 Kazakh (Paratype)", "cyrillic"),

    CodePage("cp1253", "Windows-1253", "Windows-1253 Greek", "greek"),
    CodePage("iso8859-7", "ISO-8859-7", "ISO-8859-7 Greek", "greek"),
    CodePage("cp737", "CP737", "CP737 DOS Greek", "greek"),
    CodePage("cp869", "CP869", "CP869 DOS Greek 2", "greek"),
    CodePage("mac-greek", "MacGreek", "MacGreek Mac Greek", "greek"),

    CodePage("cp1254", "Windows-1254", "Windows-1254 Turkish", "turkish"),
    CodePage("iso8859-9", "ISO-8859-9", "ISO-8859-9 Latin 5, Turkish", "turkish"),
    CodePage("cp857", "CP857", "CP857 DOS Turkish", "turkish"),
    CodePage("mac-turkish", "MacTurkish", "MacTurkish Mac Turkish", "turkish"),

    CodePage("cp1255", "Windows-1255", "Windows-1255 Hebrew", "hebrew"),
    CodePage("iso8859-8", "ISO-8859-8", "ISO-8859-8 Hebrew", "hebrew"),
    CodePage("cp862", "CP862", "CP862 DOS Hebrew", "hebrew"),

    CodePage("cp1256", "Windows-1256", "Windows-1256 Arabic", "arabic"),
    CodePage("iso8859-6", "ISO-8859-6", "ISO-8859-6 Arabic", "arabic"),
    CodePage("cp720", "CP720", "CP720 DOS Arabic", "arabic"),

    CodePage("cp874", "Windows-874", "Windows-874 Thai", "southeast_asian"),
    CodePage("tis-620", "TIS-620", "TIS-620 Thai", "southeast_asian"),
    CodePage("iso8859-11", "ISO-8859-11", "ISO-8859-11 Thai", "southeast_asian"),
    CodePage("cp1258", "Windows-1258", "Windows-1258 Vietnamese", "southeast_asian"),

    CodePage("shift_jis", "Shift_JIS", "Shift_JIS Japanese", "japanese", False),
    CodePage("euc_jp", "EUC-JP", "EUC-JP Japanese", "japanese", False),

    CodePage("gb18030", "GB18030", "GB18030 Chinese Simplified", "chinese", False),
    CodePage("gbk", "GBK", "GBK Chinese Simplified", "chinese", False),
    CodePage("gb2312", "GB2312", "GB2312 Chinese Simplified", "chinese", False),
    CodePage("big5", "Big5", "Big5 Chinese Traditional", "chinese", False),

    CodePage("euc_kr", "EUC-KR", "EUC-KR Korean", "korean", False),
    CodePage("cp949", "CP949", "CP949 Korean (Unified Hangul)", "korean", False),
)

#: The code pages a byte a character: what the viewer can show.
ONE_BYTE: tuple[CodePage, ...] = tuple(page for page in CODEPAGES if page.one_byte)

_BY_KEY = {page.key: page for page in CODEPAGES}


def find(key: str) -> CodePage | None:
    return _BY_KEY.get(key)


def grouped(pages: tuple[CodePage, ...] = CODEPAGES) -> list[tuple[str, list[CodePage]]]:
    """*pages* by group, the groups in :data:`GROUPS`' order, empty ones left out."""
    return [(group, members) for group in GROUPS
            if (members := [page for page in pages if page.group == group])]
