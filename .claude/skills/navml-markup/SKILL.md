---
name: navml-markup
description: Writing or editing a `.nml` markup document in navml/ or navigator/ -- its imports, ids, property and style-property declarations, aliases, `event` lines, property expressions, `style:`, `keys:`, `anchors:` and `when` blocks, one-line handlers and `on_<id>_<event>` methods -- and rebuilding with `python -m navml build --check`.
---

# Writing navml markup

`*.nml` is QML for the architecture (a declarative tree, `id`s, properties that are re-evaluated expressions) and Kivy
for the syntax (blocks made by indentation, no braces, no semicolons, one property per line). How a component's two
halves fit together, and how the parser and generator work, is the `navml-components` skill.

**After editing any `.nml`, regenerate**: `./venv/bin/python -m navml build navml navigator` (both packages must be
named; the bare form builds only the installed `navml`). `--check` exits 1 when markup no longer matches its generated
half. A generated file is only ever overwritten if its first line is `# navml: generated`.

## Lexical rules (the parser's)

- **Blocks are made of spaces**; a tab is an error.
- **A logical line continues only while a bracket is open** -- Python's implicit continuation and nothing else.
- **`#` opens a comment only when a space, an end of line or a `:` follows it**, because `#rrggbb` is a colour inside
  a `style:` block. A `#:` run above a declaration is captured and re-emitted by the generator.
- **The root block takes no `id`** -- it is `root` in every expression already.

## Types and imports

- A document says where its types come from in Python's own words -- `from navml.widgets.dialog.label import Label` at
  the top, copied into the generated module verbatim. `import *` and `__future__` imports are refused. Any import is
  legal and worth taking: a declared type is only checked at run time if the generated module can resolve it, and a
  `style:` block can only be validated against a property whose widget has been imported.
- **Write a bare `Button:` to extend `Widget`, never `Button(Widget):`.** The parenthesised form names a type, and a type
  a document names is one it imports. The hand-written half still spells `class Button(Widget)`.
- **A widget markup constructs must take no required constructor argument** -- a child block compiles to
  `Type(parent=self)` and nothing else (which is why `Panel.path` has a default).
- **Everything the generator emits for itself is underscored** (`_bind`, `_reactive`, `_Widget` ...), so it reserves no
  word. The language reserves `self`, `root`, `parent` and `event`; an import named `event` is rejected.

## Properties

- A component's parameters are the properties it declares, arriving as keywords; `Component.__init__` sets them before
  `Widget.__init__` joins the widget to its parent. An unknown keyword still raises.
- A property line compiles to a binding (an expression's free names are rewritten on the syntax tree into the
  one-argument lambda `bind()` expects). A line that reads nothing of the widget tree is evaluated once -- **unless it
  reads an imported module or instance** (`SETTINGS`, `country`; `expression.followed_imports`), which can change
  under it: `visible: SETTINGS.interface.clock` is bound. An imported class, function or immutable value is not
  followed (`command: RestoreTrash`, `height: LIMIT` stay plain), nor is a root `property` declaration (still a
  factory) or a plain attribute that cannot follow a binding.
- **Markup cannot import from its own hand-written half** (a circular import); give the `.py` a method the line calls
  (`text: ... if root.trashing() else ...` in `delete_dialog.nml`). `tr()` in a markup line is not seen by
  `tools/i18n.py extract`: put the call in a method too (`CountryPage.example_text`).
- **A property a widget *navigates* cannot be bound.** A bound attribute is read-only until unbound, so
  `path: root.left_path` paints and then raises the first time `Panel.enter()` assigns `path`. Markup cannot say a
  starting value: seed it in the hand-written `__init__` after `super().__init__()` (`manager.py` seeds `left.path`,
  `right.path`, `console.cwd`).
- **Captions are translated**: a string literal of `text`/`title`/`label_text`/`items`/`prompt` compiles to
  `_bind(lambda _o: _tr('...'), yielding=True)` -- live on a language change, and replaced (not refused) by a later
  assignment from Python. Other properties' strings (`key:`, `history_id:`, `after:`) are names, never translated
  (`i18n` skill).
- `equal=` is not expressible in markup (a comparator is a function); declare such a property in the hand-written half.
- markup assigns a component's own `stylesheet` like any other property (`stylesheet` is what an object brings,
  `effective_stylesheet` what it resolves against).

## Handlers and events

- **A handler is one line taking one argument called `event`.** Anything longer is a method in the hand-written half
  that the line calls (`on_click: self.confirm_quit()`). It compiles to a one-statement `def` closing over its widget
  (not a lambda -- `on_key: self.title = event.key` is an assignment), and **always ends `return True`** (consumes).
- **Every `on_*` handler is `async def`**; navkit refuses a synchronous one, and `check_handlers` enforces it on both
  halves at build time.
- **A child's event reaches the hand-written half as `on_<id>_<event>`.** For every id'd child and every event its class
  `emits`, the generated class declares a no-op handler returning False and assigns it
  (`self.cancel.on_click = self.on_cancel_click`); the `.py` overrides it. A stub nobody overrides declines, so the
  component's own `on_click` still catches the rest. An explicit `on_click:` line on that child suppresses the
  convention, and the method such a line routes to is **never** named `on_*` (it would be called twice by one walk).
  The generator refuses an `on_<X>_<event>` whose `X` names no id (a renamed id would orphan it).
- **An event is declared by the half that emits it.** Python: `class ClickEvent(Event)` beside the widget plus
  `emits = (ClickEvent,)`. Markup: `event ClickEvent` (root block only, no fields), which puts the class in the
  generated module -- so the hand-written half may never name it. Never both.

## Blocks

- `style:` -- a `.nss` declaration set, checked at build time (`stylesheet.check_declarations`), `$variables` left for
  run time.
- `keys:` -- the component's key table (root block only), as a class attribute `keys = {...}` would be.
- `anchors:` -- where the widget sits, as edges. See *Anchors* below.
- `when COND:` -- lines that differ while a condition holds. See *When* below.

## Anchors

An `anchors:` block is build-time sugar (`navml/anchors.py`, called from `parse()`). It becomes the `x`/`y`/`width`/
`height` property lines you would otherwise write by hand, so nothing at run time knows anchors exist and the generated
code is the familiar `max(0, parent.width - 12)`. Prefer it to hand arithmetic for the common idioms.

| Key | Means | Writes |
|---|---|---|
| `left: L` / `top: T` | inset from the parent's start edge | `x = L` |
| `right: R` / `bottom: B` | inset from the parent's end edge | alone: `x = max(0, parent.width - R - self.width)` |
| `after: id + G` / `below: id + G` | G cells past a sibling's end edge | `x = id.x + id.width + G` |
| `before: id + G` / `above: id + G` | G cells short of a sibling's start edge | alone: `x = max(0, id.x - G - self.width)` |
| a start and an end edge on one axis | stretch between them | `x` from the start, `width = max(0, END - ...)` |
| `fill: N` | all four insets; a named edge on a side wins | |
| `center: horizontal` / `vertical` / `both` | centre in the parent | `max(0, (parent.width - self.width) // 2)` |

- An end edge alone **keeps the widget's own size** and pins against it, so a content-sized widget (the clock) works.
- **A sibling form may list ids**: `before: macro_mark, root_mark, clock + 1` sits against the first one *shown*
  (`visible` and a non-zero size on that axis), with one gap for all.
- **A bare id in an expression loses to the widget's own property of that name**: under a `Label`, `text` is its
  caption even with a sibling `id: text`. Write `root.text` there. Anchors always do (`root.<id>`).
- **A sibling form plus a parent edge on the same side makes the parent edge its fallback**, used when no listed
  sibling is shown: `before: options + 1` with `right: 1`. Without a fallback, the last id is sat against
  unconditionally. A lone id with no fallback is the plain `a.x + a.width + G`, with no visibility test.
- **A written `x:` plus an end edge stretches the width from it.** This is for a start no edge can say
  (`x: menu.item_span(...)[0] + 1` in the Shell's window strip).
- Values are ordinary expressions (`right: 2 + root.gap`). A sibling form is an id, optionally `+ gap`.
- **Refused at build time**, with the line:
  - an anchor plus an explicit `x:`/`y:` line on that axis;
  - a stretching pair plus an explicit `width:`/`height:` line;
  - two parent edges, or two sibling forms, on one side of an axis; one id named twice in a list;
  - `center` (or `fill`) together with an edge on a centred axis;
  - a sibling form naming an id that is not under the same parent, or used on the root block;
  - anchors on a child of a `Layout`, which owns its children's geometry (`checks._check_anchors`).
- **Mixing is fine.** Anchor one axis and write the other (`dialog.nml`'s message anchors `left`/`right` and keeps
  `height: max(1, ...)`).
- **Anchoring makes a side a binding.** A Python half that re-places an anchored widget must `unbind()` first, exactly
  as before.
- **Convert only where the generated value is unchanged.** Every anchor clamps at 0; a line with another floor
  (`max(1, ...)`) stays an expression.

## When

`when COND:` inside a widget holds property lines and at most one `anchors:` block. While COND holds, the widget is
as if those lines replaced its own (`navml/states.py`, in the same pass as anchors). It is QML's *States*, kept small.
It is how a page reflows when narrow (System setup, Volumes: `when parent.width < 67:`).

- **A property line replaces the widget's line of that name.**
- **An anchor line replaces the widget's anchors on the sides it names.**
  - Sides: `left`/`after` the horizontal start, `right`/`before` its end, `top`/`below` and `bottom`/`above`
    likewise.
  - A `center` loses any axis the block puts an edge on.
  - `fill` stays the default for any side the block leaves alone.
  - So `bottom: 6` under a widget anchored `top: 1, bottom: 4` still stretches it.
- **The widget and each variant are expanded alike**, so every anchor rule holds per variant. A differing line
  becomes `(variant) if (COND) else (own)`. Several blocks: the first whose condition holds wins, in document order.
- **Refused, with the line:**
  - a variant giving a property the widget has no line for (nothing to fall back on while COND is false);
  - a block with no condition, or one that says nothing;
  - an id, handler, declaration, child, `style:`/`keys:` or nested `when` inside it;
  - a property written twice in one block.

`when` is a keyword: no property or id may be called that. Model documents refuse it.

## Model documents

A root extending `navkit.database.Model` with `field name: type [= literal]`, `index name: a, b` and
`unique name: a, b` lines (root only) declares a table, not a widget: `navml/model.py` builds it, and refuses
children, handlers, `style:`/`keys:` and the widget directives. The `navkit-database` skill has the grammar and the
rules.

## Read when

| Reference | Read when |
|---|---|
| `reference/imports.md` | adding imports, a bare head vs `Name(Base):`, what the generator checks on a type, cold build order |
| `reference/ids.md` | what an id becomes, naming rules, scope and anonymity |
| `reference/properties.md` | declaring a property: where the line lands, naming, what the generator does |
| `reference/style-properties.md` | declaring a style property (`.nss` value on the right-hand side) |
| `reference/aliases.md` | property aliases, re-owned bindings, what an alias cannot carry |
| `reference/events.md` | `event` lines, `on_<id>_<event>` stubs, what a handler line is checked for |
| `reference/expressions.md` | how a property expression compiles, name resolution, the worked example |
| `reference/blocks-and-handlers.md` | `style:` / `keys:` blocks, handler bodies, the `event` argument |
| `reference/anchors.md` | why anchors are sugar and not QML's run-time anchors, what is not offered yet |
