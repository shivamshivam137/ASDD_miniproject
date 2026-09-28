let rows=[];

async function init(){
  const data=await (await fetch('/api/dashboard')).json();
  rows=data.rows||[];
  navCount.textContent=rows.length;
  const high=rows.filter(x=>x.priority==='High').length;
  const open=rows.filter(x=>!['Resolved','Rejected'].includes(x.status)).length;
  const escalated=rows.filter(x=>x.status==='Escalated').length;
  const today=new Date().toISOString().slice(0,10);
  const sla=rows.filter(x=>!['Resolved','Rejected'].includes(x.status)&&x.sla_due<=today).length;
  stats.innerHTML=[['TOTAL GRIEVANCES',rows.length],['OPEN / PENDING',open],['HIGH PRIORITY',high],['OVERDUE SLA',sla]].map(x=>`<div class="card"><small>${x[0]}</small><b>${x[1]}</b></div>`).join('');
  renderHome();
  populateCategories(data.categories||[]);
  renderQueue();
  renderProjectStats(data.projects||[]);
  analyticsProjects.innerHTML=(data.projects||[]).map(x=>barRow(x.name,x.count,rows.length)).join('');
  analyticsCategories.innerHTML=(data.categories||[]).map(x=>barRow(x.category,x.count,rows.length)).join('');
}

function barRow(name,count,total){const pct=total?Math.max(8,Math.round(count/total*100)):0;return `<div class="bar-row"><span style="width:190px">${name}</span><div class="bar-bg"><div class="bar" style="width:${pct}%"></div></div><b>${count}</b></div>`}
function renderProjectStats(projects){projectStats.innerHTML=projects.slice(0,6).map(x=>`<div class="project-row"><span style="flex:1"><b>${x.name}</b><small class="muted">Project</small></span><b>${x.count}</b></div>`).join('')||'<p class="muted">No project data.</p>'}
function renderHome(){
  const priority=rows.filter(x=>x.priority==='High').slice(0,5);
  homeq.innerHTML=priority.map(g=>`<div class="project-row"><span style="flex:1"><b>${g.ticket}</b><small>${g.owner_name} · ${g.project_name} · ${g.survey_no}</small></span><span class="tag high">${g.priority}</span><a class="view-btn" href="/grievance/${g.ticket}">View</a></div>`).join('')||'<p class="muted">No high priority grievances.</p>';
}
function populateCategories(categories){categoryFilter.innerHTML='<option value="">All Categories</option>'+categories.map(x=>`<option>${x.category}</option>`).join('')}
function renderQueue(){
  const q=(searchBox?.value||'').toLowerCase(), s=statusFilter?.value||'', c=categoryFilter?.value||'';
  const filtered=rows.filter(g=>{
    const hay=[g.ticket,g.owner_name,g.project_name,g.survey_no,g.subject,g.category].join(' ').toLowerCase();
    return (!q||hay.includes(q))&&(!s||g.status===s)&&(!c||g.category===c);
  });
  qEl=document.getElementById('q');
  qEl.innerHTML=filtered.map(g=>`<tr><td><b>${g.ticket}</b><small class="muted">${g.created}</small></td><td class="owner-cell"><b>${g.owner_name}</b><small>${g.mobile} · ${g.owner_code}</small></td><td class="project-cell"><b>${g.project_name}</b><small>${g.district}</small></td><td><b>${g.survey_no}</b><small class="muted">${g.parcel_code}</small></td><td><span class="tag cat">${g.category}</span></td><td><span class="tag ${g.priority.toLowerCase()}">${g.priority}</span></td><td><span class="status-badge status-${g.status.toLowerCase().replaceAll(' ','-')}">${g.status}</span></td><td>${g.sla_due}</td><td><a class="view-btn view-primary" href="/grievance/${g.ticket}">View</a></td></tr>`).join('')||'<tr><td colspan="9" class="muted">No grievances match the selected filters.</td></tr>';
}
function page(id,button){document.querySelectorAll('main section').forEach(x=>x.classList.add('hide'));document.getElementById(id).classList.remove('hide');document.querySelectorAll('.nav').forEach(x=>x.classList.remove('active'));if(button)button.classList.add('active');window.scrollTo({top:0,behavior:'smooth'})}
async function runTriage(){let d=await (await fetch('/api/triage',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:triageText.value})})).json();triageOut.innerHTML=`<div class="result"><b>Category:</b> ${d.category}<br><b>Priority:</b> ${d.priority}<br><b>Confidence:</b> ${Math.round(d.confidence*100)}%<hr>Recommended: verify land record → GIS → notification/award → compensation → field evidence.</div>`}
async function runDocumentVerification(){let d=await (await fetch('/api/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:doc.value})})).json();vo.innerHTML=`<div class="result"><b>Confidence:</b> ${Math.round(d.confidence*100)}%<hr>${d.checks.map(x=>`<div>${x.field}: <span class="${x.status==='Verified'?'ok':'warn'}">${x.status}</span></div>`).join('')}</div>`}
async function findDuplicates(){let d=await (await fetch('/api/duplicates',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({owner:owner.value,survey_no:survey.value})})).json();du.innerHTML=`<div class="result"><b>${d.rows.length} matching grievance(s)</b><br>${d.rows.map(x=>`<a href="/grievance/${x.ticket}">${x.ticket}</a> — ${x.owner_name} — ${x.project_name} — ${x.subject} — ${x.status}`).join('<br>')||'No matching tickets found.'}</div>`}
async function generateVerificationReport(){
  const ticket=document.getElementById('rt').value.trim(), findings=document.getElementById('find').value.trim(), recommendation=document.getElementById('rec').value.trim();
  if(!ticket||!findings||!recommendation){document.getElementById('ro').innerHTML='<div class="warn">Enter the grievance ID, findings and recommendation before generating the report.</div>';return;}
  try{
    const r=await fetch('/api/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ticket,findings,recommendation})});
    const d=await r.json();
    if(!r.ok||!d.report_no)throw new Error(d.error||'Report generation failed');
    document.getElementById('ro').innerHTML=`<div class="result"><b>✓ Verification report generated</b><br>Report No: <b>${d.report_no}</b><br>Grievance: ${ticket}<br><span class="muted">The report has been stored in the audit-ready report register.</span><br><button class="primary-btn" style="margin-top:10px" onclick="window.print()">Print / Save PDF</button></div>`;
  }catch(e){document.getElementById('ro').innerHTML='<div class="warn">Unable to generate the report: '+e.message+'</div>';}
}

async function loadDetail(){
  const data=await (await fetch('/api/grievance/'+encodeURIComponent(window.TICKET))).json();
  const g=data.grievance;
  document.getElementById('actionStatus').value=g.status;
  document.getElementById('actionPriority').value=g.priority;
  const cats=[...document.getElementById('actionCategory').options].map(o=>o.value); if(cats.includes(g.category))document.getElementById('actionCategory').value=g.category;
  document.getElementById('actionRemarks').value=g.remarks||'';
  document.getElementById('actionResponse').value=g.officer_response||'';
  document.getElementById('detailDocs').innerHTML=data.documents.map(d=>`<div class="doc-item"><span>▤ <b>${d.name}</b><small class="muted"> · ${d.doc_type} · ${d.uploaded}</small></span><span class="${d.verification==='Verified'?'ok':'warn'}">${d.verification}</span></div>`).join('')||'<p class="muted">No evidence documents uploaded.</p>';
  document.getElementById('timeline').innerHTML=data.events.map(e=>`<div class="event"><div class="event-title">${e.status}</div><div class="event-meta">${e.created} · ${e.actor}</div><div class="event-note">${e.note||''}</div></div>`).join('')||'<p class="muted">No timeline events yet.</p>';
}
async function saveAction(ev){
  ev.preventDefault();
  const payload={ticket:window.TICKET,status:actionStatus.value,priority:actionPriority.value,category:actionCategory.value,remarks:actionRemarks.value,response:actionResponse.value};
  const r=await fetch('/api/grievance/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}); const d=await r.json();
  if(d.ok){saveOut.innerHTML='<div class="save">✓ Officer action saved. Timeline and audit trail updated.</div>';setTimeout(()=>location.reload(),900)}else saveOut.innerHTML='<div class="warn">Unable to save action.</div>';
}

if(document.getElementById('stats')) init();
if(window.TICKET) loadDetail();
