# quiz-me

A [Claude Code](https://code.claude.com) skill that turns the assistant from author into examiner. After an agent has written a change, a plan or a document for you, `/quiz-me` reads the work as it actually stands and builds a self-contained HTML page: a brief to read on top, a few questions with real blast radius at the bottom, answers and citations hidden until you commit each one, a live score, and a map of what you now know you did not know. Paste the page's results block back and the examiner re-checks any answer you dispute against the source.

It exists because of a quiet failure mode of agentic work: the tests stay green while your understanding erodes. You merge code you could not explain, execute plans you skimmed, and sign off on documents from their table of contents. A quiz you have to pass is a cheap forcing function that keeps you accountable for work you did not type.

## Install

As a personal skill (recommended for daily use; `/quiz-me` in every project on the machine):

```bash
git clone https://github.com/kajarenc/quiz-me.git ~/.claude/skills/quiz-me
```

A running session picks it up without a restart if `~/.claude/skills` already existed; otherwise run `/reload-skills`. Update with `git -C ~/.claude/skills/quiz-me pull`.

As a plugin, from the repository's own marketplace (for a team, or a second machine):

```bash
claude plugin marketplace add kajarenc/quiz-me
claude plugin install quiz-me@kajarenc-quiz-me
```

Pick one of the two per machine; installing both gives two copies of the same skill. The folder is in the open [Agent Skills](https://agentskills.io) format (one `SKILL.md` plus references and a script), so other tools that read that format can use it too: put the folder where that tool looks for skills. The page builder needs only `python3` (3.8 or newer, no packages).

## Use

```
/quiz-me                      # what was done in this session; else the branch diff
/quiz-me diff                 # working tree + branch against main
/quiz-me pr 123               # a pull request
/quiz-me plan MigrationPlan.md
/quiz-me doc docs/rfcs/retry-policy.md
/quiz-me src/storage/         # a module as it stands
/quiz-me topic "shard index"  # a concept, grounded in how this repo uses it

/quiz-me diff quick           # 3 questions instead of 5
/quiz-me diff deep            # up to 10, until the ranked list is exhausted
/quiz-me diff chat            # run the round in the conversation instead of a page
/quiz-me unknowns src/auth/   # blind-spot pass before you start work in an area
/quiz-me random notes.md      # three random details from a long document
/quiz-me retest               # fresh questions on the open gaps in your log
/quiz-me results              # after pasting the page's results block
```

Saying "quiz me on this before I open the PR" works as well as the slash command.

### What a quiz looks like

The examiner reads the work (diff, touched files, the code paths they rely on, the conversation for what was asked and claimed), then writes a page to `~/.claude/quiz-me/quizzes/<date>-<project>-<target>.html` and opens it:

- **Brief** on top: context, what was done, the existing code paths it relies on, decisions made without an instruction, assumptions nothing checked, verified versus claimed. Collapsible, so you can take the quiz cold.
- **Quiz** at the bottom: five questions, each typed `recall`, `predict` or `judgement`, with what it probes. You type an answer in your own words and commit it; only then does the page show the answer, where to verify it, and what a wrong belief puts at risk. You mark yourself correct, partial or wrong, or dispute the key. "Don't know" is an honest answer and becomes a gap.
- **Result**: the score, whether your merge gate is met, the gap map (what to read to close each gap), what the examiner could not settle from the material, and the smallest next action.
- **Copy results** produces a short text block. Paste it into Claude Code as `/quiz-me results` and the examiner re-checks disputed and partial answers against the source and logs the outcome.

The page is a single local HTML file with no network calls. Your answers are kept in the browser's local storage so a reload does not lose them.

Understanding is not verification: a perfect pass means you understand the change, not that it is correct. Tests, logs and review still decide that.

## Make it fit your work

Two optional profile files tell the examiner what carries blast radius in your world: the reviewer to emulate, what to emphasise, rules you must know cold, and defaults (page or chat, question count, whether the result reports a perfect-pass gate, where pages go, a log path for `retest`).

- Project: `.claude/quiz-me.md` in the repository root.
- User: `~/.claude/quiz-me/profile.md`.

Format and an example in [`references/profile.md`](references/profile.md). Without profiles the skill still works; it reads the repository and uses general lenses (code change, data pipeline, training and evaluation, infrastructure, plan, document) from [`references/question-design.md`](references/question-design.md).

## The practice

The skill is the easy part; the habit is the point. The moments it pays off:

- **After a long agent session, before you merge.** `/quiz-me`. The agent may have done far more than you realised, and the diff alone gives a light understanding because behaviour depends on code paths the diff does not show.
- **Before you mark a pull request ready.** `/quiz-me diff` or `/quiz-me pr N`. The questions are the ones a demanding reviewer asks first.
- **Before a plan is executed**, by you or by an agent. `/quiz-me plan FILE`. Find the first thing that will go wrong while it is still a sentence in a file.
- **Before a design review or a meeting about a document.** `/quiz-me doc FILE`.
- **When you start in an area you do not know.** `/quiz-me unknowns PATH` surfaces the unknown unknowns first, so you prompt better.
- **Weekly.** `/quiz-me retest` on the gaps in your log; a gap that reappears is a gap worth a note in your own docs.

A rule several practitioners use: merge only after a perfect pass. Set `gate: perfect` in a profile and the close will say whether you met it. It is your rule to keep or relax; the skill only reports.

## Design notes

The examiner's contract, in one place:

- Read the work first, never from memory of the conversation or an earlier summary.
- Rank questions by blast radius; drop trivia.
- Fix the expected answer and its citation before asking, so the bar cannot move.
- Free-text answers in your own words; no multiple choice unless you ask for it.
- Withhold answers until you commit; "don't know" is an honest answer and becomes a gap.
- Nothing leaves the machine: the page is a local file with no network calls.
- Mark every question with a citation, including the correct ones; partial is partial; the examiner can lose and says so; ambiguity in the material is a defect, not your error.
- Close with the gap map and the smallest next action, not the score.

## Sources

The practice is assembled from three sources. The examiner's procedure in `SKILL.md` adapts kanciak0's skill (MIT; its notice is kept in [LICENSE](LICENSE)); the rest is a synthesis.

- Thariq Shihipar, [A field guide to Claude Fable: Finding your unknowns](https://claude.com/resources/articles/a-field-guide-to-claude-fable-finding-your-unknowns) (Anthropic, 2026). The origin of the habit and its framing: the map versus the territory, the four kinds of unknowns, the post-session quiz you must pass before merging, the blind-spot pass before you start.
- Addy Osmani, [Critical thinking when agents do the work](https://x.com/addyosmani/article/2117512471930167377) (2026). The why: cognitive offloading sliding into deferral and surrender, comprehension debt, intent debt, and the discipline around a quiz (answer in your own words, define "verified" up front, ask what would have to be true for this to be wrong).
- kanciak0's [quiz-me skill](https://github.com/kanciak0/claude-skills) (listed on [mcpmarket](https://mcpmarket.com/tools/skills/quiz-me)). The operating procedure this skill adapts: read the work first, rank by blast radius, typed questions in small rounds, honest marks with citations, close with the gap rather than the score.

## License

MIT. See [LICENSE](LICENSE).
