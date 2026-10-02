## Specificity and the tie-break

**CSS's model, unchanged: a three-column tuple `(names, classes + states, types)` compared left to right, ties broken by
source order with the last rule winning.** There is no `!important`.

### The tuple

Count every simple selector across the whole complex selector; combinators contribute nothing, as in CSS.
`Panel:active::row.selected` is `(0, 2, 2)` — `:active` and `.selected` in the middle column, `Panel` and the `::row`
part in the last.

**The columns do not add.** One `#name` beats any number of classes — a tuple comparison, not a weighted sum. This is
worth keeping rather than simplifying: a sum needs an arbitrary base to carry each column, and the arbitrary base is
wrong as soon as a selector is long enough to overflow it. Python's own tuple ordering is the comparator, so there is
nothing to implement.

**Class and state share a column,** as in CSS. They are orthogonal conditions — there is no principled reason
`Panel:active` should outrank `Panel.wide` or the reverse — so source order settles it, which is what CSS concluded too.

### The cascade is per property, not per rule

The important consequence, and the one easiest to get wrong when reading "bake the winner"
above: the *winner* is decided separately for each declaration, not once for the rule. A lower-specificity rule still
supplies every property the higher one did not mention.

Sorting the matching rules ascending by `(specificity, order)` and updating a dict with each rule's declarations in turn
produces exactly this, because a later `update` only overwrites the keys it carries:

```python
declarations = {}
for rule in sorted(matches, key=lambda r: (r.specificity, r.order)):
    declarations.update(rule.declarations)
return base.derive(**declarations)
```

Checked against the case that distinguishes it: with `Panel {fg; bg}`, `Panel:active {fg}` and
`#left-panel {bg}`, the name rule wins overall on specificity yet `fg` still comes from
`Panel:active`, because `#left-panel` never mentioned `fg`. A per-rule cascade would have dropped it.

So the whole engine below the selector matcher is a sort, a dict update and one `derive`.

### Last wins, and that is the theming mechanism

Source order breaking a tie is not merely a convention inherited from CSS here — it is how a colour scheme is meant to
work. A user's sheet loaded after the built-in one overrides it without having to out-specify it, rule by rule. For a
project whose point is recreating a particular look, and whose users will want to swap schemes, that is the feature.
"Order" is therefore sheet load order first, then position within the sheet.

### No `!important`

CSS needs it for two jobs, and both are already done here by other means:

- **Beating an inline style.** An inline declaration is the widget's own statement about itself, and a sheet reaching
  past it inverts who is in charge. The reason people actually reach for
  `!important` — forcing a theme through — is served here by variables, which change what the rules resolve to instead
  of fighting them.
- **Letting a user sheet override an author sheet.** Load order does this, per above.

It would buy nothing and cost the wart, so it is left out deliberately rather than not-yet-implemented.

