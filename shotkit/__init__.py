"""shotkit — parse shot specs and render prompts for video generators.

    from shotkit import parse_file, build_prompt

    shot = parse_file("shots/monarch-butterfly-ferrari.md")
    print(build_prompt(shot, "veo", negative=True))
"""

from .model import Beat, Note, Shot, UnknownTarget, Variant, Variation
from .parser import ShotParseError, load_dir, parse, parse_file, unwrap
from .render import (
    beat_sheet,
    beats_csv,
    build_prompt,
    negative_terms,
    prompt_targets,
    summary,
    technical_tail,
    to_json,
)
from .validate import Issue, check, errors

__version__ = "0.1.0"

__all__ = [
    "Beat",
    "Issue",
    "Note",
    "Shot",
    "ShotParseError",
    "UnknownTarget",
    "Variant",
    "Variation",
    "__version__",
    "beat_sheet",
    "beats_csv",
    "build_prompt",
    "check",
    "errors",
    "load_dir",
    "negative_terms",
    "parse",
    "parse_file",
    "prompt_targets",
    "summary",
    "technical_tail",
    "to_json",
    "unwrap",
]
