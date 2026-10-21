"""What the multi-rename box does: the rule read from its controls, the
preview kept up with every key, and OK only for a plan that can be done.

The rule is kept for the session, as *Find File*'s answers are.
"""

from __future__ import annotations

from typing import Any, Hashable, Sequence

from navkit.i18n import tr, tr_n
from navkit.reactive import effect
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.file_ops import multirename

#: The last rule accepted, offered again next time.
_session: dict[str, Any] = {"rule": multirename.Rule()}


class MultiRenameDialog(Dialog):
    """*items* to rename, *taken* the names already in each of their places."""

    def __init__(self, items: Sequence[multirename.Item] = (), taken: dict[Hashable, set[str]] | None = None,
                 **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.files = list(items)
        self.taken = taken or {}
        self.rows: list[multirename.Row] = []
        self.problem: str | None = None
        rule = _session["rule"]
        self.name_mask.value = rule.name_mask
        self.ext_mask.value = rule.ext_mask
        self.search.value = rule.search
        self.replace.value = rule.replace
        self.options.value = (1 if rule.regex else 0) | (2 if rule.case_sensitive else 0) | (4 if rule.first_only else 0)
        self.case.value = multirename.CASES.index(rule.case)
        self.start.value = str(rule.counter_start)
        self.step.value = str(rule.counter_step)
        self.digits.value = str(rule.counter_width)
        # The mask all selected, so typing replaces it.
        self.name_mask.entry.anchor, self.name_mask.entry.cursor = 0, len(rule.name_mask)

    def mounted(self) -> None:
        super().mounted()
        effect(self, MultiRenameDialog._follow_rule)

    def rule(self) -> multirename.Rule:
        """The rule as the controls stand; :class:`multirename.RuleError` for a counter that is no number."""
        def number(text: str, minimum: int | None = None) -> int:
            try:
                value = int(text.strip() or "0")
            except ValueError:
                raise multirename.RuleError(tr("{text} is not a number").format(text=text)) from None
            return value if minimum is None else max(minimum, value)

        options = self.options.value
        return multirename.Rule(
            name_mask=self.name_mask.value, ext_mask=self.ext_mask.value,
            search=self.search.value, replace=self.replace.value,
            regex=bool(options & 1), case_sensitive=bool(options & 2), first_only=bool(options & 4),
            case=multirename.CASES[self.case.value],
            counter_start=number(self.start.value), counter_step=number(self.step.value),
            counter_width=number(self.digits.value, 1))

    def _follow_rule(self) -> None:
        """The preview and the line under it, from the controls as they are."""
        try:
            rows = multirename.plan(self.rule(), self.files, self.taken)
        except multirename.RuleError as error:
            self.rows, self.problem = [], str(error)
            self.preview.items = [multirename.Row(item, item.name) for item in self.files]
            self.status.text = self.problem
            return
        self.rows, self.problem = rows, None
        self.preview.items = rows
        changed = sum(1 for row in rows if row.changed)
        wrong = sum(1 for row in rows if row.problem)
        if wrong:
            self.status.text = tr_n("{n} name cannot be given", "{n} names cannot be given", wrong)
        else:
            self.status.text = tr_n("{n} file to rename", "{n} files to rename", changed)

    def valid(self) -> bool:
        """OK only for a rule that reads, with something renamed and nothing wrong."""
        return (self.problem is None and any(row.changed for row in self.rows)
                and not any(row.problem for row in self.rows))

    def accept(self) -> list[multirename.Row]:
        """The rows to rename, the rule kept for next time."""
        _session["rule"] = self.rule()
        return [row for row in self.rows if row.changed]
