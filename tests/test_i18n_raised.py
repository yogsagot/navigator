"""Error text raised in ``navigator`` is translated where it is raised.

``tools/i18n.py check`` keeps the catalogues whole for every literal ``tr()``
key -- but a message built into an exception (``raise OSError(errno.ENOENT,
"Where it came from is not known")``) has no key to miss, and reached a
Russian box in English.  This walks the code instead: any sentence raised as
one of the errors a user is shown, not wrapped in ``tr``, is a failure.

The root helper is the exception: a process of its own, started ``-I`` as
root, with no catalogues.  Its messages come back as text and are translated
as they arrive (``elevate.HELPER_TEXTS``), which the second test keeps whole.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: The errors whose message a user is shown -- a box, a toast, a panel's line.
SHOWN = {
    "OSError", "FileNotFoundError", "PermissionError", "FileExistsError", "IsADirectoryError",
    "NotADirectoryError", "TimeoutError", "ConnectionError", "InterruptedError", "BlockingIOError",
    "DriveGone", "ToolError", "SplitError",
}

#: What is the helper's own, translated on arrival (the second test).
HELPER = ROOT / "navigator" / "lib" / "system" / "roothelper.py"

#: Messages that never reach a user, each with why.  Keep it near empty.
ALLOWED: dict[tuple[str, str], str] = {}

TRANSLATORS = {"tr", "tr_n", "tr_plain"}


def _sentence(text: str) -> bool:
    """Words for a reader: two or more of them -- not a lone name, a format
    of placeholders, or a command line's fragment."""
    import re

    return len(re.findall(r"[A-Za-z]{2,}", text.replace("{}", ""))) >= 2 and " " in text.strip()


def _literal(node: ast.AST, constants: dict[str, str]) -> str | None:
    """The English sentence *node* is, when it is one: a literal, an
    f-string, or a module constant holding one."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value if _sentence(node.value) else None
    if isinstance(node, ast.JoinedStr):
        text = "".join(part.value if isinstance(part, ast.Constant) else "{}" for part in node.values)
        return text if _sentence(text) else None
    if isinstance(node, ast.Name) and node.id in constants:
        return constants[node.id]
    if isinstance(node, ast.BoolOp):  # ``said or "A sentence"``
        return next((text for value in node.values if (text := _literal(value, constants)) is not None), None)
    if isinstance(node, ast.IfExp):
        return _literal(node.body, constants) or _literal(node.orelse, constants)
    return None


def _constants(tree: ast.Module) -> dict[str, str]:
    """Module-level ``NAME = "A sentence"`` -- not ``tr_noop("...")``, which is extracted."""
    found = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
                and _sentence(node.value.value)):
            found[node.targets[0].id] = node.value.value
    return found


def raised_untranslated(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    constants = _constants(tree)
    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call)):
            continue
        func = node.exc.func
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
        if name not in SHOWN:
            continue
        for arg in node.exc.args:
            text = _literal(arg, constants)
            if text is not None:
                found.append((node.lineno, text))
    return found


def test_every_message_raised_for_a_user_is_translated_where_it_is_raised():
    found = []
    for path in sorted((ROOT / "navigator").rglob("*.py")):
        if path == HELPER or path.name.endswith("_nml.py"):
            continue
        for line, text in raised_untranslated(path):
            where = str(path.relative_to(ROOT))
            if (where, text) not in ALLOWED:
                found.append(f"{where}:{line}: {text!r}")
    assert found == [], "raised in English, not through tr():\n" + "\n".join(found)


def test_every_message_the_root_helper_raises_is_translated_as_it_arrives():
    from navigator.lib.system.elevate import HELPER_TEXTS

    tree = ast.parse(HELPER.read_text(encoding="utf-8"))
    constants = _constants(tree)
    raised = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
            for arg in node.exc.args:
                # A template filled on the helper's side (*unknown request
                # NAME*, a guard no user meets) cannot be looked up: left out.
                if isinstance(arg, ast.JoinedStr):
                    continue
                text = _literal(arg, constants)
                if text is not None:
                    raised.add(text)
    assert raised and raised <= set(HELPER_TEXTS), sorted(raised - set(HELPER_TEXTS))


# -- and they come out in the user's language ---------------------------------------------------------


XX = """[meta]
name = "Test"

[strings]
"Where it came from is not known" = "XX unknown origin"
"Remote drive {name} is not accessible" = "XX {name} gone"
"Cannot connect to {hostname}: {reason}" = "XX {hostname} refused: {reason}"
"Not a regular file" = "XX not a file"
"""


def test_an_error_is_raised_in_the_language_shown(tmp_path):
    import errno

    from navkit.i18n import LOCALE, register_directory

    from navigator.lib.drives.base import DriveGone, reason_of
    from navigator.lib.file_ops import trash
    from navigator.lib.system import elevate

    (tmp_path / "xx.toml").write_text(XX, encoding="utf-8")
    register_directory(tmp_path)
    LOCALE.code = "xx"
    item = trash.Item(trash=tmp_path, name="lost")  # its info file says nothing of where it was
    try:
        trash.restore(item)
    except OSError as error:
        assert error.strerror == "XX unknown origin"
    else:
        raise AssertionError("restored with no origin")
    gone = DriveGone("srv")
    assert gone.strerror == "XX srv gone"
    assert reason_of(gone) == ""  # a bare *not accessible* says nothing more, in any language
    assert elevate._helper_text("Not a regular file") == "XX not a file"
    import os

    assert elevate._helper_text(os.strerror(errno.ENOENT)) == os.strerror(errno.ENOENT)  # the system's, as came
