import json, unittest, importlib.util, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class GraphContentTests(unittest.TestCase):
 def test_hierarchy_and_source_references(self):
  for profile,sections,statements in [('ib-chemistry',22,165),('ib-math-ai-sl',39,0)]:
   root=ROOT/'resources'/profile;g=json.loads((root/'syllabus-graph.json').read_text(encoding='utf-8'));refs=json.loads((root/'syllabus-cross-references.json').read_text(encoding='utf-8'));nodes={n['id']:n for n in g['nodes']}
   self.assertEqual(sum(n['kind']=='section' for n in nodes.values()),sections);self.assertEqual(sum(n['kind']=='statement' for n in nodes.values()),statements)
   for e in g['edges']:
    self.assertIn(e['source'],nodes);self.assertIn(e['target'],nodes)
    if e['kind']=='hierarchy':self.assertEqual(nodes[e['target']]['parent'],e['source'])
    else:
     source=nodes[e['source']];parent=source['parent'] if source['kind']=='statement' else source['id']
     self.assertIn(e['target'],{r['target'] for r in refs['sections'][parent]})
   for n in nodes.values():
    if not n['href'].startswith('http'):self.assertTrue((root/n['href'].split('#')[0]).is_file())
  g=json.loads((ROOT/'resources/ib-chemistry/syllabus-graph.json').read_text(encoding='utf-8'))
  self.assertEqual({e['target'] for e in g['edges'] if e['source']=='S1.1.1' and e['kind']=='reference'},{'S2.2','S2.3'})

@unittest.skipUnless(importlib.util.find_spec('playwright'),'Requires Playwright')
class GraphBrowserTests(unittest.TestCase):
 def test_both_graphs_offline(self):
  from playwright.sync_api import sync_playwright
  with sync_playwright() as p:
   browser=p.chromium.launch(channel='msedge' if os.name=='nt' else 'chromium');page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for profile,code in [('ib-chemistry','S1.1.1'),('ib-math-ai-sl','1.3')]:
    page.goto((ROOT/'resources'/profile/'syllabus-graph.html').as_uri());self.assertGreater(page.locator('svg circle').count(),39)
    page.get_by_label('Find a code or topic').fill(code);page.get_by_label('Choose a part').select_option(code)
    self.assertEqual(page.locator('#graph-inspector h2').inner_text(),code);self.assertGreater(page.locator('.edge.active').count(),0)
    page.get_by_label('Selected connections only').check();self.assertLess(page.locator('svg circle').count(),30)
    page.get_by_role('button',name='Zoom in',exact=True).click();page.get_by_role('button',name='Fit graph',exact=True).click()
    page.set_viewport_size({'width':390,'height':850});self.assertTrue(page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    page.get_by_role('button',name='Clear selection',exact=True).click();page.set_viewport_size({'width':1440,'height':1000})
    if profile=='ib-chemistry':
     page.get_by_label('Show individual statements').uncheck();self.assertEqual(page.locator('[data-node="S1.1.1"]').count(),0)
     page.get_by_role('button',name='Fit graph',exact=True).click()
   self.assertEqual(errors,[]);browser.close()
