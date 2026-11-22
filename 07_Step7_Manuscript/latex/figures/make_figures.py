"""Generate the manuscript figures as SVG (standard library only).

Usage:  python3 make_figures.py            -> writes fig1..fig4 .svg next to this file
Convert to PDF for LaTeX (LibreOffice):
        soffice --headless --convert-to pdf fig1_overview.svg
"""
import os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "Liberation Serif, Times New Roman, serif"
INK = "#1a1a1a"
GREY = "#666666"
LIGHT = "#f2f2f2"
ACCENT = "#1f4e79"
ACCENT_FILL = "#dbe7f3"
WARN = "#9c2a2a"
WARN_FILL = "#f6dede"


class SVG:
    def __init__(self, w, h):
        self.w, self.h, self.items = w, h, []
        self.items.append(
            '<defs>'
            f'<marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker>'
            f'<marker id="arrg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{GREY}"/></marker>'
            '</defs>')

    def rect(self, x, y, w, h, fill="white", stroke=INK, sw=1.2, rx=6, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def ellipse(self, cx, cy, rx, ry, fill="none", stroke=INK, sw=1.2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def circle(self, cx, cy, r, fill="white", stroke=INK, sw=1.2, dash=None):
        self.ellipse(cx, cy, r, r, fill, stroke, sw, dash)

    def line(self, x1, y1, x2, y2, stroke=INK, sw=1.2, arrow=False, dash=None, both=False, grey=False):
        m = "arrg" if grey else "arr"
        a = f' marker-end="url(#{m})"' if arrow else ""
        if both:
            a += f' marker-start="url(#{m})"'
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{a}{d}/>')

    def path(self, d, stroke=INK, sw=1.2, arrow=False, dash=None, fill="none"):
        a = ' marker-end="url(#arr)"' if arrow else ""
        ds = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{a}{ds}/>')

    def text(self, x, y, s, size=13, anchor="middle", weight="normal", fill=INK, italic=False):
        st = ' font-style="italic"' if italic else ""
        lines = s.split("\n")
        dy0 = -(len(lines) - 1) * size * 0.6
        for i, ln in enumerate(lines):
            self.items.append(
                f'<text x="{x}" y="{y + dy0 + i * size * 1.2 + size * 0.35}" font-family="{FONT}" font-size="{size}" '
                f'text-anchor="{anchor}" font-weight="{weight}" fill="{fill}"{st}>{escape(ln)}</text>')

    def box(self, x, y, w, h, label, fill="white", stroke=INK, size=13, weight="normal", dash=None, rx=6):
        self.rect(x, y, w, h, fill=fill, stroke=stroke, rx=rx, dash=dash)
        self.text(x + w / 2, y + h / 2, label, size=size, weight=weight)

    def save(self, name):
        p = os.path.join(HERE, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                    f'viewBox="0 0 {self.w} {self.h}">\n<rect width="100%" height="100%" fill="white"/>\n')
            f.write("\n".join(self.items))
            f.write("\n</svg>\n")
        return p


def drone(s, x, y, label, crashed=False, fill=ACCENT_FILL):
    if crashed:
        s.line(x - 24, y - 24, x + 24, y + 24, stroke=WARN, sw=2.2)
        s.line(x - 24, y + 24, x + 24, y - 24, stroke=WARN, sw=2.2)
    s.circle(x, y, 17, fill=WARN_FILL if crashed else fill, stroke=WARN if crashed else ACCENT, sw=1.6)
    s.text(x, y, label, size=12, weight="bold")


def fig1():
    s = SVG(760, 430)
    s.rect(10, 10, 740, 340, fill="white", stroke=GREY, rx=4)
    s.text(380, 30, "Search-and-rescue area divided into M sectors (tasks)", size=13, italic=True, fill=GREY)
    for gx in range(1, 6):
        s.line(10 + gx * 740 / 6, 42, 10 + gx * 740 / 6, 350, stroke="#e3e3e3", sw=1)
    for gy in range(1, 4):
        s.line(10, 42 + gy * 77, 750, 42 + gy * 77, stroke="#e3e3e3", sw=1)
    # partition A
    s.ellipse(175, 165, 140, 85, fill="#eef4fa", stroke=ACCENT, dash="6,4")
    s.text(175, 95, "Partition A", size=12, weight="bold", fill=ACCENT)
    pa = {"1": (110, 150), "2": (190, 200), "3": (255, 140)}
    s.line(*pa["1"], *pa["2"], stroke=ACCENT, sw=1.8)
    s.line(*pa["2"], *pa["3"], stroke=ACCENT, sw=1.8)
    for k, (x, y) in pa.items():
        drone(s, x, y, "U" + k)
    # partition B
    s.ellipse(560, 140, 110, 70, fill="#eef4fa", stroke=ACCENT, dash="6,4")
    s.text(560, 82, "Partition B", size=12, weight="bold", fill=ACCENT)
    pb = {"4": (515, 150), "5": (605, 130)}
    s.line(*pb["4"], *pb["5"], stroke=ACCENT, sw=1.8)
    for k, (x, y) in pb.items():
        drone(s, x, y, "U" + k)
    # isolated U6
    s.circle(430, 265, 45, fill="none", stroke=GREY, dash="3,3")
    drone(s, 430, 265, "U6")
    s.text(430, 328, "isolated, alive", size=11, fill=GREY, italic=True)
    # crashed U7
    drone(s, 650, 285, "U7", crashed=True)
    s.text(650, 328, "crashed (silent)", size=11, fill=WARN, italic=True)
    # store-carry-forward arrows
    s.path("M 272 128 C 360 70, 420 80, 495 135", stroke=GREY, dash="5,4", arrow=True)
    s.text(385, 70, "store-carry-forward on contact", size=11, fill=GREY, italic=True)
    s.path("M 412 250 C 330 240, 260 235, 205 215", stroke=GREY, dash="5,4", arrow=True)
    s.text(300, 268, "later contact: ledger merge", size=11, fill=GREY, italic=True)
    # caption-like legend
    s.circle(40, 395, 9, fill=ACCENT_FILL, stroke=ACCENT)
    s.text(55, 395, "UAV running identical agent stack", size=12, anchor="start")
    s.line(300, 395, 335, 395, stroke=ACCENT, sw=1.8)
    s.text(342, 395, "D2D link (d ≤ Rc)", size=12, anchor="start")
    s.text(560, 395, "U6 and U7 look identical to peers", size=12, anchor="start", weight="bold", fill=WARN)
    return s.save("fig1_overview.svg")


def fig2():
    s = SVG(760, 520)
    s.rect(10, 10, 740, 500, fill="white", stroke=GREY, rx=8, dash="6,4")
    s.text(380, 30, "UAV i — onboard agent stack (identical on every UAV)", size=13, weight="bold")
    # radio + sync
    s.box(30, 60, 150, 50, "Radio\n(range Rc, lossy)", fill=LIGHT)
    s.box(30, 160, 150, 70, "M6 Sync engine\ndigest + prioritised\ndelta anti-entropy", fill=LIGHT, size=12)
    s.line(105, 110, 105, 160, both=True, arrow=True)
    # ledger
    s.rect(230, 55, 270, 190, fill=ACCENT_FILL, stroke=ACCENT, sw=1.6)
    s.text(365, 73, "M2 Mission ledger (CRDT replica)", size=13, weight="bold", fill=ACCENT)
    s.box(245, 90, 115, 60, "D: completed\nG-Set", size=12)
    s.box(372, 90, 115, 60, "H: evidence\nof life (max-reg.)", size=12)
    s.box(245, 165, 115, 65, "CL: claims\n(epoch, progress,\nrelease)", size=12)
    s.box(372, 165, 115, 65, "MEM:\nmembership\n2P-Set", size=12)
    s.line(180, 195, 230, 165, both=True, arrow=True)
    # suspicion / allocator / policy
    s.box(560, 60, 175, 70, "M1 Suspicion estimator\nψ = accrual φ + plan-\naware term (local only)", fill=WARN_FILL, size=12)
    s.box(560, 175, 175, 70, "M4 Allocator\nevent-driven async\nCBBA (own group)", fill=LIGHT, size=12)
    s.box(400, 300, 230, 75, "M3 Takeover policy\nMAPPO actor or threshold\nCONTINUE / HOLD / CLAIM(k)", fill="#e8f1e4", size=12)
    s.box(130, 300, 200, 75, "Executor\nnavigation, sector service,\nisolation & energy policy", fill=LIGHT, size=12)
    s.box(560, 420, 175, 55, "M5 Group coordinator\n(ablation only)", fill="white", size=12, dash="5,4")
    # arrows
    s.line(500, 110, 560, 95, arrow=True)          # ledger -> suspicion
    s.line(500, 200, 560, 210, arrow=True)         # ledger -> allocator
    s.line(690, 130, 690, 175, arrow=True)         # suspicion -> allocator
    s.line(600, 130, 560, 300, arrow=True)         # suspicion -> policy
    s.line(620, 245, 580, 300, arrow=True)         # allocator -> policy
    s.line(440, 245, 480, 300, arrow=True)         # ledger -> policy
    s.line(400, 337, 330, 337, arrow=True)         # policy -> executor
    s.line(647, 420, 647, 245, arrow=True, dash="5,4", grey=True)  # coord -> allocator
    s.path("M 230 300 C 230 270, 260 255, 290 245", arrow=True)    # executor -> ledger
    s.text(150, 268, "progress, completion,\nclaims, heartbeat", size=11, fill=GREY, italic=True)
    s.box(130, 420, 200, 50, "Own state: position,\nenergy, GNSS clock", fill="white", size=12)
    s.line(230, 420, 230, 375, arrow=True)
    s.text(380, 495, "Merged state (ledger) is convergent; suspicion ψ is a local view and never merged.",
           size=12, italic=True, fill=GREY)
    return s.save("fig2_components.svg")


def fig3():
    s = SVG(760, 640)
    W = 300
    cx = 210

    def node(y, label, fill="white", h=52):
        s.box(cx - W / 2, y, W, h, label, fill=fill, size=12)
        return y + h

    def diamond(x, y, w, h, label):
        s.path(f"M {x} {y} L {x + w / 2} {y + h / 2} L {x} {y + h} L {x - w / 2} {y + h / 2} Z", fill="#fff8e1")
        s.text(x, y + h / 2, label, size=12)

    y = 15
    b = node(y, "Peer j silent in UAV i's view")
    s.line(cx, b, cx, b + 18, arrow=True)
    b = node(b + 18, "Suspicion ψ_ij = accrual φ_ij\n+ κ·(time silent while expected in range)", fill=WARN_FILL, h=58)
    s.line(cx, b, cx, b + 18, arrow=True)
    b = node(b + 18, "j's unfinished tasks become orphan\ncandidates (with ψ of their owner)")
    s.line(cx, b, cx, b + 18, arrow=True)
    diamond(cx, b + 18, 280, 78, "Takeover policy:\nCONTINUE / HOLD / CLAIM k")
    dy = b + 18 + 78
    s.path(f"M {cx - 140} {b + 18 + 39} L {30} {b + 18 + 39} L 30 {40} L {cx - W / 2} 40", arrow=True)
    s.text(38, b + 18 - 60, "continue\n/ hold", size=11, anchor="start", fill=GREY, italic=True)
    s.line(cx, dy, cx, dy + 18, arrow=True)
    s.text(cx + 30, dy + 9, "CLAIM k", size=11, anchor="start", fill=GREY, italic=True)
    b = node(dy + 18, "Write claim on k: epoch = max known + 1;\ngossip; fly to k; record progress", fill="#e8f1e4", h=56)
    s.line(cx, b, cx, b + 18, arrow=True)
    diamond(cx, b + 18, 280, 70, "Does j reappear before\nk is completed?")
    q = b + 18
    # no branch
    s.line(cx, q + 70, cx, q + 95, arrow=True)
    s.text(cx + 10, q + 82, "no (j had crashed)", size=11, anchor="start", fill=GREY, italic=True)
    b2 = node(q + 95, "Complete k → add to D (G-Set)\nself-healing achieved", fill=ACCENT_FILL)
    # yes branch
    s.line(cx + 140, q + 35, 470, q + 35, arrow=True)
    s.text(395, q + 22, "yes (false suspicion)", size=11, fill=GREY, italic=True)
    diamond(590, q, 240, 70, "j's progress ρ_kj ≥ ρ_min ?")
    s.line(590, q + 70, 590, q + 95, arrow=True)
    s.text(600, q + 82, "yes", size=11, anchor="start", fill=GREY, italic=True)
    s.box(475, q + 95, 230, 62, "j reasserts (epoch + 1); owner\nrule selects j; i yields\n(i's travel counted as wasted)", size=12)
    s.line(710, q + 35, 745, q + 35)
    s.line(745, q + 35, 745, q - 60)
    s.line(745, q - 60, 705, q - 60, arrow=True)
    s.text(740, q - 70, "no", size=11, anchor="end", fill=GREY, italic=True)
    s.box(475, q - 92, 230, 62, "j yields to i; j's partial\nservice counted as\nduplicated work", size=12)
    # converge
    s.box(cx - W / 2 + 60, b2 + 40, 510, 48, "All replicas converge to the same owner and completion state once merged",
          fill=LIGHT, size=12, weight="bold")
    s.line(cx, b2, cx, b2 + 40, arrow=True)
    s.line(590, q + 157, 590, b2 + 40, arrow=True)
    s.path(f"M 475 {q - 61} L 440 {q - 61} L 440 {b2 + 40}", arrow=True)
    return s.save("fig3_recovery.svg")


def fig4():
    s = SVG(760, 330)
    x0, x1 = 90, 730
    T = 320.0

    def X(t):
        return x0 + (x1 - x0) * t / T
    lanes = {"U3": 80, "U5": 175}
    s.text(380, 22, "Example: a disconnected UAV continues its mission and later reconciles", size=13, weight="bold")
    for name, y in lanes.items():
        s.text(45, y, name, size=13, weight="bold")
        s.line(x0, y, x1, y, stroke="#bbbbbb", sw=2)
    # connectivity band
    s.rect(X(0), 225, X(120) - X(0), 16, fill=ACCENT_FILL, stroke=ACCENT, rx=2)
    s.rect(X(120), 225, X(300) - X(120), 16, fill=WARN_FILL, stroke=WARN, rx=2)
    s.rect(X(300), 225, X(320) - X(300), 16, fill=ACCENT_FILL, stroke=ACCENT, rx=2)
    s.text(X(60), 233, "connected", size=11)
    s.text(X(210), 233, "U3 out of range (link lost)", size=11)
    # axis
    s.line(x0, 270, x1, 270, arrow=True)
    for t in (0, 60, 120, 180, 240, 300):
        s.line(X(t), 265, X(t), 275)
        s.text(X(t), 290, f"{t}", size=11)
    s.text(x1, 310, "time (s)", size=11, anchor="end", italic=True)

    def ev(t, lane, label, color=INK, up=True):
        y = lanes[lane]
        s.circle(X(t), y, 5, fill=color, stroke=color)
        s.text(X(t), y - 22 if up else y + 24, label, size=11)
    ev(0, "U3", "owns k7, k8 (ε=1)")
    ev(150, "U3", "k7 done (local D)")
    ev(210, "U3", "starts k8")
    ev(280, "U3", "ρ(k8)=0.75", up=False)
    ev(240, "U5", "ψ(U3) high → CLAIM k8 (ε=2)", color=WARN)
    ev(300, "U3", "reassert k8 (ε=3)", color=ACCENT)
    ev(300, "U5", "yields k8; travel → wasted", color=GREY, up=False)
    s.line(X(300), lanes["U3"] + 6, X(300), lanes["U5"] - 6, both=True, arrow=True, stroke=ACCENT, sw=1.6)
    s.text(X(300) + 6, 128, "contact:\nmerge", size=11, anchor="start", fill=ACCENT)
    return s.save("fig4_example.svg")


if __name__ == "__main__":
    for f in (fig1, fig2, fig3, fig4):
        print(f())
