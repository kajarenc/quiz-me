# Question design

How to turn "read the work" into five questions worth the user's time. SKILL.md gives the order of sources (decisions made for the user, invisible invariants, drift, tradeoffs, falsification, verification). This file gives the shapes, the lenses per kind of work, what never qualifies, and marking examples. Examples are generic; replace the nouns with what is actually in the material.

Contents: 1. The three types · 2. Shapes that find drift · 3. Lenses by kind of work · 4. Trivia · 5. Marking examples

## 1. The three types

- `[recall]`: what is true of the work right now. Not "what is the function called" but "what does the function do when X, as of this diff". Good recall questions target a belief that may have drifted: a default, a limit, a contract, who owns what.
- `[predict]`: give a concrete input, edge case or failure and ask what happens and which line or step decides it. The user has to run the code in their head; this is where "I read the diff" and "I understand the change" separate.
- `[judgement]`: why it was built this way, what that costs, what the alternative was and why it lost. No single right answer; the mark is for knowing the tradeoff and which way this codebase went.

A default round of five is roughly two recall, two predict, one judgement. For a plan or a document, one recall, two predict, two judgement. For `quick`, one of each.

## 2. Shapes that find drift

Each shape is a template; fill it from the material, never from a summary.

- **The unexamined default.** "I added retries to the upload without asking. How many attempts, what backoff, and what happens after the last failure?" (probes: a default now in your code that nobody chose)
- **The silent exclusion.** "The request mentioned three inputs; the change handles two. Which one was left out, and was that a scope cut you agreed to?" (probes: intent debt)
- **The reinterpreted requirement.** "The spec said 'one record per item' and the existing schema stores lists. Which won, where, and what does the consumer see?" (probes: a conflict settled without you)
- **Ownership.** "After `materialize()` returns, who closes the client, and does that still hold on the exception path?" (probes: cleanup responsibility not visible in the diff)
- **The downstream contract.** "What does the reader of this output assume about ordering or uniqueness that the writer does not enforce?" (probes: an invariant that lives in two places)
- **Drift.** "You last read this module before the session. What changed in it since, and does your mental model of its entry point still hold?" (probes: a belief formed on an older version)
- **The pre-mortem** (plans). "When this plan runs, what is the first thing that goes wrong, and at which step?" (probes: whether the risk is in the plan or only in your head)
- **Falsification.** "What would have to be true for this migration to be wrong, and which test would show it?" (probes: whether 'it works' is a hypothesis or a conclusion)
- **Stress.** "Ten times the items, the dependency down for thirty minutes, an empty item: what happens, and where?" (probes: failure handling the tests do not cover)
- **Verification.** "The test that passed: what did it actually prove, and what remains unverified?" (probes: a green check proves one property)
- **Explain the line.** "Why is this line written this way?" for two or three load-bearing lines, chosen by you, not at random. (probes: whether the user can defend the code they did not type)
- **Random three** (`random` mode, long outputs). Three details chosen at random from the material; explain each without reopening it. (probes: whether the document was read or skimmed)
- **The reviewer's first question.** "What will the maintainer of this module ask first, and what is your answer?" (probes: readiness for review)
- **Numbers, only load-bearing ones.** Roughly how many, how big, how long: the counts and sizes a reviewer or an on-call engineer will ask about. Never exact constants nobody needs.

## 3. Lenses by kind of work

Use the lens that matches the target to decide what carries blast radius there.

### A code change
- Behaviour on the paths the diff does not show: callers, the error path, concurrency, startup and shutdown.
- Which existing behaviour changed as a side effect; who depended on the old one.
- What the tests pin and what they let through; what was only claimed.
- Rollback: can it be reverted cleanly, what state does it leave behind.

### A data pipeline change (ingestion, transformation, dataset builds)
- The contract of the output: schema, required fields, one record per what, ordering, idempotence.
- What is dropped, skipped or rewritten, under which condition, and how often; whether a drop is logged or silent.
- Provenance and licence of the source; dedupe and overlap with evaluation data; what "clean" means here.
- Counts and sizes that must be known roughly: records in, records out, bytes, time; where the outputs land and under which key.
- Resumability and partial failure: what happens when a shard, a download or an upload fails half way.
- What a preview would show that a unit test cannot; which samples were actually looked at.

### A model training or evaluation change
- What the metric measures and what it cannot see; how a wrong label or a leaked sample would move it.
- Which configuration values are load-bearing (batch, sequence length, sampling weights, seeds) and which are inherited defaults.
- Reproducibility: what is pinned, what is read from the environment, what differs between the local run and the cluster run.
- Cost: time and compute of the run, and what a mistake costs to rerun.

### Infrastructure and operations
- Where it runs, with which permissions, and what it does to shared resources (login nodes, shared filesystems, queues, budgets).
- Failure modes an operator meets at 3 a.m.: what the error looks like, where the logs are, how to stop it, how to resume.
- Blast radius of a wrong flag: the queue, the partition, the bucket, the account.
- What is irreversible (deletes, overwrites, published artifacts).

### A plan or design
- What the plan commits to versus what it assumes; which assumption, if false, invalidates the most steps.
- Order and dependencies: which step must finish before another can start; what can run in parallel.
- Scope: what is deliberately out, what is silently out.
- Definition of done and of verified: which artifact proves each step worked.
- The first thing that goes wrong, and the cheapest step to move earlier to find out.

### A document (research notes, RFC, ADR, paper)
- The claim the document rests on and the evidence given for it; what a sceptic would attack first.
- Which decision the document makes and which alternative it rejects, and why.
- Numbers and dates that drive a decision; whether they are measured, quoted or estimated.
- What the document is silent about that the reader will need.

## 4. Trivia: what never qualifies

- Names of variables, functions, files or branches, unless the name itself encodes a contract the user must honour.
- Line numbers, exact constants, string literals, version numbers nobody acts on.
- Anything whose answer the user would look up rather than need to know.
- Restatements of the summary the agent already gave; a question the user can answer by remembering the conversation instead of understanding the work.
- Yes/no questions with no "why" attached.
- Questions the examiner cannot answer confidently from the material. If you cannot cite it, do not ask it; note it as under-documented instead.

## 5. Marking examples

Good marks are short, cited, and say what the belief puts at risk.

```
Q1 ✅ Three attempts, exponential backoff from one second, then the exception propagates and the shard is left half-written — src/storage/upload.py:142-160
Q2 🟡 Right that the reader skips a missing shard; missing: it also drops the whole batch that contained it, so the count in the index no longer matches — src/reader.py:88-95
Q3 ❌ The schema conflict was settled in favour of the existing list shape; the spec's "one record per item" was not implemented. Risk if believed: downstream code written for single records receives lists — src/export.py:31, spec.md "Output"
Q4 ⬜ skipped — the plan's step 4 runs the backfill before the index rebuild, so a crash between them leaves readers on a stale index — PLAN.md "Rollout", steps 4-5
Q5 ✅ You were right and I was wrong: the lock is released by the context manager, not by the caller; corrected — src/cache.py:210
```

What not to write: "Great answer!", "Almost!", a paragraph of explanation after a correct answer, a mark without a citation, a cross without the evidence that settles it.
