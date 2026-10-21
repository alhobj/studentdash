"""Build ten offline design options from the same fictional student view."""
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
THEMES.update({
    '06-signal': ('Signal', 'Bold ink outlines, electric yellow and offset cards: a confident poster-like dashboard.', """
    :root{--ink:#20221b;--muted:#515448;--teal:#3e591c;--bg:#f6f6ec;--line:#34382a;--paper:#fffef8}
    body{background-image:radial-gradient(#c7cbb7 .8px,transparent .8px);background-size:18px 18px}
    .topline{border-bottom:3px solid var(--ink);padding-bottom:18px;text-transform:uppercase;letter-spacing:.08em}
    .hero{position:relative;overflow:hidden;background:#e4f769;color:var(--ink);border:3px solid var(--ink);border-radius:0;box-shadow:10px 10px 0 #20221b;margin-bottom:40px}
    .hero h1{font-weight:900;letter-spacing:-.06em;max-width:780px}.hero .eyebrow,.hero .muted{color:#35431c}
    .hero:after{content:'';position:absolute;right:30px;top:30px;width:100px;height:100px;border:16px solid #20221b;border-radius:50%;opacity:.12;pointer-events:none}
    .card{border:2px solid #34382a;border-radius:0;box-shadow:5px 5px 0 #d5d9c5}.stat{border:2px solid #34382a;border-radius:0;background:#fffef8}.stat:first-child{background:#e4f769}
    .stat strong{font-size:2.8rem;font-weight:900}.tag{background:#20221b;color:#e4f769;border-radius:0}
    button{background:#20221b;border-radius:0}.notice{background:#fffef8;border:2px solid #34382a;border-left:10px solid #34382a;border-radius:0}
    h2{font-weight:850}.section>.eyebrow{display:inline-block;background:#20221b;color:#e4f769;padding:4px 10px}
    @media(max-width:700px){.hero{box-shadow:6px 6px 0 #20221b}.hero:after{display:none}.stat strong{font-size:2rem}}
    """),
    '07-observatory': ('Observatory', 'An atmospheric midnight-blue journal with orbital lines and luminous cyan details.', """
    :root{color-scheme:dark;--ink:#eaf5ff;--muted:#b7c9dc;--teal:#8ee8ea;--bg:#091a2c;--line:#36536e;--paper:#122c43}
    body{background-image:radial-gradient(circle at 80% 0,#183c58 0,transparent 45%),radial-gradient(#456179 .6px,transparent .6px);background-size:auto,28px 28px}
    main{max-width:1160px}.topline{font-family:Consolas,monospace;letter-spacing:.04em}.tag{background:#193d52;color:#b0f4ed;border:1px solid #517c8c}
    .hero{position:relative;isolation:isolate;overflow:hidden;background:#102a43;border:1px solid #50758e;border-radius:32px 32px 100px 32px;min-height:360px}
    .hero:before,.hero:after{content:'';position:absolute;z-index:-1;width:360px;height:360px;border:1px solid #48798c;border-radius:50%;right:-90px;top:-150px;pointer-events:none}
    .hero:after{width:480px;height:480px;right:-150px;top:-210px}.hero h1{font-family:Georgia,serif;font-weight:400;letter-spacing:-.03em}.hero .eyebrow,.hero .muted{color:#c4edf0}
    .card{background:linear-gradient(135deg,#17324a,#12293e);border-radius:18px}.stat{background:#10283c;border-top:3px solid #8ee8ea}.stat strong{color:#a4efef;font-family:Consolas,monospace}
    .notice{background:#263c4c;border-color:#92cfd6}.empty,.hint{background:#203d54;color:#d1e3f2}button{background:#a4efef;color:#10283c}
    select{background:#10283c;color:#eaf5ff;border-color:#7290a7}progress,progress::-webkit-progress-bar{background:#355570}:focus-visible{outline-color:#f5cc8c}
    .section>.eyebrow{padding-left:16px;border-left:3px solid #8ee8ea}
    @media(max-width:700px){.hero{border-bottom-right-radius:56px;min-height:0}}
    """),
    '08-fieldnotes': ('Fieldnotes', 'A cream-paper science notebook with ruled margins, green tabs and editorial type.', """
    :root{--ink:#293c32;--muted:#566a5b;--teal:#356242;--bg:#edece0;--line:#ccd4c1;--paper:#fffef3}
    body{background-image:repeating-linear-gradient(0deg,transparent,transparent 31px,#d9dece 32px)}
    main{max-width:1040px;border-left:1px solid #c1caba;border-right:1px solid #c1caba;background:#f8f8edf0}
    .topline{font-family:Consolas,monospace;border-bottom:1px dashed #8b9b82;padding-bottom:18px}
    .hero{background:#e2e8d7;color:var(--ink);border-radius:4px;padding-left:56px;border-left:10px solid #416348;position:relative}
    .hero h1{font-family:Georgia,serif;font-weight:400}.hero .eyebrow,.hero .muted{color:#3d5944}
    .hero:after{content:'';position:absolute;right:24px;top:22px;width:70px;height:24px;background:#e8ce8caa;transform:rotate(8deg);pointer-events:none}
    .card{border-radius:3px;border:1px solid #ccd4c1;box-shadow:3px 5px 0 #d6dbc955;padding-left:36px;border-left:4px solid #a4b199}
    h2,h3{font-family:Georgia,serif}.stat{background:#fffef3;border-radius:3px;border-bottom:4px solid #82976e}.stat strong{font-family:Georgia,serif;font-weight:400;font-size:2.7rem}
    .tag{border-radius:3px;background:#416348;color:white}.notice{background:#f3ebd2;border-color:#8d743f}.question{border-bottom-style:dashed;padding:20px 0}.section>.eyebrow{font-family:Consolas,monospace}
    @media(max-width:700px){.hero{padding-left:24px}.hero:after{display:none}.card{padding-left:24px}.stat strong{font-size:2rem}}
    """),
    '09-bauhaus': ('Bauhaus', 'Cobalt, coral and geometric shapes paired with crisp square cards and oversized numbers.', """
    :root{--ink:#162441;--muted:#526078;--teal:#244bab;--bg:#f7f3ed;--line:#ccd2dd;--paper:#ffffff}
    main{max-width:1240px}.topline{font-weight:800;text-transform:uppercase;border-bottom:6px solid #1a3e92;padding-bottom:16px}
    .hero{background:#214baf;border-radius:0;color:white;position:relative;overflow:hidden;isolation:isolate;padding-right:180px}
    .hero:before{content:'';position:absolute;z-index:-1;width:240px;height:240px;background:#f48468;border-radius:50%;right:-110px;top:40px;pointer-events:none}
    .hero:after{content:'';position:absolute;z-index:-1;width:96px;height:96px;background:#f3cf64;right:45px;bottom:-50px;transform:rotate(45deg);pointer-events:none}
    .hero h1{font-weight:850;letter-spacing:-.055em}.hero .eyebrow,.hero .muted{color:#e5efff}
    .card{border-radius:0;border-top:5px solid #214baf;box-shadow:none}.stat{border:0;border-radius:0;border-bottom:6px solid #214baf}.stat:nth-child(2){border-color:#bc523b}.stat:nth-child(3){border-color:#a67a16}
    .stat strong{font-size:3.2rem;font-weight:850}.tag{background:#f6d368;color:#263251;border-radius:0}.notice{background:#fff7df;border-radius:0;border-color:#a67a16}
    .section>h2{font-size:1.8rem}button{border-radius:0}.question{padding:18px 0}
    @media(max-width:700px){.hero{padding-right:24px}.hero:before,.hero:after{opacity:.12}.stat strong{font-size:2rem}}
    """),
    '10-tidal': ('Tidal', 'A soft ocean-green canvas with sculpted corners, a spacious reading rhythm and sand accents.', """
    :root{--ink:#173f43;--muted:#4f6d70;--teal:#21676b;--bg:#edf5f2;--line:#c8ded7;--paper:#ffffff}
    body{background:radial-gradient(ellipse at 0 0,#c9e6df,transparent 60%),#edf5f2}
    main{max-width:1100px}.topline{padding:12px 18px;border:1px solid #bdd8d0;border-radius:999px;background:#ffffffa0}
    .hero{background:#174e54;border-radius:64px 16px 64px 16px;position:relative;overflow:hidden;isolation:isolate;padding:52px}
    .hero:after{content:'';position:absolute;z-index:-1;right:-70px;bottom:-100px;width:350px;height:220px;border:28px solid #36777b;border-radius:50%;transform:rotate(-20deg);pointer-events:none}
    .hero h1{font-family:Georgia,serif;font-weight:400;font-size:clamp(2.5rem,5vw,4.5rem)}.hero .eyebrow,.hero .muted{color:#d2efeb}
    .card{border-radius:28px 8px 28px 8px;box-shadow:0 12px 28px #1c5f4806;padding:32px}.stat{border-radius:24px;background:#e0efea;border:0}.stat:nth-child(2){background:#eee9db}.stat:nth-child(3){background:#dcecf0}
    .stat strong{font-family:Georgia,serif;font-size:2.8rem;font-weight:400}.tag{background:#d1e8e1;color:#235a52}.notice{background:#f6efdf;border-color:#967339;border-radius:16px}
    .section{margin-top:44px}.question{padding:22px 0}.section>.eyebrow{letter-spacing:.2em}
    @media(max-width:700px){.topline{border-radius:20px}.hero{padding:28px;border-radius:36px 8px 36px 8px}.card{padding:24px}.stat strong{font-size:2rem}}
    """),
})
PRINT = """@media print{body{background:white;color:#172e3a}main{margin:0!important;padding:0!important;max-width:none;background:white!important;border:0!important}.topline{position:static!important;width:auto!important;background:white!important;color:#172e3a!important;padding:0!important;display:flex!important}.hero,.card,.stat,.notice,.empty{background:white!important;color:#172e3a!important;box-shadow:none!important}.hero:before,.hero:after{display:none}.hero .muted,.hero .eyebrow,.muted,.stat span,.stat strong,.question small,th,.footer{color:#374957!important}.assessment-view{display:block!important}.assessment-view[hidden]{display:none!important}}"""


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
        links.append(f'<a class="option option-{slug}" href="{slug}/student1001.html"><h2>{name}</h2><p>{description}</p><span>Open design →</span></a>')
    (destination / 'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Studentdash · Ten design options</title><style>body{margin:0;background:#f3f5f9;color:#202c40;font:17px/1.6 system-ui}main{max-width:1000px;margin:auto;padding:48px 24px}h1{font-size:clamp(2rem,5vw,3.5rem);line-height:1.1;letter-spacing:-.04em}h2{margin:0}p{color:#52617a}.options{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px}.option{display:block;background:white;color:inherit;padding:28px;border:1px solid #d8e0ec;border-radius:18px;text-decoration:none}.option:hover{border-color:#315fc3}.option:focus-visible{outline:3px solid #315fc3;outline-offset:4px}.option span{color:#2455bf;font-weight:650}.option{border-top:8px solid #3468ce}.option-02-editorial{border-color:#a85c38}.option-03-campus{border-color:#163e32}.option-04-night{border-color:#293b55}.option-05-focus{border-color:#7953b6}.option-06-signal{border-color:#bbd438;background:#fcffe9}.option-07-observatory{border-color:#31788a;background:#effaff}.option-08-fieldnotes{border-color:#82976e;background:#fffef3}.option-09-bauhaus{border-color:#f48468;background:#f2f5ff}.option-10-tidal{border-color:#36777b;background:#effaf5}</style><main><p>STUDENTDASH / DESIGN REVIEW</p><h1>One learning story.<br>Ten ways to see it.</h1><p>Each design contains exactly the same fictional student 1001 results, feedback and controls. Open a design, try the assessment selector and expand the question categories. Resize the window to compare phone layouts. These are standalone offline previews.</p><div class="options">''' + ''.join(links) + '</div></main></html>', encoding='utf-8')
    print(f'Created ten identical-content previews: {destination / "index.html"}')


if __name__ == '__main__':
    main()
