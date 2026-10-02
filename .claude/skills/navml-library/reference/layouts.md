### Layouts

Every container used to place its children with arithmetic in the markup — `width: parent.width // 2` beside
`x: parent.width // 2` in the file manager, `y: max(1, parent.height - 1)` in the shell, a `button_row` ternary in
`Dialog`, `x: parent.label_width` in `Field`. Five layouts now say *how* children are arranged instead, and all four
of those documents were converted to them. The proof is the one `manager.nml` set: the first paint at 80x24, the F7
Mkdir dialog over it, and a resize to 81x25 are each `cmp`-identical on a pty to the build before.

| layout | places its visible children |
|---|---|
| `HorizontalLayout`, `VerticalLayout` | one after another along the axis, filling the other; `spacing`, `justify` |
| `GridLayout` | in equal cells, `columns` to a row, row-major; `spacing` |
| `DockLayout` | against the edges in child order, then every `fill` child over the one rectangle left |
| `StackLayout` | every one over the whole area, as layers |

All five derive from `Layout`, which is Python alone and paints nothing, and the two linear ones share
`LinearLayout`. They are the first group, under `navml/widgets/layout/` (see *Components come in groups*). What was decided, and why:

- **A child asks for room with a style hint, read off the child by its layout.** `basis` is the cells it wants along
  the axis (or a docked child's thickness), `grow` its weight in what is left, and `dock` which edge it goes against.
  They are `StyleProperty` declarations, so a `style:` block, `inline_style` or a sheet rule can say them. That bends
  the rule a sheet otherwise keeps, which is that a declaration names a property *the widget it lands on* interprets,
  because here the child carries it and the parent reads it. The alternatives were an attached-property mechanism,
  which navkit does not have and a Label cannot declare for every container it might sit in, and track lists on the
  container (`sizes: (12, "*")`), which keep the hint away from the child it describes and cannot be said for a whole
  class of children by one rule. **`grow` defaults to 1**, so children that say nothing share evenly, which is what
  two panels need. A fixed child says `basis: 11` and `grow: 0`.
- **The cells floors lose go to the trailing growers.** `distribute()` grants every basis in order, clamping the
  ones that no longer fit so that later children shrink first, and splits the remainder in floor shares. The
  leftover then goes one cell each from the end. For two equal panels that is exactly `W // 2` and `W - W // 2`, the
  arithmetic being replaced, and it is why the 81-column paint is identical too.
- **Arranging is an effect, not the `layout()` cascade**, for the reason *Windows, the desktop and the modal* gives
  for `Desktop`: a markup parent does not cascade, so a resize reaches a layout as a changed `width`. The effect
  reads the size, the layout's own knobs, and every child's `visible` and hints, so restyling or hiding a child
  re-arranges its siblings. It applies the plan untracked. `layout()` is still overridden, to size the layout and
  arrange, for a hand-written parent that does cascade. `add()` and `remove()` arrange by hand because the children
  list is not reactive.
- **A child's geometry is the layout's to write, so it is navigated**, in the sense *A property a widget navigates
  cannot be bound* uses: its markup says nothing about `x`, `y`, `width` or `height`. A side that is bound anyway is
  stepped around, as `Widget.layout()` steps around one, rather than raising. Each placed child then has
  `layout(w, h)` called on it, so a hand-written child such as a `Desktop` still cascades into its own windows.
- **A hidden child gets no slot and no spacing**, and its geometry is left as it was. That one rule deleted
  `Dialog.button_row`: three 11-column buttons two apart start at `(W - 37) // 2` and two at `(W - 24) // 2`,
  because the layout centres what is showing.
- **A dock places every `fill` after every edge**, whatever its position among the children, and gives all of them
  the same rectangle. That is what lets the shell's key bar be the *last* child, and so painted over everything,
  while still being carved off before the console and the desktop share the band between the bars. `dock: none`
  leaves a child alone entirely, which is how the clock floats over the menu bar's right end.
- **A component can *be* a layout.** `Field(HorizontalLayout):` and `Shell(DockLayout):` put the arrangement on
  the root rather than on a wrapping child, because `Layout.layout` precedes `Component.layout` in
  `class Field(HorizontalLayout, _Component)`. A component whose base is already something else, such as `Dialog`
  (a `Modal`) or `Manager` (a `Window`), holds a layout as an id'd child instead, and the ids inside it are still
  the component's own attributes, `on_<id>_<event>` included.
- **`GridLayout` has no spans and no per-track sizes yet.** Equal cells are what a table of buttons or check boxes
  wants, and a hint language for tracks is better decided against the first dialog that needs one.
- **The old `max(1, …)` floors are gone.** The shell's bars no longer keep the console at least one row tall in a
  terminal two rows high: at that size the dock simply runs out. The pty proof covers ordinary sizes, not that one.

