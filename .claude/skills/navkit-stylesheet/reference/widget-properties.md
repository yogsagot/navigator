## Widget properties: `Style` does **not** grow a border field

The last of `navigator/__main__.py`'s style decisions is the `Panel` frame doubling on `active`
(`navigator/__main__.py`), which picks a box-drawing character set. It should be stylable — but not by adding a field to
`Style`.

### Why not in `Style`

`Style` is a **per-cell** value — `type Cell = tuple[str, Style]` — and its entire contract is that it knows its own SGR
sequence. A character set produces no escape sequence, and is meaningless for the overwhelming majority of cells, which
are not borders.

The contract is load-bearing rather than decorative, and breaking it breaks `render_diff` in two places at once. It
compares whole cells (`screen.py:309`) and then styles (`screen.py:314`), both by equality, and emits `sgr()` whenever
the latter differs. A field that `sgr()` cannot express makes both comparisons report a change the terminal cannot see.
Measured on a 40x5 buffer whose glyphs and colours were identical and whose border field differed: **244 bytes emitted
for a visually identical frame**, against 0 for the same style object. Emitting only what changed is the whole purpose
of that function.

There is a plainer objection underneath. The character set is not an appearance of a cell at all: once `draw_box` has
chosen `╔` over `┌`, the choice *is* the cell's character. It is an input to a drawing operation, and inputs to drawing
operations are not styles.

### Why it should still be stylable

Not really for the active-panel frame, which in DOS Navigator is a fixed focus convention rather than a matter of taste.
The case that matters is **ASCII fallback**: a terminal or font without box-drawing glyphs needs `+-|`, and swapping
that in wholesale is exactly what a stylesheet is for.

### Where it goes instead

Into the declarations, not into the type. The cascade already resolves a `dict[str, object]`; only the **bake** step
changes. Keys that are `Style` fields become the `Style`; keys that are not are *widget properties*, which the widget
reads when it paints:

```
Panel        { border: single }
Panel:active { border: double }
```

Nothing else moves. Matching, specificity, variables, parts and the inheritance of colour are all untouched —
`Style(**declarations)` simply becomes `Style(**appearance)` plus a leftover map the widget can consult.

**Widget properties do not inherit.** This is the one split in the design, and it does not contradict the earlier
refusal of a CSS-style inheritance list — it *locates* that refusal. Within `Style`, all seven fields inherit, and the
reason given there still holds: every one of them is a cell appearance. The boundary is `Style` itself, which is a
principle rather than a list, and it has to be there — an inherited `border: double` would hand a double frame to every
child of an active panel.

**Both halves stay checkable at parse time.** A declaration key is valid if it is a `Style`
field *or* a stylable property some widget declares. Widgets already have to declare their parts; declaring their
properties in the same place gives the parser a union to check against, so `bordr: double` still fails with a `.nss`
line rather than being silently ignored the way a CSS typo is.

### The declaration is a class attribute

**Done.** `StyleProperty` is the declared route and `register_property()` the bare one underneath it:

```python
class Widget:
    border = StyleProperty(glyphs.DEFAULT_BOX, values=tuple(glyphs.BOX_CHARSETS))

class Panel(Widget):
    icons = StyleProperty("auto", values=("auto", "none"))
```

Three facts that lived in three places are one line. The **name** was a module-level `register_property("icons")` call
in `navigator/__main__.py`, nowhere near the widget that read it, because a function with a side effect can be written
anywhere; `__set_name__` takes it from the attribute instead. The **default** was at the read site,
`style_property("icons", "auto")`, repeated at every read. The **vocabulary** was nowhere at all — implied by whatever
the read site happened to compare against.

That third one was a real hole rather than an untidiness. `Panel.show_icons` tested `!= "none"`, so `icons: mone` parsed
cleanly and *turned icons on* — a typo silently meaning the opposite of what it said, which is precisely what
registering the key was introduced to prevent, caught on one half of the declaration and not the other. A sheet already
refuses an unknown variable, an unreadable colour and a palette index above 255; there was no reason for a widget
property's value to be the one thing it waved through.

**The type is the default's own.** `StyleProperty(0)` takes a number, `StyleProperty(True)` a flag,
`StyleProperty("auto")` a keyword, and `values=` narrows a keyword further. Nothing is separately spelled, which is the
inference navml's `property` directive already makes from its right-hand side, and it generalises the check past
enumerations: `icons: 3` is refused because the default is a keyword. The comparison is `type(value) is kind` rather
than `isinstance`, because `bool` is a subclass of `int` and `margin: true` must not pass for a number.

**The registry holds only what every declaration of a key must agree on** — the type and the vocabulary, not the
default. A subclass may reasonably want a `double` frame where its base wants `single` while both accept the same four
words, and the default never reaches the parser anyway. Two *conflicting* vocabularies for one name raise at import,
because the sheet cannot honour both and the winner would be whichever module imported last.

**The check runs after `parse_value`, not inside it.** That function answers `true`, `false` and a digit string before
it ever reaches its widget-property branch, so a check written there would miss `icons: true`. `check_value()` holds
the value it produced, which covers every form it can produce.

**The cost is import order, and it is worth paying.** A sheet can only be checked against properties that have been
declared, so `navigator/__main__.py` could no longer parse its default sheet at import — `navigator.nss` names `icons`
and `Panel` is defined further down the file. `SCHEME` became `default_scheme()`, parsed on first call and cached. The
failure is loud and names the property, which is the right way round: the alternative is a sheet that silently drops a
declaration because the widget that declares it had not been imported yet.

