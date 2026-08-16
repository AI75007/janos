"""Command line front end.

    python -m shotkit prompt monarch-butterfly-ferrari --target veo
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import render, validate
from .model import Shot, UnknownTarget
from .parser import ShotParseError, load_dir, parse_file

DEFAULT_DIR = os.environ.get("SHOTKIT_DIR", "shots")


def _shots_dir() -> Path:
    """`shots/` relative to the cwd, falling back to the repo's own."""
    here = Path(DEFAULT_DIR)
    if here.is_dir():
        return here
    return Path(__file__).resolve().parent.parent / DEFAULT_DIR


def resolve(spec: str) -> Path:
    """Accept a path, a filename, or a bare shot key like `monarch-...`."""
    candidate = Path(spec)
    if candidate.is_file():
        return candidate
    directory = _shots_dir()
    for name in (spec, f"{spec}.md"):
        guess = directory / name
        if guess.is_file():
            return guess
    matches = [p for p in sorted(directory.glob("*.md")) if spec.lower() in p.stem.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise SystemExit(
            f"{spec!r} matches {len(matches)} shots: "
            + ", ".join(p.stem for p in matches)
        )
    known = ", ".join(p.stem for p in sorted(directory.glob("*.md"))) or "none"
    raise SystemExit(f"no shot spec for {spec!r} (in {directory}/); known: {known}")


def load(spec: str) -> Shot:
    try:
        return parse_file(resolve(spec))
    except ShotParseError as exc:
        raise SystemExit(str(exc)) from exc


def cmd_list(args: argparse.Namespace) -> int:
    directory = Path(args.dir) if args.dir else _shots_dir()
    shots = load_dir(directory)
    if not shots:
        print(f"no shot specs in {directory}/", file=sys.stderr)
        return 1
    # The first column is the filename stem — what every other command takes.
    names = [Path(shot.path).stem for shot in shots]
    width = max(len(name) for name in names)
    for name, shot in zip(names, shots):
        runtime = f"{shot.runtime:g}s" if shot.runtime else "  ?"
        targets = ", ".join(render.prompt_targets(shot))
        print(f"{name.ljust(width)}  {runtime:>5}  {targets}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    print(render.summary(load(args.spec)))
    return 0


def cmd_prompt(args: argparse.Namespace) -> int:
    shot = load(args.spec)
    target = args.target or (render.prompt_targets(shot) or [""])[0]
    if not target:
        raise SystemExit(f"{shot.key}: no prompt variants to render")
    try:
        text = render.build_prompt(
            shot,
            target,
            tail=not args.no_tail,
            beats=args.beats,
            variation=args.variation,
            negative=args.negative,
            wrap=args.wrap,
        )
    except UnknownTarget as exc:
        raise SystemExit(str(exc)) from exc
    print(text)
    return 0


def cmd_negative(args: argparse.Namespace) -> int:
    shot = load(args.spec)
    if args.list:
        for term in render.negative_terms(shot):
            print(term)
    else:
        print(shot.negative_prompt)
    return 0


def cmd_beats(args: argparse.Namespace) -> int:
    shot = load(args.spec)
    if args.format == "csv":
        print(render.beats_csv(shot))
    elif args.format == "json":
        import json

        print(json.dumps(shot.to_dict()["beats"], indent=2, ensure_ascii=False))
    else:
        print(render.beat_sheet(shot))
    return 0


def cmd_json(args: argparse.Namespace) -> int:
    print(render.to_json(load(args.spec), indent=args.indent))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    if not args.spec:
        targets = sorted(_shots_dir().glob("*.md"))
    elif Path(args.spec).is_dir():
        targets = sorted(Path(args.spec).glob("*.md"))
    else:
        targets = [resolve(args.spec)]
    if not targets:
        print("no shot specs to validate", file=sys.stderr)
        return 1
    failed = False
    for path in targets:
        try:
            shot = parse_file(path)
        except ShotParseError as exc:
            print(f"{path}: error: {exc}")
            failed = True
            continue
        issues = validate.check(shot)
        if validate.errors(issues):
            failed = True
        if not issues:
            print(f"{path}: ok")
            continue
        print(f"{path}:")
        for issue in issues:
            if issue.level == "warning" and args.quiet:
                continue
            print(f"  {issue}")
    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shotkit",
        description="Turn shot specs into engine-ready prompts.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="index every shot spec")
    p.add_argument("dir", nargs="?", help=f"directory of specs (default: {DEFAULT_DIR}/)")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show", help="summarise one shot")
    p.add_argument("spec")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("prompt", help="render the positive prompt")
    p.add_argument("spec")
    p.add_argument("-t", "--target", help="engine or variant name, e.g. veo, runway")
    p.add_argument("--no-tail", action="store_true", help="omit the technical tail")
    p.add_argument("--beats", action="store_true", help="append the beat sheet")
    p.add_argument("--variation", help="apply a variation from the spec")
    p.add_argument("-n", "--negative", action="store_true", help="append the negative prompt")
    p.add_argument("--wrap", type=int, default=0, metavar="COLS", help="hard wrap output")
    p.set_defaults(func=cmd_prompt)

    p = sub.add_parser("negative", help="print the negative prompt")
    p.add_argument("spec")
    p.add_argument("-l", "--list", action="store_true", help="one term per line")
    p.set_defaults(func=cmd_negative)

    p = sub.add_parser("beats", help="print the beat breakdown")
    p.add_argument("spec")
    p.add_argument("-f", "--format", choices=("sheet", "csv", "json"), default="sheet")
    p.set_defaults(func=cmd_beats)

    p = sub.add_parser("json", help="dump the parsed spec as JSON")
    p.add_argument("spec")
    p.add_argument("--indent", type=int, default=2)
    p.set_defaults(func=cmd_json)

    p = sub.add_parser("validate", help="check specs for structural problems")
    p.add_argument("spec", nargs="?", help="spec or directory (default: all)")
    p.add_argument("-q", "--quiet", action="store_true", help="errors only")
    p.set_defaults(func=cmd_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
