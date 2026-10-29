# Right-to-left backlog

What is still to do for Hebrew and Arabic after the first pass (October 2026): the catalogues, `navkit/bidi.py`, the
mirrored screen, the per-terminal handling, and visual layout, movement and blocks in the viewer and editor. Ordered
by how likely a user is to meet each item. Strike an item through, or remove it, when it is done.

## High: wrong behaviour users will hit

1. **Untested terminals may reorder Hebrew a second time.** Konsole has its own bidi rendering, on by default, and
   probably ignores `CSI 8 l`, so it would reorder text Navigator has already laid out. WezTerm, Alacritty, foot,
   mlterm and Windows Terminal are also untested. Inside tmux or screen, `CSI 8 l` may never reach the terminal, and
   `TERM` hides kitty, so `TerminalInfo.bidi` falls back to `"app"` there.
2. **Global keys with a Hebrew or Arabic keyboard layout** (Alt+X, Ctrl+O, Alt+F1...) probably do not work. kitty
   sends the Latin base key, but `_kitty_key` in `navkit/terminal.py` drops it; legacy terminals send Alt+ס, with no
   Latin key at all. Not tested with a real layout switch.
3. **Console output (Ctrl+O).** VTE no longer reorders anything while Navigator owns the screen, so Hebrew printed by
   programs shows in logical order. Each console row could be laid out as a terminal would (`order_cells` per row in
   `ScreenView`), with the cursor mapped to match.
4. **The diff view (File > Compare files)** keeps left to right but paints its lines cell by cell and never reorders
   them (`navigator/widgets/viewer/diff_view/`). Hebrew in compared files shows in logical order.
5. **Direction overrides in file names.** U+202E and similar characters take no cell and are honoured by the layout,
   so a name can still disguise its extension (`gpj.exe`). The panel should show overrides visibly.

## Medium: incomplete or approximate

6. **Input lines and the command line** swap Left/Right only when the whole line is Hebrew. Within mixed text they
   move by position in the text, not on screen, and Shift+arrow selection is by text position too, unlike the editor's
   (`FileEditor._step_visually`, `_block_runs`).
7. **Viewer, wrapped lines:** each screen row is ordered on its own, not the whole line. Horizontal scrolling to a
   search hit (`file_viewer.py`, the offset-to-column search near line 700) uses file positions, so the hit can land in
   the wrong column on a reordered row.
8. **Editor, end of a Hebrew line:** the caret sits past the right end of the text, while typed text appears on the
   left. Hebrew lines are also left-aligned; whether they should be right-aligned is still to decide.
9. **Editor, small mismatches:**
   - The "current column" highlight follows file columns.
   - A lam-alef ligature shifts later tab stops on its line by one column.
   - ^K I/U falls back to the character's direction when neither placement paints the blank at the block's edge
     (`_painted_insert`).
   - A case change that alters the text's length turns a visual block back into a plain stretch of text.
10. **Widths measured with `len()`** in centring and layout code: Arabic lam-alef pairs, and anything shaped
    narrower, can leave text a cell off.
11. **Links in dialog text** are marked by text column, so on a mirrored screen the link can land on the wrong cells
    (`link_urls` in `navml/widgets/dialog/static_text/static_text.py`).
12. **Markdown and reStructuredText view:** a right-to-left paragraph is reordered but stays left-aligned.
13. **kitty handling is based on probing** (`for_words` in `navkit/screen.py`):
    - Re-probe after kitty updates (the skill says how).
    - Arabic preceded by Latin in the same run is an untested case.
    - kitty draws niqqud imperfectly.

## Low: polish and checks

14. **Menu tooltips** advertise Alt keys only for Latin hotkeys (`navml/widgets/menu/menu_bar/menu_bar.py`,
    `tooltip_at`).
15. **Column headers aligned with spaces** inside translations (attributes dialog, Top Ten, dBase structure) line up
    left to right.
16. **Translations need native review:**
    - the Latin hotkeys in the Links and calculator menus
    - key-bar abbreviations
    - DN terms (XLat, glass, Pinned)
    - Arabic captions that may overflow their dialogs
17. **Settings:**
    - Direction comes only from the catalogue or `--direction`; there is no Options setting.
    - `NAVKIT_BIDI` has no command-line flag.
    - Nothing hands bidi back to a terminal that does it well, such as mlterm.
18. **Not yet tried live:**
    - switching language from Options > Interface, which should flip mirroring at once
    - dragging and resizing windows on a mirrored screen
    - column blocks, since switching to them has no default key
19. **Performance:** the mirrored frame (`ScreenBuffer.mirrored`), the kitty pass and per-line ordering run on every
    frame. Not measured on a large screen or a large file.
20. **Packaging:**
    - `packaging/linux/build.sh` has not been run with the two new dependencies, so its `arch: all` check is
      unverified.
    - python-bidi 0.4.2 is from 2019 and needs `six`; check how distributions package it.
21. **Tooling:**
    - `tools/screenshot.py` has no right-to-left scene or `--language` option.
    - There is no automated end-to-end check on a real pty.

## Pre-existing, not right-to-left specific

22. A window title runs under the frame buttons, in English too (`navml/widgets/window/window.py`, `render`).
