### The `style` block

One property is not compiled as a Python expression at all:

```
Panel:
    style:
        bg: $surface
        fg: white
```

The block is a **stylesheet fragment**, in the `.nss` value grammar rather than Python, and it compiles to a
declarations string assigned to `inline_style` — the same attribute a runtime
`widget.inline_style = "bg: red"` writes, since `navkit/DESIGN.md` makes that one slot rather than two. Read that file's
*Where a widget's style comes from* before implementing this.

Two things follow, and both are worth having:

- **`$name` is meaningful here and nowhere else in a `.nml` file.** A variable is a stylesheet concept; inside an
  ordinary property expression the free names resolve by the table under *Name resolution* above, where `$` is not even
  valid Python. The block is the boundary, and it is a sharp one because the two sides are different languages.
- **The generator validates the block, and should.** A property name checks against `Style`'s fields **or** the widget
  properties something has declared — `navkit.stylesheet.declared_property()` is the read side of that registry, and
  the union is the one the `.nss` parser itself checks, so `border: double` is as legal here as it is in a sheet.
  Values check against the literal grammar and, where the property declared a vocabulary, against that too. All of it
  at generation time with the `.nml` line, leaving only variable *resolution* to run time, because the sheets do not
  exist yet. That makes the markup channel strictly better than the code channel, where a malformed string cannot
  surface until the widget is first painted and the failure is then cached.

The variable reference surviving to run time is what makes a theme swap reach markup-authored styles: the string is
parsed inside the `style` computed, which reads the reactive variable table, so replacing the sheet restyles these
widgets along with everything else.

### The `keys` block

The other block that is not a widget, and the root block's alone:

```
Dialog(Modal):
    keys:
        escape: Cancel
        enter: Default
        tab: SelectNext
        shift+tab: SelectPrevious
```

It compiles to the class's `keys` attribute (`navkit/DESIGN.md`, *Commands and key tables*), one entry per line,
each carrying its `# dialog.nml:N`. A `#:` run above the block is re-emitted above the attribute.

- **The left side is a key spec**, read by `navkit.commands.parse_key` in the parser. It is written in its
  canonical spelling, so `Ctrl+R` and `ctrl+r` are one key, and binding it twice is an error with both line
  numbers. A modifier navkit does not know is refused there, not left to never match.
- **The right side is a Python expression, but a class-level one.** A key table is made once, when the class is,
  before any instance exists, so `self`, `root`, `parent` and every id mean nothing in it. The generator refuses any
  name the import block did not bind, *by name*, instead of letting it surface as a `NameError` on import. What is
  left is evaluated as the class body will evaluate it and has to be a `Command` class or instance. That is the check
  navkit makes too, only earlier and with a line number.
- **Root block only.** A child block is an instance of a class that already exists, and a key table is a class's.
  A child that needs keys of its own is a component of its own.
- **The hand-written half may have a `keys` too**, and the two merge down the MRO like any two tables. The
  hand-written half is the derived class, so its binding of a key wins. The markup is where a component's keys are
  read; the `.py` is where a key whose binding needs Python goes.

`Manager` shows the shape: its document binds Tab, Ctrl+R and F2 to F8, and `manager.py` holds three handlers.
Every panel command without a handler is disabled, and its caption on the key bar is greyed.

### A handler body is one line

**A handler written in markup is one line, and it compiles to a function holding that one statement.** Anything
longer — a branch, a loop, a `try`, two statements in sequence — is a method in the hand-written half, and the markup
line calls it:

```
Button:
    text: "Quit"
    on_click: await self.confirm_quit()
```

`confirm_quit()` lives in `button.py` and may be as long as it needs to be. **The `await` is not decoration**: the
method is `async def` like everything else a handler reaches, and without it the line builds a coroutine, drops it,
returns `True`, and the button does nothing — a `RuntimeWarning` at the next collection and no traceback. *What the
generator checks about a handler line* above is what catches the omission.

The spelling of the handler line and what the function is handed besides the component were both deferred to *Still
open* from here, and both are answered now — *The handler's one argument is `event`* below, and *Which child it was is
a question the generator answers* above for the line that routes to a method. Neither touches this rule, which governs
the body rather than the line introducing it.

Four reasons, in the order they carry weight:

- **There is one expression compiler, and this is what keeps it one.** A handler body goes through the transformer in
  the appendix exactly as a property expression does, and its free names resolve by the table under *Name resolution*
  above — `self`, the ids and the reactive attributes mean there what they mean everywhere else in the document. A
*block* needs a second set of rules stacked on that one, for the names a body may *write* rather than read:
  `count = 0` in a handler is a dead local, `self.count = 0` is an attribute of the owner, and the two look alike. One
  statement asks that question once and leaves it answerable by the parser, the statement being the whole body; a block
  interleaves reads and writes until the rewriter has to carry a scope of its own. *Naming rules* above records that
  Kivy resolves names one way inside a property expression and the opposite way inside an `on_*` handler; a second set
  of rules is how a language arrives there, and one table used in both places is the whole of the alternative.
- **The failure stays findable.** A binding's failure is already cached and surfaces arbitrarily far from where it was
  written — *Source mapping* above — and the answer there was that generated code is a real file every tool can
  read. A one-line body is one emitted statement carrying one `# button.nml:12` comment, so the frame a traceback
  names and the markup line its reader wants are the same line. A block is one frame standing in for many markup lines,
  and the line wanted is the one the block opened on, which nothing in the traceback names.
- **It is the split the file layout already makes.** *The two halves of a component* gives `button_nml.py` the tree and
  `button.py` the handlers. This rule reads that same sentence one level down: markup says *what* is connected to what,
  Python says *how*. A document grown a body of logic has stopped describing a tree.
- **It costs the markup-only shape nothing.** A component with no `.py` half that needs a real handler gains one, and
  *The two halves of a component* is explicit that gaining it changes no import line anywhere and no line of the markup
  either. The escape hatch is one new file and no edit.

The parser check is mechanical: a line indented under a handler line is an error, and the message names the component's
`.py` file. Lines indented under a *property* line are a different question, still open below.

Not adopted: allowing the long form and leaving its length to convention, which is what both ancestors do. Kivy takes an
indented block of statements under `on_press:` and compiles it out of the file's text at load time, so nothing but Kivy
reads it — no completion, no checker. QML takes a JavaScript function body inline, which its engine does report
properly; the cost there is not tooling but the document, which stops being a tree and becomes a program with a tree in
it. The advice that follows in both is to keep such bodies short, and enforcing that is cheaper than repeating it.

### The handler's one argument is `event`

**Every handler takes exactly one argument, the event object, and in markup it is always called `event`.**

```
Label:
    id: b
    on_key: self.text = event.key
```

A hand-written handler may call it whatever it likes — the call is positional — but there is nothing to gain by it:
navkit's own hooks already say `event` throughout, `Widget.on_key(self, event)` and `Application.on_mouse_click(self,
event)` included, so markup is adopting the house spelling rather than inventing one.

A `Label:` and not a `Button:`, deliberately, and the difference is the subject of *What the generator checks about a
handler line* above: the line assigns onto the instance, and an instance attribute beats a class method, so on a
`Button` it would land in front of `Button.on_key` and take Space and Enter away from the button without saying so. A
`Label` implements neither handler, so this is what the rule permits.

Two halves to the rule, and the second is the one that needs defending:

- **Fixed at one argument**, because markup has no parameter list and should not grow one. A property line and a handler
  line are the same shape — `name:` and one line of Python — and a parameter list is precisely what would make them two
  shapes. So the arity cannot vary with the event. One serves an event that carries something and an event that carries
  nothing alike, provided the object always exists, which is navkit's side of it: an argumentless event is already
  idiomatic there — `Event` declares no fields and `WakeEvent` adds none.

  This once carried a second clause, that a future `on_mount` would announce itself with an empty event rather than an
  empty argument list. **That is void.** navkit's lifecycle hooks are not handlers and not called `on_*`, because the
  mount walk runs from a constructor and a constructor cannot await — `navkit/DESIGN.md`, *Why the hook is not an
  event, and not called `on_*`*. The rule above is unaffected; only the example it reached for is.
- **Fixed at the name `event`**, because with no parameter list there is nobody to ask. The author cannot name it, so
  the language names it, once, for every handler in every document.

**`event` therefore joins `self`, `root` and `parent` in the reserved list** that *Naming rules* above checks, and for
that section's own reason: a document allowed to declare `id: event` or `property event:` would have the name mean
`self.event` in a property expression and the handler's argument inside a handler body. That is the divergence
*Naming rules* convicts Kivy of, arrived at from a different direction. One list, checked once, in the parser.

**What it does to the compiled form** — three things, the second of which amends the section above:

- **A handler does not take the owner, so it closes over it.** `bind()`'s convention is that an expression's one
  argument is the object that owns the attribute — *What this asks of navkit* below — and a handler's one argument is
  now spoken for. So markup's `self` compiles not to the function's parameter but to the expression that names the
  owner in the enclosing `__init__`: `self.b` for a widget with an id, the anonymous local otherwise. **This is one
  change to the transformer in the appendix**, whose `owner` becomes an expression rather than a name; every other row
  of *Name resolution* reads unchanged, `root` still being the component's bare `self` and an id still `self.<id>`.
- **The emitted form is a one-statement `def` inside `__init__`** — not a lambda, and not a method on the generated
  class:

  ```python
  def __init__(self, **kwargs: Any) -> None:
      super().__init__(**kwargs)
      self.b = Label(parent=self)  # id: b

      async def _on_key(event):  # button.nml:4
          self.b.text = event.key
          return True
      self.b.on_key = _on_key
  ```

  **`async def`, not `def`.** Every handler is awaited — `navkit/DESIGN.md`, *Every handler is `async def`* — and
  `_call` holds an instance-assigned one to it at the call, which is precisely the case markup compiles to. A
  synchronous one raises `TypeError` at the first key rather than at generation, and a body that awaits anything, which
  the canonical routed body below does, could not be compiled at all.

  **Not a lambda**, because the commonest handler body there is — the one in the example above — is an assignment, and a
  lambda cannot hold one. The way to keep the literal lambda is to rewrite `self.title = event.key` into a `setattr`
  call, which makes the transformer rewrite *statements* as well as names and drags in augmented assignment, subscript
  targets and chained targets behind it. That is the seam *A handler body is one line* exists to avoid, so the emitted
  shape gives way rather than the rule. **Not a method**, because *Building the tree* above already establishes the
  hazard: a derived component's generated class would name its handlers by the same rule as its base's and shadow them,
  which is the argument that keeps the tree out of a `_build()` method.

  The body is copied through with its free names rewritten and nothing else done to it, so the one statement under
  the comment is exactly the one markup line it names. The `return True` beneath it is the generator's own, for the
  reason in the next bullet.
- **An assignment beats a method, which is backwards here, so the generator rejects the pair.**
  `self.b.on_click = _on_click` lands on the instance and wins over a `def on_click` defined on the class — and for a
  component written as both halves that inverts the usual precedence, the hand-written class being the derived one that
  wins everywhere else. `navkit/DESIGN.md` states the rule and leaves the catch here, under *One handler per widget per
  event*, because the assignment is legal and navkit cannot tell a shadow from an intention. **The rule is about the
  object the line lands on, not about a name**, and *What the generator checks about a handler line* above states it
  and says why a check phrased by name alone was wrong in both directions. A component that wants the Python one
  deletes the markup line; a component that wants both writes the markup line to call the method.
- **A markup handler always consumes.** navkit reads a handler's return value as *stop propagating* — `dispatch_key`
  offers a key to the children topmost-first and stops at the first `True` — and a body that is an assignment returns
  `None`, so without this the commonest handler there is would read its event and let it through. The third possible
  answer goes out first: passing the body's value through makes `on_key: self.close()` consume or not according to what
  `close()` happens to return, which is the value-dependent divergence this file refuses everywhere else. The two that
  remain are both fixed and so both uniform, and the choice between them is not about the body at all but about which
  of the two cases stays reachable from the other side. Under *never consumes*, a markup-only component could not bind
  a key at all without growing a Python half, which would make the first-class markup-only shape degenerate after all.
  Under *always consumes*, a component that merely watches an event writes that one handler in its `.py`, where a
  handler returns what it likes. The rarer case is the one that pays, and the failure it can cause is legible: an outer
  handler that stops running, with the document that claimed the event one level in.

  Two edges. Where the protocol ignores the value — `Application.on_resize` is annotated `-> None` — the `return True`
  costs nothing, and where it reads it the answer is the same every time, which is the property being bought. And the
  emit mechanism has since been designed around this same protocol rather than around a broadcast —
  `navkit/DESIGN.md`, *Emitting: a widget event walks up* — so consuming means something for a widget's own events
  too: the ancestors do
  not see what the document that named the widget has claimed. The two notes agree on which claim is the specific one.
- **It works for input as well as for signals.** `Widget.emit()` now exists — `navkit/DESIGN.md`, *Emitting: a
  widget event walks up* — and it looks a handler up under `event.handler`, which finds an instance attribute exactly
  as `dispatch_key` finds `self.on_key`. So one emitted assignment serves both directions: a key arriving from the
  terminal and a `ClickEvent` a sibling raised reach the same generated function, with the same one argument, under the
  same name. What the widget library adds is more events to handle, not a different shape of handler.

