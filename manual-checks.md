# Manual checks

What the test suite and the headless tools cannot cover: each needs a real terminal, a real `sudo`, real hardware or
a real keyboard layout. Each item says what to do and what you should see. Use a scratch directory, and start
Navigator with `--config` and `--database` pointing there if you'd rather not touch your real settings.

## 1. Root access, with real `sudo`

1. Make a directory you can't read: `mkdir /tmp/locked && sudo chown root /tmp/locked && sudo chmod 700 /tmp/locked`.
2. In Navigator, go to `/tmp` and press `Enter` on `locked`.
   - **Expect:** a box with *As root* and *Cancel*.
3. Choose *As root* and give your password.
   - **Expect:** the panel shows `root:///tmp/locked`, and *ROOT* appears on the menu bar beside the clock.
4. Press `F7`, make a directory, then `F8` it.
   - **Expect:** both work, and no second password prompt.
5. Open *Utilities*.
   - **Expect:** the entry reads *Close root access*. Choose it; the panel goes back to the disk and *ROOT* disappears.
6. Idle timeout: set *Options > Settings > System > Keep root open while idle* to `1`. Open root access again, then
   leave Navigator alone for a little over a minute.
   - **Expect:** *ROOT* disappears by itself.
7. If you have `pkexec`, set *Root access* to *pkexec* on the same page and repeat step 3.
   - **Expect:** your desktop's polkit dialog asks instead of Navigator's box.

## 2. Pictures on kitty or a sixel terminal

1. Install the extra if needed: `pip install navigator-fm[images]` (Pillow).
2. In kitty, press `F3` on a PNG, a JPEG and a GIF.
   - **Expect:** each is drawn as a picture.
   - **Also:** `Ctrl+Q` on a picture shows it in the other panel's place.
3. Without Pillow, only the PNG should draw. Pressing `Shift+F3` switches between the picture and its bytes.
4. In a sixel terminal (foot, WezTerm, xterm `-ti vt340`), repeat step 2.
   - **Expect:** the same, except sixel needs Pillow for every format.
5. `nav --graphics none`.
   - **Expect:** pictures show as bytes everywhere.

## 3. Mounting a disk image

1. Have an `.iso` on hand; any small one will do.
2. Press `Enter` on it.
   - **Expect:** it mounts through `udisksctl` and the panel opens inside it.
3. Go back to the `.iso` and choose *Disk > Unmount image*.
   - **Expect:** it unmounts, and any panel inside it goes back to the image's directory.
4. Without udisks2 installed, *Disk > Mount image* should be greyed.

## 4. A Hebrew keyboard layout

1. Add the Hebrew layout to your desktop and switch to it.
2. Run `./venv/bin/python tools/keyprobe.py` in ghostty, then in xfce4-terminal. Press `Alt+X` and a Latin shortcut
   such as `Ctrl+S`.
   - **Expect:** they show as `alt+x` and `ctrl+s`, not as Hebrew letters. Quit with `q` twice.
3. In Navigator with the Hebrew layout on, press `Alt+X`.
   - **Expect:** the exit question, as with the Latin layout.
4. In xfce4-terminal this needs *Disable all menu access keys* on, as before.

## 5. Hebrew inside tmux

1. In a terminal that reorders text itself (xfce4-terminal or GNOME Terminal, both VTE), start `tmux`, then
   `nav --language he`.
   - **Expect:** within a moment, a notice titled *טקסט מימין לשמאל* ("Right-to-left text") says the terminal's own
     right-to-left handling has to be switched off in its settings. It stays about 12 seconds.
2. Outside tmux, `nav --language he`.
   - **Expect:** no notice.
3. Inside tmux, `nav` in English.
   - **Expect:** no notice.

Items 4 and 5 also settle two entries in the right-to-left backlog
(`.claude/skills/navkit-bidi/reference/backlog.md`): strike them through there once they pass.
