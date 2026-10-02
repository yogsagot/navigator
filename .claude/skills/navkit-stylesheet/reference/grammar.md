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

