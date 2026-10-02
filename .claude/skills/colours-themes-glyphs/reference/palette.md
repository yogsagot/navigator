## Terminal capabilities: the palette stays exact, the edge quantises

`TerminalInfo` in `capabilities.py` holds what the terminal supports and makes the decisions that follow. The question
that forced it was whether the generated `.nss` themes should carry
`#rrggbb` at all: eight of DOS Navigator's eleven palettes reprogram the sixteen VGA colour registers, and truecolor is
near-universal but not universal.

**The decision is made once, at the edge.** A widget asks for the colour it wants, a sheet records the colour the
original asked for, and only `render_diff` — the last place a `Style`
exists before it becomes bytes — asks whether this terminal can express it. Nothing upstream of that has to know or
care.

**So the palette stays exact.** Baking a sixteen-colour approximation into the sheet at generation time would throw the
original away permanently, and on a terminal that can show it, for nothing. It would also be wrong rather than merely
lossy: `BW.PAL` is a greyscale ramp whose *blue* register holds a mid grey, so writing the DOS colour name `blue` into
the sheet would come back a real blue everywhere. Quantising at the edge gives a grey on a sixteen-colour terminal and
the exact grey on a capable one.

**An index is left alone unless a palette says what it means.** With `TerminalInfo.palette`
unset — the kit's default, since navkit knows nothing about DOS — `blue` in a sheet reaches the terminal as index 4 and
the user's own theme decides what blue looks like; approximating it against our reference table would replace their
theme with ours. A truecolor triple has no such claim on anything and is quantised, against the fixed part of the xterm
palette: indices 0–15 are skipped when targeting 256 colours for the same reason, since what a terminal paints for those
is not knowable from here.

### What an index in a *transcribed* sheet actually means

That rule alone makes Navigator unreadable in a terminal whose sixteen colours are not a VGA adapter's — a light IDE
scheme paints `blue` pale and `light_gray` near-white, and the app is white-on-white. It is not a quantising bug:
`norton.nss` says `blue` because `NORTON.PAL` left the colour registers *alone*, which is a statement about the IBM DAC
and not an invitation for the terminal to choose. The palette stays exact; what was missing was somewhere to say what an
index is exact *about*.

**So `TerminalInfo.palette` names the sixteen, and resolution happens at the same edge.** An index is resolved through
it before the depth checks, and from there it is an ordinary triple.
`VGA_PALETTE` is the reference table the quantiser already carried, under the name that says what it is: the same
colours `tools/palconv.py` holds as six-bit DAC values.

**Pinning is free on a terminal that could not have shown the difference.** Resolving an index through `VGA_PALETTE` and
quantising the result searches the very table it came from, so
`_nearest` returns the index it started with — byte-identical output on a sixteen-colour terminal, and the eight-colour
fold lands in the same place too. Only a terminal that *can* do better is asked for anything different, which is what
makes it safe as an application default rather than a flag nobody finds.

**The kit's default is `None`; the application's is the VGA DAC.** navkit is a terminal library and has no business
asserting what `blue` is. `navigator` is a recreation of a program that drove a VGA adapter, so it pins by default and
`--palette terminal` hands the question back.
`NAVKIT_PALETTE` overrides the application's default the way `NAVKIT_COLORS` overrides the detected depth, and an
explicit flag outranks the variable in turn.

**A sixteen-colour terminal is reachable only by rewriting its registers**, which is what
`--reprogram-palette` does: OSC 4 for the sixteen on `start()`, OSC 104 on `stop()`. It stays opt-in because it repaints
colours outside this application's cells for as long as it runs, and a process killed outright leaves them changed. On a
terminal that can name more, pinning has already done the job and reprogramming changes nothing visible.

**Detection is conservative and overridable.** A terminal that does not say it supports more gets sixteen colours,
because being downgraded on a capable terminal is a disappointment while being upgraded on an incapable one is a
screenful of unreadable escapes — and `COLORTERM` is the only reliable statement of truecolor support. `NAVKIT_COLORS`
overrides the guess outright, and outranks `NO_COLOR`, which in turn outranks any claim of support.

**The answer is fixed for the terminal's life**, detected in `Terminal.__init__` rather than on use. A frame that
quantised differently from the one before it would show up as the diff repainting cells whose content never changed.

A capability is separate from a preference, and either vetoes: `Terminal(mouse=False)` says the caller does not want
mouse input, `info.mouse` says asking would be no use. `stop()` cancels exactly what `start()` asked for, so a feature
never turned on is never turned off either.

