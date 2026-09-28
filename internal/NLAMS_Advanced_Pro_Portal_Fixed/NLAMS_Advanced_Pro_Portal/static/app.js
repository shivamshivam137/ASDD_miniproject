async function api(u,m='GET',d=null){let o={method:m,headers:{'Content-Type':'application/json'}};if(d)o.body=JSON.stringify(d);let r=await fetch(u,o);if(!r.ok){let x={};try{x=await r.json()}catch{};toast(x.error||'Request failed','error');throw Error(x.error||'Request failed')}return r.json()}
function esc(x){return String(x??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function fmt(x){return x?new Date(x.replace(' ','T')).toLocaleString() :''}
function status(x){let c={'Active':'green','In Progress':'blue','Submitted':'orange','Approved':'green','Completed':'green','Pending':'orange','Open':'red','Resolved':'green','On Hold':'purple','Inactive':'red','Verified':'green','Approved':'green','High':'red','Medium':'orange','Low':'green'}[x]||'';return `<span class="status ${c}">${esc(x)}</span>`}
function risk(x){return status(x)}
function modal(h){document.getElementById('modalRoot').innerHTML=`<div class=modal-backdrop id=mb><div class=modal>${h}</div></div>`}
function closeModal(){document.getElementById('modalRoot').innerHTML=''}
function toast(x,c='success'){let d=document.createElement('div');d.className='toast '+c;d.textContent=x;d.style.position='fixed';d.style.right='18px';d.style.bottom='18px';d.style.zIndex=200;document.body.appendChild(d);setTimeout(()=>d.remove(),2600)}
async function openNotifs(){overlay.style.display='block';drawer.classList.add('open');let x=await api('/api/notifications');notifs.innerHTML=x.map(n=>`<div class="notification ${n.is_read?'':'unread'}" onclick="readN(${n.id})"><h4>${esc(n.title)}</h4><p>${esc(n.message)}</p><small>${fmt(n.created_at)}</small></div>`).join('');badge.textContent=x.filter(n=>!n.is_read).length}
function closeNotifs(){overlay.style.display='none';drawer.classList.remove('open')}
async function readN(id){await api('/api/notifications','PUT',{id});openNotifs()}
async function badgeLoad(){try{let x=await api('/api/notifications');badge.textContent=x.filter(n=>!n.is_read).length}catch{}}
function globalSearch(e){if(e.key==='Enter'&&e.target.value.trim()){location.href='/projects?q='+encodeURIComponent(e.target.value.trim())}}
badgeLoad();document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeModal();closeNotifs()}})