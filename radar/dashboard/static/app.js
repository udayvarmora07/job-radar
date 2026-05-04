/** Job Radar Dashboard — Frontend Logic */

const API = '/api/jobs';

let allJobs = [];
let displayedJobs = [];

// ─── Init ────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  loadJobs();
  bindControls();
});

// ─── Data Loading ────────────────────────────────────────────────────────────

async function loadJobs() {
  try {
    const res = await fetch(API);
    const data = await res.json();
    allJobs = data.jobs || [];
    updateStats(allJobs);
    renderJobs(allJobs);
  } catch (err) {
    console.error('Failed to load jobs:', err);
    document.getElementById('job-grid').innerHTML = `
      <div class="empty-state">
        <p>Failed to load jobs. <button onclick="loadJobs()">Retry</button></p>
      </div>`;
  }
}

// ─── Rendering ───────────────────────────────────────────────────────────────

function renderJobs(jobs) {
  const grid = document.getElementById('job-grid');
  const empty = document.getElementById('empty-state');

  if (!jobs.length) {
    grid.innerHTML = '';
    empty.style.display = 'block';
    return;
  }

  empty.style.display = 'none';
  grid.innerHTML = jobs.map(job => cardHTML(job)).join('');
}

function cardHTML(job) {
  const score = job.score || 0;
  const tier = score >= 40 ? 'strong' : score >= 20 ? 'moderate' : 'weak';
  const tierLabel = tier === 'strong' ? 'Strong' : tier === 'moderate' ? 'Moderate' : 'Weak';
  const loc = job.location || 'Unknown';
  const posted = job.posted_at ? relativeDate(job.posted_at) : '';
  const skills = extractSkills(job);
  const desc = job.description || '';

  return `
  <a href="${job.url || '#'}" target="_blank" rel="noopener" class="job-card tier-${tier}">
    <div class="job-card-top">
      <span class="job-company">${escHtml(job.company || 'Unknown')}</span>
      <span class="job-score">${score} pts</span>
    </div>
    <div class="job-title">${escHtml(job.title || 'Unknown Title')}</div>
    <div class="job-meta">
      <span class="job-location">${escHtml(loc)}</span>
      ${posted ? `<span class="job-date">${posted}</span>` : ''}
    </div>
    ${skills.length ? `<div class="job-skills">${skills.map(s => `<span class="skill-tag">${escHtml(s)}</span>`).join('')}</div>` : ''}
    ${desc ? `<p class="job-description">${escHtml(desc)}</p>` : ''}
    <div class="job-card-footer">
      <span class="apply-btn">View & Apply →</span>
    </div>
  </a>`;
}

// ─── Filtering ────────────────────────────────────────────────────────────────

function bindControls() {
  const searchInput = document.getElementById('search-input');
  const locationFilter = document.getElementById('filter-location');
  const tierFilter = document.getElementById('filter-tier');
  const sortFilter = document.getElementById('filter-sort');
  const sourceFilter = document.getElementById('filter-source');

  let debounceTimer;
  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(applyFilters, 200);
  });

  [locationFilter, tierFilter, sortFilter, sourceFilter].forEach(el => {
    el.addEventListener('change', applyFilters);
  });
}

function applyFilters() {
  const q = document.getElementById('search-input').value.trim();
  const location = document.getElementById('filter-location').value;
  const tier = document.getElementById('filter-tier').value;
  const sort = document.getElementById('filter-sort').value;
  const source = document.getElementById('filter-source').value;

  let jobs = [...allJobs];

  if (q) {
    const qLower = q.toLowerCase();
    jobs = jobs.filter(j =>
      (j.title || '').toLowerCase().includes(qLower) ||
      (j.company || '').toLowerCase().includes(qLower) ||
      (j.description || '').toLowerCase().includes(qLower) ||
      (j.location || '').toLowerCase().includes(qLower)
    );
  }

  if (location) {
    if (location === 'remote') {
      jobs = jobs.filter(j => /remote|wfh|work from home/i.test(j.location || ''));
    } else {
      jobs = jobs.filter(j => (j.location || '').toLowerCase().includes(location));
    }
  }

  if (tier) {
    if (tier === 'strong') jobs = jobs.filter(j => (j.score || 0) >= 40);
    else if (tier === 'moderate') jobs = jobs.filter(j => { const s = j.score || 0; return s >= 20 && s < 40; });
    else if (tier === 'weak') jobs = jobs.filter(j => { const s = j.score || 0; return s > 0 && s < 20; });
  }

  if (source) {
    jobs = jobs.filter(j => j.source === source);
  }

  if (sort === 'date') {
    jobs.sort((a, b) => (b.posted_at || '').localeCompare(a.posted_at || ''));
  } else if (sort === 'company') {
    jobs.sort((a, b) => (a.company || '').localeCompare(b.company || ''));
  } else {
    jobs.sort((a, b) => (b.score || 0) - (a.score || 0));
  }

  renderJobs(jobs);
}

function resetFilters() {
  document.getElementById('search-input').value = '';
  document.getElementById('filter-location').value = '';
  document.getElementById('filter-tier').value = '';
  document.getElementById('filter-source').value = '';
  document.getElementById('filter-sort').value = 'score';
  applyFilters();
}

// ─── Stats ───────────────────────────────────────────────────────────────────

function updateStats(jobs) {
  const total = jobs.length;
  const strong = jobs.filter(j => (j.score || 0) >= 20).length;
  const moderate = jobs.filter(j => { const s = j.score || 0; return s >= 10 && s < 20; }).length;
  const weak = jobs.filter(j => { const s = j.score || 0; return s > 0 && s < 10; }).length;

  const now = new Date();
  const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  const fresh = jobs.filter(j => {
    if (!j.posted_at) return false;
    const d = new Date(j.posted_at);
    return d >= weekAgo;
  }).length;

  document.getElementById('stat-total').textContent = total;
  document.getElementById('stat-strong').textContent = strong;
  document.getElementById('stat-moderate').textContent = moderate;
  document.getElementById('stat-weak').textContent = weak;
  document.getElementById('stat-fresh').textContent = fresh;
  document.getElementById('total-count').textContent = total ? `${total} jobs` : '';
}

// ─── Utilities ────────────────────────────────────────────────────────────────

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function relativeDate(dateStr) {
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    const diff = Date.now() - d.getTime();
    const days = Math.floor(diff / 86400000);
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days}d ago`;
    if (days < 30) return `${Math.floor(days / 7)}w ago`;
    return `${Math.floor(days / 30)}mo ago`;
  } catch {
    return dateStr;
  }
}

function extractSkills(job) {
  const skillKeywords = [
    'kubernetes', 'k8s', 'terraform', 'aws', 'gcp', 'azure', 'docker',
    'gitops', 'argocd', 'github actions', 'jenkins', 'prometheus', 'grafana',
    'linux', 'python', 'bash', 'ansible', 'vault', 'helm', 'ci/cd',
  ];
  const text = ((job.title || '') + ' ' + (job.description || '')).toLowerCase();
  return skillKeywords.filter(s => text.includes(s)).slice(0, 6);
}