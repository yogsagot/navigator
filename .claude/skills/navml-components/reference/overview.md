## Where the inspiration is taken from

**QML for the architecture, Kivy for the syntax.** From QML come the shape of the language and its semantics: a
declarative tree of objects, `id`s naming them, properties that are expressions re-evaluated when what they read
changes, and a component that is a class. From Kivy comes the surface, because the file should read like Python:

- **blocks are made by indentation**, not by braces;
- **no semicolons**, and one property per line;
- a widget opens a block with a trailing colon — `Panel:` — and its properties and children are the lines indented under
  it;
- `id: left` is a directive rather than a property — see *Ids* below.

So a declaration reads:

```
Panel:
    id: left
    width: parent.width // 2
```

and never `Panel { id: left; width: parent.width // 2 }`.

