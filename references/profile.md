# Profile format

Profiles tell the examiner what matters in your work, so the questions land where a real reviewer's would. Two optional files, both plain Markdown:

- Project: `.claude/quiz-me.md` in the repository root. Commit it to share with the team, or keep it untracked.
- User: `~/.claude/quiz-me/profile.md`. Applies to every project on the machine.

When both exist, project settings win over user settings, and the rule lists merge. Every section is optional. The examiner reads them in step 2 and uses them in step 3; a profile never changes the standing rules.

## Sections

```markdown
# quiz-me profile

## Who is answering
One or two lines: role, how much of the work in this repository is written by agents, what the user tends to skim.

## Reviewer to emulate
The kind of reviewer whose questions the quiz should anticipate: "a senior maintainer who asks about contracts, counts and what was left out".

## Emphasis
Bullets, most important first. Areas or properties that carry blast radius in this project: data contracts, schema rules, licences, cluster etiquette, cost, rollback, whatever a wrong belief would actually cost here.

## Rules the user must know cold
Bullets. Conventions and rules that are fair game in any quiz whose target touches them. Keep each one short enough to be a question.

## Defaults
round_size: 5          # questions per round (quick = 3)
gate: perfect          # perfect | none. "perfect" makes the close say whether the merge rule is met
log: ~/.claude/quiz-me/log.md   # append one entry per quiz; omit to disable logging
```

## Example (a data team)

```markdown
# quiz-me profile

## Who is answering
Data pipeline engineer. Most large diffs here are written by coding agents under my direction; quiz the decisions the agent made, not the typing.

## Reviewer to emulate
A demanding senior reviewer on the data team: asks about the output contract, what is skipped and why, counts and sizes, licences, overlap with evaluation data, and what was deliberately not done.

## Emphasis
- Output contract: one record per what, required fields, ordering, idempotence.
- Skips and drops: condition, rate, whether logged.
- Counts and sizes: records in and out, bytes, hours; where outputs land.
- Tests: what the golden test pins, what is only checked by eye in the previewer.
- Cluster etiquette: which queue, what runs on the login node, where scratch goes.

## Rules the user must know cold
- Every landing ships processor, tests, registry entry and decision record in one PR; utility scripts stay off main.
- A landing that supersedes an existing key marks the old key as superseded.
- Tests run through the project CLI, never bare pytest.

## Defaults
round_size: 5
gate: perfect
log: ~/.claude/quiz-me/log.md
```
