"""Build a single-column review copy (HTML -> DOCX and PDF via LibreOffice) from latex/main.tex.

The LaTeX source is the master. This script understands only the LaTeX subset used in main.tex.
Usage:  python3 build_review_copy.py
Output: review_copy/Manuscript_Review_Copy.{html,docx,pdf}
"""
import base64
import os
import re
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "latex", "main.tex")
BIB = os.path.join(HERE, "latex", "references.bib")
OUT = os.path.join(HERE, "review_copy")

# ---------------------------------------------------------------- bibliography
def parse_bib(path):
    s = open(path, encoding="utf-8").read()
    entries = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", s, re.S):
        typ, key, body = m.group(1).lower(), m.group(2).strip(), m.group(3)
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*\{(.*)\},?\s*$", body, re.M):
            fields[fm.group(1).lower()] = fm.group(2).strip()
        fields["_type"] = typ
        entries[key] = fields
    return entries


def bibtex_text(t):
    t = t.strip("{}")
    rep = {r"{\.I}": "İ", r"{\c{S}}": "Ş", r"{\c{s}}": "ş", r"{\'c}": "ć", r"\&": "&", "--": "–"}
    for a, b in rep.items():
        t = t.replace(a, b)
    return t.replace("{", "").replace("}", "")


def fmt_name(n):
    parts = n.split()
    if len(parts) == 1:
        return parts[0]
    particles = {"van", "de", "der", "von"}
    i = len(parts) - 1
    while i > 1 and parts[i - 1].lower() in particles:
        i -= 1
    first, last = parts[:i], parts[i:]
    initials = " ".join(p[0] + "." if not p.endswith(".") else p for p in first for p in p.split("-") if p)
    return f"{initials} {' '.join(last)}"


def fmt_ref(e):
    authors = [fmt_name(bibtex_text(a)) for a in e.get("author", "").split(" and ")]
    if len(authors) > 6:
        au = authors[0] + " et al."
    elif len(authors) > 2:
        au = ", ".join(authors[:-1]) + ", and " + authors[-1]
    else:
        au = " and ".join(authors)
    title = bibtex_text(e.get("title", ""))
    parts = [f'{au}, “{title},”']
    if e["_type"] == "article":
        parts.append(f"<i>{bibtex_text(e.get('journal', ''))}</i>,")
    elif e["_type"] == "inproceedings":
        parts.append(f"in <i>{bibtex_text(e.get('booktitle', ''))}</i>,")
    else:
        parts.append(bibtex_text(e.get("howpublished", "")) + ",")
    if e.get("volume"):
        parts.append(f"vol. {e['volume']},")
    if e.get("number"):
        parts.append(f"no. {e['number']},")
    if e.get("pages"):
        parts.append(f"pp. {bibtex_text(e['pages'])},")
    parts.append(e.get("year", "") + ("," if e.get("doi") or e.get("note") else "."))
    if e.get("note"):
        parts.append(bibtex_text(e["note"]) + ("," if e.get("doi") else "."))
    if e.get("doi"):
        parts.append(f"doi: {e['doi']}.")
    return " ".join(parts)

# ---------------------------------------------------------------- math
SYM = {
    r"\varepsilon": "ε", r"\epsilon": "ϵ", r"\sigma": "σ", r"\tau": "τ", r"\rho": "ρ", r"\phi": "φ",
    r"\psi": "ψ", r"\kappa": "κ", r"\lambda": "λ", r"\mu": "μ", r"\gamma": "γ", r"\beta": "β",
    r"\eta": "η", r"\pi": "π", r"\Phi": "Φ", r"\Delta": "Δ", r"\sqcup": "⊔", r"\subseteq": "⊆",
    r"\times": "×", r"\cup": "∪", r"\leftarrow": "←", r"\gets": "←", r"\to": "→", r"\infty": "∞",
    r"\le": "≤", r"\ge": "≥", r"\neq": "≠", r"\in": "∈", r"\sum": "Σ", r"\int": "∫", r"\log": "log",
    r"\max": "max", r"\min": "min", r"\arg": "arg", r"\bmod": " mod ", r"\dots": "…", r"\|": "‖",
    r"\ind": "<b>1</b>", r"\Rc": "R<sub>c</sub>", r"\rhomin": "ρ<sub>min</sub>", r"\quad": "  ", r"\qquad": "    ",
    r"\left": "", r"\right": "", r"\!": "", r"\,": " ", r"\;": " ", r"\cdot": "·", r"\mid": "|",
    r"\colon": ":", r"\sqrt": "√", r"\big": "", r"\bigl": "", r"\bigr": "", r"\Big": "",
    r"\pm": "±", r"\#": "#", r"\ell": "ℓ", r"\langle": "⟨", r"\rangle": "⟩", r"\Omega": "Ω",
}
CAL = {}
BB = {"R": "ℝ", "N": "ℕ"}


def group(s, i):
    """Return (content, end_index) for a {...} group starting at s[i]=='{', else single char."""
    if s[i] != "{":
        if s[i] == "\\":
            m = re.match(r"\\[A-Za-z]+", s[i:])
            return s[i:i + m.end()], i + m.end()
        return s[i], i + 1
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    return s[i + 1:], len(s)


def subsup(s):
    out, i = "", 0
    while i < len(s):
        c = s[i]
        if c in "_^" and i + 1 < len(s):
            g, j = group(s, i + 1)
            tag = "sub" if c == "_" else "sup"
            out += f"<{tag}>{subsup(g)}</{tag}>"
            i = j
        else:
            out += c
            i += 1
    return out


def math(s):
    s = s.replace("&", "").replace(r"\{", "\u27e8LB\u27e9").replace(r"\}", "\u27e8RB\u27e9")
    s = re.sub(r"\\label\{[^}]*\}", "", s)
    s = re.sub(r"\\nonumber", "", s)
    s = re.sub(r"\\mathcal\{(\w)\}", lambda m: "\u200b" + CAL.get(m.group(1), m.group(1)), s)
    s = re.sub(r"\\mathbb\{(\w)\}", lambda m: "\u200b" + BB.get(m.group(1), m.group(1)), s)
    s = re.sub(r"\\mathbf\{1\}", "<b>1</b>", s)
    s = re.sub(r"\\(?:mathrm|mathit|text|textsc|mathbf|operatorname)\{([^{}]*)\}", lambda m: "\u200b" + m.group(1), s)
    s = re.sub(r"\\hat\s*\{\\mathbf\{(\w)\}\}", lambda m: m.group(1) + "\u0302", s)
    s = re.sub(r"\\hat\s*\{?(\w)\}?", lambda m: m.group(1) + "\u0302", s)
    # fractions
    while r"\frac" in s:
        i = s.index(r"\frac")
        a, j = group(s, i + 5)
        b, k = group(s, j)
        s = s[:i] + f"({a})/({b})" + s[k:]
    for k in sorted(SYM, key=len, reverse=True):
        look = r"(?![A-Za-z])" if k[-1].isalpha() else ""
        s = re.sub(re.escape(k) + look, lambda m, v=SYM[k]: v, s)
    out = subsup(s)
    out = out.replace("{", "").replace("}", "").replace("\u200b", "")
    out = out.replace("\u27e8LB\u27e9", "&#123;").replace("\u27e8RB\u27e9", "&#125;")
    out = re.sub(r"\\([A-Za-z]+)", r"\1", out)
    return f"<i>{out}</i>" if out.strip() else out

# ---------------------------------------------------------------- text
class Ctx:
    def __init__(self, bib):
        self.bib, self.cite_order, self.labels = bib, [], {}

    def cite(self, keys):
        nums = []
        for k in [x.strip() for x in keys.split(",")]:
            if k not in self.cite_order:
                self.cite_order.append(k)
            nums.append(self.cite_order.index(k) + 1)
        return ", ".join(f"[{n}]" for n in nums)


def inline(t, ctx):
    t = re.sub(r"(?<!\\)%.*", "", t)
    t = t.replace("``", "“").replace("''", "”").replace("---", "—").replace("--", "–")
    t = re.sub(r"\\cite\{([^}]*)\}", lambda m: ctx.cite(m.group(1)), t)
    t = re.sub(r"\\eqref\{([^}]*)\}", lambda m: f"({ctx.labels.get(m.group(1), '?')})", t)
    t = re.sub(r"\\ref\{([^}]*)\}", lambda m: str(ctx.labels.get(m.group(1), "?")), t)
    t = re.sub(r"(?<!\\)\$(.+?)(?<!\\)\$", lambda m: math(m.group(1)), t, flags=re.S)
    for cmd, tag in (("textbf", "b"), ("emph", "i"), ("textit", "i")):
        t = re.sub(r"\\" + cmd + r"\{((?:[^{}]|\{[^{}]*\})*)\}", rf"<{tag}>\1</{tag}>", t)
    t = re.sub(r"\\textsc\{([^}]*)\}", lambda m: m.group(1).upper(), t)
    t = re.sub(r"\\Call\{([^}]*)\}\{([^}]*)\}", r"<span style='font-variant:small-caps'>\1</span>(\2)", t)
    t = t.replace(r"\,", "\u2009").replace(r"\#", "#")
    t = t.replace(r"\%", "%").replace(r"\&", "&").replace("~", " ").replace(r"\\", "<br/>")
    t = t.replace(r"\'c", "ć").replace(r"Matari\'c", "Matarić")
    t = re.sub(r"\\(?:centering|footnotesize|small|noindent|par|IEEEPARstart)\b", "", t)
    t = re.sub(r"\\setlength\{[^}]*\}\{[^}]*\}", "", t)
    t = re.sub(r"\\Rc\b", "R<sub>c</sub>", t)
    t = t.replace("{", "").replace("}", "")
    return t.strip()


def number_labels(body, ctx):
    eq = fig = tab = alg = sec = 0
    counters = {"assumption": 0, "proposition": 0, "lemma": 0, "definition": 0}
    for m in re.finditer(r"\\begin\{(equation|align|figure|table\*?|algorithm|assumption|proposition|lemma|definition)\}(.*?)\\end\{\1\}"
                         r"|\\section\{[^}]*\}\\label\{([^}]*)\}", body, re.S):
        if m.group(3):
            sec += 1
            ctx.labels[m.group(3)] = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"][sec - 1]
            continue
        env, content = m.group(1), m.group(2)
        if env == "equation":
            eq += 1
            for l in re.findall(r"\\label\{([^}]*)\}", content):
                ctx.labels[l] = eq
        elif env == "align":
            for line in content.split(r"\\"):
                eq += 1
                for l in re.findall(r"\\label\{([^}]*)\}", line):
                    ctx.labels[l] = eq
        elif env == "figure":
            fig += 1
            for l in re.findall(r"\\label\{([^}]*)\}", content):
                ctx.labels[l] = fig
        elif env.startswith("table"):
            tab += 1
            for l in re.findall(r"\\label\{([^}]*)\}", content):
                ctx.labels[l] = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"][tab - 1]
        elif env == "algorithm":
            alg += 1
            for l in re.findall(r"\\label\{([^}]*)\}", content):
                ctx.labels[l] = alg
        else:
            counters[env] += 1
            for l in re.findall(r"\\label\{([^}]*)\}", content):
                ctx.labels[l] = counters[env]
    # sections labelled on separate line
    secn = 0
    for m in re.finditer(r"\\section\{[^}]*\}(\\label\{([^}]*)\})?", body):
        secn += 1
        if m.group(2):
            ctx.labels[m.group(2)] = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"][secn - 1]
    secn = subn = 0
    for m in re.finditer(r"\\section\{[^}]*\}|\\subsection\{[^}]*\}(\\label\{([^}]*)\})?", body):
        if m.group(0).startswith("\\section"):
            secn += 1
            subn = 0
        else:
            subn += 1
            if m.group(2):
                ctx.labels[m.group(2)] = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"][secn - 1] + "-" + chr(64 + subn)


def table_html(content, ctx):
    cap = re.search(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}", content)
    lab = re.search(r"\\label\{([^}]*)\}", content)
    tab = re.search(r"\\begin\{tabular\}\{.*?\}\n(.*?)\\end\{tabular\}", content, re.S).group(1)
    rows = []
    for raw in tab.split(r"\\"):
        raw = re.sub(r"\\(toprule|midrule|bottomrule)", "", raw).strip()
        if not raw:
            continue
        rows.append([inline(c, ctx) for c in raw.split("&")])
    num = ctx.labels.get(lab.group(1), "") if lab else ""
    h = f"<p class='cap'>TABLE {num}<br/>{inline(cap.group(1), ctx).upper()}</p><table>"
    for i, r in enumerate(rows):
        tag = "th" if i == 0 else "td"
        h += "<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in r) + "</tr>"
    return h + "</table>"


def expand_alg(raw):
    """Replace \\If{..}, \\For{..}, \\Comment{..}, \\Call{..}{..} using balanced-brace parsing."""
    out, i = "", 0
    while i < len(raw):
        m = re.match(r"\\(If|For|Comment|Call|Else|EndIf|EndFor|State)", raw[i:])
        if not m:
            out += raw[i]
            i += 1
            continue
        cmd = m.group(1)
        j = i + m.end()
        if cmd in ("If", "For", "Comment"):
            g, j = group(raw, j)
            g = expand_alg(g)
            out += {"If": f"<b>if</b> {g} <b>then</b> ", "For": f"<b>for</b> {g} <b>do</b> ",
                    "Comment": f"  ▹ {g}"}[cmd]
        elif cmd == "Call":
            a, j = group(raw, j)
            b, j = group(raw, j)
            out += f"\\textsc{{{a}}}({b})"
        elif cmd == "Else":
            if raw[j:j + 2] == "{}":
                j += 2
            out += " <b>else</b> "
        else:
            out += {"EndIf": " <b>end if</b>", "EndFor": " <b>end for</b>", "State": ""}[cmd]
        i = j
    return out


def algorithm_html(content, ctx):
    cap = re.search(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}", content).group(1)
    lab = re.search(r"\\label\{([^}]*)\}", content).group(1)
    body = re.search(r"\\begin\{algorithmic\}\[1\](.*?)\\end\{algorithmic\}", content, re.S).group(1)
    lines, n = [], 0
    for raw in body.split("\n"):
        raw = raw.strip()
        if not raw:
            continue
        n += 1
        lines.append(f"<p class='algline'>{n}: {inline(expand_alg(raw), ctx)}</p>")
    return (f"<p class='alg'><b>Algorithm {ctx.labels[lab]}</b> {inline(cap, ctx)}</p>" + "".join(lines))


def convert(tex, ctx):
    body = tex[tex.index(r"\begin{document}") + 16:tex.index(r"\end{document}")]
    number_labels(body, ctx)
    title = re.search(r"\\title\{(.*?)\}\n", tex).group(1)
    html = [f"<h1>{title}</h1><p class='auth'>[Author Name], [Co-author Name], and [Supervisor Name]<br/>"
            "[Department], [University], [City, Country]</p>"
            "<p class='note'>Review copy generated from the IEEEtran LaTeX source (latex/main.tex). "
            "Layout is single-column; the LaTeX version is authoritative for formatting.</p>"]
    abs_ = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", body, re.S).group(1)
    html.append(f"<p class='abs'><b><i>Abstract</i>—</b>{inline(abs_, ctx)}</p>")
    kw = re.search(r"\\begin\{IEEEkeywords\}(.*?)\\end\{IEEEkeywords\}", body, re.S).group(1)
    html.append(f"<p class='abs'><b><i>Index Terms</i>—</b>{inline(kw, ctx)}</p>")
    body = body[body.index(r"\end{IEEEkeywords}") + 18:]
    body = re.sub(r"(?m)^\s*%.*$", "", body)
    body = body.replace(r"\IEEEPARstart{S}{warms}", "Swarms")

    pos, sec, sub = 0, 0, 0
    roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    pattern = re.compile(
        r"\\section\*?\{([^}]*)\}(?:\\label\{[^}]*\})?|\\subsection\{([^}]*)\}(?:\\label\{[^}]*\})?|\\paragraph\*\{([^}]*)\}"
        r"|\\begin\{(equation|align|figure|table\*?|algorithm|enumerate|itemize|assumption|proposition|lemma|definition|IEEEproof)\}(.*?)\\end\{\4\}"
        r"|\\pending\{((?:[^{}]|\{[^{}]*\})*)\}|\\bibliographystyle\{[^}]*\}|\\bibliography\{[^}]*\}", re.S)
    eqn = 0
    for m in pattern.finditer(body):
        text = body[pos:m.start()]
        for para in re.split(r"\n\s*\n", text):
            if para.strip():
                html.append(f"<p>{inline(para, ctx)}</p>")
        pos = m.end()
        if m.group(1) is not None:
            if m.group(0).startswith(r"\section*"):
                html.append(f"<h2>{m.group(1)}</h2>")
            else:
                sec += 1
                sub = 0
                html.append(f"<h2>{roman[sec - 1]}. {m.group(1).upper()}</h2>")
        elif m.group(2) is not None:
            sub += 1
            html.append(f"<h3>{chr(64 + sub)}. {inline(m.group(2), ctx)}</h3>")
        elif m.group(3) is not None:
            html.append(f"<p><i>{m.group(3)}:</i></p>")
        elif m.group(6) is not None:
            html.append(f"<table class='pending'><tr><td><b>[RESULTS PENDING]</b> {inline(m.group(6), ctx)}</td></tr></table>")
        elif m.group(4):
            env, c = m.group(4), m.group(5)
            if env == "equation":
                eqn += 1
                html.append(f"<p class='eq'>{math(c)}<span class='eqn'>({eqn})</span></p>")
            elif env == "align":
                for line in c.split(r"\\"):
                    if line.strip():
                        eqn += 1
                        html.append(f"<p class='eq'>{math(line)}<span class='eqn'>({eqn})</span></p>")
            elif env == "figure":
                img = re.search(r"\\includegraphics(?:\[.*?\])?\{([^}]*)\}", c).group(1)
                png = os.path.join(HERE, "latex", img.replace(".pdf", ".png"))
                with open(png, "rb") as fh:
                    data = base64.b64encode(fh.read()).decode()
                cap = re.search(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}", c).group(1)
                lab = re.search(r"\\label\{([^}]*)\}", c).group(1)
                html.append(f"<p class='fig'><img src='data:image/png;base64,{data}' width='600'/></p>"
                            f"<p class='cap'>Fig. {ctx.labels[lab]}. {inline(cap, ctx)}</p>")
            elif env.startswith("table"):
                html.append(table_html(c, ctx))
            elif env == "algorithm":
                html.append(algorithm_html(c, ctx))
            elif env in ("enumerate", "itemize"):
                tag = "ol" if env == "enumerate" else "ul"
                items = [x for x in re.split(r"\\item", c) if x.strip()]
                rendered = []
                for x in items:
                    parts = re.split(r"\\begin\{equation\}(.*?)\\end\{equation\}", x, flags=re.S)
                    h = ""
                    for pi, part in enumerate(parts):
                        if pi % 2:
                            eqn += 1
                            h += f"<br/>{math(part)}  ({eqn})<br/>"
                        else:
                            h += inline(part, ctx)
                    rendered.append(h)
                html.append(f"<{tag}>" + "".join(f"<li>{x}</li>" for x in rendered) + f"</{tag}>")
            elif env == "IEEEproof":
                html.append(f"<p><i>Proof:</i> {inline(c, ctx)} ∎</p>")
            else:
                lab = re.search(r"\\label\{([^}]*)\}", c)
                num = ctx.labels.get(lab.group(1), "") if lab else ""
                opt = re.match(r"\s*\[([^\]]*)\]", c)
                if opt:
                    c = c[opt.end():]
                head = f"{env.capitalize()} {num}" + (f" ({opt.group(1)})" if opt else "")
                c = re.sub(r"\\label\{[^}]*\}", "", c)
                if r"\begin{enumerate}" in c:
                    pre, rest = c.split(r"\begin{enumerate}")
                    items = [x for x in re.split(r"\\item", rest.split(r"\end{enumerate}")[0]) if x.strip()]
                    html.append(f"<p><b>{head}:</b> <i>{inline(pre, ctx)}</i></p><ol>" +
                                "".join(f"<li><i>{inline(x, ctx)}</i></li>" for x in items) + "</ol>")
                else:
                    html.append(f"<p><b>{head}:</b> <i>{inline(c, ctx)}</i></p>")
    tail = body[pos:]
    for para in re.split(r"\n\s*\n", tail):
        if para.strip() and "bibliography" not in para:
            html.append(f"<p>{inline(para, ctx)}</p>")
    html.append("<h2>REFERENCES</h2>")
    for i, k in enumerate(ctx.cite_order, 1):
        html.append(f"<p class='ref'>[{i}] {fmt_ref(ctx.bib[k])}</p>")
    return "\n".join(html)


CSS = """<style>
body{font-family:'Liberation Serif','Times New Roman',serif;font-size:11pt;line-height:1.35;max-width:760px;margin:auto}
h1{font-size:20pt;text-align:center;font-weight:normal}
h2{font-size:11pt;text-align:center;font-variant:small-caps;margin-top:18pt}
h3{font-size:11pt;font-style:italic;font-weight:normal}
p{text-align:justify}
.auth{text-align:center}.note{font-size:9pt;color:#555;text-align:center}
.abs{font-size:10pt}
.eq{text-align:center}.eqn{float:right}
.cap{font-size:9pt;text-align:center}
.fig{text-align:center}
table{border-collapse:collapse;margin:auto;font-size:9pt}
th,td{border-top:1px solid #000;border-bottom:1px solid #000;padding:2px 5px;text-align:left}
table.pending{width:100%;border:1.5px solid #8b0000;background:#fdeeee;font-size:10pt}
table.pending td{border:1.5px solid #8b0000;padding:6px}
td p,th p{margin:0}
.algline{text-align:left;margin:0;font-size:9.5pt}
.ref{text-align:left;font-size:9pt;margin:2pt 0;padding-left:2em;text-indent:-2em}
.alg{font-size:10pt;border-top:1.5px solid #000;border-bottom:1px solid #000}
.algbody{font-size:9.5pt;font-family:'Liberation Serif',serif;border-bottom:1.5px solid #000;padding-bottom:4px}
.refs{font-size:9pt;list-style:none;padding-left:0}
</style>"""


def main():
    os.makedirs(OUT, exist_ok=True)
    ctx = Ctx(parse_bib(BIB))
    body = convert(open(TEX, encoding="utf-8").read(), ctx)
    html_path = os.path.join(OUT, "Manuscript_Review_Copy.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Manuscript review copy</title>{CSS}</head><body>{body}</body></html>")
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        subprocess.run([soffice, "--headless", "--convert-to", "docx:MS Word 2007 XML", "--outdir", OUT, html_path],
                       check=False, capture_output=True, timeout=300)
        docx = os.path.join(OUT, "Manuscript_Review_Copy.docx")
        if os.path.exists(docx):
            subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", OUT, docx],
                           check=False, capture_output=True, timeout=300)
    print("cited references:", len(ctx.cite_order))
    for f in sorted(os.listdir(OUT)):
        print(os.path.join(OUT, f))


if __name__ == "__main__":
    main()
