## Compiling a property expression

Everything to the right of a property's `:` is stored as source text:

```
Panel:
    width: parent.width // 2
```

`navkit.reactive.bind()` takes a callable of exactly one argument, called with the object that owns the attribute, so
the generator has to produce:

```python
self.left.width = _bind(lambda _o: _o.parent.width // 2)
```

`_bind` rather than `bind` because that is the name the generated preamble imports it under — every generated-code
example in this file spells the generator's own machinery with a leading underscore, and hand-written Python still
calls `bind`. *Importing another component* says why.

The bare `parent` in the markup is not a free variable there — it names something about the widget. Turning the text
into a lambda is therefore a *rewrite*, not a wrapping: string formatting would have to know which names in an arbitrary
expression refer to the widget, which refer to another object in the document, and which are ordinary globals like
`max`.

The rewrite is done on the syntax tree — `ast.parse(source, mode="eval")`, transform the free `Name` nodes, wrap the
result in a one-argument `ast.Lambda`, `ast.unparse` it into the generated class. A prototype of exactly this compiled
all eleven of the current
`Manager`'s bindings correctly, including the scoping corner cases below.

### Name resolution

Checked in this order. **The widget's own property wins**: a bare name inside a widget means that widget first, so
adding an `id` elsewhere in a document can never silently change what an existing expression refers to. An id that
collides with a property name is simply unreachable by a bare name from inside that widget.

| A free name in the expression                                                           | compiles to                                              | example                                                      |
|-----------------------------------------------------------------------------------------|----------------------------------------------------------|--------------------------------------------------------------|
| bound inside the expression itself — a comprehension target, a nested lambda's argument | left alone                                               | `e` in `', '.join(e.name for e in entries)`                  |
| `self`                                                                                  | the lambda's argument                                    | `self.width` → `_o.width`                                    |
| `root`                                                                                  | the component instance                                   | `root.left.width` → `self.left.width`                        |
| `parent`, or any reactive attribute the widget's class declares                         | an attribute of the lambda's argument                    | `parent.width` → `_o.parent.width`                           |
| an `id` declared elsewhere in the same document                                         | a closure reference to the component instance            | `left.width` → `self.left.width`                             |
| anything else                                                                           | left alone, resolved as a global of the generated module | `max`, `min`, and whatever the document imports              |

For the component's own expressions the fourth row includes the properties the document itself declares, which are on
no class until the generator has emitted one — see *Declaring a property* above. It includes aliases as well, in both
directions: the component's own, and those of a component used as a child. `declarations()` returns them, because an
alias is one of navkit's declarations — see *Aliases* above — so the rewriter needs no second source that could fall out
of step with the first.

That last row read "and whatever the paired handler module imports" until *The two halves of a component* was settled,
and the `__bases__` splice made it false: the two halves are separate modules with separate globals, so a compiled
expression cannot see what `button.py` imports and never could. *Importing another component* is what gives the document
back the capability the row promises, and the row now says so.

**Inside a handler body the same table applies, with one substitution.** The function's one argument is the event
rather than the owner — *The handler's one argument is `event`* below — so every row reading "the lambda's argument"
means instead the expression naming the owner in the enclosing `__init__`, `event` joins the first row as a name the
function itself binds, and nothing else moves.

Only the leftmost name of an attribute chain is rewritten: `parent.width` becomes
`_o.parent.width`, never `_o.parent._o.width`.

**An attribute the markup's expressions name has to be declared in the markup.** The `own` set is `declarations(base)`
plus what the document itself declares, and the hand-written half is not in it — that module does not exist when the
base is generated, and importing it would be a cycle. So a `reactive()` declared only in `button.py` falls through to
the last row of the table, compiles to a global of the generated module, and raises a `NameError` that lazy-and-cached
bindings surface at first read, arbitrarily far from the line that caused it. The rule is the cheap half of the fix and
costs nothing: a property markup reads is a `property` line. The other half the generator can afford whenever it is
wanted — `ast.parse` the sibling `.py` *without importing it*, collect the class-body `name: T = reactive(...)`
assignments, and report the collision at generation time with the `.nml` line. The hand-written half may still declare
whatever the markup never names.

`root` comes from Kivy and names the component the markup declares — the generated `self`, which is *not* what `self`
means in the markup. That is the one place where the QML/Kivy vocabulary and the generated Python disagree, so the
generator should never emit a bare
`self` for anything but the component.

Because the ids become attributes of the component, `root.<id>` also reaches an id that a widget's own property shadows:
inside a `Panel`, `cursor` is the panel's own property and
`root.cursor` is the widget declared with `id: cursor`.

**An id may not collide with an attribute of the component's own class**, and the generator has to reject one that does.
The component is a `Widget`, so `id: width` would be stored as
`self.width` — the component's own reactive width, silently broken rather than shadowed, and
`root.width` would read the geometry back instead of the widget. This is not a case the expression compiler can rescue;
it has to fail when the document is compiled, naming the line. The banned set is exactly `declarations(component_class)`
plus its ordinary attributes (`children`, `parent`, …).

### Worked example

The markup for the desktop `navigator/__main__.py` builds by hand today, matching
`Manager._place()` as it now stands:

```
from navigator.widgets.shell.console import Console
from navigator.widgets.shell.keybar import KeyBar
from navigator.widgets.menubar import MenuBar
from navigator.widgets.manager.panel import Panel

Manager:
    property console_visible: False

    MenuBar:
        id: menu
        x: 0
        y: 0
        width: parent.width
        height: 1
    KeyBar:
        id: keybar
        x: 0
        y: max(1, parent.height - 1)
        width: parent.width
        height: 1
    Panel:
        id: left
        x: 0
        y: 1
        width: parent.width // 2
        height: max(3, parent.height - 2)
        visible: not parent.console_visible
    Panel:
        id: right
        y: 1
        x: parent.width // 2
        width: parent.width - left.width
        height: max(3, parent.height - 2)
        visible: not parent.console_visible
    Console:
        id: console
        x: 0
        y: 1
        width: parent.width
        height: max(1, parent.height - 2)
        visible: parent.console_visible
```

The four import lines name a package that **now exists**: `navigator/widgets/`, one module per screen, with
`navigator/scheme.py` beside it holding the sheet those screens resolve against. They used to live in
`navigator/__main__.py`, and while `from navigator.__main__ import Panel` would have resolved, it would have resolved
to a *second* copy of the module `python -m navigator` is already running as `__main__` — so moving them out was the
prerequisite for any of this compiling, and it is done. The move also turned one implicit rule into a stated one:
`load_scheme()` imports `navigator.widgets.manager.panel` before it parses, because `navigator.nss` names the `icons` property
that class declares. That is a consequence of the import spelling rather than a cost of it: the
document says where its children come from, and saying it makes the problem visible at the top of the file instead of
at run time.

The three `visible` lines are the whole of Ctrl+O, and they are ordinary boolean expressions over a reactive attribute —
nothing about them needs a new language feature. What they do need is the `property` line above, which *Declaring a
property* settles. `Console(left)`'s constructor argument is the one hole the example still has, and it is the first of
the two left in the section after next.

and what the generator emits — verified output of the prototype, not an illustration, re-spelled only where *Importing
another component* later underscored the generator's own names (`bind` to `_bind`), which is a rename and changes
nothing the run established. Run against a real widget tree it
reproduces the geometry `navigator/__main__.py` produces by hand, at 80x24, 120x40, and 200x60. The prototype predates
the console, so the run covered the four widgets below and not the `Console` or the three `visible` lines; those compile
by the same rules —
`visible` is an ordinary reactive attribute and `not parent.console_visible` an ordinary expression — but they are
unverified, and the emitted block is left as it was actually produced rather than extended by hand:

```python
    def __init__(self, **kwargs: _Any) -> None:
      super().__init__(**kwargs)
      self.menu.x = 0
      self.menu.y = 0
      self.menu.width = _bind(lambda _o: _o.parent.width)
      self.menu.height = _bind(lambda _o: 1)
      self.keybar.x = 0
      self.keybar.y = _bind(lambda _o: max(1, _o.parent.height - 1))
      self.keybar.width = _bind(lambda _o: _o.parent.width)
      self.keybar.height = _bind(lambda _o: 1)
      self.left.x = 0
      self.left.y = 1
      self.left.width = _bind(lambda _o: _o.parent.width // 2)
      self.left.height = _bind(lambda _o: max(3, _o.parent.height - 2))
      self.right.y = 1
      self.right.x = _bind(lambda _o: _o.parent.width // 2)
      self.right.width = _bind(lambda _o: _o.parent.width - self.left.width)
      self.right.height = _bind(lambda _o: max(3, _o.parent.height - 2))
```

Note `x: 0` compiling to a plain `0` while `height: 1` compiles to a binding — that was the constant-size trap described
below, and the decision recorded there since supersedes it: with the generated class overriding `layout()`, `height: 1`
compiles to a plain `1` too. `self.left.width` in the last-but-one line is the id reference, resolved through the
closure over the component; every other name went to `_o`.

The `property` line compiles to neither of these but to a line of the generated *class body*, and is unverified for the
same reason the `Console` is — the prototype predates it:

```python
class Manager(_Widget):
    console_visible = _reactive(False)
```

The prototype was run against a widget tree that already existed, so what it emits is the property half of the generated
`__init__` only. The real generator constructs the four widgets first — see *Ids* — and construction being a separate earlier pass
is also why `right` may name `left`
regardless of which of the two the document declares first.

Two expressions written only to exercise the scope tracking, from the same run:

```python
  self.left.footer_text = _bind(lambda _o: ', '.join((e.name for e in _o.entries)))
  self.left.error = _bind(lambda _o: (lambda entries: entries)(_o.cursor))
```

The first keeps `e` a comprehension target while `entries` beside it becomes `_o.entries`. In the second the nested
lambda's argument `entries` shadows the property of that name, and the outer `cursor` still resolves to `_o.cursor`.

### Two things that fall out of the rule

- **A literal is not a binding — except for a size.** `height: 1` has nothing to depend on, so it is tempting to compile
  it to a plain assignment rather than a cell holding a constant expression. That is right for `x`, `y` and anything
  else, and *wrong* for `width` and
  `height`: `Widget.layout()` cascades the parent's size into every child whose size is not bound, so a constant size
  assigned plainly is silently overwritten on the first resize. This was measured, not guessed — compiling `height: 1`
  to an assignment gave the menu bar a height of 24 in an 80x24 terminal. `navigator/__main__.py`'s `bind(lambda w: 1)`
  is therefore not redundancy; the binding is what protects the constant.

  **This is the decision that was taken and the generator now depends on**: a generated class overrides `layout()` to
  size only itself, so a literal `width` or `height` compiles to a plain value like everything else and the trap does
  not exist for generated code. `navml/expression.py` reports `constant` and `rewritten` separately for exactly this
  reason, and `tests/test_nml_generator.py` pins that a `Button`'s caption is not bound to its height.

  The tidier fix belongs to navml rather than to the expression compiler, and it is now **decided**: a generated class
  overrides `layout()` to size only itself and does not cascade into its children, because a component whose children
  are all placed by markup does not want the inherited cascade at all. So a literal `width` or `height` compiles to a
  plain value like everything else, and the trap does not exist for generated code.

  Three things follow. `Widget.layout()`'s `is_bound` guard becomes a concern of hand-written widgets only — it stays,
  because they still need it, but nothing the generator emits relies on it. A markup child that says nothing about its
  size therefore *stays zero* rather than silently filling its parent, which is the honest failure: the size is missing
  from the document and the screen says so. And `Manager` already works this way, having no `layout()`
  at all, so the emitted shape matches the worked example below rather than departing from it.
- **A `computed` target is a generation-time error.** `Panel.title_text` is a `@computed`, and `Computed.__set__`
  refuses a binding. The generator knows the widget's class, so
  `title_text: …` in markup should be rejected with a line number instead of failing when the widget is first painted.

