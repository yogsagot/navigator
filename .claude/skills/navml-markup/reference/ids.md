## Ids

An id is a **name, never a value**, and both ancestors agree on that much. QML's docs are blunt about it — "it is not
possible to access `myTextInput.id`" — and Kivy deprecated
`Widget.id` through the 1.x line and removed it in 2.0.0, leaving only the `ids` dict. navml follows: a widget has no
`id` attribute, and there is no reverse lookup either (QML keeps one for C++, `qmlContext(o)->nameForObject(o)`).
Nothing needs one. An id exists so that one expression can name another widget in the same document, and that job is
finished at generation time. If a test or a debugger ever wants to name a widget at run time, that is a separate
reactive attribute on `Widget` — QML's `objectName`, which is a different thing with different rules — not this.

**In particular, an id is not a stylesheet selector.** `README.md` promises navkit a CSS-like stylesheet, and the
obvious reading of that is `#left` matching `id: left`. It does not: the lookup engine is navkit, which cannot depend on
navml and has nothing to match anyway, and a navml id is unique per document where CSS `#` presumes it is unique across
everything being styled. `#` matches `Widget.name`, an ordinary run-time property written in markup as
`name: "left-panel"` like any other. This is the same split Qt draws between a QML `id` and
`QObject::objectName`; `navkit/DESIGN.md` records it in full.

Where the two ancestors *disagree* is what an id compiles to, and there navml takes QML's side. QML assigns each id a
slot index in the instance's `QQmlContextData` at compile time, so a reference costs an array read. Kivy stores a
`WeakProxy` in a `DictProperty` and re-resolves the name out of that dict on every re-evaluation, because its compiled
expression is `eval`'d with the id map as its globals.

### What an id becomes

A plain instance attribute of the component, assigned in the generated `__init__`:

```
Panel:
    id: left
```

```python
self.left = Panel(parent=self)
```

Not a dict. Three reasons, in order of weight: the expression rewriter already emits
`self.left.width`, so an attribute is the form the compiled output wants anyway; the paired handler module writes
`self.left` by hand and gets completion and a rename for it; and a mistyped id fails as an `AttributeError` naming the
component, rather than a `KeyError` on a dict that could be anybody's.

The attribute holds the widget itself, not a weak proxy. Kivy needs `WeakProxy` because its
`ids` dict outlives the widget it names; a navml component owns its tree the way a QML context owns its objects and is
collected with it, so there is no cycle to break by hand. That also avoids Kivy's sharpest corner, where the key
survives the widget and `root.ids.gone` is a live entry holding a dead proxy that raises `ReferenceError` on any access.

Two consequences worth stating outright:

- **The id attribute is never reassigned after the generated `__init__` has run**, and that is what makes an ordinary
  safe. A binding compiled from `left.width` reads `self.left` and then subscribes to `Panel.width`: it tracks the
  panel's width, but *not* a replacement of
  `self.left`. QML does track its id slot — `captureProperty(context->idValueBindings(idx))` — because incremental
  creation can refill one. navml has no such moment.
- **Removing a widget from `children` leaves `self.left` pointing at it.** Deliberate: an id names a widget the document
  declares, not a position in the tree.

### Naming rules

Checked by the parser, each failing with the `.nml` line:

| Rule                                                   | Rejects                  | Why                                                        |
|--------------------------------------------------------|--------------------------|------------------------------------------------------------|
| a Python identifier, and not a keyword                 | `id: 2left`, `id: class` | it is emitted into generated source as an attribute name   |
| not one of the reserved words `self`, `root`, `parent`, `event` | `id: parent`       | each already means something in the resolution table below |
| not an attribute of the component's own class          | `id: width`              | it would be stored as `self.width` — see *Name resolution* |
| unique within the document                             | two `id: left`           | the second assignment would silently win                   |
| not a property or alias the document declares          | `id: console_visible`    | both become `self.<name>`, and the descriptor wins the tie |

The reserved-word row is the one both ancestors got wrong, in the same direction. QML checks id names against the
JavaScript globals but not against `parent`, so `id: parent` compiles and shadows `Item.parent` for a whole component
scope. Kivy rejects exactly `self` and `root` and silently shadows the rest — and shadows them *in opposite directions*
depending on context:
inside a property expression the globals overwrite the ids, inside an `on_*` handler the ids overwrite the globals. One
explicit list, checked once, in the parser.

Not adopted: QML's rule that an id must start with a lowercase letter. It exists to keep ids distinguishable from type
names, and navml distinguishes them by position — a type opens a block, an `id:` is a directive line indented under it —
so the rule buys nothing.

### Scope, order, and anonymity

**An id is scoped to its document.** One `.nml` file declares one component, and its ids are visible from every
expression in that file and from nowhere else. This is Kivy's per-rule boundary rather than QML's component scopes,
which chain upward so that a delegate can read names from wherever it happened to be instantiated. The reason is
mechanical rather than aesthetic: the compiled form is a closure over *one* component instance, and there is no
enclosing instance in scope to chain to.

**Order does not matter.** An expression may name an id declared further down the document.
The generated `__init__` constructs every widget before it installs any binding, and a binding body is not run until
the value, so a forward reference costs nothing.

**A widget without an id is anonymous, by construction.** It gets a local in the generated `__init__`, which dies when
that returns — the parent's `children` list is then the only reference to it:

```python
    def __init__(self, **kwargs: Any) -> None:
      super().__init__(**kwargs)
      _w1 = MenuBar(parent=self)
      _w1.width = _bind(lambda _o: _o.parent.width)
  
      self.left = Panel(parent=self)  # id: left
      self.left.width = _bind(lambda _o: _o.parent.width // 2)
```

No rule is needed to keep an un-id'd widget out of expressions: an id reference always compiles to `self.<id>` and never
to a bare local, so the widget is unreachable from any expression whether or not the local is still alive.

**Ids are live before any hand-written code runs.** The generated `__init__` assigns every id attribute before it
installs the first binding, and runs to completion during the component's construction — so there is no window in which
`self.left` is
missing. Kivy has one, which is why its ids are unusable from `__init__` and why 1.11 had to add `on_kv_post` after
years of
`Clock.schedule_once` folklore. The contract this puts on the still-undecided merge with the hand-written half is a
single line: the generated `__init__` builds the tree, and a hand-written `__init__` must call `super().__init__()`
before it touches an id. See *Building the tree* above for why that construction is not a `_build()` method.

