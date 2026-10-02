## Declaring a style property

The other half of what a component declares about itself is what a *stylesheet* may say about it:

```
Panel:
    style_property icons: auto | none

    style:
        bg: $panel-bg
```

A stylable property is a declaration a sheet may make that `Style` has no field for — `border` being the first of them,
for the reason `navkit/DESIGN.md` argues at length — and navkit now takes it as a class attribute,
`icons = StyleProperty("auto", values=("auto", "none"))`. This directive is that line, and compiles to exactly it --
spelled `_StyleProperty`, like everything else the generator imports for itself.

`style_property` is a two-token head like `property` and `id`, so the directive rule stands unchanged; the underscored
spelling is what keeps it decidable against the `style:` block without lookahead, and it is the name it compiles to.

### The right-hand side is a `.nss` value, not a Python expression

This is the same boundary *The `style` block* draws below, and it is drawn for the same reason: what is being written is
what a sheet may say, in the grammar a sheet says it in. So a `$variable` is **not** meaningful here, which it is inside
that block — there is no sheet loaded when a class body runs, and a default that could not be resolved until one was
would be a different mechanism wearing the same syntax.

**The default's form is the type, and `|` narrows it further.** Nothing spells a type:

```
style_property icons: auto | none         # a keyword, one of two
style_property align: left                # a keyword, any
style_property margin: 0                  # a number
style_property scrollbar: true            # a flag
style_property indent: 2 | 4 | 8          # a number, one of three
```

The first alternative is the default and the rest complete the vocabulary. This is the inference `property` already
makes from *its* right-hand side rather than a second idea, it is what navkit's `StyleProperty` does with the default it
is handed, and it is what makes the directive useful beyond enumerations — a sheet saying `margin: wide` is refused
because the default is a number.

Deliberately not offered: a **range** (`0 .. 80`). A widget clamps a number it is given, the one property that might
want a range does not exist, and a spelling invented for a hypothetical case is one the `.py` half can carry instead.
**A value is required**, as for `property`, so there is no markup way to say "no default"; a property wanting one is
declared in the paired module — the escape hatch `equal=` already uses.

### Where it may appear, and what it may be called

**In the root block only**, and for exactly the reason `property` is: it emits a descriptor onto the class the root
block becomes, and every other block is an instance of a class that already exists.

The naming rules are `property`'s, with one addition. It may not collide with an `id` or an `alias` — `StyleProperty`
defines `__get__` *and* `__set__`, so it is a data descriptor and would beat the instance `__dict__` the same way
`Reactive` does. It may not shadow a base-class attribute, which now includes `Widget.border`; a component wanting a
different *default* frame is the one case where re-declaring is right rather than wrong, and navkit permits it
explicitly — two declarations of a name must agree on the vocabulary, not on the default.

One name is worth checking for in the paired module rather than in the markup: a component declaring `style_property
icons` and importing a module called `icons` has two of them a few lines apart. Python resolves it correctly — a class
body's names are not in scope inside its methods, so the global wins — which is what makes it a trap rather than an
error. `navigator/__main__.py` hit precisely this and renamed the import.

### What it asks of navkit

Nothing further. `StyleProperty` is there, it registers the name from `__set_name__`, and the parser checks both halves
of a declaration against what was registered. The one thing the generator inherits is **import order**: a sheet may only
be parsed once the widgets it styles have been declared, which is why `navigator/__main__.py` now parses its default
sheet on first use rather than at import. A generated module is imported before anything loads a sheet naming its
properties, so this costs markup nothing — but a sheet loaded by a plugin for a component nobody has imported yet will
fail with `unknown property`, and that is the honest failure rather than a silently dropped declaration.

