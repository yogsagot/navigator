### Still open

- ~~Multi-line property bodies.~~ **Answered, and the parser settled it as the bracket rule.** *A handler body is
  one line* refused statements for reasons that did not care whether the line was a handler or a property; what was
  left was the lexical half, whether a single expression may be *spread* over indented lines. It may not: a logical
  line continues while a bracket is open, which is Python's own implicit continuation, and an indent goes on meaning
  exactly one thing. See *An expression continues inside brackets, and nowhere else* above.
- ~~Whether `equal=` is expressible in markup.~~ **Answered, and answered as no**, at both sites — a `bind()`
  expression and a `property` declaration. A comparator is a *function*, and a document has nowhere to define one:
  every value in the language is a one-line expression, and a language that grew a place to put a function body would
  have stopped describing a tree, which is the argument *A handler body is one line* already makes. Nothing in the
  repository needs one. A property that does is declared in the hand-written half — the same escape hatch a fielded
  event and a property with no default already use, and the one that makes an incomplete `property` acceptable. The
  third site was settled first and settled the same way: on an `alias`, never, for the reason under *Three things an
  alias cannot carry*.
- ~~Comment syntax.~~ **Answered: `#` to end of line, and `#:` above a declaration is kept.** The doc comments
  `navigator/__main__.py` writes beside every reactive attribute it declares are carried onto the node and emitted
  above the generated declaration, so the reason a property exists survives the move into markup. The one wrinkle is
  that a `#` opens a comment only when a space, an end of line or a `:` follows it, because `#rrggbb` is a colour
  inside a `style:` block — *Comments: `#` and a space, `#:` and a declaration* above has the whole of it.
- ~~Signal and handler syntax.~~ **Answered, and the last piece was the one this bullet said had to wait.** The body,
  its argument and what it returns are settled under *A handler body is one line* and *The handler's one argument is
  `event`*; navkit's half is *Emitting: a widget event walks up*; and *Declaring an event* above settles where an
  event class lives, that a widget declares what it emits, how the generator checks an `on_click:` line in both of the
  places bubbling makes it legal, and the `event ClickEvent` directive. The alias question *Aliases* deferred here is
  answered with it, and answered as no. What this bullet was waiting for — "the widget library declares some events to
  point at" — is `navml/widgets/dialog/button/button.py`, which emits a `ClickEvent` from two input routes.
- **How the hand-written half gets type-checked.** The id-annotation question is answered — the generated class carries
  `left: Panel` and the generated `.pyi` carries the merged surface — but the answer brought its own problem with it,
  measured rather than predicted: a stub replaces its module for a checker, so an error planted in `button.py` is not
  reported even when mypy is pointed at the file. Options are a second pass with the stubs held aside, moving the stubs
  somewhere only an IDE reads, or accepting that handler bodies are covered by tests rather than by a checker. Nothing
  forces a choice yet, because `CLAUDE.md` records that no lint tooling is configured; the day it is, this is waiting.
- ~~Whether the generated half gets a base of its own.~~ **Answered: yes, `navml.component.Component`** — see *The
  shared base, and how a value gets in* above, which has the whole of it. Still not identity: *The two halves of a
  component* settles that and settles it as no, and the base is a home for what every generated module would otherwise
  repeat rather than a test of anything. Two of the three arguments against it dissolved rather than being overruled.
  The one that decided it was the third of the arguments *for*: component parameters needed something to interpret
  them at construction, and that turned out to be the blocker standing between the generator and the `Manager`
  conversion, not a tidiness question. The `.nss` selector is real and is kept as a documented consequence —
  `Component { }` matches every markup-built widget and no hand-written one. *A bare head, and why nothing is
  reserved* needs no footnote after all: `Label:` compiles to `_Component`, underscored like everything else the
  generator names for itself, so a document that imports its own `Component` still gets exactly that. And the
  byte-identical `layout()` the first argument rested on is now observed in all four stand-ins rather than asserted.

