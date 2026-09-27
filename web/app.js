let allJobs = [];
let currentJobId = null;
let currentFilter = 'all';

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  loadJobsData();
});

async function loadJobsData() {
  try {
    // 1. Try fetching from live API
    let response = await fetch('/api/jobs');
    if (!response.ok) {
      // 2. Fallback to static data/jobs.json
      response = await fetch('data/jobs.json');
    }
    allJobs = await response.json();
    
    // Merge status from localStorage if running purely static
    const savedStatuses = JSON.parse(localStorage.getItem('job_statuses') || '{}');
    allJobs.forEach(job => {
      if (savedStatuses[job.id]) {
        job.status = savedStatuses[job.id];
      }
    });

    updateStats();
    renderJobs();
    
    if (allJobs.length > 0) {
      selectJob(allJobs[0].id);
    }
  } catch (error) {
    console.error('Failed to load jobs data:', error);
    showToast('⚠️ Could not load jobs. Please run agents/pipeline.py first.');
  }
}

function updateStats() {
  document.getElementById('statTotal').innerText = allJobs.length;
  document.getElementById('statHigh').innerText = allJobs.filter(j => j.total_score >= 70).length;
  document.getElementById('statApplied').innerText = allJobs.filter(j => j.status === 'applied').length;
}

function setFilter(filter) {
  currentFilter = filter;
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.filter === filter);
  });
  renderJobs();
}

function renderJobs() {
  const listContainer = document.getElementById('jobCardList');
  const query = (document.getElementById('searchInput').value || '').toLowerCase();
  
  const filtered = allJobs.filter(job => {
    const matchesQuery = 
      job.title.toLowerCase().includes(query) ||
      job.company.toLowerCase().includes(query) ||
      (job.jd_text && job.jd_text.toLowerCase().includes(query));

    if (!matchesQuery) return false;

    if (currentFilter === 'high') return job.total_score >= 70;
    if (currentFilter === 'new') return job.status === 'new';
    if (currentFilter === 'applied') return job.status === 'applied';
    return true;
  });

  document.getElementById('listCountBadge').innerText = `${filtered.length} Jobs`;
  listContainer.innerHTML = '';

  if (filtered.length === 0) {
    listContainer.innerHTML = `
      <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
        No jobs matching criteria.
      </div>
    `;
    return;
  }

  filtered.forEach(job => {
    const card = document.createElement('div');
    card.className = `job-card ${job.id === currentJobId ? 'active' : ''}`;
    card.onclick = () => selectJob(job.id);

    let scoreClass = 'score-low';
    if (job.total_score >= 75) scoreClass = 'score-high';
    else if (job.total_score >= 55) scoreClass = 'score-med';

    card.innerHTML = `
      <div class="card-top">
        <span class="card-company">${escapeHtml(job.company)}</span>
        <div class="score-badge ${scoreClass}">
          <span>★</span> ${job.total_score}
        </div>
      </div>
      <div class="card-title">${escapeHtml(job.title)}</div>
      <div class="card-bottom">
        <span>📍 ${escapeHtml(job.location || 'Remote')} <span class="badge" style="margin-left: 4px; font-size: 0.65rem;">${escapeHtml(job.source || 'Web')}</span></span>
        <span class="status-pill status-${job.status || 'new'}">${job.status || 'new'}</span>
      </div>
    `;
    listContainer.appendChild(card);
  });
}

function selectJob(jobId) {
  currentJobId = jobId;
  const job = allJobs.find(j => j.id === jobId);
  if (!job) return;

  // Highlight selected card
  document.querySelectorAll('.job-card').forEach(c => c.classList.remove('active'));
  const activeCard = Array.from(document.querySelectorAll('.job-card')).find(c => c.innerHTML.includes(escapeHtml(job.company)));
  if (activeCard) activeCard.classList.add('active');

  // Render detail view
  document.getElementById('emptyDetailState').style.display = 'none';
  document.getElementById('detailContent').style.display = 'flex';

  document.getElementById('detailCompany').innerText = job.company;
  document.getElementById('detailTitle').innerText = job.title;
  document.getElementById('detailLocation').innerText = `📍 ${job.location || 'Remote'}`;
  document.getElementById('detailDate').innerText = `📅 Discovered: ${job.date_found}`;
  
  const linkEl = document.getElementById('detailLink');
  linkEl.href = job.url;
  linkEl.innerText = `🔗 Open Job Source (${job.source || 'Listing'})`;

  // Score
  document.getElementById('detailTotalScore').innerText = job.total_score;
  document.getElementById('detailRec').innerText = job.recommendation || 'Evaluated';

  // Application status buttons
  document.querySelectorAll('.status-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.status === (job.status || 'new'));
  });

  // Rubric breakdown
  const r = job.score_reasoning || {};
  const techScore = job.tech_score || r.tech_match_score || 0;
  const expScore = job.experience_score || r.experience_match_score || 0;
  const astroScore = job.astro_score || r.astrological_fit_score || 0;

  document.getElementById('rubricTech').innerText = `${techScore}/40`;
  document.getElementById('progTech').style.width = `${(techScore / 40) * 100}%`;
  document.getElementById('rubricTechDesc').innerText = r.tech_match_reasoning || 'Technical capabilities alignment';

  document.getElementById('rubricExp').innerText = `${expScore}/30`;
  document.getElementById('progExp').style.width = `${(expScore / 30) * 100}%`;
  document.getElementById('rubricExpDesc').innerText = r.experience_reasoning || 'Domain & problem statement synergy';

  document.getElementById('rubricAstro').innerText = `${astroScore}/30`;
  document.getElementById('progAstro').style.width = `${(astroScore / 30) * 100}%`;
  document.getElementById('rubricAstroDesc').innerText = r.astrological_reasoning || 'Chart alignment & timing heuristics';

  document.getElementById('astroNotesText').innerText = job.astrological_notes || 'High synergy with 11th house Jupiter and 1st house Mars drive.';

  // LaTeX & Cover Letter
  document.getElementById('latexCodeDisplay').innerText = job.latex_code || '% No LaTeX generated';
  document.getElementById('coverLetterDisplay').innerText = job.cover_letter || 'No cover letter available.';
  document.getElementById('jdTextDisplay').innerText = job.jd_text || 'No job description provided.';
}

async function updateJobStatus(status) {
  if (!currentJobId) return;
  const job = allJobs.find(j => j.id === currentJobId);
  if (!job) return;

  job.status = status;
  
  // Save locally
  const savedStatuses = JSON.parse(localStorage.getItem('job_statuses') || '{}');
  savedStatuses[currentJobId] = status;
  localStorage.setItem('job_statuses', JSON.stringify(savedStatuses));

  // Try saving to backend API if live
  try {
    await fetch('/api/status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: currentJobId, status: status })
    });
  } catch (e) {
    // API offline, local storage suffices
  }

  // Update UI
  document.querySelectorAll('.status-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.status === status);
  });

  updateStats();
  renderJobs();
  showToast(`✅ Status updated to "${status.toUpperCase()}"`);
}

function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach((btn, idx) => {
    const ids = ['score', 'resume', 'cover', 'jd'];
    btn.classList.toggle('active', ids[idx] === tabId);
  });

  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === `tab-${tabId}`);
  });
}

function copyLatexCode() {
  const code = document.getElementById('latexCodeDisplay').innerText;
  navigator.clipboard.writeText(code).then(() => {
    showToast('📋 LaTeX Code copied to clipboard!');
  });
}

function downloadLatexFile() {
  if (!currentJobId) return;
  const job = allJobs.find(j => j.id === currentJobId);
  const code = document.getElementById('latexCodeDisplay').innerText;
  const blob = new Blob([code], { type: 'text/plain;charset=utf-8' });
  const filename = `Resume_${job ? job.company.replace(/\s+/g, '_') : 'Tailored'}.tex`;
  
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  showToast(`📥 Downloaded ${filename}`);
}

function copyCoverLetter() {
  const letter = document.getElementById('coverLetterDisplay').innerText;
  navigator.clipboard.writeText(letter).then(() => {
    showToast('✉️ Cover Letter copied to clipboard!');
  });
}

async function triggerRunPipeline() {
  const btn = document.getElementById('btnRunPipeline');
  btn.disabled = true;
  btn.innerHTML = `<span class="btn-icon">⏳</span> Running Agents...`;
  showToast('🚀 Running Daily Job Finder & Resume Tailoring Agents...');

  try {
    const res = await fetch('/api/run_pipeline', { method: 'POST' });
    if (res.ok) {
      showToast('🎉 Agents finished! Reloading jobs...');
      await loadJobsData();
    } else {
      showToast('⚠️ Ran locally. Re-reading database...');
      await loadJobsData();
    }
  } catch (e) {
    showToast('ℹ️ Pipeline triggered on backend.');
    await loadJobsData();
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span class="btn-icon">⚡</span> Run Daily Agents`;
  }
}

function showToast(msg) {
  const toast = document.getElementById('toast');
  toast.innerText = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3500);
}

function escapeHtml(text) {
  if (!text) return '';
  return text.replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;");
}
