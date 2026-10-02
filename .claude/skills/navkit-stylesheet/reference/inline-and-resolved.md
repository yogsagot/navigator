## The inline / resolved split

**`style` is the resolved value and a `computed`. `inline_style` is what the author wrote, a reactive source.** Every
`render()` reads `self.style` and gets the cascaded answer.

### Why the resolved value gets the short name

This is the reverse of the DOM, where `element.style` is the *inline* declaration and the cascaded answer needs
`getComputedStyle(element)`. The departure is deliberate, and it follows from who reads what. In the DOM, scripts write
inline styles constantly and read computed ones rarely, so the short name goes to the thing that is written. Here it is
the other way round: a style is read at every paint by every widget, and written at a handful of authoring sites. The
name reached for most often should be the one that is right.

The failure modes settle it even if the frequency argument does not. With `style` resolved, someone who writes
`widget.style = PANEL` out of habit gets an immediate `AttributeError` from
`Computed.__set__`, whose message already says what to do instead — assign what it derives from. With `style` inline,
someone who writes `surface.fill(..., self.style)` in a render method silently paints the *un-cascaded* value, which for
most widgets is nothing at all. One mistake is loud and self-correcting, the other is silent and looks like a stylesheet
bug.

### Why a computed rather than a bound source

The engine could equally install `widget.style = bind(lambda w: sheet.resolve(w))` on a reactive source, and assigning
over that also raises. But it only raises *while a binding happens to be installed*: a widget built outside any
stylesheet'd tree would quietly accept
`widget.style = X`, so the guarantee would hold in most places and not all. A computed refuses unconditionally. It is
also the type-correct choice in this layer's own vocabulary — a source is written, a computed is derived, an effect is
impure, and a resolved style is derived.

Per-instance flexibility does not argue the other way, because the computed can consult whichever stylesheet governs the
widget:

```python
@computed
def style(self) -> Style:
    if self.inline_style is not None:
        return self.inline_style
    sheet = self.stylesheet  # walks parents, which are reactive
    return sheet.resolve(self) if sheet is not None else DEFAULT_STYLE
```

A subtree can carry its own sheet, and a widget opts out entirely through `inline_style`.

### Why laziness is safe here, and the one thing that would break it

A computed does not recompute when its inputs change; it is marked stale and waits to be read. Nothing pushes a repaint
on its behalf either — `_Cell.notify()` calls `_reactive_changed` only on the cell that was *written*, so a widget whose
style went stale because of an ancestor's write never hears about it.

It works anyway because damage tracking is a single global flag. `Widget.invalidate()` sets
`Application._dirty`, the frame re-renders the whole tree, and every widget pulls its own style on the way past — by
which time the stale cell recomputes. `widget.py`'s `_reactive_changed`
docstring already states this ("the application tracks dirtiness with a single flag ... per-widget damage tracking would
have to look at the derived values as well").

        **The application is an owner too, and was once forgotten as one.** `Application.focused` and
`Application.stylesheet` are reactive, and a write to either only marks widgets stale — so until `Application` grew
its own `_reactive_changed`, a key that moved the focus and did nothing else (Tab between the two panels) painted no
frame, and the switch appeared with the next unrelated key. Any object carrying a reactive the screen depends on needs
the hook, and a test for one counts frames rather than reading state, because the state was right all along.

The stylesheet sharpens that constraint rather than merely relying on it. With descendant combinators a widget's style
depends on its *ancestors'* state, so per-widget damage tracking would have to follow the reactive graph out of the
widget entirely. Anyone adding it has to deal with this; the global flag is load-bearing, not a placeholder.

### Inline is partial, and cascades per property

`inline_style` is `str | Mapping | None`, and `None` means nothing was authored. It is a set of declarations, not a
`Style`, so it overlays the cascade's answer property by property — `"bg:
red"` changes the background and leaves everything the sheet decided alone.

It could not have been a `Style`. A `Style` cannot say which of its fields were meant, so folding `Style(fg=RED)` in as
a high-specificity participant would carry `bold=False` and
`bg=None` with it and silently undo the sheet. What was missing was a partial-declaration type to author with — and a
declarations string is exactly that, in the value grammar the stylesheet already defines. The authoring channel supplies
the type the cascade needed.

Two stored forms, for a reason:

- **A string is stored verbatim**, and the `style` computed parses it against the live variable table. That is what lets
  `"bg: $surface"` work inline and survive a theme swap: the parse happens *inside* the computed, which reads the table,
  so replacing the sheet invalidates it.
- **A mapping** is what `merge_style()` stores, because merging two strings by concatenating them would grow without
  bound.

Reading `inline_style` back gives whichever was last stored. The resolved answer is always
`style`.

Both collections a widget can carry need a helper, for the same reason: the reactive layer counts a change only when the
collection is *replaced*, never mutated in place.

- `merge_style(text_or_mapping)` — parse, overlay onto the current declarations, replace.
- `add_class(*names)` / `remove_class(*names)` — replace the frozenset.

One cost is accepted rather than solved: a malformed inline string fails when the widget is first painted, and a lazy
failure is cached. The mitigation is the one `navml/DESIGN.md`
already prescribes for property expressions — carry the source text into the error. The markup channel avoids it
outright, because the generator can check the block before anything runs.

### What this costs to adopt

Small, and much smaller now than later — `style` is written at six places in the repo and read at one:

- `Widget.__init__` takes `inline_style: str | Mapping | None = None` and assigns it. The
  `style=` keyword goes away, so the four `navigator/__main__.py` call sites (`navigator/__main__.py`) become
  `inline_style=`, and a stale `style=` raises on the unknown keyword rather than being quietly accepted.
- `tests/conftest.py:80`'s `RecordingWidget` keeps reading `self.style` and is then reading the resolved value, which is
  what it wants. `tests/test_widget.py:135,148` move to the new keyword.
- In markup the property is `inline_style:`. Writing `style:` needs no special case in the generator: navml already
  rejects a `computed` target at generation time, with the line number, which is exactly the right error.

