// Validate real production assets under reference headers and a configured subpath.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {execFileSync} = require('node:child_process');
const root = process.env.SMOKE_URL || 'http://127.0.0.1:4174/chemistree/';
(async () => {
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 try {
  const page=await browser.newPage(); page.setDefaultTimeout(8000);
  const errors=[], requests=[]; page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(r.url().startsWith('http'))requests.push(new URL(r.url()));});
  await page.addInitScript(()=>{window.__violations=[];addEventListener('securitypolicyviolation',e=>window.__violations.push(e.effectiveDirective));});
  const response=await page.goto(root+'#node=ib-2025-structure-2.2.6');
  const headers=response.headers(); assert.match(headers['content-security-policy'],/default-src 'none'/); assert.equal(headers['referrer-policy'],'no-referrer');
  await page.locator('.skill-card').first().waitFor(); await page.getByRole('heading',{name:'Guided practice',exact:true}).waitFor();
  await page.getByRole('button',{name:'Help',exact:true}).click(); await page.keyboard.press('Escape');
  await page.reload(); await page.locator('.skill-card').first().waitFor();
  assert.equal(await page.locator('.official-statement > b').innerText(),'Structure 2.2.6');
  assert.ok((await page.getByRole('link',{name:'Link to this statement',exact:true}).getAttribute('href')).startsWith(new URL(root).pathname+'#node='));
  assert.deepEqual(await page.evaluate(()=>window.__violations),[]); assert.deepEqual(errors,[]);
  assert.ok(requests.every(url=>url.origin===new URL(root).origin && url.pathname.startsWith(new URL(root).pathname)));
  assert.ok(requests.some(url=>/MapView-/.test(url.pathname))); assert.ok(requests.some(url=>/PracticeSection-/.test(url.pathname)));
  const anchor = execFileSync('python3', ['-c', 'import sys; from integration.chemistree_links import load_node_titles,node_anchor; print(node_anchor(sys.argv[1],"ib-2025-structure-2.2.6",load_node_titles()))', root], {encoding:'utf8'});
  const report = await browser.newPage();
  await report.route('**/fictional-report?*', route => route.fulfill({contentType:'text/html', body:'<!doctype html><html><body>'+anchor+'</body></html>'}));
  await report.goto(new URL('/fictional-report?record=fictional', root).href);
  const destinationRequest = report.waitForRequest(request => request.isNavigationRequest() && new URL(request.url()).pathname === new URL(root).pathname);
  await report.getByRole('link', {name:'Molecular polarity', exact:true}).click();
  assert.equal((await destinationRequest).headers()['referer'], undefined, 'A report link must not leak its source report URL');
  await report.locator('.skill-card').first().waitFor();
  await report.close();
  fs.writeFileSync('artifacts/hosting-check.json',JSON.stringify({basePath:new URL(root).pathname,cspViolations:[],externalRequests:[],deepLinkReload:true,localLazyChunks:true,reportReferrerSuppressed:true},null,2)+'\n');
  console.log('Reference hosting passed: subpath, local lazy modules, deep-link reload, no CSP violations or external requests.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
