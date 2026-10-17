const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icons = {violet:'✳',blue:'◈',orange:'⌁',green:'◉'};
async function request(path, options) { const res = await fetch(path, options); const data = await res.json(); if (!res.ok) throw new Error(data.error || 'Something went wrong'); return data; }
function renderProjects(projects) {
  $('#projects-list').innerHTML = projects.map(p => `<tr><td class="project-name"><span class="project-logo logo-${esc(p.color)}">${icons[p.color] || '◈'}</span><span>${esc(p.name)}<span class="repo">${esc(p.repo)}</span></span></td><td><span class="status-pill ${p.status === 'Building' ? 'building' : 'success'}"><i class="live-dot"></i>${esc(p.status)}</span></td><td>${esc(p.updated)}</td><td><span class="branch">⑂ ${esc(p.branch)}</span></td><td><button class="row-menu" aria-label="Project menu">···</button></td></tr>`).join('') || '<tr><td colspan="5" class="loading-cell">No projects yet. Create your first one.</td></tr>';
  $('#project-select').innerHTML = projects.map(p => `<option value="${p.id}">${esc(p.name)}</option>`).join('');
  $('.count-pill').textContent = String(projects.length).padStart(2,'0');
}
function renderDeployments(items) {
  $('#deploy-list').innerHTML = items.slice(0,5).map(d => `<div class="deploy-row"><div class="deploy-project"><span class="deploy-icon">↥</span>${esc(d.project)}</div><span class="deploy-version">${esc(d.version)}</span><span class="deploy-env"><span class="env-tag">${esc(d.environment)}</span></span><span class="deploy-time">${esc(new Date(d.created).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}))}</span><span class="duration">${d.status === 'Building' ? '<span class="status-pill building"><i class="live-dot"></i>Building</span>' : esc(d.duration)}</span></div>`).join('') || '<div class="loading-cell">No deployments yet.</div>';
}
async function load() { try { const data = await request('/api/overview'); renderProjects(data.projects); renderDeployments(data.deployments); } catch(e) { $('#projects-list').innerHTML = `<tr><td colspan="5" class="loading-cell">Could not reach the API: ${esc(e.message)}</td></tr>`; } }
const modal = $('#deploy-modal');
function showModal() { modal.classList.add('open'); modal.setAttribute('aria-hidden','false'); $('#deploy-message').textContent=''; }
function hideModal() { modal.classList.remove('open'); modal.setAttribute('aria-hidden','true'); }
$('#new-deploy').addEventListener('click', showModal);
document.querySelectorAll('[data-close]').forEach(b => b.addEventListener('click', hideModal));
modal.addEventListener('click', e => { if (e.target === modal) hideModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') hideModal(); });
function toast(message) { const node=$('#toast'); node.textContent=message; node.classList.add('show'); setTimeout(()=>node.classList.remove('show'),2800); }
$('#deploy-form').addEventListener('submit', async e => { e.preventDefault(); const f=new FormData(e.currentTarget); const btn=e.currentTarget.querySelector('button[type=submit]'); btn.disabled=true; btn.textContent='Starting…'; try { await request('/api/deployments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(f))}); hideModal(); toast('Deployment queued successfully'); await load(); } catch(err) { $('#deploy-message').textContent=err.message; } finally { btn.disabled=false; btn.innerHTML='Start deployment <span>→</span>'; } });
$('#new-project').addEventListener('click', async () => { const name=prompt('What should we call this project?'); if (!name) return; const repo=prompt('Repository name (for example, northstar/my-app):','northstar/'); if (!repo) return; try { await request('/api/projects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,repo,branch:'main'})}); toast('Project created'); await load(); } catch(e) { toast(e.message); } });
$('#view-all').addEventListener('click', () => $('#deployments').scrollIntoView({behavior:'smooth'}));
$('#all-deploys').addEventListener('click', () => toast('Showing the latest deployments'));
load();

