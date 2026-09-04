import io, re, html

import os
BASE = os.path.dirname(os.path.abspath(__file__)) + "/../"  # docs/Claude_docs/
PARTS = [
    ("part-clocks", "Clocks and rosters", "The trade-off ledger for untying skill duration k and agent count N, with the repository's tie points, toy numbers, and labelled literature.", "research_notes/UNTIED_K_N_TRADEOFF_LEDGER_20260901.md"),
    ("part-workflow", "The workflow, reviewed", "The Codex science workflow read as a research process: what it is, what it produced, where it fails, and what to change first.", "reviews/CODEX_SCIENCE_WORKFLOW_REVIEW_20260901.md"),
    ("part-hosts", "Hosts", "Design advice for the toy hosts and the UAV environment, with one parametric family proposed to replace five incompatible ones.", "environment_design/TOY_HOST_AND_UAV_ENV_DESIGN_ADVICE_20260901.md"),
]

LABEL_RE = re.compile(r"^((?:K|N)-\d|[DPURF]\d|Q\d)[.\s]\s*")
ALPHA_RE = re.compile(r"^\(([a-e])\)\s+")


def inline(text):
    t = html.escape(text, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    return t


def render_table(lines):
    rows = [l.strip().strip("|").split("|") for l in lines]
    rows = [[c.strip() for c in r] for r in rows]
    header = rows[0]
    aligns = []
    if len(rows) > 1 and all(re.fullmatch(r":?-{3,}:?", c) for c in rows[1]):
        for c in rows[1]:
            aligns.append("right" if c.endswith(":") and not c.startswith(":") else ("center" if c.startswith(":") and c.endswith(":") else "left"))
        body = rows[2:]
    else:
        aligns = ["left"] * len(header)
        body = rows[1:]
    def td(tag, cells):
        out = []
        for i, c in enumerate(cells):
            a = aligns[i] if i < len(aligns) else "left"
            cls = f' class="al-{a}"' if a != "left" else ""
            out.append(f"<{tag}{cls}>{inline(c)}</{tag}>")
        return "".join(out)
    h = f"<thead><tr>{td('th', header)}</tr></thead>"
    b = "<tbody>" + "".join(f"<tr>{td('td', r)}</tr>" for r in body) + "</tbody>"
    return f'<div class="tablewrap"><table>{h}{b}</table></div>'


def render_md(md, skip_first_h1=True):
    lines = md.split("\n")
    out = []
    i = 0
    para = []
    list_type = None  # 'ul' | 'ol' | 'alpha'
    list_items = []

    def flush_para():
        nonlocal para
        if para:
            text = " ".join(para).strip()
            m = LABEL_RE.match(text)
            if m:
                label = m.group(1)
                rest = text[m.end():]
                out.append(f'<p class="ledger"><span class="tag">{label}</span>{inline(rest)}</p>')
            else:
                out.append(f"<p>{inline(text)}</p>")
            para = []

    def flush_list():
        nonlocal list_type, list_items
        if list_type:
            tag = "ul" if list_type == "ul" else "ol"
            cls = ' class="alpha"' if list_type == "alpha" else ""
            out.append(f"<{tag}{cls}>" + "".join(f"<li>{inline(x)}</li>" for x in list_items) + f"</{tag}>")
            list_type, list_items = None, []

    first_h1_seen = False
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if s.startswith("|"):
            flush_para(); flush_list()
            tbl = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tbl.append(lines[i]); i += 1
            out.append(render_table(tbl))
            continue
        if s == "":
            flush_para(); flush_list(); i += 1; continue
        m = re.match(r"^(#{1,3})\s+(.*)$", s)
        if m:
            flush_para(); flush_list()
            level = len(m.group(1)); text = m.group(2)
            if level == 1:
                if skip_first_h1 and not first_h1_seen:
                    first_h1_seen = True; i += 1; continue
            hl = min(level + 1, 4)
            text = re.sub(r"^\d+\.\s+", "", text) if hl == 3 and re.match(r"^\d+\.\s", text) and "order to adopt" not in text else text
            out.append(f"<h{hl}>{inline(text)}</h{hl}>")
            i += 1; continue
        mb = re.match(r"^-\s+(.*)$", s)
        mn = re.match(r"^\d+\.\s+(.*)$", s)
        ma = ALPHA_RE.match(s)
        if mb:
            flush_para()
            if list_type not in (None, "ul"): flush_list()
            list_type = "ul"; list_items.append(mb.group(1)); i += 1; continue
        if mn and not LABEL_RE.match(s):
            flush_para()
            if list_type not in (None, "ol"): flush_list()
            list_type = "ol"; list_items.append(mn.group(1)); i += 1; continue
        if ma:
            flush_para()
            if list_type not in (None, "alpha"): flush_list()
            list_type = "alpha"; list_items.append(s[ma.end():]); i += 1; continue
        # continuation of a list item? (indented) -> append to last item
        if list_type and line.startswith("  ") and list_items:
            list_items[-1] += " " + s; i += 1; continue
        flush_list()
        para.append(s); i += 1
    flush_para(); flush_list()
    return "\n".join(out)


CSS = r"""
:root{
  --bg:#F5F7F9; --surface:#FFFFFF; --ink:#182028; --muted:#5B6673; --line:#D6DCE3;
  --accent:#1F4E9C; --accent-ink:#173B75; --accent-soft:#E3ECF9; --warn:#9A3B1E; --code-bg:#EDF1F5;
  --shadow:0 1px 0 rgba(24,32,40,.06);
  color-scheme:light;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#0F141A; --surface:#161C24; --ink:#E6EBF0; --muted:#98A3AF; --line:#2A3440;
    --accent:#7FA8F0; --accent-ink:#A9C4F5; --accent-soft:#1B2A44; --warn:#E08A66; --code-bg:#1D2530;
    --shadow:none; color-scheme:dark;
  }
}
:root[data-theme="dark"]{
  --bg:#0F141A; --surface:#161C24; --ink:#E6EBF0; --muted:#98A3AF; --line:#2A3440;
  --accent:#7FA8F0; --accent-ink:#A9C4F5; --accent-soft:#1B2A44; --warn:#E08A66; --code-bg:#1D2530;
  --shadow:none; color-scheme:dark;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-size:16px;line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none;border-bottom:1px solid transparent}
a:hover,a:focus-visible{border-bottom-color:var(--accent)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.page{max-width:1120px;margin:0 auto;padding:0 24px 96px}
header.masthead{padding:56px 0 28px;border-bottom:1px solid var(--line)}
.eyebrow{font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
h1{font-family:"IBM Plex Serif",Georgia,"Times New Roman",serif;font-weight:600;font-size:clamp(34px,4.6vw,52px);line-height:1.08;margin:10px 0 14px;text-wrap:balance;letter-spacing:-.01em}
.lede{font-size:18px;max-width:68ch;color:var(--muted);margin:0 0 26px}
.lede strong{color:var(--ink);font-weight:600}
figure.schematic{margin:8px 0 0;max-width:760px}
figure.schematic svg{width:100%;height:auto;display:block}
figure.schematic figcaption{font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;font-size:12px;color:var(--muted);margin-top:8px}
.seg{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1}
.seg.alt{fill:var(--surface)}
.gap{fill:none;stroke:var(--warn);stroke-width:1;stroke-dasharray:3 3}
.grid{stroke:var(--line);stroke-width:1}
.axis{stroke:var(--muted);stroke-width:1}
.lbl{font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;font-size:11px;fill:var(--muted)}
.lbl.strong{fill:var(--ink)}
nav.parts{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);margin:0 -24px;padding:0 24px}
nav.parts ol{list-style:none;margin:0;padding:0;display:flex;gap:28px;overflow-x:auto}
nav.parts a{display:block;padding:14px 0 12px;font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;font-size:13px;letter-spacing:.02em;color:var(--muted);border-bottom:2px solid transparent;white-space:nowrap}
nav.parts a:hover,nav.parts a:focus-visible{color:var(--ink);border-bottom-color:var(--accent)}
main{display:grid;grid-template-columns:1fr;gap:0}
section.part{padding:56px 0 24px;border-bottom:1px solid var(--line)}
section.part:last-child{border-bottom:0}
.part-head{display:grid;grid-template-columns:minmax(0,72ch);gap:6px;margin-bottom:28px}
.part-head .eyebrow{color:var(--accent)}
.part-head h2{font-family:"IBM Plex Serif",Georgia,serif;font-weight:600;font-size:clamp(28px,3.4vw,38px);line-height:1.12;margin:0;text-wrap:balance}
.part-head p{margin:6px 0 0;color:var(--muted);max-width:68ch;font-size:17px}
.prose{max-width:72ch}
.prose h3{font-family:"IBM Plex Serif",Georgia,serif;font-weight:600;font-size:24px;line-height:1.2;margin:44px 0 12px;text-wrap:balance}
.prose h4{font-family:"IBM Plex Sans",system-ui,sans-serif;font-weight:600;font-size:17px;margin:28px 0 8px}
.prose p{margin:0 0 14px}
.prose ul,.prose ol{margin:0 0 16px;padding-left:22px}
.prose li{margin:0 0 6px}
.prose ol.alpha{list-style:lower-alpha}
.prose code{font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;font-size:.88em;background:var(--code-bg);padding:.08em .35em;border-radius:3px;color:var(--ink)}
.prose strong{font-weight:600}
p.ledger{position:relative;padding-left:0;margin:0 0 16px}
p.ledger .tag{display:inline-block;font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;font-size:12px;letter-spacing:.06em;color:var(--accent-ink);background:var(--accent-soft);padding:2px 7px;border-radius:3px;margin-right:10px;vertical-align:middle;transform:translateY(-1px)}
@media (min-width:1000px){
  p.ledger{padding-left:0}
  p.ledger .tag{position:absolute;left:-76px;top:.25em;margin:0}
  .prose{margin-left:76px}
  .part-head{margin-left:76px}
}
.tablewrap{overflow-x:auto;margin:6px 0 22px;border:1px solid var(--line);border-radius:4px;background:var(--surface);box-shadow:var(--shadow);max-width:min(100%,1040px)}
table{border-collapse:collapse;width:100%;font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;font-variant-numeric:tabular-nums;line-height:1.4}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}
th{font-weight:600;color:var(--muted);letter-spacing:.02em;background:var(--bg);white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
td.al-right,th.al-right{text-align:right}
td.al-center,th.al-center{text-align:center}
td code,th code{background:transparent;padding:0;font-size:inherit}
.prose .tablewrap{max-width:none;width:min(1040px,calc(100vw - 48px))}
footer.colophon{margin-top:56px;padding-top:18px;border-top:1px solid var(--line);font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;font-size:12px;color:var(--muted);max-width:80ch}
@media (prefers-reduced-motion: reduce){*{scroll-behavior:auto!important}}
html{scroll-behavior:smooth}
"""

SVG = """
<svg viewBox="0 0 760 178" role="img" aria-labelledby="schem-title" xmlns="http://www.w3.org/2000/svg">
  <title id="schem-title">Three clocks from the repository: fixed k = 10 synchronous segments; process-core lifetimes of 30 and 70 steps on the shared 10-step grid; a temporary roster leave from step 40 to 80 with the skill frozen.</title>
  <g class="gridlines">
    GRID
  </g>
  <text class="lbl strong" x="0" y="26">k = 10, synchronous</text>
  <text class="lbl" x="0" y="40">base route, two agents</text>
  ROW1
  <text class="lbl strong" x="0" y="82">lifetimes 30 / 70</text>
  <text class="lbl" x="0" y="96">process-core, 10-step grid</text>
  ROW2
  <text class="lbl strong" x="0" y="138">temporary leave 40–80</text>
  <text class="lbl" x="0" y="152">roster event, skill frozen</text>
  ROW3
  <line class="axis" x1="160" y1="168" x2="760" y2="168"/>
  AXIS
</svg>
"""


def build_svg():
    x0, px = 160, 5  # 0..120 steps -> 600 px
    grid = "".join(f'<line class="grid" x1="{x0+px*t}" y1="12" x2="{x0+px*t}" y2="164"/>' for t in range(0, 121, 10))
    def segs(y, bounds, h=12, alt_every=True):
        out = []
        for j in range(len(bounds)-1):
            a, b = bounds[j], bounds[j+1]
            cls = "seg" + (" alt" if (alt_every and j % 2) else "")
            out.append(f'<rect class="{cls}" x="{x0+px*a+0.5}" y="{y}" width="{px*(b-a)-1}" height="{h}" rx="1.5"/>')
        return "".join(out)
    row1 = segs(16, list(range(0, 121, 10))) + segs(32, list(range(0, 121, 10)))
    row2 = segs(72, [0, 30, 100, 120]) + segs(88, [0, 70, 100, 120])
    # row3: present 0-40, gap 40-80 dashed, rejoin 80-120
    row3 = (f'<rect class="seg" x="{x0+0.5}" y="128" width="{px*40-1}" height="12" rx="1.5"/>'
            f'<rect class="gap" x="{x0+px*40+0.5}" y="128" width="{px*40-1}" height="12" rx="1.5"/>'
            f'<rect class="seg" x="{x0+px*80+0.5}" y="128" width="{px*40-1}" height="12" rx="1.5"/>'
            f'<text class="lbl" x="{x0+px*60}" y="150" text-anchor="middle">skill and age held</text>')
    axis = "".join(f'<text class="lbl" x="{x0+px*t}" y="178" text-anchor="middle">{t}</text>' for t in range(0, 121, 20))
    return SVG.replace("GRID", grid).replace("ROW1", row1).replace("ROW2", row2).replace("ROW3", row3).replace("AXIS", axis)


def main():
    parts_html = []
    for pid, title, blurb, fname in PARTS:
        md = io.open(BASE + fname, encoding="utf-8").read()
        body = render_md(md)
        parts_html.append(f"""
<section class="part" id="{pid}">
  <div class="part-head">
    <div class="eyebrow">{html.escape(title)}</div>
    <h2>{html.escape(title)}</h2>
    <p>{html.escape(blurb)}</p>
  </div>
  <div class="prose">
  {body}
  </div>
</section>""")
    nav = "".join(f'<li><a href="#{pid}">{html.escape(t)}</a></li>' for pid, t, _, _ in PARTS)
    page = f"""<title>Clocks and Rosters</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@400;600&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>{CSS}</style>
<div class="page">
<header class="masthead">
  <div class="eyebrow">HMASD · 2026-09-01 review · addenda 2026-09-02</div>
  <h1>Clocks and Rosters</h1>
  <p class="lede">What it costs to let a skill run for an <strong>unfixed duration</strong> and a team have an <strong>unfixed size</strong> in HMASD-style multi-agent RL, with the repository's own tie points, toy numbers, and labelled literature; followed by a review of the Codex science workflow and design advice for the toy hosts and the UAV environment.</p>
  <figure class="schematic">
    {build_svg()}
    <figcaption>Steps 0–120. Constants are the repository's: k = 10 (config_1.py), lifetimes from (3, 7, 13, 24) intervals (ha_ctse_process/config.py), TEMPORARY_LEAVE keeps the skill and its age (variable_roster_event.py).</figcaption>
  </figure>
</header>
<nav class="parts" aria-label="Parts"><ol>{nav}</ol></nav>
<main>
{''.join(parts_html)}
</main>
<footer class="colophon">Prepared by Claude Fable 5.1 as a read-only review. Sources: two literature scouts (local libraries and web), one repository scout, one workflow scout, one environment scout, an Opus toy-model study, and a Fable red-team pass whose corrections are incorporated. For the 2026-09-01 review no repository file was changed and no experiment was run. On 2026-09-02, after the owner set the research paradigm, an addendum was added to each part and the same calibration was written into docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md as section 11, at the owner's request.</footer>
</div>
"""
    out = BASE + "artifacts/clocks_and_rosters_20260902.html"
    io.open(out, "w", encoding="utf-8", newline="\n").write(page)
    # structural check
    from html.parser import HTMLParser
    class Chk(HTMLParser):
        def __init__(self):
            super().__init__(); self.stack=[]; self.errors=[]
        def handle_starttag(self, tag, attrs):
            if tag not in ("link","meta","br","hr","img","line","rect","input"): self.stack.append(tag)
        def handle_endtag(self, tag):
            if tag in ("line","rect","link"): return
            if self.stack and self.stack[-1]==tag: self.stack.pop()
            else: self.errors.append((tag, list(self.stack[-3:])))
    c = Chk(); c.feed(page)
    print("bytes", len(page.encode("utf-8")), "unclosed", c.stack[:5], "mismatches", c.errors[:5])

main()
