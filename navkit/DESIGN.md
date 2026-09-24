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

### A declaration is an extension point

`_Declaration` is the base of `Reactive` and `Computed`, and `declarations(cls)` is what a code generator asks for a
class's reactive surface. navml needs to subclass the first so that its own descriptors are answered for by the second
— an `alias`, which redirects a name on a component to an attribute of a widget declared inside it, is a declaration
whose `cell()` returns a cell it does not own (`navml/DESIGN.md`, *Aliases*). That makes the base a documented shape
rather than an implementation detail, and three things follow.

**It should have a public name. Now done:** `Declaration`, exported from `navkit`, with `_Declaration` kept as an
alias because navml's prototype already imports the private spelling and a dependency that is going to exist should be
spelled honestly. The layering is unchanged:
navkit still knows nothing of navml, and navml subclasses downward, which is the direction that was always allowed.

**`cell()` is the overridable part, and the only one.** Everything that walks a declaration — `unbind()`, `is_bound()`,
`peek()`, the identity check that the class really declares the attribute — goes through it or through ordinary
attribute access, so a subclass answering with another object's cell is answered correctly everywhere without navkit
learning why. `_resolve_annotation`'s caching is the constraint on such a subclass rather than on navkit: the type is
worked out once and kept on the declaration that every instance shares, so a subclass must not derive it per instance.

**A `Binding` can be copied with its owner fixed, and that method is navkit's to give.** `bind()`'s convention is
that an expression's one argument is the object that *owns* the attribute, and there is exactly one place where the
owner and the object the expression was written against differ: a declaration that forwards to another widget's
attribute. The expression would be handed the target, which usually has an attribute of that name too — so nothing
raises, a wrong number is computed, and it goes on being computed. `Binding.owned_by(owner)` returns a copy whose
expression is always called with `owner`, carrying `equal` across because the copy replaces the original at the cell.

It lives here rather than in navml for two reasons. It bends navkit's own convention, so navkit should be the one to
say how; and it composes — the wrapper ignores its own argument, so a forward into something that forwards further
re-wraps an expression that is already owned and the *outermost* owner wins, which is the answer a reader of the outer
document expects. The expression has to be lifted into a local before the lambda closes over it: closing over the
`Binding` while the caller rebinds the name on the same line gives a wrapper that finds itself at call time and
recurses.

**`unbind()` and `is_bound()` refuse a `Computed`, and now say so.** Found while working the above out, and a bug
here rather than anything markup caused: `_declaration()` checks only that its argument is a declaration, and
`Computed` is one, so `is_bound()` answered `True` for every computed — a cell carrying a `compute` is what being
bound means to it — and `unbind()` unlinked that cell, leaving the computed frozen at its last value and deaf to its
inputs for good. Measured rather than reasoned about: a `total` of 3 stayed 3 after the source it sums went to 10.
`_bindable()` is the guard, and it **rejects `Computed` rather than requiring `Reactive`**, so a declaration
subclassed outside this module stays bindable — which is the extension point above being used the first time it is
described. `peek()` still takes either, because reading a derived value without subscribing to it is a legitimate
thing to ask of a computed.

## The cursor: shown where the keys go

**Written**, and the fifth and smallest item of *What the widget library needs first* below. `Widget.cursor_position()`,
the `caret` widget property, `terminal.place_cursor()`, and a few lines at the end of `Application._render`.

The terminal's own cursor was hidden at startup and never placed again, so the only caret available was a reversed
cell — which is what `Console.render` paints by hand, and which cannot blink, cannot be a bar, and is not where a
screen reader or a terminal's own copy-mode thinks the cursor is.

**A widget says where it wants one, in its own coordinates, and only the widget the keys are going to is asked.** The
one the application asks is the head of the focus path — the same walk `dispatch_key` makes, so the same modal, the
same invisible-ancestor test, and the same answer of "nobody" when nothing holds the keyboard. A caret drawn on a
widget that could not receive what is typed into it would be a lie told once per frame, and reusing the walk is what
makes it impossible rather than merely avoided.

### Why it is not called `cursor`

`navigator`'s `Panel` already has one: `cursor: int = reactive(0)`, the row its selection bar is on. A `cursor` on
`Widget` would have been shadowed by it in silence — a subclass attribute beating a base-class method with no
complaint from anything — and the application would have been handed a row number where it expected a position. The
name is `cursor_position()` for that reason and no other.

It is a **method rather than a reactive attribute** because exactly one widget per frame is asked, at paint time, and
nothing derives from the answer. A cell on every widget would buy the ability to bind something to a caret's position,
which nothing wants, and cost one on every widget that has no caret at all.

### Where the escape goes

At the end of the frame, after the diff, always: **painting moves the terminal's cursor as a side effect**, so
anything placed before it is left wherever the last cell was written. Three cases, and the third is the one that keeps
an existing promise:

- the cursor changed, appeared or went away — place and show it, or hide it;
- unchanged, but the frame painted something — re-emit the position alone, since it is already visible and already
  the right shape, and the painting has just moved it;
- unchanged, and the frame painted nothing — emit nothing, which is what keeps a frame that changes nothing writing
  nothing, and `tests/test_application.py` has asserted that since long before there was a cursor.

`render_diff` was left alone. It turns one buffer into another and the cursor is not in the buffer; the placement is
the application's, which is the layer that already owns the terminal and knows what the focus is.

### The shape is a widget property, from the sheet

`caret` joins `border` as a `StyleProperty` — `Input { caret: bar }` — for the reason *Widget properties: `Style` does
not grow a border field* above gives: a cursor shape produces no SGR sequence and is an input to an escape rather than
an appearance a cell can carry. The vocabulary is DECSCUSR's, spelled out (`block`, `underline`, `bar`, each with a
`blink-` form).

**`default` means "leave the user's own alone", and is the default.** A terminal's cursor shape is a setting somebody
chose, and a library that overrode it merely because it had the ability would be the rudest thing in it; the escape is
not emitted at all unless a widget asks for something specific. The reset at shutdown *is* unconditional, like the SGR
reset it sits beside, because a widget may have changed the shape at any point in the run and the flag that would say
so belongs to a frame rather than to the terminal.

### The console was the first thing converted

`navigator`'s console painted the child program's cursor by reversing a cell, for want of a real one. It has the real
one now, and the conversion is three small things worth recording because they are what any adopter does:

- **It takes the focus while it is showing.** `Console.can_focus` is set in `__init__` — not in the class body, where
  a plain `can_focus = True` would shadow the `Reactive` descriptor with an ordinary attribute — and a `Manager` effect
  hands it the keyboard whenever `console_visible` goes true. Saying that to navkit is what gets the cursor drawn:
  `Navigator.on_key` had been saying it in a comment for as long as the console has existed, "it has the screen, so it
  should have the keyboard".
- **`cursor_position()` is three lines**, `ConsoleScreen.cursor` having reported `(x, y, hidden)` all along.
- **It fixed a bug on the way through.** The reversed cell was painted whether or not the view was scrolled back, so
  scrolling into the history highlighted whatever happened to sit at the live cursor's coordinates among rows it has
  nothing to do with. `cursor_position()` answers None while `scrolled_back`, which is the question the hack never
  asked.

Checked on a real pty rather than only against `FakeTerminal`, since this is output the fake one cannot prove: startup
hides the cursor and never shows it, Ctrl+O emits the placement immediately after the frame's last cell, toggling back
hides it again, and exit restores both the cursor and the shape.

## Modal and overlay: the input, not the painting

**Written**, and the fourth item of *What the widget library needs first* below — the last of them. `Widget.modal`,
`Application.modal`, `Application.overlay()`, and the two dispatch paths rerouted around them.

Z-order was never the missing piece. Rendering walks children forwards and hit-testing backwards, so a dialog added
last is painted over everything and asked about a click first; what "modal" adds is that **the widgets underneath stop
being reachable**, which is a question about input and about nothing else.

### Modality is a property of the widget, maintained by the lifecycle

`Widget.modal` is declared beside `can_focus`, and reads the same way: what kind of widget this is, on the class, with
an instance free to differ. The application is told by the **mount walks** — mounting a modal pushes it, unmounting
pops it — rather than by a `push_modal()` a caller has to remember to pair.

That is the whole reason the mechanism is small. Every route a widget can leave a live tree by already runs the unmount
walk: `remove()`, a replaced root, an ancestor carried off with it. So the input comes back on all of them without any
of them knowing what a modal is, and there is no path on which a dialog can leave the screen still holding the
keyboard. It is the second thing *Mounting: joining a live tree, and leaving one* above paid for, the first being the
effect disposal it was built for.

The flag is read **when the widget is mounted**. Flipping it on something already mounted does nothing until the next
time, which is the shape a dialog is used in — declared modal, opened, closed — and the alternative is a stack that has
to be re-derived whenever anything anywhere is assigned.

### Keys: one substitution

`Application._handle` dispatches a key on `self.modal or self._root`. That single change is the whole of keyboard
exclusivity, and it is *Focus: one pointer, and eligibility decided at delivery* above paying out: `dispatch_key` walks
from the focused widget up to the widget it was called on, so dispatching on the modal means the walk cannot start
outside it — `_focus_path()` answers empty for a focus elsewhere — and cannot bubble past it, the modal being where the
walk ends. Nothing was added to either method.

A modal with nothing focusable inside it absorbs keys itself, which falls out of the same walk: an empty focus path
leaves the widget that was dispatched on, and that is the modal.

### The mouse is where modality actually costs something

The mouse routes by **position**, not by focus, so every widget under the pointer is on its path whether or not it is
supposed to be reachable. There is no equivalent of the focus path to reroute; the event has to be moved.

`Application._dispatch_mouse` translates the event into the modal's *parent's* frame — `Widget.offset()` sums the
ancestors' positions, the root sitting at the origin — and offers it there, because `dispatch_mouse` takes an event in
the widget's parent's coordinates and shifts it inward itself. **An action landing outside the modal reaches nothing at
all**: not the widgets underneath, which is the point, and not the modal either, whose coordinate system it is not in.

**Dismissing on an outside click is a policy and is deliberately absent.** A widget that wants it watches the
application's own `on_mouse_click`, which still sees every action before any of this and is where a policy about input
belongs. Baking it in would make the other choice unexpressible.

### Focus is confined, and handed back

Three things, and the third is the one that was promised earlier:

- `Widget.focus()` refuses a widget outside the active modal, so nothing can put the keyboard back behind the dialog.
- `Application.focus_next()` runs the tab order over `self.modal or self._root`, which is the whole of what keeps a
  dialog's Tab inside the dialog — `focusable()` was already subtree-scoped for exactly this.
- **The stack remembers what had the focus when each modal took over, and hands it back when that modal leaves.** The
  focus section above said a per-container memory is a feature that composes on top of one pointer and cannot be taken
  back out of one; this is that feature, built the day something needed it, and the stack is the only place that did.

A modal removed out of order — not the top one — simply leaves the stack without moving the focus, which stays with
whatever is still holding the input rather than being handed back past it.

Two smaller decisions inside that:

- **The focus is settled after the subtree has finished mounting**, which is why `_mount` is two methods: a modal
  choosing its first field has to be choosing from children that exist, and a mount handler that focuses something
  itself must not then be overruled by a default. Handler last wins.
- **A modal with nothing focusable takes the focus away rather than leaving it outside.** Otherwise a widget the user
  can no longer reach keeps the `:focused` highlight and goes on looking like the live one.

### Overlay is one method

`Application.overlay(widget)` adds it as the last child of the root and returns it. A widget deep in the tree opens one
with `self.application.overlay(dialog)`, which is the point: where a dialog is *created* has nothing to do with where
it belongs on the screen.

There is no `close_overlay()` to pair with it, because the inverse already exists and already does more than a wrapper
would: `app.root.remove(dialog)` unmounts the subtree, disposes its effects, releases the input if it was modal and
hands the focus back. A second name for that would only be a worse place to read about it.

### What is deliberately not here

- **Nothing dims or disables what is behind a modal.** `Application.modal` is a plain property over a plain list rather
  than anything observable, so no widget can currently restyle itself for being blocked. A `computed` can be added the
  day a widget asks; guessing at the shape now would cost a cell on every widget for a look nothing has asked for.
- ~~**The mouse is not *captured*.**~~ It is now — see *Windows: raising, capturing, painting over* below. It was
  left to "a scrollbar's problem", and a window's title bar turned out to be the first thing that needed it.
- ~~**`navigator`'s console is still the `visible`-binding trick.**~~ Rewritten: the console is the background layer
  of the screen and is always showing, and Ctrl+O hides the desktop above it. One `visible` binding is left, on the
  desktop, and that is the whole of Ctrl+O.

## Windows: raising, capturing, painting over

**Written**, for navml's overlapping `Window` and its `Desktop`. Three additions, each small, each something a widget
library could not do for itself without reaching into navkit's privates.

### Raising is a reorder, never a re-add

*Z-order needed nothing* was true while the only thing on top was a dialog added last. A window that is clicked has to
*become* the last child, and `add()` already moves a child — by detaching it first, which unmounts the subtree,
disposes its effects, takes the focus away if the focus was inside it and pops it off the modal stack. Bringing a
window forward must do none of that: it is the same window, still holding the same keyboard.
`Widget.raise_child(child)` and `lower_child(child)` reorder `children` in place and call `invalidate()` by hand,
because the children list is not reactive. Anything that needs to *observe* the order — a window's `:active` state —
is given a reactive of its own by whoever does the raising (`Desktop.active_window`), rather than navkit making every
children list observable to serve one reader.

### Mouse capture

Routing is by position, and a pointer dragging a window's edge is routinely outside the window by the time the
terminal reports it — a fast hand, or a resize the window refuses past its minimum. So
`Application.capture_mouse(widget)` sends every mouse action to *widget*'s handler, under `event.handler` and in its
own coordinates, with **no hit test**. It is the application's rather than the widget's because `_dispatch_mouse` is
the one place every action passes through. The application's own `on_mouse_click` hook still sees each action first,
as it always has.

It is released in three places, each of which would otherwise leave the mouse stuck on something unreachable: **after
a `release` is delivered** (the ordinary end of a drag), **when the holder is unmounted** (a window closed mid-drag),
and **when a modal opens that does not hold it** (the modal's rule is that nothing outside it is reachable, and a
capture is a way of reaching). A double-click, which is dispatched inline right after its second press, goes to the
holder too — which is how a window zooms on a double-click on the title it has just started dragging.

### `render_after`: painting over the children

`render_tree` paints a widget and then its children, so nothing a widget draws in `render()` can sit on top of them.
A frameless window needs exactly that: the file manager's panels *are* its frame, and its close and zoom icons belong
on their top edge. `Widget.render_after(surface)` is an empty hook called after the children, on the same view. The
alternative — asking the panels to leave gaps for icons they know nothing about — would have put a window's chrome
into a list widget.

## Mounting: joining a live tree, and leaving one

**Written**, and the third item of *What the widget library needs first* below. `Widget.mounted`, `on_mount`,
`on_unmount`, the walks behind them, and `navkit.reactive.dispose_effects()`.

**Mounted means reachable from an application, not "has a parent".** A tree under construction is not mounted, however
deeply it is nested; the whole of it mounts at once when its root is handed to `Application.root`, which is how
`navigator` builds its desktop and then attaches it. A widget added to a tree that is already mounted mounts
immediately, and that case — a dialog opened at run time — is the one the whole section exists for.

The transition is **driven by the three operations that can cause it** — the `root` setter, `add()` and `remove()` —
rather than derived from `Widget.application`. Deriving would be the tidier-looking answer and does not work: a
`computed` is lazy, so nothing would notice the change until something happened to read it, and "notice" is the entire
job. An effect per widget watching its own `application` would work and costs one eager cell per widget for a fact
three methods already know.

### Why the hook is not an event, and not called `on_*`

`Widget.mounted()` and `Widget.unmounting()`: synchronous, argumentless, and outside the `on_*` namespace altogether.

**This was decided twice, and the second answer is the one that stands.** The first design made them `on_mount(event)`
and `on_unmount(event)` with two fieldless event classes, on the argument that markup fixes every handler at exactly
one argument so a hook taking none is the one shape a `.nml` document could not spell. That argument died with
*Every handler is `async def`* below: **the mount walk runs from `add()`, which runs from `__init__` when a widget is
constructed with a parent, and a constructor cannot await.** A lifecycle hook therefore cannot be a handler, whatever
it is called, and `MountEvent`/`UnmountEvent` were deleted with the names.

What survives is the better rule, stated once and applying to both: **a hook that cannot be awaited where it is called
does not get an `on_*` name.** `Application.on_start` and `on_stop` take no event either and *keep* their names,
because `run_async` can await them — so the line is drawn by what the call site can do, not by whether an event object
happens to exist.

The cost, recorded rather than glossed: **markup can no longer write a mount hook.** A markup-only component that needs
work at mount gains a `.py`. That is the same line *A handler body is one line* draws in `navml/DESIGN.md` — markup
says what, Python says how — falling where it already falls.

The hooks are **called directly, never emitted.** Emitting walks up, so mounting a subtree of twenty widgets would
deliver twenty mounts to the root, each of which it can do nothing with. A widget that wants its ancestors to know it
has arrived emits something of its own, which is one line and says what it actually means.

### Parents first, children first

Mounting is parents first, so a child's handler finds every ancestor already mounted. Unmounting is children first, so
a child is taken apart while its parent is still whole. Both walk in child order, the tree told about in the order it
is written.

`on_unmount` runs **before** the unlink and before the effects are disposed. It is the only moment a leaving widget has
everything it needs: still parented, still sized, still reachable through `application`. A handler releasing something
outside the reactive graph — a subprocess, an open file, a timer — has no other place to do it from.

### Why removal disposes effects, and what that asks of a widget

This is the part that was a bug rather than a missing feature. **An effect is eager**, so an effect whose expression
stops making sense does not wait to be read before it fails: `remove()` sets `parent = None`, that write queues every
effect that read it, and the next flush raises `AttributeError: 'NoneType' object has no attribute 'width'` — which
`Application._flush_effects` turns into an `exit()` and a re-raise. **Removing a widget took the application down**, and
it is measured rather than argued: switching the disposal off and removing a widget whose effect reads
`self.parent.width` reproduces it in six lines.

So `remove()` disposes every effect registered on each widget of the subtree, through the new
`reactive.dispose_effects(obj)` — the counterpart to calling `effect()` without keeping the handle, which is how every
effect in this repository is created. `Effect.dispose()` existed and nothing called it; this is its caller.

A binding needs no such rescue, and the asymmetry is the point: a binding is lazy, so a detached widget's
`w.parent.width` is never evaluated while nothing paints it, and re-attaching writes `parent` again, which invalidates
the cell and lets the cached failure recover. Eagerness is what makes effects the ones that have to be stopped.

**What it asks of a widget is one sentence: a widget that can be removed and put back declares its effects in
`on_mount`.** Disposal is permanent, so effects created in `__init__` do not come back — the widget would be detached
once and dead afterwards, which is worse than the crash it replaces if it is not written down. A widget built once and
never detached may keep declaring them in `__init__`, which is what `navigator`'s `Panel` does and why nothing in the
application had to change: its panels are never removed. The flush order that `Panel.__init__`'s comment calls
load-bearing is preserved either way, being the order the `effect()` calls are made in.

### Two smaller things that fell out

- **`add()` lays a child out, but only into a mounted parent.** Otherwise the child is 0x0 until the next terminal
  resize and a run-time dialog paints nothing, silently. The restriction to mounted parents is not timidity: `layout()`
  hands the parent's size to every child whose size is not bound, so laying out during construction would overwrite a
  `width=` the caller had just passed to the constructor. A tree still being assembled has no size to cascade anyway,
  and `Application.root` lays the whole of it out when it is attached.
- **`Application.root = None` unmounts the outgoing tree and drops the focus into it.** The focus half was already
  owed — *Focus: one pointer, and eligibility decided at delivery* above clears focus in `remove()` for the same reason
  — and replacing the root is the other way a focused widget can leave the screen.

## Focus: one pointer, and eligibility decided at delivery

**Written**, and the first item of *What the widget library needs first* below. `Application.focused` holds the widget
keys go to, `Widget.can_focus` says which widgets may hold it, `Widget.focus()` takes it, `Application.focus_next()`
moves it along, and `Widget.dispatch_key` was rewritten around it.

### The application holds it, the widget derives it

One pointer, on the application, rather than a focused flag per widget or a remembered child per container. The flag
would need every widget that takes focus to clear every other, and a per-container memory is a *feature* — a dialog
restoring what it had — that composes on top of a pointer and cannot be taken back out of one.

`Widget.focused` is therefore a `computed` reading `self.application.focused is self`, and that buys the thing worth
having: **it is a stylesheet state for free.** `:state` selectors resolve through `getattr(widget, state, False)`
inside the style cascade's own computed, so `Panel:focused { … }` matches with nothing added to the stylesheet engine,
and moving focus restyles the widget that lost it and the one that took it without either being told. That is
`navigator`'s hand-rolled `Panel.active` — which `Manager.active_panel` assigns and `navigator.nss` reads — arriving as
a navkit notion.

### A widget is not focusable until it says so

`can_focus` is `False` on `Widget`, so a container, a frame and a label stay out of the tab order by saying nothing.
The other default would put every box in the tree in it and make opting *out* the common case, which is the wrong way
round for a library whose widgets are mostly structure.

It is `reactive` rather than a plain class attribute because a widget withdraws from the order while it is disabled,
and because a binding should be able to decide it. That costs one cell per widget and makes `Panel:focused` and
a disabled button's exit from the tab order the same kind of fact.

### Eligibility is decided when the key arrives, not when focus is set

`focus()` refuses a widget that is not focusable, not visible, or not attached to an application. It does **not** walk
up checking that every ancestor is visible, and `Application.focused` is not policed at all on assignment.

The reason is that the alternative is worse than it looks. A focused widget can stop being reachable without anything
touching it — `navigator` hides a whole band of the desktop when the console opens, by flipping one reactive flag that
three `visible` bindings read — so keeping the pointer correct would mean an effect watching the visibility of every
ancestor of the focused widget, re-established whenever focus moves. Instead `dispatch_key` walks from the focused
widget up to itself and abandons the walk at the first invisible step, which is a walk it has to make anyway:

- the focus is a *pointer*, and it stays where the author put it;
- whether the keyboard can reach it is a question about the tree right now, asked once per key.

So hiding a container does not have to chase the focus inside it, and showing it again does not have to restore
anything. What the walk costs is one `parent` hop per level, on the key path, against an effect per focused widget on
the write path.

The one place the pointer *is* corrected is `remove()`: a focus left pointing into a detached subtree would send every
key to a widget that is no longer on screen and can never be reached again. `remove()` clears it before the unlink,
while the focused widget can still be walked back to the child being removed.

### A key goes to the focused widget and bubbles up

`dispatch_key` was a positional lottery — every visible descendant offered the key, deepest and last-added first, until
one returned `True`. It now walks the focus path: the focused widget, then its ancestors up to the widget dispatch was
called on. The same shape as `emit`, started from where the keyboard is rather than from where an event was raised,
so a container can carry the bindings its children share and an unhandled key finds it.

**With nothing focused, the widget dispatch was called on is offered the key and nobody else.** That is a deliberate
change rather than a fallback: a key belongs to whatever holds the keyboard, and when nothing does, to nothing. The old
behaviour only looked harmless because no widget in the repository defines `on_key` — `navigator` routes every key from
one `if/elif` chain in `Navigator.on_key`, which runs before the tree and is untouched by this.

Two things this deliberately does not do, both of them the widget library's:

- **Nothing binds Tab.** navkit provides `focus_next(reverse=…)` and no key binding for it, because `navigator` spends
  Tab on switching panels and a library that took it would be wrong there first.
- **A mouse press does not focus what it hits.** `dispatch_mouse` routes by position and says nothing about the
  keyboard; a Button that wants the pair calls `focus()` in its own `on_mouse_click`, which is one line and a policy.

### The tab order is a walk, not a list

`Widget.focusable()` returns the visible, focusable widgets of a subtree in tree order, pre-order, so a container that
takes focus comes before the children it contains. `Application.focus_next()` runs it over the root each time rather
than keeping one: the tree is reactive, so a kept order would be stale the moment a widget is added, hidden or
disabled, and the walk is over a tree the loop already repaints whole.

**It is scoped to a subtree because that is what modal will need.** A dialog runs the same walk over itself and nothing
outside it is reachable — which is the half of *Modal and overlay* below that focus is responsible for, left in the
right shape rather than built now.

A focus that has left the order — hidden, or removed — does not stop a move: the search starts from the end it came
from, so Tab out of a vanished widget lands on the first widget rather than on nothing.

## Emitting: a widget event walks up

**Written**, and decided ahead of the code because `navml/DESIGN.md` had written its handler rules against it —
*A handler body is one line* and *The handler's one argument is `event`* — and *What the widget library needs first*
below said the two halves had to be settled together. This is navkit's half: `Event.handler` and `emitted()` in
`navkit/events.py`, `Widget.emit()` and `emits` in `navkit/widget.py`, and one fallback branch in
`Application._handle`.

The verb was `announce` for one commit and is now `emit`, renamed throughout on the author's preference. Nothing about
the mechanism moved with the name.

`Widget.emit(event)` offers the event to the widget itself, then to each of its ancestors in turn, then to the
application, and stops at the first handler that returns `True`:

```python
async def emit(self, event: Event) -> bool:
    """Offer *event* to this widget, then to its ancestors, then to the application."""
    widget: Widget | None = self
    while widget is not None:
        handler = getattr(widget, event.handler, None)
        if handler is not None and await _call(widget, event, handler):
            return True
        widget = widget.parent
    app = self.application
    if app is not None:
        handler = getattr(app, event.handler, None)
        if handler is not None and await _call(app, event, handler):
            return True
    return False
```

That is the whole mechanism, `_call` being the one line that holds an instance-assigned handler to the async rule
below. **A handler is an `async def on_*`, or an instance attribute of the same name, taking one argument and
returning a bool** — which is what `Widget.on_key` and `Application.on_mouse_click` already are, so a signal
introduces no second convention for handlers, no second one for consumption, and no new kind of object. A widget
emits something by declaring an `Event` subclass and calling the one method.

### The handler name is read off the event class, not invented

`Event` gains a `handler` class attribute, derived from the class name at class creation: strip a trailing `Event`,
snake-case what is left, prefix `on_`. **The rule was not chosen, it was measured** — every event that existed when
it was written down already obeyed it, the one that is never dispatched included:

| event              | derived          | today                                                    |
|--------------------|------------------|----------------------------------------------------------|
| `KeyEvent`         | `on_key`         | `Widget.on_key`, `Application.on_key`                    |
| `MouseClickEvent`  | `on_mouse_click` | `Widget.on_mouse_click`, `Application.on_mouse_click`    |
| `DoubleClickEvent` | `on_double_click`| a widget's, when it wants one                            |
| `ResizeEvent`      | `on_resize`      | `Application.on_resize`                                  |
| `PasteEvent`       | `on_paste`       | `Application.on_paste`                                   |
| `WakeEvent`        | `on_wake`        | never dispatched                                         |

The second row is the one honest exception to "measured": it was `MouseEvent` reaching `on_mouse` when the rule was
written, and the class was **renamed to `MouseClickEvent` so that `on_mouse_click` would derive** rather than being
pinned with an explicit `handler`. That is the trade the rule asks for and the right way round — an override would
have put the first hole in a table whose whole value is that a reader can predict the handler from the class. What it
costs is that the class name is narrower than the class: a `MouseClickEvent` still carries `action="move"` for a drag
and `button="wheel_up"` for the wheel, so **the name says click and the type says every mouse action**. The docstring
says so too, since the name no longer can.

so `ClickEvent` reaches `on_click` and `SelectionChanged` reaches `on_selection_changed` without anything being
registered anywhere. A class may set `handler` explicitly and is then left alone. **A subclass derives its own name
rather than inheriting one**: `DoubleClickEvent(MouseClickEvent)` reaches `on_double_click` and not `on_mouse_click`,
because a refinement that arrived at the handler for the thing it refines would be indistinguishable from it, and the
widget that wanted only the plain event could not say so.

One measured trap, because it costs an hour to find and a line to avoid: **`@dataclass(slots=True)` replaces the class
it decorates**, so the `__class__` cell a zero-argument `super()` closes over inside `__init_subclass__` names the
*pre-slots* class, and every subclass then fails to be created with
`TypeError: super(type, obj): obj must be an instance or subtype of type`. Spelling it `super(Event, cls)` resolves the
global at call time and works. Every event in `navkit/events.py` is `frozen=True, slots=True`, so this is not a corner
case, it is the first line written.

### Every handler is `async def`, and a synchronous one raises

`Widget.on_key`, `Widget.on_mouse_click`, `Widget.emit`, both dispatchers, every `Application` hook, and every `on_*` a
widget library or an application declares. `_main_loop` awaits `_handle`; the emit walk awaits each handler in turn,
which is what keeps consumption meaning what it meant.

**The reason is not symmetry with the reactive layer**, and it is worth writing down because it reads as though it
should be: `navkit/reactive.py` contains no `async` and no `await` at all. Observable attributes are *deferred* — a
write marks dependents stale, values recompute lazily on read, effects queue to a scheduler flushed once per frame —
and deferred is a different property from asynchronous. The reason is the plain one: a handler that wants to read a
file, start a process or talk to a socket should be able to, and a synchronous handler can only block the loop while
it does.

**A hook that cannot be awaited where it is called does not get an `on_*` name.** That is the whole of the rule's
boundary, and it is what `Widget.mounted()` and `Widget.unmounting()` are called that instead — see *Why the hook is
not an event, and not called `on_*`* above. `Application.on_start` and `on_stop` take no event either and keep their
names, because `run_async` can await them.

**Enforced in two places, because neither can see what the other does.**

- `Widget.__init_subclass__` and `Application.__init_subclass__` call `check_handlers(cls)`, which refuses a class
  whose own body defines a synchronous `on_*`. It fires at import, naming the class and the method — a traceback at
  class creation otherwise points at the `class` statement and nothing else.
- The emit and dispatch walks check a handler found on the **instance** before calling it. That is what markup
  compiles to and what no class-creation check can see. Without it the failure is
  `TypeError: object bool can't be used in 'await' expression`, which names neither the widget nor the handler.

**What the frame model gives up is less than it looks.** A handler that awaits lets the loop run mid-batch — reading
input, pty output, timers, signals — so a batch is no longer an uninterrupted stretch of Python. But **it cannot cause
a repaint**: `_render` has exactly two call sites, both inside `_main_loop`, so nothing paints until the batch has
drained. One frame per batch survives untouched, and `tests/test_application.py` pins it with a handler that yields.
The real cost is bigger than "the frame waits for it", and the omission was paid for. **The batch waits too.**
`Application._events` has exactly one consumer — the `while` loop in `_main_loop` — so a handler that awaits is
holding it: input is read and queued by the reader callback and *nothing dispatches it*. For a handler awaiting
something that will resolve on its own, that is only latency. For a handler awaiting something a **later keystroke**
must resolve, it is a deadlock with the old frame still on the screen: the widget library's first dialog was written
this way, mounted correctly, took the modal focus correctly, and was never painted and never answered.

So `Application.spawn(coro)` exists, and the rule is **a handler starts work that waits; it does not wait itself.**
The task is held rather than left to the caller — an unreferenced `create_task` may be collected mid-flight and takes
its exception with it — and whatever is still pending when the application stops is cancelled, so a dialog left open
at exit tears itself down through its own `finally`. `Application._dispatching` is set around `_handle` so that the
mistake can be *refused*: `navml.widgets.Dialog.execute` reads it and raises a `RuntimeError` naming `spawn`, which
is three lines and the difference between a diagnosable error and a frozen terminal.

### A widget declares what it emits

`emits = (ClickEvent,)`, a class attribute on `Widget` defaulting to `()`, read through `navkit.events.emitted(cls)`.

It exists because **emitting is otherwise invisible**. `Event.handler` means nothing has to be registered for an event
to be *delivered*, which is the mechanism's best property — but it also means a component's events can only be
discovered by reading its method bodies for `emit` calls. The declaration is the public surface instead: what a reader
consults, what a `.pyi` carries, and what navml's generator checks an `on_click:` line against.

**`emitted()` unions over the MRO where `declarations()` shadows**, and the difference is not an inconsistency. Two
declarations of one attribute are two versions of the same thing, so the nearest wins. A subclass that emits something
new is *adding* to what its base emits — `FramedButton` keeps `Button`'s `ClickEvent` without naming it — because
nothing about emitting one event says anything about another.

### What belongs in `navkit/events.py`, and what does not

**Only events navkit itself raises**: `KeyEvent`, `MouseClickEvent`, `ResizeEvent` and `PasteEvent` come from the
terminal, and `WakeEvent` from the loop. A `ClickEvent` does not belong here however generally useful it sounds,
because a click is something a *widget* means and navkit has no widgets beyond the base class.

The boundary is the layering rule read at the level of one module, and it is what the deleted `MountEvent` was already
straining: navkit knew what it meant, but nothing in navkit ever emitted it. The widget library declares its own,
beside the component that emits them — `navml/DESIGN.md`, *Declaring an event*.

### Why synchronous, and not through the queue

`post_event` exists and an emitted event could have gone through it. It does not, for three reasons and at one cost:

- **The return value is the protocol.** A queued event's answer goes nowhere, and consumption is what `dispatch_key`
  already means by `True` — and what navml made load-bearing when it settled that a markup handler always consumes.
- **The batching that matters happens at the frame, not at the queue.** The loop dispatches a whole batch, flushes the
  effects it queued and paints once; a handler that changes reactive state during dispatch is already inside that
  batch. So queueing an emitted event would buy none of the coalescing the queue exists for.
- **Cause and effect stay adjacent.** A queued event is handled after everything else the terminal has delivered
  in the meantime, so the press and its consequence would be separated by whatever arrived between them — for no gain,
  since both land in the same frame either way.

The cost is that a handler which emits back into its own emitter recurses. That is the author's cycle rather than
the mechanism's, and the stack names every frame of it; the same cycle through the queue would spin the loop forever
and leave no trace of where it started.

### Why up, and what the application sees

Input travels **down** because the user pointed at a place, or at what focus will eventually designate. An emitted event
travels **up** because it already knows its sender and does not know its audience. So the application sees input
*before* the tree and emitted events *after* it, which is the same asymmetry read from the other end.

`Application.on_event` is **not** offered an emitted event. Its contract is to intercept an event before the widgets get
it, and an emitted event reaching the application has already passed every widget that could have claimed it; the named
hook is offered instead.

**The emitter is offered its own event first.** Without that a component could not handle what it itself raises, which
is exactly what markup writes — `on_click:` sits on the `Button:` block that emits it. And it agrees with the two
notes' other precedence rules: `dispatch_key` offers a key innermost-first, and navml resolves a bare name to the
widget's own property before anything else. The most specific claim wins in all three.

### One handler per widget per event

A slot, not a list. `w.on_click = handler` is the whole of connecting, and there is no `connect()`, no
`disconnect()` and no `Signal` object.

- **Bubbling already covers the second listener.** The usual reason for a listener list is that two objects care, and
  here the second one is an ancestor, which the walk reaches anyway.
- **A list would need a disconnect story navkit does not have.** `Effect.dispose()` exists and nothing calls it, and
  `remove()` sets `parent = None` and stops — *Mount and unmount* below. A listener list would add a second kind of
  reference held across a detach, on top of the one already unresolved.
- **Markup assigns.** navml's generator emits `self.b.on_click = _on_click`; a list would need a different spelling
  there for no benefit the walk does not already give.

**The one hazard is a precedence inversion, and it is worth stating plainly.** An instance attribute beats a class
method, so a handler assigned onto the instance wins over one defined on the class. For a component written as both
halves that is backwards: `button.py`'s `def on_click` is on the *derived* class, which wins everywhere else in the
language, and the generated `__init__`'s assignment silently beats it. navkit cannot catch this — the assignment is
legal and the two names are equal — so it is navml's to catch when the document is compiled. The rule it catches it
with is about the **object the assignment lands on** rather than about a name: a markup `on_X:` line may not land on
an object whose class already implements `on_X`. Phrased by name alone it was wrong in both directions — it refused a
line that lands on a *child* and shadows nothing, and it never saw a line on a child block quietly beating that
child's own `on_key`. `navml/DESIGN.md`, *What the generator checks about a handler line*, has the whole of it.

The same inversion is what makes navml's `on_<id>_<event>` convention safe, by turning it the right way up: the
generated half declares a no-op handler for each id'd child and *assigns a bound method of the component*, so the
hand-written half overrides it as an ordinary derived class and nothing is assigned onto an instance at all. The
component's own `on_click` still sits behind it on the walk, because the stub returns False.

### What it cost `Application`

One fix, small and owed anyway: `_handle` dispatched only the four types it knew, so an event posted with `post_event`
reached `on_event` and then nothing. It now falls back to `event.handler`, so `post_event(TickEvent())` reaches
`Application.on_tick`. There are then three paths and each has a reason: input arrives from outside and goes **down**;
a widget's own event goes **up**; a posted event has no sender in the tree and stops at the application.

**One edge came out of writing it**, and it is the reason the fallback is four lines rather than two: a bare `Event`
derives `on_event`, which `_handle` has *already* offered every event to at the top — so the fallback called the same
hook a second time, measured at two calls for one `post_event(Event())`. The guard compares the bound method rather
than the name, which also covers an event class that names `on_event` deliberately.

### What the tests pin

`tests/test_widget.py` holds the walk and `tests/test_events.py` the naming. Four of them are pinning a decision rather
than an implementation, and should be read as the decision: the emitter is offered its own event before its ancestors;
a handler returning `True` stops the walk where it stands; `Application.on_event` is **not** offered an emitted event;
and a widget with no parent and no application emits into nothing and returns `False` rather than raising. A fifth
pins the derivation against the four events that predate it, so a renamed hook cannot drift from the class it serves.

The last one is the useful one: **a mouse press is turned into an emitted event with no focus notion anywhere**, which
is a whole mouse-driven button in twelve lines of test, and it corrects the build order below. `dispatch_mouse` already
routes by position, so emitting never needed focus. What waits for focus is a button driven by the *keyboard*, which
is a different sentence than the one that list was making.

## Double-click: a timer, not a meaning

**Written.** `DoubleClickEvent` in `navkit/events.py`, `ClickTracker` and `DOUBLE_CLICK_TIMEOUT` in
`navkit/application.py`, and a `getattr` at each of the two mouse dispatch points.

### Why it is navkit's, when `ClickEvent` is not

*What belongs in `navkit/events.py`* refuses `ClickEvent` because a click is something a widget *means*. A
double-click is not a meaning, it is a **temporal disambiguation of raw terminal input**, and the kit already does one
of those. A lone `ESC` byte is indistinguishable from the start of a sequence, so `InputParser` states the ambiguity,
`_schedule_escape_flush` arms a timer and `_flush_escape` manufactures a `KeyEvent("escape")` that was never on the
wire. SGR 1006 reports `press`, `release` and `move` and nothing else; two presses close together in one cell are a
fact neither press carries, and the same machine produces it.

The membership test that section states is **does navkit raise it**, and navkit raises this one — which is exactly
what `ClickEvent` fails, nothing in navkit emitting it, and what the deleted `MountEvent` failed for the same reason.
Excluding a double-click would mean adding a second, unstated test after the fact, to rule out the first case that
passes the first one.

What settles it is not taste, though. **`Application._loop.time()` is the only clock reachable from event handling** —
`Widget` has no timer and this design offers none — so a widget library doing this itself would have to reach into the
private loop of the one object that owns it. That is the layering violation the boundary rule exists to prevent, so
the feature lands on navkit's side of the layer by the resource it needs rather than by argument.

**navkit raises the fact and never the meaning.** `DoubleClickEvent` asserts only that one button went down twice in
one cell inside the window. "Enter the directory" is `Panel.on_double_click`; "select the word" would be a text
widget's; `navml`'s `Button` gets nothing, because a double-click on a button is two clicks and that is already what
it receives. The same division as `KeyEvent`: navkit says F10 was pressed and never that F10 quits.

The honest concession: **what counts as "the same thing" under the pointer is arguably the widget's to say** — a row,
a cell, a word — and navkit has no way to ask. That is a *Still open* line below rather than a reason to refuse,
because the cell is the only answer navkit can give and it is the right default.

### The dispatch had to learn to read `event.handler`

*The handler name is read off the event class* promised that `DoubleClickEvent(MouseClickEvent)` reaches
`on_double_click` and not `on_mouse_click`. **It was not true when it was written.** `Widget.dispatch_mouse` ended in
`await self.on_mouse_click(local)`, and `Application._handle` matched `isinstance(event, MouseClickEvent)` and called
`self.on_mouse_click(event)` — so the one worked example in this file would have gone to the very handler it was the
example of not going to. Both now look the handler up the way `emit` already did:

```python
handler = getattr(self, event.handler, None)
return handler is not None and await _call(self, local, handler)
```

Four consequences, none of which needed anything else written:

- **A plain `MouseClickEvent` is unchanged.** `Widget.on_mouse_click` and `Application.on_mouse_click` are defined
  on the base classes, so the lookup always finds them and the call is the one that was always made. It *gains* the
  instance-handler async check `_call` carries, which *Every handler is `async def`* above already claimed both
  dispatch walks had and which only `emit` actually did.
- **A widget defining no `on_double_click` is skipped, and skipped already means unclaimed** — so the event falls
  outward to an overlapping sibling and then to an ancestor, exactly as an unhandled press does, and no widget needs a
  stub. The same property `emit` has for the same reason.
- **Modal routing cost nothing.** `translated()` rebuilds through `dataclasses.replace`, which keeps the subclass, so
  `_dispatch_mouse` reroutes a double-click into the modal's parent's frame and drops one landing outside it without
  knowing the class exists.
- **`isinstance(event, MouseClickEvent)` is true of it** — relied on in `_handle`'s branch chain, and a trap
  anywhere that meant only a plain mouse action. That is the price of the subclass and it is the right price: a
  standalone class would have needed a duplicate of every field, a duplicate `translated()`, and a second
  positional-routing path.

Refused: **a `clicks: int = 1` field on `MouseClickEvent`**. It is the cheapest option mechanically, needing no
routing change at all, and it is the case *The handler name is read off the event class* already refuses — "a
refinement that arrived at the handler for the thing it refines would be indistinguishable from it, and the widget
that wanted only the plain event could not say so". A field is opt-*out*: every `on_mouse_click` acting on a press
would act twice, silently, until its author noticed a field they had never heard of.

### Additive, and inline

**The second press is still delivered.** Suppressing it needs no deferral — the count is known *at* press two — so it
is the serious alternative, and it loses because it takes input away from code that never asked for the feature:
`Navigator.on_mouse_click` would stop moving the cursor onto the row it was clicked on, and a double-clicked `Button`
would fire one `ClickEvent` instead of two. A facility is not added to a kit by changing the contract of the stream
every existing widget is written against.

**Deferring the press until a timer expires is refused harder.** `ESCAPE_TIMEOUT` can spend 50ms because a lone `ESC`
is genuinely undecidable until then — there is no correct thing to do with it meanwhile. A press is a press whatever
follows it, and deferring would tax every single click in the application with 400ms of latency to serve the one in a
hundred that turns out to be a double.

The cost of additive, named: **a widget acting on both a press and a double-click acts twice.** That is the widget's
to arbitrate, and it is the right way round — "move the cursor to this row" on the press *composes with* "enter it" on
the double-click, which is exactly why `Panel.on_double_click` is three lines and not a rewrite.

**Dispatched inline**, immediately after the press, not through `post_event`. *Why synchronous, and not through the
queue* argues every clause of this already: the batching that matters happens at the frame and not at the queue, so
queueing buys no coalescing, and cause and effect stay adjacent. Concretely the press's own `release` is usually
already in the queue from the same read burst, so queueing would deliver press, release, double-click; inline delivers
press, double-click, release, which is what Qt and GTK both do. `_flush_escape` is not a counter-precedent — it runs
from a timer callback, *outside* any dispatch, where the queue is the only door in.

It re-enters `_handle` rather than being pushed straight at the tree, so `on_event` sees it, as it sees the escape key
navkit manufactures. The cost is that an `on_event` swallowing the press swallows the double-click too, which is
`on_event` being the outermost door and not a special case.

**The count is taken from the press before it is delivered, and regardless of who consumes it.** Whether a widget
claimed a press says nothing about whether the user clicked twice — and `Navigator.on_mouse_click` returns True for
every press inside a panel, so the other choice would have made the feature unreachable in the only application here.
A `DoubleClickEvent` is never counted as a press, which is what bounds the recursion at one level.

### What the detector keys on

`ClickTracker.press(event, now)` returns how many clicks the press completes, and only a count of exactly **2** raises
anything.

- **The run counts upward and never restarts inside itself.** A triple click is 1, 2, 3 and a fourth press is 4, so
  one double-click is raised and no more. Resetting to 1 after each pair would have entered the same directory twice
  on a fast triple click.
- **The exact cell, with no tolerance**, and the asymmetry is the argument: exact fails by *missing* a double-click,
  which the user repeats at the cost of a second; a one-cell tolerance fails by *inventing* one on the item next door,
  which opens something nobody asked to open. A missed double-click is an annoyance, an unasked-for one is
  destructive. navkit also cannot see the pointer wander between the presses — `MOUSE_ON` asks for 1000/1002/1006, and
  1002 reports motion only while a button is held, so the press coordinates are the only positional evidence there is.
- **Button identity is part of the key**, and all three buttons count; a handler filters by button the way one reading
  a plain press already does.
- **A wheel detent is not a click.** It arrives as `action="press"`, and two notches in one cell inside the window is
  the *normal* way to use a wheel. It also ends the run, which is the general rule the other resets follow: **the run
  is forgotten whenever navkit knows the cell no longer denotes the same thing** — a wheel scrolled the content, a
  resize moved the layout, a modal pushed or popped put something else under the pointer. That last one closes a real
  hole: press one on the desktop opens a dialog under the pointer, and press two at the same screen cell would
  otherwise arrive at the dialog as a double-click it never earned.

### The timeout is a constructor argument, and `ESCAPE_TIMEOUT` is not

`DOUBLE_CLICK_TIMEOUT = 0.4`, what GTK and Qt both default to, and `Application(double_click=...)` overrides it; `0`
disables the feature. The inconsistency is deliberate: the escape window is calibrated against a terminal's
transmission, which is nobody's preference, and the double-click window against a user's hand, which is the
application's to state. `Terminal(mouse=…)` against `info.mouse` is the same shape — the caller's wish and the
device's ability, either vetoing.

It also buys the test, and that earns it a place independently. **`ClickTracker` is clockless by construction** —
`press()` is *told* `now` rather than reading one — so the whole rule, triple clicks included, is tested in a plain
function with no loop, no application and no fake clock, which `tests/conftest.py` has no way to provide and should
not grow for one feature. The integration tests then work the real clock from both ends: `run_app` leaves 0.02s
between actions, twenty times inside the default window, and a test needing a pair to be *too slow* shrinks the window
to 0.001 instead of sleeping 0.4s of real time.

## Still open

- Whether the cell test should ever gain a tolerance. Two presses must land in the *same* cell today, which fails by
  missing a double-click rather than by inventing one, and that is the right way round where the consequence is
  opening something. But a cell is a large target next to the pixel slop a GUI toolkit allows, and what counts as "the
  same thing" is arguably the widget's to say — a row, a cell, a word — which navkit has no way to ask. The day
  something asks, the answer is probably a widget-supplied granularity rather than a constant, and it should not be
  guessed at before then.

- ~~What `Application.background` becomes.~~ **Answered: it is derived from the root widget's resolved style.** The
  duplication was never the second *paint* — `Manager.render` filling its own area is what lets the desktop be painted
  with no application around it, which `Manager.__init__`'s own sheet exists for. It was the second *derivation*:
  `navigator.nss` says `Manager { fg: $desktop-fg; bg: $desktop-bg }`, and `desktop_style()` read those same two
  variables by a separate route, going behind the cascade to the raw variable table because it ran "before any widget
  exists to ask". Asking the root at paint time is later, and later is when the answer exists. `background=` is now
  `None` by default and still accepted, for a root that paints only part of itself or for no root at all; `Navigator`
  stops passing it and `desktop_style()` is gone. Checked across all eleven themes: every desktop colour resolves to
  what it did before.
- ~~Which parts and properties the eventual *library* widgets declare.~~ **Answered, and the answer was read off
  DOS Navigator rather than designed.** The Colors dialog's slot table — all 144 entries of it, already transcribed
  into every theme by `tools/palconv.py` and carried inert — *names the widgets and their states*: frame and frame
  icons, scroll bar page and icons, static text, label normal/selected/shortcut, button
  normal/default/selected/disabled/shortcut/shadow, cluster normal/selected/shortcut, input normal/selected/arrow,
  list normal/focused/selected/divider. So the library's parts are a transcription, `navigator/styles/navigator.nss`
  binds them, and `navml/DESIGN.md`'s *The widget library* has the table.

  The half of this bullet that was *wrong* is now fixed too. "They are what the parser checks an unknown key
  against" was not true of parts: a `::part` selector was accepted whatever it named, so `Panel::rwo { }` matched
  nothing and said nothing. It cannot be checked at parse time — a selector matches by class *name* over the MRO, so
  the parser has no class to ask and a sheet may legally name a type it could not import. It is checked where the
  class is in hand instead: `Widget.parts` declares them, `stylesheet.parts_of()` unions them down the MRO the way
  `emitted()` does, and `part_style()` refuses a name its widget never declared. A test loads the shipped sheet with
  the widgets imported and asks the same question of every `::part` in it, which is the parse-time check spelled the
  only way it can be.
- What a full-screen child does. `run_on_terminal` hands over the real terminal and loses the output, which is the one
  thing the console exists to keep. The alternative is teaching the console an alternate buffer of its own — pyte stores
  `?1049` without obeying it — and that is worth doing only once something actually launches an editor.
- ~~Where the console's key routing belongs.~~ **Answered by focus, as predicted, and it took three methods instead
  of one.** `Navigator.on_key` keeps only what means the same thing wherever the focus is — Ctrl+O, and F10/Ctrl+Q —
  because an application hook runs before the widgets, so whatever is kept there is kept from the console, from the
  panels and from every dialog not yet written. `Console.on_key` keeps the scrollback and sends the rest to the child.
  `Manager.on_key` keeps the panel keys. **The `if manager.console_visible:` that used to arbitrate is gone
  entirely**: the console holds the focus while it is showing, so the focus path answers that question and the
  desktop's own handler never runs. Alt+X sat with the desktop rather than with the other two ways out because it has
  always been a desktop key — with the console up it is a keystroke for the child, and the child got it by
  `Manager.on_key` never running. **That stopped being true once windows could be closed**: closing the file manager
  took the key with it, and the user was left with no Alt+X at all. It is `Navigator.on_key`'s now, and the one
  application key that asks a question — it is left for the child while Ctrl+O has put windows away, and quits when
  there are none, because then the console *is* the desktop.

  One thing had to change to make it safe, and it is worth knowing before writing anything similar: **the focus
  handover has to be synchronous with the flag it follows.** It was an effect for one commit, which is correct for the
  cursor — an effect runs before the frame is composed, so the caret is never drawn in the wrong place. It is wrong
  for a keyboard: a batch of events is dispatched *before* the effects flush, so a Ctrl+O and the keystroke behind it,
  arriving together as a paste or fast typing do, would be routed by a focus that had not moved yet and the second key
  would reach the panels. `toggle_console` now moves the focus itself, and a test posts both events in one callback to
  pin it.
- ~~Which glyphs beyond a box frame the *library* widgets need.~~ **Answered: three vocabularies, and the third
  answer is the same for all of them.** `SCROLLBARS` is six characters — up, down, left, right, track, thumb, which is
  Turbo Vision's `TScrollBar.Chars` plus the thumb; `MARKS` is four — check off, check on, radio off, radio on, with
  the brackets around them fixed in the widget because they are ASCII in the original too; and `BOX_JOINS` is five
  tees keyed by *the frame's own name*, because a single rule meeting a double frame is `╤` and not `┬`, and
  `border: double` with `+` tees is a bug rather than a preference. Each has a lookup mirroring `charset()` and each
  collapses at the same lower boundary.

  **A Nerd Font improves on none of them.** Every shape is box-drawing, block-element or geometric-shape, all of
  which `GLYPHS_UNICODE` already guarantees; the Private Use Area carries icons, and an icon is a *replacement* for
  one of these rather than a better version — the one real candidate, a single-glyph check box, is refused because it
  collapses three cells into one and moves every caption in the cluster. `navigator/icons.py` remains the project's
  one deliberate departure and this is not a second.

### What the widget library needs first

**All four are now built**, and this list is kept as the record of what they were and in which order they unblocked
each other, because each one is cheaper than the last for reasons the previous one paid for. The markup language never
needed any of them — a `.nml` that declares a tree, binds geometry and carries a `style` block compiles onto what was
already here, and `Manager._place()` is the proof. A **widget library** needs all four, because a button, a dialog and
a pull-down menu are made of them.

1. **Focus — done.** `Application.focused`, `Widget.can_focus`, `Widget.focus()`, `Widget.focusable()` and
   `Application.focus_next()` are written and tested, and `dispatch_key` now walks the focus path instead of touring
   every descendant until one claimed the key; *Focus: one pointer, and eligibility decided at delivery* above is the
   reasoning. (4) did depend on this one, and cost one substitution because of it. (2) and (3) turned out not to — see
   *Emitting: a widget event walks up*, where a nested button takes a mouse press by position with no focus anywhere
   in the picture. What is left here is the application's own use of it: `Navigator.on_key` is still one central
   `if/elif` chain over a hand-rolled `Panel.active`, and `Manager.active_panel` is still what a focused widget would
   otherwise be. Converting those is `navigator`'s work, not navkit's, and nothing forces it before the panels have to
   compete with a dialog.
2. **Signals — done.** `Widget.emit()`, `Event.handler` and the `_handle` fallback are written and tested;
   *Emitting: a widget event walks up* above is the whole of the reasoning, and `navml/DESIGN.md` has the markup half
   it had to be settled with. Reactive attributes plus `effect()` stay the right answer for *state*; a signal is for
   the thing that has no state, "this button was pressed". Of the two events that still never reach a widget,
   `ResizeEvent` is answered by `layout()` already and `PasteEvent` is waiting on focus rather than on this.
3. **Mount and unmount — done.** `Widget.mounted`, `on_mount`/`on_unmount` with their empty events, the two walks and
   `reactive.dispose_effects()` are written and tested; *Mounting: joining a live tree, and leaving one* above is the
   reasoning. `add()` now lays a child out into a mounted parent, and `remove()` disposes the subtree's effects — which
   was a crash rather than a gap, since an eager effect reading `self.parent.width` raises at the flush that follows
   the detach and `Application._flush_effects` turns that into an exit. The binding half needed nothing: lazy cells are
   never evaluated while nothing paints them, and re-attaching invalidates the cached failure.
4. **Modal and overlay — done.** `Widget.modal`, `Application.modal`, `Application.overlay()` and the two rerouted
   dispatch paths are written and tested; *Modal and overlay: the input, not the painting* above is the reasoning.
   Z-order needed nothing — paint forwards, hit-test backwards already puts a dialog on top. Keyboard exclusivity cost
   one substitution, because (1) had made `dispatch_key` walk a focus path that a modal can be the end of. The mouse
   cost an actual reroute, routing by position rather than by focus. And the modal stack is maintained by (3)'s mount
   walks, so every way out of the tree gives the input back without knowing what a modal is.

A fifth, smaller — **done**: the cursor was unconditionally hidden (`Terminal.start` emits `HIDE_CURSOR` and
`render_diff` still never places one), so a text input had no caret except a reversed cell. `Widget.cursor_position()`
now says where one belongs, the application places it at the end of the frame for whichever widget the keys are going
to, and `caret` is a widget property the sheet can set to a DECSCUSR shape. *The cursor: shown where the keys go*
above is the reasoning. `navigator`'s console was converted with it: it takes the focus while it is showing and reports
the child program's cursor, so `Console.render`'s reversed cell is gone.
