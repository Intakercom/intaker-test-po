// Small, dependency-free UI. Every durable change goes through the Python API.
const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels = {new:'New',assessing:'Assessing',queued:'Queued',repairing:'In repair',ready:'Ready to collect',closed:'Closed',cancelled:'Cancelled',lighting:'Lighting',sewing:'Sewing',appliances:'Appliances',audio:'Audio',not_requested:'Not requested',pending:'Awaiting decision',approved:'Approved',declined:'Declined',needed:'Needed',ordered:'Ordered',received:'Received',accepted:'Provider accepted',failed:'Failed'};
const activeStatuses = ['new','assessing','queued','repairing','ready'];
const paths = {
  list:'M5 4h14v16H5z M9 8h6 M9 12h6 M9 16h3',
  pulse:'M3 17V9 M9 17V4 M15 17v-7 M21 17V7 M2 21h20',
  mail:'M3 5h18v14H3z M3 6l9 7 9-7',
  plus:'M12 5v14 M5 12h14',
  search:'M20 20l-5-5 M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0',
  arrow:'M9 5l7 7-7 7',
  close:'M6 6l12 12 M6 18L18 6',
  help:'M9 8a3 3 0 0 1 6 0c0 3-3 2-3 5 M12 17h.01 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
  leaf:'M20 3C7 2 2 9 7 16s15 0 13-13 M4 21L16 8',
  clock:'M12 8v5l3 2 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
  check:'M5 12l4 4L19 6',
  box:'M3 7l9-4 9 4v11l-9 4-9-4z M3 7l9 5 9-5 M12 12v10 M7 5l10 5',
  user:'M8 7a4 4 0 1 0 8 0 4 4 0 0 0-8 0 M4 21v-3c0-4 16-4 16 0v3',
  refresh:'M20 7v5h-5 M4 17v-5h5 M5 8a8 8 0 0 1 14-2l1 2 M4 16l1 2a8 8 0 0 0 14-2',
  lighting:'M8 3h8l4 10H4z M12 13v7 M7 21h10',
  sewing:'M3 17h18v4H3z M5 17V6h12a4 4 0 0 1 4 4v3h-7V9H9v8 M17 13v4 M5 3h5',
  appliances:'M6 3h12v18H6z M9 6h6 M9 12h6 M9 16h6',
  audio:'M4 5h16v15H4z M7 3v2 M7 9h2 M15 9a4 4 0 1 0 0 8 4 4 0 0 0 0-8',
  note:'M4 3h16v18H4z M8 8h8 M8 12h8 M8 16h4',
};
const icon = name => `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.list}"/></svg>`;
const badge = status => `<span class="badge ${esc(status)}">${esc(labels[status] || status)}</span>`;
const initials = name => String(name).split(' ').map(x=>x[0]).slice(0,2).join('');
const avatar = (name,id='') => `<span class="avatar ${esc(id)}">${esc(initials(name))}</span>`;
const equipmentIcon = category => `<span class="equipment-icon ${esc(category)}">${icon(category)}</span>`;
const time = value => {
  const hours = Math.max(0,(Date.now()-new Date(value).getTime())/3600000);
  return hours < 1 ? 'Just now' : hours < 24 ? `${Math.floor(hours)}h ago` : `${Math.floor(hours/24)}d ago`;
};
const fullTime = value => new Date(value).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'});
let storedUser = 'alex';
try { storedUser = localStorage.getItem('intake-desk-user') || 'alex'; } catch {}
const state = { userId:storedUser, boot:null, rows:[], stats:null, outbox:[], view:'requests', filter:'active', category:'all', search:'', detail:null, tab:'overview', loadId:0 };
let toastTimer;

async function api(path, method='GET', data) {
  const response = await fetch(`/api${path}`, {method, headers:{'X-Demo-User':state.userId,...(data ? {'Content-Type':'application/json'} : {})}, ...(data ? {body:JSON.stringify(data)} : {})});
  const body = await response.json();
  if (!response.ok) { const error = new Error(body.error || 'Could not complete that action.'); error.status=response.status; throw error; }
  return body;
}
function toast(message,error=false) {
  clearTimeout(toastTimer); $('#toast').textContent=message; $('#toast').className=`visible ${error?'error':''}`;
  // The top layer keeps feedback visible above native modal dialogs.
  $('#toast').showPopover?.();
  toastTimer=setTimeout(()=>{ $('#toast').hidePopover?.(); $('#toast').className=''; },error?9000:4000);
}
const coordinator = () => state.boot.user.role === 'coordinator';
const ownerName = id => state.boot.staff.find(x=>x.id===id)?.name || 'Unassigned';
function shell() {
  const titles={requests:'Repair requests',pulse:'Workshop pulse',outbox:'Message outbox'};
  const orgShort=state.boot.organization.id==='benchside'?'Benchside':'Northstar';
  $('#app').innerHTML=`<div class="shell">
    <aside class="sidebar"><div class="brand"><img src="/mark.svg" alt="">Intake Desk</div>
      <div class="workspace"><span class="workspace-mark">${icon('leaf')}</span><div><strong>${esc(orgShort)} workshop</strong><span class="small">Community repair collective</span></div></div>
      <div class="nav-label">WORKSPACE</div><nav aria-label="Main navigation">
      ${[['requests','list','Repair requests'],['pulse','pulse','Workshop pulse'],['outbox','mail','Message outbox']].map(([view,i,label])=>`<button class="nav-btn ${state.view===view?'active':''}" data-nav="${view}" ${state.view===view?'aria-current="page"':''} title="${label}">${icon(i)}<span class="nav-text">${label}</span>${view==='requests'?`<span class="nav-count">${state.stats.active}</span>`:''}</button>`).join('')}
      </nav><div class="sidebar-foot"><div class="demo-card"><span class="eyebrow">Repair. Reuse. Repeat.</span><p>A little care. A longer life.<br>One repair at a time.</p></div><button class="nav-btn" data-action="help">${icon('help')}About this demo</button></div>
    </aside>
    <div class="main-wrap"><header class="topbar"><div class="breadcrumb"><span>${esc(orgShort)}</span>${icon('arrow')}<span>${titles[state.view]}</span></div><div class="top-actions"><span class="local-badge"><i class="dot"></i>Local demo</span><div class="profile">${avatar(state.boot.user.name,state.userId)}<label class="sr-only" for="profile">Demo profile</label><select id="profile" aria-label="Demo profile">${state.boot.profiles.map(p=>`<option value="${esc(p.id)}" ${p.id===state.userId?'selected':''}>${esc(p.name)} · ${p.role==='coordinator'?'Coordinator':'Technician'}${p.id==='robin'?' · Northstar':''}</option>`).join('')}</select></div></div></header>
      <main id="main" tabindex="-1">${state.view==='requests'?requestsView():state.view==='pulse'?pulseView():outboxView()}<div class="footer-note"><span>${icon('leaf')}Fewer things thrown away. More things made useful.</span><span>Fictional workshop · No real customer data</span></div></main>
    </div></div>`;
}
function statCards() {
  return `<div class="stats">${[
    ['Active repairs',state.stats.active,'In the workshop','list',''],
    ['Needs assessment',state.stats.new,'New arrivals','search',''],
    ['Customer decision',state.stats.approval_pending,'Awaiting approval','clock','alert'],
    ['Waiting on parts',state.stats.waiting_parts,'Keep an eye on these','box',''],
  ].map(([label,value,detail,i,cls])=>`<div class="stat ${cls}"><div class="stat-top"><span>${label}</span>${icon(i)}</div><div class="stat-bottom"><span class="stat-number">${value}</span><span class="stat-detail">${detail}</span></div></div>`).join('')}</div>`;
}
function filterRows(filter=state.filter) {
  return state.rows.filter(r=>{
    const active=activeStatuses.includes(r.status);
    const matches=filter==='closed'?!active:filter==='unassigned'?active&&!r.assigned_to:filter==='approval'?active&&r.approval_status==='pending':filter==='parts'?active&&r.pending_parts>0:active;
    return matches;
  });
}
function visibleRows() {
  const search=state.search.toLowerCase();
  return filterRows().filter(r=>(state.category==='all'||r.category===state.category)&&[r.equipment,r.customer_name,r.reference].some(x=>x.toLowerCase().includes(search)));
}
function requestsView() {
  return `<div class="page-head"><div><div class="eyebrow">A second life starts here</div><h1>Repair requests</h1><p>From the front desk to the workbench. Keep every repair moving.</p></div>${coordinator()?`<button class="button primary" data-action="new">${icon('plus')}New request</button>`:''}</div>
    ${statCards()}<section class="panel" aria-label="Repair requests"><div class="toolbar"><label class="search">${icon('search')}<input id="search" type="search" placeholder="Search equipment, customer, or reference…" aria-label="Search repair requests" value="${esc(state.search)}"></label><label class="filter-select"><span class="sr-only">Equipment category</span><select id="category" aria-label="Equipment category"><option value="all">All equipment</option>${state.boot.categories.map(c=>`<option value="${c}" ${state.category===c?'selected':''}>${labels[c]}</option>`).join('')}</select></label><button class="icon-button" data-action="refresh" title="Refresh requests" aria-label="Refresh requests">${icon('refresh')}</button></div>
    <div class="tabs" aria-label="Request filters">${[['active','All active'],['unassigned','Unassigned'],['approval','Customer decision'],['parts','Waiting on parts'],['closed','Closed']].map(([id,label])=>`<button class="tab ${state.filter===id?'active':''}" data-filter="${id}" aria-pressed="${state.filter===id}">${label}<span class="tab-count">${filterRows(id).length}</span></button>`).join('')}</div><div id="request-results">${tableContent()}</div></section>`;
}
function tableContent() {
  const rows=visibleRows();
  if(!rows.length) return `<div class="empty">${icon('list')}<h3>No repairs here</h3><p>${state.search||state.category!=='all'?'Try a different search or equipment category.':'There are no requests in this view for your demo profile.'}</p>${state.search||state.category!=='all'?'<button class="button small" data-action="clear-search">Clear filters</button>':''}</div>`;
  return `<div class="table-wrap"><table><thead><tr><th>Repair request</th><th class="customer-col">Customer</th><th>Status</th><th class="owner-col">Assigned to</th><th class="updated-col">Updated</th><th class="chevron-col"><span class="sr-only">Open</span></th></tr></thead><tbody>${rows.map(r=>`<tr data-request="${r.id}"><td><div class="request-cell">${equipmentIcon(r.category)}<div><button class="request-title" data-request="${r.id}">${esc(r.equipment)}</button><div class="reference">${esc(r.reference)}${r.priority==='high'?'<i class="priority-dot"></i><span>High priority</span>':''}</div></div></div></td><td class="customer-col customer-name">${esc(r.customer_name)}</td><td>${badge(r.status)}${r.approval_status==='pending'?'<div class="sub-status">Awaiting customer</div>':r.pending_parts?'<div class="sub-status">Parts outstanding</div>':''}</td><td class="owner-col"><div class="owner">${r.assigned_to?avatar(r.owner_name,r.assigned_to):`<span class="unassigned">${icon('user')}</span>`}${esc(r.owner_name?.split(' ')[0]||'Unassigned')}</div></td><td class="updated-col updated"><time datetime="${r.updated_at}" title="${esc(fullTime(r.updated_at))}">${time(r.updated_at)}</time></td><td class="chevron-col">${icon('arrow')}</td></tr>`).join('')}</tbody></table></div><div class="table-footer"><span>${rows.length} ${rows.length===1?'request':'requests'} · ${coordinator()?'Across your workshop':'Assigned to you'}</span><span>Changes are saved locally</span></div>`;
}
function pulseView() {
  const max=Math.max(1,...Object.values(state.stats.by_status));
  return `<div class="page-head"><div><div class="eyebrow">The workshop, at a glance</div><h1>Workshop pulse</h1><p>A current snapshot of ${coordinator()?'your workshop':'your assigned work'}. Counts update as repairs move.</p></div><button class="button" data-action="refresh">${icon('refresh')}Refresh</button></div>${statCards()}
  <div class="pulse-grid"><section class="panel"><div class="panel-head"><h3>Where repairs stand</h3><p>All visible requests, including closed and cancelled</p></div><div class="bar-list">${state.boot.statuses.map(s=>`<div class="bar-row"><span>${labels[s]}</span><div class="bar-track"><div class="bar" style="width:${state.stats.by_status[s]/max*100}%"></div></div><strong>${state.stats.by_status[s]}</strong></div>`).join('')}</div></section>
  <section class="panel"><div class="panel-head"><h3>What’s on the workbench</h3><p>Active repairs by equipment category</p></div><div class="category-grid">${state.boot.categories.map(c=>`<div class="category-card">${equipmentIcon(c)}<strong>${state.stats.by_category[c]}</strong><p>${labels[c]}</p></div>`).join('')}</div><div class="legend">${state.stats.unassigned} active ${state.stats.unassigned===1?'request needs':'requests need'} an owner.<br>Customer-decision and parts counts can overlap. These are current counts, not historical performance measures.</div></section></div>`;
}
function messageCard(m,detail=false) {
  return `<article class="message-card"><div class="message-top">${detail?`<span class="small muted">Customer update #${m.id}</span>`:`<button class="link-button" data-request="${m.request_id}">${esc(m.reference)} · ${esc(m.equipment)}</button>`}${badge(m.status)}</div><p>${esc(m.body)}</p><div class="message-meta"><span><time datetime="${m.created_at}" title="${esc(fullTime(m.created_at))}">${time(m.created_at)}</time> · ${m.attempts} provider ${m.attempts===1?'attempt':'attempts'}</span>${m.status==='failed'?`<button class="button small" data-retry="${m.id}" data-request-id="${m.request_id}">Retry message</button>`:m.provider_reference?`<span>${esc(m.provider_reference)}</span>`:''}</div>${m.last_error?`<div class="message-error">${esc(m.last_error)}</div>`:''}</article>`;
}
function outboxView() {
  return `<div class="page-head"><div><div class="eyebrow">Keep customers in the loop</div><h1>Message outbox</h1><p>Inspect queued updates and try the local provider simulator.</p></div></div><section class="panel"><div class="panel-head"><h3>Customer updates</h3><p>No email is sent. “Provider accepted” does not confirm delivery or that a customer read it.</p></div>${coordinator()?`<div class="outbox-tools"><label class="check"><input id="fail-first" type="checkbox">Simulate a timeout for the first queued message</label><button class="button primary" data-action="process">${icon('mail')}Process queued messages</button></div>`:'<div class="legend">A coordinator can run the provider simulation. You can queue updates and retry failed messages for your assigned repairs.</div>'}<div class="outbox-list">${state.outbox.length?state.outbox.map(m=>messageCard(m)).join(''):'<div class="empty"><h3>No customer updates yet</h3><p>Queue an update from a repair request to see it here.</p></div>'}</div></section>`;
}
async function load() {
  const loadId=++state.loadId;
  const [boot,rows,stats,outbox]=await Promise.all([api('/bootstrap'),api('/requests'),api('/dashboard'),api('/outbox')]);
  if(loadId!==state.loadId) return;
  Object.assign(state,{boot,rows,stats,outbox});
  shell();
}
async function route() {
  const hash=location.hash.slice(1)||'requests';
  const match=hash.match(/^request\/(\d+)$/);
  if(match) { await openDetail(Number(match[1])); return; }
  state.view=['requests','pulse','outbox'].includes(hash)?hash:'requests';
  state.detail=null;
  if($('#detail').open) $('#detail').close();
  shell();
}
async function openDetail(id) {
  const profile=state.userId;
  const detail=await api(`/requests/${id}`);
  if(profile!==state.userId||location.hash!==`#request/${id}`) return;
  if(state.detail?.id!==id) state.tab='overview';
  state.detail=detail; renderDetail();
  if(!$('#detail').open) $('#detail').showModal();
}
function renderDetail() {
  const r=state.detail;
  $('#detail').innerHTML=`<div class="drawer-top"><span class="eyebrow">Repair request / ${esc(r.reference)}</span><div><button class="icon-button" data-action="refresh-detail" aria-label="Refresh request" title="Refresh request">${icon('refresh')}</button><button class="icon-button" data-action="close-detail" aria-label="Close request">${icon('close')}</button></div></div><div class="drawer-head"><div class="drawer-title">${equipmentIcon(r.category)}<div><h2>${esc(r.equipment)}</h2><p class="muted">${esc(r.customer_name)} · ${esc(r.customer_email)}</p></div></div></div>
  <div class="tabs detail-tabs" aria-label="Request sections">${[['overview','Overview'],['activity',`Activity (${r.activity.length})`],['messages',`Messages (${r.messages.length})`]].map(([id,label])=>`<button class="tab ${state.tab===id?'active':''}" data-detail-tab="${id}" aria-pressed="${state.tab===id}">${label}</button>`).join('')}</div><div class="drawer-body">${state.tab==='overview'?detailOverview(r):state.tab==='activity'?detailActivity(r):detailMessages(r)}</div>`;
}
function detailOverview(r) {
  const options=(values,selected)=>values.map(v=>`<option value="${v}" ${v===selected?'selected':''}>${labels[v]||v}</option>`).join('');
  return `<section class="section"><div class="section-title"><h3>What needs a little care</h3>${r.priority==='high'?'<span class="badge pending">High priority</span>':''}</div><p class="description">${esc(r.description)}</p></section>
  <section class="section"><div class="section-title"><h3>Repair workflow</h3>${badge(r.status)}</div><form data-form="workflow"><div class="detail-grid">
  <div class="field"><label for="repair-status">Status</label><select id="repair-status" name="status">${options(state.boot.statuses,r.status)}</select></div>
  <div class="field"><label for="repair-owner">Assigned technician</label><select id="repair-owner" name="assigned_to" ${coordinator()?'':'disabled'}><option value="">Unassigned</option>${state.boot.staff.filter(u=>u.role==='technician').map(u=>`<option value="${u.id}" ${u.id===r.assigned_to?'selected':''}>${esc(u.name)}</option>`).join('')}</select></div>
  <div class="field"><label for="repair-estimate">Estimated bench time</label><input id="repair-estimate" type="number" name="estimated_minutes" value="${r.estimated_minutes??''}" placeholder="Not estimated" min="1" max="480"><span class="hint">Minutes of hands-on repair work</span></div>
  <div class="field"><label for="repair-priority">Priority</label><select id="repair-priority" name="priority" ${coordinator()?'':'disabled'}><option value="normal" ${r.priority==='normal'?'selected':''}>Normal</option><option value="high" ${r.priority==='high'?'selected':''}>High</option></select></div></div><div class="form-actions"><span class="hint">Version ${r.version}</span><button class="button" type="submit">Save workflow</button></div></form></section>
  <div class="subtle-rule"></div><section class="section"><div class="section-title"><h3>Customer approval</h3></div><div class="estimate-card"><div><div class="estimate-amount">${r.quote_cents===null?'—':`£${(r.quote_cents/100).toFixed(2)}`}</div><p>Repair estimate</p></div>${badge(r.approval_status)}</div>
  ${coordinator()?`<form data-form="quote" class="inline-form"><div class="field"><label for="quote-amount">${r.quote_cents===null?'Create':'Replace'} estimate (£)</label><input id="quote-amount" type="number" min="0" max="1000" step="0.01" name="amount" placeholder="25.00" required></div><button class="button" type="submit">Request approval</button></form><p class="small muted" style="margin-top:9px;line-height:1.6">A new estimate resets approval to pending and queues a simulated customer message.</p>${r.approval_status==='pending'?'<div class="demo-controls"><span>Simulate customer response</span><button class="button small" data-approval="approved">Approve</button><button class="button small" data-approval="declined">Decline</button></div>':''}`:''}</section>
  <div class="subtle-rule"></div><section class="section"><div class="section-title"><h3>Parts & materials</h3><span class="small muted">${r.parts.length} ${r.parts.length===1?'item':'items'}</span></div>${r.parts.length?r.parts.map(p=>`<div class="part-item"><div>${esc(p.name)}<p>Quantity ${p.quantity}</p></div><select aria-label="Status for ${esc(p.name)}" data-part="${p.id}">${options(['needed','ordered','received'],p.status)}</select></div>`).join(''):'<p class="small muted">No parts have been recorded for this repair.</p>'}<form data-form="part" class="inline-form"><div class="field"><label for="part-name">Add a part</label><input id="part-name" name="name" maxlength="120" placeholder="e.g. Replacement switch" required></div><div class="field" style="max-width:65px"><label for="part-qty">Qty</label><input id="part-qty" type="number" name="quantity" value="1" min="1" max="99" required></div><button class="button" type="submit">Add</button></form></section>
  <div class="callout">Recorded ${esc(fullTime(r.created_at))}.<br>Last updated ${esc(fullTime(r.updated_at))}.</div>`;
}
function detailActivity(r) {
  return `<section class="section"><form data-form="note"><div class="field"><label for="note-body">Leave a workshop note</label><textarea id="note-body" name="body" placeholder="An observation, a handoff, or the next step…" maxlength="2000" required></textarea></div><div class="form-actions"><button class="button primary" type="submit">Add note</button></div></form></section><div class="subtle-rule"></div>${r.activity.map(a=>`<article class="timeline-item"><span class="timeline-dot">${icon(a.event_type==='note'?'note':a.event_type==='message'?'mail':'check')}</span><div class="timeline-body"><strong>${esc(a.actor)}</strong><time datetime="${a.created_at}" title="${esc(fullTime(a.created_at))}">${time(a.created_at)}</time><p>${esc(a.message)}</p></div></article>`).join('')}`;
}
function detailMessages(r) {
  return `<div class="callout orange">This is a local simulation. Provider acceptance does not confirm delivery or a customer response. A coordinator can process queued messages in the outbox.</div><section class="section" style="margin-top:23px"><form data-form="message"><div class="field"><label for="message-body">Customer update</label><textarea id="message-body" name="body" placeholder="Write an update about this repair…" maxlength="2000" required></textarea></div><div class="form-actions"><button class="button primary" type="submit">${icon('mail')}Queue update</button></div></form></section>${r.messages.length?r.messages.map(m=>messageCard(m,true)).join(''):'<div class="empty"><h3>No messages yet</h3><p>Queue a customer update using the form above.</p></div>'}`;
}
function modal(title,body) {
  $('#modal').innerHTML=`<div class="modal-head"><h2 id="modal-title">${title}</h2><button class="icon-button" data-action="close-modal" aria-label="Close dialog">${icon('close')}</button></div><div class="modal-body">${body}</div>`;
  $('#modal').showModal();
}
function newRequest() {
  modal('A new beginning',`<p>Add a repair to the workshop. It will start as a new, unassigned request.</p><form data-form="new"><div class="detail-grid"><div class="field"><label for="customer-name">Customer name</label><input id="customer-name" name="customer_name" maxlength="100" required></div><div class="field"><label for="customer-email">Email</label><input id="customer-email" type="email" name="customer_email" maxlength="200" required></div></div><div class="field"><label for="equipment">Equipment</label><input id="equipment" name="equipment" placeholder="e.g. Brass desk lamp" maxlength="120" required></div><div class="detail-grid"><div class="field"><label for="new-category">Category</label><select id="new-category" name="category">${state.boot.categories.map(c=>`<option value="${c}">${labels[c]}</option>`).join('')}</select></div><div class="field"><label for="new-priority">Priority</label><select id="new-priority" name="priority"><option value="normal">Normal</option><option value="high">High</option></select></div></div><div class="field"><label for="description">What needs repairing?</label><textarea id="description" name="description" maxlength="2000" required></textarea></div><div class="form-actions"><button type="button" class="button" data-action="close-modal">Cancel</button><button class="button primary" type="submit">Create request</button></div></form>`);
}
function showHelp() {
  modal('A small workshop. A real workflow.',`<p>Intake Desk is a fictional community repair product created for a hiring exercise. The people, organizations, equipment records, and messages are synthetic.</p><ul><li><strong>Alex</strong> coordinates the Benchside workshop and sees all its repairs.</li><li><strong>Sam and Jules</strong> see only repairs assigned to them.</li><li><strong>Robin</strong> coordinates a separate workshop, Northstar.</li><li>Use the profile menu to explore these perspectives. This selector is demo infrastructure, not real authentication.</li><li>Every edit is saved to your local SQLite database. No external service or AI account is needed to run the app.</li><li>Messages and customer responses are explicitly simulated. No email leaves the application.</li></ul><p>To restore the original fixtures, stop the server, then run <code>python3 run.py --reset</code>. On Windows, use <code>py -3 run.py --reset</code>.</p>`);
}
async function refreshAfterChange(message) {
  const detailId=state.detail?.id;
  await load();
  if(detailId&&location.hash===`#request/${detailId}`) {
    try { await openDetail(detailId); } catch(e) { if(e.status===404){location.hash=state.view;toast('This repair is no longer visible to your profile.');return;} throw e; }
  }
  if(message) toast(message);
}
async function mutate(action,data,message) {
  const r=state.detail;
  await api(`/requests/${r.id}${action?'/'+action:''}`,action?'POST':'PATCH',{...data,version:r.version});
  await refreshAfterChange(message);
}
async function retryMessage(messageId,requestId) {
  const r=await api(`/requests/${requestId}`);
  await api(`/requests/${requestId}/retry-message`,'POST',{message_id:messageId,version:r.version});
  await refreshAfterChange('Message queued for another attempt.');
}
document.addEventListener('click',async event=>{
  const button=event.target.closest('button,[data-request]');
  if(!button)return;
  try {
    if(button.dataset.nav){location.hash=button.dataset.nav;return;}
    if(button.dataset.request){location.hash=`request/${button.dataset.request}`;return;}
    if(button.dataset.filter){state.filter=button.dataset.filter;shell();return;}
    if(button.dataset.detailTab){state.tab=button.dataset.detailTab;renderDetail();return;}
    if(button.dataset.approval){button.disabled=true;await mutate('approval',{decision:button.dataset.approval},'Simulated customer decision recorded.');return;}
    if(button.dataset.retry){button.disabled=true;await retryMessage(Number(button.dataset.retry),Number(button.dataset.requestId));return;}
    switch(button.dataset.action){
      case 'new':newRequest();break;
      case 'help':showHelp();break;
      case 'close-modal':$('#modal').close();break;
      case 'close-detail':location.hash=state.view;break;
      case 'refresh':await load();toast('Workshop refreshed.');break;
      case 'refresh-detail':await openDetail(state.detail.id);toast('Request refreshed.');break;
      case 'clear-search':state.search='';state.category='all';shell();break;
      case 'process':{
        button.disabled=true;
        const result=await api('/outbox/process','POST',{fail_first:$('#fail-first').checked});
        await refreshAfterChange(`${result.processed} queued ${result.processed===1?'message processed':'messages processed'}.`);break;
      }
    }
  } catch(error){toast(error.message,true);} finally {button.disabled=false;}
});
document.addEventListener('input',event=>{
  if(event.target.id==='search'){state.search=event.target.value;$('#request-results').innerHTML=tableContent();}
});
document.addEventListener('change',async event=>{
  const input=event.target;
  try {
    if(input.id==='category'){state.category=input.value;$('#request-results').innerHTML=tableContent();}
    if(input.id==='profile'){
      state.userId=input.value;
      try {localStorage.setItem('intake-desk-user',state.userId);} catch {}
      state.detail=null;state.filter='active';state.search='';state.category='all';
      if($('#detail').open)$('#detail').close();
      history.replaceState(null,'',`#${state.view}`);
      await load();toast(`Viewing as ${state.boot.user.name}.`);
    }
    if(input.dataset.part){input.disabled=true;await mutate('part-status',{part_id:Number(input.dataset.part),status:input.value},'Part status updated.');}
  } catch(error){toast(error.message,true);} finally {input.disabled=false;}
});
document.addEventListener('submit',async event=>{
  const form=event.target;
  if(!form.dataset.form)return;
  event.preventDefault();
  const button=form.querySelector('[type=submit]');
  if(button.disabled)return;
  button.disabled=true;
  const data=Object.fromEntries(new FormData(form));
  try {
    switch(form.dataset.form){
      case 'new':{
        const result=await api('/requests','POST',data);$('#modal').close();await load();location.hash=`request/${result.id}`;toast('Repair request created.');break;
      }
      case 'workflow':{
        const update={status:data.status,estimated_minutes:data.estimated_minutes===''?null:Number(data.estimated_minutes)};
        if(coordinator()){update.assigned_to=data.assigned_to||null;update.priority=data.priority;}
        await mutate('',update,'Workflow saved.');break;
      }
      case 'quote':await mutate('quote',{quote_cents:Math.round(Number(data.amount)*100)},'Estimate created. Customer update queued.');break;
      case 'part':await mutate('parts',{name:data.name,quantity:Number(data.quantity)},'Part added.');break;
      case 'note':await mutate('notes',{body:data.body},'Workshop note added.');break;
      case 'message':await mutate('messages',{body:data.body},'Customer update queued.');break;
    }
  } catch(error){toast(error.message,true);} finally {button.disabled=false;}
});
$('#detail').addEventListener('close',()=>{if(location.hash.startsWith('#request/'))location.hash=state.view;});
window.addEventListener('hashchange',()=>route().catch(error=>{toast(error.message,true);location.hash=state.view;}));
async function start() {
  try {
    await load();
    try { await route(); }
    catch(error) { toast(error.message,true); location.hash=state.view; }
  } catch(error){
    if(error.status===401&&state.userId!=='alex'){state.userId='alex';return start();}
    $('#app').innerHTML=`<div class="empty"><h1>Couldn’t open the workshop</h1><p>${esc(error.message)} Make sure the Python server is running, then reload this page.</p><button class="button" id="reload-page">Try again</button></div>`;
    $('#reload-page').addEventListener('click',()=>location.reload());
  }
}
start();
