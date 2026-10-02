## Selectors

### `:not()`

Added after the fact. The first grammar had none, and `navml`'s `disabled` flag was named around that absence. The
argument is **one compound, and a plain one**: no combinator, no comma, no `::part`, and no nested `:not`. Excluding
several things is `:not(.a):not(.b)`. That is where CSS 3 drew the line, and it keeps negation a test on one widget:
`:not(A > B)` would have to match a chain it cannot see.

- **Before or after the part.** A `:not` before `::part` is about the widget, so `Panel:not(:active)::row` works. One
  after it is about the part, and may name only classes and states, the only things a part carries:
  `Panel::row:not(:selected)`.
- **Counted as its argument.** A `:not(x)` adds the specificity of `x`, as in CSS. The negation itself is free, and
  `:not(#left)` still outranks any number of classes.
- **A negated state is still a state the sheet names.** `Stylesheet.state_names` includes it, because
  `Widget.part_style` keys its cache on that set, and a state it missed would never invalidate a part.
- **The comma is split at the top level only**, so that `:not(.a, .b)` gets an error that names the fix, rather than
  one about half a selector.

### An id is not a selector

The obvious reading of "\*.css like" is that a stylesheet names widgets the way CSS names elements: `.classname` for a
class and `#id-name` for an id. The class half is right. The id half is not, and cannot be — a navml `id` is unreachable
from here, for two independent reasons, either of which alone settles it:

- **Layering.** The lookup engine is navkit; navkit does not depend on navml, and never will. A navml id is a
  compile-time label that stops existing when the generator finishes, so there is nothing at run time for the engine to
  match even in principle.
- **Uniqueness.** A navml id is unique *within its document* (see `navml/DESIGN.md`, *Ids*). CSS `#` presumes uniqueness
  across everything being styled. Two components each declaring
  `id: cursor` is perfectly legal navml, and both would answer to `#cursor`.

Qt reached the same split from the same starting point, and its answer is the one to copy: a QML `id` is a compile-time
name in the document, `QObject::objectName` is a run-time property, and Qt Style Sheets match `QPushButton#okButton`
against **`objectName`**. navkit and navml stand in the same relation as QtWidgets and QML.

So this is not a limitation to be worked around later by teaching the engine about documents. The id and the selector
name are different things with different scopes, and collapsing them is the mistake rather than the fix.

### What each selector matches

| Selector      | Matches                                                                 | Hook                                                   |
|---------------|-------------------------------------------------------------------------|--------------------------------------------------------|
| `Panel`       | the widget's Python class, subclasses included — walk `type(w).__mro__` | exists                                                 |
| `.selected`   | membership in `Widget.classes`                                          | new: `classes: frozenset[str] = reactive(frozenset())` |
| `:active`     | a reactive boolean attribute of the widget that is currently true       | exists — `Panel.active`, `Widget.visible`              |
| `#left-panel` | `Widget.name`                                                           | new: `name: str = reactive("")`                        |
| `Panel::row`  | a named part the widget paints itself — see *Parts*                     | the widget's own `render()`                            |
| `:not(.wide)` | everything its one-compound argument does not — see *`:not()`*          | none: it is grammar                                    |

Two new attributes on `Widget` for selectors to match against, and no more. Both are reactive, which is what the next
section turns out to depend on. (A third, `inline_style`, arrives from the authoring side — see *Where a widget's style
comes from*. Nothing selects on it.)

- **`classes` is a `frozenset`, not a `set`.** A collection has to be *replaced* to count as changed — the equality
  guard sees the same object through an in-place mutation and propagates nothing. A mutable set would silently fail to
  restyle anything; freezing it makes the only expressible update the correct one.
- **`name` is never derived from a navml `id`.** In markup it is an ordinary property,
  `name: "left-panel"`, bindable like any other and absent unless written. Having the generator quietly emit one from
  the `id` would undo the whole distinction above and drag the document-scoped uniqueness problem into a global
  namespace.
- **`:state` costs no new state at all.** `Panel.active` is already declared and already chooses three of the styles
  `navigator/__main__.py` paints; matching it directly is free. A `classes` set that had to carry `"active"` alongside
  it would be the same fact stored twice, kept in step by an effect that exists only to serve the stylesheet.
- **But `:state` draws its names from the widget's own namespace, so it inherits that namespace's collisions.** `Panel`
  already declares `selected` — a computed returning the
  `DirEntry` under the cursor — so `Panel:selected` would mean "this panel's listing is not empty", not "this panel is
  selected". A `.selected` class tag is a different name in a different space and does not collide. Whether `:state`
  should be restricted to attributes declared `bool`, or match any truthy value, is part of the grammar still to settle.
- **Explicitly not adopted: Qt's `.QPushButton`,** which in QSS means *this exact class, no subclasses*. Here `.` is a
  class tag, as in CSS and in Textual. Spending the same sigil on a type distinction is a wart worth not inheriting.

### Resolution belongs in a computed

Every one of those matches is a reactive read: `name`, `classes`, the state booleans, and
`parent` for any combinator. Resolve a widget's style inside a `computed` and the consequences follow on their own — a
state change invalidates the resolved style, which invalidates the widget, which asks for a repaint, all through
machinery `reactive.py` already has. Nothing new is needed to make a stylesheet react.

It is also safe. A computed is pure and pull-based, so it may be recomputed in the middle of composing a frame; that is
precisely the exemption the frame loop's "nothing reactive runs during the paint" rule leaves open. Resolving
imperatively inside `render()` instead would re-run every selector on every frame and discard the result each time.

### Two things `Style` and `Widget` do not do today

Both surfaced from reading the existing code rather than from the language design, and both change what the engine can
be built on.

**`Style` cannot cascade.** It is `@dataclass(frozen=True, slots=True)` whose only composition is `derive(**changes)`, a
`dataclasses.replace` wrapper. Every field defaults to `None` or
`False`, which is indistinguishable from *not specified* — `Style(bold=False) == Style()` is
`True`. There is no way to express "overlay the fields this rule actually set onto what was inherited", which is the
whole of the cascade.

Leave `Style` alone. Cascade over a `dict[str, object]` of declarations, where a key being absent is what carries
"unset", and bake the winner into `Style(**declarations)` once at the end. That keeps `Style` frozen, slotted and
hashable — `render_diff` compares styles per cell and leans on cheap equality — and keeps `style.py`'s promise that it
is the value type the engine resolves *to*, not a participant in resolving.

**Inline style and resolved style cannot be the same attribute.** `Widget.style` is a reactive source, assigned in
`__init__`. If the engine drives it with `bind()`, then an inline `style:`
written in markup becomes a plain assignment over a live binding — which navkit raises on, deliberately. In CSS an
inline style *wins*; here it would crash instead. So the author's input and the cascade's result need separate
attributes; the next section is which is which.

