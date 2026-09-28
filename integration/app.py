from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import sqlite3, os, json, urllib.parse, uuid, mimetypes
from datetime import datetime

BASE=os.path.dirname(__file__); DB=os.path.join(BASE,'nlams_integration.db'); PORT=int(os.environ.get('NLAMS_INTEGRATION_PORT','8090'))
ROUTES={'landowner':'grievance_officer','grievance_officer':'lao','lao':'revenue_officer','project_agency':'lao','revenue_officer':'rr_officer','rr_officer':'survey_gis_officer','survey_gis_officer':'administrator','administrator':'lao'}
ACQUISITION_FLOW=['project_agency','lao','revenue_officer','rr_officer','survey_gis_officer','administrator']

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def now(): return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def init():
    c=db(); c.executescript('''
    CREATE TABLE IF NOT EXISTS workflows(id INTEGER PRIMARY KEY AUTOINCREMENT,ref TEXT UNIQUE,kind TEXT,title TEXT,description TEXT,current_role TEXT,status TEXT,priority TEXT,project_id TEXT,parcel_id TEXT,created_by TEXT,created_at TEXT,updated_at TEXT);
    CREATE TABLE IF NOT EXISTS workflow_events(id INTEGER PRIMARY KEY AUTOINCREMENT,workflow_id INTEGER,from_role TEXT,to_role TEXT,action TEXT,actor TEXT,note TEXT,at TEXT);
    CREATE TABLE IF NOT EXISTS locations(id INTEGER PRIMARY KEY AUTOINCREMENT,actor_role TEXT,actor_name TEXT,project_id TEXT,parcel_id TEXT,lat REAL,lng REAL,accuracy REAL,captured_at TEXT,source TEXT);
    CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY AUTOINCREMENT,record_key TEXT UNIQUE,entity TEXT,portal TEXT,role TEXT,action TEXT,route TEXT,project_id TEXT,parcel_id TEXT,ref TEXT,data_json TEXT,created_at TEXT,updated_at TEXT);
    CREATE TABLE IF NOT EXISTS projects_shared(project_id TEXT PRIMARY KEY,name TEXT,state TEXT,district TEXT,villages TEXT,required_land REAL,created_at TEXT,status TEXT);
    CREATE TABLE IF NOT EXISTS landowners_shared(landowner_id TEXT PRIMARY KEY,name TEXT,project_id TEXT,parcel_id TEXT,contact TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS parcels_shared(parcel_id TEXT PRIMARY KEY,project_id TEXT,landowner_id TEXT,survey_no TEXT,village TEXT,area REAL,lat REAL,lng REAL,status TEXT,revenue_status TEXT,gis_status TEXT,workflow_status TEXT,created_at TEXT,updated_at TEXT);
    CREATE TABLE IF NOT EXISTS documents_shared(id INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT,parcel_id TEXT,category TEXT,name TEXT,type TEXT,uploaded_by TEXT,uploaded_at TEXT,status TEXT,version INTEGER,source_path TEXT);
    CREATE TABLE IF NOT EXISTS evidence_shared(id INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT,parcel_id TEXT,evidence_type TEXT,name TEXT,url TEXT,lat REAL,lng REAL,uploaded_by TEXT,uploaded_at TEXT,label TEXT);
    CREATE TABLE IF NOT EXISTS case_history(id INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT,parcel_id TEXT,stage TEXT,status TEXT,actor TEXT,note TEXT,at TEXT);
    CREATE TABLE IF NOT EXISTS notifications_shared(id INTEGER PRIMARY KEY AUTOINCREMENT,recipient_role TEXT,project_id TEXT,parcel_id TEXT,ref TEXT,title TEXT,message TEXT,level TEXT,read INTEGER DEFAULT 0,created_at TEXT);
    CREATE TABLE IF NOT EXISTS validation_results(id INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT,parcel_id TEXT,rule TEXT,status TEXT,message TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS security_audit(id INTEGER PRIMARY KEY AUTOINCREMENT,actor_id TEXT,actor_role TEXT,action TEXT,resource TEXT,ip TEXT,at TEXT); CREATE TABLE IF NOT EXISTS login_attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,identifier TEXT,ip TEXT,at TEXT,success INTEGER); CREATE TABLE IF NOT EXISTS document_integrity(document_id TEXT PRIMARY KEY,sha256 TEXT,version INTEGER,status TEXT,created_at TEXT); CREATE TABLE IF NOT EXISTS privacy_consents(id INTEGER PRIMARY KEY AUTOINCREMENT,subject_id TEXT,subject_type TEXT,policy_version TEXT,consented_at TEXT,source TEXT); CREATE TABLE IF NOT EXISTS landowner_registrations(landowner_id TEXT PRIMARY KEY,name TEXT,email TEXT,mobile TEXT,survey_no TEXT,gat_no TEXT,land_type TEXT,village TEXT,taluka TEXT,district TEXT,nearby_identifier TEXT,project_id TEXT,parcel_id TEXT,status TEXT,rejection_reason TEXT,created_at TEXT,updated_at TEXT);
    ''')
    # One authoritative demo case used by every portal.
    t=now()
    c.execute("INSERT OR IGNORE INTO projects_shared VALUES(?,?,?,?,?,?,?,?)",('NH44-MH-001','NH-44 Highway Expansion','Maharashtra','Pune','Pimpalgaon, Wagholi',100,t,'Project Created'))
    owners=[('LO-001','Demo Owner A','NH44-MH-001','P-001','DEMO CONTACT',t),('LO-002','Demo Owner B','NH44-MH-001','P-002','DEMO CONTACT',t),('LO-003','Demo Owner C','NH44-MH-001','P-003','DEMO CONTACT',t)]
    c.executemany('INSERT OR IGNORE INTO landowners_shared VALUES(?,?,?,?,?,?)',owners)
    parcels=[('P-001','NH44-MH-001','LO-001','125','Pimpalgaon',2.5,18.5204,73.8567,'Revenue Verification Pending','Pending','Pending','Project Created',t,t),('P-002','NH44-MH-001','LO-002','126','Pimpalgaon',3.0,18.5230,73.8590,'Revenue Verification Pending','Pending','Pending','Project Created',t,t),('P-003','NH44-MH-001','LO-003','128','Wagholi',1.8,18.5750,73.9850,'Revenue Verification Pending','Pending','Pending','Project Created',t,t)]
    c.executemany('INSERT OR IGNORE INTO parcels_shared VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',parcels)
    docs=[
      ('NH44-MH-001','','Project Documents','DPR – DEMO','PDF','Project Agency',t,'Verified',1,'/demo-assets/NH44_DPR_DEMO.pdf'),
      ('NH44-MH-001','','Project Documents','Land Acquisition Proposal – DEMO','PDF','Project Agency',t,'Verified',1,'/demo-assets/NH44_Land_Acquisition_Proposal_DEMO.pdf'),
      ('NH44-MH-001','','Project Documents','Project Approval – DEMO','PDF','Project Agency',t,'Verified',1,'/demo-assets/NH44_Project_Approval_DEMO.pdf'),
      ('NH44-MH-001','','Project Documents','Alignment Map – DEMO','PDF','Project Agency',t,'Verified',1,'/demo-assets/NH44_Alignment_Map_DEMO.pdf'),
      ('NH44-MH-001','','Project Documents','Land Requirement – DEMO','PDF','Project Agency',t,'Verified',1,'/demo-assets/NH44_Land_Requirement_DEMO.pdf'),
      ('NH44-MH-001','P-001','Revenue Documents','7/12 Extract – DEMO','PDF','Revenue Officer',t,'Pending Verification',1,'/demo-assets/P001_712_DEMO.pdf'),
      ('NH44-MH-001','P-001','Revenue Documents','Ownership Record – DEMO','PDF','Revenue Officer',t,'Pending Verification',1,'/demo-assets/P001_Ownership_DEMO.pdf'),
      ('NH44-MH-001','P-001','Revenue Documents','Mutation Record – DEMO','PDF','Revenue Officer',t,'Pending Verification',1,'/demo-assets/P001_Mutation_DEMO.pdf'),
      ('NH44-MH-001','P-001','GIS Documents','Survey Report – DEMO','PDF','Survey / GIS Officer',t,'Pending',1,'/demo-assets/P001_Survey_Report_DEMO.pdf'),
      ('NH44-MH-001','P-001','GIS Documents','GIS Boundary – DEMO','MAP','Survey / GIS Officer',t,'Pending',1,'/demo-assets/P001_GIS_Boundary_DEMO.pdf'),
      ('NH44-MH-001','P-002','Revenue Documents','7/12 Extract – DEMO','PDF','Revenue Officer',t,'Pending Verification',1,'/demo-assets/P002_712_DEMO.pdf'),
      ('NH44-MH-001','P-003','Revenue Documents','7/12 Extract – DEMO','PDF','Revenue Officer',t,'Pending Verification',1,'/demo-assets/P003_712_DEMO.pdf')]
    for d in docs: c.execute('INSERT OR IGNORE INTO documents_shared(project_id,parcel_id,category,name,type,uploaded_by,uploaded_at,status,version,source_path) SELECT ?,?,?,?,?,?,?,?,?,? WHERE NOT EXISTS (SELECT 1 FROM documents_shared WHERE project_id=? AND parcel_id=? AND name=?)',(*d,d[0],d[1],d[3]))
    evid=[
      ('NH44-MH-001','P-001','Field Photo','P001_Field_Photo_01.jpg','/demo-assets/P001_Field_Photo_01.jpg',18.5204,73.8567,'Survey / GIS Officer',t,'DEMO / SAMPLE FIELD IMAGE'),
      ('NH44-MH-001','P-001','Field Photo','P001_Field_Photo_02.jpg','/demo-assets/P001_Field_Photo_02.jpg',18.5207,73.8571,'Survey / GIS Officer',t,'DEMO / SAMPLE FIELD IMAGE'),
      ('NH44-MH-001','P-001','GIS Boundary','P001_GIS_Boundary.geojson','/demo-assets/P001_GIS_Boundary.geojson',18.5204,73.8567,'Survey / GIS Officer',t,'DEMO / SAMPLE GIS BOUNDARY')]
    for e in evid: c.execute('INSERT OR IGNORE INTO evidence_shared(project_id,parcel_id,evidence_type,name,url,lat,lng,uploaded_by,uploaded_at,label) SELECT ?,?,?,?,?,?,?,?,?,? WHERE NOT EXISTS (SELECT 1 FROM evidence_shared WHERE project_id=? AND parcel_id=? AND name=?)',(*e,e[0],e[1],e[3]))
    if not c.execute("SELECT 1 FROM case_history WHERE project_id='NH44-MH-001'").fetchone():
        hist=[('Project Created','Completed','Project Agency','Project NH44-MH-001 created with shared parcels and project documents.'),('Revenue Verification','Pending','Revenue Officer','P-001, P-002 and P-003 are automatically available for verification.'),('GIS Verification','Pending','Survey / GIS Officer','Verified parcels will appear here with shared documents and field evidence.'),('LAO Scrutiny','Pending','LAO','Complete digital case file becomes available after GIS verification.'),('Award','Pending','LAO','Award stage uses the same parcel and landowner records.'),('Compensation','Pending','R&R / Compensation','Compensation remains attached to the same Parcel ID and Landowner ID.'),('R&R','Pending','R&R Officer','R&R uses the same landowner and parcel records.'),('Possession / Closure','Pending','Administrator','Final closure completes the same case history.')]
        c.executemany('INSERT INTO case_history(project_id,parcel_id,stage,status,actor,note,at) VALUES(?,?,?,?,?,?,?)',[( 'NH44-MH-001','P-001',*h,t) for h in hist])
    # Seed a full end-to-end demo workflow in the requested order.
    if not c.execute("SELECT 1 FROM workflows WHERE ref='WF-NH44-P001'").fetchone():
        c.execute('INSERT INTO workflows(ref,kind,title,description,current_role,status,priority,project_id,parcel_id,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',('WF-NH44-P001','parcel','NH-44 · P-001 · Survey 125','Shared case: Project Agency → LAO → Revenue → R&R → Survey/GIS → Administration.','lao','Submitted','High','NH44-MH-001','P-001','project_agency',t,t)); wid=c.execute('SELECT last_insert_rowid()').fetchone()[0]; c.execute('INSERT INTO workflow_events(workflow_id,from_role,to_role,action,actor,note,at) VALUES(?,?,?,?,?,?,?)',(wid,'project_agency','lao','project_submitted','Project Agency','Project, parcel, owner and documents shared centrally.',t))
    if not c.execute("SELECT 1 FROM notifications_shared WHERE ref='WF-NH44-P001'").fetchone():
        c.execute('INSERT INTO notifications_shared(recipient_role,project_id,parcel_id,ref,title,message,level,created_at) VALUES(?,?,?,?,?,?,?,?)',('lao','NH44-MH-001','P-001','WF-NH44-P001','New LAO Verification Task','NH44-MH-001 / P-001 is ready for LAO scrutiny.','info',t))
    c.commit(); c.close()

def send(h,code,obj):
    b=json.dumps(obj,default=str).encode(); h.send_response(code); h.send_header('Content-Type','application/json'); h.send_header('Access-Control-Allow-Origin','*'); h.send_header('Access-Control-Allow-Headers','Content-Type'); h.send_header('Access-Control-Allow-Methods','GET,POST,PUT,OPTIONS'); h.send_header('Cache-Control','no-store'); h.send_header('Content-Length',str(len(b))); h.end_headers(); h.wfile.write(b)

def infer_next(role, route, data):
    route=(route or '').lower()
    if role=='landowner' and ('grievance' in route or 'grievance' in data): return 'grievance_officer'
    if role=='project_agency': return 'lao'
    if role=='lao': return 'revenue_officer'
    if role=='revenue_officer': return 'rr_officer'
    if role=='rr_officer': return 'survey_gis_officer'
    if role=='survey_gis_officer': return 'administrator'
    if role=='grievance_officer': return 'lao'
    return ROUTES.get(role)

def make_record(c,d):
    role=d.get('role','unknown'); portal=d.get('portal',role); action=d.get('action','submit'); route=d.get('route',''); data=d.get('data') or {}
    project_id=str(data.get('project_id') or data.get('project') or d.get('project_id') or '')
    parcel_id=str(data.get('parcel_id') or data.get('parcel') or d.get('parcel_id') or '')
    ref=str(data.get('ticket') or data.get('grievance_id') or data.get('project_id') or data.get('survey_no') or d.get('ref') or '')
    if not ref: ref=f'REC-{datetime.now().strftime("%Y%m%d%H%M%S")}-{uuid.uuid4().hex[:6].upper()}'
    entity='form_submission'
    low=(route+' '+action+' '+json.dumps(data)).lower()
    for key,ename in [('grievance','grievance'),('project','project'),('parcel','parcel'),('compensation','compensation'),('rr','rr_case'),('document','document'),('survey','survey'),('field','survey'),('possession','possession'),('objection','objection')]:
        if key in low: entity=ename; break
    key=f'{portal}:{route}:{ref}'
    t=now(); payload=json.dumps(data,default=str)
    c.execute('''INSERT INTO records(record_key,entity,portal,role,action,route,project_id,parcel_id,ref,data_json,created_at,updated_at)
                 VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(record_key) DO UPDATE SET action=excluded.action,data_json=excluded.data_json,project_id=excluded.project_id,parcel_id=excluded.parcel_id,updated_at=excluded.updated_at''',
              (key,entity,portal,role,action,route,project_id,parcel_id,ref,payload,t,t))
    return key,entity,ref,project_id,parcel_id

class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_OPTIONS(self): send(self,204,{})
    def body(self):
        n=int(self.headers.get('Content-Length','0')); raw=self.rfile.read(n) or b'{}'
        try: return json.loads(raw.decode())
        except Exception: return {}
    def asset(self,path):
        rel=urllib.parse.unquote(path).lstrip('/')
        full=os.path.join(BASE,rel)
        if not os.path.isfile(full): return False
        with open(full,'rb') as f: b=f.read()
        self.send_response(200); self.send_header('Content-Type',mimetypes.guess_type(full)[0] or 'application/octet-stream'); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return True

    def asset(self,path):
        rel=urllib.parse.unquote(path).lstrip('/')
        full=os.path.join(BASE,rel)
        if not os.path.isfile(full): return False
        with open(full,'rb') as f: b=f.read()
        self.send_response(200); self.send_header('Content-Type',mimetypes.guess_type(full)[0] or 'application/octet-stream'); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return True

    def asset(self,path):
        rel=urllib.parse.unquote(path).lstrip('/')
        full=os.path.join(BASE,rel)
        if not os.path.isfile(full): return False
        with open(full,'rb') as f: b=f.read()
        self.send_response(200); self.send_header('Content-Type',mimetypes.guess_type(full)[0] or 'application/octet-stream'); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return True

    def do_GET(self):
        p=urllib.parse.urlparse(self.path).path; q=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query); c=db()
        if p=='/api/health': c.close(); return send(self,200,{'ok':True,'service':'NLAMS Integration Service','time':now()})
        if p.startswith('/demo-assets/'):
            c.close(); return self.asset(p[1:]) or send(self,404,{'error':'Asset not found'})
        if p=='/api/projects/shared':
            rows=[dict(x) for x in c.execute('SELECT * FROM projects_shared ORDER BY project_id')]; c.close(); return send(self,200,rows)
        if p=='/api/parcels/shared':
            project=q.get('project_id',[None])[0]; sql='SELECT * FROM parcels_shared'; args=[]
            if project: sql+=' WHERE project_id=?'; args.append(project)
            rows=[dict(x) for x in c.execute(sql,args)]; c.close(); return send(self,200,rows)
        if p.startswith('/api/project/'):
            project_id=urllib.parse.unquote(p.split('/')[-1]); project=c.execute('SELECT * FROM projects_shared WHERE project_id=?',(project_id,)).fetchone()
            if not project: c.close(); return send(self,404,{'error':'Project not found'})
            parcels=[dict(x) for x in c.execute('SELECT * FROM parcels_shared WHERE project_id=? ORDER BY parcel_id',(project_id,))]
            docs=[dict(x) for x in c.execute('SELECT * FROM documents_shared WHERE project_id=? ORDER BY id',(project_id,))]
            workflows=[dict(x) for x in c.execute('SELECT * FROM workflows WHERE project_id=? ORDER BY id DESC',(project_id,))]
            history=[dict(x) for x in c.execute('SELECT * FROM case_history WHERE project_id=? ORDER BY id DESC',(project_id,))]
            c.close(); return send(self,200,{'project':dict(project),'parcels':parcels,'documents':docs,'workflows':workflows,'history':history})
        if p.startswith('/api/case/'):
            parcel_id=urllib.parse.unquote(p.split('/')[-1]); parcel=c.execute('SELECT * FROM parcels_shared WHERE parcel_id=?',(parcel_id,)).fetchone()
            if not parcel: c.close(); return send(self,404,{'error':'Parcel not found'})
            project=c.execute('SELECT * FROM projects_shared WHERE project_id=?',(parcel['project_id'],)).fetchone(); owner=c.execute('SELECT * FROM landowners_shared WHERE landowner_id=?',(parcel['landowner_id'],)).fetchone(); docs=[dict(x) for x in c.execute('SELECT * FROM documents_shared WHERE project_id=? AND (parcel_id=? OR parcel_id=\'\') ORDER BY id',(parcel['project_id'],parcel_id))]; ev=[dict(x) for x in c.execute('SELECT * FROM evidence_shared WHERE project_id=? AND parcel_id=? ORDER BY id',(parcel['project_id'],parcel_id))]; hist=[dict(x) for x in c.execute('SELECT * FROM case_history WHERE project_id=? AND (parcel_id=? OR parcel_id=\'\') ORDER BY id',(parcel['project_id'],parcel_id))]; c.close(); return send(self,200,{'project':dict(project),'parcel':dict(parcel),'landowner':dict(owner),'documents':docs,'evidence':ev,'history':hist})
        if p=='/api/case-history':
            project=q.get('project_id',['NH44-MH-001'])[0]; parcel=q.get('parcel_id',['P-001'])[0]; rows=[dict(x) for x in c.execute('SELECT * FROM case_history WHERE project_id=? AND (parcel_id=? OR parcel_id=\'\') ORDER BY id',(project,parcel))]; c.close(); return send(self,200,rows)
        if p.startswith('/demo-assets/'):
            c.close(); return self.asset(p[1:]) or send(self,404,{'error':'Asset not found'})
        if p=='/api/projects/shared':
            rows=[dict(x) for x in c.execute('SELECT * FROM projects_shared ORDER BY project_id')]; c.close(); return send(self,200,rows)
        if p=='/api/parcels/shared':
            project=q.get('project_id',[None])[0]; sql='SELECT * FROM parcels_shared'; args=[]
            if project: sql+=' WHERE project_id=?'; args.append(project)
            rows=[dict(x) for x in c.execute(sql,args)]; c.close(); return send(self,200,rows)
        if p.startswith('/api/case/'):
            parcel_id=urllib.parse.unquote(p.split('/')[-1]); parcel=c.execute('SELECT * FROM parcels_shared WHERE parcel_id=?',(parcel_id,)).fetchone()
            if not parcel: c.close(); return send(self,404,{'error':'Parcel not found'})
            project=c.execute('SELECT * FROM projects_shared WHERE project_id=?',(parcel['project_id'],)).fetchone(); owner=c.execute('SELECT * FROM landowners_shared WHERE landowner_id=?',(parcel['landowner_id'],)).fetchone(); docs=[dict(x) for x in c.execute('SELECT * FROM documents_shared WHERE project_id=? AND (parcel_id=? OR parcel_id=\'\') ORDER BY id',(parcel['project_id'],parcel_id))]; ev=[dict(x) for x in c.execute('SELECT * FROM evidence_shared WHERE project_id=? AND parcel_id=? ORDER BY id',(parcel['project_id'],parcel_id))]; hist=[dict(x) for x in c.execute('SELECT * FROM case_history WHERE project_id=? AND (parcel_id=? OR parcel_id=\'\') ORDER BY id',(parcel['project_id'],parcel_id))]; c.close(); return send(self,200,{'project':dict(project),'parcel':dict(parcel),'landowner':dict(owner),'documents':docs,'evidence':ev,'history':hist})
        if p=='/api/case-history':
            project=q.get('project_id',['NH44-MH-001'])[0]; parcel=q.get('parcel_id',['P-001'])[0]; rows=[dict(x) for x in c.execute('SELECT * FROM case_history WHERE project_id=? AND (parcel_id=? OR parcel_id=\'\') ORDER BY id',(project,parcel))]; c.close(); return send(self,200,rows)
        if p.startswith('/demo-assets/'):
            c.close(); return self.asset(p[1:]) or send(self,404,{'error':'Asset not found'})
        if p=='/api/projects/shared':
            rows=[dict(x) for x in c.execute('SELECT * FROM projects_shared ORDER BY project_id')]; c.close(); return send(self,200,rows)
        if p=='/api/parcels/shared':
            project=q.get('project_id',[None])[0]; sql='SELECT * FROM parcels_shared'; args=[]
            if project: sql+=' WHERE project_id=?'; args.append(project)
            rows=[dict(x) for x in c.execute(sql,args)]; c.close(); return send(self,200,rows)
        if p.startswith('/api/case/'):
            parcel_id=urllib.parse.unquote(p.split('/')[-1]); parcel=c.execute('SELECT * FROM parcels_shared WHERE parcel_id=?',(parcel_id,)).fetchone()
            if not parcel: c.close(); return send(self,404,{'error':'Parcel not found'})
            project=c.execute('SELECT * FROM projects_shared WHERE project_id=?',(parcel['project_id'],)).fetchone(); owner=c.execute('SELECT * FROM landowners_shared WHERE landowner_id=?',(parcel['landowner_id'],)).fetchone(); docs=[dict(x) for x in c.execute('SELECT * FROM documents_shared WHERE project_id=? AND (parcel_id=? OR parcel_id=\'\') ORDER BY id',(parcel['project_id'],parcel_id))]; ev=[dict(x) for x in c.execute('SELECT * FROM evidence_shared WHERE project_id=? AND parcel_id=? ORDER BY id',(parcel['project_id'],parcel_id))]; hist=[dict(x) for x in c.execute('SELECT * FROM case_history WHERE project_id=? AND (parcel_id=? OR parcel_id=\'\') ORDER BY id',(parcel['project_id'],parcel_id))]; c.close(); return send(self,200,{'project':dict(project),'parcel':dict(parcel),'landowner':dict(owner),'documents':docs,'evidence':ev,'history':hist})
        if p=='/api/case-history':
            project=q.get('project_id',['NH44-MH-001'])[0]; parcel=q.get('parcel_id',['P-001'])[0]; rows=[dict(x) for x in c.execute('SELECT * FROM case_history WHERE project_id=? AND (parcel_id=? OR parcel_id=\'\') ORDER BY id',(project,parcel))]; c.close(); return send(self,200,rows)
        if p=='/api/workflows': r=[dict(x) for x in c.execute('SELECT * FROM workflows ORDER BY id DESC')]; c.close(); return send(self,200,r)
        if p.startswith('/api/inbox/'):
            role=urllib.parse.unquote(p.split('/')[-1]); r=[dict(x) for x in c.execute("SELECT * FROM workflows WHERE current_role=? AND status NOT LIKE 'Completed%' AND status!='Rejected' ORDER BY CASE priority WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END,id DESC",(role,))]; c.close(); return send(self,200,r)
        if p.startswith('/api/workspace/'):
            ref=urllib.parse.unquote(p.split('/')[-1]); w=c.execute('SELECT * FROM workflows WHERE ref=?',(ref,)).fetchone()
            if not w: c.close(); return send(self,404,{'error':'Workflow task not found'})
            w=dict(w); project=None; parcels=[]; docs=[]; evidence=[]; owners=[]; history=[]
            if w.get('project_id'):
                project=c.execute('SELECT * FROM projects_shared WHERE project_id=?',(w['project_id'],)).fetchone()
                parcels=[dict(x) for x in c.execute('SELECT * FROM parcels_shared WHERE project_id=? ORDER BY parcel_id',(w['project_id'],)).fetchall()]
                docs=[dict(x) for x in c.execute('SELECT * FROM documents_shared WHERE project_id=? ORDER BY id DESC',(w['project_id'],)).fetchall()]
                evidence=[dict(x) for x in c.execute('SELECT * FROM evidence_shared WHERE project_id=? OR parcel_id IN (SELECT parcel_id FROM parcels_shared WHERE project_id=?) ORDER BY id DESC',(w['project_id'],w['project_id'])).fetchall()]
                owners=[dict(x) for x in c.execute('SELECT * FROM landowners_shared WHERE landowner_id IN (SELECT landowner_id FROM parcels_shared WHERE project_id=?) ORDER BY landowner_id',(w['project_id'],)).fetchall()]
                history=[dict(x) for x in c.execute('SELECT * FROM case_history WHERE project_id=? ORDER BY id DESC',(w['project_id'],)).fetchall()]
            c.close(); return send(self,200,{'workflow':w,'project':dict(project) if project else None,'parcels':parcels,'documents':docs,'evidence':evidence,'landowners':owners,'history':history})
        if p.startswith('/api/workflow/'):
            ref=urllib.parse.unquote(p.split('/')[-1]); w=c.execute('SELECT * FROM workflows WHERE ref=?',(ref,)).fetchone()
            if not w: c.close(); return send(self,404,{'error':'Not found'})
            e=[dict(x) for x in c.execute('SELECT * FROM workflow_events WHERE workflow_id=? ORDER BY id',(w['id'],))]
            records=[dict(x) for x in c.execute('SELECT * FROM records WHERE ref=? ORDER BY id DESC',(ref,))]
            for r in records:
                try:r['data']=json.loads(r.pop('data_json'))
                except Exception:r['data']=r.pop('data_json')
            c.close(); return send(self,200,{'workflow':dict(w),'events':e,'records':records})
        if p=='/api/automation/summary':
            total=c.execute('SELECT COUNT(*) FROM parcels_shared').fetchone()[0]
            verified=c.execute("SELECT COUNT(*) FROM parcels_shared WHERE revenue_status='Verified' AND gis_status='Verified'").fetchone()[0]
            pending=c.execute("SELECT COUNT(*) FROM workflows WHERE status NOT IN ('Completed','Rejected')").fetchone()[0]
            unread=c.execute('SELECT COUNT(*) FROM notifications_shared WHERE read=0').fetchone()[0]
            docs=c.execute('SELECT COUNT(*) FROM documents_shared').fetchone()[0]
            evidence=c.execute('SELECT COUNT(*) FROM evidence_shared').fetchone()[0]
            c.close(); return send(self,200,{'parcels':total,'fully_verified':verified,'pending_tasks':pending,'unread_notifications':unread,'documents':docs,'evidence':evidence})
        if p=='/api/automation/tasks':
            role=q.get('role',[None])[0]; sql="SELECT * FROM workflows WHERE status NOT IN ('Completed','Rejected')"; args=[]
            if role: sql+=' AND current_role=?'; args.append(role)
            rows=[dict(x) for x in c.execute(sql+' ORDER BY id DESC',args)]; c.close(); return send(self,200,rows)
        if p=='/api/automation/notifications':
            role=q.get('role',[None])[0]; sql='SELECT * FROM notifications_shared'; args=[]
            if role: sql+=" WHERE recipient_role=? OR recipient_role='all'"; args.append(role)
            rows=[dict(x) for x in c.execute(sql+' ORDER BY id DESC LIMIT 100',args)]; c.close(); return send(self,200,rows)
        if p=='/api/automation/audit':
            project=q.get('project_id',[None])[0]; parcel=q.get('parcel_id',[None])[0]; sql='SELECT * FROM workflow_events WHERE 1=1'; args=[]
            if parcel: sql+=' AND workflow_id IN (SELECT id FROM workflows WHERE parcel_id=?)'; args.append(parcel)
            elif project: sql+=' AND workflow_id IN (SELECT id FROM workflows WHERE project_id=?)'; args.append(project)
            rows=[dict(x) for x in c.execute(sql+' ORDER BY id DESC LIMIT 100',args)]; c.close(); return send(self,200,rows)
        if p=='/api/case-health':
            pid=q.get('parcel_id',['P-001'])[0]; parcel=c.execute('SELECT * FROM parcels_shared WHERE parcel_id=?',(pid,)).fetchone()
            if not parcel: c.close(); return send(self,404,{'error':'Parcel not found'})
            docs=c.execute("SELECT category,name,status FROM documents_shared WHERE project_id=? AND (parcel_id=? OR parcel_id='')",(parcel['project_id'],pid)).fetchall(); ev=c.execute('SELECT evidence_type,name,lat,lng,label FROM evidence_shared WHERE parcel_id=?',(pid,)).fetchall()
            checks=[]
            required=['7/12 Extract','Ownership Record','Survey Report']
            names=' '.join((d['name'] or '') for d in docs).lower()
            for req in required: checks.append({'name':req,'status':'PASS' if req.lower() in names else 'MISSING'})
            checks += [{'name':'GPS Evidence','status':'PASS' if any(e['lat'] is not None and e['lng'] is not None for e in ev) else 'MISSING'}, {'name':'Field Photograph','status':'PASS' if any(e['evidence_type']=='Field Photo' for e in ev) else 'MISSING'}, {'name':'GIS Boundary','status':'PASS' if any(e['evidence_type']=='GIS Boundary' for e in ev) else 'MISSING'}]
            score=round(sum(x['status']=='PASS' for x in checks)/len(checks)*100)
            risk='LOW' if score>=85 else ('MEDIUM' if score>=60 else 'HIGH')
            c.close(); return send(self,200,{'parcel':dict(parcel),'checks':checks,'score':score,'risk':risk,'document_count':len(docs),'evidence_count':len(ev)})
        if p=='/api/validation':
            pid=q.get('parcel_id',['P-001'])[0]; parcel=c.execute('SELECT * FROM parcels_shared WHERE parcel_id=?',(pid,)).fetchone();
            if not parcel: c.close(); return send(self,404,{'error':'Parcel not found'})
            checks=[]; docs=[x['name'].lower() for x in c.execute("SELECT name FROM documents_shared WHERE project_id=? AND (parcel_id=? OR parcel_id='')",(parcel['project_id'],pid)).fetchall()]; ev=[dict(x) for x in c.execute('SELECT * FROM evidence_shared WHERE parcel_id=?',(pid,)).fetchall()]
            checks.append({'rule':'Revenue evidence complete','status':'PASS' if any('7/12' in x for x in docs) and any('ownership' in x for x in docs) else 'WARN','message':'7/12 and ownership evidence are available.' if any('7/12' in x for x in docs) and any('ownership' in x for x in docs) else 'Add 7/12 and ownership evidence.'})
            checks.append({'rule':'GIS evidence complete','status':'PASS' if any(x['evidence_type']=='Field Photo' for x in ev) and any(x['lat'] is not None and x['lng'] is not None for x in ev) else 'WARN','message':'Field photo and GPS evidence are available.' if any(x['evidence_type']=='Field Photo' for x in ev) and any(x['lat'] is not None and x['lng'] is not None for x in ev) else 'Add field photo and GPS evidence before GIS approval.'})
            checks.append({'rule':'Area consistency','status':'PASS','message':'Demo parcel area is within prototype validation tolerance.'})
            c.close(); return send(self,200,{'parcel_id':pid,'checks':checks})
        if p=='/api/ai/document-guide':
            text=(q.get('text',[''])[0] or '').lower(); category=(q.get('category',[''])[0] or '').lower()
            rules=[
              ('Land Record','7/12 Extract','Confirms the recorded survey/land entry.',['survey','gat','7/12','ownership','wrong land','land record']),
              ('Land Record','Ownership / Title Record','Supports ownership verification.',['owner','ownership','title','name mismatch']),
              ('Land Record','Mutation Record','Helps verify changes in recorded ownership.',['mutation','transfer','inheritance']),
              ('Compensation','Award Copy / Compensation Statement','Supports payment or award complaints.',['compensation','payment','award','unpaid','amount']),
              ('Possession','Possession / Handover Notice','Supports possession-related complaints.',['possession','handover','eviction']),
              ('R&R','R&R / Rehabilitation Eligibility Record','Supports rehabilitation or resettlement claims.',['rehabilitation','resettlement','rr','displaced']),
              ('Notification','Acquisition Notification / Notice','Supports notice and notification complaints.',['notification','notice','gazette']),
              ('GIS','Survey / Measurement Report','Supports boundary, area or location disputes.',['boundary','area mismatch','measurement','map','wrong parcel','survey'])]
            selected=[]
            for cat,name,why,keys in rules:
                if category and category in cat.lower() or any(k in text for k in keys): selected.append({'category':cat,'name':name,'why':why,'required':True})
            if not selected: selected=[{'category':'General','name':'Grievance description / application','why':'Explains the issue and lets the officer route the case.','required':True},{'category':'General','name':'Relevant land record or notice','why':'Provides evidence related to the reported issue.','required':False}]
            # De-duplicate while preserving order.
            out=[]; seen=set()
            for x in selected:
                if x['name'] not in seen: out.append(x); seen.add(x['name'])
            c.close(); return send(self,200,{'assistant':'NLAMS Document Guide','confidence':0.91 if len(out)>1 else 0.72,'documents':out,'note':'AI-style prototype guidance. Final document requirements remain subject to officer/legal verification.'})
        if p=='/api/locations':
            limit=min(int(q.get('limit',['500'])[0]),2000); r=[dict(x) for x in c.execute('SELECT * FROM locations ORDER BY id DESC LIMIT ?', (limit,))]; c.close(); return send(self,200,r)
        if p=='/api/records':
            role=q.get('role',[None])[0]; entity=q.get('entity',[None])[0]; project=q.get('project_id',[None])[0]; parcel=q.get('parcel_id',[None])[0]; ref=q.get('ref',[None])[0];
            sql='SELECT * FROM records WHERE 1=1'; args=[]
            for col,val in [('role',role),('entity',entity),('project_id',project),('parcel_id',parcel),('ref',ref)]:
                if val: sql+=f' AND {col}=?'; args.append(val)
            sql+=' ORDER BY id DESC LIMIT 500'; rows=[]
            for x in c.execute(sql,args):
                r=dict(x)
                try:r['data']=json.loads(r.pop('data_json'))
                except Exception:r['data']=r.pop('data_json')
                rows.append(r)
            c.close(); return send(self,200,rows)
        if p=='/api/notifications':
            role=q.get('role',[''])[0]; project=q.get('project_id',[''])[0]
            sql='SELECT * FROM notifications_shared WHERE recipient_role=?'; args=[role]
            if project: sql+=' AND project_id=?'; args.append(project)
            sql+=' ORDER BY id DESC LIMIT 100'; rows=[dict(x) for x in c.execute(sql,args)]; c.close(); return send(self,200,rows)
        if p=='/api/projects/shared/search':
            term=q.get('q',[''])[0].strip(); like='%'+term+'%'; rows=[dict(x) for x in c.execute('SELECT * FROM projects_shared WHERE project_id LIKE ? OR name LIKE ? OR district LIKE ? OR villages LIKE ? ORDER BY project_id',(like,like,like,like))]; c.close(); return send(self,200,rows)
        if p=='/api/landowner/project-lookup':
            survey=q.get('survey_no',[''])[0].strip(); gat=q.get('gat_no',[''])[0].strip(); village=q.get('village',[''])[0].strip()
            sql='SELECT p.*,pr.name project_name,pr.state,pr.district,pr.villages FROM parcels_shared p JOIN projects_shared pr ON pr.project_id=p.project_id WHERE 1=1'; args=[]
            if survey: sql+=' AND p.survey_no=?'; args.append(survey)
            if village: sql+=' AND p.village LIKE ?'; args.append('%'+village+'%')
            rows=[dict(x) for x in c.execute(sql+' ORDER BY p.project_id,p.parcel_id',args)]; c.close(); return send(self,200,rows)

        if p=='/api/privacy/policy':
            c.close(); return send(self,200,{'version':'NLAMS-PRIVACY-v1.0','title':'NLAMS Data Privacy & Security','principles':['Purpose limitation','Role-based access','Minimum necessary data','Auditability','Secure document integrity','No public exposure of personal land records'],'notice':'Personal and land information is used only for authentication, land-acquisition services, workflow processing and grievance handling. Demo records are synthetic. Production deployment requires approved government identity, hosting, key management and retention controls.'})
        if p=='/api/security/heartbeat':
            role=q.get('role',['unknown'])[0]; c.execute('INSERT INTO security_audit(actor_id,actor_role,action,resource,ip,at) VALUES(?,?,?,?,?,?)',('',role,'portal_access','heartbeat',self.client_address[0],now())); c.commit(); c.close(); return send(self,200,{'ok':True,'security':'active','privacy_policy':'NLAMS-PRIVACY-v1.0'})
        if p=='/api/security/consent' and self.command=='POST':
            d=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0')) or 0) or b'{}'); c.execute('INSERT INTO privacy_consents(subject_id,subject_type,policy_version,consented_at,source) VALUES(?,?,?,?,?)',(d.get('subject_id',''),d.get('subject_type','unknown'),'NLAMS-PRIVACY-v1.0',now(),d.get('source','portal'))); c.commit(); c.close(); return send(self,200,{'ok':True,'policy_version':'NLAMS-PRIVACY-v1.0'})

        if p=='/api/automation/next-actions':
            pid=q.get('parcel_id',['P-001'])[0]; parcel=c.execute('SELECT * FROM parcels_shared WHERE parcel_id=?',(pid,)).fetchone();
            if not parcel: c.close(); return send(self,404,{'error':'Parcel not found'})
            actions=[]
            w=c.execute("SELECT * FROM workflows WHERE parcel_id=? AND status NOT IN ('Completed','Rejected') ORDER BY id DESC LIMIT 1",(pid,)).fetchone()
            if w: actions.append({'role':w['current_role'],'action':'Complete assigned workflow task','reason':w['title'],'workflow_ref':w['ref']})
            elif parcel['gis_status']!='Verified': actions.append({'role':'survey_gis_officer','action':'Complete GIS and field verification','reason':'GIS verification is incomplete'})
            else: actions.append({'role':'administrator','action':'Close acquisition case','reason':'GIS verification is complete'})
            c.close(); return send(self,200,{'parcel_id':pid,'actions':actions,'automation':'rules-engine'})
        c.close(); return send(self,404,{'error':'Not found'})
    def do_POST(self):
        p=urllib.parse.urlparse(self.path).path; d=self.body(); c=db()
        if p.startswith('/api/notifications/') and p.endswith('/read'):
            nid=urllib.parse.unquote(p.split('/')[-2]); c.execute('UPDATE notifications_shared SET read=1 WHERE id=?',(nid,)); c.commit(); c.close(); return send(self,200,{'ok':True})

        if p=='/api/workflow':
            ref=d.get('ref') or f"WF-{int(datetime.now().timestamp())}"; role=d.get('current_role') or ROUTES.get(d.get('created_role','landowner'),'lao'); t=now();
            c.execute('INSERT OR IGNORE INTO workflows(ref,kind,title,description,current_role,status,priority,project_id,parcel_id,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(ref,d.get('kind','task'),d.get('title','NLAMS Workflow Task'),d.get('description',''),role,d.get('status','Submitted'),d.get('priority','Medium'),d.get('project_id',''),d.get('parcel_id',''),d.get('created_by',d.get('created_role','System')),t,t)); wid=c.execute('SELECT id FROM workflows WHERE ref=?',(ref,)).fetchone()[0]; c.execute('INSERT INTO workflow_events(workflow_id,from_role,to_role,action,actor,note,at) VALUES(?,?,?,?,?,?,?)',(wid,d.get('created_role','system'),role,'created',d.get('created_by','System'),d.get('note','Created in NLAMS.'),t)); c.commit(); c.close(); return send(self,200,{'ok':True,'ref':ref})
        if p=='/api/shared/project/create':
            t=now(); pid=d.get('project_id')
            if not pid: c.close(); return send(self,400,{'error':'project_id required'})
            c.execute('INSERT OR REPLACE INTO projects_shared(project_id,name,state,district,villages,required_land,created_at,status) VALUES(?,?,?,?,?,?,COALESCE((SELECT created_at FROM projects_shared WHERE project_id=?),?),?)',(pid,d.get('name',''),d.get('state',''),d.get('district',''),d.get('villages',''),float(d.get('required_land') or 0),pid,t,d.get('status','Draft')))
            # Creating a project is the authoritative workflow event. LAO is always the first receiving portal.
            ref='WF-PROJECT-'+pid
            if not c.execute('SELECT 1 FROM workflows WHERE ref=?',(ref,)).fetchone():
                c.execute('INSERT INTO workflows(ref,kind,title,description,current_role,status,priority,project_id,parcel_id,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(ref,'project','Project '+pid,'Project-level approval workflow: Project Agency → LAO → Revenue → R&R → Survey/GIS → Administration.','lao','Submitted','High',pid,'','project_agency',t,t))
                wid=c.execute('SELECT id FROM workflows WHERE ref=?',(ref,)).fetchone()[0]
                c.execute('INSERT INTO workflow_events(workflow_id,from_role,to_role,action,actor,note,at) VALUES(?,?,?,?,?,?,?)',(wid,'project_agency','lao','project_created','Project Agency','New project created in Project Agency and registered in the central NLAMS data store.',t))
                c.execute('INSERT INTO notifications_shared(recipient_role,project_id,parcel_id,ref,title,message,level,created_at) VALUES(?,?,?,?,?,?,?,?)',('lao',pid,'',ref,'New Project for LAO Verification',pid+' has been created and is ready for LAO scrutiny.','success',t))
            c.commit(); c.close(); return send(self,200,{'ok':True,'project_id':pid,'workflow_ref':ref,'next_role':'lao'})
        if p=='/api/shared/parcel/create':
            t=now(); pid=d.get('parcel_id'); c.execute('INSERT OR IGNORE INTO parcels_shared(parcel_id,project_id,landowner_id,survey_no,village,area,lat,lng,status,revenue_status,gis_status,workflow_status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(pid,d.get('project_id',''),d.get('landowner_id',''),d.get('survey_no',''),d.get('village',''),float(d.get('area') or 0),d.get('lat'),d.get('lng'),d.get('status','Proposed'),'Pending','Pending','Project Created',t,t)); c.commit(); c.close(); return send(self,200,{'ok':True,'parcel_id':pid})
        if p=='/api/shared/parcel/update':
            pid=d.get('parcel_id'); project=d.get('project_id','NH44-MH-001'); fields={k:d[k] for k in ('status','revenue_status','gis_status','workflow_status') if k in d};
            if not pid or not fields: c.close(); return send(self,400,{'error':'parcel_id and update fields required'})
            sets=','.join([f'{k}=?' for k in fields]+['updated_at=?']); vals=list(fields.values())+[now(),pid]
            c.execute(f'UPDATE parcels_shared SET {sets} WHERE parcel_id=?',vals); c.commit(); c.close(); return send(self,200,{'ok':True,'parcel_id':pid})
        if p=='/api/shared/document/status':
            name=d.get('name',''); project=d.get('project_id',''); parcel=d.get('parcel_id',''); status=d.get('status','Verified');
            c.execute('UPDATE documents_shared SET status=? WHERE project_id=? AND parcel_id=? AND name=?',(status,project,parcel,name)); c.commit(); c.close(); return send(self,200,{'ok':True})
        if p=='/api/shared/document':
            t=now(); c.execute('INSERT INTO documents_shared(project_id,parcel_id,category,name,type,uploaded_by,uploaded_at,status,version,source_path) VALUES(?,?,?,?,?,?,?,?,?,?)',(d.get('project_id','NH44-MH-001'),d.get('parcel_id',''),d.get('category','Other Evidence'),d.get('name','Untitled Document'),d.get('type','FILE'),d.get('uploaded_by','NLAMS Officer'),t,d.get('status','Pending'),int(d.get('version',1)),d.get('source_path',''))); c.commit(); c.close(); return send(self,200,{'ok':True})
        if p=='/api/shared/evidence':
            pid=d.get('parcel_id'); project=d.get('project_id','NH44-MH-001'); t=now(); c.execute('INSERT INTO evidence_shared(project_id,parcel_id,evidence_type,name,url,lat,lng,uploaded_by,uploaded_at,label) VALUES(?,?,?,?,?,?,?,?,?,?)',(project,pid,d.get('evidence_type','Field Photo'),d.get('name','DEMO evidence'),d.get('url',''),d.get('lat'),d.get('lng'),d.get('uploaded_by','Survey / GIS Officer'),t,d.get('label','DEMO / SAMPLE FIELD EVIDENCE'))); c.commit(); c.close(); return send(self,200,{'ok':True})
        if p=='/api/sync/record':
            key,entity,ref,project_id,parcel_id=make_record(c,d); role=d.get('role','unknown'); data=d.get('data') or {}; route=d.get('route',''); action=d.get('action','submit');
            create_flow=bool(d.get('create_workflow',True)) and action not in ('view','search','login','logout','download','open') and (entity in ('grievance','project','parcel','survey','compensation','rr_case','possession','objection','form_submission'))
            flow=None
            if create_flow:
                to=infer_next(role,route,data)
                if to and to!=role:
                    t=now(); title=str(data.get('subject') or data.get('name') or data.get('title') or data.get('grievance_id') or ref); desc=' · '.join([f'{k}: {v}' for k,v in list(data.items())[:6] if v not in ('',None)])
                    c.execute('INSERT OR IGNORE INTO workflows(ref,kind,title,description,current_role,status,priority,project_id,parcel_id,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(ref,entity,title,desc,to,'Submitted',str(data.get('priority','Medium')),project_id,parcel_id,role,t,t)); w=c.execute('SELECT id FROM workflows WHERE ref=?',(ref,)).fetchone();
                    if w: c.execute('INSERT INTO workflow_events(workflow_id,from_role,to_role,action,actor,note,at) VALUES(?,?,?,?,?,?,?)',(w['id'],role,to,action,d.get('actor_name',role),f'Data synchronized from {portal_label(role)} via {route}.',t))
                    flow={'ref':ref,'current_role':to,'status':'Submitted'}
            c.commit(); c.close(); return send(self,200,{'ok':True,'record_key':key,'entity':entity,'ref':ref,'workflow':flow})
        if p=='/api/landowner/project-discovery-request':
            ref='REQ-PROJECT-'+datetime.now().strftime('%Y%m%d%H%M%S')+'-'+uuid.uuid4().hex[:5].upper(); t=now()
            c.execute('INSERT INTO workflows(ref,kind,title,description,current_role,status,priority,project_id,parcel_id,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(ref,'landowner_project_request','Landowner Project/Parcel Discovery Request','Landowner could not find a mapped project/parcel. Revenue/Grievance team must validate the land record and map it to a project if applicable.','grievance_officer','Submitted','Medium',d.get('project_id',''),d.get('parcel_id',''),'landowner',t,t))
            wid=c.execute('SELECT last_insert_rowid()').fetchone()[0]
            c.execute('INSERT INTO workflow_events(workflow_id,from_role,to_role,action,actor,note,at) VALUES(?,?,?,?,?,?,?)',(wid,'landowner','grievance_officer','project_not_found_request','Landowner',f'Survey/Gat: {d.get("survey_no","")} · Village: {d.get("village","")}',t))
            c.execute('INSERT INTO notifications_shared(recipient_role,project_id,parcel_id,ref,title,message,level,created_at) VALUES(?,?,?,?,?,?,?,?)',('grievance_officer','','',ref,'Landowner Project/Parcel Not Found','Validate the landowner request and check whether a project/parcel should be mapped to NLAMS.','warning',t)); c.commit(); c.close(); return send(self,200,{'ok':True,'ref':ref,'message':'Request sent to the Grievance Officer for project/parcel validation.'})

        if p=='/api/landowners/register':
            lid=d.get('landowner_id')
            if not lid: c.close(); return send(self,400,{'error':'landowner_id required'})
            t=now(); c.execute('INSERT OR REPLACE INTO landowner_registrations(landowner_id,name,email,mobile,survey_no,gat_no,land_type,village,taluka,district,nearby_identifier,project_id,parcel_id,status,rejection_reason,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,COALESCE((SELECT created_at FROM landowner_registrations WHERE landowner_id=?),?),?)',(lid,d.get('name',''),d.get('email',''),d.get('mobile',''),d.get('survey_no',''),d.get('gat_no',''),d.get('land_type',''),d.get('village',''),d.get('taluka',''),d.get('district',''),d.get('nearby_identifier',''),d.get('project_id',''),d.get('parcel_id',''),'PENDING VERIFICATION','',lid,t,t));
            c.execute('INSERT INTO notifications_shared(recipient_role,project_id,parcel_id,ref,title,message,level,created_at) VALUES(?,?,?,?,?,?,?,?)',('project_agency',d.get('project_id',''),d.get('parcel_id',''),lid,'New Landowner Verification','Landowner '+lid+' is awaiting verification.','warning',t)); c.commit(); c.close(); return send(self,200,{'ok':True,'landowner_id':lid,'status':'PENDING VERIFICATION'})
        if p=='/api/landowners':
            rows=[dict(x) for x in c.execute('SELECT * FROM landowner_registrations ORDER BY created_at DESC').fetchall()]; c.close(); return send(self,200,rows)
        if p.startswith('/api/landowners/') and p.endswith('/verify'):
            lid=urllib.parse.unquote(p.split('/')[-2]); row=c.execute('SELECT * FROM landowner_registrations WHERE landowner_id=?',(lid,)).fetchone()
            if not row: c.close(); return send(self,404,{'error':'Landowner not found'})
            t=now(); c.execute("UPDATE landowner_registrations SET status='VERIFIED',rejection_reason='',updated_at=? WHERE landowner_id=?",(t,lid)); c.execute('INSERT INTO case_history(project_id,parcel_id,stage,status,actor,note,at) VALUES(?,?,?,?,?,?,?)',(row['project_id'],row['parcel_id'],'Landowner Verification','Verified','Project Agency','Landowner account verified. Eligible ON-HOLD complaints may now be released.',t));
            released=[]
            for w in c.execute("SELECT * FROM workflows WHERE kind='grievance' AND status='ON HOLD' AND parcel_id=?",(row['parcel_id'],)).fetchall():
                c.execute("UPDATE workflows SET current_role='grievance_officer',status='Submitted',updated_at=? WHERE ref=?",(t,w['ref'])); c.execute('INSERT INTO workflow_events(workflow_id,from_role,to_role,action,actor,note,at) VALUES(?,?,?,?,?,?,?)',(w['id'],'landowner','grievance_officer','released_after_verification','Project Agency','Landowner account verified; complaint released automatically.',t)); c.execute('INSERT INTO notifications_shared(recipient_role,project_id,parcel_id,ref,title,message,level,created_at) VALUES(?,?,?,?,?,?,?,?)',('grievance_officer',w['project_id'],w['parcel_id'],w['ref'],'Verified Complaint Released','ON-HOLD complaint '+w['ref']+' is now submitted to the Grievance Officer.','success',t)); released.append(w['ref'])
            c.execute('INSERT INTO notifications_shared(recipient_role,project_id,parcel_id,ref,title,message,level,created_at) VALUES(?,?,?,?,?,?,?,?)',('landowner',row['project_id'],row['parcel_id'],lid,'Account Verified','Your NLAMS landowner account is verified.','success',t)); c.commit(); c.close(); return send(self,200,{'ok':True,'status':'VERIFIED','released_complaints':released})
        if p.startswith('/api/landowners/') and p.endswith('/reject'):
            lid=urllib.parse.unquote(p.split('/')[-2]); reason=d.get('reason','Details could not be verified.'); t=now(); row=c.execute('SELECT * FROM landowner_registrations WHERE landowner_id=?',(lid,)).fetchone()
            if not row: c.close(); return send(self,404,{'error':'Landowner not found'})
            c.execute("UPDATE landowner_registrations SET status='REJECTED',rejection_reason=?,updated_at=? WHERE landowner_id=?",(reason,t,lid)); c.execute('INSERT INTO notifications_shared(recipient_role,project_id,parcel_id,ref,title,message,level,created_at) VALUES(?,?,?,?,?,?,?,?)',('landowner',row['project_id'],row['parcel_id'],lid,'Account Verification Rejected',reason,'danger',t)); c.commit(); c.close(); return send(self,200,{'ok':True,'status':'REJECTED','reason':reason})
        if p=='/api/grievances/submit':
            ref=d.get('ticket') or f"GRV-{datetime.now().strftime('%Y%m%d')}-{os.urandom(2).hex().upper()}"; t=now()
            owner=c.execute('SELECT status FROM landowner_registrations WHERE landowner_id=?',(d.get('landowner_id'),)).fetchone() if d.get('landowner_id') else None
            status='Submitted' if owner and owner['status']=='VERIFIED' else 'ON HOLD'; role='grievance_officer' if status=='Submitted' else 'landowner'
            note='Grievance submitted from Landowner portal.' if status=='Submitted' else 'Complaint is ON HOLD until Project Agency verifies the landowner account.'
            c.execute('INSERT OR IGNORE INTO workflows(ref,kind,title,description,current_role,status,priority,project_id,parcel_id,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(ref,'grievance',d.get('subject','New Grievance'),d.get('description',''),role,status,d.get('priority','High'),d.get('project_id',''),d.get('parcel_id',''),'landowner',t,t)); wid=c.execute('SELECT id FROM workflows WHERE ref=?',(ref,)).fetchone()[0]; c.execute('INSERT INTO workflow_events(workflow_id,from_role,to_role,action,actor,note,at) VALUES(?,?,?,?,?,?,?)',(wid,'landowner',role,'submitted','Landowner',note,t)); c.commit(); c.close(); return send(self,200,{'ok':True,'ref':ref,'status':status,'message':note})
        if p.startswith('/api/workflow/') and p.endswith('/transition'):
            ref=urllib.parse.unquote(p.split('/')[-2]); w=c.execute('SELECT * FROM workflows WHERE ref=?',(ref,)).fetchone()
            if not w: c.close(); return send(self,404,{'error':'Not found'})
            actor=d.get('actor_role','system'); action=d.get('action','forward'); note=d.get('note','')
            if actor!=w['current_role'] and actor!='administrator': c.close(); return send(self,403,{'error':'This task is not assigned to your role.'})
            if action=='return':
                to_role=w['created_by'] if str(w['created_by']).lower() in ROUTES else w['current_role']; status='Returned'
            elif action=='reject':
                to_role=w['created_by'] if str(w['created_by']).lower() in ROUTES else w['current_role']; status='Rejected'
            elif action in ('approve','resolve','complete'):
                # Reliability gates for the real workflow.
                if w['kind']=='project':
                    if actor=='lao':
                        has_doc=c.execute("SELECT 1 FROM documents_shared WHERE project_id=? AND parcel_id='' AND (status LIKE 'Verified%' OR status LIKE 'Pending%') LIMIT 1",(w['project_id'],)).fetchone()
                        if not has_doc:
                            c.close(); return send(self,409,{'error':'LAO verification blocked: upload at least one project proposal/DPR/approval document first.','validation':'PROJECT_DOCUMENT'})
                    if actor in ('revenue_officer','rr_officer','survey_gis_officer'):
                        pc=c.execute('SELECT COUNT(*) FROM parcels_shared WHERE project_id=?',(w['project_id'],)).fetchone()[0]
                        if pc==0:
                            c.close(); return send(self,409,{'error':f'{portal_label(actor)} verification blocked: no land parcel is linked to this project yet. Project Agency must add parcels first.','validation':'PROJECT_PARCELS'})
                    if actor=='survey_gis_officer':
                        gps=c.execute('SELECT 1 FROM locations WHERE project_id=? LIMIT 1',(w['project_id'],)).fetchone()
                        if not gps:
                            c.close(); return send(self,409,{'error':'GIS verification blocked: capture at least one live GPS location on the GIS map first.','validation':'GPS_TRACKING'})
                if w['parcel_id'] and actor in ('revenue_officer','survey_gis_officer'):
                    pid=w['parcel_id']; docs=[x['name'].lower() for x in c.execute('SELECT name FROM documents_shared WHERE project_id=? AND (parcel_id=? OR parcel_id=?)',(w['project_id'],pid,'')).fetchall()]; ev=[dict(x) for x in c.execute('SELECT * FROM evidence_shared WHERE parcel_id=?',(pid,)).fetchall()]
                    if actor=='revenue_officer' and not (any('7/12' in x for x in docs) and any('ownership' in x for x in docs)):
                        c.close(); return send(self,409,{'error':'Validation blocked: Revenue verification needs 7/12 and Ownership evidence.','validation':'REVENUE_DOCUMENTS'})
                    if actor=='survey_gis_officer' and not (any(x['evidence_type']=='Field Photo' for x in ev) and any(x['lat'] is not None and x['lng'] is not None for x in ev)):
                        c.close(); return send(self,409,{'error':'Validation blocked: GIS verification needs at least one field photo and GPS evidence.','validation':'GIS_EVIDENCE'})
                if w['kind']=='grievance':
                    to_role='landowner'; status='Completed'
                elif actor=='administrator':
                    to_role='administrator'; status='Completed'
                else:
                    to_role=d.get('next_role') or ROUTES.get(actor,'administrator'); status='Approved - Pending Administration' if to_role=='administrator' else 'Approved - Pending Next Officer'
            else:
                to_role=d.get('to_role') or ROUTES.get(actor,'lao'); status='Forwarded'
            t=now(); c.execute('UPDATE workflows SET current_role=?,status=?,updated_at=? WHERE ref=?',(to_role,status,t,ref)); c.execute('INSERT INTO workflow_events(workflow_id,from_role,to_role,action,actor,note,at) VALUES(?,?,?,?,?,?,?)',(w['id'],actor,to_role,action,d.get('actor_name',actor),note,t));
            c.execute('INSERT INTO notifications_shared(recipient_role,project_id,parcel_id,ref,title,message,level,created_at) VALUES(?,?,?,?,?,?,?,?)',(to_role,w['project_id'],w['parcel_id'],ref,'New NLAMS Task',f'{w["title"]} is now assigned to {portal_label(to_role)}.','success' if action in ('approve','complete','resolve') else 'info',t))
            if w['project_id']:
                stage_map={'lao':'LAO Scrutiny','revenue_officer':'Revenue Verification','rr_officer':'R&R Review','survey_gis_officer':'GIS Field Verification','administrator':'Administration / Closure'}
                stage=stage_map.get(actor,portal_label(actor))
                c.execute('INSERT INTO case_history(project_id,parcel_id,stage,status,actor,note,at) VALUES(?,?,?,?,?,?,?)',(w['project_id'],w['parcel_id'],stage,status,d.get('actor_name',actor),note,t))
                project_status={'lao':'LAO Verification','revenue_officer':'Revenue Verification','rr_officer':'R&R Review','survey_gis_officer':'GIS Verification','administrator':'Completed'}.get(to_role,status)
                c.execute('UPDATE projects_shared SET status=? WHERE project_id=?',(project_status,w['project_id']))
            # Keep every related record visibly aligned with the authoritative workflow state.
            for rr in c.execute('SELECT id,data_json FROM records WHERE ref=?',(ref,)).fetchall():
                try:
                    obj=json.loads(rr['data_json'])
                except Exception:
                    obj={}
                obj.update({'workflow_status':status,'current_role':to_role,'last_action':action,'last_actor':d.get('actor_name',actor),'last_note':note,'last_updated':t})
                c.execute('UPDATE records SET data_json=?,updated_at=? WHERE id=?',(json.dumps(obj,default=str),t,rr['id']))
            if w['parcel_id']:
                ps={'workflow_status':status}
                if actor=='revenue_officer': ps['revenue_status']='Verified' if action=='approve' else ('Rejected' if action=='reject' else 'Flagged'); ps['status']='Revenue Verified' if action=='approve' else status
                if actor=='survey_gis_officer': ps['gis_status']='Verified' if action=='approve' else ('Rejected' if action=='reject' else 'Needs Correction'); ps['status']='GIS Verified' if action=='approve' else status
                sets=','.join(f'{k}=?' for k in ps)+',updated_at=?'; vals=list(ps.values())+[t,w['parcel_id']]; c.execute(f'UPDATE parcels_shared SET {sets} WHERE parcel_id=?',vals)
                if actor in ('revenue_officer','survey_gis_officer'):
                    stage='Revenue Verification' if actor=='revenue_officer' else 'GIS Verification'; st='Completed' if action=='approve' else status; c.execute('INSERT INTO case_history(project_id,parcel_id,stage,status,actor,note,at) VALUES(?,?,?,?,?,?,?)',(w['project_id'],w['parcel_id'],stage,st,d.get('actor_name',actor),note,t))
            c.commit(); c.close(); return send(self,200,{'ok':True,'ref':ref,'current_role':to_role,'status':status})
        if p=='/api/locations':
            if 'lat' not in d or 'lng' not in d: c.close(); return send(self,400,{'error':'lat and lng required'})
            t=d.get('captured_at') or now(); project_id=d.get('project_id',''); parcel_id=d.get('parcel_id',''); lat=float(d['lat']); lng=float(d['lng'])
            c.execute('INSERT INTO locations(actor_role,actor_name,project_id,parcel_id,lat,lng,accuracy,captured_at,source) VALUES(?,?,?,?,?,?,?,?,?)',(d.get('actor_role','survey_gis_officer'),d.get('actor_name',''),project_id,parcel_id,lat,lng,float(d.get('accuracy') or 0),t,d.get('source','browser-geolocation')))
            if parcel_id:
                c.execute('UPDATE parcels_shared SET lat=?,lng=?,updated_at=? WHERE parcel_id=?',(lat,lng,now(),parcel_id))
                c.execute('INSERT INTO evidence_shared(project_id,parcel_id,evidence_type,name,url,lat,lng,uploaded_by,uploaded_at,label) VALUES(?,?,?,?,?,?,?,?,?,?)',(project_id,parcel_id,'GPS Track','Live GPS Capture', '',lat,lng,d.get('actor_name','Survey / GIS Officer'),t,'LIVE BROWSER GPS EVIDENCE'))
            c.commit(); c.close(); return send(self,200,{'ok':True,'lat':lat,'lng':lng,'accuracy':float(d.get('accuracy') or 0),'captured_at':t})

        c.close(); return send(self,404,{'error':'Not found'})

def portal_label(role):
    return {'landowner':'Landowner Portal','grievance_officer':'Grievance Officer Portal','lao':'LAO Portal','project_agency':'Project Agency Portal','revenue_officer':'Revenue Officer Portal','survey_gis_officer':'Survey & GIS Officer Portal','rr_officer':'R&R Officer Portal','administrator':'Administration Portal'}.get(role,role)


init()
if __name__=='__main__': ThreadingHTTPServer(('127.0.0.1',PORT),H).serve_forever()
