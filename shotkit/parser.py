"""Markdown -> `Shot`.

The parser is deliberately forgiving: a spec may omit any section except the
title, and unknown sections are ignored rather than fatal. What it will not do
is guess — a malformed beat table raises, because a silently dropped beat is
worse than a failed parse.
"""

from __future__ import annotations

import re
from pathlib import Path

from .model import Beat, Note, Shot, Variant, Variation, slug

# `0.0–2.0s`, `0-2 s`, `6.5 – 7.2s` — en dash, em dash or hyphen.
_TIME_RANGE = re.compile(
    r"(\d+(?:\.\d+)?)\s*[–—-]\s*(\d+(?:\.\d+)?)\s*s?\b"
)
# `## Beat breakdown (8s)` -> 8.0
_RUNTIME = re.compile(r"\((\d+(?:\.\d+)?)\s*s(?:ec(?:onds)?)?\)")
_FENCE = re.compile(r"^```[^\n]*\n(.*?)^```", re.M | re.S)
_BOLD_LEAD = re.compile(r"^\*\*(.+?)\*\*\s*(.*)$", re.S)
_HEADING_NOTE = re.compile(r"^(.*?)\s*\((.*)\)\s*$")


class ShotParseError(ValueError):
    """Raised when a spec section is present but unreadable."""


def _blocks(text: str) -> list[str]:
    """Split on blank lines, dropping horizontal rules and empties."""
    out = []
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if block and not re.fullmatch(r"-{3,}|\*{3,}|_{3,}", block):
            out.append(block)
    return out


def unwrap(text: str) -> str:
    """Undo hard wrapping so a prompt pastes as flowing paragraphs.

    Blank-line paragraph breaks survive. So does the shape of a structured
    prompt: a line matching `Key: value` starts a new line, and its indented
    continuations fold into it.
    """
    paragraphs = []
    for para in re.split(r"\n\s*\n", text.strip()):
        lines = [ln for ln in para.splitlines() if ln.strip()]
        if not lines:
            continue
        structured = sum(
            1 for ln in lines if re.match(r"^\S[^:\n]{0,40}:\s", ln)
        ) >= max(2, len(lines) // 2)
        if structured:
            folded: list[str] = []
            for line in lines:
                if line[:1].isspace() and folded:
                    folded[-1] += " " + line.strip()
                else:
                    folded.append(line.rstrip())
            paragraphs.append("\n".join(folded))
        else:
            paragraphs.append(" ".join(ln.strip() for ln in lines))
    return "\n\n".join(paragraphs)


def _sections(body: str) -> list[tuple[int, str, str]]:
    """Yield (level, heading, body) for every `##`/`###` heading, in order.

    Fenced code is masked first so a `#` inside a prompt is never a heading.
    """
    masked = _FENCE.sub(lambda m: "\x00" * len(m.group(0)), body)
    heads = [
        (m.start(), len(m.group(1)), m.group(2).strip())
        for m in re.finditer(r"^(#{2,3}) +(.+)$", masked, re.M)
    ]
    out = []
    for i, (pos, level, title) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else len(body)
        start = body.index("\n", pos) + 1 if "\n" in body[pos:] else len(body)
        out.append((level, title, body[start:end].strip()))
    return out


def _fences(text: str) -> list[str]:
    return [m.group(1).rstrip("\n") for m in _FENCE.finditer(text)]


def _parse_beats(body: str) -> list[Beat]:
    rows = [
        ln.strip()
        for ln in body.splitlines()
        if ln.strip().startswith("|") and ln.strip().endswith("|")
    ]
    beats: list[Beat] = []
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) < 4:
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):  # separator
            continue
        match = _TIME_RANGE.search(cells[0])
        if not match:
            if cells[0].lower().startswith("time"):  # header row
                continue
            raise ShotParseError(f"beat row has no time range: {row}")
        start, end = float(match.group(1)), float(match.group(2))
        if end <= start:
            raise ShotParseError(f"beat ends before it starts: {row}")
        beats.append(
            Beat(
                start=start,
                end=end,
                action=cells[1],
                camera=cells[2],
                light=cells[3],
            )
        )
    return beats


def _parse_variants(subsections: list[tuple[int, str, str]]) -> list[Variant]:
    variants: list[Variant] = []
    for level, title, body in subsections:
        if level != 3:
            continue
        blocks = _fences(body)
        if not blocks:
            continue
        name, note = title, ""
        match = _HEADING_NOTE.match(title)
        if match:
            name, note = match.group(1).strip(), match.group(2).strip()
        engines = tuple(slug(part) for part in name.split("/") if slug(part))
        variants.append(
            Variant(name=name, engines=engines, body=blocks[0], note=note)
        )
    return variants


def _parse_notes(body: str) -> list[Note]:
    notes = []
    for block in _blocks(body):
        match = _BOLD_LEAD.match(block)
        if match:
            headline = match.group(1).strip().rstrip(".")
            notes.append(Note(headline=headline, body=unwrap(match.group(2))))
        else:
            notes.append(Note(headline="", body=unwrap(block)))
    return notes


def _parse_variations(body: str) -> list[Variation]:
    variations: list[Variation] = []
    current: list[str] = []

    def flush() -> None:
        if not current:
            return
        text = unwrap(" ".join(current))
        match = re.match(r"\*\*(.+?)\*\*\s*[–—-]?\s*(.*)", text, re.S)
        if match:
            variations.append(
                Variation(name=match.group(1).strip(), body=match.group(2).strip())
            )
        current.clear()

    for line in body.splitlines():
        if re.match(r"^\s*[-*]\s+", line):
            flush()
            current.append(re.sub(r"^\s*[-*]\s+", "", line).strip())
        elif line.strip() and current:
            current.append(line.strip())
        elif not line.strip():
            flush()
    flush()
    return variations


def parse(text: str, path: str = "") -> Shot:
    """Parse a shot spec. `path` is recorded for error messages only."""
    title_match = re.search(r"^# +(.+)$", text, re.M)
    if not title_match:
        raise ShotParseError(f"{path or 'spec'}: no `# ` title line")
    title = re.sub(r"^shot:\s*", "", title_match.group(1).strip(), flags=re.I)

    sections = _sections(text)
    preamble = text[title_match.end() :]
    if sections:
        first = re.search(r"^#{2,3} +" + re.escape(sections[0][1]), preamble, re.M)
        if first:
            preamble = preamble[: first.start()]

    shot = Shot(title=title, path=path)
    blocks = _blocks(preamble)
    if blocks:
        shot.logline = unwrap(blocks[0])

    for index, (level, heading, body) in enumerate(sections):
        if level != 2:
            continue
        name = slug(heading)
        subsections = []
        for sub in sections[index + 1 :]:
            if sub[0] == 2:
                break
            subsections.append(sub)

        if name.startswith("source-prompt"):
            quoted = "\n".join(
                re.sub(r"^\s*>\s?", "", ln) for ln in body.splitlines() if ln.strip().startswith(">")
            )
            shot.source_prompt = unwrap(quoted or body)
        elif name.startswith("beat"):
            runtime = _RUNTIME.search(heading)
            shot.runtime = float(runtime.group(1)) if runtime else None
            shot.beats = _parse_beats(body)
        elif name.startswith("prompt-variant"):
            shot.variants = _parse_variants(subsections)
        elif name.startswith("negative"):
            fences = _fences(body)
            shot.negative_prompt = unwrap(fences[0] if fences else body)
        elif name.startswith("direction-note"):
            shot.notes = _parse_notes(body)
        elif name.startswith("variation"):
            shot.variations = _parse_variations(body)

    return shot


def parse_file(path: str | Path) -> Shot:
    path = Path(path)
    return parse(path.read_text(encoding="utf-8"), path=str(path))


def load_dir(directory: str | Path) -> list[Shot]:
    """Parse every `.md` in a directory, sorted by filename."""
    return [parse_file(p) for p in sorted(Path(directory).glob("*.md"))]
