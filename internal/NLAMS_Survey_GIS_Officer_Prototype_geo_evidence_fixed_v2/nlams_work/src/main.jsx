import React, {useEffect, useMemo, useState} from "react";
import {createRoot} from "react-dom/client";
import {MapContainer, TileLayer, Polygon, Marker, Popup, useMap, CircleMarker, Polyline} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import {
  LayoutDashboard, FolderKanban, Map, MapPinned, Boxes, AlertTriangle,
  ClipboardCheck, FileText, BarChart3, Bell, History, User, Settings,
  LogOut, Search, Menu, X, LocateFixed, Layers, Camera, Upload, CheckCircle2,
  Clock3, Navigation, ShieldCheck, ChevronRight, RefreshCw, Download,
  Eye, Send, Ruler, MapPin, CircleAlert, Smartphone, LockKeyhole, Trash2, FileImage, FileArchive
} from "lucide-react";
import "./styles.css";

const projects = [{id:"NH44-MH-001", name:"NH-44 Highway Expansion", type:"Highway", district:"Pune", area:100, parcels:3, surveyed:0, verified:0, status:"Revenue Verification"}];

const parcels = [
  {id:"P-001", project:"NH44-MH-001", survey:"125", village:"Pimpalgaon", taluka:"Pune", area:2.5, measured:2.5, lat:18.5204, lng:73.8567, landUse:"Agricultural", status:"Revenue Verification Pending", boundary:"Pending", gps:"Available", owner:"Demo Owner A"},
  {id:"P-002", project:"NH44-MH-001", survey:"126", village:"Pimpalgaon", taluka:"Pune", area:3.0, measured:3.0, lat:18.5230, lng:73.8590, landUse:"Agricultural", status:"Revenue Verification Pending", boundary:"Pending", gps:"Available", owner:"Demo Owner B"},
  {id:"P-003", project:"NH44-MH-001", survey:"128", village:"Wagholi", taluka:"Pune", area:1.8, measured:1.8, lat:18.5750, lng:73.9850, landUse:"Agricultural", status:"Revenue Verification Pending", boundary:"Pending", gps:"Available", owner:"Demo Owner C"}
];

const requests = [
  {id:"REQ-1025", parcel:"P-MH-RGD-00127", project:"NLAMS-001", priority:"High", deadline:"10 Sep 2026", text:"Please verify the disputed boundary and submit updated GPS evidence."},
  {id:"REQ-1026", parcel:"P-MH-RGD-00130", project:"NLAMS-001", priority:"Medium", deadline:"12 Sep 2026", text:"Please validate the measured area and upload field photographs."},
  {id:"REQ-1027", parcel:"P-MH-RGD-00126", project:"NLAMS-001", priority:"Normal", deadline:"14 Sep 2026", text:"Complete initial field survey for the assigned parcel."}
];

const notifications = [
  ["LAO requested re-survey for Parcel P-MH-RGD-00127.","High","2h ago"],
  ["5 surveys are due within 48 hours.","Medium","4h ago"],
  ["Parcel P-MH-RGD-00125 verification approved.","Success","Yesterday"],
  ["New field survey assigned in NLAMS-001.","Info","Yesterday"]
];

function statusClass(s){ return s.toLowerCase().replaceAll(" ","-").replaceAll("/","-"); }

function App(){
  const [page,setPage] = useState("dashboard");
  const [mobile,setMobile] = useState(false);
  const [selected,setSelected] = useState(parcels[0]);
  const [sharedParcels,setSharedParcels] = useState(parcels);
  useEffect(()=>{fetch("http://127.0.0.1:8090/api/parcels/shared?project_id=NH44-MH-001",{cache:"no-store"}).then(r=>r.json()).then(rows=>{if(rows?.length){const mapped=rows.map(x=>({...x,id:x.parcel_id,project:x.project_id,survey:x.survey_no,village:x.village,area:x.area,measured:x.area,lat:x.lat,lng:x.lng,landUse:"Agricultural",owner:x.landowner_id,status:x.status,boundary:x.gis_status,gps:"Available"}));setSharedParcels(mapped);setSelected(mapped[0]);}}).catch(()=>{});},[]);
  const [search,setSearch] = useState("");
  const [surveyParcel,setSurveyParcel] = useState(null);
  const [toast,setToast] = useState("");
  const [showLayers,setShowLayers] = useState(true);
  const [documents,setDocuments] = useState([
    {id:"seed-1",name:"Survey_Report_P00125.pdf",category:"Survey Reports",type:"PDF",size:"2.4 MB",uploadedBy:"Rajesh Patil",uploadedOn:"05 Sep 2026, 14:20",version:2},
    {id:"seed-2",name:"Cadastral_Map_P00125.pdf",category:"Cadastral Maps",type:"PDF",size:"3.8 MB",uploadedBy:"Rajesh Patil",uploadedOn:"04 Sep 2026, 14:18",version:1},
    {id:"seed-3",name:"Boundary_Evidence_P00127.jpg",category:"Evidence",type:"Image",size:"1.6 MB",uploadedBy:"Rajesh Patil",uploadedOn:"03 Sep 2026, 14:15",version:2},
    {id:"seed-4",name:"Measurement_Sheet_P00130.pdf",category:"Survey Reports",type:"PDF",size:"1.2 MB",uploadedBy:"Rajesh Patil",uploadedOn:"02 Sep 2026, 14:10",version:1},
    {id:"seed-5",name:"Field_Inspection_Report_NLAMS001.pdf",category:"Evidence",type:"PDF",size:"856 KB",uploadedBy:"Rajesh Patil",uploadedOn:"01 Sep 2026, 14:05",version:2}
  ]);

  const notify=(msg)=>{setToast(msg); setTimeout(()=>setToast(""),2600)};

  const go=(p)=>{setPage(p); setMobile(false); window.scrollTo(0,0)};

  const filtered = useMemo(()=>parcels.filter(p =>
    Object.values(p).join(" ").toLowerCase().includes(search.toLowerCase())
  ),[search]);

  return <div className="app">
    <aside className={"sidebar "+(mobile?"mobile-open":"")}>
      <div className="brand">
        <div className="brand-mark">N</div>
        <div><strong>NLAMS</strong><span>Land Management System</span></div>
        {mobile && <button className="icon-btn close" onClick={()=>setMobile(false)}><X/></button>}
      </div>
      <div className="role-card">
        <div className="avatar">RP</div><div><b>Rajesh Patil</b><small>Survey / GIS Officer</small></div>
      </div>
      <nav>
        <Nav icon={<LayoutDashboard/>} label="Dashboard" active={page==="dashboard"} onClick={()=>go("dashboard")}/>
        <Nav icon={<FolderKanban/>} label="My Projects" active={page==="projects"} onClick={()=>go("projects")}/>
        <Nav icon={<Map/>} label="GIS Map" active={page==="gis"} onClick={()=>go("gis")}/>
        <Nav icon={<MapPinned/>} label="Field Survey" active={page==="survey"} onClick={()=>go("survey")}/>
        <Nav icon={<Boxes/>} label="Parcel Management" active={page==="parcels"} onClick={()=>go("parcels")}/>
        <Nav icon={<AlertTriangle/>} label="Discrepancies" active={page==="discrepancies"} onClick={()=>go("discrepancies")}/>
        <Nav icon={<ClipboardCheck/>} label="Verification Requests" active={page==="requests"} onClick={()=>go("requests")} badge="3"/>
        <Nav icon={<FileText/>} label="Documents" active={page==="documents"} onClick={()=>go("documents")}/>
        <Nav icon={<BarChart3/>} label="Reports" active={page==="reports"} onClick={()=>go("reports")}/>
        <Nav icon={<Bell/>} label="Notifications" active={page==="notifications"} onClick={()=>go("notifications")} badge="4"/>
        <Nav icon={<History/>} label="Activity History" active={page==="history"} onClick={()=>go("history")}/>
        <Nav icon={<User/>} label="Profile" active={page==="profile"} onClick={()=>go("profile")}/>
        <Nav icon={<Settings/>} label="Settings" active={page==="settings"} onClick={()=>go("settings")}/>
      </nav>
      <div className="sidebar-bottom">
        <div className="secure"><LockKeyhole size={14}/> Secure Session</div>
        <button className="logout" onClick={()=>notify("Demo logout — session kept active for prototype.")}><LogOut size={17}/> Logout</button>
      </div>
    </aside>

    <main className="main">
      <header className="topbar">
        <button className="menu-btn" onClick={()=>setMobile(true)}><Menu/></button>
        <div className="crumb">NLAMS <span>/</span> Survey & GIS Officer</div>
        <div className="top-actions">
          <div className="global-search"><Search size={17}/><input placeholder="Search project, parcel, survey no..." value={search} onChange={e=>setSearch(e.target.value)}/></div>
          <button className="icon-btn" onClick={()=>go("notifications")}><Bell size={19}/><i>4</i></button>
          <div className="top-user"><div className="avatar small">RP</div><div><b>Rajesh Patil</b><small>GIS-1025</small></div></div>
        </div>
      </header>

      <div className="content">
        {page==="dashboard" && <Dashboard go={go} parcels={sharedParcels} notify={notify} onSelect={(p)=>{setSelected(p);go("parcel-details")}}/>}
        {page==="projects" && <Projects go={go}/>}
        {page==="gis" && <GIS parcels={sharedParcels.filter(p => Object.values(p).join(" ").toLowerCase().includes(search.toLowerCase()))} selected={selected} setSelected={setSelected} showLayers={showLayers} setShowLayers={setShowLayers} go={go}/>}
        {page==="survey" && <Survey parcel={surveyParcel || selected} setSurveyParcel={setSurveyParcel} notify={notify} go={go} onDocumentAdded={doc=>setDocuments(prev=>[doc,...prev])}/>}
        {page==="parcels" && <Parcels data={sharedParcels.filter(p => Object.values(p).join(" ").toLowerCase().includes(search.toLowerCase()))} go={go} setSelected={setSelected}/>}
        {page==="parcel-details" && <ParcelDetails parcel={selected} go={go} notify={notify}/>}
        {page==="discrepancies" && <Discrepancies data={parcels.filter(p=>p.status==="Discrepancy"||p.status==="Re-Survey Required"||p.boundary==="Discrepancy")} go={go} notify={notify}/>}
        {page==="requests" && <Requests go={go} setSurveyParcel={setSurveyParcel}/>}
        {page==="documents" && <Documents notify={notify} documents={documents} setDocuments={setDocuments}/>}
        {page==="reports" && <Reports notify={notify}/>}
        {page==="notifications" && <Notifications notify={notify}/>}
        {page==="history" && <HistoryPage/>}
        {page==="profile" && <Profile/>}
        {page==="settings" && <SettingsPage notify={notify}/>}
      </div>
    </main>
    {toast && <div className="toast"><CheckCircle2 size={18}/>{toast}</div>}
    {page==="survey" && <SharedCasePanel parcel={surveyParcel || selected}/>}
    <WorkflowDock/>
  </div>
}

function Nav({icon,label,active,onClick,badge}){return <button className={"nav-item "+(active?"active":"")} onClick={onClick}>{icon}<span>{label}</span>{badge&&<b className="nav-badge">{badge}</b>}</button>}

function PageHeader({eyebrow,title,desc,actions}){return <div className="page-head"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{desc&&<p>{desc}</p>}</div><div className="head-actions">{actions}</div></div>}

function Dashboard({go,parcels,notify,onSelect}){
 const total=parcels.length, surveyed=parcels.filter(p=>p.status!=="Pending").length, verified=parcels.filter(p=>p.status==="Verified").length;
 return <><PageHeader eyebrow="Sunday, 06 September 2026" title="Good afternoon, Rajesh" desc="Survey & GIS Officer · Raigad District" actions={<><button className="btn secondary" onClick={()=>go("gis")}><Map size={16}/> Open GIS Map</button><button className="btn primary" onClick={()=>go("survey")}><MapPinned size={16}/> Start Field Survey</button></>}/>
 <div className="kpis">
   <Kpi icon={<FolderKanban/>} label="Assigned Projects" value="12" note="3 high priority"/>
   <Kpi icon={<Clock3/>} label="Pending Surveys" value="28" note="5 due in 48 hours"/>
   <Kpi icon={<CheckCircle2/>} label="Verified Parcels" value="145" note="+12 this week" good/>
   <Kpi icon={<AlertTriangle/>} label="Re-Survey Required" value="7" note="2 high priority" warn/>
   <Kpi icon={<Ruler/>} label="Surveyed Area" value="486.72 ha" note="86% of assigned"/>
   <Kpi icon={<ShieldCheck/>} label="Verification Accuracy" value="96%" note="Last 30 days" good/>

 </div>
 <section className="panel survey-dashboard-panel">
   <div className="panel-title"><div><h3>Survey / GIS Dashboard</h3><p>Field workload and verification status</p></div><span className="mini-status">Today</span></div>
   <div className="dashboard-metrics">
     <Kpi icon={<Boxes/>} label="Total Assigned Parcels" value={parcels.length} note="Current officer workload"/>
     <Kpi icon={<CheckCircle2/>} label="Surveys Completed" value={parcels.filter(p=>p.status!=="Pending").length} note="Field surveys recorded" good/>
     <Kpi icon={<Clock3/>} label="Pending Surveys" value={parcels.filter(p=>p.status==="Pending").length} note="Awaiting field survey" warn/>
     <Kpi icon={<ShieldCheck/>} label="Verified Parcels" value={parcels.filter(p=>p.status==="Verified").length} note="Verification complete" good/>
     <Kpi icon={<AlertTriangle/>} label="Discrepancies" value={parcels.filter(p=>p.status==="Discrepancy"||p.boundary==="Discrepancy"||p.status==="Re-Survey Required").length} note="Needs correction" warn/>
     <Kpi icon={<MapPinned/>} label="Today's Surveys" value="6" note="Field activity today"/>
   </div>
 </section>
 <div className="grid-2 dashboard-grid">
   <section className="panel progress-panel">
     <div className="panel-title"><div><h3>Survey Progress</h3><p>Current assigned workload</p></div><span className="mini-status">86% complete</span></div>
     <div className="progress-ring"><div><strong>86%</strong><span>surveyed</span></div></div>
     <div className="legend-row"><Legend dot="blue" label="Surveyed" value="215"/><Legend dot="green" label="Verified" value="190"/><Legend dot="amber" label="Pending" value="35"/><Legend dot="red" label="Re-survey" value="25"/></div>
   </section>
   <section className="panel">
     <div className="panel-title"><div><h3>Project Survey Progress</h3><p>Assigned projects</p></div><button className="text-btn" onClick={()=>go("projects")}>View all <ChevronRight size={15}/></button></div>
     <div className="bars">{projects.map(p=><div className="bar-row" key={p.id}><div><span>{p.name}</span><b>{Math.round(p.surveyed/p.parcels*100)}%</b></div><div className="bar"><i style={{width:(p.surveyed/p.parcels*100)+"%"}}/></div></div>)}</div>
   </section>
 </div>
 <section className="panel map-preview">
   <div className="panel-title"><div><h3>Active Survey Area</h3><p>Interactive parcel overview · Panvel, Raigad</p></div><div className="map-actions"><span className="map-live"><i/> Live GIS</span><button className="btn secondary small" onClick={()=>go("gis")}>Open full map <ChevronRight size={14}/></button></div></div>
   <div className="map-wrap compact"><MiniMap parcels={parcels} onSelect={onSelect}/></div>
 </section>
 <div className="grid-2">
   <section className="panel"><div className="panel-title"><div><h3>Priority Tasks</h3><p>Actions requiring attention</p></div></div>
    <div className="task-list">
      <Task icon={<AlertTriangle/>} title="Re-survey Parcel P-MH-RGD-00127" text="LAO requested boundary verification." action="Start Survey" onClick={()=>go("survey")} danger/>
      <Task icon={<Clock3/>} title="5 surveys due within 48 hours" text="Prioritize pending field visits." action="View Tasks" onClick={()=>go("parcels")}/>
      <Task icon={<CheckCircle2/>} title="Parcel P-MH-RGD-00125 ready for review" text="All evidence has been uploaded." action="Review" onClick={()=>onSelect(parcels[0])} success/>
    </div>
   </section>
   <section className="panel"><div className="panel-title"><div><h3>Recent Field Activity</h3><p>Latest actions</p></div><button className="text-btn" onClick={()=>go("history")}>View history <ChevronRight size={15}/></button></div>
    <Timeline compact/>
   </section>
 </div>
 </>;
}
function Kpi({icon,label,value,note,good,warn}){return <div className="kpi"><div className={"kpi-icon "+(good?"good":"")+(warn?" warn":"")}>{icon}</div><div><span>{label}</span><strong>{value}</strong><small>{note}</small></div></div>}
function Legend({dot,label,value}){return <div className="legend"><i className={dot}/><span>{label}</span><b>{value}</b></div>}
function Task({icon,title,text,action,onClick,danger,success}){return <div className="task"><div className={"task-icon "+(danger?"danger":"")+(success?" success":"")}>{icon}</div><div className="task-copy"><b>{title}</b><span>{text}</span></div><button className="text-btn" onClick={onClick}>{action}<ChevronRight size={14}/></button></div>}

function Projects({go}){
 return <><PageHeader eyebrow="Work allocation" title="My Assigned Projects" desc="Projects currently assigned to your Survey/GIS team." actions={<button className="btn primary" onClick={()=>go("gis")}><Map/> GIS Workspace</button>}/>
 <section className="panel"><div className="toolbar"><div className="filter-chip active">All Projects · 12</div><div className="filter-chip">In Progress · 9</div><div className="filter-chip">High Priority · 3</div><div className="toolbar-spacer"/><button className="btn secondary small"><Download size={15}/> Export</button></div>
 <div className="table-scroll"><table><thead><tr><th>Project</th><th>Type</th><th>District</th><th>Area</th><th>Parcels</th><th>Surveyed</th><th>Verified</th><th>Progress</th><th>Status</th><th/></tr></thead><tbody>{projects.map(p=><tr key={p.id}><td><b>{p.id}</b><span className="cell-sub">{p.name}</span></td><td>{p.type}</td><td>{p.district}</td><td>{p.area} ha</td><td>{p.parcels}</td><td>{p.surveyed}</td><td>{p.verified}</td><td><div className="table-progress"><i style={{width:(p.surveyed/p.parcels*100)+"%"}}/></div><small>{Math.round(p.surveyed/p.parcels*100)}%</small></td><td><Badge text={p.status}/></td><td><button className="icon-btn" onClick={()=>go("gis")}><Eye size={16}/></button></td></tr>)}</tbody></table></div></section></>
}

function GIS({parcels,selected,setSelected,showLayers,setShowLayers,go}){
 const [tracking,setTracking]=useState(false);
 return <><PageHeader eyebrow="Live geospatial workspace" title="GIS Map & Live Field Tracking" desc="Real OpenStreetMap basemap, parcel geometry and browser GPS tracking." actions={<><button className={"btn "+(tracking?"primary":"secondary")} onClick={()=>setTracking(v=>!v)}><LocateFixed/> {tracking?"Stop Live Tracking":"Start Live Tracking"}</button><button className="btn secondary" onClick={()=>setShowLayers(!showLayers)}><Layers/> Layers</button><button className="btn primary" onClick={()=>go("survey")}><MapPinned/> Field Survey</button></>}/>
 <div className="gis-workspace">
   <aside className="layer-panel">
    <div className="side-head"><b>Map Layers</b><span>10 layers</span></div>
    {["Project Boundary","Land Parcels","Surveyed Parcels","Verified Parcels","Pending Parcels","Re-Survey Parcels","Acquired Parcels","Village Boundary","Roads","Water Bodies"].map((x,i)=><label className="layer-row" key={x}><input type="checkbox" defaultChecked={i<6}/><span className={"layer-symbol s"+i}/>{x}</label>)}
    <div className="map-legend"><b>Parcel Status</b><Legend dot="green" label="Verified" value=""/><Legend dot="amber" label="Pending" value=""/><Legend dot="red" label="Discrepancy" value=""/><Legend dot="blue" label="In progress" value=""/></div>
   </aside>
   <div className="large-map"><LiveGISMap parcels={parcels} selected={selected} setSelected={setSelected} tracking={tracking}/><div className="map-tools"><button><LocateFixed/></button><button><Layers/></button><button>+</button><button>−</button></div><div className="map-scale">© OpenStreetMap contributors</div></div>
   <aside className="parcel-side">{selected?<ParcelPanel parcel={selected} go={go}/>:<div className="empty-side"><MapPin/><b>Select a parcel</b><span>Click a parcel on the map to view its details.</span></div>}</aside>
 </div></>
}

function LiveGISMap({parcels,selected,setSelected,tracking}){
 const [pos,setPos]=useState(null); const [trail,setTrail]=useState([]); const [error,setError]=useState("");
 useEffect(()=>{ if(!tracking){setError("");return;} if(!navigator.geolocation){setError("Browser GPS is not supported.");return;} const id=navigator.geolocation.watchPosition(p=>{const x=[p.coords.latitude,p.coords.longitude]; setPos({lat:x[0],lng:x[1],accuracy:p.coords.accuracy,at:new Date(p.timestamp||Date.now())}); setTrail(t=>[...t.slice(-49),x]); fetch("http://127.0.0.1:8090/api/locations",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({actor_role:"survey_gis_officer",actor_name:"Rajesh Patil",project_id:"NH44-MH-001",parcel_id:selected?.id||"",lat:x[0],lng:x[1],accuracy:p.coords.accuracy,captured_at:new Date(p.timestamp||Date.now()).toISOString(),source:"browser-live-tracking"})}).catch(()=>{});},e=>setError(e.code===1?"Location permission denied. Allow location access in the browser.":"Unable to read GPS location."),{enableHighAccuracy:true,maximumAge:3000,timeout:15000}); return()=>navigator.geolocation.clearWatch(id);},[tracking,selected?.id]);
 const center=selected?[selected.lat,selected.lng]:(pos?[pos.lat,pos.lng]:[18.5204,73.8567]);
 return <MapContainer center={center} zoom={14} scrollWheelZoom className="leaflet-map"><TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>{parcels.map((p,i)=>{const d=.0014+(i%3)*.00025;const pts=[[p.lat-d,p.lng-d],[p.lat-d,p.lng+d],[p.lat+d,p.lng+d],[p.lat+d,p.lng-d]];return <Polygon key={p.id} positions={pts} pathOptions={{color:selected?.id===p.id?"#111827":"#3d78b8",fillOpacity:(selected?.id===p.id)?.42:.18,weight:selected?.id===p.id?3:1.5}} eventHandlers={{click:()=>setSelected(p)}}><Popup><b>{p.id}</b><br/>Survey No. {p.survey}<br/>{p.village}<br/>{p.area} ha</Popup></Polygon>})}{pos&&<><CircleMarker center={[pos.lat,pos.lng]} radius={9} pathOptions={{color:"#d22",fillOpacity:.8}}><Popup><b>LIVE GPS</b><br/>{pos.lat.toFixed(6)}, {pos.lng.toFixed(6)}<br/>Accuracy ±{Math.round(pos.accuracy)} m<br/>{pos.at.toLocaleTimeString()}</Popup></CircleMarker><Polyline positions={trail} pathOptions={{color:"#d22",weight:4}}/></>}<LiveMapStatus tracking={tracking} pos={pos} error={error}/></MapContainer>
}
function LiveMapStatus({tracking,pos,error}){return <div className="live-map-status"><b>{tracking?"● LIVE GPS TRACKING":"GIS MAP"}</b>{pos&&<span>±{Math.round(pos.accuracy)} m · {pos.lat.toFixed(5)}, {pos.lng.toFixed(5)}</span>}{error&&<span className="gps-error">{error}</span>}</div>}

function MapCanvas({parcels,selected,setSelected}) {
 const center=[18.9894,73.1175];
 return <MapContainer center={center} zoom={13} scrollWheelZoom={true} className="leaflet-map">
   <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
   {parcels.map((p,i)=>{
     const d=.0014+(i%3)*.00025;
     const pts=[[p.lat-d,p.lng-d],[p.lat-d,p.lng+d],[p.lat+d,p.lng+d],[p.lat+d,p.lng-d]];
     const fill=p.status==="Verified"?"#2e9b68":(p.status==="Pending"?"#d29a27":(p.status==="Discrepancy"||p.status==="Re-Survey Required"?"#d95b58":"#3d78b8"));
     return <Polygon key={p.id} positions={pts} pathOptions={{color:fill,fillColor:fill,fillOpacity:selected?.id===p.id?0.5:0.22,weight:selected?.id===p.id?3:1.5}} eventHandlers={{click:()=>setSelected(p)}}><Popup><b>{p.id}</b><br/>Survey No. {p.survey}<br/>{p.area} ha<br/><b>{p.status}</b></Popup></Polygon>
   })}
 </MapContainer>
}
function MiniMap({parcels,onSelect}){return <MapContainer center={[18.9894,73.1175]} zoom={13} scrollWheelZoom={false} dragging={false} className="leaflet-map"><TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>{parcels.slice(0,7).map((p,i)=>{const d=.0013; const pts=[[p.lat-d,p.lng-d],[p.lat-d,p.lng+d],[p.lat+d,p.lng+d],[p.lat+d,p.lng-d]];return <Polygon key={p.id} positions={pts} pathOptions={{color:p.status==="Verified"?"#2e9b68":p.status==="Pending"?"#d29a27":p.status.includes("Re-Survey")||p.status==="Discrepancy"?"#d95b58":"#3d78b8",fillOpacity:.35}} eventHandlers={{click:()=>onSelect(p)}}/>})}</MapContainer>}

function ParcelPanel({parcel,go}){return <div><div className="selected-head"><div><span>SELECTED PARCEL</span><h3>{parcel.id}</h3></div><Badge text={parcel.status}/></div><div className="parcel-summary"><Info label="Survey Number" value={parcel.survey}/><Info label="Village" value={parcel.village}/><Info label="Area" value={parcel.area+" ha"}/><Info label="Land Use" value={parcel.landUse}/><Info label="Boundary" value={parcel.boundary}/><Info label="GPS" value={parcel.gps}/></div><div className="coords"><Navigation size={15}/><span>{parcel.lat.toFixed(4)}, {parcel.lng.toFixed(4)}</span><b>±4 m</b></div><div className="side-actions"><button className="btn primary full" onClick={()=>go("parcel-details")}>View Parcel Details</button><button className="btn secondary full" onClick={()=>go("survey")}><MapPinned/> Start Field Survey</button></div></div>}
function Info({label,value}){return <div><span>{label}</span><b>{value}</b></div>}
function Badge({text}){return <span className={"badge "+statusClass(text)}>{text}</span>}

function Parcels({data,go,setSelected}){
 return <><PageHeader eyebrow="Land inventory" title="Parcel Management" desc="Search, verify and monitor land parcels assigned to your projects." actions={<button className="btn primary" onClick={()=>go("survey")}><MapPinned/> Start Survey</button>}/>
 <section className="panel"><div className="toolbar"><div className="search-local"><Search size={16}/><input placeholder="Search parcel, survey no., village..." /></div><select><option>All Statuses</option><option>Verified</option><option>Pending</option><option>Discrepancy</option></select><select><option>All Projects</option><option>NLAMS-001</option></select><div className="toolbar-spacer"/><button className="btn secondary small"><Download size={15}/> Export</button></div>
 <div className="table-scroll"><table><thead><tr><th>Parcel</th><th>Survey No.</th><th>Village</th><th>Area</th><th>Land Use</th><th>Survey</th><th>Boundary</th><th>GPS</th><th>Action</th></tr></thead><tbody>{data.map(p=><tr key={p.id}><td><b>{p.id}</b><span className="cell-sub">{p.project}</span></td><td>{p.survey}</td><td>{p.village}</td><td>{p.area} ha</td><td>{p.landUse}</td><td><Badge text={p.status}/></td><td><Badge text={p.boundary}/></td><td><span className="gps-ok"><Navigation size={14}/> Available</span></td><td><button className="icon-btn" onClick={()=>{setSelected(p);go("parcel-details")}}><Eye size={16}/></button></td></tr>)}</tbody></table></div></section></>
}

function ParcelDetails({parcel,go,notify}){
 const diff=Math.abs(parcel.area-parcel.measured), pct=(diff/parcel.area*100).toFixed(2);
 const [checks,setChecks]=useState({ownership:false,gps:true,boundary:parcel.boundary==="Verified",area:pct<=5});
 const [decision,setDecision]=useState("Verified");
 const [remarks,setRemarks]=useState("");
 const [verifiedAt,setVerifiedAt]=useState("");
 const toggle=k=>setChecks(v=>({...v,[k]:!v[k]}));
 const verify=()=>{
   const now=new Date().toLocaleString();
   setVerifiedAt(now);
   notify(`Parcel marked ${decision}. Verification recorded.`);
 };
 return <><PageHeader eyebrow="Parcel profile" title={parcel.id} desc={`Survey No. ${parcel.survey} · ${parcel.village}, ${parcel.taluka}`} actions={<><button className="btn secondary" onClick={()=>go("gis")}><Map/> View on Map</button><button className="btn primary" onClick={()=>go("survey")}><MapPinned/> Edit / Survey</button></>}/>
 <div className="detail-grid"><section className="panel"><div className="detail-status"><div><span>Current Status</span><h3>{parcel.status}</h3></div><Badge text={parcel.status}/></div><div className="detail-section"><h4>Land Information</h4><div className="info-grid"><Info label="Survey Number" value={parcel.survey}/><Info label="Village" value={parcel.village}/><Info label="Taluka" value={parcel.taluka}/><Info label="District" value="Raigad"/><Info label="State" value="Maharashtra"/><Info label="Cadastral Area" value={parcel.area+" ha"}/><Info label="Land Use" value={parcel.landUse}/><Info label="Current Land Use" value={parcel.landUse}/></div></div><div className="detail-section"><h4>GIS & Measurement Verification</h4><div className="compare-grid"><div><span>Cadastral Area</span><strong>{parcel.area} ha</strong></div><div><span>GPS Measured Area</span><strong>{parcel.measured} ha</strong></div><div className={pct>5?"danger-text":""}><span>Difference</span><strong>{diff.toFixed(2)} ha ({pct}%)</strong></div></div>{pct>5?<div className="alert danger"><AlertTriangle/><div><b>Area discrepancy detected</b><span>Measured area differs significantly from cadastral records. Re-survey recommended.</span></div></div>:<div className="alert success"><CheckCircle2/><div><b>Measurement within tolerance</b><span>GPS measurement is consistent with recorded cadastral area.</span></div></div>}</div>
 <div className="detail-section"><h4>Field Verification</h4><div className="verification-checks">
 {[
  ["ownership","Ownership / land details verified"],
  ["gps","GPS location verified"],
  ["boundary","Boundary verified"],
  ["area","Area verified"]
 ].map(([key,label])=><label className="verify-check" key={key}><input type="checkbox" checked={checks[key]} onChange={()=>toggle(key)}/><span>{label}</span></label>)}</div>
 <div className="verification-decision"><label>Verification Decision<select value={decision} onChange={e=>setDecision(e.target.value)}><option>Verified</option><option>Needs Correction</option><option>Rejected</option></select></label>
 <label>Officer Remarks<textarea value={remarks} onChange={e=>setRemarks(e.target.value)} placeholder="Add verification remarks..."/></label></div>
 <button className="btn primary" onClick={verify}><ClipboardCheck/> Record Verification</button>{verifiedAt&&<div className="verification-record"><CheckCircle2/><span><b>{decision}</b> · Verified {verifiedAt}</span></div>}</div></section>
 <section className="panel"><h3>Survey Information</h3><div className="info-stack"><Info label="Survey Date" value="05 September 2026"/><Info label="Survey Officer" value="Rajesh Patil"/><Info label="GPS Accuracy" value="±4 meters"/><Info label="Boundary Status" value={parcel.boundary}/><Info label="Evidence Files" value="6 files"/></div><hr/><h4>Geo-tagged Evidence</h4><div className="demo-banner">DEMO / SAMPLE FIELD EVIDENCE · Shared with LAO & Admin</div><div className="photo-grid"><div><img src="http://127.0.0.1:8090/demo-assets/P001_Field_Photo_01.jpg" alt="DEMO field evidence"/><span>Photo 01 · DEMO</span></div><div><img src="http://127.0.0.1:8090/demo-assets/P001_Field_Photo_02.jpg" alt="DEMO field evidence"/><span>Photo 02 · DEMO</span></div><div><MapPin/><span>GPS 18.5204, 73.8567</span></div><div><FileText/><span>Survey Report · DEMO</span></div></div><button className="btn primary full" onClick={()=>notify("Verification submitted to LAO.")}><Send/> Submit Verification</button></section></div></>
}

function syncNLAMSGPS(location, parcel){
  fetch("http://127.0.0.1:8090/api/locations",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({actor_role:"survey_gis_officer",actor_name:"Rajesh Patil",project_id:parcel?.project||"NLAMS-001",parcel_id:parcel?.id||"",lat:location.lat,lng:location.lng,accuracy:location.accuracy,captured_at:location.timestamp.toISOString(),source:"browser-geolocation"})}).catch(()=>{});
}

function SharedCasePanel({parcel}){
 const [data,setData]=useState(null);
 useEffect(()=>{if(!parcel?.id)return;fetch("http://127.0.0.1:8090/api/case/"+encodeURIComponent(parcel.id),{cache:"no-store"}).then(r=>r.json()).then(setData).catch(()=>{});},[parcel?.id]);
 if(!data)return null;
 return <section className="panel" style={{marginTop:18}}><div className="panel-title"><div><h3>Shared Digital Case File</h3><p>One authoritative record · {data.project.project_id} → {data.parcel.parcel_id} → {data.landowner.landowner_id}</p></div><span className="mini-status">CONNECTED</span></div><div className="info-grid"><Info label="Project" value={data.project.name}/><Info label="Parcel" value={data.parcel.parcel_id}/><Info label="Survey / Gat" value={data.parcel.survey_no}/><Info label="Landowner" value={data.landowner.name}/><Info label="Area" value={data.parcel.area+" acres"}/><Info label="Workflow" value={data.parcel.workflow_status}/></div><div style={{marginTop:14}}><b>Shared documents: {data.documents.length}</b> · <b>GIS evidence: {data.evidence.length}</b><div className="demo-banner" style={{marginTop:8}}>Every authorized portal reads this same project/parcel record. Evidence is synthetic/demo only.</div></div></section>
}

function WorkflowDock(){
 const [items,setItems]=useState([]); const [open,setOpen]=useState(false);
 const load=()=>fetch("http://127.0.0.1:8090/api/inbox/survey_gis_officer").then(r=>r.json()).then(setItems).catch(()=>setItems([]));
 useEffect(()=>{load(); const t=setInterval(load,10000); return()=>clearInterval(t)},[]);
 const act=(ref,action)=>fetch("http://127.0.0.1:8090/api/workflow/"+encodeURIComponent(ref)+"/transition",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({actor_role:"survey_gis_officer",actor_name:"Rajesh Patil",action,note:"Handled from Survey/GIS Officer portal."})}).then(load);
 return <div style={{position:"fixed",right:18,bottom:18,zIndex:9999,fontFamily:"Arial"}}><div style={{display:open?"block":"none",width:330,maxHeight:360,overflow:"auto",background:"white",border:"1px solid #dce5ea",borderRadius:10,boxShadow:"0 15px 40px #0003",marginBottom:8}}><div style={{padding:12,borderBottom:"1px solid #eee",fontWeight:700}}>Connected Workflow</div>{items.length?items.map(x=><div key={x.ref} style={{padding:10,borderBottom:"1px solid #eee",fontSize:11}}><b>{x.ref}</b><div>{x.title}</div><small>{x.status} · {x.priority}</small><div style={{display:"flex",gap:5,marginTop:6}}><button onClick={()=>act(x.ref,"approve")}>Approve</button><button onClick={()=>act(x.ref,"forward")}>Forward</button><button onClick={()=>act(x.ref,"return")}>Return</button></div></div>):<div style={{padding:15,color:"#789"}}>No pending Survey/GIS tasks.</div>}</div><button onClick={()=>{setOpen(!open);load()}} style={{border:0,borderRadius:20,padding:"10px 14px",background:"#173b57",color:"white",boxShadow:"0 5px 20px #0003"}}>↔ Workflow {items.length}</button></div>
}

function Survey({parcel,setSurveyParcel,notify,go,onDocumentAdded}){
 const p=parcel||parcels[0];
 const [step,setStep]=useState(1);
 const [gps,setGps]=useState(null);
 const [gpsError,setGpsError]=useState("");
 const [boundary,setBoundary]=useState(p?.boundary||"Verified");
 const [measured,setMeasured]=useState(String(p?.measured||p?.area||3.25));
 const [land,setLand]=useState({landUse:p?.landUse||"Agricultural",encroachment:"No",structures:"No",roadAccess:"Yes"});
 const [remarks,setRemarks]=useState("");
 const [photos,setPhotos]=useState([]);
 const [document,setDocument]=useState(null);

 const persistSurvey=async (extra={})=>{
   const payload={
     portal:"Survey & GIS Officer Portal",
     role:"survey_gis_officer",
     action:extra.action||"save",
     route:"/field-survey",
     ref:`SUR-${p?.id||"UNKNOWN"}`,
     project_id:p?.project||"",
     parcel_id:p?.id||"",
     create_workflow:extra.create_workflow??false,
     data:{
       parcel_id:p?.id||"", project_id:p?.project||"", survey_no:p?.survey||"",
       village:p?.village||"", taluka:p?.taluka||"", land_use:land.landUse,
       encroachment:land.encroachment, structures:land.structures, road_access:land.roadAccess,
       measured_area:Number(measured)||0, boundary, remarks, gps,
       photos:photos.map(x=>({name:x.name,size:x.size,location:x.location})),
       document:document?{name:document.name,size:document.size,type:document.type}:null
     }
   };
   try{
     await fetch("http://127.0.0.1:8090/api/sync/record",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
   }catch(e){ console.warn("NLAMS integration sync failed",e); }
 };

 useEffect(()=>{
   let alive=true;
   fetch(`http://127.0.0.1:8090/api/records?entity=survey&parcel_id=${encodeURIComponent(p?.id||"")}`,{cache:"no-store"}).then(r=>r.json()).then(rows=>{const x=rows?.[0]?.data;if(!alive||!x)return;if(x.measured_area!==undefined)setMeasured(String(x.measured_area));if(x.land_use||x.encroachment||x.structures||x.road_access)setLand(v=>({...v,landUse:x.land_use||v.landUse,encroachment:x.encroachment||v.encroachment,structures:x.structures||v.structures,roadAccess:x.road_access||v.roadAccess}));if(x.boundary)setBoundary(x.boundary);if(x.remarks)setRemarks(x.remarks);if(x.gps)setGps({...x.gps,timestamp:new Date(x.gps.timestamp||Date.now())});}).catch(()=>{});
   return()=>{alive=false};
 },[p?.id]);

 useEffect(()=>{
   if(!navigator.geolocation) return;
   const id=navigator.geolocation.watchPosition(pos=>{
     const location={lat:pos.coords.latitude,lng:pos.coords.longitude,accuracy:pos.coords.accuracy,timestamp:new Date(pos.timestamp||Date.now())};
     setGps(location); syncNLAMSGPS(location,p);
   },()=>{}, {enableHighAccuracy:true,maximumAge:5000,timeout:15000});
   return()=>navigator.geolocation.clearWatch(id);
 },[p?.id]);

 const capture=()=>{
   if(!navigator.geolocation){setGpsError("Geolocation is not supported by this browser.");notify("GPS is not supported on this device/browser.");return;}
   setGpsError(""); notify("Requesting high-accuracy GPS location...");
   navigator.geolocation.getCurrentPosition(pos=>{
     const next={lat:pos.coords.latitude,lng:pos.coords.longitude,accuracy:pos.coords.accuracy,timestamp:new Date(pos.timestamp||Date.now())};
     setGps(next); syncNLAMSGPS(next,p); notify("GPS coordinates captured successfully.");
   },err=>{
     const messages={1:"Location permission was denied. Allow location access in your browser and try again.",2:"Your position could not be determined. Move to an open area and try again.",3:"GPS timed out. Check location services and try again."};
     setGpsError(messages[err.code]||"Unable to capture GPS location. Please try again."); notify("GPS capture failed.");
   },{enableHighAccuracy:true,timeout:20000,maximumAge:0});
 };

 const getFreshGPS=()=>new Promise((resolve,reject)=>{
   if(!navigator.geolocation){reject(new Error("Geolocation is not supported by this browser."));return;}
   navigator.geolocation.getCurrentPosition(pos=>resolve({lat:pos.coords.latitude,lng:pos.coords.longitude,accuracy:pos.coords.accuracy,timestamp:new Date(pos.timestamp||Date.now())}),err=>{
     const messages={1:"Location permission was denied. Allow location access in your browser and try again.",2:"Your position could not be determined. Move to an open area and try again.",3:"GPS timed out. Check location services and try again."}; reject(new Error(messages[err.code]||"Unable to capture GPS location."));
   },{enableHighAccuracy:true,timeout:20000,maximumAge:0});
 });

 const addPhoto=async e=>{
   const files=Array.from(e.target.files||[]); if(!files.length)return;
   try{
     notify("Capturing GPS for geo-tagged evidence...");
     const location=await getFreshGPS();
     setGps(location); syncNLAMSGPS(location,p); setGpsError("");
     const added=files.map(file=>({id:crypto.randomUUID?.()||`${Date.now()}-${Math.random()}`,file,name:file.name,size:file.size,type:file.type,location,preview:URL.createObjectURL(file)}));
     setPhotos(prev=>[...prev,...added]);
     added.forEach(photo=>onDocumentAdded?.({id:photo.id,name:photo.name,category:"Evidence",type:"Image",size:formatBytes(photo.size),uploadedBy:"Rajesh Patil",uploadedOn:formatDateTime(photo.location.timestamp),version:1,file:photo.file,geo:photo.location,preview:photo.preview}));
     notify(`${files.length} field photo${files.length>1?"s":""} uploaded and geo-tagged.`);
   }catch(err){setGpsError(err.message);notify("Photo upload cancelled because GPS could not be captured.");}
   e.target.value="";
 };

 const addDocument=e=>{const file=e.target.files?.[0];if(!file)return; const doc={id:crypto.randomUUID?.()||`${Date.now()}-${Math.random()}`,name:file.name,category:"Survey Reports",type:file.type.includes("pdf")?"PDF":"Image",size:formatBytes(file.size),uploadedBy:"Rajesh Patil",uploadedOn:formatDateTime(new Date()),version:1,file}; setDocument(doc); onDocumentAdded?.(doc); notify("Survey document uploaded successfully."); setTimeout(()=>persistSurvey({action:"document_upload",create_workflow:false}),0); e.target.value="";};
 const measuredNum=Number(measured)||0; const diff=Math.abs(p.area-measuredNum); const pct=p.area?((diff/p.area)*100).toFixed(2):"0.00"; const gpsComplete=!!gps;
 return <><PageHeader eyebrow="Mobile-ready field workflow" title="Field Survey" desc={`${p.id} · ${p.village}, ${p.taluka}`} actions={<span className="demo-tag"><Smartphone size={15}/> Field Mode</span>}/>
 <div className="survey-stepper">{["Location","Land Details","Boundary","Evidence","Review"].map((x,i)=><div className={(step===i+1?"current ":"")+(step>i+1?"done":"")} key={x}><i>{step>i+1?<CheckCircle2 size={16}/>:i+1}</i><span>{x}</span></div>)}</div>
 <div className="survey-layout"><section className="panel survey-card">
 {step===1&&<><div className="survey-title"><div><h3>1. Capture Survey Location</h3><p>Record the parcel's real device GPS coordinates.</p></div><span className={"gps-pill "+(gps?"on":"")}><Navigation size={15}/> {gps?"GPS Captured":"GPS Required"}</span></div>
   <div className="gps-box"><div className="gps-map-real"><SurveyGPSMap gps={gps} fallback={[p.lat,p.lng]}/></div><div className="gps-data"><Info label="Latitude" value={gps?gps.lat.toFixed(6):"—"}/><Info label="Longitude" value={gps?gps.lng.toFixed(6):"—"}/><Info label="Accuracy" value={gps?`±${Math.round(gps.accuracy)} meters`:"—"}/><Info label="Captured" value={gps?gps.timestamp.toLocaleString():"—"}/></div></div>
   {gpsError&&<div className="alert danger"><AlertTriangle/><div><b>GPS capture error</b><span>{gpsError}</span></div></div>}
   <button className="btn primary full big" onClick={capture}><LocateFixed/> {gps?"Refresh GPS":"Capture Current Location"}</button><p className="gps-help">Browser location permission is required. Every evidence upload also captures a fresh GPS position and timestamp.</p>
 </>}
 {step===2&&<SurveyForm p={p} measured={measured} setMeasured={setMeasured} land={land} setLand={setLand}/>}
 {step===3&&<><div className="survey-title"><div><h3>3. Boundary Verification</h3><p>Compare cadastral boundary information with field observations.</p></div></div><div className="compare-grid big"><div><span>Cadastral Area</span><strong>{p.area} ha</strong></div><div><span>GPS Measured Area</span><strong>{measuredNum.toFixed(2)} ha</strong></div><div className={pct>5?"danger-text":""}><span>Difference</span><strong>{pct}%</strong></div></div><div className="boundary-options">{["Verified","Minor Difference","Discrepancy","Unable to Verify"].map(x=><button className={boundary===x?"selected":""} onClick={()=>setBoundary(x)} key={x}><span>{x==="Verified"?"✓":x==="Discrepancy"?"!":"•"}</span>{x}</button>)}</div>{(boundary==="Discrepancy"||pct>5)&&<div className="alert danger"><AlertTriangle/><div><b>Discrepancy detected</b><span>System recommends a re-survey and additional boundary evidence.</span></div></div>}<textarea className="remarks" value={remarks} onChange={e=>setRemarks(e.target.value)} placeholder="Add field remarks or observations..."/></>}
 {step===4&&<><div className="survey-title"><div><h3>4. Geo-tagged Field Evidence</h3><p>Upload field photographs. GPS coordinates, accuracy and capture time are recorded with every photo.</p></div></div>
   <div className="geo-evidence-status"><MapPin size={17}/><div><b>{gps?`Current GPS: ${gps.lat.toFixed(6)}, ${gps.lng.toFixed(6)}`:"GPS will be captured automatically"}</b><span>{gps?`Accuracy ±${Math.round(gps.accuracy)} m · ${gps.timestamp.toLocaleString()}`:"Allow browser location access when you upload a photo."}</span></div></div>
   <div className="upload-box"><Camera size={28}/><b>Capture / Upload Field Photos</b><span>Each photo gets a fresh GPS coordinate, accuracy and timestamp automatically.</span><label className="btn secondary" htmlFor="survey-photo-input"><Camera/> Add Photo</label><input id="survey-photo-input" className="file-input" type="file" accept="image/*" capture="environment" multiple onChange={addPhoto}/></div>
   {photos.length>0&&<div className="evidence-grid">{photos.map(photo=><div className="evidence-card" key={photo.id}><img src={photo.preview} alt={photo.name}/><button className="evidence-remove" onClick={()=>{URL.revokeObjectURL(photo.preview);setPhotos(prev=>prev.filter(x=>x.id!==photo.id));notify("Evidence photo removed.")}}><X size={13}/></button><div className="evidence-meta"><b>{photo.name}</b><span><MapPin size={11}/> {photo.location.lat.toFixed(6)}, {photo.location.lng.toFixed(6)}</span><span>±{Math.round(photo.location.accuracy)} m · {photo.location.timestamp.toLocaleString()}</span></div></div>)}</div>}
   <div className="upload-row"><FileText/><div><b>Survey Report / Measurement Sheet</b><span>{document?`${document.name} · ${document.size}`:"PDF, JPG or PNG · Max 10 MB"}</span></div><label className="btn secondary" htmlFor="survey-doc-input"><Upload/> {document?"Replace":"Upload"}</label><input id="survey-doc-input" className="file-input" type="file" accept=".pdf,image/*" onChange={addDocument}/></div>
 </>}
 {step===5&&<><div className="survey-title"><div><h3>5. Review & Submit</h3><p>Confirm all information before sending verification to LAO.</p></div></div><div className="review-list"><Review label="GPS Location" ok={gpsComplete}/><Review label="Land Details" ok/><Review label="Boundary Verification" ok={boundary!=="Unable to Verify"}/><Review label="Field Evidence" ok={photos.length>0}/><Review label="Required Documents" ok={!!document}/></div>{(boundary==="Discrepancy"||pct>5)&&<div className="alert warning"><CircleAlert/><div><b>Re-survey will be recommended</b><span>The LAO will receive the discrepancy details with your submission.</span></div></div>}<button className="btn primary full big" disabled={!gpsComplete} onClick={async()=>{await persistSurvey({action:"submit",create_workflow:true});notify("Survey saved and submitted to LAO.");go("dashboard")}}><Send/> Submit Verification to LAO</button></>}
 <div className="survey-nav">{step>1?<button className="btn secondary" onClick={()=>setStep(step-1)}>Back</button>:<button className="btn secondary" onClick={()=>go("dashboard")}>Cancel</button>}{step<5&&<button className="btn primary" onClick={async()=>{await persistSurvey({action:"step_save",create_workflow:false});setStep(step+1)}}>Continue <ChevronRight/></button>}</div>
 </section><aside className="panel survey-side"><div className="side-head"><b>Parcel Summary</b><Badge text={p.status}/></div><Info label="Parcel ID" value={p.id}/><Info label="Survey No." value={p.survey}/><Info label="Village" value={p.village}/><Info label="Area" value={p.area+" ha"}/><hr/><div className="field-tip"><ShieldCheck/><div><b>Field verification</b><span>All actions are recorded in the NLAMS audit trail.</span></div></div><div className="field-tip"><Smartphone/><div><b>Mobile optimized</b><span>Use GPS and camera directly from your device.</span></div></div></aside></div></>
}
function formatBytes(bytes){if(!bytes)return "0 KB";const units=["B","KB","MB","GB"];const i=Math.min(Math.floor(Math.log(bytes)/Math.log(1024)),units.length-1);return `${(bytes/Math.pow(1024,i)).toFixed(i?1:0)} ${units[i]}`;}
function formatDateTime(date){return new Date(date).toLocaleString([], {day:"2-digit",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit"});}
function SurveyGPSMap({gps,fallback}){
 const center=gps?[gps.lat,gps.lng]:fallback;
 return <MapContainer center={center} zoom={16} scrollWheelZoom className="leaflet-survey-map"><TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/><Marker position={center}><Popup><b>{gps?"Captured Survey Location":"Parcel Reference Location"}</b><br/>{center[0].toFixed(6)}, {center[1].toFixed(6)}{gps&&<><br/>Accuracy: ±{Math.round(gps.accuracy)} m<br/>Captured: {gps.timestamp.toLocaleString()}</>}</Popup></Marker></MapContainer>
}
function SurveyForm({p,measured,setMeasured,land,setLand}){const update=k=>e=>setLand(v=>({...v,[k]:e.target.value}));return <><div className="survey-title"><div><h3>2. Land & Measurement Details</h3><p>Record actual field observations. Values remain available throughout the workflow.</p></div></div><div className="form-grid"><label>Survey Number<input value={p.survey} readOnly/></label><label>Village<input value={p.village} readOnly/></label><label>Taluka<input value={p.taluka} readOnly/></label><label>District<input value="Raigad" readOnly/></label><label>Recorded Area (ha)<input value={p.area} readOnly/></label><label>Measured Area (ha)<input type="number" step=".01" value={measured} onChange={e=>setMeasured(e.target.value)}/></label><label>Land Use<select value={land.landUse} onChange={update("landUse")}><option>Agricultural</option><option>Residential</option><option>Commercial</option><option>Industrial</option><option>Forest</option><option>Barren</option></select></label><label>Encroachment<select value={land.encroachment} onChange={update("encroachment")}><option>No</option><option>Yes</option></select></label><label>Structures Present<select value={land.structures} onChange={update("structures")}><option>No</option><option>Yes</option></select></label><label>Road Access<select value={land.roadAccess} onChange={update("roadAccess")}><option>Yes</option><option>No</option></select></label></div></>}
function Review({label,ok}){return <div className="review-row"><div><CheckCircle2 className={ok?"":"muted"}/><b>{label}</b></div><span className={ok?"complete":"incomplete"}>{ok?"Complete":"Required"}</span></div>}

function Discrepancies({data,go,notify}){return <><PageHeader eyebrow="Smart validation" title="Discrepancies" desc="Review automated and field-reported data inconsistencies." actions={<button className="btn secondary" onClick={()=>notify("Report export prepared.")}><Download/> Export Report</button>}/><div className="kpis four"><Kpi icon={<AlertTriangle/>} label="Total Discrepancies" value="18" note="Across 4 projects" warn/><Kpi icon={<CircleAlert/>} label="High Priority" value="5" note="Needs action" warn/><Kpi icon={<Clock3/>} label="Pending Resolution" value="11" note="3 overdue"/><Kpi icon={<CheckCircle2/>} label="Resolved" value="7" note="+2 this week" good/></div><section className="panel"><div className="table-scroll"><table><thead><tr><th>Issue</th><th>Parcel</th><th>Issue Type</th><th>Severity</th><th>Detected</th><th>Status</th><th/></tr></thead><tbody>{data.map((p,i)=><tr key={p.id}><td><b>ISS-{1020+i}</b></td><td>{p.id}</td><td>{p.boundary==="Discrepancy"?"Boundary mismatch":"Area mismatch"}</td><td><Badge text={i===0?"High":"Medium"}/></td><td>05 Sep 2026</td><td><Badge text="Pending Resolution"/></td><td><button className="btn secondary small" onClick={()=>{go("parcel-details");notify("Opening discrepancy details.")}}>Review</button></td></tr>)}</tbody></table></div></section></>}

function Requests({go,setSurveyParcel}){return <><PageHeader eyebrow="LAO coordination" title="Verification Requests" desc="Requests and field-verification tasks received from Land Acquisition Officers."/><div className="request-grid">{requests.map(r=><div className="panel request-card" key={r.id}><div className="request-top"><b>{r.id}</b><Badge text={r.priority}/></div><h3>{r.parcel}</h3><p>{r.text}</p><div className="request-meta"><span><FolderKanban size={14}/> {r.project}</span><span><Clock3 size={14}/> Due {r.deadline}</span></div><button className="btn primary full" onClick={()=>{setSurveyParcel(parcels.find(p=>p.id===r.parcel));go("survey")}}><MapPinned/> Start Survey</button></div>)}</div></>}

function Documents({notify,documents,setDocuments}){
 const [tab,setTab]=useState("All Documents"); const [query,setQuery]=useState(""); const [preview,setPreview]=useState(null); const [uploadCategory,setUploadCategory]=useState("Evidence");
 const tabs=["All Documents","Survey Reports","Cadastral Maps","Evidence"];
 const visible=documents.filter(d=>(tab==="All Documents"||d.category===tab)&&d.name.toLowerCase().includes(query.toLowerCase()));
 const upload=e=>{const file=e.target.files?.[0];if(!file)return;const doc={id:crypto.randomUUID?.()||`${Date.now()}-${Math.random()}`,name:file.name,category:uploadCategory,type:file.type.includes("pdf")?"PDF":file.type.startsWith("image/")?"Image":"File",size:formatBytes(file.size),uploadedBy:"Rajesh Patil",uploadedOn:formatDateTime(new Date()),version:1,file};setDocuments(prev=>[doc,...prev]);notify(`${uploadCategory} document uploaded successfully.`);e.target.value="";};
 const view=d=>{if(d.file){setPreview({...d,url:URL.createObjectURL(d.file)});}else setPreview(d);};
 const closePreview=()=>{if(preview?.url)URL.revokeObjectURL(preview.url);setPreview(null);};
 const download=d=>{if(!d.file){notify("This seeded repository file has no local file attached.");return;}const url=URL.createObjectURL(d.file);const a=document.createElement("a");a.href=url;a.download=d.name;a.click();URL.revokeObjectURL(url);};
 return <><PageHeader eyebrow="Secure repository" title="Documents" desc="Survey evidence, cadastral maps and field reports with version history." actions={<div className="doc-upload-controls"><select value={uploadCategory} onChange={e=>setUploadCategory(e.target.value)}><option>Evidence</option><option>Survey Reports</option><option>Cadastral Maps</option></select><label className="btn primary"><Upload/> Upload Document<input className="file-input" type="file" accept=".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx" onChange={upload}/></label></div>}/>
 <section className="panel"><div className="toolbar doc-toolbar"><div className="doc-tabs">{tabs.map(t=><button key={t} className={"filter-chip "+(tab===t?"active":"")} onClick={()=>setTab(t)}>{t}</button>)}</div><div className="doc-search"><Search size={15}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search documents..."/></div></div>
 <div className="document-count">Showing {visible.length} of {documents.length} documents · {tab}</div>
 <div className="table-scroll"><table className="documents-table"><thead><tr><th>File Name</th><th>Category</th><th>Type</th><th>Uploaded By</th><th>Geo-tagged</th><th>Size</th><th>Uploaded On</th><th>Actions</th></tr></thead><tbody>{visible.map(d=><tr key={d.id}><td><div className="file-cell"><div className="doc-icon">{d.type==="Image"?<FileImage/>:<FileText/>}</div><div><b>{d.name}</b><span>Version {d.version}</span></div></div></td><td><span className="category-pill">{d.category}</span></td><td>{d.type}</td><td>{d.uploadedBy}</td><td>{d.geo?<span className="geo-pill-table"><MapPin size={11}/> Yes</span>:<span className="muted-text">No</span>}</td><td>{d.size}</td><td>{d.uploadedOn}</td><td><div className="doc-actions"><button className="icon-btn" title="View" onClick={()=>view(d)}><Eye/></button><button className="icon-btn" title="Download" onClick={()=>download(d)}><Download/></button>{d.file&&<button className="icon-btn danger-icon" title="Delete" onClick={()=>{setDocuments(prev=>prev.filter(x=>x.id!==d.id));notify("Document removed.")}}><Trash2/></button>}</div></td></tr>)}</tbody></table></div>{visible.length===0&&<div className="empty-docs"><FileArchive/><b>No documents found</b><span>Upload a document or change the selected tab/search.</span></div>}</section>
 {preview&&<div className="modal-backdrop" onClick={closePreview}><div className="doc-modal" onClick={e=>e.stopPropagation()}><div className="modal-head"><div><b>{preview.name}</b><span>{preview.category} · {preview.type} · {preview.size}</span></div><button className="icon-btn" onClick={closePreview}><X/></button></div><div className="modal-body">{preview.url&&preview.type==="Image"?<img src={preview.url} alt={preview.name}/>:preview.url&&preview.type==="PDF"?<iframe title={preview.name} src={preview.url}/>:<div className="seed-preview"><FileText/><b>Repository record</b><span>This prototype has the document metadata for this seeded file, but no local file bytes to preview.</span></div>}</div></div></div>}
 </>;
}

function Reports({notify}){return <><PageHeader eyebrow="MIS & decision support" title="Reports" desc="Generate survey, GIS and discrepancy reports for project monitoring."/><div className="report-grid">{["Project Survey Report","Parcel Survey Report","Pending Survey Report","Verified Parcel Report","Re-Survey Report","GIS Discrepancy Report","Geo-Tagged Evidence Report","Survey Progress Report"].map((x,i)=><div className="panel report-card" key={x}><div className="report-icon"><BarChart3/></div><h3>{x}</h3><p>Generate filtered {x.toLowerCase()} for assigned projects.</p><button className="btn secondary full" onClick={()=>notify(`${x} generated in demo mode.`)}><Download/> Generate Report</button></div>)}</div></>}

function Notifications({notify}){return <><PageHeader eyebrow="Alerts & updates" title="Notifications" desc="Stay up to date with survey assignments, requests and deadlines." actions={<button className="btn secondary" onClick={()=>notify("All notifications marked as read.")}><CheckCircle2/> Mark all read</button>}/><section className="panel notification-list">{notifications.map((n,i)=><div className="notification" key={i}><div className={"notif-dot "+n[1].toLowerCase()}/><div><b>{n[0]}</b><span>{n[2]} · NLAMS System</span></div><button className="text-btn" onClick={()=>notify("Notification opened.")}>Open <ChevronRight size={15}/></button></div>)}</section></>}

function HistoryPage(){return <><PageHeader eyebrow="Traceability" title="Activity History" desc="Every important field action is recorded for accountability and audit."/><section className="panel"><Timeline/></section></>}
function Timeline({compact}){const items=[["06 Sep 2026 · 10:42 AM","GPS coordinates captured","Parcel P-MH-RGD-00125"],["06 Sep 2026 · 10:45 AM","Boundary photograph uploaded","Parcel P-MH-RGD-00125"],["06 Sep 2026 · 10:51 AM","Area measurement updated","3.25 ha → 3.18 ha"],["06 Sep 2026 · 10:55 AM","Boundary verified","Parcel P-MH-RGD-00125"],["06 Sep 2026 · 11:02 AM","Survey submitted to LAO","SUR-2026-00125"],["05 Sep 2026 · 04:35 PM","Re-survey requested","Parcel P-MH-RGD-00127"]];return <div className={"timeline "+(compact?"compact":"")}>{items.slice(0,compact?4:6).map((x,i)=><div className="timeline-item" key={i}><i>{i===0?<Navigation/>:i===1?<Camera/>:i===4?<Send/>:<CheckCircle2/>}</i><div><b>{x[1]}</b><span>{x[0]} · {x[2]}</span></div></div>)}</div>}

function Profile(){return <><PageHeader eyebrow="Officer profile" title="Profile" desc="Survey/GIS Officer account and performance overview."/><div className="profile-grid"><section className="panel profile-card"><div className="profile-hero"><div className="avatar xl">RP</div><div><h2>Rajesh Patil</h2><p>Survey / GIS Officer</p><span>Employee ID · GIS-1025</span></div></div><div className="info-grid"><Info label="Department" value="Land Acquisition"/><Info label="District" value="Raigad"/><Info label="State" value="Maharashtra"/><Info label="Assigned Projects" value="12"/><Info label="Completed Surveys" value="145"/><Info label="Pending Surveys" value="28"/><Info label="Verification Accuracy" value="96%"/><Info label="Last Login" value="06 Sep 2026, 09:12 AM"/></div></section><section className="panel"><h3>Performance</h3><div className="performance"><strong>96%</strong><span>Survey verification accuracy</span><div className="bar"><i style={{width:"96%"}}/></div><small>Excellent · Based on last 30 days</small></div><hr/><h4>Security</h4><div className="secure-row"><ShieldCheck/><div><b>Role-based access enabled</b><span>Survey/GIS permissions active</span></div></div></section></div></>}

function SettingsPage({notify}){return <><PageHeader eyebrow="Preferences" title="Settings" desc="Configure map, notification and security preferences."/><div className="settings-grid"><section className="panel"><h3>Map Preferences</h3><Setting label="Default map layer" value="Street Map"/><Setting label="Show verified parcels" value="Enabled" toggle/><Setting label="Show discrepancy alerts" value="Enabled" toggle/></section><section className="panel"><h3>Notifications</h3><Setting label="LAO verification requests" value="Enabled" toggle/><Setting label="Deadline reminders" value="Enabled" toggle/><Setting label="System alerts" value="Enabled" toggle/></section><section className="panel"><h3>Security</h3><Setting label="Secure session" value="Active"/><Setting label="Audit logging" value="Enabled"/><button className="btn secondary" onClick={()=>notify("Password change flow opened.")}>Change Password</button></section></div></>}
function Setting({label,value,toggle}){return <div className="setting"><div><b>{label}</b><span>{value}</span></div>{toggle?<button className="toggle on"><i/></button>:<ChevronRight size={16}/>}</div>}

function AppRoot(){return <App/>}
createRoot(document.getElementById("root")).render(<AppRoot/>);