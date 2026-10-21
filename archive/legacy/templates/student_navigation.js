const sectionLinks = [...document.querySelectorAll('[data-section-link]')];
function updateNavigation() {
  const active = document.querySelector('.assessment-view:not([hidden])');
  sectionLinks.forEach(link => {
    link.href = '#' + active.dataset.assessment + '-' + link.dataset.sectionLink;
  });
  markSection('overview');
}
function markSection(key) {
  sectionLinks.forEach(link => {
    if (link.dataset.sectionLink === key) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  });
}
sectionLinks.forEach(link => link.addEventListener('click', () => {
  markSection(link.dataset.sectionLink);
  const target = document.getElementById(link.hash.slice(1));
  if (target) target.focus({preventScroll: true});
}));
updateNavigation();
let navigationFrame = false;
window.addEventListener('scroll', () => {
  if (navigationFrame) return;
  navigationFrame = true;
  requestAnimationFrame(() => {
    const sections = [...document.querySelectorAll('.assessment-view:not([hidden]) [data-section]')];
    const reached = sections.filter(section => section.getBoundingClientRect().top <= 140);
    if (reached.length) markSection(reached[reached.length - 1].dataset.section);
    navigationFrame = false;
  });
}, {passive: true});
