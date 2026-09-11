# navkit design notes

Decisions taken ahead of the code that will need them, so the work starts from a spec rather than rediscovering it,
and — increasingly — the account of what building that code settled.
`navkit/` is written, the stylesheet engine included: the sections below were written before
`stylesheet.py` existed and *What the migration settled* and *What building it settled* record what happened when it
did. Anything not written down here is still open, and the *Still open*
section at the end is where the unbuilt parts are named.

## Selectors

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

## Where a widget's style comes from

Four channels feed one widget, and they are one ordering rather than four mechanisms — weakest to strongest:

|   | Channel                                          | Written where                       |
|---|--------------------------------------------------|-------------------------------------|
| 1 | the parent's resolved style, inherited           | nowhere — it is the `derive` base   |
| 2 | matching `.nss` rules, by `(specificity, order)` | a stylesheet                        |
| 3 | `inline_style`, per-widget declarations          | a `.nml` `style` block, **or** code |
| 4 | a `Style` passed straight to a drawing primitive | `render()`                          |

Level 1 needs no rule of its own; it falls out of the parent's style being the `derive` base, so any matching
declaration, however weak, replaces it. CSS behaves the same way — an inherited value loses to any declaration on the
element itself. A universal selector, if the grammar grows one, is `(0, 0, 0)` and loses to everything except
inheritance.

**Level 3 is one slot, not two.** The markup block and a runtime string write the same attribute, exactly as the DOM's
`el.style` is a single declaration set that markup fills in and code merges into. So a widget whose markup set `bg`
keeps it when code later merges `fg`, and a code write that names `bg` replaces what markup said about `bg` and nothing
else.

**Level 4 is outside the cascade by construction**, and needs no design at all: `fill`,
`draw_text` and `draw_box` already take a `Style`. It is how the decisions under *What a stylesheet cannot reach* are
served — a substring span or a per-row model flag has no widget to select — and it stays the bottom escape hatch
precisely because it answers to nothing.

**Changing classes at run time costs nothing.** `classes` is reactive, so `add_class("wide")`
re-runs selector matching through the `style` computed and repaints, with no machinery beyond what levels 1-3 already
need. The same is true of the state selectors: `Panel.active` flipping restyles the panel because `style` read it.

## The grammar

**`.nss`, in classic CSS syntax — braces, semicolons, `/* */` comments, whitespace insensitive.** This is the one place
the project does *not* take Kivy's surface, and the reasons are specific to what a stylesheet is.

```
/* The Navigator default scheme. */

Manager { fg: cyan; bg: black }

Panel {
    fg: light_cyan;
    bg: blue;
}

Panel:active::row:selected {
    fg: black;
    bg: cyan;
}

MenuBar, KeyBar { fg: black; bg: cyan }
```

`.nss` follows `.nml`'s naming and sits beside Qt's `.qss` and Textual's `.tcss` — every CSS-like dialect renames the
extension, because none of them is quite CSS.

### Why the house syntax stops here

The rule `navml` takes from Kivy is about markup: *the file should read like Python*, because markup describes a
**tree**, and indentation carrying block structure is what makes a nested tree legible without punctuation. A stylesheet
has no tree. It is a flat list of rules that are always exactly two levels deep, so the thing indentation is good at
never comes up.

The precedent runs the same way, including where the project already looks. Qt pairs QML's braces with QSS's braces.
Textual — the closest analogue there is, a Python terminal UI framework with a CSS engine — uses literal CSS. And Sass
ran the experiment directly: the original `.sass` was indentation-based, `.scss` added braces four years later, and SCSS
is what essentially everyone writes now. A stylesheet is the one place this idea has been tried at scale, and it lost.

Braces also pay for themselves immediately, because two collisions that an indented grammar has to work around simply do
not arise:

- **The state colon.** `Panel:active::row:selected { … }` is unambiguous. An indented grammar opening blocks with a
  trailing colon gives `Panel:active::row:selected:`, so it would have to drop the colon and rely on column position
  instead — a special rule earning nothing. Parts make this worse, not better: they put a second colon form in the same
  selector.
- **The `#` sigil.** Comments are `/* */`, so `#` is free. That is what lets `#0088ff` be a colour, in the table below,
  with position telling it apart from the `#left-panel` selector exactly as CSS does. An indented grammar wanting
  Python's `#` comments has to split the two by a following-whitespace rule, which is subtle in a way that produces
  baffling errors.

Rules do not nest. CSS gained nesting late and SCSS made it popular, but it complicates specificity for no gain at two
levels deep, and specificity staying simple is what the previous section depends on.

### Values are literals, never expressions

`navml` compiles a property's right-hand side as a Python expression, because it has a widget to evaluate it against. A
stylesheet has no `self`, no tree and nothing to close over, so allowing expressions would buy nothing and cost a great
deal. Every value is a literal from this list:

| Kind             | Spelling                                                  | Becomes                                           |
|------------------|-----------------------------------------------------------|---------------------------------------------------|
| named colour     | `light_cyan` — `style.py`'s sixteen constants, lowercased | the palette index it already names                |
| palette index    | `33` — any integer 0-255                                  | itself                                            |
| true colour      | `#0088ff`, or `rgb(0, 136, 255)`                          | the `(r, g, b)` tuple `Color` already allows      |
| terminal default | `default`                                                 | `None`, which is what `Style` already means by it |
| flag             | `true` / `false`                                          | the bool                                          |
| variable         | `$accent`                                                 | whatever the name resolves to — see *Variables*   |

Every colour form lands on the existing `Color = int | tuple[int, int, int]`; nothing new is needed in `style.py`.
Lowercased constant names keep one source of truth for the palette — a colour named in a sheet is the same colour the
Python constant names.

`#0088ff` is available only because comments are `/* */`, and it is worth having: it is the one colour spelling every
reader already knows. Nothing disambiguates it from a `#left-panel`
selector except position — a value follows `prop:`, a selector precedes `{` — which is exactly how CSS has always
resolved `#id { color: #fff }`.

`default` also settles what was an open question: with inheritance being the rule rather than the exception here, the
keyword actually needed is not CSS's `inherit` but its opposite, and
`Style` already gives it a meaning.

It is valid on `fg` and `bg` only. Those are the two fields whose type includes `None`, and the only two for which "the
terminal's own" differs from "off"; on a flag the way not to inherit is
`false`, which says it already. Allowing it everywhere would put `None` into a field declared
`bool` — harmless today, since `sgr()` only tests truthiness, and wrong in a way that would outlive the reason.

Flags are `true`/`false` rather than Python's `True`/`False`. The value grammar is a stylesheet's, not Python's, and
every other stylesheet language a reader will have met spells them lowercase.

### Variables

`$name: value;` at the top level of a sheet defines one; `$name` stands wherever a value is allowed. A theme is then a
sheet that redefines the names rather than a fork of every rule:

```
/* theme-dark.nss, loaded after the default */
$accent:  light_cyan;
$surface: blue;

/* default.nss */
Panel        { fg: $accent; bg: $surface }
Panel:active { fg: $accent; bold: true }
```

**They are substituted, not looked up.** Parse every loaded sheet, merge the variable tables in load order with later
definitions winning, substitute into the rule values, and cascade over what is left — by which point no variable
survives. The `$` sigil is Sass's, and Sass's `$` is compile-time substitution, so it is the honest one. CSS's
`var(--name)` is a different thing: a runtime lookup against a value that inherits per element.

Two decisions already taken carry this with nothing added. Ordering is the tie-break rule — sheet load order first, last
wins — so a theme sheet needs no new notion of precedence. And propagation is *A constraint this exposes* paying for
itself: substitution happens at sheet load, the parsed sheet is already required to be a reactive source, so replacing
it invalidates every `style` computed downstream and the next frame repaints in the new colours.

Details worth fixing now:

- A variable holds **one value**, from the literal grammar above — not a group of declarations. A named group is
  `@mixin`, a different feature, deliberately out.
- A variable may name another (`$surface: $blue`), resolved after the merge. A cycle is a parse error naming the line.
- **An undefined name is an error**, naming the line. CSS falls back silently, which is a well-known source of invisible
  breakage, and there is nothing here to fall back *to*.
- Variables are global to the loaded sheet set; there is no per-subtree rebinding. That is what classes are for. It is
  also not an additive thing to add later — per-subtree variables resolve per widget rather than at load, so it would
  move *when* values resolve, and the substitution model above would have to go.

### Declaration keys are checked when the sheet is parsed

The keys are exactly `Style`'s fields — `fg`, `bg`, `bold`, `dim`, `italic`, `underline`,
`reverse`. Baking already rejects anything else, since `derive` raises `TypeError` on an unknown keyword, but that
happens when a widget is first painted and says nothing about where it was written. Check the key against
`Style.__dataclass_fields__` at parse time and fail with the `.nss` line, the same way `navml` rejects a bad `id`.

Comma-separated selectors share a block, as in CSS. There is no `@import`: multiple sheets are loaded in order by the
application, which is what the tie-break already relies on.

## Parts: listing rows do **not** become widgets

A `Panel` keeps painting its own rows, and the stylesheet reaches them through a **part** —
`Panel::row`, with states and classes of its own:

```
Panel::row               { fg: white }
Panel::row.directory     { fg: white; bold: true }
Panel:active::row:selected { fg: black; bg: cyan }
```

### Why not row widgets

**Because row widgets would not have finished the job.** The menu hotkey letter (`navigator/__main__.py`) and the key
bar's digit (`navigator/__main__.py`) are substrings inside a single
`draw_text` run; no widget granularity reaches them short of a widget per character run. A mechanism for styling what a
widget paints rather than what it *is* was therefore needed whatever was decided about rows — and once it exists, rows
need nothing further.

The precedent is not an analogy but the same problem, solved twice. Qt's style sheets have sub-controls —
`QComboBox::drop-down`, `QScrollBar::handle` — precisely for a complex widget painted as one unit whose parts need
styling. CSS has pseudo-elements — `::first-line`,
`::selection`, `::marker` — for styling things that are not elements at all. `::` is their spelling and it is the right
one to borrow.

Fidelity agrees, and here it is a direct precedent rather than a parallel: TurboVision's
`TListViewer` draws its own items and picks a palette entry per item according to its state. One view, many items, no
per-item objects. Rows were never objects in the original.

The costs avoided are real. Rows as widgets means a recycled pool sized to the visible count, resynced on every scroll
and resize, each row carrying ten reactive cells — and this project has already declined per-widget overhead once on
benchmark evidence, when per-widget buffers lost to surface views. Mouse hit-testing does not argue back: the row under
a click is
`y - 1 + scroll`.

### How a part resolves

A part is not a widget and has no place in the tree. It inherits from its **owner's resolved style** — `self.style` is
the `derive` base — and then the matching `::part` rules cascade over it exactly as rules cascade for a widget. Owner
state composes with part state, which is what
`Panel:active::row:selected` says and what `navigator/__main__.py`'s real condition
(`index == self.cursor and self.active`) actually needs.

A sub-control counts in the **type** column of the specificity tuple, as CSS counts a pseudo-element.

The widget names its own parts and supplies their state when it paints, since it is the only thing that knows a row is
selected:

```python
style = self.part_style("row", selected=..., classes=("directory",) if entry.is_dir else ())
```

**Caching needs one wrinkle.** A part lookup takes arguments, so it cannot be a plain
`computed`. Make the computed return a *resolver* instead — rebuilt whenever the sheet or the widget's own style
changes, memoising combinations internally. Measured at 120 rows against 50 rules, naive rescanning costs 0.35 ms per
frame and the memoised resolver 0.019 ms. Against a frame budget neither is a problem, so this is an optimisation to
reach for rather than a condition of the design working.

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

## Reaching the application

**Done, ahead of the engine, because it was a latent bug on its own.** `Widget._application` is now `reactive`, and
`Widget.application` is a `computed` rather than a property that walks.

The hazard it removes: `_application` was a plain attribute assigned by `Application.root`'s setter, so a value derived
before that assignment memoised the answer it got when there was no application and never recovered — only an unrelated
reactive write dislodged it. Since a widget reaches the stylesheet *through* the application, every style pulled before
attachment would have resolved against no sheet and stayed that way. Normal startup paints after attachment, so the bug
would have hidden until a test or an early access found it.

Two things fell out that are worth knowing:

- **It made the hot path faster, not slower.** `invalidate()` asks for `application` on every reactive change. Making
  `_application` reactive but keeping the walk costs 2464 ns per lookup at depth six, against 1347 ns for the plain walk
  it replaces — nearly twice as slow. Memoising it as a computed costs 290 ns, because a clean cell skips the walk
  entirely. The correct fix is the fast one, which is not the usual way round.
- **Attaching a tree now asks for a repaint.** Assigning `_application` reaches
  `_reactive_changed` like any other observable write, where before it was silent. That is right — a tree that has just
  joined an application needs painting — but it is a behaviour change, not just an optimisation.

Reparenting still invalidates the memo, because the walk reads `parent`, which was already observable for exactly this
class of reason.

## What a stylesheet still cannot reach

Nothing, of what `navigator/__main__.py` does today. All thirteen decisions are expressible: colour and attributes
through `Style`, spans and sub-elements through parts, and the border character set through a widget property.

The shape that is left is clean and worth stating as the boundary it is. A stylesheet reaches whatever a widget
declares — its parts and its properties — plus whatever a cell can look like. Anything outside both is the `render()`
escape hatch, level 4 above, which answers to nothing precisely so that there is always somewhere to go.

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

A third is a mechanism the design had listed as merely possible: a widget may carry its own sheet in `_stylesheet`, the
nearest winning. `Manager` uses it, which is what lets the desktop be styled with no application around it — and lets a
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

## Terminal capabilities: the palette stays exact, the edge quantises

`TerminalInfo` in `capabilities.py` holds what the terminal supports and makes the decisions that follow. The question
that forced it was whether the generated `.nss` themes should carry
`#rrggbb` at all: eight of DOS Navigator's eleven palettes reprogram the sixteen VGA colour registers, and truecolor is
near-universal but not universal.

**The decision is made once, at the edge.** A widget asks for the colour it wants, a sheet records the colour the
original asked for, and only `render_diff` — the last place a `Style`
exists before it becomes bytes — asks whether this terminal can express it. Nothing upstream of that has to know or
care.

**So the palette stays exact.** Baking a sixteen-colour approximation into the sheet at generation time would throw the
original away permanently, and on a terminal that can show it, for nothing. It would also be wrong rather than merely
lossy: `BW.PAL` is a greyscale ramp whose *blue* register holds a mid grey, so writing the DOS colour name `blue` into
the sheet would come back a real blue everywhere. Quantising at the edge gives a grey on a sixteen-colour terminal and
the exact grey on a capable one.

**An index is left alone unless a palette says what it means.** With `TerminalInfo.palette`
unset — the kit's default, since navkit knows nothing about DOS — `blue` in a sheet reaches the terminal as index 4 and
the user's own theme decides what blue looks like; approximating it against our reference table would replace their
theme with ours. A truecolor triple has no such claim on anything and is quantised, against the fixed part of the xterm
palette: indices 0–15 are skipped when targeting 256 colours for the same reason, since what a terminal paints for those
is not knowable from here.

### What an index in a *transcribed* sheet actually means

That rule alone makes Navigator unreadable in a terminal whose sixteen colours are not a VGA adapter's — a light IDE
scheme paints `blue` pale and `light_gray` near-white, and the app is white-on-white. It is not a quantising bug:
`norton.nss` says `blue` because `NORTON.PAL` left the colour registers *alone*, which is a statement about the IBM DAC
and not an invitation for the terminal to choose. The palette stays exact; what was missing was somewhere to say what an
index is exact *about*.

**So `TerminalInfo.palette` names the sixteen, and resolution happens at the same edge.** An index is resolved through
it before the depth checks, and from there it is an ordinary triple.
`VGA_PALETTE` is the reference table the quantiser already carried, under the name that says what it is: the same
colours `tools/palconv.py` holds as six-bit DAC values.

**Pinning is free on a terminal that could not have shown the difference.** Resolving an index through `VGA_PALETTE` and
quantising the result searches the very table it came from, so
`_nearest` returns the index it started with — byte-identical output on a sixteen-colour terminal, and the eight-colour
fold lands in the same place too. Only a terminal that *can* do better is asked for anything different, which is what
makes it safe as an application default rather than a flag nobody finds.

**The kit's default is `None`; the application's is the VGA DAC.** navkit is a terminal library and has no business
asserting what `blue` is. `navigator` is a recreation of a program that drove a VGA adapter, so it pins by default and
`--palette terminal` hands the question back.
`NAVKIT_PALETTE` overrides the application's default the way `NAVKIT_COLORS` overrides the detected depth, and an
explicit flag outranks the variable in turn.

**A sixteen-colour terminal is reachable only by rewriting its registers**, which is what
`--reprogram-palette` does: OSC 4 for the sixteen on `start()`, OSC 104 on `stop()`. It stays opt-in because it repaints
colours outside this application's cells for as long as it runs, and a process killed outright leaves them changed. On a
terminal that can name more, pinning has already done the job and reprogramming changes nothing visible.

**Detection is conservative and overridable.** A terminal that does not say it supports more gets sixteen colours,
because being downgraded on a capable terminal is a disappointment while being upgraded on an incapable one is a
screenful of unreadable escapes — and `COLORTERM` is the only reliable statement of truecolor support. `NAVKIT_COLORS`
overrides the guess outright, and outranks `NO_COLOR`, which in turn outranks any claim of support.

**The answer is fixed for the terminal's life**, detected in `Terminal.__init__` rather than on use. A frame that
quantised differently from the one before it would show up as the diff repainting cells whose content never changed.

A capability is separate from a preference, and either vetoes: `Terminal(mouse=False)` says the caller does not want
mouse input, `info.mouse` says asking would be no use. `stop()` cancels exactly what `start()` asked for, so a feature
never turned on is never turned off either.

## Terminal capabilities: characters, and why a font cannot be detected

Colour asks how many colours a terminal can name. The other half of the same question is which *characters* arrive as
shapes rather than as replacement boxes, and it is answered the same way: once, at the edge, by
`TerminalInfo.glyphs`. Three tiers, ordered and compared with `>=` exactly as the colour depths are —
`GLYPHS_ASCII`, `GLYPHS_UNICODE`, `GLYPHS_NERD`.

### The detection is honest about what it cannot know

**No escape sequence reports the font a terminal is using.** The usual proposal is to print a glyph, ask for the cursor
column with `CSI 6n` and infer from how far it moved. That measures the terminal's own width table and *not* whether
the font has an outline for the codepoint, so on precisely the terminals where the answer is unknown it reports the
same column either way. It would also be the first query round-trip in the codebase, and would have to run before raw
mode. It was rejected on the first ground alone; the second only makes it worse.

What can be known is which *emulators ship a Nerd Font fallback of their own* — kitty, WezTerm and Ghostty each bundle
`Symbols Nerd Font Mono` and map the icon ranges onto it, so the glyphs render whatever font the user configured. That
is a fact about the emulator rather than a guess about the font, which is what makes it safe to act on. Everything else
has to say so itself, through `NERD_FONT` or `NAVKIT_GLYPHS`.

The guess is conservative in the same direction the colour guess is, and for a sharper reason: a colour guessed too high
is a slightly wrong shade, but a glyph guessed too high is a replacement box on every line of every frame. So a
non-UTF-8 locale gets ASCII rather than the benefit of the doubt, and a multiplexer — where `TERM` becomes
`screen-256color` and the marker variables are not forwarded — reports Unicode and is documented as needing the override
rather than being guessed at.

### The vocabulary lives apart from both the buffer and the capability

`navkit/glyphs.py` holds the box character sets and the tiers, and imports nothing. That placement is what keeps two
existing rules intact at once: `screen.py` still has no runtime import of `capabilities.py`, because `draw_box` takes
the **six characters themselves** rather than a name for them and so never learns that tiers exist; and
`capabilities.py` still describes the terminal rather than the drawing.

This answers the two questions the *Still open* section carried. `draw_box`'s `double=` keyword **did** become a
charset argument, and the `border` vocabulary is `single`, `double`, `round`, `ascii`. Resolution happens in the widget
— `Widget.box_charset()` — because that is the one place both halves are in hand: the sheet says which set is *wanted*
and the tier says which can be *shown*, and either vetoes, the same shape as `Terminal(mouse=False)` against
`info.mouse`.

Note what the tier does **not** do: no tier above `GLYPHS_UNICODE` changes a box frame, because box drawing is ordinary
Unicode and a Nerd Font adds nothing to it. The tier matters at the lower boundary, where every set collapses to
`+-|`. Icons are where the top tier earns its place, and icons are an application's vocabulary rather than the kit's.

`Widget.glyphs` is a plain property and not a `computed`. The tier is settled when the terminal is detected and never
changes, so there is nothing for a dependency to invalidate; a detached widget assumes Unicode, which is what the kit
assumes whenever it has no terminal to ask.

### Icons in the file manager are a departure, and a deliberate one

DOS Navigator had no icons and could not have had them — CP437 has no such glyphs, and the original distinguished a
directory by colour and by the word `DIR` in the size column, which Navigator still does. Showing a Nerd Font icon
beside each name therefore cuts against the project's standing rule of preferring the original's behaviour to a modern
alternative. It was taken anyway, on the grounds that a terminal shipping the font makes it free, and it is reversible
in two ways rather than one: `icons: none` in a sheet, or `--glyphs unicode` on the command line.

The gutter is **two cells, not one**. A Nerd Font *Mono* build patches its icons to a single cell and `char_width`
agrees with it, the Private Use Area measuring as ambiguous — but the plain build draws some of them two cells wide and
no table records which of the two is installed. Spending the second cell on a space means a glyph that comes out
double-width covers the space instead of shoving the name along.

## The console: the screen is owned, never read back

Ctrl+O in DOS Navigator hid the panels and showed the last program's output *as the desktop background*, with the menu
bar and key bar still painted over it. Reproducing that is the question that produced `console.py`, `process.py` and
`Surface.blit`, and the answer turned out to be about where the cells live rather than about how to fetch them.

**DN had no special capability; it had a special position.** DOS had one screen — the video RAM at `B800:0000` — and
every program shared it. The previous program's cells were still sitting there, so DN read them. Nothing about that is
portable to a terminal, where the grid lives in another process and the protocol has no request that returns it.

**Every read-back route was surveyed and rejected**, so that it is not surveyed again:

- **DECRQCRA** (`CSI Pi;Pg;Pt;Pl;Pb;Pr * y`) returns a *checksum* of a rectangle, not its text. It is xterm's, gated
  behind `allowWindowOps` — off by default — and absent from VTE, Terminal.app and most others. Recovering characters
  would mean one synchronous round trip per cell, on one terminal, with a non-default setting.
- `CSI 18 t` and `CSI 21 t` report window size and title; `CSI 6 n` reports where the cursor is, not what is under it.
  Nothing in the protocol reports content.
- `/dev/vcsa<N>` on a Linux virtual console *is* the exact analogue — four header bytes, then one character byte and one
  attribute byte per cell, the layout DN read. It works only on a real VT, never inside a terminal emulator or over ssh,
  and needs group `tty`. It survives as one branch of `seed_from_host`, which is the honest scope for it.
- `tmux capture-pane -p -e`, `screen -X hardcopy -h` and `kitty @ get-text` return real text with attributes, but each
  only inside its own host and each needs opt-in. Also
  `seed_from_host` branches.

**Midnight Commander is the control experiment.** It owns a pty for its subshell and still cannot do this, because it
pipes the child's output straight through to the real terminal and so never holds the cells either. All it can do is
flip the alternate screen and let the terminal show what it kept — which is why its Ctrl+O cannot composite a key bar
over the output. Its own manual page is candid that the feature needs "the subshell or a terminal that can save the
output".

**So the output is received rather than fetched.** A child runs on a pty this application owns, its bytes go through an
emulator into a grid, and Ctrl+O becomes an ordinary compositing question the render tree already answers:
`console.visible` and the two panels' bind to one reactive flag, the bars are simply left alone, and no layout pass
runs. The buffer is load-bearing well past one key — a command line, a Terminal window and F3/F4 all want it.

### Why pyte rather than a parser of our own

`InputParser` was written by hand because decoding *input* is a few hundred lines and there is no library shaped like
navkit's events. Decoding *output* is a different size of problem — cursor motion, scroll regions, insert/delete,
character sets, an alternate buffer — and pyte already does it, tested, in pure Python. It is the one run-time
dependency, and it brings only
`wcwidth`.

Three things made the adapter thin enough to be worth it, and are worth recording because they are what a replacement
would have to match:

- **The wide-character representation is already identical.** pyte writes the character, then
  `data=""` into the cell after it; navkit's `set_cell` writes `("", style)`. The two grids can be copied into each
  other without reconciliation.
- **`Screen.buffer` is a `StaticDefaultDict`, which does not materialise on a miss.** Reading every cell of a screen
  allocates nothing, so the conversion can be a plain loop.
- **`Screen.dirty` is a set of changed line numbers** — the same row-granular idea `render_diff`
  uses to skip untouched rows.

**The colour names are the one real seam**, and it is where the palette work above is cashed in. pyte stores `fg`/`bg`
as names (`"brown"` for 33, `"brightbrown"` for 93) or six-digit hex. The names map onto navkit's *indices*, not its
constant names, because an index is what a pinned palette resolves — so a child's `ESC [ 33 m` comes out in the DOS
Navigator brown the theme asked for. Two details are easy to get wrong and are pinned by tests:

- The first sixteen entries of pyte's 256-colour table are mapped **back** to their indices. Without that,
  `ESC [ 38;5;4 m` would arrive as an `(r, g, b)` triple and step around the pinned palette, so the same blue would
  paint two different colours depending on which escape asked for it.
- pyte 0.8.2 misspells bright magenta as `"bfightmagenta"` in `BG_AIXTERM`. The typo is carried in the table, so
  `ESC [ 105 m` keeps its colour; the correct spelling is there too, so a fixed release costs nothing.

**The style cache is keyed on appearance, not on the cell.** A `Char` carries its character, so memoising the whole of
it keys the table by `(character, appearance)` and misses on every new letter. Thousands of cells share a handful of
appearances, and that ratio is the entire point of the cache.

### The mirror, and why the conversion and the paint are split

pyte's grid is a sparse mapping and navkit's is a list of rows, so something has to convert. Doing it in `render()`
would cost a lookup per cell per frame; doing it on every feed would cost a full screen per byte. `ConsoleScreen` keeps
a real `ScreenBuffer` beside pyte's and converts only the rows pyte reports dirty, clearing the mark afterwards as pyte
documents. Painting is then one `blit`, which `_View` forwards whole so it reaches `ScreenBuffer`'s row-slice copy
rather than a Python call per cell.

**`blit` blanks a double-width character cut in half at either edge** — a stub whose owner was clipped off the left, and
a wide character whose trailing half was clipped off the right. That is the same bargain `set_cell` already makes at the
edge of the screen, and it is why the fast path can be a slice with two fixups rather than a loop with a state machine.

### What owning the pty costs

A child only ever talks to what the emulator implements, and pyte does not implement `?1049` — a program that switches
to its own alternate screen draws over the same buffer. For the line-oriented output a file manager runs, that is
everything; for a full-screen program it is wrong, and `run_on_terminal` is the escape hatch that hands over the real
terminal and accepts that the output then cannot be captured. The two are genuinely exclusive: either the pty is owned
and the emulation has to be good enough, or the child gets the terminal and the cells are gone. There is no third
option, which is the whole finding above.

**`set_winsize` on the master is the whole of resize handling.** The kernel carries the size to the slave and raises
`SIGWINCH` on the foreground process group itself, so nothing signals the child by hand. **EOF on the master is the
child's exit**: a pty reports `EIO` rather than an empty read once the last process holding the slave is gone, which is
where the reader is detached and the child reaped.

## Declared types: a write is checked, a computed value is not

Every reactive attribute in the repository is already annotated — `width: int = reactive(0)`,
`parent: Widget | None = reactive(None)` — and until now the annotation was addressed to the type checker alone. It is
the only statement of intent an attribute carries, so `Reactive.__set__` reads it and refuses a write that contradicts
it with `ReactiveTypeError`. Nothing had to be spelled twice for this: the declarations were not touched.

**The check guards the boundary where a value enters the graph, and nothing else.** A plain assignment is that
boundary — it is where a value arrives from outside, from an event handler, a parsed file, a test. A value a *bound
expression* computed is not checked, and neither is a `computed`'s return, because both were derived from values that
were already checked at their own boundaries. The alternative was checking inside `_Cell._recompute`, which is
consistent in a different way and was rejected on two counts: the cell has no declaration to consult, so every cell
would have to carry the erased check; and a recompute happens lazily on read, so the refusal would arrive during a
paint, at a read far from the assignment that caused it, cached the way `_recompute` caches every other failure. A
write is the rare operation and the one with a caller to blame. Recomputes are the hot path and have none.

**Resolution is lazy, and one annotation at a time.** `typing.get_type_hints()` is all-or-nothing, and this repository
already contains the case that breaks it: `Widget._application` is annotated `Application | None`, with `Application`
imported only under `TYPE_CHECKING` to break an import cycle. One name it cannot see would take *every other
annotation on the class* down with it, so a single unresolvable import would quietly disarm the check for the whole
widget tree. `_resolve_annotation` therefore evaluates one string and answers `UNKNOWN` if it cannot, leaving that
attribute unchecked and its eleven neighbours checked. Laziness is forced by a second case: `__set_name__` runs while
the class body is still executing, and `parent: Widget | None` cannot be evaluated there, because `Widget` is precisely
what is being defined. Both the type and its erased form are worked out on first ask and kept on the declaration, which
is shared by every instance — resolving costs some hundred times what checking against the result does.

**`UNKNOWN` is not `Any`.** `Any` is an answer: the author said this attribute takes anything. `UNKNOWN` is the absence
of one — no annotation, or one naming something that does not exist at run time. Both go unchecked, so the distinction
buys nothing today; it is kept because a consumer that wants to *report* on a class's reactive surface, which is
exactly what the navml generator will do, needs to tell "unconstrained" from "unknown" and could not recover it later.

**The erasure is shallow, on purpose.** `frozenset[str]` checks the container and not the elements, because checking
them means walking every collection on every write — and `classes` is a `frozenset` that is replaced whenever a state
changes. A union is flattened to the tuple `isinstance` takes rather than handed over whole, which works for `X | Y`
but not for `Optional[X]` or a union with a parameterised arm. A form too clever to erase — `Literal`, or an arm that
is itself unerasable — disarms the *whole* union rather than half-checking it, since a partial check would refuse
values the annotation allows.

**There is no flag to turn it off.** Opting out is the same act as never opting in: leave the annotation off, or write
`Any`. A per-attribute switch would be a second way to say what the annotation already says.

**The declared default is not checked.** `n: int = reactive("zero")` is accepted. The default sits three characters
from the annotation that contradicts it, where a type checker catches it for free and a reader catches it faster; the
run-time check exists for values arriving later, from somewhere else. Checking it would also mean running every
`factory=` at declaration time or per instance, for a class of mistake that never survives its first reading.

**A bound attribute reports being bound, not being mistyped.** Assigning a wrong-typed value over a live binding raises
the existing "call `unbind()` first", because correcting the type would not make that assignment legal either — the
guard that refuses every value alike is the one with something useful to say. So `__set__` consults the cell before it
consults the annotation, which is the only reason the two lines are in that order.

## Still open

- What `Application.background` becomes. It clears the buffer each frame and already duplicates what `Manager.render`
  paints; once the desktop widget paints its resolved style, one of the two is redundant.
- Which parts and properties the eventual *library* widgets declare. `navigator/__main__.py` has settled its own —
  `Panel` paints `row`, `title`, `footer` and `error` and reads `border` and `icons` properties,
  `MenuBar` paints `hotkey`, `KeyBar` paints `number` — but a widget's parts are its public styling surface, and they
  are what the parser checks an unknown key against, so the library's belong with the library.
- What a full-screen child does. `run_on_terminal` hands over the real terminal and loses the output, which is the one
  thing the console exists to keep. The alternative is teaching the console an alternate buffer of its own — pyte stores
  `?1049` without obeying it — and that is worth doing only once something actually launches an editor.
- Where the console's key routing belongs. `Navigator.on_key` currently decides what the child gets and what Navigator
  keeps, which is the application's business only for as long as there is one console; a focus notion in `Widget` is the
  eventual home — the first item of the section below.
- Which glyphs beyond a box frame the *library* widgets need — a scrollbar thumb, a menu's submenu arrow, a checkbox.
  `navkit/glyphs.py` holds box character sets and nothing else, because those are all anything draws today. Each new one
  needs the same three answers the box sets have: an ASCII form, a Unicode form, and whether a Nerd Font improves on it.

### What the widget library needs first

The markup language does not need any of these — a `.nml` that declares a tree, binds geometry and carries a `style`
block compiles onto what is already here, and `Manager._place()` is the proof. A **widget library** does, because a
button, a dialog and a pull-down menu are all made of them. Listed in the order they block each other, which is also the
order to build them:

1. **Focus.** There is none. `dispatch_key` offers a key to *every* visible descendant, deepest and last-added first,
   until one returns True — a positional lottery that works only because nothing yet competes for a key. The application
   sidesteps it entirely: `Navigator.on_key` is one central `if/elif` chain over a hand-rolled `Panel.active` bool, and
   `Manager.active_panel`
   is what a focused widget would otherwise be. Everything below depends on this one.
2. **Signals.** A widget cannot announce anything. `Application.post_event` accepts any `Event`, but `_handle`
   dispatches only the four types it knows, so a user-defined event is queued and dropped; `ResizeEvent` and
   `PasteEvent` never reach a widget at all. Reactive attributes plus
   `effect()` are the current substitute and are the right one for *state* — a signal is for the thing that has no
   state, "this button was pressed". `navml/DESIGN.md` lists the markup half of this as open, and the two have to be
   settled together.
3. **Mount and unmount.** `add()` appends and invalidates but never calls `layout()` on the new child, so a widget added
   while the application is running is 0x0 until the next resize unless every one of its sizes is bound — a dialog
   opened at run time silently paints nothing.
   `remove()` sets `parent = None` and stops; `Effect.dispose()` exists and nothing calls it, and a binding written as
   `w.parent.width` then raises on a detached widget and *caches* the failure. Effects are held by weak reference, so
   this is a correctness question rather than a leak.
4. **Modal and overlay.** Z-order is child-list order — paint forwards, hit-test backwards — which is enough to put a
   dialog on top and no help at all in stopping the widgets underneath from also handling the keystroke. Exclusive input
   is what "modal" means, and it needs (1) first. The application's `visible`-binding trick, where the console and the
   panels take turns, is the whole-screen special case of this and does not generalise to a centred dialog.

A fifth, smaller: **the cursor is unconditionally hidden** (`Terminal.start` emits `HIDE_CURSOR`
and `render_diff` never places one), so a text input has no caret except a reversed cell — which is what
`Console.render` already does by hand.
