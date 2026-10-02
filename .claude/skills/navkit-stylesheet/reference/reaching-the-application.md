## Reaching the application

**Done, ahead of the engine, because it was a latent bug on its own.** `Widget._application` is now `reactive`, and
`Widget.application` is a `computed` rather than a property that walks.

The hazard it removes: `_application` was a plain attribute assigned by `Application.root`'s setter, so a value derived
before that assignment memoised the answer it got when there was no application and never recovered — only an unrelated
reactive write dislodged it. Since a widget reaches the stylesheet *through* the application, every style pulled before
attachment would have resolved against no sheet and stayed that way. Normal startup paints after attachment, so the bug
would have hidden until a test or an early access found it.

Two things fell out that are worth knowing:

- **It made the hot path faster, not slower.** `invalidate()` asks for `application` on every reactive change. Making
  `_application` reactive but keeping the walk costs 2464 ns per lookup at depth six, against 1347 ns for the plain walk
  it replaces — nearly twice as slow. Memoising it as a computed costs 290 ns, because a clean cell skips the walk
  entirely. The correct fix is the fast one, which is not the usual way round.
- **Attaching a tree now asks for a repaint.** Assigning `_application` reaches
  `_reactive_changed` like any other observable write, where before it was silent. That is right — a tree that has just
  joined an application needs painting — but it is a behaviour change, not just an optimisation.

Reparenting still invalidates the memo, because the walk reads `parent`, which was already observable for exactly this
class of reason.

## What a stylesheet still cannot reach

Nothing, of what `navigator/__main__.py` does today. All thirteen decisions are expressible: colour and attributes
through `Style`, spans and sub-elements through parts, and the border character set through a widget property.

The shape that is left is clean and worth stating as the boundary it is. A stylesheet reaches whatever a widget
declares — its parts and its properties — plus whatever a cell can look like. Anything outside both is the `render()`
escape hatch, level 4 above, which answers to nothing precisely so that there is always somewhere to go.

