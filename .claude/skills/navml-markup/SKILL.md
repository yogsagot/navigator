---
name: navml-markup
description: Writing or editing a `.nml` markup document in navml/ or navigator/ -- its imports, ids, property and style-property declarations, aliases, `event` lines, property expressions, `style:` and `keys:` blocks, one-line handlers and `on_<id>_<event>` methods -- and rebuilding with `python -m navml build --check`.
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
  one-argument lambda `bind()` expects).
- **A property a widget *navigates* cannot be bound.** A bound attribute is read-only until unbound, so
  `path: root.left_path` paints and then raises the first time `Panel.enter()` assigns `path`. Markup cannot say a
  starting value: seed it in the hand-written `__init__` after `super().__init__()` (`manager.py` seeds `left.path`,
  `right.path`, `console.cwd`).
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
