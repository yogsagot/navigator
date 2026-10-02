## Inheritance

**Style inherits down the widget tree, and every field inherits.** A widget's cascade starts from its parent's
*resolved* style rather than from nothing, so a widget the sheet says nothing about looks like its container.

### Why all seven fields, with no CSS-style split list

CSS inherits `color` and not `background-color`, and the split is not arbitrary: CSS properties include layout —
inheriting `border` or `margin` would be absurd — and backgrounds do not need to inherit because they are transparent by
default, so an ancestor's shows through.

Neither reason survives the move to a cell buffer. `Style` holds only cell appearance; there is no field for which
inheritance is nonsense. And a cell has exactly one `(char, Style)` pair with no transparency, so "the ancestor's
background shows through" is not something inheritance provides — it is what happens when a widget simply *does not
paint* a cell, which
`render_tree` already gives for free.

That last point is worth being precise about, because it narrows what inheritance is actually for. It is not for the
empty parts of a widget; those already show the parent's paint. It is for the parts a widget *does* paint — a label
drawing text inside a dialog, which must know the dialog's background or it will punch a hole in it.

### Why inherit at all

Without inheritance every such pairing needs a rule that restates the container's colours:
`Dialog Label`, `Dialog Button`, `Dialog CheckBox`, and so on for each widget type that can appear inside each
container. That is tolerable at `navigator/__main__.py`'s scale — its eleven style constants collapse to about five
distinct values — and it does not scale to the TurboVision-like library of windows, buttons, menus and labels the README
plans.

Fidelity points the same way. TurboVision resolves colours *through the ownership chain*: a view's palette indexes into
its owner's palette, and so on up until an index lands on an absolute colour. The mechanism is index remapping rather
than value inheritance, so this is a parallel and not a precedent — but the direction is the same, and colour descending
the tree is what the original does.

### The mechanism already exists

Inheritance is: take the parent's resolved `Style`, overlay this widget's winning declarations. That is exactly
`Style.derive(**declarations)`.

This does **not** contradict "`Style` cannot cascade" above. Those are two different operations. Rule-versus-rule
cascade needs `dict[str, object]` because a `Style` cannot say which of its fields a rule meant. Parent-to-child
inheritance has no such problem: the parent's resolved style is complete, every field carries a real value, so there is
no "unset" to lose. One type, two operations, and `style.py` already has the second one.

`derive` also rejects a property name it does not know — `TypeError: Style.__init__() got an
unexpected keyword argument 'colour'` — so baking the declarations gives the engine a free check on a misspelled
property, at the point where the line number is still available.

### How it composes with the two decisions above

`style` is a computed, `parent` is reactive, so the chain is tracked and memoised per widget:

```python
@computed
def style(self) -> Style:
    base = self.parent.style if self.parent is not None else DEFAULT_STYLE
    sheet = self.stylesheet
    declarations = dict(sheet.declarations_for(self)) if sheet is not None else {}
    declarations.update(declarations_of(self.inline_style))  # level 3, per property
    return base.derive(**declarations)
```

An ancestor's state change lazily restyles everything beneath it — confirmed through two levels of nesting — at a cost
of O (depth) per widget and O (n) for a tree, since each parent's answer is memoised for all its children.

Note that an inline declaration does **not** block inheritance. It overlays the base like any other declaration, so a
widget carrying `"bg: red"` still inherits its parent's foreground and attributes. Only the properties it names stop
descending; a whole-`Style` inline would have cut the chain, which is one more thing the declarations form gets right.

The root inherits from `DEFAULT_STYLE`, not from `Application.background`. The background is reached by walking to
`_application`, which is a plain non-reactive attribute, so a background change would restyle nothing; and the desktop
widget's own rule is the honest place to say what the desktop looks like. `navigator/__main__.py` already carries this
redundancy — `background=DESKTOP` at
`navigator/__main__.py` and `Manager.render` filling with `DESKTOP` at `navigator/__main__.py`.

### A constraint this exposes: the sheet itself has to be reactive

Inheritance propagates because everything it reads is reactive. The stylesheet's *contents* are not, unless they are
made so. A sheet held in a plain dict can be edited, reloaded or swapped for a dark theme and **nothing will restyle** —
every widget's `style` cell is clean, nothing marked it stale, and the values stay memoised until some unrelated write
forces a frame.

This is easy to miss because it fails silently and only for whole-sheet changes; per-widget state changes keep working
perfectly. Whatever holds the parsed sheet has to be a reactive source, so that replacing it invalidates every style
downstream.

