## Declaring a property

A document may add a reactive attribute to the component it declares:

```
Manager:
    property console_visible: False
```

`property` is a directive line like `id:`, told from an ordinary assignment by its two-token head. The `:` goes on
meaning what it means everywhere else in the file — name on the left, value on the right — which is why the
Python-flavoured `property console_visible: bool = False` loses: it would give one line's colon two jobs. QML's
`property bool consoleVisible: false` keeps the colon honest and is where the word comes from; navml drops the type
and the slot stays free if it is ever wanted.

navkit *does* check one now — a reactive attribute is checked against the annotation written beside it, see *Declared
types* in `navkit/DESIGN.md` — so what a typeless `property` generates is a declaration with no annotation, which that
layer leaves unchecked. That is the right default rather than a gap: an attribute the document declares is written and
read by that document and its paired handler module, where a wrong type is a local mistake, and the generator has no
type to emit until the language has a spelling for one. What changed is the cost of adding the spelling later: it is
now one annotation on the emitted line and the check follows, rather than a run-time mechanism that would have to be
built first.

The word is deliberately the one this file already uses for every `name: value` line. That overload is QML's too —
everything is a property, `property` declares a new one — and the alternative, `reactive`, would leak the name of the
machinery into a language that otherwise never mentions it. Python's `@property` is the *opposite* thing, a computed
rather than a source, which is the one real cost; navml is not Python and its `:` lines already are not, so it was
judged smaller than either alternative.

### Where the line lands

The class body always gets the declaration, because that is where a descriptor has to live:

```python
class Manager(_Widget):
    console_visible = _reactive(False)
```

Without it, `self.console_visible = _bind(...)` would store a `Binding` on an ordinary attribute and do nothing, there
being no descriptor to notice it — the failure whose only symptom is the `<unassigned binding ...>` repr.

What varies is whether a second line joins it in the generated `__init__`, and the test is **whether the expression reads anything
reactive** — precisely whether the rewriter of the next section rewrote any free name:

| The right-hand side  | rewritten? | compiles to                                                                  |
|----------------------|------------|------------------------------------------------------------------------------|
| `False`, `0`, `None` | no         | `console_visible = _reactive(False)`                                         |
| `[]`, `Path(".")`    | no         | `entries = _reactive(factory=lambda: [])`                                    |
| `self.width // 3`    | yes        | `w = _reactive()`, and `self.w = _bind(lambda _o: _o.width // 3)` in `__init__`|

So a declared property may be derived, and `property first_column_width: self.width // 3` is one line rather than two.
The test costs the generator nothing: the expression compiler already knows whether it touched a free name, so the
answer falls out of a pass it runs anyway. It is the same rule as *A literal is not a binding* below, asked at the
declaration site.

The second row over-applies `factory=` on purpose, and the one case in the repository shows it: `Panel.path` is a plain
`reactive(Path("."))` today, an immutable default instances can safely share, and markup generates a factory for it
instead. The two are indistinguishable through the equality guard, and erring this way costs one object per instance
where erring the other way costs a shared mutable.

**Not "a constant is a default, everything else is a binding".** That is the obvious rule, and it is wrong in a way
worth recording so it is not tried again. `property entries: []` is not a constant, and compiling it to a binding would
leave `entries` a live bound cell — over which navkit refuses a plain assignment, so `Panel`'s scan effect could never
write `self.entries = ...` again. A list display reads nothing, so it is an initial value; `factory=` is what stops the
instances sharing it, and it is inferred rather than spelled for exactly this pair of cases. `equal=` gets no spelling
at all: nothing in the repository needs one, and a property that does is declared in the paired hand-written module,
which is the escape hatch that makes an incomplete `property` acceptable.

**A bound property is read-only until something unbinds it.** The third row's consequence, stated here rather than
discovered later: the hand-written half cannot assign `first_column_width` without calling `unbind()` first. That is
the trade every bound attribute in the repository already makes, and the honest reading of having written a derived
expression. It is still the right form rather than a `computed`, which fixes one function on the class; a binding
belongs to one instance and can be replaced or taken back.

**A default *and* a binding still take two lines** — `property width_hint: 0`, then `width_hint: parent.width // 2`
lower down. Only the derived case stopped needing them. The two-line form remains for the case where the initial value
is genuinely observed before the binding is installed.

**A value is required.** `property console_visible` alone is rejected rather than quietly meaning `reactive(None)`.

### Where it may appear

**In the root block only.** `Reactive` is a descriptor installed on a class, and the root block is the only block in a
document that becomes one — every other block is an *instance* of a class that already exists, so a `property` under
it would have to synthesise a per-document subclass. One under a child is rejected with its `.nml` line, pointing at
giving that child a document of its own or declaring the attribute in the `.py` half. Nothing is lost today: every
declaration `navigator/__main__.py` carries — `Manager.console_visible`, `Console.revision` and `Panel`'s seven — is
on a class that becomes some document's root.

The ancestors sit on either side of this. QML allows a `property` on any object, because there an object carrying one
becomes its own anonymous type. Kivy allows it nowhere: a `.kv` file declares nothing, the properties live in the
Python class and the markup only assigns them — which is the hole this section fills.

### Naming rules

Everything the id rules say, and one more, each checked by the parser with the `.nml` line:

- **A property may not collide with an id, nor with an alias.** Both become `self.<name>`, and `Reactive` defines
  `__get__` *and*
  `__set__`, so it is a data descriptor and beats the instance `__dict__`. The generated `__init__`'s
  `self.left = Panel(parent=self)` would therefore write the panel *into a reactive cell* rather than shadow the
  declaration — wrong, and silently so. An alias collides more simply, both being lines of the same class body: the
  second name would overwrite the first outright.
- **A property may not shadow an attribute of the component's base class**, reactive or not. `property width: 0` on a
  `Manager` re-declares `Widget.width` with a fresh cell, and `property title_text: ...` on a `Panel` collides with a
  `Computed` that *A `computed` target is a generation-time error* already rejects from the other side. The banned set
  is the one the id rules name: `declarations(base)` plus the ordinary attributes.

### What the generator has to do about it

Declared properties join the `own` set the expression rewriter checks. The table under *Name resolution* reads "any
reactive attribute the widget's class declares", and for the component's own expressions that class does not exist yet
— so the generator collects declarations in a first pass and compiles expressions in a second. Construction is already
a separate earlier pass, so this is one more table filled before an existing one rather than new structure. A
declaration's own right-hand side is compiled in that second pass like everything else, which is what makes
`property first_column_width: self.width // 3` safe: `self` resolves to the component, and the cell is lazy, so nothing
is read while the class is still being built.

One knock-on, flagged rather than solved: a binding installed in the generated `__init__` lands *after* the children are
constructed,
and `Panel.__init__` starts a directory scan from an effect at construction — so a `Panel` whose `path` came from a
component property would scan once against the default before the binding arrives. That is the *Component parameters*
question under *What converting `Manager` needs and does not have*, which this decision makes reachable without
answering.

This asks navkit for nothing: `reactive()` is callable in a class body, and that is the whole requirement.

