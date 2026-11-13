'use strict';
const search = document.querySelector('#search');
const paper = document.querySelector('#paper');
const level = document.querySelector('#level');
const review = document.querySelector('#review');
const results = document.querySelector('#results');
const more = document.querySelector('#more');
let limit = 50;
for (const [key, select] of [['paper', paper], ['level', level]]) {
  for (const value of [...new Set(catalog.map(q => q[key]))].sort()) {
    if (value) select.add(new Option(value, value));
  }
}
function render() {
  const needle = search.value.trim().toLowerCase();
  const found = catalog.filter(q => (!paper.value || q.paper === paper.value) &&
    (!level.value || q.level === level.value) && (!review.checked || q.review) &&
    `${q.title} ${q.topic} ${q.date} ${q.text}`.toLowerCase().includes(needle));
  results.replaceChildren();
  for (const q of found.slice(0, limit)) {
    const card = document.createElement('article');
    const link = document.createElement('a');
    link.href = `questions/${q.id}.html`;
    link.textContent = `${q.title} — Paper ${q.paper}, ${q.level}`;
    const detail = document.createElement('p');
    detail.textContent = `${q.date} · ${q.topic}${q.review ? ' · Source warnings' : ''}`;
    card.append(link, detail);
    results.append(card);
  }
  document.querySelector('#count').textContent = `${found.length} records found; showing ${Math.min(limit, found.length)}.`;
  more.hidden = found.length <= limit;
}
for (const el of [search, paper, level, review]) el.addEventListener('input', () => { limit = 50; render(); });
more.addEventListener('click', () => { limit += 50; render(); });
render();
