## The shared base, and how a value gets in

Three questions were open here and they turned out to be one mechanism: **whether every generated class shares a
base**, **how a component is handed a value from outside**, and **how markup says `_stylesheet`**. The first is
answered yes, and the other two are free once it is.

### Why there is a base: `navml.component.Component`

It holds three things, each of which the generator would otherwise repeat in every file it writes:

- **`layout()`**, which sizes the widget and does not cascade into its children — *Two things that fall out of the
  rule* below decided that, and it was byte-identical in all four hand-written stand-ins, which is the observation the
  argument for a base was waiting on.
- **`__init__`**, which is the whole of *How a value gets in* below. This is the one that turned the question from a
  tidiness argument into a blocker.
- **`__navml_source__`**, the document a class was generated from. *The two halves of a component* above says
  provenance had nowhere to live; now it has one, and `navml build --check` gains a run-time route to a stale
  generated half rather than only a file comparison.

**It is not a test of componenthood, and the asymmetry is visible outside Python.** It is true of a component written
in markup and false of one written in Python — `navml/widgets/spacer/spacer.py` is a component and is not a `Component` — so
it answers *built from markup* and may never be read as *is a component*. That was already stated above as a property
of any such test. What is new is where it shows: **`navkit.stylesheet._is_a` matches a type selector by class *name*
walking the MRO, so `Component { }` is a live `.nss` selector** with exactly that membership. Underscoring the name
the generator imports it under (`_Component`, like the rest of its machinery) does not hide `__name__` and nothing
can, so the name was chosen knowing it would be one. A sheet author reading `Component { }` should read *everything
written in markup*.

**The generator emits it unconditionally** — `class Label(_Component)` for a bare head, `class FramedButton(Button,
_Component)` for a named one. Not only when the head is bare, because a component derived from a *Python-only* widget
would otherwise inherit `Widget.layout` and cascade into children the markup placed. C3 puts it in one place however
deep the chain goes: `FramedButton, FramedButton, Button, Button, Component, Widget`, which `tests/test_navml.py`
pins. `_merge.py`'s `_check_bases` is unaffected — it constrains the *hand-written* half's bases, which stay single.

### How a value gets in

**A component's parameters are the properties it declares, and they arrive as keywords.** Markup has no parameter
list and grows none — the reason *The handler's one argument is `event`* gives holds here too, that a property line
and a directive line are the same shape and a parameter list is what would make them two. So:

```
Manager:
    property left_path: Path(".")
    property right_path: Path(".")

    Panel:
        id: left
        path: root.left_path
```

**That last line is wrong, and converting the desktop is what found it** — see *A property a widget navigates cannot
be bound* below. The mechanism it illustrates is right; the example should bind something the child does not itself
assign. Read it as `text: root.caption` and it says the same thing truthfully.

```python
Manager(left_path=a, right_path=b, stylesheet=scheme)
```

`Component.__init__` takes the names `type(self)` declares out of `**kwargs`, sets them, and hands the rest to
`Widget.__init__`. **That constructor is keyword-only and closed** — no `**kwargs`, eight named parameters — so
without this a component could not be given anything it declares at all, and a caller would have to construct first
and assign after. Three consequences worth stating:

- **A keyword naming no declaration still raises**, because it is left in `kwargs` and reaches the constructor that
  already refuses it. A typo fails at the call with the name in it, exactly as it does today.
- **They are set before the tree is joined, not after.** `Widget.__init__` finishes with `parent.add(self)`, which
  lays the widget out and runs its `mounted()`; a value assigned afterwards would arrive after the callbacks most
  likely to read it. The cells these writes create do not need `Widget.__init__` to have run — a cell belongs to the
  instance and is made on first touch.
- **The set of parameters is read off `Widget.__init__`'s signature**, not spelled in navml, so the two cannot drift.

QML's answer is that a component has no constructor and everything is a property; Kivy's is that `__init__` keeps
taking Python arguments. This is QML's, with Python's keyword syntax doing the work — and it costs no new language.
**A hand-written half may still take a positional argument if it wants one**: `navml/widgets/dialog/button/button.py` spells
`def __init__(self, text: str = "", **kwargs)`, which captures `text` before `Component` ever sees it. That is a
choice a component makes about its own call site, not something markup needs to know.

### A widget markup constructs takes no required constructor arguments

The other half, and a rule on the **library** rather than on the language: a child block compiles to
`Type(parent=self)` and nothing else, because markup sets every property *after* construction. So a type with a
required positional argument cannot appear in a document at all.

This was not written down anywhere and it was the sharpest blocker of the set: `Panel.__init__(self, path: Path)`
made `Panel(parent=self)` a `TypeError`, so the desktop conversion — the proof the generator exists to produce — was
unreachable. `Panel` now defaults its `path`, which is the reactive's own default anyway.

**What it costs is one scan against the default.** `Panel` starts a directory scan from an effect at construction, and
a value arriving afterwards — whether a markup binding or an assignment from the parent — reaches it only after that
scan has run. So the panel lists the working directory once before the real path arrives, and, because an effect is
flushed rather than run immediately, *it goes on listing it until the next flush*. That is a wasted scan rather than a
wrong answer — the application flushes before it paints, so the first frame is already right — and it is the honest
price of "construct, then bind", which is what a declarative tree does. A widget that cannot afford it takes the value
in its hand-written `__init__` instead.

### A property a widget navigates cannot be bound

The one thing converting `Manager` turned up, and it cost nothing to fix once it was named. **A markup property line
compiles to a binding, a bound attribute is read-only until something unbinds it, and `Panel.enter()` assigns `path`
every time the user descends a directory.** So `path: root.left_path` compiles, runs, paints the right listing, and
then raises `ReactiveError: Panel.path is bound to an expression` the first time somebody presses Enter.

The rule is about what the *child* does with the property, not about what the parent wants to say:

| the child | the parent may |
|---|---|
| never assigns it — `Label.text`, `Panel.visible`, every geometry line | bind it, and should |
| assigns it itself — `Panel.path`, a scroll offset, a cursor | give it a starting value, and only that |

A starting value is not something markup can say. Every line in a document is an expression that is re-evaluated, which
is the whole point of the language, and "once, then never again" is the opposite of that. So it stays in the
hand-written half: `manager.py` assigns `self.left.path`, `self.right.path` and `self.console.cwd` after
`super().__init__()` has built the tree, and `manager.nml` says nothing about any of them.

Three things were considered and not adopted. An **initial-value spelling** (`path =: root.left_path`, say) buys one
line and adds a second kind of property line to a language whose whole claim is that there is one. **Unbinding on
first write** makes `enter()` silently change what a document said, which is worse than refusing. And **making the
parent the source of truth**, so that `enter()` writes `root.left_path` back, asks the panel to know which side of the
desktop it is on — the panel owns its path, and that is the design rather than an accident of it.

### The sheet a component brings

`Manager.__init__` assigns a stylesheet so the desktop is styled with or without an application around it, and markup
had no spelling for it. It needs none: **the attribute was already reactive and only lacked a public name.**
`Widget._stylesheet` is now `Widget.stylesheet`, and a document assigns it like any other property —

```
Manager:
    stylesheet: default_scheme()
```

— while the computed that walks up to the nearest one becomes `effective_stylesheet`. That is the swap round the
right way: `Application.stylesheet` was already the settable sheet an *application* brings, so the widget-level name
now means the same thing one layer down, and the derived one is the one that says it is derived. **`stylesheet` is
what an object brings and is assigned; `effective_stylesheet` is what a widget resolves against and cannot be.** A
`style:` block remains a different slot again with different semantics, `inline_style`: one is a sheet governing a
subtree, the other a handful of declarations for one widget.

`Manager`'s `scheme or default_scheme()` does **not** become a markup line. A line on the root block compiles to an
assignment in the generated `__init__`, which runs *after* `super().__init__()` has applied the caller's keywords — so
it would silently clobber a sheet that was passed in. A default that depends on whether the caller supplied one is
logic, and logic is the hand-written half's, which is the split this file rests on everywhere else.

