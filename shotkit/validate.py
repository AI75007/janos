"""Structural checks on a shot spec.

Errors are things that would make the spec generate wrong: a beat table that
doesn't add up to the stated runtime, a missing prompt body. Warnings are
things a director would want to know about but can defend.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import Shot
from .render import negative_terms, prompt_targets, technical_tail

TOLERANCE = 0.001


@dataclass(frozen=True)
class Issue:
    level: str  # "error" | "warning"
    message: str

    def __str__(self) -> str:
        return f"{self.level}: {self.message}"


def check(shot: Shot) -> list[Issue]:
    issues: list[Issue] = []
    err = lambda msg: issues.append(Issue("error", msg))  # noqa: E731
    warn = lambda msg: issues.append(Issue("warning", msg))  # noqa: E731

    if not shot.logline:
        warn("no logline under the title")

    if not shot.beats:
        err("no beat breakdown")
    else:
        first = shot.beats[0]
        if abs(first.start) > TOLERANCE:
            err(f"first beat starts at {first.start:g}s, not 0")
        for previous, beat in zip(shot.beats, shot.beats[1:]):
            gap = round(beat.start - previous.end, 3)
            if gap > TOLERANCE:
                err(f"{gap:g}s gap between {previous.label} and {beat.label}")
            elif gap < -TOLERANCE:
                err(f"{-gap:g}s overlap between {previous.label} and {beat.label}")
        if shot.runtime is None:
            warn("beat breakdown heading declares no runtime, e.g. `(8s)`")
        else:
            end = shot.beats[-1].end
            if abs(end - shot.runtime) > TOLERANCE:
                err(
                    f"beats end at {end:g}s but the heading declares "
                    f"{shot.runtime:g}s"
                )

    if not shot.variants:
        err("no prompt variants")
    for variant in shot.variants:
        if not variant.body.strip():
            err(f"prompt variant {variant.key!r} has an empty code block")
    if shot.variants and not prompt_targets(shot):
        err("every prompt variant is a technical tail — nothing to render")
    if not technical_tail(shot):
        warn("no technical tail block")

    if not shot.source_prompt:
        warn("no source prompt recorded")

    terms = negative_terms(shot)
    if not terms:
        warn("no negative prompt")
    seen: set[str] = set()
    for term in terms:
        low = term.lower()
        if low in seen:
            warn(f"negative prompt repeats {term!r}")
        seen.add(low)

    return issues


def errors(issues: list[Issue]) -> list[Issue]:
    return [issue for issue in issues if issue.level == "error"]
