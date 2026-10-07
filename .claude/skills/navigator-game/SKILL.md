---
name: navigator-game
description: ≡ > Game (Alt+F9), DOS Navigator's TETRIS.PAS "Navigator's game" -- navigator/tetris.py (Game: the glass, the 27 figures, rotation, scoring, levels; the Top Ten helpers), the TetrisScore model, the [tetris] settings section, and navigator/widgets/game/ (GameWindow with Glass and GameInfo, GameSetupDialog, TopTenDialog, WinnerDialog). Use when changing the game.
---

# The game (≡ > Game, Alt+F9)

- **The rules are `navigator/tetris.py`'s `Game`, transcribed from TETRIS.PAS**: the glass `SHI` 12 by `VIS` 19 with
  walls and a floor (a dict keyed `(row, col)`, columns from 1, rows -2 above it empty); `FIGURES` (the first seven
  Tetris's, all 27 Pentix's), `TURNS` (`CRot`, the square a figure turns in), `colour_of` (`15 - n mod 7`, a VGA
  index), `DELAYS` (hundredths a row, `LevelDelay`); the score for a figure set down, for each line, for an empty
  glass, seven tenths with the preview; the climb `1 + (lines - (90 - (9 - start) * 10)) // 20 + start`. The time is
  the caller's: `tick(hundredths)`; `drop()` goes to the bottom and the next fall sets it, as DN's did.
- **`GameWindow`** (`widgets/game/game_window/`) is `TGameWindow`, a dialog on the desktop as a window, one at a time,
  centred (`Shell.on_game`), DN's 53 by 22 -- the glass's frame on the window's bottom edge, as its rectangles put
  it. `Glass` draws `█` twice a cell on black (`Style(fg=colour, bg=0)`, the game's own colours) and takes Left/Home,
  Right/PgUp, Up, Down/Space; `GameInfo` is *Info*, *Next* and *Best* (parts `info`, `best` and their `-bright`). A
  `call_every(0.05)` clock; the game pauses when the window loses the keyboard (having had it). Keys are `StatusDef
  hcTetris`'s: F2 new, F3 pause, F4 Top 10, F5 setup, Gray +/* level and preview, Alt+N/P/T/S, Esc closes.
- **The end**: *Game over / Final score*, then for a place in the Top Ten `WinnerDialog` (history `tetris`,
  *Anonymous*), `tetris.enter` and `TopTenDialog` with the line bright. The Top Ten is the `TetrisScore` model (ten a
  style, best first, a tie after), where DN kept `dn.tet` XOR'd.
- **Setup game** (`GameSetupDialog`, `dlgGameSetup`) answers the `[tetris]` section (`TetrisData`: `level`, `style`,
  `preview`), saved, and starts a new game. Alt+F9 is the application's key with no caption, as DN's status line had
  none.
