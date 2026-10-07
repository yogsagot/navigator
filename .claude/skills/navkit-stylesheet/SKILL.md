---
name: navkit-stylesheet
description: The `.nss` stylesheet language and navkit's lookup engine (navkit/stylesheet.py, navkit/style.py) -- selectors, specificity, inheritance, `inline_style`/`merge_style`, the computed `style`, parts (`Panel::row`), `StyleProperty` widget properties, variables, `stylesheet` vs `effective_stylesheet`, and editing navigator/styles/navigator.nss rules. Use when writing style rules or adding a stylable property.
---

# Stylesheets

CSS in shape (selectors, brace-delimited declarations, a cascade ordered by specificity) and not in scope: every
declaration either names a `Style` field or names a property the widget interprets. `parse()` reads one sheet, `load()`
merges several in order so a theme can redefine another's variables. `Style` (`navkit/style.py`) is an immutable cell
appearance that knows its own SGR sequence; nothing else writes colour codes. Theme colours and palconv are the
`colours-themes-glyphs` skill.

- Selectors: `Panel` (by class *name*, subclasses included), `.tag`, `:state` (any truthy attribute, including navkit's
  `focused`, `focus_within`, `hovered`, `inert`), `:not(compound)`, `#name`, `Panel::part`, descendant and child
  combinators. Specificity is CSS's `(names, classes + states, types)`, ties break on source order, no `!important`.
- **`Component { }` matches every markup-built widget** and no hand-written one (type selectors match by name).
- `navigator/styles/navigator.nss` holds the rules and defines no variable (it does not parse alone); a theme is always
  loaded after it. The command line's `$0F`/`$07` is the one literal-colour rule in it.

## Things to know before touching it

- **A widget's `style` is a `computed`, not a value you assign.** It cascades in four levels: the parent's resolved
  style (appearance inherits), matching `.nss` rules, `inline_style`, then what `render()` passes to a primitive.
  Assigning `widget.style` raises; author through `inline_style` or `merge_style()`.
- **`inline_style` is partial**: `"bg: red"` overlays one property. A `Style` is accepted and becomes seven declarations.
- **`classes` is a `frozenset` and `inline_style` is replaced, never mutated**: use `add_class`/`remove_class`/
  `merge_style`.
- **Only a *reactive* attribute restyles.** A plain attribute matches the first time and never invalidates.
- **Widget properties do not inherit**, only `Style` fields do. A non-`Style` declaration is declared on the widget that
  reads it -- `icons = StyleProperty("auto", values=("auto", "none"))` -- naming it, defaulting it, and saying what a
  sheet may set; the parser rejects an unregistered name and an out-of-vocabulary value with its `.nss` line. The type
  is the default's own. `stylesheet.register_property()` is the bare form.
- **A sheet cannot be parsed before the widgets it styles are imported** -- which is why `load_scheme()` imports
  `navigator.widgets.manager.panel` before it parses.
- Listing rows are **parts** (`Panel::row`, `Panel::heading`, `Panel::divider`), never widgets.
- A widget may carry its own sheet in `stylesheet` (what an object brings, assigned); `effective_stylesheet` (derived)
  walks up to the nearest, ending at the application's. `Manager` uses this, so the desktop is styled with or without an
  application around it.
- **`inherit` on a `Style` field drops the declaration** (`stylesheet.INHERIT`), whether written or held by a
  variable -- how `attributes.nss` gives every entry an attribute variable without breaking inheritance.
  `variables_in(text)` answers a sheet's definitions as written (references unresolved).
- `stylesheet.check_declarations(text, *, line, filename)` checks names and grammar, leaving `$variables` for run time
  (navml's `style:` blocks use it).

## Read when

| Reference | Read when |
|---|---|
| `reference/selectors.md` | `:not()`, ids, what each selector matches, resolution in a computed |
| `reference/inline-and-resolved.md` | the inline/resolved split, partial inline styles |
| `reference/inheritance.md` | why all seven fields inherit, the reactive sheet |
| `reference/specificity.md` | the tuple, per-property cascade, theming by last-wins |
| `reference/style-source.md` | where a widget's style comes from |
| `reference/grammar.md` | the grammar, literal values, variables, checked keys |
| `reference/parts.md` | why rows are parts, how a part resolves |
| `reference/widget-properties.md` | `StyleProperty`, why border is not a `Style` field |
| `reference/reaching-the-application.md` | how a sheet reaches the application; what it still cannot reach |
| `reference/settled.md` | what the migration and the build settled |
