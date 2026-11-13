# The calculator

`Ctrl+F6`, or *Utilities > Calculator*, opens the calculator. You type an expression on the line, and its value is
worked out as you type. `Enter` evaluates it: the expression goes into the line's history and the value is left
selected, so a digit starts a new calculation and an operator goes on from the value.

## The four faces

The calculator has four faces, chosen from the strip along its top, from the *Calculator* menu, or by pressing
`Ctrl+F6` again to go to the next one. It remembers the face you used last.

- *Simple* is a pocket calculator: digits and the four operations.
- *Classic* shows the value in five forms at once: decimal, hexadecimal, binary, octal and scientific notation.
- *Scientific* adds functions, a choice of angle unit, a memory and the last answer.
- *Programming* works in whole numbers of a chosen size, in four bases.

In *Simple*, *Scientific* and *Programming* a pad of keys under the line types into it, as the keyboard does. A
function key wraps the number before the cursor: `9` then `√` gives `SQRT(9)`.

## Expressions

| You write | What it is |
|---|---|
| `12`, `1.5`, `.5`, `1E+3` | Numbers |
| `$FF`, `0FFh`, `0x1F` | Hexadecimal numbers |
| `101b`, `0b101` | Binary numbers |
| `17o` | An octal number |
| `+`, `-`, `*`, `/` | The four operations |
| `^` | A power: `2^10` |
| `%` | The remainder of dividing two whole numbers |
| `&`, `\|`, `\`, `~` | Bitwise and, or, exclusive or, and not |
| `<<`, `>>` | Shifts |
| `=`, `<>`, `<`, `>`, `<=`, `>=` | Comparisons, which give 1 or 0 |
| `&&`, `\|\|` | And, or of two truths |
| `(`, `)` | Brackets |
| `PI` | The number π |

Capital and small letters are the same. Multiplication and division come before addition and subtraction, and a
power before them all.

The functions are `SIN`, `COS`, `TAN`, `CTAN`, `ARCTAN`, `SQR` (the square), `SQRT` (the square root), `LN`, `LG`
(the logarithm to base ten), `EXP`, `SIGN`, and `IF(condition, a, b)`, which is `a` when the condition is true
and `b` otherwise.

## Classic

The five lines show the value in each form; a number that is not whole shows its whole part in hexadecimal,
binary and octal.

- *Evaluate* works the expression out, as `Enter` does.
- *Copy As* chooses the form, and *Copy* puts the value on the clipboard in that form.
- *Close* closes the calculator.

## Scientific

- *Deg*, *Rad* and *Grad* choose the unit the trigonometric functions take and give.
- More functions: `ASIN`, `ACOS`, `ATAN`, `SINH`, `COSH`, `TANH`, `ABS`, `CBRT`, `ROOT(x, n)`, `LOG`, `LOG2`,
  `FACT`, and `!` after a number for its factorial. `E` is the number e.
- `ANS`, or the *Ans* key, is the last value evaluated.
- The memory keys: *MS* stores the value, *MR* recalls it, *M+* and *M−* add to it and subtract from it, and *MC*
  clears it.
- *2nd* and *hyp* change what the function keys type: the inverse functions, and the hyperbolic ones.

## Programming

- *HEX*, *DEC*, *OCT* and *BIN* choose the base you type numbers in. The value is shown in all four.
- *QWORD*, *DWORD*, *WORD* and *BYTE* choose the size of the number: 64, 32, 16 or 8 bits. A result that does not
  fit is cut to that size.
- *Signed* reads the number as signed. Unticked, it is never negative.
- Division gives a whole number.
- The operations can also be written as words: `AND`, `OR`, `XOR`, `NAND`, `NOR`, `NOT`, `MOD`, `SHL`, `SHR`,
  `SAR`, `ROL` and `ROR`.
- *Bit toggling keypad*, in the *Calculator* menu, shows the 64 bits in place of the keys. A click or `Space`
  flips a bit.

## Keys

| Key | What it does |
|---|---|
| `Enter` | Evaluate |
| `Ctrl+F6` | The next face |
| `Ctrl+1` to `Ctrl+4` | Simple, Classic, Scientific, Programming, where the terminal sends these keys |
| `Down` on the line | The history of expressions |
| `Esc` | Close the calculator |
