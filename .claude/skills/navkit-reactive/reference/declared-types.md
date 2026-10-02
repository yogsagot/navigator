## Declared types: a write is checked, a computed value is not

Every reactive attribute in the repository is already annotated — `width: int = reactive(0)`,
`parent: Widget | None = reactive(None)` — and until now the annotation was addressed to the type checker alone. It is
the only statement of intent an attribute carries, so `Reactive.__set__` reads it and refuses a write that contradicts
it with `ReactiveTypeError`. Nothing had to be spelled twice for this: the declarations were not touched.

**The check guards the boundary where a value enters the graph, and nothing else.** A plain assignment is that
boundary — it is where a value arrives from outside, from an event handler, a parsed file, a test. A value a *bound
expression* computed is not checked, and neither is a `computed`'s return, because both were derived from values that
were already checked at their own boundaries. The alternative was checking inside `_Cell._recompute`, which is
consistent in a different way and was rejected on two counts: the cell has no declaration to consult, so every cell
would have to carry the erased check; and a recompute happens lazily on read, so the refusal would arrive during a
paint, at a read far from the assignment that caused it, cached the way `_recompute` caches every other failure. A
write is the rare operation and the one with a caller to blame. Recomputes are the hot path and have none.

**Resolution is lazy, and one annotation at a time.** `typing.get_type_hints()` is all-or-nothing, and this repository
already contains the case that breaks it: `Widget._application` is annotated `Application | None`, with `Application`
imported only under `TYPE_CHECKING` to break an import cycle. One name it cannot see would take *every other
annotation on the class* down with it, so a single unresolvable import would quietly disarm the check for the whole
widget tree. `_resolve_annotation` therefore evaluates one string and answers `UNKNOWN` if it cannot, leaving that
attribute unchecked and its eleven neighbours checked. Laziness is forced by a second case: `__set_name__` runs while
the class body is still executing, and `parent: Widget | None` cannot be evaluated there, because `Widget` is precisely
what is being defined. Both the type and its erased form are worked out on first ask and kept on the declaration, which
is shared by every instance — resolving costs some hundred times what checking against the result does.

**`UNKNOWN` is not `Any`.** `Any` is an answer: the author said this attribute takes anything. `UNKNOWN` is the absence
of one — no annotation, or one naming something that does not exist at run time. Both go unchecked, so the distinction
buys nothing today; it is kept because a consumer that wants to *report* on a class's reactive surface, which is
exactly what the navml generator will do, needs to tell "unconstrained" from "unknown" and could not recover it later.

**The erasure is shallow, on purpose.** `frozenset[str]` checks the container and not the elements, because checking
them means walking every collection on every write — and `classes` is a `frozenset` that is replaced whenever a state
changes. A union is flattened to the tuple `isinstance` takes rather than handed over whole, which works for `X | Y`
but not for `Optional[X]` or a union with a parameterised arm. A form too clever to erase — `Literal`, or an arm that
is itself unerasable — disarms the *whole* union rather than half-checking it, since a partial check would refuse
values the annotation allows.

**There is no flag to turn it off.** Opting out is the same act as never opting in: leave the annotation off, or write
`Any`. A per-attribute switch would be a second way to say what the annotation already says.

**The declared default is not checked.** `n: int = reactive("zero")` is accepted. The default sits three characters
from the annotation that contradicts it, where a type checker catches it for free and a reader catches it faster; the
run-time check exists for values arriving later, from somewhere else. Checking it would also mean running every
`factory=` at declaration time or per instance, for a class of mistake that never survives its first reading.

**A bound attribute reports being bound, not being mistyped.** Assigning a wrong-typed value over a live binding raises
the existing "call `unbind()` first", because correcting the type would not make that assignment legal either — the
guard that refuses every value alike is the one with something useful to say. So `__set__` consults the cell before it
consults the annotation, which is the only reason the two lines are in that order.

### A declaration is an extension point

`_Declaration` is the base of `Reactive` and `Computed`, and `declarations(cls)` is what a code generator asks for a
class's reactive surface. navml needs to subclass the first so that its own descriptors are answered for by the second
— an `alias`, which redirects a name on a component to an attribute of a widget declared inside it, is a declaration
whose `cell()` returns a cell it does not own (`navml/DESIGN.md`, *Aliases*). That makes the base a documented shape
rather than an implementation detail, and three things follow.

**It should have a public name. Now done:** `Declaration`, exported from `navkit`, with `_Declaration` kept as an
alias because navml's prototype already imports the private spelling and a dependency that is going to exist should be
spelled honestly. The layering is unchanged:
navkit still knows nothing of navml, and navml subclasses downward, which is the direction that was always allowed.

**`cell()` is the overridable part, and the only one.** Everything that walks a declaration — `unbind()`, `is_bound()`,
`peek()`, the identity check that the class really declares the attribute — goes through it or through ordinary
attribute access, so a subclass answering with another object's cell is answered correctly everywhere without navkit
learning why. `_resolve_annotation`'s caching is the constraint on such a subclass rather than on navkit: the type is
worked out once and kept on the declaration that every instance shares, so a subclass must not derive it per instance.

**A `Binding` can be copied with its owner fixed, and that method is navkit's to give.** `bind()`'s convention is
that an expression's one argument is the object that *owns* the attribute, and there is exactly one place where the
owner and the object the expression was written against differ: a declaration that forwards to another widget's
attribute. The expression would be handed the target, which usually has an attribute of that name too — so nothing
raises, a wrong number is computed, and it goes on being computed. `Binding.owned_by(owner)` returns a copy whose
expression is always called with `owner`, carrying `equal` across because the copy replaces the original at the cell.

It lives here rather than in navml for two reasons. It bends navkit's own convention, so navkit should be the one to
say how; and it composes — the wrapper ignores its own argument, so a forward into something that forwards further
re-wraps an expression that is already owned and the *outermost* owner wins, which is the answer a reader of the outer
document expects. The expression has to be lifted into a local before the lambda closes over it: closing over the
`Binding` while the caller rebinds the name on the same line gives a wrapper that finds itself at call time and
recurses.

**`unbind()` and `is_bound()` refuse a `Computed`, and now say so.** Found while working the above out, and a bug
here rather than anything markup caused: `_declaration()` checks only that its argument is a declaration, and
`Computed` is one, so `is_bound()` answered `True` for every computed — a cell carrying a `compute` is what being
bound means to it — and `unbind()` unlinked that cell, leaving the computed frozen at its last value and deaf to its
inputs for good. Measured rather than reasoned about: a `total` of 3 stayed 3 after the source it sums went to 10.
`_bindable()` is the guard, and it **rejects `Computed` rather than requiring `Reactive`**, so a declaration
subclassed outside this module stays bindable — which is the extension point above being used the first time it is
described. `peek()` still takes either, because reading a derived value without subscribing to it is a legitimate
thing to ask of a computed.

