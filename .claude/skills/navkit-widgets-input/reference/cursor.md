## The cursor: shown where the keys go

**Written**, and the fifth and smallest item of *What the widget library needs first* below. `Widget.cursor_position()`,
the `caret` widget property, `terminal.place_cursor()`, and a few lines at the end of `Application._render`.

The terminal's own cursor was hidden at startup and never placed again, so the only caret available was a reversed
cell — which is what `Console.render` paints by hand, and which cannot blink, cannot be a bar, and is not where a
screen reader or a terminal's own copy-mode thinks the cursor is.

**A widget says where it wants one, in its own coordinates, and only the widget the keys are going to is asked.** The
one the application asks is the head of the focus path — the same walk `dispatch_key` makes, so the same modal, the
same invisible-ancestor test, and the same answer of "nobody" when nothing holds the keyboard. A caret drawn on a
widget that could not receive what is typed into it would be a lie told once per frame, and reusing the walk is what
makes it impossible rather than merely avoided.

**Then the rest of the focus path, nearest first, and the first answer wins.** This went in with Navigator's command
line, which is DOS Navigator's `ofPostProcess` `TCommandLine`: it never holds the keyboard, and it gets the printable
keys because the focused panel declines them and they walk up to the screen that holds the line. Asking only the head
left the line without a caret while it was being typed into. Walking the path keeps the rule rather than bending it —
a key the head declines *does* go to the ancestor, so the ancestor's caret is where the keys go — and it costs a widget
nothing: the default `cursor_position()` is None, so an ancestor with no text field answers exactly as it did.

### Why it is not called `cursor`

`navigator`'s `Panel` already has one: `cursor: int = reactive(0)`, the row its selection bar is on. A `cursor` on
`Widget` would have been shadowed by it in silence — a subclass attribute beating a base-class method with no
complaint from anything — and the application would have been handed a row number where it expected a position. The
name is `cursor_position()` for that reason and no other.

It is a **method rather than a reactive attribute** because exactly one widget per frame is asked, at paint time, and
nothing derives from the answer. A cell on every widget would buy the ability to bind something to a caret's position,
which nothing wants, and cost one on every widget that has no caret at all.

### Where the escape goes

At the end of the frame, after the diff, always: **painting moves the terminal's cursor as a side effect**, so
anything placed before it is left wherever the last cell was written. Three cases, and the third is the one that keeps
an existing promise:

- the cursor changed, appeared or went away — place and show it, or hide it;
- unchanged, but the frame painted something — re-emit the position alone, since it is already visible and already
  the right shape, and the painting has just moved it;
- unchanged, and the frame painted nothing — emit nothing, which is what keeps a frame that changes nothing writing
  nothing, and `tests/test_application.py` has asserted that since long before there was a cursor.

`render_diff` was left alone. It turns one buffer into another and the cursor is not in the buffer; the placement is
the application's, which is the layer that already owns the terminal and knows what the focus is.

### The shape is a widget property, from the sheet

`caret` joins `border` as a `StyleProperty` — `Input { caret: bar }` — for the reason *Widget properties: `Style` does
not grow a border field* above gives: a cursor shape produces no SGR sequence and is an input to an escape rather than
an appearance a cell can carry. The vocabulary is DECSCUSR's, spelled out (`block`, `underline`, `bar`, each with a
`blink-` form).

**`default` means "leave the user's own alone", and is the default.** A terminal's cursor shape is a setting somebody
chose, and a library that overrode it merely because it had the ability would be the rudest thing in it; the escape is
not emitted at all unless a widget asks for something specific. The reset at shutdown *is* unconditional, like the SGR
reset it sits beside, because a widget may have changed the shape at any point in the run and the flag that would say
so belongs to a frame rather than to the terminal.

### The console was the first thing converted

`navigator`'s console painted the child program's cursor by reversing a cell, for want of a real one. It has the real
one now, and the conversion is three small things worth recording because they are what any adopter does:

- **It takes the focus while it is showing.** `Console.can_focus` is set in `__init__` — not in the class body, where
  a plain `can_focus = True` would shadow the `Reactive` descriptor with an ordinary attribute — and a `Manager` effect
  hands it the keyboard whenever `console_visible` goes true. Saying that to navkit is what gets the cursor drawn:
  `Navigator.on_key` had been saying it in a comment for as long as the console has existed, "it has the screen, so it
  should have the keyboard".
- **`cursor_position()` is three lines**, `ConsoleScreen.cursor` having reported `(x, y, hidden)` all along.
- **It fixed a bug on the way through.** The reversed cell was painted whether or not the view was scrolled back, so
  scrolling into the history highlighted whatever happened to sit at the live cursor's coordinates among rows it has
  nothing to do with. `cursor_position()` answers None while `scrolled_back`, which is the question the hack never
  asked.

Checked on a real pty rather than only against `FakeTerminal`, since this is output the fake one cannot prove: startup
hides the cursor and never shows it, Ctrl+O emits the placement immediately after the frame's last cell, toggling back
hides it again, and exit restores both the cursor and the shape.

