"""Build five offline design options from the same fictional student view."""
from pathlib import Path
from tempfile import TemporaryDirectory

from create_example_workbook import create_example
from studentdash.excel import read_workbook
from studentdash.render import render_student

ROOT = Path(__file__).resolve().parent
COMMON = """
html{scroll-behavior:smooth}body{font-size:16px}main{max-width:1180px}
.card,.stat{box-shadow:0 6px 24px #172e3a05}.card{padding:30px}
h2{font-size:1.4rem}h3{font-size:1.06rem}.hero{padding:48px}
.hero h1{font-size:clamp(2.6rem,5vw,4.3rem)}
summary{min-height:36px}button,select{min-height:44px}
:focus-visible{outline:3px solid #a75a00;outline-offset:4px}
@media(max-width:700px){main{padding:20px 16px}.hero,.card{padding:24px}.grid{grid-template-columns:1fr}.stats{grid-template-columns:1fr}.stat{display:flex;justify-content:space-between;gap:16px}summary .muted{float:none;display:block}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""
THEMES = {
    '01-studio': ('Studio', 'An airy blue dashboard with a wide welcome panel and balanced cards.', """
    :root{--ink:#142645;--muted:#52617a;--teal:#2455bf;--bg:#f2f5fb;--line:#dce3ef}
    .hero{background:linear-gradient(120deg,#173d8b,#3468ce);border-radius:28px}
    .hero .eyebrow,.hero .muted{color:#e0ebff}.tag{background:#e0eaff;color:#244d99}
    .stat{border-top:4px solid #3468ce}.stat strong{color:#2455bf}.card{border-radius:22px}
    """),
    '02-editorial': ('Editorial', 'A warm reading-first journal with serif headings and a narrow page.', """
    :root{--ink:#342b26;--muted:#6b5b50;--teal:#8a4226;--bg:#faf7f0;--line:#e3d9ca;--paper:#fffdf8}
    main{max-width:880px}h1,h2,h3{font-family:Georgia,serif}h1{letter-spacing:-.035em}
    .hero{background:transparent;color:var(--ink);padding:28px 0;border-radius:0;border-top:2px solid var(--ink);border-bottom:1px solid var(--line)}
    .hero .eyebrow,.hero .muted{color:var(--muted)}.card{border:0;border-top:1px solid var(--line);border-radius:0;box-shadow:none}
    .grid{grid-template-columns:1fr}.stat{border-radius:0;background:transparent;border:0;border-left:2px solid #a85c38}
    .tag{background:#eee3d3;color:#75442d}.notice{background:#f1e9da}.question{padding:20px 0}
    """),
    '03-campus': ('Campus', 'A desktop side rail with a compact green workspace; stacked on phones.', """
    :root{--ink:#193c34;--muted:#526c63;--teal:#16654b;--bg:#f0f5f1;--line:#d6e4da}
    .hero{background:#dcece1;color:var(--ink);border-radius:12px}.hero .eyebrow,.hero .muted{color:#365d4e}
    .card,.stat{border-radius:12px}.tag{background:#e0efe5;color:#18533e}
    @media(min-width:1100px){main{margin-left:250px;max-width:1180px;padding:40px}.topline{position:fixed;inset:0 auto 0 0;width:250px;padding:44px 26px;background:#163e32;color:#fff;display:flex;flex-direction:column;align-items:flex-start;justify-content:flex-start;gap:28px;margin:0}.hero{padding:32px}.hero h1{font-size:3rem}.stats{gap:12px}}
    """),
    '04-night': ('Night', 'A calm dark canvas with mint highlights and high-contrast reading surfaces.', """
    :root{color-scheme:dark;--ink:#e7edf8;--muted:#b2c0d5;--teal:#8ddbc9;--bg:#111a2b;--paper:#1c2940;--line:#3a4b65}
    .hero{background:linear-gradient(130deg,#263b59,#20394a);border:1px solid #526884}
    .hero .eyebrow,.hero .muted{color:#c6e9e4}.tag{background:#2b4a50;color:#d1f5eb}
    .notice{background:#343126;border-color:#e4b863}.empty,.hint{background:#263650;color:#c6d2e5}
    button{background:#8ddbc9;color:#122c2b}select{background:#1c2940;color:#e7edf8;border-color:#8295ad}
    progress,progress::-webkit-progress-bar{background:#41536c}.stat strong{color:#9ce2d2}
    :focus-visible{outline-color:#ffd18a}
    """),
    '05-focus': ('Focus', 'A structured violet workspace with a compact header and two-column evidence.', """
    :root{--ink:#29233f;--muted:#665c7c;--teal:#6742a4;--bg:#f6f4fb;--line:#e1dbee}
    main{max-width:1280px}.hero{background:#ece5f8;color:var(--ink);border-radius:16px;border-left:6px solid #7953b6}
    .hero .eyebrow,.hero .muted{color:#5e497d}.hero h1{font-size:2.8rem}
    .tag{background:#ece5f8;color:#59328d}.card{border-radius:12px}.stat{background:#fff;border-radius:12px}
    @media(min-width:950px){.assessment-view{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(280px,1fr);gap:24px;align-items:start}.assessment-view>.stats,.assessment-view>.section,.assessment-view>.card{grid-column:1/-1}.assessment-view>.card{margin:0}.assessment-view>.stats{margin-bottom:0}.hero{padding:28px 36px}.grid{grid-template-columns:1.4fr 1fr;gap:24px}}
    """),
}
PRINT = """@media print{body{background:white;color:#172e3a}main{margin:0!important;padding:0!important;max-width:none}.topline{position:static!important;width:auto!important;background:white!important;color:#172e3a!important;padding:0!important;display:flex!important}.hero,.card,.stat,.notice,.empty{background:white!important;color:#172e3a!important;box-shadow:none}.hero .muted,.hero .eyebrow,.muted,.stat span,.stat strong,.question small,th,.footer{color:#374957!important}.assessment-view{display:block!important}.assessment-view[hidden]{display:none!important}}"""


def main():
    destination = ROOT / 'examples' / 'layouts'
    destination.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as temporary:
        workbook = Path(temporary) / 'fictional.xlsx'
        create_example(workbook)
        base = render_student(read_workbook(workbook), '1001', include_examples=False)
    links = []
    for slug, (name, description, css) in THEMES.items():
        folder = destination / slug
        folder.mkdir(exist_ok=True)
        page = base.replace('</head>', '<style>' + COMMON + css + PRINT + '</style></head>')
        (folder / 'student1001.html').write_text(page, encoding='utf-8')
        links.append(f'<a class="option" href="{slug}/student1001.html"><h2>{name}</h2><p>{description}</p><span>Open design →</span></a>')
    (destination / 'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Studentdash · Five design options</title><style>body{margin:0;background:#f3f5f9;color:#202c40;font:17px/1.6 system-ui}main{max-width:1000px;margin:auto;padding:48px 24px}h1{font-size:clamp(2rem,5vw,3.5rem);line-height:1.1;letter-spacing:-.04em}h2{margin:0}p{color:#52617a}.options{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px}.option{display:block;background:white;color:inherit;padding:28px;border:1px solid #d8e0ec;border-radius:18px;text-decoration:none}.option:hover{border-color:#315fc3}.option:focus-visible{outline:3px solid #315fc3;outline-offset:4px}.option span{color:#2455bf;font-weight:650}</style><main><p>STUDENTDASH / DESIGN REVIEW</p><h1>One learning story.<br>Five ways to see it.</h1><p>Each design contains exactly the same fictional student 1001 results, feedback and controls. Open a design, try the assessment selector and expand the question categories. Resize the window to compare phone layouts. These are standalone offline previews.</p><div class="options">''' + ''.join(links) + '</div></main></html>', encoding='utf-8')
    print(f'Created five identical-content previews: {destination / "index.html"}')


if __name__ == '__main__':
    main()
