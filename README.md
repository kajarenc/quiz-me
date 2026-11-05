# quiz-me

A [Claude Code](https://code.claude.com) skill that turns the assistant from author into examiner. After an agent has written a change, a plan or a document for you, `/quiz-me` reads the work as it actually stands, asks you a few questions with real blast radius, marks your answers against the source with citations, and ends with a map of what you now know you did not know.

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

Pick one of the two per machine; installing both gives two copies of the same skill. The folder is in the open [Agent Skills](https://agentskills.io) format (one `SKILL.md` plus references), so other tools that read that format can use it too: put the folder where that tool looks for skills.

## Use

```
/quiz-me                      # what was done in this session; else the branch diff
/quiz-me diff                 # working tree + branch against main
/quiz-me pr 123               # a pull request
/quiz-me plan MigrationPlan.md
/quiz-me doc docs/rfcs/retry-policy.md
/quiz-me src/storage/         # a module as it stands
/quiz-me topic "shard index"  # a concept, grounded in how this repo uses it

/quiz-me diff quick           # 3 questions, one round
/quiz-me diff deep            # keep going until the ranked list is exhausted
/quiz-me diff one             # one question per message
/quiz-me diff brief           # a short explainer first, then the quiz
/quiz-me unknowns src/auth/   # blind-spot pass before you start work in an area
/quiz-me random notes.md      # three random details from a long document
/quiz-me retest               # fresh questions on the gaps in your log
```

Saying "quiz me on this before I open the PR" works as well as the slash command.

### What a session looks like

```
Round 1 — the upload retry change on branch feature/upload-retries
Answer in your own words. "don't know" and "skip" are fine; "hint N" gets one hint.

Q1 [recall] Retry default: I added retries to the shard upload without asking. How many
   attempts, what backoff, and what happens after the last failure? (probes: a default
   now in your code that nobody chose)
Q2 [predict] Half-written shard: the third attempt fails. What does the index contain
   afterwards, and which line decides? (probes: cleanup on the failure path)
Q3 [judgement] Retry vs resume: the change retries instead of resuming a partial upload.
   What does that buy, what does it cost? (probes: the tradeoff you will defend in review)
```

You answer. The examiner marks:

```
Q1 🟡 Three attempts, right; missing: the exception propagates and the shard stays
   half-written — src/storage/upload.py:142-160
Q2 ❌ The index is updated before the upload completes, so it names a shard that does
   not exist. Risk if believed: readers fail on first read — src/storage/index.py:77
Q3 ✅ Simpler and idempotent per attempt; costs re-sending the whole shard — upload.py:130

Score: 1/3 (1 partial) — not a perfect pass

Gap map, by risk:
1. The index can point at a missing shard → every reader of this dataset → read index.py:70-90
2. Failure after the last retry leaves a partial object → storage cost and confusing listings → upload.py:155

Could not be settled from the material: whether the listing tool tolerates a missing shard (not documented)
Smallest next action: move the index write after the upload confirms, then re-run the quiz.
Did I miss anything you expected to be asked?
```

Understanding is not verification: a perfect pass means you understand the change, not that it is correct. Tests, logs and review still decide that.

## Make it fit your work

Two optional profile files tell the examiner what carries blast radius in your world: the reviewer to emulate, what to emphasise, rules you must know cold, and defaults (round size, whether the close reports a perfect-pass gate, a log path for `retest`).

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
- Mark every question with a citation, including the correct ones; partial is partial; the examiner can lose and says so; ambiguity in the material is a defect, not your error.
- Close with the gap map and the smallest next action, not the score.

## Sources

The practice is assembled from three sources. The examiner's procedure in `SKILL.md` adapts kanciak0's skill (MIT; its notice is kept in [LICENSE](LICENSE)); the rest is a synthesis.

- Thariq Shihipar, [A field guide to Claude Fable: Finding your unknowns](https://claude.com/resources/articles/a-field-guide-to-claude-fable-finding-your-unknowns) (Anthropic, 2026). The origin of the habit and its framing: the map versus the territory, the four kinds of unknowns, the post-session quiz you must pass before merging, the blind-spot pass before you start.
- Addy Osmani, [Critical thinking when agents do the work](https://x.com/addyosmani/article/2117512471930167377) (2026). The why: cognitive offloading sliding into deferral and surrender, comprehension debt, intent debt, and the discipline around a quiz (answer in your own words, define "verified" up front, ask what would have to be true for this to be wrong).
- kanciak0's [quiz-me skill](https://github.com/kanciak0/claude-skills) (listed on [mcpmarket](https://mcpmarket.com/tools/skills/quiz-me)). The operating procedure this skill adapts: read the work first, rank by blast radius, typed questions in small rounds, honest marks with citations, close with the gap rather than the score.

## License

MIT. See [LICENSE](LICENSE).
