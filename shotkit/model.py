"""Data model for a shot spec.

A shot spec is a markdown document under `shots/`. These dataclasses are the
parsed form of one — everything the renderers need, and nothing about markdown.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Any


def slug(text: str) -> str:
    """`Veo / Sora` -> `veo-sora`, `Technical tail` -> `technical-tail`."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


@dataclass(frozen=True)
class Beat:
    """One row of the beat breakdown — a slice of the runtime."""

    start: float
    end: float
    action: str
    camera: str
    light: str

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 3)

    @property
    def label(self) -> str:
        return f"{self.start:g}–{self.end:g}s"

    def as_prose(self) -> str:
        """One line of a beat sheet, for prompts that accept a timeline."""
        return f"{self.label}: {self.action}. Camera: {self.camera}. Light: {self.light}."


class UnknownTarget(LookupError):
    """No prompt variant (or variation) answers to that name."""

    def __str__(self) -> str:  # LookupError reprs its arg; we want it plain
        return str(self.args[0]) if self.args else ""


@dataclass(frozen=True)
class Variant:
    """A prompt body targeted at one family of engines.

    `engines` is every name in the heading split on `/`, slugified, so
    `### Veo / Sora (prose)` is reachable as either `veo` or `sora`.
    """

    name: str
    engines: tuple[str, ...]
    body: str
    note: str = ""

    @property
    def key(self) -> str:
        return slug(self.name)

    @property
    def is_tail(self) -> bool:
        """A technical tail is an ingredient appended to prompts, not a prompt."""
        return self.key in ("technical-tail", "tail") or self.key.endswith("-tail")

    def matches(self, target: str) -> bool:
        t = slug(target)
        return t == self.key or t in self.engines


@dataclass(frozen=True)
class Note:
    headline: str
    body: str


@dataclass(frozen=True)
class Variation:
    name: str
    body: str

    @property
    def key(self) -> str:
        return slug(self.name)


@dataclass
class Shot:
    """A parsed shot spec."""

    title: str
    logline: str = ""
    source_prompt: str = ""
    runtime: float | None = None
    beats: list[Beat] = field(default_factory=list)
    variants: list[Variant] = field(default_factory=list)
    negative_prompt: str = ""
    notes: list[Note] = field(default_factory=list)
    variations: list[Variation] = field(default_factory=list)
    path: str = ""

    @property
    def key(self) -> str:
        return slug(self.title)

    @property
    def covered(self) -> float:
        """Total runtime actually described by the beats."""
        return round(sum(b.duration for b in self.beats), 3)

    @property
    def tail(self) -> Variant | None:
        """The append-to-anything camera/format block, if the spec has one."""
        return next((v for v in self.variants if v.is_tail), None)

    def variant(self, target: str) -> Variant:
        for v in self.variants:
            if v.matches(target):
                return v
        raise UnknownTarget(
            f"no prompt variant for {target!r}; available: "
            f"{', '.join(self.targets()) or 'none'}"
        )

    def targets(self, *, include_tail: bool = False) -> list[str]:
        """Every name a `--target` can be given, deduped, in spec order."""
        seen: list[str] = []
        for v in self.variants:
            if v.is_tail and not include_tail:
                continue
            for name in (v.key, *v.engines):
                if name not in seen:
                    seen.append(name)
        return seen

    def variation(self, key: str) -> Variation:
        for var in self.variations:
            if var.key == slug(key):
                return var
        known = ", ".join(v.key for v in self.variations) or "none"
        raise UnknownTarget(f"no variation {key!r}; available: {known}")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["key"] = self.key
        data["covered"] = self.covered
        for raw, beat in zip(data["beats"], self.beats):
            raw["duration"] = beat.duration
            raw["label"] = beat.label
        for raw, variant in zip(data["variants"], self.variants):
            raw["key"] = variant.key
            raw["engines"] = list(variant.engines)
            raw["is_tail"] = variant.is_tail
        for raw, variation in zip(data["variations"], self.variations):
            raw["key"] = variation.key
        return data
