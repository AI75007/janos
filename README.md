# janos

Shot specs for AI video generation, and `shotkit` — the tool that turns them
into prompts you can paste into an engine.

A shot spec is one markdown file under `shots/`: the source prompt, a beat
breakdown, per-engine prompt variants, a negative prompt, and the direction
notes explaining why the shot is written the way it is. The markdown is the
source of truth; `shotkit` is a reader for it, never a second copy.

## Quick start

No dependencies, Python 3.10+:

```
python3 -m shotkit list
python3 -m shotkit prompt monarch-butterfly-ferrari --target veo --negative
```

Or install it and get the `shotkit` command: `pip install -e .`

## Commands

| Command | What it does |
|---|---|
| `list [dir]` | Index every spec: name, runtime, engine targets |
| `show <spec>` | Index card — runtime, targets, negative term count, note headlines |
| `prompt <spec>` | Render the positive prompt for one engine |
| `negative <spec>` | The negative prompt, whole or `--list` one term per line |
| `beats <spec>` | Beat breakdown as a sheet, `--format csv`, or `--format json` |
| `json <spec>` | The whole parsed spec as JSON |
| `validate [spec\|dir]` | Structural check; non-zero exit on errors |

`<spec>` is a path, a filename, or a fragment of one — `monarch` resolves to
`shots/monarch-butterfly-ferrari.md` as long as it's unambiguous.

### `prompt`

```
shotkit prompt monarch -t runway --beats --variation reflection-first -n
```

- `-t, --target` — engine name (`veo`, `sora`, `runway`, `kling`) or variant
  key. Both halves of a `### Veo / Sora` heading are targets. Defaults to the
  first variant in the spec.
- `--no-tail` — omit the technical tail, which is otherwise appended last
- `--beats` — append the beat sheet as a timed shot list
- `--variation` — fold in one of the spec's variations
- `-n, --negative` — append the negative prompt
- `--wrap COLS` — hard wrap the output

Prompt bodies come out unwrapped: the spec's 80-column wrapping is for reading
the markdown, not for the prompt box. Structured prompts keep their field
shape — a `Key: value` line stays one line, indented continuations fold into
it.

### `validate`

Errors are things that would generate wrong: beats that gap, overlap, start
late, or don't add up to the runtime the heading declares; a missing or empty
prompt body. Warnings are defensible — no technical tail, a repeated negative
term. Exit status is non-zero only for errors, so it works in CI:

```
shotkit validate shots/
```

## Writing a spec

`shotkit` reads these `##` sections, all optional except the `#` title:

- **Source prompt** — a blockquote; the original ask, kept for provenance
- **Beat breakdown (8s)** — a table of `Time | Action | Camera | Light`. The
  runtime in the heading is checked against the last beat's end.
- **Prompt variants** — `###` subsections, each with one fenced block. The
  heading names the engines (`Veo / Sora`); a heading ending in "tail" is the
  technical tail and gets appended to other prompts rather than rendered alone.
- **Negative prompt** — a fenced comma-separated list
- **Direction notes** — paragraphs led by a `**bold**` headline
- **Variations** — a bullet list of `**Name** — description`

A `#` inside a fenced block is never read as a heading, so prompt bodies can
contain anything.

## Library use

```python
from shotkit import parse_file, build_prompt, check

shot = parse_file("shots/monarch-butterfly-ferrari.md")
print(shot.runtime, len(shot.beats), shot.targets())
print(build_prompt(shot, "veo", negative=True))
assert not check(shot)
```

## Tests

```
python3 -m unittest discover -s tests
```
