
function openModal(id){document.getElementById(id).classList.add('show')}
function closeModal(id){document.getElementById(id).classList.remove('show')}
function filterTable(inputId, tableId){
 const q=document.getElementById(inputId).value.toLowerCase();
 document.querySelectorAll('#'+tableId+' tbody tr').forEach(r=>r.style.display=r.innerText.toLowerCase().includes(q)?'':'none');
}
function toast(msg){
 const el=document.createElement('div'); el.className='toast'; el.textContent=msg; document.body.appendChild(el);
 setTimeout(()=>el.remove(),2800);
}
function validateUpload(input){
 const file=input.files[0]; if(!file)return;
 if(file.size>10*1024*1024){toast('File exceeds 10 MB demo limit');input.value='';return}
 toast('File selected: '+file.name);
}
document.addEventListener('DOMContentLoaded',()=>{
 document.querySelectorAll('.parcel').forEach(p=>p.addEventListener('click',()=>{
   document.getElementById('parcelInfo').innerHTML='<b>Survey/Gat:</b> '+p.dataset.survey+'<br><b>Village:</b> '+p.dataset.village+'<br><b>Owner:</b> '+p.dataset.owner+'<br><b>Area:</b> '+p.dataset.area+' Ha<br><b>Status:</b> '+p.dataset.status;
   openModal('parcelModal');
 }));
});
