"""Build an IEEE-format Word manuscript (two-column, Times 10 pt) from latex/main.tex.

The LaTeX source remains the master; this script reuses the parser in build_review_copy.py.
Writes raw Office Open XML (no third-party packages). LibreOffice is used only to render
high-resolution figure PNGs and an optional PDF preview.

Usage:  python3 build_ieee_docx.py
Output: ieee_word/Manuscript_IEEE.docx  (+ Manuscript_IEEE_preview.pdf if LibreOffice is present)
"""
import html
import os
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile
from html.parser import HTMLParser
from xml.sax.saxutils import escape

import build_review_copy as brc

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "latex", "main.tex")
FIGDIR = os.path.join(HERE, "latex", "figures")
OUT = os.path.join(HERE, "ieee_word")
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

# ---- page geometry (US Letter, IEEE two-column) in twips (1 in = 1440) ----
PAGE_W, PAGE_H = 12240, 15840
MAR_T, MAR_B, MAR_L, MAR_R = 1080, 1440, 900, 900          # 0.75", 1", 0.625", 0.625"
COL_GAP = 360                                               # 0.25"
COL_W = (PAGE_W - MAR_L - MAR_R - COL_GAP) // 2            # 3.5"
TEXT_W = PAGE_W - MAR_L - MAR_R
EMU_PER_TWIP = 635


# =============================================================== inline HTML -> runs
class RunBuilder(HTMLParser):
    """Turn the HTML fragments produced by build_review_copy.inline()/math() into w:r elements."""

    def __init__(self, base=None):
        super().__init__(convert_charrefs=True)
        self.stack = [dict(base or {})]
        self.runs = []

    def handle_starttag(self, tag, attrs):
        cur = dict(self.stack[-1])
        if tag in ("i", "em"):
            cur["i"] = True
        elif tag in ("b", "strong"):
            cur["b"] = True
        elif tag == "sub":
            cur["va"] = "subscript"
        elif tag == "sup":
            cur["va"] = "superscript"
        elif tag == "span" and "small-caps" in (dict(attrs).get("style") or ""):
            cur["sc"] = True
        elif tag == "br":
            self.runs.append("<w:r><w:br/></w:r>")
            return
        self.stack.append(cur)

    def handle_startendtag(self, tag, attrs):
        if tag == "br":
            self.runs.append("<w:r><w:br/></w:r>")

    def handle_endtag(self, tag):
        if tag != "br" and len(self.stack) > 1:
            self.stack.pop()

    def handle_data(self, data):
        if data:
            self.runs.append(run(data, **self.stack[-1]))


def run(text, b=False, i=False, sc=False, va=None, sz=None, caps=False, color=None, tab=False):
    rpr = ""
    if b:
        rpr += "<w:b/><w:bCs/>"
    if i:
        rpr += "<w:i/><w:iCs/>"
    if caps:
        rpr += "<w:caps/>"
    if sc:
        rpr += "<w:smallCaps/>"
    if color:
        rpr += f'<w:color w:val="{color}"/>'
    if sz:
        rpr += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    if va:
        rpr += f'<w:vertAlign w:val="{va}"/>'
    rpr = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
    if tab:
        return f"<w:r>{rpr}<w:tab/></w:r>"
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def runs_from_html(fragment, **base):
    fragment = fragment.replace("\u200b", "")
    rb = RunBuilder(base)
    rb.feed(fragment)
    rb.close()
    return "".join(rb.runs)


def para(runs_xml, style=None, jc=None, ind=None, spacing=None, keep_next=False, tabs=None,
         border=None, shade=None, sect=None):
    ppr = ""
    if style:
        ppr += f'<w:pStyle w:val="{style}"/>'
    if keep_next:
        ppr += "<w:keepNext/>"
    if border:
        ppr += border
    if shade:
        ppr += f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>'
    if tabs:
        ppr += "<w:tabs>" + "".join(f'<w:tab w:val="{v}" w:pos="{p}"/>' for v, p in tabs) + "</w:tabs>"
    if spacing:
        ppr += spacing
    if ind:
        ppr += ind
    if jc:
        ppr += f'<w:jc w:val="{jc}"/>'
    if sect:
        ppr += sect
    return f"<w:p><w:pPr>{ppr}</w:pPr>{runs_xml}</w:p>"


def sect_pr(cols, continuous=True, header=False):
    hdr = '<w:headerReference w:type="default" r:id="rIdHeader1"/>' if header else ""
    typ = '<w:type w:val="continuous"/>' if continuous else ""
    colxml = (f'<w:cols w:num="2" w:space="{COL_GAP}" w:equalWidth="1"/>' if cols == 2
              else '<w:cols w:space="720"/>')
    return (f"<w:sectPr>{hdr}{typ}<w:pgSz w:w=\"{PAGE_W}\" w:h=\"{PAGE_H}\"/>"
            f'<w:pgMar w:top="{MAR_T}" w:right="{MAR_R}" w:bottom="{MAR_B}" w:left="{MAR_L}" '
            f'w:header="540" w:footer="540" w:gutter="0"/>{colxml}</w:sectPr>')


# =============================================================== figures
def hires_pngs():
    """Render each SVG at 3x size to PNG (sharper in print). Returns {name: path}."""
    tmp = tempfile.mkdtemp(prefix="ieeefig_")
    out = {}
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    for f in sorted(os.listdir(FIGDIR)):
        if not f.endswith(".svg"):
            continue
        s = open(os.path.join(FIGDIR, f), encoding="utf-8").read()
        m = re.search(r'width="(\d+)" height="(\d+)"', s)
        w, h = int(m.group(1)), int(m.group(2))
        s = s.replace(m.group(0), f'width="{w * 3}" height="{h * 3}"', 1)
        p = os.path.join(tmp, f)
        open(p, "w", encoding="utf-8").write(s)
        if soffice:
            subprocess.run([soffice, "--headless", "--convert-to", "png", "--outdir", tmp, p],
                           capture_output=True, timeout=300)
        png = p.replace(".svg", ".png")
        out[f.replace(".svg", "")] = png if os.path.exists(png) else os.path.join(FIGDIR, f.replace(".svg", ".png"))
    return out


def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    return struct.unpack(">II", head[16:24])


def drawing(rid, idx, path, width_twips):
    pw, ph = png_size(path)
    cx = width_twips * EMU_PER_TWIP
    cy = int(cx * ph / pw)
    return (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{idx}" name="Figure {idx}"/>'
            f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            f'<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:nvPicPr><pic:cNvPr id="{idx}" name="fig{idx}.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
            f'</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')


# =============================================================== tables
def plain(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).replace("\u200b", "")


def col_widths(rows, width, font_sz, force=False):
    """Give every column room for its longest word, then share the rest by average text length.
    If even the longest words do not fit, return None (or, with force=True, scale them to fit)."""
    ncol = max(len(r) for r in rows)
    char_tw = font_sz * 10 * 0.5            # approx. Times character width in twips (sz is half-points)
    pad = 125                               # left + right cell margins (57 twips each) + slack
    longest = [0] * ncol
    avg = [0.0] * ncol
    for r in rows:
        for ci in range(ncol):
            t = plain(r[ci]) if ci < len(r) else ""
            words = t.split() or [""]
            longest[ci] = max(longest[ci], max(len(w) for w in words))
            avg[ci] += len(t) / len(rows)
    need = [int(l * char_tw * 1.08) + pad for l in longest]
    if sum(need) > width:
        if not force:
            return None
        return [int(n * width / sum(need)) for n in need]
    spare = width - sum(need)
    tot = sum(avg) or 1
    return [n + int(spare * a / tot) for n, a in zip(need, avg)]


def table_xml(rows, width, font_sz=16):
    ncol = max(len(r) for r in rows)
    widths = col_widths(rows, width, font_sz)
    if widths is None:                       # too tight: drop to 7 pt
        font_sz = 14
        widths = col_widths(rows, width, font_sz, force=True)
    cw = widths
    rule = '<w:{side} w:val="single" w:sz="{sz}" w:space="0" w:color="000000"/>'
    out = [f'<w:tbl><w:tblPr><w:tblW w:w="{width}" w:type="dxa"/><w:jc w:val="center"/>'
           '<w:tblLayout w:type="fixed"/>'
           '<w:tblCellMar><w:left w:w="57" w:type="dxa"/><w:right w:w="57" w:type="dxa"/></w:tblCellMar>'
           '</w:tblPr><w:tblGrid>' + "".join(f'<w:gridCol w:w="{w}"/>' for w in cw) + "</w:tblGrid>"]
    for ri, r in enumerate(rows):
        out.append("<w:tr>" + ("<w:trPr><w:tblHeader/></w:trPr>" if ri == 0 else ""))
        for ci in range(ncol):
            cell = r[ci] if ci < len(r) else ""
            borders = ""
            if ri == 0:
                borders += rule.format(side="top", sz=8) + rule.format(side="bottom", sz=4)
            if ri == len(rows) - 1:
                borders += rule.format(side="bottom", sz=8)
            tcpr = f'<w:tcPr><w:tcW w:w="{cw[ci]}" w:type="dxa"/>' + (f"<w:tcBorders>{borders}</w:tcBorders>" if borders else "") + "</w:tcPr>"
            rr = runs_from_html(cell, b=(ri == 0), sz=font_sz)
            out.append(f"<w:tc>{tcpr}" + para(rr, style="TableText", keep_next=ri < len(rows) - 1) + "</w:tc>")
        out.append("</w:tr>")
    out.append("</w:tbl>")
    return "".join(out)


# =============================================================== LaTeX walk
def walk(tex, ctx):
    """Yield blocks (type, ...) in document order."""
    body = tex[tex.index(r"\begin{document}") + 16:tex.index(r"\end{document}")]
    brc.number_labels(body, ctx)
    blocks = []
    title = re.search(r"\\title\{(.*?)\}\n", tex).group(1)
    authors = re.search(r"\\author\{(.*?)%", tex, re.S).group(1).strip()
    thanks = [brc.inline(t, ctx) for t in re.findall(r"\\thanks\{((?:[^{}]|\{[^{}]*\})*)\}", tex)]
    mark = re.search(r"\\markboth\{([^}]*)\}", tex).group(1)
    blocks.append(("title", title, authors, thanks, brc.inline(mark, ctx)))
    abs_ = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", body, re.S).group(1)
    kw = re.search(r"\\begin\{IEEEkeywords\}(.*?)\\end\{IEEEkeywords\}", body, re.S).group(1)
    blocks.append(("abstract", brc.inline(abs_, ctx), brc.inline(kw, ctx)))
    body = body[body.index(r"\end{IEEEkeywords}") + 18:]
    body = re.sub(r"(?m)^\s*%.*$", "", body)
    first_par = [True]
    body = body.replace(r"\IEEEPARstart{S}{warms}", "\u2063DROPCAP\u2063warms")

    pattern = re.compile(
        r"\\section\*?\{([^}]*)\}(?:\\label\{[^}]*\})?|\\subsection\{([^}]*)\}(?:\\label\{[^}]*\})?|\\paragraph\*\{([^}]*)\}"
        r"|\\begin\{(equation|align|figure|table\*?|algorithm|enumerate|itemize|assumption|proposition|lemma|definition|IEEEproof)\}(.*?)\\end\{\4\}"
        r"|\\pending\{((?:[^{}]|\{[^{}]*\})*)\}|\\bibliographystyle\{[^}]*\}|\\bibliography\{[^}]*\}", re.S)
    pos, sec, sub, eqn = 0, 0, 0, 0

    def paras(text):
        for p in re.split(r"\n\s*\n", text):
            if p.strip():
                blocks.append(("para", brc.inline(p, ctx)))

    def eq_block(src):
        nonlocal eqn
        eqn += 1
        blocks.append(("eq", brc.math(src), eqn))

    for m in pattern.finditer(body):
        paras(body[pos:m.start()])
        pos = m.end()
        if m.group(1) is not None:
            if m.group(0).startswith(r"\section*"):
                blocks.append(("h1", None, m.group(1)))
            else:
                sec += 1
                sub = 0
                blocks.append(("h1", ROMAN[sec - 1], m.group(1)))
        elif m.group(2) is not None:
            sub += 1
            blocks.append(("h2", chr(64 + sub), brc.inline(m.group(2), ctx)))
        elif m.group(3) is not None:
            blocks.append(("runin", m.group(3)))
        elif m.group(6) is not None:
            blocks.append(("pending", brc.inline(m.group(6), ctx)))
        elif m.group(4):
            env, c = m.group(4), m.group(5)
            if env == "equation":
                eq_block(c)
            elif env == "align":
                for line in c.split(r"\\"):
                    if line.strip():
                        eq_block(line)
            elif env == "figure":
                img = re.search(r"\\includegraphics(?:\[.*?\])?\{([^}]*)\}", c).group(1)
                cap = re.search(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}", c).group(1)
                lab = re.search(r"\\label\{([^}]*)\}", c).group(1)
                blocks.append(("fig", os.path.basename(img).replace(".pdf", ""), ctx.labels[lab], brc.inline(cap, ctx)))
            elif env.startswith("table"):
                cap = re.search(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}", c).group(1)
                lab = re.search(r"\\label\{([^}]*)\}", c).group(1)
                tab = re.search(r"\\begin\{tabular\}\{.*?\}\n(.*?)\\end\{tabular\}", c, re.S).group(1)
                rows = []
                for raw in tab.split(r"\\"):
                    raw = re.sub(r"\\(toprule|midrule|bottomrule)", "", raw).strip()
                    if raw:
                        rows.append([brc.inline(x, ctx) for x in raw.split("&")])
                blocks.append(("table", ctx.labels[lab], brc.inline(cap, ctx), rows, env == "table*"))
            elif env == "algorithm":
                cap = re.search(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}", c).group(1)
                lab = re.search(r"\\label\{([^}]*)\}", c).group(1)
                alg = re.search(r"\\begin\{algorithmic\}\[1\](.*?)\\end\{algorithmic\}", c, re.S).group(1)
                lines = [brc.inline(brc.expand_alg(x.strip()), ctx) for x in alg.split("\n") if x.strip()]
                blocks.append(("alg", ctx.labels[lab], brc.inline(cap, ctx), lines))
            elif env in ("enumerate", "itemize"):
                items = [x for x in re.split(r"\\item", c) if x.strip()]
                for n, it in enumerate(items, 1):
                    label = f"{n})" if env == "enumerate" else "\u2022"
                    parts = re.split(r"\\begin\{equation\}(.*?)\\end\{equation\}", it, flags=re.S)
                    for pi, part in enumerate(parts):
                        if pi % 2:
                            eq_block(part)
                        elif part.strip():
                            blocks.append(("item", label if pi == 0 else "", brc.inline(part, ctx)))
            elif env == "IEEEproof":
                blocks.append(("proof", brc.inline(c, ctx)))
            else:
                lab = re.search(r"\\label\{([^}]*)\}", c)
                num = ctx.labels.get(lab.group(1), "") if lab else ""
                opt = re.match(r"\s*\[([^\]]*)\]", c)
                if opt:
                    c = c[opt.end():]
                head = f"{env.capitalize()} {num}" + (f" ({opt.group(1)})" if opt else "")
                c = re.sub(r"\\label\{[^}]*\}", "", c)
                items = []
                if r"\begin{enumerate}" in c:
                    pre, rest = c.split(r"\begin{enumerate}")
                    items = [brc.inline(x, ctx) for x in re.split(r"\\item", rest.split(r"\end{enumerate}")[0]) if x.strip()]
                    c = pre
                blocks.append(("thm", head, brc.inline(c, ctx), items))
    tail = body[pos:]
    for p in re.split(r"\n\s*\n", tail):
        if p.strip() and "bibliography" not in p:
            blocks.append(("para", brc.inline(p, ctx)))
    blocks.append(("refs", [brc.fmt_ref(ctx.bib[k]) for k in ctx.cite_order]))
    return blocks


# =============================================================== render
def render(blocks, figs):
    body, media, rels = [], [], []
    fig_id = [0]
    eq_tabs = [("center", COL_W // 2), ("right", COL_W)]
    rule_tb = ('<w:pBdr><w:top w:val="single" w:sz="8" w:space="1" w:color="000000"/>'
               '<w:bottom w:val="single" w:sz="4" w:space="1" w:color="000000"/></w:pBdr>')
    runin = ""
    header_text = ""
    footnotes = []

    for b in blocks:
        t = b[0]
        if t == "title":
            _, title, authors, thanks, header_text = b
            body.append(para(run(title, sz=48), style="PaperTitle"))
            body.append(para(run(authors, sz=22) +
                             '<w:r><w:footnoteReference w:customMarkFollows="1" w:id="1"/></w:r>'
                             + run("\u200a", sz=22), style="Author"))
            footnotes = thanks
            body.append(para("", spacing='<w:spacing w:before="0" w:after="120"/>', sect=sect_pr(1, continuous=False, header=True)))
        elif t == "abstract":
            _, abs_, kw = b
            body.append(para(run("Abstract", b=True, i=True, sz=18) + run("\u2014", b=True, sz=18) +
                             runs_from_html(abs_, b=True, sz=18), style="Abstract"))
            body.append(para(run("Index Terms", b=True, i=True, sz=18) + run("\u2014", b=True, sz=18) +
                             runs_from_html(kw, b=True, sz=18), style="Abstract"))
        elif t == "h1":
            _, num, text = b
            label = (f"{num}. " if num else "") + text
            body.append(para(run(label, sc=True), style="Heading1"))
        elif t == "h2":
            _, letter, text = b
            body.append(para(run(f"{letter}. ", i=True) + runs_from_html(text, i=True), style="Heading2"))
        elif t == "runin":
            runin = run(b[1] + ": ", i=True)
        elif t == "para":
            txt = b[1]
            if runin:
                body.append(para(runin + runs_from_html(txt), style="BodyText"))
                runin = ""
                continue
            if "\u2063DROPCAP\u2063" in txt:
                txt = txt.replace("\u2063DROPCAP\u2063", "")
                body.append(para(run("S", sz=40) + run("WARMS", caps=True) + runs_from_html(txt[len("warms"):]),
                                 style="BodyText", ind='<w:ind w:firstLine="0"/>'))
            else:
                body.append(para(runs_from_html(txt), style="BodyText"))
        elif t == "eq":
            _, mathhtml, n = b
            body.append(para(run("", tab=True) + runs_from_html(mathhtml) + run("", tab=True) + run(f"({n})"),
                             style="Equation", tabs=eq_tabs))
        elif t == "item":
            _, label, txt = b
            if label:
                body.append(para(run(label) + run("", tab=True) + runs_from_html(txt), style="ListItem",
                                 tabs=[("left", 360)]))
            else:
                body.append(para(runs_from_html(txt), style="ListItem"))
        elif t == "thm":
            _, head, txt, items = b
            body.append(para(run(head + ": ", i=True) + runs_from_html(txt, i=True), style="BodyText"))
            for n, it in enumerate(items, 1):
                body.append(para(run(f"{n})", i=True) + run("", tab=True) + runs_from_html(it, i=True),
                                 style="ListItem", tabs=[("left", 360)]))
        elif t == "proof":
            body.append(para(run("Proof: ", i=True) + runs_from_html(b[1]) + run("  \u25A1"), style="BodyText"))
        elif t == "pending":
            body.append(para(run("[RESULTS PENDING] ", b=True, color="8B0000") + runs_from_html(b[1]),
                             style="Pending", shade="FDEEEE",
                             border='<w:pBdr>' + "".join(f'<w:{s} w:val="single" w:sz="8" w:space="4" w:color="8B0000"/>'
                                                         for s in ("top", "left", "bottom", "right")) + "</w:pBdr>"))
        elif t == "fig":
            _, name, num, cap = b
            fig_id[0] += 1
            rid = f"rIdImg{fig_id[0]}"
            media.append((f"media/{name}.png", figs[name]))
            rels.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{name}.png"/>')
            body.append(para(drawing(rid, fig_id[0], figs[name], COL_W), style="Figure", keep_next=True))
            body.append(para(run(f"Fig. {num}. ", sz=16) + runs_from_html(cap, sz=16), style="FigCaption"))
        elif t == "table":
            _, num, cap, rows, wide = b
            if wide:   # close the two-column section, insert a one-column section for the wide table
                body.append(para("", sect=sect_pr(2)))
            body.append(para(run(f"TABLE {num}", sz=16), style="TableCaption", keep_next=True))
            body.append(para(runs_from_html(cap, sc=True, sz=16), style="TableCaption", keep_next=True,
                             spacing='<w:spacing w:before="0" w:after="80"/>'))
            body.append(table_xml(rows, TEXT_W if wide else COL_W))
            body.append(para("", spacing='<w:spacing w:before="0" w:after="120"/>',
                             sect=sect_pr(1) if wide else None))
        elif t == "alg":
            _, num, cap, lines = b
            body.append(para(run(f"Algorithm {num} ", b=True, sz=18) + runs_from_html(cap, sz=18),
                             style="AlgCaption", keep_next=True, border=rule_tb))
            for li, ln in enumerate(lines, 1):
                last = li == len(lines)
                bdr = '<w:pBdr><w:bottom w:val="single" w:sz="8" w:space="1" w:color="000000"/></w:pBdr>' if last else None
                body.append(para(run(f"{li}:", sz=16) + run("", tab=True) + runs_from_html(ln, sz=17),
                                 style="AlgLine", keep_next=not last, border=bdr, tabs=[("left", 300)]))
        elif t == "refs":
            body.append(para(run("References", sc=True), style="Heading1"))
            for n, r in enumerate(b[1], 1):
                body.append(para(run(f"[{n}]", sz=16) + run("", tab=True) + runs_from_html(r, sz=16),
                                 style="Reference", tabs=[("left", 360)]))
    return body, media, rels, header_text, footnotes


# =============================================================== package parts
W_NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')


def style(sid, name, sz=20, b=False, i=False, sc=False, jc="both", before=0, after=0, first=0, left=0, hanging=0,
          keep_next=False, line=None, based="Normal"):
    rpr = ('<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman"/>'
           + ("<w:b/><w:bCs/>" if b else "") + ("<w:i/><w:iCs/>" if i else "") + ("<w:smallCaps/>" if sc else "")
           + f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>')
    ind = f'<w:ind w:left="{left}" w:firstLine="{first}"/>' if not hanging else f'<w:ind w:left="{left}" w:hanging="{hanging}"/>'
    ln = f' w:line="{line}" w:lineRule="auto"' if line else ""
    ppr = (("<w:keepNext/>" if keep_next else "") + f'<w:spacing w:before="{before}" w:after="{after}"{ln}/>'
           + ind + f'<w:jc w:val="{jc}"/>')
    basedon = f'<w:basedOn w:val="{based}"/>' if based and sid != "Normal" else ""
    return (f'<w:style w:type="paragraph" w:customStyle="1" w:styleId="{sid}"><w:name w:val="{name}"/>{basedon}'
            f'<w:qFormat/><w:pPr>{ppr}</w:pPr><w:rPr>{rpr}</w:rPr></w:style>')


def styles_xml():
    s = [style("Normal", "Normal", jc="both"),
         style("PaperTitle", "Paper Title", sz=48, jc="center", after=120),
         style("Author", "Author", sz=22, jc="center", after=60),
         style("Abstract", "Abstract", sz=18, b=True, jc="both", after=80, first=202),
         style("Heading1", "IEEE Heading 1", sz=20, sc=True, jc="center", before=160, after=80, keep_next=True),
         style("Heading2", "IEEE Heading 2", sz=20, i=True, jc="left", before=120, after=60, keep_next=True),
         style("BodyText", "IEEE Body Text", sz=20, jc="both", first=202),
         style("Equation", "IEEE Equation", sz=20, jc="left", before=60, after=60),
         style("ListItem", "IEEE List", sz=20, jc="both", left=360, hanging=360),
         style("FigCaption", "IEEE Figure Caption", sz=16, jc="both", before=60, after=160),
         style("Figure", "IEEE Figure", sz=20, jc="center", before=120, after=0),
         style("TableCaption", "IEEE Table Caption", sz=16, jc="center", before=120, after=0),
         style("TableText", "IEEE Table Text", sz=16, jc="left"),
         style("AlgCaption", "IEEE Algorithm Caption", sz=18, jc="left", before=120, after=0),
         style("AlgLine", "IEEE Algorithm Line", sz=17, jc="left", left=300, hanging=300),
         style("Pending", "Results Pending Box", sz=18, jc="both", before=80, after=80),
         style("Reference", "IEEE Reference", sz=16, jc="both", left=360, hanging=360),
         style("Header", "IEEE Header", sz=16, jc="left"),
         style("FootnoteText", "footnote text", sz=16, jc="both")]
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles {W_NS}>'
            '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
            'w:cs="Times New Roman" w:eastAsia="Times New Roman"/><w:sz w:val="20"/><w:szCs w:val="20"/>'
            '<w:lang w:val="en-US"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="240" '
            'w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>' + "".join(s) +
            '<w:style w:type="character" w:styleId="FootnoteReference"><w:name w:val="footnote reference"/>'
            '<w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style></w:styles>')


def build():
    os.makedirs(OUT, exist_ok=True)
    ctx = brc.Ctx(brc.parse_bib(brc.BIB))
    blocks = walk(open(TEX, encoding="utf-8").read(), ctx)
    figs = hires_pngs()
    body, media, rels, header_text, thanks = render(blocks, figs)

    doc = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {W_NS}><w:body>'
           + "".join(body) + sect_pr(2) + "</w:body></w:document>")
    header = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:hdr {W_NS}>'
              + para(runs_from_html(header_text, sz=16) + run("", tab=True, sz=16)
                     + '<w:r><w:rPr><w:sz w:val="16"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>'
                       '<w:r><w:rPr><w:sz w:val="16"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
                       '<w:r><w:rPr><w:sz w:val="16"/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r>'
                       '<w:r><w:rPr><w:sz w:val="16"/></w:rPr><w:t>1</w:t></w:r>'
                       '<w:r><w:rPr><w:sz w:val="16"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r>',
                     style="Header", tabs=[("right", TEXT_W)]) + "</w:hdr>")
    fn_paras = "".join(para(runs_from_html(t, sz=16), style="FootnoteText") for t in thanks)
    footnotes = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:footnotes {W_NS}>'
                 '<w:footnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:footnote>'
                 '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>'
                 f'<w:footnote w:id="1">{fn_paras}</w:footnote></w:footnotes>')
    settings = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings {W_NS}>'
                '<w:defaultTabStop w:val="360"/><w:characterSpacingControl w:val="doNotCompress"/>'
                '<w:footnotePr><w:footnote w:id="-1"/><w:footnote w:id="0"/></w:footnotePr>'
                '<w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat>'
                '</w:settings>')
    doc_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                '<Relationship Id="rIdSettings" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>'
                '<Relationship Id="rIdHeader1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>'
                '<Relationship Id="rIdFootnotes" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes" Target="footnotes.xml"/>'
                + "".join(rels) + "</Relationships>")
    content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Default Extension="png" ContentType="image/png"/>'
                     '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                     '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                     '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
                     '<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
                     '<Override PartName="/word/footnotes.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>'
                     '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                     '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
                     '</Types>')
    root_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                 '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
                 '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
                 '</Relationships>')
    title = next(b for b in blocks if b[0] == "title")[1]
    core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:title>{escape(title)}</dc:title><dc:creator>[Author Name]</dc:creator></cp:coreProperties>')
    app = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
           '<Application>build_ieee_docx.py</Application></Properties>')

    path = os.path.join(OUT, "Manuscript_IEEE.docx")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
        z.writestr("word/document.xml", doc)
        z.writestr("word/styles.xml", styles_xml())
        z.writestr("word/settings.xml", settings)
        z.writestr("word/header1.xml", header)
        z.writestr("word/footnotes.xml", footnotes)
        z.writestr("word/_rels/document.xml.rels", doc_rels)
        for arc, src in media:
            z.write(src, "word/" + arc)
    print(path)
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        tmp = tempfile.mkdtemp(prefix="ieeepdf_")
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp, path],
                       capture_output=True, timeout=300)
        pdf = os.path.join(tmp, "Manuscript_IEEE.pdf")
        if os.path.exists(pdf):
            shutil.move(pdf, os.path.join(OUT, "Manuscript_IEEE_preview.pdf"))
            print(os.path.join(OUT, "Manuscript_IEEE_preview.pdf"))


if __name__ == "__main__":
    build()
