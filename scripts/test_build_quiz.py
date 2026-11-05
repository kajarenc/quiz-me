#!/usr/bin/env python3
"""Regression tests for build_quiz.py. Run: python3 scripts/test_build_quiz.py"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_quiz as bq  # noqa: E402


def spec(**over):
    base = {
        "title": "t", "slug": "2026-01-01-proj-target",
        "questions": [
            {"type": "recall", "title": "a", "question": "q1?", "answer": "a1", "citation": "f.py:1"},
            {"type": "predict", "title": "b", "question": "q2?", "answer": "a2", "citation": "f.py:2"},
        ],
    }
    base.update(over)
    return base


class BuildTests(unittest.TestCase):
    def test_placeholder_in_content_stays_text(self):
        s = spec()
        s["questions"][0]["question"] = "what does {{SPEC}} do?"
        s["questions"][1]["title"] = "<img src=x onerror='alert(1)'>"
        page = bq.build(bq.validate(s))
        self.assertIn("what does {{SPEC}} do?", page)
        self.assertNotIn("<img src=x", page)
        self.assertIn("&lt;img src=x", page)
        self.assertEqual(page.count("window.QUIZ ="), 1)

    def test_embedded_json_cannot_close_script(self):
        s = spec(target="</script><script>alert(1)</script>")
        page = bq.build(bq.validate(s))
        self.assertNotIn("</script><script>alert", page)
        self.assertIn("\\u003c/script\\u003e", page)

    def test_duplicate_numbers_rejected(self):
        s = spec()
        s["questions"][0]["n"] = 2
        with self.assertRaises(SystemExit):
            bq.validate(s)

    def test_fingerprint_changes_with_questions(self):
        a = bq.fingerprint(bq.validate(spec()))
        s = spec()
        s["questions"][0]["answer"] = "different"
        self.assertNotEqual(a, bq.fingerprint(bq.validate(s)))

    def test_cli_writes_next_to_spec_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp).resolve()  # the builder resolves the spec path; macOS temp dirs are symlinked
            p = d / "s.json"
            p.write_text(json.dumps(spec()))
            cmd = [sys.executable, str(HERE / "build_quiz.py"), str(p)]
            first = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
            second = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
            self.assertEqual(Path(first), d / "2026-01-01-proj-target.html")
            self.assertEqual(Path(second), d / "2026-01-01-proj-target-2.html")
            self.assertEqual(json.loads((d / "2026-01-01-proj-target-2.json").read_text())["slug"],
                             "2026-01-01-proj-target-2")
            forced = subprocess.run(cmd + ["--force"], capture_output=True, text=True, check=True).stdout.strip()
            self.assertEqual(Path(forced), Path(first))

    def test_md_is_minimal_and_escaped(self):
        out = bq.md("line one\n\n- `code` & **bold**\n- <b>x</b>")
        self.assertIn("<p>line one</p>", out)
        self.assertIn("<li><code>code</code> &amp; <strong>bold</strong></li>", out)
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", out)


if __name__ == "__main__":
    unittest.main()
