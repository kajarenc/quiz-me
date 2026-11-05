#!/usr/bin/env python3
"""Build a self-contained quiz-me HTML page from a spec JSON file.

usage: build_quiz.py SPEC.json [--out PATH] [--quiz-dir DIR] [--open]

The page makes no network calls and has no dependencies. The spec is copied
next to the page so the examiner can mark pasted results later. Python 3.8+.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import webbrowser
from pathlib import Path

INLINE_CODE = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
TYPES = ("recall", "predict", "judgement")
PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")
DEFAULT_DIR = Path.home() / ".claude" / "quiz-me" / "quizzes"


def inline(text) -> str:
    t = html.escape(str(text), quote=False)
    t = INLINE_CODE.sub(r"<code>\1</code>", t)
    t = BOLD.sub(r"<strong>\1</strong>", t)
    return t


def md(text) -> str:
    """Tiny Markdown: paragraphs, '- ' bullets, inline code and bold. Nothing else."""
    out, para, items = [], [], []

    def flush_para():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    def flush_items():
        if items:
            out.append("<ul>" + "".join("<li>" + inline(i) + "</li>" for i in items) + "</ul>")
            items.clear()

    for line in str(text).splitlines():
        s = line.strip()
        if not s:
            flush_para()
            flush_items()
            continue
        if s.startswith("- "):
            flush_para()
            items.append(s[2:])
            continue
        flush_items()
        para.append(s)
    flush_para()
    flush_items()
    return "\n".join(out)


def validate(spec: dict) -> dict:
    missing = [k for k in ("title", "slug", "questions") if k not in spec]
    if missing:
        sys.exit("spec is missing: " + ", ".join(missing))
    if not re.fullmatch(r"[A-Za-z0-9._-]+", str(spec["slug"])):
        sys.exit("slug must be filename-safe: letters, digits, dot, underscore, hyphen")
    if not spec["questions"]:
        sys.exit("spec has no questions")
    for i, q in enumerate(spec["questions"], 1):
        q.setdefault("n", i)
        for k in ("type", "title", "question", "answer", "citation"):
            if not q.get(k):
                sys.exit(f"question {q['n']} is missing '{k}'")
        if q["type"] not in TYPES:
            sys.exit(f"question {q['n']}: type must be one of {TYPES}")
    numbers = [str(q["n"]) for q in spec["questions"]]
    if len(set(numbers)) != len(numbers) or any(not n.strip() for n in numbers):
        sys.exit("question numbers must be unique and non-empty: " + ", ".join(numbers))
    for k, v in (("gate", "none"), ("date", ""), ("project", ""), ("target", ""), ("brief", []),
                 ("not_settled", []), ("next_action", ""), ("note", "")):
        spec.setdefault(k, v)
    return spec


def render_question(q: dict) -> str:
    n = html.escape(str(q["n"]))
    parts = [
        f'<article class="q" data-n="{n}" data-mark="">',
        f'<div class="qhead"><span class="num">Q{n}</span> <span class="type">{html.escape(q["type"])}</span> '
        f'<span class="title">{inline(q["title"])}</span></div>',
        f'<p class="text">{inline(q["question"])}</p>',
    ]
    if q.get("probes"):
        parts.append(f'<p class="probes">probes: {inline(q["probes"])}</p>')
    parts.append('<textarea rows="4" placeholder="Your answer, in your own words"></textarea>')
    actions = ['<button class="commit">Commit answer</button>',
               '<button class="dontknow secondary">Don\'t know</button>']
    if q.get("hint"):
        actions.append('<button class="hint secondary">Hint</button>')
    parts.append('<div class="actions">' + " ".join(actions) + "</div>")
    if q.get("hint"):
        parts.append(f'<p class="hinttext hidden">Hint: {inline(q["hint"])}</p>')
    parts.append('<div class="key hidden">')
    parts.append('<div class="answer"><div class="label">Answer</div>' + md(q["answer"]) + "</div>")
    parts.append(f'<p><span class="label">Where</span> <code>{html.escape(str(q["citation"]))}</code></p>')
    if q.get("risk"):
        parts.append(f'<p><span class="label">Risk if wrong</span> {inline(q["risk"])}</p>')
    if q.get("read"):
        parts.append(f'<p><span class="label">Read</span> <code>{html.escape(str(q["read"]))}</code></p>')
    parts.append('<div class="marks"><span class="label">Mark yourself</span> '
                 '<button data-mark="correct">Correct</button> <button data-mark="partial">Partial</button> '
                 '<button data-mark="wrong">Wrong</button> <button data-mark="dispute">Dispute the key</button></div>')
    parts.append("</div></article>")
    return "\n".join(parts)


def render_brief(brief: list) -> str:
    if not brief:
        return ""
    secs = "".join(f"<h3>{inline(s.get('heading', ''))}</h3>{md(s.get('body', ''))}" for s in brief)
    return ('<section id="brief"><div class="sechead"><h2>Brief</h2>'
            '<button id="brief-toggle" class="secondary">Hide</button></div>'
            f'<div id="brief-body">{secs}</div></section>')


CSS = """
:root{--bg:#ffffff;--fg:#1a1a1a;--muted:#6b6b6b;--line:#e4e4e4;--card:#f7f7f7;--accent:#2b6cb0;--ok:#2f855a;--part:#b7791f;--bad:#c53030;--skip:#718096;--code:#efefef}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#121212;--fg:#ececec;--muted:#a3a3a3;--line:#2e2e2e;--card:#1b1b1b;--accent:#63b3ed;--ok:#68d391;--part:#f6e05e;--bad:#fc8181;--skip:#a0aec0;--code:#242424}}
:root[data-theme="dark"]{--bg:#121212;--fg:#ececec;--muted:#a3a3a3;--line:#2e2e2e;--card:#1b1b1b;--accent:#63b3ed;--ok:#68d391;--part:#f6e05e;--bad:#fc8181;--skip:#a0aec0;--code:#242424}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
main{max-width:860px;margin:0 auto;padding:24px 16px 96px}
header{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;border-bottom:1px solid var(--line);padding-bottom:16px;margin-bottom:8px}
h1{font-size:1.5rem;margin:0 0 4px}
h2{font-size:1.2rem;margin:28px 0 12px}
h3{font-size:1rem;margin:18px 0 6px}
p{margin:8px 0}
ul{margin:6px 0;padding-left:22px}
.meta{color:var(--muted);margin:0;font-size:.95rem}
.scorebox{text-align:right;min-width:90px}
.scorebox .n{font-size:1.8rem;font-weight:700;line-height:1}
.scorebox .l{color:var(--muted);font-size:.8rem}
code{background:var(--code);padding:1px 5px;border-radius:4px;font-size:.92em}
.sechead{display:flex;align-items:center;justify-content:space-between}
article.q{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--line);border-radius:8px;padding:16px;margin:0 0 16px}
article.q[data-mark="correct"]{border-left-color:var(--ok)}
article.q[data-mark="partial"]{border-left-color:var(--part)}
article.q[data-mark="wrong"]{border-left-color:var(--bad)}
article.q[data-mark="skipped"]{border-left-color:var(--skip)}
article.q[data-mark="dispute"]{border-left-color:var(--accent)}
.qhead{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-bottom:6px}
.num{font-weight:700}
.type{font-size:.75rem;text-transform:uppercase;letter-spacing:.04em;padding:2px 7px;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
.title{font-weight:600}
.text{margin:6px 0}
.probes{color:var(--muted);font-size:.9rem;margin:0 0 10px}
textarea{width:100%;min-height:92px;padding:10px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);font:inherit;resize:vertical}
textarea:disabled{opacity:.85}
.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
button{font:inherit;font-size:.92rem;padding:7px 12px;border-radius:6px;border:1px solid var(--accent);background:var(--accent);color:#fff;cursor:pointer}
button.secondary,.marks button{background:transparent;color:var(--fg);border-color:var(--line)}
button.on{outline:2px solid var(--accent);outline-offset:1px}
.hinttext{color:var(--muted);font-size:.95rem;margin:8px 0 0}
.key{margin-top:12px;border-top:1px dashed var(--line);padding-top:12px}
.label{font-weight:600;color:var(--muted);font-size:.8rem;text-transform:uppercase;letter-spacing:.04em;margin-right:6px}
.answer .label{margin-bottom:2px}
.marks{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:10px}
.hidden{display:none}
.muted{color:var(--muted)}
#result{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px}
#gate{font-weight:600}
#export{width:100%;min-height:170px;margin-top:10px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.85rem}
.footnote{color:var(--muted);font-size:.9rem}
@media (max-width:480px){header{flex-direction:column}.scorebox{text-align:left}}
"""

JS = r"""
(function(){
  var Q = window.QUIZ, key = 'quizme:' + Q.slug + ':' + Q.fingerprint, state = {};
  try { state = JSON.parse(localStorage.getItem(key) || '{}'); } catch (e) { state = {}; }
  function save(){ try { localStorage.setItem(key, JSON.stringify(state)); } catch (e) {} }
  var cards = Array.prototype.slice.call(document.querySelectorAll('article.q'));
  function st(n){ return state[n] || (state[n] = {answer:'', status:'pending', mark:null, hint:false}); }
  function qOf(n){ for (var i=0;i<Q.questions.length;i++) if (String(Q.questions[i].n) === String(n)) return Q.questions[i]; return {}; }
  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function render(card){
    var n = card.dataset.n, s = st(n), ta = card.querySelector('textarea');
    var keyEl = card.querySelector('.key'), hintEl = card.querySelector('.hinttext'), actions = card.querySelector('.actions');
    if (ta.value !== s.answer) ta.value = s.answer;
    if (s.status !== 'pending') { ta.disabled = true; keyEl.classList.remove('hidden'); actions.classList.add('hidden'); }
    else { ta.disabled = false; keyEl.classList.add('hidden'); actions.classList.remove('hidden'); }
    if (hintEl) hintEl.classList.toggle('hidden', !s.hint);
    card.querySelectorAll('.marks button').forEach(function(b){
      b.classList.toggle('on', s.mark === b.dataset.mark);
      b.classList.toggle('hidden', s.status === 'skipped' && b.dataset.mark !== 'dispute'); });
    card.dataset.mark = s.mark || (s.status === 'skipped' ? 'skipped' : '');
  }
  function tally(){
    var t = {total: cards.length, correct:0, partial:0, wrong:0, skipped:0, dispute:0, pending:0};
    cards.forEach(function(c){ var s = st(c.dataset.n);
      if (s.mark === 'dispute') t.dispute++; else if (s.status === 'skipped') t.skipped++;
      else if (s.status === 'pending' || !s.mark) t.pending++; else t[s.mark]++; });
    return t;
  }
  function summary(){
    var t = tally(), done = t.pending === 0, perfect = done && t.correct === t.total, gate;
    document.getElementById('score').textContent = t.correct + '/' + t.total;
    if (!done) gate = t.pending + ' question' + (t.pending === 1 ? '' : 's') + ' still open.';
    else if (Q.gate === 'perfect') gate = perfect ? 'Gate met: perfect pass.' : 'Gate not met: your rule is a perfect pass before merging.';
    else gate = perfect ? 'Perfect pass.' : 'Not a perfect pass.';
    document.getElementById('gate').textContent = gate;
    document.getElementById('counts').textContent = t.partial + ' partial · ' + t.wrong + ' wrong · ' + t.skipped + ' skipped · ' + t.dispute + ' disputed';
    var gaps = [], disputes = [];
    cards.forEach(function(c){ var s = st(c.dataset.n), q = qOf(c.dataset.n);
      if (s.status === 'skipped' || s.mark === 'wrong' || s.mark === 'partial') gaps.push(q);
      if (s.mark === 'dispute') disputes.push(q); });
    var gl = document.getElementById('gaps'); gl.innerHTML = '';
    if (!gaps.length) gl.innerHTML = '<li class="muted">' + (done ? 'No gaps.' : 'Fills in as you mark.') + '</li>';
    gaps.forEach(function(q){ var li = document.createElement('li');
      li.innerHTML = '<strong>Q' + esc(q.n) + ' ' + esc(q.title) + '</strong>' + (q.risk ? ' → ' + esc(q.risk) : '') + (q.read ? ' → read <code>' + esc(q.read) + '</code>' : '');
      gl.appendChild(li); });
    var dw = document.getElementById('disputes-wrap'), dl = document.getElementById('disputes'); dl.innerHTML = '';
    dw.classList.toggle('hidden', !disputes.length);
    disputes.forEach(function(q){ var li = document.createElement('li'); li.textContent = 'Q' + q.n + ' ' + q.title; dl.appendChild(li); });
  }
  var ICON = {correct:'✅', partial:'🟡', wrong:'❌', dispute:'⚠️'};
  function exportText(){
    var t = tally();
    var lines = ['quiz-me results · ' + Q.date + ' · ' + Q.project + ' · ' + Q.target + ' · ' + Q.slug,
      'Score: ' + t.correct + '/' + t.total + ' (' + t.partial + ' partial, ' + t.wrong + ' wrong, ' + t.skipped + ' skipped, ' + t.dispute + ' disputed, ' + t.pending + ' open)'];
    cards.forEach(function(c){ var n = c.dataset.n, s = st(n), q = qOf(n);
      var tag = s.mark === 'dispute' ? '⚠️ dispute' : (s.status === 'skipped' ? '⬜ skipped' : (s.mark ? ICON[s.mark] + ' ' + s.mark : '… open'));
      lines.push('Q' + n + ' ' + tag + ' — ' + q.title + (s.answer.trim() ? ' — my answer: ' + s.answer.trim().replace(/\s+/g, ' ') : '')); });
    lines.push('(paste this into Claude Code as: /quiz-me results)');
    return lines.join('\n');
  }
  cards.forEach(function(card){
    var n = card.dataset.n, ta = card.querySelector('textarea');
    ta.addEventListener('input', function(){ st(n).answer = ta.value; save(); });
    card.querySelector('.commit').addEventListener('click', function(){
      if (!ta.value.trim()) { ta.focus(); return; }
      var s = st(n); s.answer = ta.value; s.status = 'committed'; save(); render(card); summary(); });
    card.querySelector('.dontknow').addEventListener('click', function(){
      var s = st(n); s.answer = ta.value; s.status = 'skipped'; s.mark = null; save(); render(card); summary(); });
    var hb = card.querySelector('.hint'); if (hb) hb.addEventListener('click', function(){ st(n).hint = true; save(); render(card); });
    card.querySelectorAll('.marks button').forEach(function(b){ b.addEventListener('click', function(){
      var s = st(n);
      if (s.status === 'skipped' && b.dataset.mark !== 'dispute') return;
      s.mark = (s.mark === b.dataset.mark) ? null : b.dataset.mark;   // click again to clear
      save(); render(card); summary(); }); });
    render(card);
  });
  document.getElementById('copy').addEventListener('click', function(){
    var text = exportText(), out = document.getElementById('export'), btn = document.getElementById('copy');
    out.value = text; out.classList.remove('hidden');
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function(){ btn.textContent = 'Copied'; setTimeout(function(){ btn.textContent = 'Copy results'; }, 1500); }, function(){ out.select(); });
    } else { out.select(); }
  });
  document.getElementById('reset').addEventListener('click', function(){
    if (!confirm('Clear your answers and marks for this quiz?')) return;
    state = {}; save(); cards.forEach(function(c){ c.querySelector('textarea').value = ''; render(c); });
    var ex = document.getElementById('export'); ex.value = ''; ex.classList.add('hidden'); summary();
  });
  var bt = document.getElementById('brief-toggle');
  if (bt) bt.addEventListener('click', function(){ var hidden = document.getElementById('brief-body').classList.toggle('hidden'); bt.textContent = hidden ? 'Show' : 'Hide'; });
  summary();
})();
"""

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}}</title>
<style>{{CSS}}</style>
</head>
<body>
<main>
<header>
  <div><h1>{{TITLE}}</h1><p class="meta">{{META}}</p></div>
  <div class="scorebox"><div class="n" id="score">0/0</div><div class="l">correct</div></div>
</header>
{{BRIEF}}
<section id="quiz">
<h2>Quiz</h2>
<p class="footnote">Answer in your own words, then commit. The answer and its citation appear only after you commit; mark yourself honestly. "Don't know" is an honest answer and becomes a gap.</p>
{{QUESTIONS}}
</section>
<section id="result">
<h2>Result</h2>
<p id="gate"></p>
<p id="counts" class="muted"></p>
<h3>Gap map (what you now know you did not know)</h3>
<ul id="gaps"></ul>
<div id="disputes-wrap" class="hidden"><h3>Disputed keys (paste results back so the examiner re-checks the source)</h3><ul id="disputes"></ul></div>
{{NOT_SETTLED}}
{{NEXT}}
{{NOTE}}
<div class="actions"><button id="copy">Copy results</button> <button id="reset" class="secondary">Reset</button></div>
<textarea id="export" class="hidden" readonly></textarea>
</section>
</main>
<script>window.QUIZ = {{SPEC}};</script>
<script>{{JS}}</script>
</body>
</html>
"""


def build(spec: dict) -> str:
    meta = " · ".join(x for x in (spec["date"], spec["project"], spec["target"]) if x)
    not_settled = ""
    if spec["not_settled"]:
        not_settled = "<h3>Could not be settled from the material</h3><ul>" + "".join(
            "<li>" + inline(x) + "</li>" for x in spec["not_settled"]) + "</ul>"
    nxt = f'<p><span class="label">Smallest next action</span> {inline(spec["next_action"])}</p>' if spec["next_action"] else ""
    note = f'<p class="footnote">{inline(spec["note"])}</p>' if spec["note"] else ""
    public = {k: spec[k] for k in ("slug", "date", "project", "target", "gate")}
    public["fingerprint"] = fingerprint(spec)
    public["questions"] = [{"n": q["n"], "title": q["title"], "risk": q.get("risk", ""), "read": q.get("read", "")}
                           for q in spec["questions"]]
    # Inside a <script> the JSON is a JS literal; escaping <, > and & keeps spec content from ending the script.
    embedded = (json.dumps(public, ensure_ascii=False)
                .replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e"))
    values = {
        "TITLE": html.escape(str(spec["title"])), "CSS": CSS, "META": html.escape(meta),
        "BRIEF": render_brief(spec["brief"]),
        "QUESTIONS": "\n".join(render_question(q) for q in spec["questions"]),
        "NOT_SETTLED": not_settled, "NEXT": nxt, "NOTE": note, "SPEC": embedded, "JS": JS,
    }
    # One pass over the template: inserted values are never rescanned, so spec text that
    # happens to contain a {{PLACEHOLDER}} stays escaped text.
    return PLACEHOLDER.sub(lambda m: values[m.group(1)], TEMPLATE)


def fingerprint(spec: dict) -> str:
    """Stable id of the question set; browser state is keyed by slug + fingerprint so a rebuilt
    slug with different questions never restores old answers or marks."""
    material = [[str(q["n"]), q["question"], q["answer"]] for q in spec["questions"]]
    return hashlib.sha256(json.dumps(material, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]


def unique_path(path: Path) -> Path:
    """Never overwrite an earlier quiz and its key: add -2, -3, ... to the stem."""
    if not path.exists():
        return path
    i = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{i}{path.suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path, help="spec JSON file (see references/page-spec.md)")
    ap.add_argument("--out", type=Path, help="HTML path to write (default: <slug>.html next to the spec)")
    ap.add_argument("--quiz-dir", type=Path, help=f"directory for the page instead of the spec's directory "
                                                  f"(the skill's default directory is {DEFAULT_DIR})")
    ap.add_argument("--open", action="store_true", help="open the page in the default browser")
    ap.add_argument("--force", action="store_true", help="overwrite an existing page of the same slug "
                                                         "instead of adding a -2, -3 suffix")
    args = ap.parse_args()
    try:
        spec = validate(json.loads(args.spec.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"cannot read spec: {e}")
    if args.out:
        out = args.out
    else:
        out_dir = Path(args.quiz_dir).expanduser() if args.quiz_dir else args.spec.resolve().parent
        out = out_dir / f"{spec['slug']}.html"
        if not args.force:
            out = unique_path(out)
            spec["slug"] = out.stem
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(spec), encoding="utf-8")
    # The key next to the page, under the slug that was actually used.
    out.with_suffix(".json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out)
    if args.open:
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
