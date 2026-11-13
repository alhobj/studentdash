// Focused browser checks against a local production preview. This is not a full
// accessibility certification or a replacement for assistive-technology testing.
// NODE_PATH=/opt/codex/cua_node/lib/node_modules node scripts/accessibility-smoke.cjs
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const root = process.env.SMOKE_URL || 'http://127.0.0.1:4173';
const origin = new URL(root).origin;
const requests = new Set();
const errors = [];
const results = {contrast: [], viewports: [], keyboard: [], externalRequests: []};

async function listView(page) {
  const list = page.getByRole('button', {name: 'List', exact: true});
  await list.waitFor();
  if (await list.getAttribute('aria-pressed') !== 'true') await list.click();
  await page.locator('.list-view button').first().waitFor();
}

async function noHorizontalOverflow(page, label) {
  const size = await page.evaluate(() => ({viewport: innerWidth, content: document.documentElement.scrollWidth}));
  assert.ok(size.content <= size.viewport + 1, `${label}: document is ${size.content}px wide in ${size.viewport}px viewport`);
  results.viewports.push({...size, label});
}

async function contrast(page, selectors) {
  const samples = await page.evaluate(selectors => {
    const rgb = value => {
      const numbers = value.match(/[\d.]+/g)?.map(Number);
      if (!numbers || numbers.length < 3) throw new Error(`Unsupported computed colour: ${value}`);
      return [...numbers.slice(0, 3), numbers[3] ?? 1];
    };
    const blend = (top, under) => [...top.slice(0, 3).map((value, i) => value * top[3] + under[i] * (1 - top[3])), 1];
    const luminance = colour => colour.slice(0, 3).map(value => {
      const c = value / 255;
      return c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4;
    }).reduce((sum, value, i) => sum + value * [.2126, .7152, .0722][i], 0);
    return selectors.flatMap(selector => [...document.querySelectorAll(selector)].filter(el => el.getClientRects().length).map(el => {
      const layers = [];
      let opacity = 1;
      for (let node = el; node; node = node.parentElement) {
        const style = getComputedStyle(node);
        opacity *= Number(style.opacity);
        layers.unshift(rgb(style.backgroundColor));
      }
      const background = layers.reduce((under, layer) => blend(layer, under), [255, 255, 255, 1]);
      const foreground = blend(rgb(getComputedStyle(el).color), background);
      const [a, b] = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
      return {selector, text: el.textContent.trim().slice(0, 60), ratio: (a + .05) / (b + .05), opacity};
    }));
  }, selectors);
  for (const selector of selectors) assert.ok(samples.some(sample => sample.selector === selector), `Missing visible contrast sample: ${selector}`);
  for (const sample of samples) {
    assert.ok(sample.opacity >= .99, `${sample.selector} is faded; contrast calculation requires opaque text groups`);
    assert.ok(sample.ratio >= 4.5, `${sample.selector} (${sample.text}) contrast ${sample.ratio.toFixed(2)}:1 is below 4.5:1`);
  }
  results.contrast.push(...samples.map(sample => ({...sample, ratio: Number(sample.ratio.toFixed(2))})));
}

async function focusRing(page, locator) {
  await locator.focus();
  await page.keyboard.press('Tab');
  await page.keyboard.press('Shift+Tab');
  const ring = await locator.evaluate(el => {
    const style = getComputedStyle(el);
    return {focused: document.activeElement === el, style: style.outlineStyle, width: parseFloat(style.outlineWidth)};
  });
  assert.ok(ring.focused && ring.style !== 'none' && ring.width >= 3, 'Keyboard focus must remain visible');
}

async function modalKeyboard(page, buttonName, dialogName) {
  const opener = page.getByRole('button', {name: buttonName, exact: true});
  await opener.focus();
  await page.keyboard.press('Enter');
  const dialog = page.getByRole('dialog', {name: dialogName, exact: true});
  await dialog.waitFor();
  assert.equal(await dialog.evaluate(el => el.contains(document.activeElement)), true, `${dialogName} receives focus`);
  for (let i = 0; i < 7; i++) {
    await page.keyboard.press('Tab');
    const focus = await dialog.evaluate(el => ({inside: el.contains(document.activeElement), browserBoundary: document.activeElement === document.body, modal: el.matches(':modal')}));
    // Chromium may report body when Tab visits browser chrome at the native
    // dialog boundary. It must never focus an underlying app control, and the
    // next Tab must return to the modal. Retain the platform's native behavior.
    assert.ok(focus.modal && (focus.inside || focus.browserBoundary), `${dialogName} prevents focus on underlying application controls`);
    if (focus.browserBoundary) {
      await page.keyboard.press('Tab');
      assert.equal(await dialog.evaluate(el => el.contains(document.activeElement)), true, `${dialogName} receives focus again after browser chrome`);
    }
  }
  await page.keyboard.press('Escape');
  await dialog.waitFor({state: 'detached'});
  await page.waitForFunction(name => document.activeElement?.textContent.trim() === name, buttonName);
  results.keyboard.push(`${dialogName}: Enter, focus containment, Escape and return to opener`);
}

(async () => {
  fs.mkdirSync('artifacts', {recursive: true});
  const browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage']});
  try {
    const context = await browser.newContext({viewport: {width: 1440, height: 1000}, reducedMotion: 'reduce'});
    context.on('request', request => {
      const url = new URL(request.url());
      if (/^https?:$/.test(url.protocol)) requests.add(`${url.origin}${url.pathname}`);
    });
    const page = await context.newPage();
    page.setDefaultTimeout(10000);
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(root);
    await page.getByRole('button', {name: 'List', exact: true}).waitFor();
    await page.keyboard.press('Tab');
    assert.equal(await page.locator('.skip-link').evaluate(el => el === document.activeElement), true);
    const skip = await page.locator('.skip-link').boundingBox();
    assert.ok(skip.y >= 0, 'Focused skip link must be visible');
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('#main').evaluate(el => el === document.activeElement), true);
    results.keyboard.push('First Tab exposes skip link; Enter focuses curriculum');

    await listView(page);
    const search = page.getByRole('textbox', {name: 'Search nodes', exact: true});
    await search.focus();
    await page.keyboard.type('Structure 1.1.1');
    assert.equal(await page.locator('.list-view button').count(), 1);
    await page.locator('.list-view button').focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('.official-statement>b').textContent(), 'Structure 1.1.1');
    assert.equal(await page.getByLabel('How do you feel about this statement?', {exact: true}).inputValue(), 'not-reviewed');
    assert.equal(await page.evaluate(() => localStorage.length), 0, 'Keyboard navigation must not create progress');
    await focusRing(page, page.locator('.list-view button'));
    await search.fill('');
    const level = page.getByLabel('Level filter', {exact: true});
    await level.focus();
    await page.keyboard.press('End');
    await page.keyboard.press('Enter');
    assert.equal(await level.inputValue(), 'HL-only');
    assert.equal(await page.locator('.list-view button').count(), 61);
    await page.keyboard.press('Home');
    await page.keyboard.press('Enter');
    assert.equal(await level.inputValue(), 'SL');
    assert.equal(await page.locator('.list-view button').count(), 104);
    await level.selectOption('all');
    results.keyboard.push('Search, activate list item and change native SL/HL filter using keyboard');

    const summary = page.locator('.guided-practice .practice-solution > summary');
    await summary.focus();
    await page.keyboard.press('Space');
    assert.equal(await summary.evaluate(el => el.parentElement.open), true);
    await page.keyboard.press('Enter');
    assert.equal(await summary.evaluate(el => el.parentElement.open), false);
    await focusRing(page, summary);
    results.keyboard.push('Native worked explanation opens/closes with Space/Enter and has a focus ring');

    await contrast(page, ['.notice', '.list-view .chosen', '.list-view .chosen small', '.list-view b', '.muted', '.source-note', '.eyebrow', '.legend span', '.map-summary span', '.detail-body h3>span', '.misconception b', '.guided-practice .practice-kicker', '.self-assessment select', '.progress-tools button']);
    await modalKeyboard(page, 'Import self-assessment', 'Import self-assessment');
    // The Help dialog is part of the student release, so missing help is a failure.
    const help = page.getByRole('button', {name: 'Help', exact: true});
    await help.focus();
    await page.keyboard.press('Enter');
    const helpDialog = page.getByRole('dialog');
    await helpDialog.waitFor();
    const helpName = await helpDialog.getAttribute('aria-labelledby');
    assert.ok(helpName, 'Help dialog needs a named heading');
    const dialogTitle = await page.locator(`[id="${helpName}"]`).textContent();
    await page.keyboard.press('Escape');
    await helpDialog.waitFor({state: 'detached'});
    await modalKeyboard(page, 'Help', dialogTitle.trim());

    // Map text is checked at its authored size; the list supplies an unscaled alternative.
    await page.getByRole('button', {name: 'Map', exact: true}).click();
    await page.locator('.skill-card').first().waitFor();
    const selectedCard = page.locator('.skill-card[aria-pressed="true"]');
    await focusRing(page, selectedCard);
    await selectedCard.focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('.official-statement>b').textContent(), 'Structure 1.1.1');
    results.keyboard.push('Selected map card has a visible keyboard focus ring and opens with Enter');
    await contrast(page, ['.skill-card strong', '.skill-card .node-meta>span', '.skill-card .node-meta>b', '.skill-card .node-status', '.skill-card .self-dot']);
    const targets = await page.locator('.progress-tools button,.toolbar button,.toolbar select,.map-options button,.map-options select,.react-flow__controls-button,.header-right button,.header-right select').evaluateAll(elements => elements.map(el => {
      const box = el.getBoundingClientRect();
      return {label: el.getAttribute('aria-label') || el.textContent.trim(), width: box.width, height: box.height};
    }));
    for (const target of targets) assert.ok(target.width >= 44 && target.height >= 44, `${target.label} target is ${target.width}×${target.height}`);
    assert.equal(await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches), true);
    const motion = await page.locator('.skill-card').first().evaluate(el => ({animation: getComputedStyle(el).animationName, transition: getComputedStyle(el).transitionDuration}));
    assert.equal(motion.animation, 'none');
    assert.equal(motion.transition, '0s');

    await listView(page);
    await page.screenshot({path: 'artifacts/accessibility-desktop.png', fullPage: true});
    for (const width of [720, 360, 320]) {
      // 720 CSSpx represents the reflow area of a 1440px window at 200% zoom.
      // Device scaling is not used as a substitute for changing the CSS viewport.
      await page.setViewportSize({width, height: width === 720 ? 500 : 800});
      await noHorizontalOverflow(page, width === 720 ? '200% zoom-equivalent reflow' : `${width}px mobile reflow`);
      await page.getByRole('button', {name: 'Import self-assessment', exact: true}).click();
      const dialog = page.getByRole('dialog', {name: 'Import self-assessment', exact: true});
      await dialog.waitFor();
      const box = await dialog.boundingBox();
      assert.ok(box.x >= 0 && box.x + box.width <= width + 1, 'Import dialog fits the viewport');
      await noHorizontalOverflow(page, `${width}px with import dialog`);
      await page.keyboard.press('Escape');
    }
    await page.locator('.list-view .chosen').focus();
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => document.activeElement?.id === 'node-details');
    assert.equal(await page.getByLabel('How do you feel about this statement?', {exact: true}).inputValue(), 'not-reviewed');
    results.keyboard.push('320px list selection moves focus to its details without changing confidence');
    await page.screenshot({path: 'artifacts/accessibility-mobile-320.png', fullPage: true});
    results.externalRequests = [...requests].filter(url => new URL(url).origin !== origin);
    assert.deepEqual(results.externalRequests, [], 'Normal use must make no third-party requests');
    assert.deepEqual(errors, [], 'No browser exceptions');
    const selectors = [...new Set(results.contrast.map(sample => sample.selector))];
    const contrastSummary = selectors.map(selector => {
      const samples = results.contrast.filter(sample => sample.selector === selector);
      return {selector, count: samples.length, minimumRatio: Math.min(...samples.map(sample => sample.ratio))};
    });
    const report = {...results, contrastSampleCount: results.contrast.length, minimumContrastRatio: Math.min(...results.contrast.map(sample => sample.ratio)), contrast: contrastSummary};
    fs.writeFileSync('artifacts/accessibility-report.json', JSON.stringify(report, null, 2) + '\n');
    console.log(`Accessibility smoke passed: ${results.contrast.length} computed contrast samples (all ≥4.5:1), keyboard controls/dialogs, 44px primary targets, reduced motion and 320/360/720px reflow. External requests: 0.`);
    await context.close();
  } finally {await browser.close();}
})().catch(error => {console.error(error); process.exitCode = 1;});
