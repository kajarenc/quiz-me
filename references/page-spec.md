# Page spec

`scripts/build_quiz.py` turns one JSON file into a self-contained HTML page: the brief on top, the quiz at the bottom, answers hidden until the user commits, self-marking, a live score, the gap map and an export block. The page makes no network calls; the spec is copied next to it as `<slug>.json` so the examiner can mark pasted results later.

```
python3 ${CLAUDE_SKILL_DIR}/scripts/build_quiz.py SPEC.json [--open] [--quiz-dir DIR] [--out PATH]
```

The page is written next to the spec as `<slug>.html`, with a normalised copy of the spec as `<slug>.json` beside it (`--quiz-dir` or `--out` change that). The skill writes specs into `~/.claude/quiz-me/quizzes/` unless a profile sets `quiz_dir:`. An existing page of the same slug is never overwritten: the new one gets a `-2`, `-3` suffix and the printed path is authoritative (`--force` overwrites instead). `--open` opens the default browser. Python 3.8+, no dependencies.

Browser state (answers, marks) is stored under the slug plus a fingerprint of the question set, so a rebuilt page with different questions starts clean. Spec text is HTML-escaped everywhere, including inside the embedded JSON; `scripts/test_build_quiz.py` covers this.

## Fields

| Field | Required | Meaning |
|---|---|---|
| `title` | yes | Page title, e.g. `Quiz: upload retries on feature/upload-retries` |
| `slug` | yes | Filename-safe id: `YYYY-MM-DD-<project>-<target words>` |
| `date`, `project`, `target` | no | Shown in the header and in the export block |
| `gate` | no | `perfect` makes the result say whether the merge rule is met; default `none` |
| `brief` | no | List of `{heading, body}`; body is tiny Markdown: paragraphs, `- ` bullets, `code`, **bold** |
| `questions` | yes | List of questions, fields below |
| `not_settled` | no | Ambiguities or under-documented spots the examiner could not settle from the material |
| `next_action` | no | The smallest next action that closes the widest gap |
| `note` | no | Footer line, normally the "understanding is not verification" sentence for a change |

Question fields:

| Field | Required | Meaning |
|---|---|---|
| `n` | no | Number; defaults to position |
| `type` | yes | `recall`, `predict` or `judgement` |
| `title` | yes | Three to six words |
| `question` | yes | One belief, under about 50 words |
| `probes` | no | What the question tests, so a wrong answer is legible |
| `answer` | yes | The real answer with the evidence that settles it, two to four sentences; tiny Markdown allowed |
| `citation` | yes | Where the user can open and verify: `path:line`, a heading, a plan step |
| `risk` | no | What a wrong belief puts at risk; shown in the gap map |
| `read` | no | What to read to close the gap; shown in the gap map |
| `hint` | no | One hint that narrows without answering |

## Example

```json
{
  "title": "Quiz: upload retries on feature/upload-retries",
  "slug": "2026-11-05-myrepo-diff-upload-retries",
  "date": "2026-11-05",
  "project": "myrepo",
  "target": "diff: feature/upload-retries against main",
  "gate": "perfect",
  "brief": [
    {"heading": "What changed", "body": "The shard uploader retries failed puts.\n\n- Three attempts, exponential backoff from one second.\n- The index is still written before the upload confirms."},
    {"heading": "Decisions made without an instruction", "body": "- The retry count and backoff were chosen by the agent.\n- Partial objects are not deleted after the last failure."}
  ],
  "questions": [
    {"type": "recall", "title": "Retry default",
     "question": "How many attempts does the uploader make, with what backoff, and what happens after the last failure?",
     "probes": "a default now in your code that nobody chose",
     "answer": "Three attempts with exponential backoff from one second; after the third failure the exception propagates and the partial object is left in place.",
     "citation": "src/storage/upload.py:142-160",
     "risk": "a bad shard produces a retry storm and a leftover partial object",
     "read": "src/storage/upload.py:130-165",
     "hint": "The loop bound is a module constant."},
    {"type": "predict", "title": "Half-written shard",
     "question": "The third attempt fails. What does the index contain afterwards, and which line decides it?",
     "answer": "The index already names the shard: it is written before the upload confirms, so readers fail on first read.",
     "citation": "src/storage/index.py:77",
     "risk": "every reader of this dataset fails on the missing shard",
     "read": "src/storage/index.py:70-90"}
  ],
  "not_settled": ["Whether the listing tool tolerates a missing shard (not documented)."],
  "next_action": "Move the index write after the upload confirms, then re-run the quiz.",
  "note": "Understanding is not verification: a perfect pass means you understand the change, not that it is correct."
}
```

## Results block

The page's "Copy results" button produces:

```
quiz-me results · 2026-11-05 · myrepo · diff: feature/upload-retries against main · 2026-11-05-myrepo-diff-upload-retries
Score: 1/2 (0 partial, 1 wrong, 0 skipped, 0 disputed, 0 open)
Q1 ✅ correct — Retry default — my answer: three tries, backoff doubling from 1s, then it raises
Q2 ❌ wrong — Half-written shard — my answer: the index is rolled back
(paste this into Claude Code as: /quiz-me results)
```

The examiner reads the matching `<slug>.json` for the key, re-checks disputed and partial answers against the source, and appends the log entry.
