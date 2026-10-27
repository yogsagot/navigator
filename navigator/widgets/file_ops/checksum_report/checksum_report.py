"""What the report says: the counts, and one row for every file that did not match."""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr, tr_n

from navml.widgets.dialog.dialog import Dialog

from navigator.lib.file_ops.checksum import NO_CHECKSUMS, VerifyResult


class ChecksumReport(Dialog):
    """*Verify Checksums*: how many files matched, and the ones that did not."""

    def __init__(self, result: VerifyResult | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.message.visible = False
        result = result or VerifyResult()
        self.summary.text = summary(result)
        self.bad.items = rows(result)


def summary(result: VerifyResult) -> str:
    """The counts, a line each; one line when every file matched."""
    if not result.bad and not result.malformed and not result.lists_unreadable:
        return tr_n("The {n} file is OK.", "All {n} files are OK.", result.ok)
    lines = [
        tr("OK: {n}").format(n=result.ok),
        tr("Failed: {n}").format(n=len(result.failed)),
        tr("Missing: {missing}    Unreadable: {unreadable}").format(
            missing=len(result.missing), unreadable=len(result.unreadable)),
    ]
    if result.malformed:
        lines.append(tr_n("{n} line is not a checksum.", "{n} lines are not checksums.", result.malformed))
    return "\n".join(lines)


def rows(result: VerifyResult) -> list[str]:
    """One row per file that did not match, and per list not read."""
    failed, missing, unreadable = tr("FAILED"), tr("MISSING"), tr("UNREADABLE")
    width = max(len(failed), len(missing), len(unreadable)) + 2
    out = [f"{failed:<{width}}{location}" for location in result.failed]
    out += [f"{missing:<{width}}{location}" for location in result.missing]
    out += [f"{unreadable:<{width}}{location}: {reason}" for location, reason in result.unreadable]
    no_checksums = tr("no checksums in it")
    out += [f"{unreadable:<{width}}{location}: {no_checksums if reason == NO_CHECKSUMS else reason}"
            for location, reason in result.lists_unreadable]
    return out
