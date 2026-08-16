"""Tests for shotkit. Stdlib unittest, no dependencies.

    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import io
import sys
import textwrap
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import shotkit
from shotkit import cli, parser, render, validate
from shotkit.model import UnknownTarget

REPO = Path(__file__).resolve().parent.parent
MONARCH = REPO / "shots" / "monarch-butterfly-ferrari.md"

MINIMAL = textwrap.dedent(
    """\
    # Shot: Test Shot

    A one-line logline that is
    hard wrapped across lines.

    ## Source prompt

    > A cat sits
    > on a wall.

    ## Beat breakdown (4s)

    | Time | Action | Camera | Light |
    |---|---|---|---|
    | 0.0–2.0s | Cat sits | Wide | Day |
    | 2.0–4.0s | Cat blinks | Push | Dusk |

    ## Prompt variants

    ### Veo / Sora (prose)

    ```
    A cat sits on a wall.
    ```

    ### Technical tail (append to any of the above)

    ```
    Shot on 50mm, T2.
    ```

    ## Negative prompt

    ```
    blurry, extra legs
    ```

    ## Direction notes

    **Stillness is the shot.** Do not let the cat move.

    ## Variations

    - **Night version** — same beats, after dark.
    """
)


class ParseMinimalTest(unittest.TestCase):
    def setUp(self) -> None:
        self.shot = parser.parse(MINIMAL, path="minimal.md")

    def test_title_drops_shot_prefix(self) -> None:
        self.assertEqual(self.shot.title, "Test Shot")
        self.assertEqual(self.shot.key, "test-shot")

    def test_logline_is_unwrapped(self) -> None:
        self.assertEqual(
            self.shot.logline, "A one-line logline that is hard wrapped across lines."
        )

    def test_source_prompt_strips_quote_markers(self) -> None:
        self.assertEqual(self.shot.source_prompt, "A cat sits on a wall.")

    def test_runtime_and_beats(self) -> None:
        self.assertEqual(self.shot.runtime, 4.0)
        self.assertEqual(len(self.shot.beats), 2)
        first = self.shot.beats[0]
        self.assertEqual((first.start, first.end, first.duration), (0.0, 2.0, 2.0))
        self.assertEqual(first.action, "Cat sits")
        self.assertEqual(first.camera, "Wide")
        self.assertEqual(first.light, "Day")
        self.assertEqual(self.shot.covered, 4.0)

    def test_variant_engine_aliases(self) -> None:
        self.assertEqual(self.shot.targets(), ["veo-sora", "veo", "sora"])
        self.assertEqual(self.shot.variant("Sora").body, "A cat sits on a wall.")
        self.assertEqual(self.shot.variant("veo").note, "prose")

    def test_tail_is_found_but_not_a_target(self) -> None:
        self.assertIsNotNone(self.shot.tail)
        self.assertNotIn("technical-tail", self.shot.targets())
        self.assertIn("technical-tail", self.shot.targets(include_tail=True))

    def test_negative_prompt_terms(self) -> None:
        self.assertEqual(render.negative_terms(self.shot), ["blurry", "extra legs"])

    def test_notes_and_variations(self) -> None:
        self.assertEqual(self.shot.notes[0].headline, "Stillness is the shot")
        self.assertEqual(self.shot.notes[0].body, "Do not let the cat move.")
        self.assertEqual(self.shot.variations[0].key, "night-version")
        self.assertEqual(self.shot.variations[0].body, "same beats, after dark.")


class ParseEdgeCaseTest(unittest.TestCase):
    def test_missing_title_raises(self) -> None:
        with self.assertRaises(parser.ShotParseError):
            parser.parse("no title here\n")

    def test_backwards_beat_raises(self) -> None:
        bad = MINIMAL.replace("| 2.0–4.0s |", "| 4.0–2.0s |")
        with self.assertRaises(parser.ShotParseError):
            parser.parse(bad)

    def test_timeless_beat_row_raises(self) -> None:
        bad = MINIMAL.replace("| 0.0–2.0s |", "| soon |")
        with self.assertRaises(parser.ShotParseError):
            parser.parse(bad)

    def test_hyphen_and_em_dash_ranges_parse(self) -> None:
        for dash in ("-", "—", "–"):
            shot = parser.parse(MINIMAL.replace("0.0–2.0s", f"0.0{dash}2.0s"))
            self.assertEqual(shot.beats[0].end, 2.0)

    def test_heading_inside_code_fence_is_not_a_section(self) -> None:
        spec = MINIMAL.replace(
            "A cat sits on a wall.", "A cat sits on a wall.\n## Not a heading"
        )
        shot = parser.parse(spec)
        self.assertIn("## Not a heading", shot.variant("veo").body)
        self.assertEqual(shot.targets(), ["veo-sora", "veo", "sora"])

    def test_sparse_spec_parses(self) -> None:
        shot = parser.parse("# Shot: Bare\n")
        self.assertEqual(shot.title, "Bare")
        self.assertEqual(shot.beats, [])
        self.assertEqual(shot.targets(), [])

    def test_unwrap_preserves_structured_lines(self) -> None:
        structured = "Subject: a cat\nCamera: slow push,\n  handheld\nStyle: photoreal"
        self.assertEqual(
            parser.unwrap(structured),
            "Subject: a cat\nCamera: slow push, handheld\nStyle: photoreal",
        )

    def test_unwrap_keeps_paragraph_breaks(self) -> None:
        self.assertEqual(parser.unwrap("one\ntwo\n\nthree\n"), "one two\n\nthree")


class BuildPromptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.shot = parser.parse(MINIMAL)

    def test_default_appends_tail_once(self) -> None:
        text = render.build_prompt(self.shot, "veo")
        self.assertEqual(text.count("Shot on 50mm, T2."), 1)
        self.assertTrue(text.startswith("A cat sits on a wall."))
        self.assertTrue(text.rstrip().endswith("Shot on 50mm, T2."))

    def test_no_tail(self) -> None:
        text = render.build_prompt(self.shot, "veo", tail=False)
        self.assertNotIn("50mm", text)

    def test_tail_target_does_not_duplicate_itself(self) -> None:
        text = render.build_prompt(self.shot, "technical-tail")
        self.assertEqual(text.count("Shot on 50mm, T2."), 1)

    def test_beats_and_variation_and_negative(self) -> None:
        text = render.build_prompt(
            self.shot,
            "veo",
            beats=True,
            variation="night-version",
            negative=True,
        )
        self.assertIn("Beat sheet:", text)
        self.assertIn("0–2s: Cat sits.", text)
        self.assertIn("Variation — Night version: same beats, after dark.", text)
        self.assertIn("Negative prompt: blurry, extra legs", text)
        # The tail stays last so format metadata cannot crowd the motion.
        self.assertLess(text.index("Beat sheet:"), text.index("Shot on 50mm"))

    def test_unknown_target_names_the_alternatives(self) -> None:
        with self.assertRaises(UnknownTarget) as caught:
            render.build_prompt(self.shot, "pika")
        self.assertIn("veo", str(caught.exception))
        self.assertNotIn("Traceback", str(caught.exception))

    def test_unknown_variation_raises(self) -> None:
        with self.assertRaises(UnknownTarget):
            render.build_prompt(self.shot, "veo", variation="daylight")

    def test_wrap(self) -> None:
        text = render.build_prompt(self.shot, "veo", wrap=20)
        self.assertTrue(all(len(line) <= 20 for line in text.splitlines()))


class RenderOutputTest(unittest.TestCase):
    def setUp(self) -> None:
        self.shot = parser.parse(MINIMAL)

    def test_beats_csv_round_trips(self) -> None:
        import csv

        rows = list(csv.DictReader(io.StringIO(render.beats_csv(self.shot))))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["action"], "Cat blinks")
        self.assertEqual(float(rows[1]["duration"]), 2.0)

    def test_json_is_serialisable_and_complete(self) -> None:
        import json

        data = json.loads(render.to_json(self.shot))
        self.assertEqual(data["key"], "test-shot")
        self.assertEqual(data["covered"], 4.0)
        self.assertEqual(data["beats"][0]["label"], "0–2s")
        self.assertTrue(data["variants"][-1]["is_tail"])

    def test_summary_mentions_runtime_and_targets(self) -> None:
        text = render.summary(self.shot)
        self.assertIn("4s across 2 beats", text)
        self.assertIn("veo", text)


class ValidateTest(unittest.TestCase):
    def test_clean_spec_has_no_issues(self) -> None:
        self.assertEqual(validate.check(parser.parse(MINIMAL)), [])

    def test_gap_between_beats_is_an_error(self) -> None:
        issues = validate.check(parser.parse(MINIMAL.replace("| 2.0–4.0s |", "| 2.5–4.0s |")))
        self.assertTrue(any("gap" in i.message for i in validate.errors(issues)))

    def test_overlap_is_an_error(self) -> None:
        issues = validate.check(parser.parse(MINIMAL.replace("| 2.0–4.0s |", "| 1.5–4.0s |")))
        self.assertTrue(any("overlap" in i.message for i in validate.errors(issues)))

    def test_runtime_mismatch_is_an_error(self) -> None:
        issues = validate.check(parser.parse(MINIMAL.replace("(4s)", "(8s)")))
        self.assertTrue(any("declares" in i.message for i in validate.errors(issues)))

    def test_late_start_is_an_error(self) -> None:
        issues = validate.check(parser.parse(MINIMAL.replace("| 0.0–2.0s |", "| 0.5–2.0s |")))
        self.assertTrue(any("not 0" in i.message for i in validate.errors(issues)))

    def test_duplicate_negative_term_warns_only(self) -> None:
        issues = validate.check(
            parser.parse(MINIMAL.replace("blurry, extra legs", "blurry, extra legs, Blurry"))
        )
        self.assertEqual(validate.errors(issues), [])
        self.assertTrue(any("repeats" in i.message for i in issues))

    def test_bare_spec_reports_missing_sections(self) -> None:
        issues = validate.check(parser.parse("# Shot: Bare\n"))
        messages = [i.message for i in validate.errors(issues)]
        self.assertIn("no beat breakdown", messages)
        self.assertIn("no prompt variants", messages)


class MonarchSpecTest(unittest.TestCase):
    """The shipped spec is the fixture we actually care about."""

    def setUp(self) -> None:
        self.shot = parser.parse_file(MONARCH)

    def test_parses_fully(self) -> None:
        self.assertEqual(self.shot.title, "Monarch Butterfly on Ferrari Hood")
        self.assertEqual(self.shot.runtime, 8.0)
        self.assertEqual(len(self.shot.beats), 6)
        self.assertEqual(self.shot.covered, 8.0)
        self.assertEqual(len(self.shot.notes), 5)
        self.assertEqual(len(self.shot.variations), 3)
        self.assertEqual(len(render.negative_terms(self.shot)), 21)

    def test_targets(self) -> None:
        self.assertEqual(
            self.shot.targets(), ["veo-sora", "veo", "sora", "runway-kling", "runway", "kling"]
        )

    def test_lightning_beat_is_the_short_one(self) -> None:
        lightning = next(b for b in self.shot.beats if "Lightning" in b.action)
        self.assertAlmostEqual(lightning.duration, 0.7)

    def test_airborne_third_of_runtime(self) -> None:
        """Direction note: the butterfly must be airborne for a third of the take."""
        touchdown = next(b for b in self.shot.beats if "Touchdown" in b.action)
        self.assertGreaterEqual(touchdown.start / self.shot.runtime, 1 / 3)

    def test_validates_clean(self) -> None:
        self.assertEqual(validate.check(self.shot), [])

    def test_prose_prompt_is_unwrapped_to_one_paragraph(self) -> None:
        text = render.build_prompt(self.shot, "veo", tail=False)
        self.assertEqual(len(text.splitlines()), 1)
        self.assertIn("igniting a hard specular streak across the hood.", text)

    def test_runway_prompt_keeps_its_field_shape(self) -> None:
        text = render.build_prompt(self.shot, "runway", tail=False)
        keys = [line.split(":")[0] for line in text.splitlines()]
        self.assertEqual(
            keys, ["Subject", "Camera", "Motion", "Lighting", "Style", "Camera motion"]
        )


class CliTest(unittest.TestCase):
    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = cli.main(list(argv))
        except SystemExit as exc:  # argparse and our own bail-outs
            code = exc.code if isinstance(exc.code, int) else 1
            if isinstance(exc.code, str):
                err.write(exc.code)
        return code, out.getvalue(), err.getvalue()

    def test_list(self) -> None:
        code, out, _ = self.run_cli("list", str(REPO / "shots"))
        self.assertEqual(code, 0)
        self.assertIn("monarch-butterfly-ferrari", out)
        self.assertIn("8s", out)

    def test_prompt_by_fuzzy_name(self) -> None:
        code, out, _ = self.run_cli("prompt", str(MONARCH), "-t", "veo")
        self.assertEqual(code, 0)
        self.assertIn("Monarch butterfly drifts into frame", out)
        self.assertIn("100mm macro", out)

    def test_prompt_defaults_to_first_target(self) -> None:
        code, out, _ = self.run_cli("prompt", str(MONARCH))
        self.assertEqual(code, 0)
        self.assertIn("Cinematic macro shot, 4K photorealistic", out)

    def test_unknown_target_exits_nonzero(self) -> None:
        code, _, err = self.run_cli("prompt", str(MONARCH), "-t", "pika")
        self.assertEqual(code, 1)
        self.assertIn("available", err)

    def test_unknown_spec_exits_nonzero(self) -> None:
        code, _, err = self.run_cli("show", "no-such-shot")
        self.assertEqual(code, 1)
        self.assertIn("no shot spec", err)

    def test_negative_list(self) -> None:
        code, out, _ = self.run_cli("negative", str(MONARCH), "-l")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[0], "cartoon")

    def test_beats_csv(self) -> None:
        code, out, _ = self.run_cli("beats", str(MONARCH), "-f", "csv")
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()), 7)

    def test_validate_directory(self) -> None:
        code, out, _ = self.run_cli("validate", str(REPO / "shots"))
        self.assertEqual(code, 0)
        self.assertIn("ok", out)

    def test_public_api_is_importable(self) -> None:
        for name in shotkit.__all__:
            self.assertTrue(hasattr(shotkit, name), name)


if __name__ == "__main__":
    unittest.main()
