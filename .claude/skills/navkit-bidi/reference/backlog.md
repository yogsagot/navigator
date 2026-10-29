# Right-to-left backlog

What is still to do for Hebrew and Arabic after the first pass (October 2026): the catalogues, `navkit/bidi.py`, the
mirrored screen, the per-terminal handling, and visual layout, movement and blocks in the viewer and editor. The second
pass (late October 2026) covered Konsole, mlterm and screen, Latin shortcuts on Hebrew and Arabic layouts, console
rows, the diff view, and direction overrides in file names; the third pass input lines, wrapped viewer rows,
right-aligned right-to-left lines in the editor and the Markdown view, painted widths, links in dialog text, and a
kitty re-probe; the fourth pass the Low items -- non-Latin menu hotkeys, translated tables laid out a column at a
time, a *Text direction* setting and `--bidi`, live checks, cost measured, packaging, the pty test and
`screenshot.py --language`, window titles clear of their icons, and a translation pass. Ordered by how likely a user
is to meet each item. Strike an item through, or remove it, when it is done.

## High: wrong behaviour users will hit

1. **Inside tmux the terminal's own bidi cannot be switched off.** Nothing reaches the terminal through tmux, even
   with `allow-passthrough on`. That covers VTE's `CSI 8 l`, Konsole's `OSC 50` and mlterm's `OSC 5379`, so a
   reordering terminal reorders Navigator's screen there. The only fix today is the terminal's own setting. Navigator
   could at least say so once.
2. **Terminals still untested:** WezTerm (not installable here), foot (Wayland only), Windows Terminal. ghostty 1.4
   dropped two probe rows (a framed line and an Arabic one), which is unexplained.
3. **Keyboard layouts have not been checked with a real layout switch.** The kitty base-layout key and the legacy
   position table are unit-tested only. The check: `tools/keyprobe.py`, then Alt+X in ghostty and xfce4-terminal with
   the Hebrew layout on.

## Medium: incomplete or approximate

4. **Editor, Up and Down** keep the text's column. Moving between a left-aligned line and a right-aligned one, or
   between two lines ordered differently, the caret jumps across the screen; a word processor keeps the painted column.
5. **Viewer, lam-alef:** the F3 viewer still loses a column to each lam-alef ligature, so tab stops after one on its
   line move a column left. The editor's fix (`file_editor._ordered`: a blank beside the next blank) could move to
   `navkit.bidi` and serve both.
6. **kitty draws niqqud imperfectly** (re-probed on 0.32.2: every other case matches VTE). That is kitty's drawing;
   re-probe when kitty changes (`for_words`, the skill says how).

## Low: polish and checks

7. **Translations still want a native speaker.** Every caption now fits in both languages (measured headless over
   every menu command and Settings tab at 80x25), and hotkeys are Hebrew letters where one was free. The wording is
   unchecked by a native:
   - Hebrew: `תפר׳` for the key bar's Menu, `מקורי` for Default in Key bindings, `השהיית רמז` for Tooltip delay,
     `ESC למסך משתמש` with its hotkey on final kaf.
   - Arabic: `سلة` for Trash, `توقف` for Pause, `إرسال البقية لسطح المكتب`, the Top Ten headings `بدء/نهاية/حصيلة`.
   - DN terms in both: XLat, glass (Hebrew `כוס`), Pinned.
   - Latvian and Russian Settings captions shortened to fit their room (every Settings tab, all three tab modes, now
     fits in all five languages): Latvian `Atlases zīme`, `Maksimizēt logus`, `Kont. izvēlne`, `Oriģ./Sasp. izmērs`,
     `Savs formāts`, `Saites mērķis`, `Uzst. cilnes`, `Aizvērt dīkstāvē pēc`, `∙ Starp zvaigznēm`; Russian `Вкладки
     опций`, `Закрыть с трассировкой`, `Заголовки`, `Контекст. меню`, `Направление`, `Оптимум заполнения`, `Убрана`,
     `Цель ссылки`.
8. **Packaging:** nfpm is not installed here, so the `.deb` and `.rpm` themselves are unbuilt (`build.sh` passes every
   check up to them with `NFPM=/bin/false`). Fedora's packaging of python-bidi is unchecked; it does not matter while
   Navigator vendors its own copy.
