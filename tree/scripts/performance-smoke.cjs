// Functional split-loading checks; byte budgets are enforced by the actual build checker.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
async function revealControls(page) {
  await page.locator('.tree-control-panel').waitFor();
  // Functional checks open menus explicitly; the application itself starts collapsed.
  await page.locator('.tree-control-panel > .control-section').evaluateAll(items => items.forEach(item => {item.open = true;}));
}
const root = process.env.SMOKE_URL || 'http://127.0.0.1:4173';
const KEY = 'chemistree-self-assessment-v1';
(async () => {
  const browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true, args:['--no-sandbox','--disable-dev-shm-usage']});
  try {
    const page = await browser.newPage(); page.setDefaultTimeout(8000);
    const requested = [], errors = [];
    page.on('request', request => {if (request.url().startsWith('http')) requested.push(new URL(request.url()));});
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(root + '#node=ib-2025-structure-3.2.12'); await revealControls(page);
    await page.locator('.skill-card').first().waitFor();
    assert.ok(requested.some(url => /MapView-.*\.js$/.test(url.pathname)));
    assert.ok(!requested.some(url => /PracticeSection-.*\.js$/.test(url.pathname)), 'Uncurated statements do not download practice content');
    await page.getByRole('button', {name:'Help', exact:true}).click();
    await page.getByRole('dialog').getByRole('button', {name:'Find guided exercises', exact:true}).click();
    await page.locator('.list-view button').first().waitFor();
    assert.equal(await page.getByRole('checkbox', {name:/Guided exercises/}).evaluate(el => document.activeElement === el), true);
    await page.locator('.list-view button').filter({hasText:'Structure 2.2.6'}).click();
    await page.getByRole('heading', {name:'Guided practice', exact:true}).waitFor();
    assert.ok(requested.some(url => /PracticeSection-.*\.js$/.test(url.pathname)));
    assert.equal(await page.evaluate(key => localStorage.getItem(key), KEY), null);
    assert.ok(requested.every(url => url.origin === new URL(root).origin)); assert.deepEqual(errors, []);
    await page.close();

    const failed = await browser.newPage(); failed.setDefaultTimeout(8000);
    await failed.route('**/MapView-*.js', route => route.abort());
    await failed.goto(root); await revealControls(failed);
    await failed.getByRole('button', {name:'Use list instead', exact:true}).click();
    assert.equal(await failed.locator('.list-view button').count(), 165);
    const self = failed.getByLabel('How do you feel about this statement?', {exact:true});
    await self.selectOption('developing');
    assert.equal(JSON.parse(await failed.evaluate(key => localStorage.getItem(key), KEY)).selfAssessments['ib-2025-structure-2.2.6'], 'developing');
    assert.equal(await failed.getByRole('textbox', {name:'AI instruction', exact:true}).count(), 1);
    await failed.close();
    const summary = {optionalMapAndPracticeChunks:true, uncuratedVisitSkipsPractice:true, mapFailureListFallback:true, fallbackKeepsReflection:true, externalRequests:[]};
    fs.writeFileSync('artifacts/performance-check.json', JSON.stringify(summary, null, 2)+'\n');
    console.log('Split loading and map-failure fallback passed; lists, details, reflection and prompt remain usable. No external requests.');
  } finally {await browser.close();}
})().catch(e => {console.error(e); process.exitCode=1;});
