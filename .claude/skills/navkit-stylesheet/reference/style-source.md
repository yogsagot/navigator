## Where a widget's style comes from

Four channels feed one widget, and they are one ordering rather than four mechanisms — weakest to strongest:

|   | Channel                                          | Written where                       |
|---|--------------------------------------------------|-------------------------------------|
| 1 | the parent's resolved style, inherited           | nowhere — it is the `derive` base   |
| 2 | matching `.nss` rules, by `(specificity, order)` | a stylesheet                        |
| 3 | `inline_style`, per-widget declarations          | a `.nml` `style` block, **or** code |
| 4 | a `Style` passed straight to a drawing primitive | `render()`                          |

Level 1 needs no rule of its own; it falls out of the parent's style being the `derive` base, so any matching
declaration, however weak, replaces it. CSS behaves the same way — an inherited value loses to any declaration on the
element itself. A universal selector, if the grammar grows one, is `(0, 0, 0)` and loses to everything except
inheritance.

**Level 3 is one slot, not two.** The markup block and a runtime string write the same attribute, exactly as the DOM's
`el.style` is a single declaration set that markup fills in and code merges into. So a widget whose markup set `bg`
keeps it when code later merges `fg`, and a code write that names `bg` replaces what markup said about `bg` and nothing
else.

**Level 4 is outside the cascade by construction**, and needs no design at all: `fill`,
`draw_text` and `draw_box` already take a `Style`. It is how the decisions under *What a stylesheet cannot reach* are
served — a substring span or a per-row model flag has no widget to select — and it stays the bottom escape hatch
precisely because it answers to nothing.

**Changing classes at run time costs nothing.** `classes` is reactive, so `add_class("wide")`
re-runs selector matching through the `style` computed and repaints, with no machinery beyond what levels 1-3 already
need. The same is true of the state selectors: `Panel.active` flipping restyles the panel because `style` read it.

