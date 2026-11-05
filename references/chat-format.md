# Chat format

Used when the user passes `chat`, or a profile sets `format: chat`. The round, the marks and the close are written as plain Markdown in the conversation; the templates below sit in code fences only so they stay verbatim.

## A round

State the scope, then the questions: numbered, typed, titled, each with what it probes so that a wrong answer is legible rather than embarrassing. One belief per question, under about 50 words. Then stop and wait. The user answers all of them in one message, or one at a time with `one`.

```
Round 1 — <what this round covers>
Answer in your own words. "don't know" and "skip" are fine; "hint N" gets one hint.

Q1 [recall] <title>: <question> (probes: <the belief this tests>)
Q2 [predict] <title>: <a concrete input, edge case or failure; what does it do, and which line decides?> (probes: ...)
Q3 [judgement] <title>: <a tradeoff; which way did this go, why, and what does it cost?> (probes: ...)
Q4 ...
Q5 ...
```

The question text never contains the answer, the key, or a leading hint. `mc` allows multiple choice; without it, free text only.

## Marks

After the user answers, mark every answered question, including the correct ones, with the real answer and a citation they can open.

```
Q1 ✅ <one-line real answer> — path/file.py:42
Q2 🟡 <what was right>; missing: <the other half> — path/file.py:88-95
Q3 ❌ <the real answer and the evidence that settles it>. Risk if believed: <what breaks> — path/file.py:120
Q4 ⬜ skipped — <real answer> — docs/plan.md "Rollout"
```

Mark only the questions the user answered or explicitly skipped. Unanswered questions stay pending: list their numbers and wait. `hint N` gets one hint for that question and no marks. `stop` ends the round; pending questions appear in the close as not answered, with their answers.

A partial answer is its own verdict. A wrong answer gets the code or text that settles it and nothing more. A disputed answer means you re-read the source before replying. If the source is ambiguous, write "ambiguous in the code: <where>" and carry it to the close as a defect. Keep each mark under four lines.

Then either open the next round (same template, new scope, highest remaining blast radius first) or close.

## The close

```
Score: <correct>/<asked> (<partial> partial, <skipped> skipped or not answered) — <perfect pass | not a perfect pass>

Gap map (what you now know you did not know), by risk:
1. <wrong or missing belief> → puts <what> at risk → read <path:line | section>
2. ...

Could not be settled from the material (defects, under-documented spots): <list, or "none">

Smallest next action that closes the widest gap: <one concrete thing>

Did I miss anything you expected to be asked?
```

If a profile sets `gate: perfect`, say explicitly whether the gate is met. Add the "understanding is not verification" line when the target was a change. Offer `retest` for the gaps. Append the log entry if a log is configured.

## `brief` in chat

Before round 1, a compact explainer the user reads first: context, the intuition behind the change, what was done, the existing code paths it relies on, decisions made alone, assumptions nothing checked, what was and was not verified. Under 25 lines. Then quiz on the material, not on the brief. Suggest it yourself when a cold round comes back mostly "don't know".
