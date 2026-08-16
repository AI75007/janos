"""`Shot` -> text you can paste into a generator.

Every renderer here is pure: shot in, string out. The CLI does the printing.
"""

from __future__ import annotations

import csv
import io
import json
import textwrap

from .model import Shot, Variant
from .parser import unwrap


def technical_tail(shot: Shot) -> Variant | None:
    """The append-to-anything camera/format block, if the spec has one."""
    return shot.tail


def prompt_targets(shot: Shot) -> list[str]:
    """Targets worth offering — the tail is an ingredient, not a prompt."""
    return shot.targets()


def beat_sheet(shot: Shot) -> str:
    return "\n".join(beat.as_prose() for beat in shot.beats)


def build_prompt(
    shot: Shot,
    target: str,
    *,
    tail: bool = True,
    beats: bool = False,
    variation: str | None = None,
    negative: bool = False,
    wrap: int | None = None,
) -> str:
    """Assemble the positive prompt for one engine.

    Order matters and is not cosmetic: the variant body carries the shot, the
    beat sheet times it, the variation overrides it, and the technical tail is
    format metadata that belongs last where it can't crowd the motion.

    Bodies are unwrapped on the way out — the spec's 80-column wrapping is for
    reading the markdown, not for the prompt box. Use `wrap` to re-wrap.
    """
    variant = shot.variant(target)
    parts = [unwrap(variant.body)]

    if beats and shot.beats:
        parts.append("Beat sheet:\n" + beat_sheet(shot))

    if variation:
        chosen = shot.variation(variation)
        parts.append(f"Variation — {chosen.name}: {chosen.body}")

    if tail and not variant.is_tail:
        tail_variant = shot.tail
        if tail_variant:
            parts.append(unwrap(tail_variant.body))

    if negative and shot.negative_prompt:
        parts.append("Negative prompt: " + shot.negative_prompt)

    text = "\n\n".join(part for part in parts if part)
    return _wrap(text, wrap)


def _wrap(text: str, width: int | None) -> str:
    if not width or width <= 0:
        return text
    out = []
    for para in text.split("\n\n"):
        lines = []
        for line in para.splitlines():
            lines.append(
                textwrap.fill(line, width=width, subsequent_indent="  ")
                if len(line) > width
                else line
            )
        out.append("\n".join(lines))
    return "\n\n".join(out)


def negative_terms(shot: Shot) -> list[str]:
    """The negative prompt as a term list, order preserved, blanks dropped."""
    flat = " ".join(shot.negative_prompt.split())
    return [term.strip() for term in flat.split(",") if term.strip()]


def beats_csv(shot: Shot) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["start", "end", "duration", "action", "camera", "light"])
    for beat in shot.beats:
        writer.writerow(
            [beat.start, beat.end, beat.duration, beat.action, beat.camera, beat.light]
        )
    return buffer.getvalue().rstrip("\n")


def to_json(shot: Shot, *, indent: int = 2) -> str:
    return json.dumps(shot.to_dict(), indent=indent, ensure_ascii=False)


def summary(shot: Shot) -> str:
    """Human-readable index card for one shot."""
    lines = [shot.title]
    if shot.logline:
        lines.append(textwrap.fill(shot.logline, width=78))
    lines.append("")
    runtime = f"{shot.runtime:g}s" if shot.runtime else "unspecified"
    lines.append(f"  runtime   {runtime} across {len(shot.beats)} beats")
    lines.append(f"  targets   {', '.join(prompt_targets(shot)) or 'none'}")
    tail_variant = technical_tail(shot)
    lines.append(f"  tail      {'yes' if tail_variant else 'no'}")
    lines.append(f"  negative  {len(negative_terms(shot))} terms")
    if shot.variations:
        lines.append(f"  variations {', '.join(v.key for v in shot.variations)}")
    if shot.notes:
        lines.append("")
        lines.append("  direction notes:")
        for note in shot.notes:
            if note.headline:
                lines.append(f"    - {note.headline}")
    return "\n".join(lines)
