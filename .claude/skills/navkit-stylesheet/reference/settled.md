## What the migration settled

`navigator/__main__.py` now paints from `self.style` and `part_style()`, and its eleven module constants are gone. The
frames are **byte-identical** — 18 variants across three terminal sizes, both panels active in turn and three cursor
positions, 54,696 bytes of terminal output, matching hash before and after.

Two things that only showed up once a real screen was expressed:

- **Most of a scheme is what you do not write.** Ten rules replaced eleven constants and thirteen branch decisions,
  because a part with no rule of its own inherits its widget. The panel title when inactive, the footer, the error line
  and an ordinary row all needed nothing at all — the four constants they used were duplicates of `PANEL` by value,
  which the inheritance rule expresses as absence.
- **A per-property cascade differs from picking a winning rule, and a real scheme finds it.**
  `Panel::row.directory` and `Panel::row:selected` tie on specificity, so source order settles the colours — but `bold`
  came from the directory rule and *survived* into the selected row, because the selected rule never mentioned it. The
  old code, choosing one whole `Style`, could not have that bug. The scheme says `bold: false` explicitly, and the
  comment there says why.

A third is a mechanism the design had listed as merely possible: a widget may carry its own sheet in `stylesheet`,
the nearest winning. It was `_stylesheet` until markup needed to say it — a private name is one a document cannot
write without reaching into something, and this attribute was always meant to be set from outside. Making it public
is the whole of what markup needed; there is no spelling of its own (`navml/DESIGN.md`, *How a value gets in*).

**The name it took was already spoken for, and the swap is the right way round.** `Application.stylesheet` is a
settable reactive holding the sheet the *application* brings, so a `Widget.stylesheet` holding the sheet a *widget*
brings is the same idea one layer down; the odd name out was the walk-up, which is the only thing in the codebase
that meant *resolved*. It is `effective_stylesheet` now. The pair says which is which: **`stylesheet` is what an
object brings and is assigned, `effective_stylesheet` is what a widget resolves against and is derived.** Most
widgets bring none and resolve against one. `Manager` uses it, which is what lets the desktop be styled with no application around it — and lets a
test hold a single `Panel` and paint it.

## What building it settled

Three things the design could not have known, found by writing `navkit/stylesheet.py` and
`tests/test_stylesheet.py`. Each is pinned by a test.

**A type selector matches by class name**, walking `type(w).__mro__` and comparing `__name__`, as CSS, Qt and Textual
all do. Two unrelated classes sharing a name therefore both match, which is the accepted cost of a sheet being able to
name a type it cannot import.

**A state matches any truthy attribute — but only a *reactive* one restyles.** Matching is
`getattr(widget, state, False)`, so `Panel:error` works on a `str | None`. The catch is that a plain attribute is read
outside the dependency graph: it matches correctly the first time and then never invalidates the memoised answer. A
widget meaning a state to be stylable has to declare it reactive, and
`test_a_state_on_a_plain_attribute_matches_but_does_not_restyle` pins the behaviour rather than endorsing it.

**Caching part styles needs the widget's live states in the *key*, not as a dependency.** The resolver is derived from
the sheet and the widget's own style, which is not enough on its own:
a state naming only a part — `Panel:active::row` with no widget-level `Panel:active` rule — never alters the widget's
own style, so nothing marks the resolver stale when it flips. Putting the live states into the cache key means a stale
entry cannot be returned in the first place.
`Stylesheet.state_names` exists to make that cheap, being bounded by the sheet.

A fourth was a plain bug, worth recording only because the shape invites it: a combinator read from the source sits
*before* the compound that follows it, while matching walks outwards from the subject and needs to know how each
ancestor relates to what came *after* it. Storing it the natural way round silently turns every `>` into a descendant
match, and every selector still appears to work.

