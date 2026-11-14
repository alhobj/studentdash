// Student-release UI checks against a local production preview (npm run preview).
// Playwright is a validation tool, not an application/runtime dependency.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const map = require('../src/data/map.json');
async function revealControls(page) {
  await page.locator('.tree-control-panel').waitFor();
  // Functional checks open menus explicitly; the application itself starts collapsed.
  await page.locator('.tree-control-panel > .control-section').evaluateAll(items => items.forEach(item => {item.open = true;}));
}
const root = process.env.SMOKE_URL || 'http://127.0.0.1:4173';
const baseOrigin = new URL(root).origin;
const KEY = 'chemistree-self-assessment-v1';
const A = 'ib-2025-structure-2.2.6';
const B = 'ib-2025-structure-1.1.1';
const C = 'ib-2025-structure-1.2.1';
const envelope = entries => ({schemaVersion: '1.0', mapVersion: '2.0', selfAssessments: entries});
const requests = new Map();
const errors = [];

function track(context) {
  context.on('request', request => {
    const url = new URL(request.url());
    if (!/^https?:$/.test(url.protocol)) return;
    // Deliberately retain only destination origin/path, never query or fragment values.
    requests.set(`${url.origin}${url.pathname}`, {origin: url.origin, path: url.pathname, method: request.method()});
  });
  context.on('page', page => {page.setDefaultTimeout(8000); page.on('pageerror', error => errors.push(error.message));});
}
async function ready(page, fragment = '') {
  await page.goto(root + fragment); await revealControls(page);
  await page.locator('.skill-card').first().waitFor();
  await page.waitForTimeout(400);
}
async function entries(page) {
  return page.evaluate(key => {const text = localStorage.getItem(key); return text ? JSON.parse(text).selfAssessments : {};}, KEY);
}
async function rawProgress(page) {return page.evaluate(key => localStorage.getItem(key), KEY);}
const selfControl = page => page.getByLabel('How do you feel about this statement?', {exact: true});
async function openImport(page, value) {
  await page.getByRole('button', {name: 'Import self-assessment', exact: true}).click();
  await page.getByRole('dialog').waitFor();
  if (value !== undefined) await chooseFile(page, value);
}
async function chooseFile(page, value) {
  const buffer = Buffer.isBuffer(value) ? value : Buffer.from(typeof value === 'string' ? value : JSON.stringify(value));
  await page.getByLabel('Choose self-assessment JSON', {exact: true}).setInputFiles({name: 'chemistree-self-assessment.json', mimeType: 'application/json', buffer});
}
async function download(page) {
  const pending = page.waitForEvent('download');
  await page.getByRole('button', {name: 'Export self-assessment', exact: true}).click();
  const file = await pending;
  assert.equal(file.suggestedFilename(), 'chemistree-self-assessment.json');
  return JSON.parse(fs.readFileSync(await file.path(), 'utf8'));
}
async function acceptDialog(page, buttonName, accept) {
  page.once('dialog', dialog => accept ? dialog.accept() : dialog.dismiss());
  await page.getByRole('button', {name: buttonName, exact: true}).click();
}
async function assertGeometry(page) {
  const boxes = await page.evaluate(() => {
    const transform = new DOMMatrix(getComputedStyle(document.querySelector('.react-flow__viewport')).transform);
    return [...document.querySelectorAll('.react-flow__node')].map(el => {
      const r = el.getBoundingClientRect();
      const source = el.querySelector('.react-flow__handle.source')?.getBoundingClientRect();
      const target = el.querySelector('.react-flow__handle.target')?.getBoundingClientRect();
      return {id: el.getAttribute('data-id'), x: r.x, y: r.y, right: r.right, bottom: r.bottom, width: r.width / transform.a, height: r.height / transform.a,
        source: source && {x: source.x + source.width / 2, y: source.y + source.height / 2},
        target: target && {x: target.x + target.width / 2, y: target.y + target.height / 2}};
    });
  });
  for (const box of boxes.filter(box => !box.id.startsWith('group-'))) {
    assert.ok(Math.abs(box.width - 264) < .1); assert.ok(Math.abs(box.height - 172) < .1);
    const centerX = (box.x + box.right) / 2;
    assert.ok(Math.abs(box.source.x - centerX) < 1 && Math.abs(box.source.y - box.bottom) < 1, `${box.id} must route out of its bottom`);
    assert.ok(Math.abs(box.target.x - centerX) < 1 && Math.abs(box.target.y - box.y) < 1, `${box.id} must receive routes at its top`);
  }
  for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
    const a = boxes[i], b = boxes[j];
    assert.ok(a.right <= b.x + .1 || b.right <= a.x + .1 || a.bottom <= b.y + .1 || b.bottom <= a.y + .1, `${a.id} overlaps ${b.id}`);
  }
}

(async () => {
  fs.mkdirSync('artifacts', {recursive: true});
  const browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage']});
  try {
    const context = await browser.newContext({viewport: {width: 1440, height: 1000}, acceptDownloads: true}); track(context);
    await context.addInitScript(() => {
      if (!/^https?:$/.test(location.protocol)) return;
      if (!localStorage.getItem('chemistree-v2')) localStorage.setItem('chemistree-v2', '{"legacyTestOnly":true}');
    });
    const page = await context.newPage();
    await ready(page);
    assert.equal(await page.locator('.skill-card').count(), 165);
    assert.equal(await page.getByLabel('Connections', {exact: true}).inputValue(), 'selected');
    assert.ok(await page.locator('.react-flow__edge').count() > 0);
    assert.ok(await page.locator('.react-flow__edge').count() < map.edges.length);
    assert.equal(await rawProgress(page), null, 'First launch must not create identity or progress records');
    assert.equal(await page.evaluate(() => localStorage.getItem('chemistree-v2')), '{"legacyTestOnly":true}', 'Old assessment storage remains unread/unmodified');
    assert.equal(await selfControl(page).inputValue(), 'not-reviewed');
    assert.deepEqual(await selfControl(page).locator('option').allTextContents(), ['Not reviewed', 'Needs practice', 'Developing', 'Confident']);
    for (const forbidden of ['Grow your chemistry.', 'Demo learner', 'Import one learner', 'Teacher judgment', 'Assessment evidence']) assert.equal(await page.getByText(forbidden, {exact: true}).count(), 0);
    assert.equal(await page.getByLabel('Demo learner', {exact: true}).count(), 0);
    await page.screenshot({path: 'artifacts/student-release-desktop.png', fullPage: true});

    await selfControl(page).selectOption('needs-practice');
    assert.deepEqual(await entries(page), {[A]: 'needs-practice'});
    await page.reload(); await revealControls(page); await page.locator('.skill-card').first().waitFor();
    assert.equal(await selfControl(page).inputValue(), 'needs-practice');
    await page.getByRole('button', {name: 'Reset this node', exact: true}).click();
    assert.deepEqual(await entries(page), {});
    await selfControl(page).selectOption('confident');
    const firstExport = await download(page);
    assert.deepEqual(firstExport, envelope({[A]: 'confident'}));
    const oldPrompt = await page.getByLabel('AI instruction', {exact: true}).inputValue();
    await selfControl(page).selectOption('developing');
    assert.equal(await page.getByLabel('AI instruction', {exact: true}).inputValue(), oldPrompt, 'Progress must not affect generated prompt');
    await page.getByLabel('Practice level', {exact: true}).selectOption('HL');
    assert.match(await page.getByLabel('AI instruction', {exact: true}).inputValue(), /at HL level/);
    await context.grantPermissions(['clipboard-read', 'clipboard-write'], {origin: baseOrigin});
    const visiblePrompt = await page.getByLabel('AI instruction', {exact: true}).inputValue();
    await page.getByRole('button', {name: 'Copy AI instruction', exact: false}).click();
    await page.getByRole('button', {name: 'Copied', exact: false}).waitFor();
    assert.equal(await page.evaluate(() => navigator.clipboard.readText()), visiblePrompt);
    assert.equal(context.pages().length, 1, 'Copy must not open an AI service');
    await selfControl(page).selectOption('confident');
    console.log('Clean launch, local-only persistence, reset, generic export and content-only AI prompt copying passed.');

    const incoming = envelope({[A]: 'needs-practice', [B]: 'developing'});
    await openImport(page, incoming);
    await page.getByRole('heading', {name: '2 self-assessment entries', exact: true}).waitFor();
    assert.equal(await page.getByRole('dialog').getByRole('checkbox').count(), 1);
    assert.equal(await page.getByRole('dialog').getByRole('checkbox').isChecked(), false);
    await page.screenshot({path: 'artifacts/student-release-import.png'});
    const beforeCancel = await rawProgress(page);
    await page.getByRole('button', {name: 'Cancel import', exact: true}).click();
    assert.equal(await rawProgress(page), beforeCancel);
    await openImport(page, incoming);
    await page.getByRole('button', {name: 'Apply merge', exact: true}).click();
    assert.deepEqual(await entries(page), {[A]: 'confident', [B]: 'developing'}, 'Unaccepted conflict preserved');
    await openImport(page, incoming);
    await page.getByRole('dialog').getByRole('checkbox').check();
    await page.getByRole('button', {name: 'Apply merge', exact: true}).click();
    assert.deepEqual(await entries(page), {[A]: 'needs-practice', [B]: 'developing'}, 'Accepted conflict replaced');
    await openImport(page, envelope({[C]: 'confident'}));
    await page.getByRole('radio', {name: 'Replace all current progress', exact: true}).check();
    const beforeReplace = await rawProgress(page);
    await acceptDialog(page, 'Replace progress', false);
    assert.equal(await rawProgress(page), beforeReplace);
    assert.equal(await page.getByRole('dialog').isVisible(), true);
    await acceptDialog(page, 'Replace progress', true);
    assert.deepEqual(await entries(page), {[C]: 'confident'});
    await openImport(page);
    await page.keyboard.press('Escape');
    assert.equal(await page.getByRole('dialog').count(), 0);
    await page.waitForFunction(() => document.activeElement?.textContent === 'Import self-assessment');
    assert.deepEqual(await entries(page), {[C]: 'confident'});
    // Re-import the actual browser download as a replacement round trip.
    await openImport(page, firstExport);
    await page.getByRole('radio', {name: 'Replace all current progress', exact: true}).check();
    await acceptDialog(page, 'Replace progress', true);
    assert.deepEqual(await entries(page), firstExport.selfAssessments);

    await openImport(page);
    const unchanged = await rawProgress(page);
    for (const invalid of [
      '{bad-json', envelope({'unknown-node': 'confident'}), envelope({[A]: 'secure'}),
      {...envelope({}), schemaVersion: '99'}, {...envelope({}), mapVersion: '1.0'},
      {...envelope({}), student: {id: 'not-accepted'}}, {...envelope({}), scores: [3]},
      {...envelope({}), teacherComments: 'not-accepted'}, {...envelope({}), students: []},
      Buffer.alloc(128 * 1024 + 1, ' '),
    ]) {
      await chooseFile(page, invalid);
      await page.getByRole('alert').filter({hasText: 'Import rejected.'}).waitFor();
      assert.equal(await rawProgress(page), unchanged);
      assert.equal(await page.getByRole('button', {name: 'Apply merge', exact: true}).count(), 0);
    }
    await page.getByRole('button', {name: 'Cancel import', exact: true}).click();
    await acceptDialog(page, 'Clear all local progress', false);
    assert.equal(await rawProgress(page), unchanged);
    await acceptDialog(page, 'Clear all local progress', true);
    assert.equal(await rawProgress(page), null);
    assert.equal(await selfControl(page).inputValue(), 'not-reviewed');
    console.log('Manual transfer preview, selective merge, replacement, cancellation, invalid files and clear confirmation passed.');

    await ready(page, `?fictional_tracking=example#node=${C}`);
    const curriculumHref = await page.getByRole('link', {name: 'Link to this statement', exact: true}).getAttribute('href');
    assert.equal(curriculumHref, new URL(root).pathname + `#node=${C}`);
    assert.ok(!curriculumHref.includes('?'));
    await page.getByRole('link', {name: 'Link to this statement', exact: true}).click();
    assert.equal(new URL(page.url()).search, '');
    await page.waitForFunction(id => document.querySelector('.skill-card.active')?.getAttribute('aria-label')?.includes('Structure 1.2.1'), C);
    assert.equal(await page.locator('.official-statement > b').innerText(), 'Structure 1.2.1');
    await selfControl(page).selectOption('developing');
    const linkProgress = await rawProgress(page);
    await page.reload(); await revealControls(page); await page.locator('.skill-card.active').waitFor();
    assert.equal(await page.locator('.official-statement > b').innerText(), 'Structure 1.2.1');
    assert.equal(await rawProgress(page), linkProgress);
    await page.getByRole('button', {name: 'List', exact: true}).click();
    await page.getByLabel('Level filter', {exact: true}).selectOption('HL-only');
    assert.equal(await page.locator('.list-view button').count(), 61);
    await page.evaluate(id => {location.hash = `node=${id}`;}, A);
    await page.waitForFunction(() => document.querySelector('.official-statement > b')?.textContent === 'Structure 2.2.6');
    assert.equal(await page.getByLabel('Level filter', {exact: true}).inputValue(), 'all');
    assert.equal(await page.locator('.list-view button.chosen').count(), 1);
    assert.equal(await rawProgress(page), linkProgress);
    await page.getByRole('textbox', {name: 'Search nodes', exact: true}).fill('Structure 2.2.6');
    assert.equal(await page.locator('.list-view button').count(), 1);
    await page.locator('.list-view button').focus(); await page.keyboard.press('Enter');
    assert.equal(new URL(page.url()).hash, `#node=${A}`);
    await page.getByRole('textbox', {name: 'Search nodes', exact: true}).fill('');
    await page.getByLabel('Level filter', {exact: true}).selectOption('SL');
    assert.equal(await page.locator('.list-view button').count(), 104);
    await page.getByLabel('Subject area', {exact: true}).selectOption('1');
    assert.equal(await page.locator('.list-view button').count(), map.nodes.filter(n => n.group === 1 && n.level === 'shared').length);
    await page.getByLabel('Subject area', {exact: true}).selectOption('all');
    await page.getByLabel('Level filter', {exact: true}).selectOption('all');
    await page.getByRole('textbox', {name: 'Search nodes', exact: true}).fill('a-search-with-no-matching-statement');
    assert.equal(await page.locator('.list-view button').count(), 0);
    await page.getByRole('status').filter({hasText: 'No matching statements.'}).waitFor();
    await page.evaluate(() => {location.hash = 'node=does-not-exist';});
    await page.getByRole('status').filter({hasText: 'curriculum node was not found'}).waitFor();
    assert.equal(await rawProgress(page), linkProgress);
    await page.reload(); await revealControls(page); await page.locator('.skill-card').first().waitFor();
    await page.getByRole('status').filter({hasText: 'curriculum node was not found'}).waitFor();
    await page.evaluate(id => {location.hash = `node=${id}&score=should-not-be-accepted`;}, A);
    await page.getByRole('status').filter({hasText: 'curriculum link is invalid'}).waitFor();
    assert.equal(await page.getByText('should-not-be-accepted', {exact: false}).count(), 0);
    await page.evaluate(id => {location.hash = `node=${id}`;}, A);
    await page.waitForFunction(() => document.querySelector('.official-statement > b')?.textContent === 'Structure 2.2.6');
    await page.getByRole('button', {name: 'Expand full prerequisite chain', exact: true}).click();
    assert.ok(await page.getByRole('button', {name: /Structure 1.3.5/}).count() > 0);
    await page.getByRole('button', {name: 'Show direct prerequisites', exact: true}).click();
    const viewport = page.locator('.react-flow__viewport');
    await page.waitForTimeout(400);
    const beforeZoom = await viewport.getAttribute('style');
    await page.getByRole('button', {name: /zoom in/i}).click(); await page.waitForTimeout(350);
    assert.notEqual(await viewport.getAttribute('style'), beforeZoom);
    const beforePan = await viewport.getAttribute('style');
    const canvas = await page.locator('.canvas').boundingBox();
    await page.mouse.move(canvas.x + 350, canvas.y + 40); await page.mouse.down(); await page.mouse.move(canvas.x + 430, canvas.y + 90, {steps: 8}); await page.mouse.up();
    assert.notEqual(await viewport.getAttribute('style'), beforePan);
    await page.getByLabel('Connections', {exact: true}).selectOption('all');
    assert.equal(await page.locator('.react-flow__edge').count(), map.edges.length);
    await assertGeometry(page);
    await page.getByRole('button', {name: /Fit map/}).click(); await page.waitForTimeout(400);
    await assertGeometry(page);
    await page.getByLabel('Connections', {exact: true}).selectOption('selected');
    console.log('Deep links, direct visits/reloads, invalid IDs, list keyboard activation, filters, chains, zoom/pan/fit and measured geometry passed.');

    const mobile = await context.newPage(); await mobile.setViewportSize({width: 390, height: 844});
    await ready(mobile, `#node=${A}`);
    assert.equal(await mobile.locator('.official-statement > b').innerText(), 'Structure 2.2.6');
    await mobile.waitForFunction(() => document.activeElement?.id === 'node-details');
    assert.equal(await mobile.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await mobile.screenshot({path: 'artifacts/student-release-mobile-details.png'});
    await mobile.getByRole('button', {name: 'List', exact: true}).click();
    await mobile.getByRole('textbox', {name: 'Search nodes', exact: true}).fill('Structure 1.1.1');
    await mobile.locator('.list-view button').focus(); await mobile.keyboard.press('Enter');
    await mobile.waitForFunction(() => document.querySelector('.official-statement > b')?.textContent === 'Structure 1.1.1');
    assert.equal(await mobile.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await mobile.getByRole('button', {name: 'Map', exact: true}).click();
    await mobile.getByRole('textbox', {name: 'Search nodes', exact: true}).fill('');
    await mobile.evaluate(() => scrollTo(0, 0)); await mobile.waitForTimeout(450);
    await mobile.screenshot({path: 'artifacts/student-release-mobile.png', fullPage: true});
    await openImport(mobile, envelope({[B]: 'needs-practice'}));
    await mobile.getByRole('heading', {name: '1 self-assessment entries', exact: true}).waitFor();
    assert.equal(await mobile.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await mobile.keyboard.press('Escape');
    await context.close();

    // Separate contexts prove storage errors do not remove session usability/export.
    for (const failure of ['read', 'quota', 'remove']) {
      const broken = await browser.newContext({viewport: {width: 1280, height: 900}, acceptDownloads: true}); track(broken);
      await broken.addInitScript(({failure, key, value}) => {
        if (!/^https?:$/.test(location.protocol)) return;
        if (failure === 'read') Object.defineProperty(window, 'localStorage', {configurable: true, get() {throw new DOMException('blocked', 'SecurityError');}});
        else if (failure === 'quota') Storage.prototype.setItem = function () {throw new DOMException('full', 'QuotaExceededError');};
        else {localStorage.setItem(key, value); Storage.prototype.removeItem = function () {throw new DOMException('blocked', 'SecurityError');};}
      }, {failure, key: KEY, value: JSON.stringify(envelope({[A]: 'confident'}))});
      const blocked = await broken.newPage(); await ready(blocked);
      if (failure === 'read') await blocked.getByRole('alert').filter({hasText: 'could not be read'}).waitFor();
      if (failure !== 'remove') {
        await selfControl(blocked).selectOption('needs-practice');
        await blocked.getByRole('alert').filter({hasText: 'unavailable or full'}).waitFor();
        assert.deepEqual((await download(blocked)).selfAssessments, {[A]: 'needs-practice'});
      } else {
        await acceptDialog(blocked, 'Clear all local progress', true);
        await blocked.getByRole('alert').filter({hasText: 'may return after a reload'}).waitFor();
        assert.equal(await selfControl(blocked).inputValue(), 'not-reviewed');
        assert.deepEqual(await entries(blocked), {[A]: 'confident'});
      }
      await broken.close();
    }
    const observed = [...requests.values()];
    const externalRequests = observed.filter(r => r.origin !== baseOrigin);
    assert.deepEqual(externalRequests, []);
    assert.ok(observed.every(r => r.method === 'GET'));
    assert.ok(observed.every(r => !/fixtures|examples|student-\d|assessment|api\//i.test(r.path)), 'Normal use must never request results/fixtures');
    assert.deepEqual(errors, []);
    const networkReport = {externalRequests: [], localAssetPaths: [...new Set(observed.map(r => r.path))].sort(), requestMethods: [...new Set(observed.map(r => r.method))]};
    fs.writeFileSync('artifacts/student-network.json', JSON.stringify(networkReport, null, 2) + '\n');
    console.log('Mobile direct links/list/import, unavailable/full storage and failed clearing passed.');
    console.log(`Student browser smoke passed; ${map.nodes.length} cards, ${map.edges.length} obstacle-routed connections, 0 external requests, ${networkReport.localAssetPaths.length} local asset paths, no page errors.`);
  } finally {await browser.close();}
})().catch(error => {console.error(error); process.exitCode = 1;});
