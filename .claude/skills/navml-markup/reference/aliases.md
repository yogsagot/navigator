## Aliases

Ids stop at the document, so markup that uses a `Panel` component cannot name anything declared inside `panel.nml`. A
component says for itself what crosses that boundary:

```
Panel:
    alias title: header.text

    Label:
        id: header
```

`alias` is a directive line with a two-token head, like `property`. QML spells it
`property alias title: header.text` and navml does not, because the second token slot is empty *on purpose*: the type
was dropped from `property bool consoleVisible: false` to keep one line's colon doing one job, and refilling that slot
with a word that is not a type would undo the reason it is free. `alias` standing alone reads as the third member of
the `id:` / `property` family, which is what it is.

Kivy has no answer at all, which is exactly why Kivy code reaches through `outer.ids.child.ids.grandchild` and the
boundary ends up meaning nothing. What separates the two is not how far a name can reach — chained aliases reach as far
as anything — but that every hop here was declared by the component it crosses.

### What an alias becomes

A line of the generated class body, as `property` is, but carrying a descriptor of navml's own:

```python
class Panel(_Widget):
    title: str = _Alias("header", "text")
```

`__get__` and `__set__` forward by `getattr` and `setattr` to `<id>.<attribute>`, and that is the whole mechanism.
Everything correct about it falls out of the *target's* descriptor doing the work rather than this one:

- **Reads are tracked.** navkit captures a dependency at the moment of the read, against whatever binding is on its
  stack, keyed by the cell — it never asks whether the read went through an attribute of the reading object, and it
  subscribes outside the memoisation, so even a cached value subscribes. A forwarded read is an ordinary read of
  `Header.text` that happens to sit a few plain Python calls deeper, so an expression mentioning `panel.title`
  invalidates when `header.text` changes.
- **Writes keep their semantics.** The value is type-checked against the *target's* annotation, refused if the target
  holds a live binding, and propagates to dependents normally.
- **A write from inside a `computed` is still refused**, because navkit asks that question of its stack rather than of
  ownership. The number of forwarding hops is irrelevant to it.

`_Alias` **subclasses navkit's declaration base** and overrides `cell()` to return the target's cell. That is not
decoration — forwarding alone would leave the alias a descriptor navkit knows nothing about — and it buys four
things:

- `unbind()`, `is_bound()` and `peek()` work through the alias. Each names an attribute by its class declaration —
  which is this descriptor — and navkit refuses anything that is not one of its own.
- `declarations(cls)` returns aliases, so the `own` set the expression rewriter checks is one function rather than two
  that have to stay in step.
- An alias that *shadows* an inherited reactive attribute is reported correctly. `declarations()` walks the MRO keeping
  what it sees first, but sees only its own declarations — so a plain descriptor shadowing a base class's `reactive`
  would be walked straight past and the shadowed one returned in its place. That answer is not incomplete, it is
  **wrong**, and a generator trusting it would emit code against a cell nothing ever reads.
- An annotated alias carries a declared type, which is what the still-open `.pyi` question will want. Annotate every
  one the generator emits: the type is resolved by walking the declaring class's MRO for the name, so an unannotated
  alias silently inherits the annotation of whatever it shadows — and since the alias verifies nothing itself, that
  type is advisory and can disagree with the target's without anything noticing.

Both routes end at the same cell, so forwarding by attribute access and `cell()` pointing at the target cannot
disagree about anything.

### A binding through an alias is re-owned

`bind()` calls its expression with the object that owns the attribute, and after forwarding that object is the
*target*. So this:

```
Panel:
    id: p
    title: self.width * 2
```

compiles by the ordinary rules to `_o.width * 2`, in which `self` meant the `Panel` — and the expression is handed the
`Label`. A `Label` has a `width` too, so nothing raises: it computes the wrong number and goes on computing it. That is
the worst shape a binding failure can take, and it is why this is a section rather than an implementation detail.

`_Alias.__set__` therefore re-wraps a `Binding` before forwarding it, so the expression keeps being called with the
object the markup was written against:

```python
if isinstance(value, Binding):
    expression = value.expression
    value = bind(lambda _t, _o=obj: expression(_o), equal=value.equal)
```

In the descriptor rather than in the generator, for two reasons. It then holds for hand-written Python too, where
`panel.title = bind(lambda p: p.width)` means the panel to whoever typed it. And it composes: the wrapper ignores its
own argument, so an alias into a component that aliases further in re-wraps an expression that is already owned, and
the outermost object wins rather than the innermost. The expression has to be lifted into a local first: closing
over `value` while rebinding it on the same line gives a wrapper that finds itself at call time and recurses.

This was measured rather than argued — argument identity, recompute on a property of the aliasing widget, the value
landing on the target with no stray cell left on the component, `unbind()` through the `cell()` override, and `equal=`
surviving the re-wrap.

**It makes `bind()` mean something different at an alias**, and deliberately: one cell hands its expression a different
object depending on which name the binding was installed through. An alias exists to make the target's location
unobservable, and the argument is part of that location. It is stated beside the one-argument convention as well as
here, because a hand-written caller meets it without having read this section.

The strong reference the re-wrap adds — the target's cell holds the expression, which holds the aliasing widget — is
the same cycle `Widget.parent` and `Widget.children` already form for every attached widget pair, between two objects
that live and die together, and the collector breaks it exactly as it breaks those. What the weakrefs inside navkit's
cells protect is the other direction, a long-lived widget not retaining a dead one through its subscriber set, and
nothing here touches it.

### Depth, and what is deliberately not offered

**Exactly one property deep.** `alias title: header.text`, never `header.child.text`. Chaining is how reach goes
further, and the rule is what makes the difference from `outer.ids.child.ids.grandchild` real: each hop is an export
that the component in the middle declared, rather than a reach-through it never agreed to.

**An alias to a widget is not offered**, and the deferral this paragraph used to end on is now discharged. QML has
one — `property alias headerItem: header` — and it hands the widget out whole, which recreates the reach-through with
one extra step and no further declaration. It would also be a declaration with no cell of its own, which `unbind()`
and `is_bound()` could not answer for. The case that wanted it was naming an inner button in order to connect a
handler to it, and **that case has evaporated**: an emitted event walks up, so an outer document handles a click from
a button it cannot name. See *This settles the widget-alias question, and settles it as no* below.

### Where it may appear, and what it may be called

**In the root block only**, for the reason `property` is restricted there: it becomes a descriptor on a class, and the
root block is the only block in a document that becomes one.

An alias declares a name on the component, so it joins the `self.<name>` namespace the ids and the declared properties
share, and takes those rules entire — not colliding with an id, not colliding with a declared property, not shadowing
an attribute of the component's base class.

### Checked when the document is compiled

Each failing with the `.nml` line:

- The target's leading name is an **id declared in this document**, and not `self`, `root`, `parent` or `event`,
  which name things that have no stable meaning from the other side of the boundary.
- The attribute **resolves to a reactive declaration** on that id's class. A plain attribute is rejected rather than
  allowed through: a `bind()` forwarded onto one is silently stored, there being no descriptor to notice it, and the
  author reading the outer document cannot see the target's declaration to work out why nothing happened.
- A target that is a **`computed` makes the alias read-only**, classified here rather than left to fail when the widget
  is first painted. navkit's own refusal is intelligible but names the target, and its advice — declare it reactive —
  is addressed to somebody who can edit the target's class, which the outer author usually cannot.
- A **self-referential alias is rejected**. It yields a `RecursionError` rather than navkit's `CycleError`: the cycle
  detector sees cells, and an alias has none of its own to be seen.

### Three things an alias cannot carry

Each reads as an oversight until it is written down.

- **An initial value.** There is no slot for one and there could not be: the cell it would fill belongs to a widget
  that does not exist until the generated `__init__` has run. A component wanting one assigns it there, like anything
  else.
- **An `equal=`.** It has no cell to put one on. The `equal=` question left open below would otherwise be asked at a
  third site, and this is why it is not: on an alias, never — the comparator belongs to the component that owns the
  target, which is the only side that knows what the value means.
- **A useful error location.** Every message navkit raises names `Header.text`, an attribute that does not appear in
  the document its reader is looking at. `_Alias` should catch and re-raise naming both ends, and carry a `__repr__`
  reading `<alias Panel.title -> header.text>`, so that the three functions which reject a non-declaration say
  something legible when they do.

