## Declaring an event

A component says what it emits, and the widget library is where every event that is not terminal input comes from.
`navkit/DESIGN.md`'s *What belongs in `navkit/events.py`* draws the other side of that line: navkit carries the events
it raises itself and nothing a widget *means*.

The worked example is the one the library will be full of — a `Button` clicked by a mouse press **or** by Space:

```python
@dataclass(frozen=True, slots=True)
class ClickEvent(Event):
    """The button was pressed, by whichever route."""


class Button(Widget):
    emits = (ClickEvent,)

    async def press(self) -> bool:
        return await self.emit(ClickEvent())

    async def on_key(self, event): ...    # Space, Enter  -> press()
    async def on_mouse_click(self, event): ...  # a left press  -> press()
```

**Two input routes, one thing they mean.** That is the whole reason a component declares an event rather than letting
documents bind to `on_key` and `on_mouse_click` themselves: a listener that had to know which route fired would break
the moment a third arrived.

### Where the class lives, and why it follows who emits it

**Beside the component, in its hand-written half** — `ClickEvent` in `button.py`, next to `Button`. Nothing is
registered anywhere: navkit derives `on_click` from the class name at class creation, so a document that uses a Button
writes `on_click:` without importing the class at all.

Markup can declare one too, and **which half owns it is decided by which half emits it**. That is not a preference; it
falls out of a rule already in this file. A markup `event` line puts the class in `button_nml.py`, and *Why the
hand-written half never names the base* forbids that half from naming the generated module — so a `.py` that emitted
it could not import it. Hence:

| the event is emitted from | declared in | reached as |
|---------------------------|-------------|------------|
| the hand-written half     | `button.py`, beside the class | an ordinary global of that module |
| a one-line markup handler | `button.nml`, with `event`    | a global of the generated module |

**A component may not do both**, and the generator rejects it with the `ast.parse` of the sibling `.py` *without
importing it* that *Name resolution* already specifies for reactive declarations the Python half alone declares.

### `event ClickEvent`

A directive line with a two-token head, like `property`, `alias` and `style_property`:

```
Button:
    event ClickEvent
    on_key: await self.emit(ClickEvent())
```

It emits both halves of the declaration into the generated class — the `Event` subclass, and the `emits` entry naming
it — so a markup-only component is a first-class shape for events too, which *The two halves of a component* insists
on everywhere else.

**The document names the class, not the event.** `event click` would be shorter and would read like the handler it
leads to, and it is refused for the reason *A bare head, and why nothing is reserved* gives: the generator would then
be putting a non-underscored `ClickEvent` into a namespace the document shares with its own imports, which is a name
taken from the author. Naming it is what keeps the generator reserving nothing. The handler name still derives from it
— navkit's rule, unchanged — so `event SelectionChanged` is handled by `on_selection_changed`.

**In the root block only**, for the reason `property` is: it emits onto the class the root block becomes, and every
other block is an instance of a class that already exists.

**A markup-declared event carries no fields**, there being no syntax for one, and none is invented here. An event that
carries data is declared in the `.py` — the same escape hatch `equal=` uses, and the same boundary: markup says what a
component emits, Python says what it emits *about*.

### What the generator checks, and why it needs two answers

An `on_*` line is legal in two different places, because emitting walks up:

- **On the block that emits it** — checked against that widget's `emitted()` set, failing with the `.nml` line and a
  list of what the widget does emit. This is the case that catches a typo where it hurts, on the component the author
  is looking at.
- **On an ancestor** — checked against the handler names of every `Event` subclass the document's imports have made
  live, walked with `Event.__subclasses__()`. No registry: the classes are already there, and navkit's own handler
  names are in the set for free, being `Event` subclasses like everything else.

The second is the looser check and has to be, because a `Dialog` may legitimately handle a click from a button three
levels down without knowing which component emitted it.

### This settles the widget-alias question, and settles it as no

*Depth, and what is deliberately not offered* refuses an alias that names a widget, and defers the refusal to this
section: "the case that wants it is naming an inner button in order to connect a handler to it, and signals are open
on both sides of the layer boundary". They are closed now, and the case has evaporated — **bubbling reaches what a
widget alias was wanted for**. An outer document writes `on_click:` on the `Dialog:` block and catches clicks from any
button inside it, without the dialog handing out a widget.

Where a component must distinguish *which* inner widget, it translates in its own markup, one line per button:

```
Dialog:
    event Accepted
    Button:
        id: ok
        on_click: await root.emit(Accepted())
```

`self` is the Button and `root` is the Dialog — the *Name resolution* table already says so — so the translation costs
one line and the outer document never learns the dialog has buttons in it at all. That is the boundary *Aliases* exists
to defend, arrived at without a new kind of declaration.

That is the answer for telling somebody *outside*. For the component's own hand-written half the next section is
the answer, and it does not cost even the one line.

### Which child it was is a question the generator answers

Bubbling gets a child's event to the component; it cannot say **which** child. `Widget.emit()` walks from the emitter
upward and hands each handler the event alone, `Event` declares no fields, and `ClickEvent` deliberately adds none —
*Declaring an event* above is what makes that a feature, since two input routes have to arrive as one thing. So a
`Dialog` with an OK and a Cancel button in it hears both clicks through one `on_click` and has nothing to switch on.

**The component never asks. The generator answers, by wiring each id'd child to a handler named after it.** For every
id'd child and every event that child's class declares in `emits`, the generated class declares a handler and assigns
it:

```
Dialog:
    Button:
        id: cancel
        text: "Cancel"
```

```python
class Dialog(_Widget):

    cancel: Button

    async def on_cancel_click(self, event: _Event) -> bool:     # dialog.nml:25
        """``cancel`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.cancel = Button(parent=self)                       # dialog.nml:24
        self.cancel.text = "Cancel"                             # dialog.nml:30
        self.cancel.on_click = self.on_cancel_click             # dialog.nml:25
```

```python
class Dialog(Widget):
    async def on_cancel_click(self, event: Event) -> bool:
        self.result = False
        return True
```

The name is `on_` + the id + the stem of the event's own handler: `cancel` and `ClickEvent`, whose handler navkit
derives as `on_click`, compose to `on_cancel_click`. **There is no second naming rule** — the stem is read off
`Event.handler`, the same value `emit()` looks the handler up under, so an event class that renames its handler renames
this too and nothing has to be told twice.

#### The stub is the whole mechanism

`on_cancel_click` on the generated class is a no-op returning False, and the hand-written half overrides it. Every
property worth having falls out of that one shape, and it works only because the generated class is the **base** and
the hand-written one the derived — the same fact *The two halves of a component* forced for its own reasons, here
paying for itself a second time.

- **The generated file stays a pure function of the `.nml`.** It never reads `dialog.py` to decide what to emit. This
  is the objection that would otherwise have sunk the whole convention: the alternative is emitting the wiring only
  when an `ast.parse` of the sibling finds a matching method, which makes a generated file's *contents* depend on a
  file it is forbidden to know, so deleting a method rewrites `dialog_nml.py` and `navml build --check` reports drift
  for an edit made somewhere else.
- **A component that does not care pays nothing.** No `AttributeError` at construction for the stub nobody wanted, and
  no `getattr(self, f"on_{id}_{stem}", None)` in the generated `__init__` — which would be lookup by computed name,
  the registry *The handler name is read off the event class, not invented* refuses.
- **The specific hook does not take the general one away.** The stub returns False, so a click the hand-written half
  did not name carries on up to the component's own `on_click`, exactly as it would have if the stub were not there.
  A component may write both, and reading them together reads in the order `emit()` walks: the named child first, then
  everything else. `navml/widgets/dialog/dialog/dialog.py` is that example — `ok` overrides its stub, `cancel` does not, and the
  dialog's `on_click` is what dismisses it.
- **`check_handlers` enforces `async def` on both halves, for free.** It scans `vars(cls)` for `on_*` at class
  creation, so a synchronous stub or a synchronous override fails where it is written rather than at the first click.
  This is what the `on_*` spelling buys, and it is why the *routed* method below is deliberately spelled otherwise.
- **The author owns the return value.** This is not a markup handler, so *A markup handler always consumes* does not
  reach it: watching without consuming is `return False`, and needs no escape hatch.

#### What an explicit markup line is still for

The convention cannot name two children routed to one method, cannot reach a widget with no id, and has nothing to say
when the method wants to be named for what the component *does* rather than for what happened to it. Those keep the
form *A handler body is one line* below already implies, which at a child block reaches the component through `root`:

```
Button:
    id: info
    on_click: await root.show_info(event)
```

**The routed method is not an `on_*`** — `show_info`, never `on_info`. The prefix means one thing in this codebase,
*navkit found me under `event.handler`*, and a method reached from one markup line was found by nobody. Two costs
beyond the misreading. Its return value would mean two things at once, since the generated function discards what it
returns while the bubbling walk would read it. And wired by hand it is called twice: `self.info.on_click =
self.on_click` is found by the walk on the button, called, and — if it declines — found again on the component one step
up, under the same name, and called again with the same event. What the `on_*` name would have bought is the
`check_handlers` coverage above, and the last check below buys it back while naming the `.nml` line as well.

**An explicit handler line suppresses the convention for that child and that event.** Both would assign to
`self.info.on_click` and one would win silently, so the generator emits only the markup's and declares no stub.

#### What the generator checks about a handler line

Four, of which the first two are the convention's own and the third replaces a check this file previously specified
wrongly. All are generation-time and all name the `.nml` line.

- **A composed name the sibling `.py` defines must name an id the document declares.** `ast.parse` the sibling `.py`
  **without importing it** — the pass *Name resolution* above already describes — and refuse an `async def on_X_Y`
  whose `on_Y` is the handler name of a live `Event` subclass and whose `X` is no id. This is the price of composing a
  name out of an id, and paying it is what makes the composition safe: without it, renaming `id: cancel` leaves
  `on_cancel_click` sitting in the other file with nothing calling it and the button silently dead, which is the worst
  shape any failure in this document takes. With it, the rename fails the build naming both files.
- **A composed name may not collide with a handler navkit would derive anyway.** `on_cancel_click` is `cancel` +
  `on_click`, and it is also what a `CancelClickEvent` would be delivered to. Refuse the document naming both
  readings. The set to test against is the one *What the generator checks, and why it needs two answers* above already
  walks with `Event.__subclasses__()`. Composed names are checked against the component's own properties and ids too,
  as ids already are against its class.
- **A markup `on_X:` line may not land on an object whose class already implements `on_X`.** This replaces the
  by-name check under *The handler's one argument is `event`*, which was wrong in both directions: read by name alone
  it refuses a document whose line lands on a *child* and shadows nothing, and it never sees `on_key:` on a `Button:`
  block quietly beating `Button.on_key`, because the `.py` it parses is the document's and not the child's. Phrased
  about the object it is one rule asked two ways, the difference being which half exists yet — on the root block the
  class is the hand-written half, which cannot be imported and so is parsed; on a child block it is the child's class,
  which *The cold build* already requires to be live. `Widget.on_key` and `Widget.on_mouse_click` are do-nothing
  stubs, so ask which class in the MRO owns the name. A document meaning to replace a child's own handling gives the
  child a subclass; a document wanting the keys the child left alone puts the line on an ancestor block, where the
  walk reaches it anyway.
- **A handler body must `await` a method the sibling `.py` defines with `async def`, and must not await a plain one.**
  Both failures are close to silent — an un-awaited coroutine is a `RuntimeWarning` at the next collection and a button
  that does nothing. Checked only where the `def` is visible in that file; an inherited method falls through to the
  run-time `TypeError`, which is what any hand-written call already gets.

Not checked, deliberately: that the routed method exists. Being right about an inherited one means following the
import graph into a base component's `.py`, and what it buys is an `AttributeError` naming the component and the
method, raised at the click. Nothing here fails late or lies.

#### Not adopted

- **A `sender` field on `Event`.** It adds no information — the wiring already knows which child it was — and
  relocates it into the one place it is least useful, inviting `if event.sender is self.cancel:` in a component's
  `on_click`: dispatch by identity, in Python, over widgets the document declared, re-broken by every rename. The
  convention is that `if` chain compiled away. It would also have to be written by `emit()` into a frozen dataclass
  every widget shares, for the benefit of the callers that do not want it.
- **Bubbling alone, with no convention at all.** It cannot tell a component's children from its children's children:
  a `Dialog` containing a `FramedButton` catches that button's click identically. Kept for what it is actually good
  at, which is the two cases the convention does not serve — treating every click alike, and watching one without
  claiming it.
- **Wiring by hand in the hand-written `__init__`.** `self.cancel.on_click = self._cancelled` works, ids being live on
  the line after `super().__init__()`. It is refused as the ordinary form because it moves *what is connected to what*
  out of the document, which is the split the file layout rests on; because it is invisible from the `.nml`, where the
  reader sees `id: cancel` and no handler; because it forfeits every check above; and because it runs *after* the
  generated `__init__`, so it silently overwrites a markup line for the same child and event and leaves a document
  that lies about itself. It remains the only spelling for a widget the markup never declared — one built in a method,
  one handed to `Application.overlay()` — and for the Python-only shape, where there is no markup line to write.

