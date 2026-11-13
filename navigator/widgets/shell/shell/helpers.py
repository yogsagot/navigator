"""What the Shell's mixins share: module-level helpers of
:mod:`navigator.widgets.shell.shell.shell`.
"""

from __future__ import annotations



#: The most candidates a Tab puts in its list; ``compgen -c`` on one letter
#: can be thousands.
MAX_COMPLETIONS = 500

#: What a file name has to have escaped to reach a command as one word.
_SHELL_SPECIAL = set(" \t'\"\\$&;|<>()*?[]!#{}`")


def elapsed_text(seconds: float) -> str:
    """``hh:mm:ss.cc``, DN's ``ShowTimeInfo``: hours as many as there are,
    then minutes, seconds and hundredths, each truncated as DN's ``div``."""
    hundredths = int(seconds * 100)
    hours, hundredths = divmod(hundredths, 360000)
    minutes, hundredths = divmod(hundredths, 6000)
    whole, hundredths = divmod(hundredths, 100)
    return f"{hours:02d}:{minutes:02d}:{whole:02d}.{hundredths:02d}"


def _escape(text: str) -> str:
    """*text* with every character a shell would split or expand backslashed."""
    return "".join("\\" + char if char in _SHELL_SPECIAL else char for char in text)
