"""Skill coverage, links, visible labels and portable self-reviewed drafts."""
import json,importlib.util,os,unittest
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
 def __init__(self,text):super().__init__();self.ids=set();self.links=[];self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.add(a['id'])
  if tag=='a' and 'href' in a:self.links.append(a['href'])

class SkillContentTests(unittest.TestCase):
 def test_complete_inventory_links_and_question_labels(self):
  for profile,new_count in [('ib-chemistry',103),('ib-math-ai-sl',64)]:
   root=ROOT/'resources'/profile;data=json.loads((root/'skills.json').read_text(encoding='utf-8'));coverage=json.loads((root/'skill-coverage.json').read_text(encoding='utf-8'))
   known={s['id'] for s in data['skills']};self.assertEqual(coverage['uncovered'],[]);self.assertEqual(set(coverage['coverage']),known);self.assertEqual(len(data['questions']),new_count)
   for key,rows in coverage['coverage'].items():self.assertTrue(rows,key)
   index=Links((root/'skills.html').read_text(encoding='utf-8'));self.assertTrue(known<=index.ids)
   pages={}
   for page in ['skills.html','skills-practice.html']:
    parsed=Links((root/page).read_text(encoding='utf-8'))
    for href in parsed.links:
     if href.startswith('http'):continue
     filename,_,anchor=href.partition('#');filename=filename or page
     self.assertTrue((root/filename).is_file(),href)
     if anchor:
      if filename not in pages:pages[filename]=Links((root/filename).read_text(encoding='utf-8')).ids
      self.assertIn(anchor,pages[filename],href)
   catalog=json.loads((root/'authored-mcq.json').read_text(encoding='utf-8'))
   for q in catalog:
    for key in q['skills']:
     self.assertIn(key,known)
     page,anchor=q['path'].split('#');html=(root/page).read_text(encoding='utf-8');card=html.split('id="'+anchor+'"',1)[1].split('</article>',1)[0]
     self.assertIn('skills.html#'+key,card)

@unittest.skipUnless(importlib.util.find_spec('playwright'),'Requires Playwright')
class SkillBrowserTests(unittest.TestCase):
 def test_index_notes_and_labels(self):
  from playwright.sync_api import sync_playwright
  with sync_playwright() as p:
   browser=p.chromium.launch(channel='msedge' if os.name=='nt' else 'chromium');page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for profile,example in [('ib-chemistry','s1-4.html'),('ib-math-ai-sl','mcq-1-2.html')]:
    root=ROOT/'resources'/profile
    page.goto((root/'skills.html').as_uri());page.get_by_label('Find a skill').fill('Arithmetic')
    self.assertGreater(page.locator('.skill-index-card:visible').count(),0)
    page.locator('.skill-index-card:visible').first.get_by_text('All questions and guidance for this skill →',exact=True).click()
    page.wait_for_url('**/skills-practice.html#*')
    card=page.locator('[data-skill-question]').first;card.locator('textarea').fill('Fictional practice notes')
    card.locator('input[type=checkbox]').check();page.reload();self.assertEqual(card.locator('textarea').input_value(),'Fictional practice notes');self.assertTrue(card.locator('input').is_checked())
    with page.expect_download() as download:page.get_by_role('button',name='Export my skills notes').click()
    raw=json.loads(Path(download.value.path()).read_text());self.assertEqual(raw['profile'],profile)
    page.get_by_label('Import skills notes').set_input_files({'name':'invalid.json','mimeType':'application/json','buffer':json.dumps({**raw,'profile':'other'}).encode()})
    page.wait_for_function("document.querySelector('#skill-status').textContent.startsWith('Import rejected')")
    page.get_by_label('Import skills notes').set_input_files({'name':'valid.json','mimeType':'application/json','buffer':json.dumps(raw).encode()})
    page.wait_for_function("document.querySelector('#skill-status').textContent.startsWith('Skills notes merged')")
    page.set_viewport_size({'width':390,'height':850});self.assertTrue(page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    page.goto((root/example).as_uri());self.assertGreater(page.locator('.authored-mcq-card .question-skills').count(),0)
    page.goto((root/'prior-learning.html').as_uri());self.assertGreater(page.locator('.foundation-step .question-skills').count(),0)
    similar=page.locator('[data-similar]').first;self.assertEqual(similar.locator('form .question-skills').count(),1)
    similar.get_by_role('button',name='Another like this',exact=True).click();self.assertEqual(similar.locator('form .question-skills').count(),1)
   self.assertEqual(errors,[]);browser.close()
