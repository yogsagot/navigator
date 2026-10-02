## Reading a document

The parser answers *what does this document say*, and the code generator answers *what Python does it become*. The
line between them is one rule: **the parser imports nothing the document names.** It never resolves a type, never
touches a live class, never calls `declarations()` or `emitted()` or `declared_property()`. Every check it makes is
one a document can fail on its own.

That is a correction as much as a decision. The tables above say "checked by the parser" in places where the check
needs a class object — *Naming rules*' third row, "not an attribute of the component's own class", wants
`declarations(base)`, and the `style:` block's property names want a registry that `StyleProperty.__set_name__` only
fills when a class body has run. Those are the generator's, which *The cold build* already requires to import. What
the split buys is two things worth having: the parser is testable with no widget tree, no application and no
components at all, and `imports_of()` is cheap enough for `navml build` to order a whole directory by its import
graph without executing any of it — which is precisely the cold build's problem, a document whose imports name
components that have not been generated yet.

So the two halves of the checking read:

| the parser | the generator |
|------------|----------------|
| structure — one root block, imports before it, a directive in the root block only, a value on every declaration, an indented line under a leaf | every type a document names resolving against what it imports |
| names — a Python identifier, not a keyword, not `self`/`root`/`parent`/`event` | an id, a property or an alias shadowing an attribute of the component's base |
| collisions the document has with itself — id against id, id against declaration, two assignments of one property, two handlers for one event | a `computed` target, an `on_*:` line against `emitted()`, a handler line against the class that already implements it |
| the shape of an `alias` target, and the form of a `style_property` vocabulary | a `style:` block's property names and values, against `Style`'s fields and the registry |
| | everything that needs the sibling `.py` parsed, and everything the expression compiler decides |

### Comments: `#` and a space, `#:` and a declaration

`.nml` takes Kivy's `#`, with one wrinkle that is not a matter of taste. **A `#` opens a comment only when a space,
an end of line, or a `:` follows it.** `#1e1e2e` is a value, not a comment, because a `style:` block is written in
the `.nss` value grammar and `navkit/stylesheet.py`'s `_HEX` makes `#rrggbb` a literal there — so `bg: #1e1e2e`
would otherwise be shortened to `bg:` and fail as a declaration with no value, for a reason nothing in the line
suggests. The rule costs `#comment` written without a space, which is a smaller loss than a colour that cannot be
written at all — and smaller than it first looks, because **the right of a property's `:` is Python, whose own
reader takes `#` as a comment however it is spaced.** So `width: 1 #comment` is unharmed either way and loses the
comment at the generator's `unparse`; the rule earns its keep in the one place the right of a `:` is not Python,
which is the `style:` block.

**The stripping is string-aware, and has to be.** The right of a `:` is Python, where a `#` inside a literal is not
a comment: `text: "# 1"` keeps its hash, and so does `f"{d['#']}"`, which the scanner gets right by never leaving a
string until that string's own quote closes. A regex over the file would be wrong in both cases. This is why the
scanner walks the line rather than matching it.

**`#:` is a doc comment**, and a run of them directly above a declaration is captured and carried on the node.
Every declaration this file moves into markup carries one in `navigator/__main__.py` — `Panel`'s seven,
`Console.revision`, `Manager.console_visible` — and without a spelling the reason a property exists is lost in
translation. A blank line ends a run; an ordinary `#` line does not.

### An expression continues inside brackets, and nowhere else

**A logical line continues while a bracket is open, which is Python's own implicit continuation and the whole of
it.** No indented continuation, no trailing backslash. This settles the half of *Multi-line property bodies* that
survived *A handler body is one line*, and it settles it the way that section's own argument points: an indent goes
on meaning exactly one thing, a block, so there is no second question about what a line under a property line is.
Nothing changes about what is emitted — still a one-argument lambda — which is why this was the parser's to decide.

What it refuses is the Kivy form, an expression spread over lines indented under its property. The message says so,
and for a handler it names the component's `.py` file instead, because a handler body that has outgrown one line is
a method rather than a longer line.

### The root block takes no id

`id:` on the root block is rejected. The root is named `root` in every expression in the document already —
*Name resolution* says so — so an id there would be a second spelling of a name the language already gives, and
`self.<id> = self` besides. QML does allow it, and `id: root` is idiomatic there, but QML has no reserved `root` to
collide with.

One thing falls out of it. *Checked when the document is compiled* asks for a self-referential alias to be rejected,
and with ids naming children only there is no way to write one: an alias target is `<id>.<attribute>`, and no id
names the component the alias is declared on. The check that remains — the target names an id this document
declares — covers everything reachable, and a cycle through *another* component's alias is the generator's to find.

### The node graph

`navml/parser.py` emits it and `navml/errors.py` carries the one exception both halves raise, `MarkupError(message,
line, filename)`, modelled on `StylesheetError` and rendering the same way: `button.nml:12: message`.

**Nothing in the graph holds a class object or a compiled expression.** Everything right of a `:` is kept as source
text with the line it came from, because compiling it is a pass that needs the document's types to be live:

- `Document(filename, imports, root)`, with `bound` naming everything the import block binds and `ids()` every id.
- `Import(source, line, module, names, modules)` — `source` verbatim, because the generator copies the line through
  untouched; `modules` for the build ordering, a relative import keeping its leading dots.
- `Block(type, line, base, id, id_line, declarations, properties, handlers, style, children, doc)`. `base` and
  `declarations` are only ever filled on the root.
- `Property(name, expression, line, doc)` and `Handler(name, body, line, doc)`.
- `PropertyDecl`, `StylePropertyDecl`, `AliasDecl`, `EventDecl` — one per directive. `StylePropertyDecl` carries the
  *decoded* default and vocabulary rather than the text, because the `|` form is `.nss` and navkit's own
  `parse_value` reads it; everything else is text.
- `StyleBlock(declarations, line)`, whose `text()` joins the block into the one `inline_style` string it becomes —
  the markup is newline-separated and that attribute is `;`-separated, and this is where the two meet.

**A block carries its `id:` line as well as its head's.** Not redundancy: the stub wired for a child's event is
named after the id and cites *that* line — `dialog_nml.py`'s `on_ok_click` reads `# dialog.nml:17`, which is
`id: ok`, while the constructor line above it reads `# dialog.nml:16`. A node that knew only the head could not
emit either comment honestly.

One asymmetry of the language shows up in the parser and nowhere else: **`event ClickEvent` is the only line in a
document with no colon on it.** Every other line is `name: value` or a head ending in `:`. That is what
*Declaring an event* asks for — the directive names a class and declares nothing about it — and it is decidable
without lookahead, but it is worth knowing that the classifier has a case for it.

### What this asks of navkit

Nothing for the parser. It reads `parse_value` and `PropertySpec.of` out of `navkit.stylesheet` to decode a
`style_property` vocabulary, rather than inventing a second reader for a grammar that already has one, and that is
the whole of its dependency.

**One thing for the generator, found while writing the parser** — and **now there**. *The `style` block* says the
generator validates a block's property names and values at generation time, leaving only variable *resolution* to run
time. `navkit.stylesheet.parse_declarations()` could not do that: `parse_value` raised `undefined variable $surface`
for any `$name` not in the mapping it was handed, so a block validated with no sheet loaded failed on exactly the
lines the design wants deferred, and the public entry point hardcoded `line=0` and `"<inline style>"`, so a failure
could not name the `.nml` line every other message in this file does. `navkit.stylesheet.check_declarations(text, *,
line, filename)` is the answer: the same key check and the same value grammar, a `$name` passed over because what it
will hold is not knowable yet, and a position to name. It returns nothing — the declarations it produced would be
half-resolved and a caller would have to know which half.

