"""Bind the four handouts into one printable PDF: handouts/print/SCAD_Robotics_Simulation_Handouts.pdf

    pip install markdown playwright && playwright install chromium
    python handouts/build_print.py
"""

import re
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
OUT = HERE / "print"
FILES = ["01-vocabulary.md", "02-learning-resources.md", "03-leave-behind-project.md", "04-visual-guide.md"]

CSS = """
@page { size: Letter; margin: 0.6in 0.65in 0.7in; }
:root { --ink:#1b1a18; --muted:#5d5a54; --gold:#c8901a; --rule:#e2ddd2; --wash:#f7f4ee; }
html { background:#fff; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; color: var(--ink); font-size: 10.2pt; line-height: 1.42; margin:0; }
.sheet { page-break-after: always; }
.sheet:last-child { page-break-after: auto; }
.mast { border-left: 6px solid var(--gold); padding: 4px 0 4px 12px; margin-bottom: 14px; }
.mast .k { font-size: 8.5pt; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.mast .t { font-size: 11pt; font-weight: 700; }
h1 { font-size: 19pt; margin: 0 0 4px; letter-spacing: -0.01em; }
h2 { font-size: 13pt; margin: 18px 0 6px; padding-bottom: 3px; border-bottom: 1px solid var(--rule); }
h3 { font-size: 11pt; margin: 14px 0 4px; color: #3b3832; }
h1, h2, h3 { page-break-after: avoid; break-after: avoid; }
p { margin: 5px 0 7px; }
a { color: #1f4fa3; text-decoration: none; word-break: break-word; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 10px; font-size: 9.2pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th, td { border-bottom: 1px solid var(--rule); padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: var(--wash); font-weight: 700; }
td:first-child { white-space: nowrap; }
code { font-family: Menlo, Consolas, monospace; font-size: 8.6pt; background: var(--wash); padding: 0 3px; border-radius: 3px; }
pre { background: var(--wash); border: 1px solid var(--rule); border-radius: 6px; padding: 8px 10px; font-size: 8.2pt; line-height: 1.35; overflow: hidden; white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
img { max-width: 100%; display: block; margin: 6px auto 4px; page-break-inside: avoid; }
ul { margin: 4px 0 8px; padding-left: 20px; }
li { margin: 2px 0; }
.foot { margin-top: 18px; font-size: 8pt; color: var(--muted); border-top: 1px solid var(--rule); padding-top: 6px; }
"""


def render(md_text: str) -> str:
    # drop the per-file byline: the masthead carries it
    md_text = re.sub(r"^\*\*Simulation for Robotics.*\*\*\n", "", md_text, flags=re.M)
    md_text = md_text.replace("- [ ] ", "- ☐ ")
    html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    return html.replace('src="img/', f'src="file://{HERE}/img/').replace('href="../', 'href="https://github.com/mrpillis/scad-robotics-simulation-demo/blob/main/')


def main():
    sheets = []
    for f in FILES:
        body = render((HERE / f).read_text())
        sheets.append(f'<section class="sheet"><div class="mast"><div class="k">SCAD · Savannah College of Art &amp; Design</div>'
                      f'<div class="t">D. Pillis · Robotics Professor Demo · Simulation for Robotics</div></div>{body}'
                      f'<div class="foot">github.com/mrpillis/scad-robotics-simulation-demo</div></section>')
    doc = f"<!doctype html><html><head><meta charset='utf-8'><title>SCAD Robotics Simulation Handouts</title><style>{CSS}</style></head><body>{''.join(sheets)}</body></html>"
    OUT.mkdir(exist_ok=True)
    html_path = OUT / "handouts.html"
    html_path.write_text(doc)

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"])
        pg = b.new_page()
        pg.goto(html_path.as_uri())
        pg.wait_for_load_state("networkidle")
        pg.pdf(path=str(OUT / "SCAD_Robotics_Simulation_Handouts.pdf"), format="Letter", print_background=True,
               display_header_footer=True, header_template="<span></span>",
               footer_template="<div style='font-size:7pt;color:#888;width:100%;text-align:center'>"
                               "<span class='pageNumber'></span> / <span class='totalPages'></span></div>",
               margin={"top": "0.6in", "bottom": "0.7in", "left": "0.65in", "right": "0.65in"})
        b.close()
    html_path.unlink()
    print("PDF ->", (OUT / "SCAD_Robotics_Simulation_Handouts.pdf").relative_to(HERE.parent))


if __name__ == "__main__":
    main()
