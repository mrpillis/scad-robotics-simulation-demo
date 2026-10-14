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
@font-face { font-family: "Montserrat"; src: url("FONTDIR/Montserrat[wght].ttf"); font-weight: 100 900; }
@page { size: Letter; margin: 0.6in 0.65in 0.7in; }
:root { --pink:#EC008C; --pink-soft:#FDE3F1; }
html { background:#fff; }
body { font-family: "Montserrat", Helvetica, Arial, sans-serif; color: #000; font-size: 9.2pt; font-weight: 400; line-height: 1.55; margin:0; }
.sheet { page-break-after: always; }
.sheet:last-child { page-break-after: auto; }
.mast { background: var(--pink); color:#000; padding: 10px 14px; margin-bottom: 18px; text-transform: uppercase; }
.mast .k { font-weight: 250; font-size: 13pt; letter-spacing: .08em; }
.mast .t { font-weight: 400; font-size: 7pt; letter-spacing: .16em; }
h1 { font-weight: 200; font-size: 24pt; line-height: 1.08; margin: 0 0 12px; text-transform: uppercase; letter-spacing: .04em; color: #000; }
h2 { font-weight: 300; font-size: 12.5pt; margin: 22px 0 8px; text-transform: uppercase; letter-spacing: .1em; color:#000; padding-bottom: 4px; border-bottom: 3px solid var(--pink); }
h3 { font-weight: 500; font-size: 8.6pt; margin: 14px 0 4px; text-transform: uppercase; letter-spacing: .14em; color: #000; }
h1, h2, h3 { page-break-after: avoid; break-after: avoid; }
p { margin: 5px 0 7px; }
a { color: #000; text-decoration: underline; text-decoration-color: var(--pink); word-break: break-word; }
strong { font-weight: 600; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 10px; font-size: 8.4pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th, td { border-bottom: 1px solid #000; padding: 5px 7px; text-align: left; vertical-align: top; }
th { background: var(--pink); color: #000; font-weight: 500; text-transform: uppercase; letter-spacing: .12em; font-size: 7.4pt; }
td { font-weight: 300; }
td:first-child { white-space: nowrap; font-weight: 500; }
code { font-family: Menlo, Consolas, monospace; font-size: 7.8pt; background: var(--pink-soft); padding: 0 3px; border-radius: 3px; }
pre { background: #fff; color: #000; border: 1px solid #000; border-left: 6px solid var(--pink); border-radius: 4px; padding: 8px 10px; font-size: 7.6pt; line-height: 1.4; overflow: hidden; white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
img { max-width: 100%; display: block; margin: 6px auto 4px; page-break-inside: avoid; }
ul { margin: 4px 0 8px; padding-left: 20px; }
li { margin: 2px 0; }
li::marker { color: var(--pink); }
.foot { margin-top: 18px; font-size: 7pt; text-transform: uppercase; letter-spacing: .14em; border-top: 1px solid #000; padding-top: 6px; }
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
        sheets.append(f'<section class="sheet"><div class="mast"><div class="k">SCAD × Simulation for Robotics</div>'
                      f'<div class="t">D. Pillis · Robotics Professor Demo · Savannah College of Art &amp; Design</div></div>{body}'
                      f'<div class="foot">github.com/mrpillis/scad-robotics-simulation-demo</div></section>')
    CSSF = CSS.replace("FONTDIR", (HERE.parent / "demo" / "assets" / "fonts").as_uri())
    doc = f"<!doctype html><html><head><meta charset='utf-8'><title>SCAD Robotics Simulation Handouts</title><style>{CSSF}</style></head><body>{''.join(sheets)}</body></html>"
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
