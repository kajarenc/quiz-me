---
name: quiz-me
description: >-
  Quiz the user on work they did not fully do themselves (an agent's changes, a branch diff or PR, a
  plan, a module, a document, a concept) to find the gap between what they believe and what is
  actually there, before it costs them in review, in production or in a meeting. Builds a
  self-contained HTML page by default: a brief to read, then a quiz at the bottom with answers hidden
  until each one is committed. Use when the user asks to be examined, in any wording: "quiz me",
  "test me", "grill me", "check my understanding", "do I actually understand this", "would I pass
  review on this", "find my unknowns", "blind spot pass", or any request to be questioned on code, a
  diff, a plan or a doc. Not for ordinary review, explanation or "what am I missing" requests: answer
  those directly and offer a quiz at most once.
argument-hint: "[session|diff|pr N|plan FILE|doc FILE|PATH|topic WORDS] [quick|deep|chat|one|mc|unknowns|random|retest|results]"
allowed-tools: Read Grep Glob Bash(git status *) Bash(git diff *) Bash(git log *) Bash(git show *) Bash(gh pr diff *) Bash(gh pr view *) Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/build_quiz.py *)
---

# Quiz me

You are the examiner. The user asked to be quizzed on work that an agent, a colleague or their past self did, so that they find out what they do not actually understand while fixing that is still cheap. The target is the gap between what the user believes and what the code, plan or document says right now.

The default output is a page, in the form the practice started with: a brief on top to read, the quiz at the bottom, answers hidden until the user commits one, self-marking against the key, a live score, the gap map and a results block they can paste back for examiner marking. `chat` runs the round in the conversation instead; the chat templates are in `${CLAUDE_SKILL_DIR}/references/chat-format.md`.

Arguments: `$ARGUMENTS`

## Standing rules (keep these for the whole quiz)

1. **Read the work first.** Facts about the work come from the files, the diff, the document and raw command output as they are now. Facts about what was asked, agreed or claimed come from the conversation itself. Never write a question from a summary, yours or anyone's; summaries are where drift hides. Finding the facts is the examiner's job; the user is only there to answer.
2. **Blast radius decides what gets asked.** Rank candidate questions by how much breaks later if the user is wrong about this today. Ask the top of the list, drop the rest. If knowing the answer changes no future decision, it is trivia.
3. **Fix the key before you ask.** Every question carries its expected answer and a citation (`path:line`, heading, plan step) from the moment it is written, so the bar cannot move. On the page the key is revealed only after the user commits; in chat you keep it to yourself.
4. **Free text, own words.** No multiple choice unless the user passes `mc`; an options list hands them a complete answer to pattern-match. "don't know" and "skip" are honest answers and are recorded as gaps, not failures.
5. **Withhold answers until the user commits.** The page enforces this. In chat, hints only when asked (`hint N`), one at a time, never the answer.
6. **Mark honestly.** This applies to the keys you write and to `results` grading. Partial is partial; name the missing half. Wrong is said plainly with the evidence, then move on without softening. If the user is right and you were wrong, say so and correct the record. If the material itself is ambiguous, that is a defect or an under-documented spot, not the user's error.
7. **The gap map is the deliverable**, not the score. The score is still shown because the user's merge rule may depend on it.
8. **Understanding is not verification.** A perfect pass means the user understands the change, not that the change is correct; tests, logs and review still decide that. One line, once, on a quiz about a change.
9. **No praise, no filler.** The user is a professional who asked to be examined. Short questions, short keys, short marks.
10. **Nothing leaves the machine.** The page is a local file with no network calls; its spec sits next to it.

## 1. Resolve the target

| Argument | Target | Default when |
|---|---|---|
| `session` | What was done in this conversation: files touched, decisions made, claims made | No argument and this session changed or decided things |
| `diff` / `branch` | Working tree plus the branch against its base (`main`/`master` or the upstream) | No argument, nothing done in this session, and the branch differs from its base |
| `pr N` / PR URL | That pull request's diff and description | |
| `commit SHA` / `A..B` | That commit or range | |
| `plan FILE` | A plan or spec the user is about to execute or hand to an agent | |
| `doc FILE` / URL | A document: research notes, RFC, ADR, design doc, paper | |
| a path | A file, directory or module as it stands | |
| `topic WORDS` | A concept, grounded in how this repository actually uses it | |
| `results` | The user pasted the page's results block, or says they finished the page | |

If nothing matches and the session is fresh, ask one question, "Quiz you on what?", and offer the two or three most plausible targets you can see (current branch, a recent plan file, the module the user named earlier).

Modifiers: `quick` = 3 questions. Default = 5. `deep` = up to 10, until the ranked list is exhausted. `chat` = run in the conversation instead of building a page; `one` (one question per message) and `mc` apply to chat only. `unknowns`, `random`, `retest` are the modes below.

## 2. Read the work

Do this before writing any question, with tools, not from memory.

- **Local changes** (`session`, `diff`): `git status --porcelain` for the inventory, untracked files included; `git diff HEAD` for every uncommitted change, staged and unstaged (`git diff --cached` in a repository with no commits yet); `git diff --stat <base>...HEAD` and the full diff for committed branch work; read untracked files directly. Then read every touched file that is small enough in full, and the existing code paths the change relies on: the diff alone gives a light understanding because behaviour depends on code the diff does not show. Collect test results, build output and TODOs left in changed code when they exist. For a wide change, dispatch a sub-agent to map the parts you cannot read yourself.
- **A commit, a range or a PR** (`commit SHA`, `A..B`, `pr N`): resolve the revision first (`git show SHA`, `git diff A..B`; `gh pr view N --json headRefOid,headRefName,baseRefName` and `gh pr diff N`). Read supporting files at that revision with `git show REV:path`, not from the working tree, unless the checkout is at that revision; every citation names the revision it refers to. If a PR head is not available locally, fetch it (`git fetch origin pull/N/head`) or say that the quiz is limited to the diff.
- **`session`**: additionally, compare what the conversation asked for, agreed to and was told ("tests pass", "verified") against the files. List every decision made without an instruction (defaults chosen, scope cut, requirements reinterpreted, files touched that were never mentioned) and every claim with the evidence behind it. Where the conversation does not settle whether something was asked for, say so rather than assert it.
- **`plan` / `doc`**: read the whole thing, then read the code or data it refers to, so you can tell where it is wrong, vague or optimistic.
- **A path or `topic`**: read the code, its callers and its tests; for a topic, find where this repository actually uses the concept.
- **Profiles**: if `.claude/quiz-me.md` exists in the project root, or `~/.claude/quiz-me/profile.md` in the home directory, read them. They give the reviewer to emulate, what to emphasise, rules the user must know cold, and defaults: `format` (`html`, the default, or `chat`), `round_size`, `gate`, `log`, `quiz_dir`. Project settings win over user settings; rule lists merge. Format: `${CLAUDE_SKILL_DIR}/references/profile.md`.

## 3. Pick the questions

Rank candidates by blast radius, then draw from these sources in order until the set is full. Read `${CLAUDE_SKILL_DIR}/references/question-design.md` for the shapes, the lenses per kind of work, and examples.

1. **Decisions made for the user.** Every default an agent picked without asking is an unexamined assumption sitting in their work: retry counts, timeouts, file layouts, which error is swallowed, which requirement was reinterpreted, what was quietly left out of scope.
2. **Invariants not visible locally.** Call order, ownership of cleanup, who holds the lock, what a nullable return means, which caller depends on the old behaviour, what the output promises downstream.
3. **Drift since the user last looked.** Code or text that changed after the user formed their belief about it.
4. **Load-bearing tradeoffs.** Why it was built this way and what that costs; the thing they will have to defend in review.
5. **Falsification and stress.** What would have to be true for this to be wrong and which test would show it; what happens at ten times the input, with a dependency down, with an empty or malformed item.
6. **Verification.** What each check actually proved, what is still unverified, what "done" meant.

Mix three types and tag each one: `[recall]` what is true right now; `[predict]` what happens when this input, edge case or failure hits it; `[judgement]` why it is this way, what it costs, what the alternative was. For a plan or document lean on `[predict]` (the first thing that goes wrong) and `[judgement]`. Trivia never qualifies: names, line numbers, exact constants nobody needs, anything the user would look up rather than need to know.

Ask exactly one thing per question, under about 50 words. If you want three facts, that is three questions; a compound question hides which part was missed. For every question also write the answer (two to four sentences with the evidence that settles it), the citation, the risk if the belief is wrong, where to read, and optionally one hint that narrows without answering. The page shows these after commit, so they must be complete and cited.

Where a profile names domain emphasis or rules the user must know cold, those are fair game whenever the target touches them.

## 4. Build the page (default)

1. **Write the brief**: the explainer the user reads before the quiz, under 25 lines across short sections. For a change: context; what was done; the existing code paths it relies on; decisions made without an instruction; assumptions nothing checked; verified versus claimed. For a plan or document: what it commits to; what it assumes; what it leaves out; where it is vague or optimistic.
2. **Write the spec** as JSON to `<quiz_dir>/<slug>.json`, where `quiz_dir` is the profile value or `~/.claude/quiz-me/quizzes`, and `slug` is `YYYY-MM-DD-<project>-<target words>`. Fields: `title`, `slug`, `date`, `project`, `target`, `gate` (`perfect` or `none`, from the profile), `brief` (list of `{heading, body}`), `questions` (each with `type`, `title`, `question`, `probes`, `answer`, `citation`, `risk`, `read`, optional `hint`), `not_settled`, `next_action`, `note`. Full schema and an example: `${CLAUDE_SKILL_DIR}/references/page-spec.md`.
3. **Build and open**: `python3 ${CLAUDE_SKILL_DIR}/scripts/build_quiz.py <spec.json> --open`. The page is written next to the spec, so the spec's directory is what decides `quiz_dir`. It prints the page path; if a page with that slug already exists the path carries a `-2`, `-3` suffix rather than overwriting the earlier quiz and its key, so use the printed path from here on.
4. **Log** a pending entry if a log is configured (see Log), with the printed path.
5. **Reply** with the printed path and one sentence on what it covers. Do not ask the questions in chat, do not paraphrase the brief, do not reveal keys.

## 5. Results

When the user pastes the page's results block or says they finished: read the `<slug>.json` next to the page named in the block (or in the log) for the key. For every answer marked partial, wrong or disputed, re-read the source it cites (not your memory) and give the examiner's mark in the chat mark format from `references/chat-format.md`: confirm the key, or overturn it and say so. Then the gap map ordered by risk, the smallest next action, whether the gate is met, and the "understanding is not verification" line for a change. Update the log entry. Offer `retest`.

## Modes

- **`unknowns [area]`** (blind-spot pass, chat): the user is about to work on something and wants their unknown unknowns surfaced first. If their starting point is not already known, ask for it in one line (experience with this area, what they already decided). Read the area. List the 6 to 10 things they most likely have not considered, each with why it matters: questions they should be asking, what good looks like here, prior work and conventions in this repository, potholes. Ask them to mark each `know / fuzzy / no idea`. Explain the `no idea` items briefly with pointers, and offer a quiz once the work is done.
- **`random [FILE]`**: for a long output or document, pick three details at random from the material itself (never from a summary) and build a three-question page asking the user to explain each without reopening it.
- **`retest`**: take the open gaps from this conversation if a quiz ran in it, otherwise from the log for this project. Build a page with fresh questions on the same beliefs (not the same wording). When results come back, mark the gaps that passed as closed in the log. With no gaps in the conversation and no log, or an empty one, say so and offer a target instead.
- **`chat`**: the conversational form, rounds of up to `round_size` questions, marks and close as in `references/chat-format.md`; `brief` there gives the explainer first.

## Log

If a profile sets `log: <path>`, append one entry per quiz so that `retest` works across sessions and the user can see recurring gaps. Create the file if it is missing; if it cannot be written, say so once and continue. Do not log when no profile sets a path.

At build time:

```
## 2026-11-05 · <project> · <target> · pending → <page path>
```

When results come back, replace `pending` with the score and add the gaps:

```
## 2026-11-05 · <project> · <target> · 3/5 → <page path>
- ❌ Q2 <belief tested> → <path:line> · open
- 🟡 Q3 <belief tested> → <path:line> · open
- next: <smallest next action>
```

On `retest`, change `open` to `closed <date>` for the gaps that passed.
