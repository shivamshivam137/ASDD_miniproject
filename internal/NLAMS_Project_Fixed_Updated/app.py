
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_file
import sqlite3, csv, io, json, os
from datetime import datetime, date, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "nlams.db")
UPLOAD_DIR = os.path.join(BASE, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=False, PERMANENT_SESSION_LIFETIME=1800)
app.secret_key = "nlams-demo-secret"

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS projects(
      id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT UNIQUE, name TEXT, ptype TEXT,
      department TEXT, state TEXT, district TEXT, taluka TEXT, villages TEXT,
      description TEXT, cost_cr REAL, duration_months INTEGER, land_required REAL,
      land_acquired REAL DEFAULT 0, stage TEXT, progress INTEGER DEFAULT 0,
      risk INTEGER DEFAULT 0, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS parcels(
      id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, survey_no TEXT, village TEXT,
      taluka TEXT, district TEXT, area REAL, land_type TEXT, status TEXT,
      lat REAL, lng REAL, owner TEXT, disputed INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS documents(
      id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, name TEXT, dtype TEXT,
      status TEXT, uploaded_at TEXT
    );
    CREATE TABLE IF NOT EXISTS compensation(
      id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, family_id TEXT, owner TEXT,
      parcel TEXT, assessed REAL, approved REAL, disbursed REAL, status TEXT, payment_ref TEXT
    );
    CREATE TABLE IF NOT EXISTS rr(
      id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, family_id TEXT, head TEXT,
      village TEXT, land_area REAL, status TEXT, benefit TEXT, progress INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS grievances(
      id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, grievance_id TEXT, citizen TEXT,
      category TEXT, description TEXT, status TEXT, priority TEXT, assigned_to TEXT,
      created_at TEXT, updated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS notifications(
      id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, body TEXT, ntype TEXT,
      read_flag INTEGER DEFAULT 0, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS audit(
      id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, action TEXT, actor TEXT, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS landowner_verifications(landowner_id TEXT PRIMARY KEY,name TEXT,mobile TEXT,email TEXT,survey_no TEXT,gat_no TEXT,village TEXT,taluka TEXT,district TEXT,project_id TEXT,parcel_id TEXT,registration_date TEXT,status TEXT,rejection_reason TEXT);
    """)
    if con.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        seed_projects = [
          ("NH44-MH-001","NH-44 Highway Expansion","Highway","Ministry of Road Transport & Highways","Maharashtra","Pune","Pune","Pimpalgaon, Wagholi","Widening and strengthening of NH-44 corridor.",100,30,100,0,"Project Created",0,10),
          ("NLAMS-2026-002","Western DFC","Railway","Ministry of Railways","Gujarat","Surat","Olpad","Suina, Kim","Dedicated freight corridor land package.",320,42,320,110,"Under Review",30,54),
          ("NLAMS-2026-003","PM GatiShakti Corridor","Road","Government of Maharashtra","Maharashtra","Raigad","Panvel","Khalapur, Rasayani","Multimodal connectivity corridor.",280,24,280,210,"Notification Issued",60,38),
          ("NLAMS-2026-004","Solar Park Development","Renewable Energy","MNRE","Madhya Pradesh","Rewa","Gurh","Gurh, Semariya","Utility-scale renewable energy park.",150,20,150,32,"Planning",20,22),
          ("NLAMS-2026-005","Delhi-Mumbai Expressway","Highway","NHAI","Maharashtra","Nashik","Sinnar","Sinnar, Dodi","Expressway access and service corridor.",620,36,620,510,"Land Acquisition",75,61)
        ]
        projects = [(*project, now) for project in seed_projects]
        con.executemany("""INSERT INTO projects(project_id,name,ptype,department,state,district,taluka,villages,description,cost_cr,duration_months,land_required,land_acquired,stage,progress,risk,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", projects)
        parcels = [
          ("NH44-MH-001","125","Pimpalgaon","Pune","Pune",2.50,"Agricultural","Proposed",18.5204,73.8567,"Demo Owner A",0),
          ("NH44-MH-001","126","Pimpalgaon","Pune","Pune",3.00,"Agricultural","Proposed",18.5230,73.8590,"Demo Owner B",0),
          ("NH44-MH-001","128","Wagholi","Pune","Pune",1.80,"Agricultural","Proposed",18.5750,73.9850,"Demo Owner C",0),
        ]
        con.executemany("""INSERT INTO parcels(project_id,survey_no,village,taluka,district,area,land_type,status,lat,lng,owner,disputed)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", parcels)
        docs = [
          ("NLAMS-2026-001","NH44_DPR.pdf","DPR","Verified"),("NLAMS-2026-001","Land_Requirement.xlsx","Land Requirement","Verified"),
          ("NLAMS-2026-001","Alignment_Map.pdf","Map","Verified"),("NLAMS-2026-002","DFC_DPR.pdf","DPR","Pending"),
          ("NLAMS-2026-003","Corridor_Plan.pdf","Project Plan","Verified")
        ]
        con.executemany("INSERT INTO documents(project_id,name,dtype,status,uploaded_at) VALUES(?,?,?,?,?)",
                        [(a,b,c,d,now) for a,b,c,d in docs])
        comps = [
          ("NLAMS-2026-001","R&R-00156","Suresh Pawar","125/2",42.5,40,38,"Disbursed","PFMS-2026-00156"),
          ("NLAMS-2026-001","R&R-00157","Sunita More","126/1",31.2,31.2,31.2,"Disbursed","PFMS-2026-00157"),
          ("NLAMS-2026-001","R&R-00158","Ramesh Jadhav","88/4",58.0,55,0,"Pending",""),
          ("NLAMS-2026-001","R&R-00159","Lata Patil","91/7",22.4,20,10,"Part Disbursed","PFMS-2026-00159")
        ]
        con.executemany("""INSERT INTO compensation(project_id,family_id,owner,parcel,assessed,approved,disbursed,status,payment_ref)
                           VALUES(?,?,?,?,?,?,?,?,?)""", comps)
        rrs = [
          ("NLAMS-2026-001","R&R-00156","Suresh Pawar","Pimpalgaon",0.45,"Completed","House + Financial",100),
          ("NLAMS-2026-001","R&R-00157","Sunita More","Pimpalgaon",0.32,"Completed","House + Employment",100),
          ("NLAMS-2026-001","R&R-00158","Ramesh Jadhav","Khalapur",0.60,"Pending","House",25),
          ("NLAMS-2026-001","R&R-00159","Lata Patil","Khalapur",0.28,"In Progress","Financial + Skill",60),
          ("NLAMS-2026-001","R&R-00160","Ganesh Shinde","Nerul",0.50,"Rejected","Financial",0),
          ("NLAMS-2026-001","R&R-00161","Meena Deshmukh","Nerul",0.42,"Completed","House + Employment",100)
        ]
        con.executemany("""INSERT INTO rr(project_id,family_id,head,village,land_area,status,benefit,progress)
                           VALUES(?,?,?,?,?,?,?,?)""", rrs)
        grievances = [
          ("NLAMS-2026-001","GRV-2026-014","Ramesh Jadhav","Compensation","My approved compensation has not been received.","Open","High","LAO"),
          ("NLAMS-2026-001","GRV-2026-015","Lata Patil","R&R","Request update on skill development benefit.","In Progress","Medium","R&R Officer"),
          ("NLAMS-2026-003","GRV-2026-016","Anita More","Land Record","Survey boundary needs correction.","Resolved","Low","Land Officer")
        ]
        con.executemany("""INSERT INTO grievances(project_id,grievance_id,citizen,category,description,status,priority,assigned_to,created_at,updated_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?)""",
                        [(*g,now,now) for g in grievances])
        ns = [
          ("3 approvals require attention","Pending approvals may delay NH-44 Expansion.","warning"),
          ("Compensation batch processed","Payment PFMS-2026-00157 confirmed.","success"),
          ("New grievance raised","GRV-2026-014 needs review.","danger"),
          ("R&R plan submitted","R&R plan submitted for 12 families.","info")
        ]
        con.executemany("INSERT INTO notifications(title,body,ntype,created_at) VALUES(?,?,?,?)",
                        [(*n,now) for n in ns])
        con.execute("INSERT INTO audit(project_id,action,actor,created_at) VALUES(?,?,?,?)",
                    ("NLAMS-2026-001","Seeded demo project data","System",now))
        con.commit()
    con.close()

init_db()

def sync_shared(payload):
    import urllib.request, json as _json
    try:
        req=urllib.request.Request("http://127.0.0.1:8090/api/shared/"+payload.pop("_endpoint"),data=_json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
        urllib.request.urlopen(req,timeout=1).read()
    except Exception:
        pass


def stats():
    con = db()
    try:
        p = con.execute("SELECT * FROM projects").fetchall()
        return {
          "projects": len(p),
          "land_required": sum(x["land_required"] or 0 for x in p),
          "land_acquired": sum(x["land_acquired"] or 0 for x in p),
          "cost": sum(x["cost_cr"] or 0 for x in p),
          "families": con.execute("SELECT COUNT(*) FROM rr").fetchone()[0],
          "pending_approvals": 3,
          "rr_benefits": con.execute("SELECT COUNT(*) FROM rr WHERE status='Completed'").fetchone()[0]
        }
    finally:
        con.close()

@app.context_processor
def inject():
    return {"now": datetime.now().strftime("%d %b %Y %H:%M"), "stats": stats()}


@app.after_request
def _nlams_security_headers(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='SAMEORIGIN'
    response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    response.headers['Permissions-Policy']='geolocation=(self), camera=(), microphone=()'
    response.headers['Cache-Control']='no-store'
    return response

@app.route("/")
def dashboard():
    con=db()
    projects=con.execute("SELECT * FROM projects ORDER BY id").fetchall()
    activities=con.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 6").fetchall()
    notes=con.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 5").fetchall()
    con.close()
    return render_template("dashboard.html", projects=projects, activities=activities, notes=notes)

@app.route("/projects")
def projects():
    q=request.args.get("q","").strip()
    stage=request.args.get("stage","")
    con=db()
    sql="SELECT * FROM projects WHERE 1=1"; args=[]
    if q:
        sql += " AND (project_id LIKE ? OR name LIKE ? OR district LIKE ? OR villages LIKE ?)"
        args += [f"%{q}%"]*4
    if stage:
        sql += " AND stage=?"; args.append(stage)
    rows=con.execute(sql+" ORDER BY id",args).fetchall()
    stages=[r[0] for r in con.execute("SELECT DISTINCT stage FROM projects").fetchall()]
    con.close()
    return render_template("projects.html", projects=rows, stages=stages, q=q, selected_stage=stage)

@app.route("/projects/new", methods=["GET","POST"])
def new_project():
    if request.method=="POST":
        con=db()
        pid=f"NLAMS-{datetime.now().year}-{con.execute('SELECT COUNT(*) FROM projects').fetchone()[0]+1:03d}"
        data=request.form
        con.execute("""INSERT INTO projects(project_id,name,ptype,department,state,district,taluka,villages,description,cost_cr,duration_months,land_required,stage,progress,risk,created_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (pid,data["name"],data["ptype"],data["department"],data["state"],data["district"],data["taluka"],data["villages"],data["description"],
           float(data["cost_cr"]),int(data["duration"]),float(data["land_required"]),"Draft",0,10,datetime.now().strftime("%Y-%m-%d %H:%M")))
        con.execute("INSERT INTO audit(project_id,action,actor,created_at) VALUES(?,?,?,?)",
                    (pid,"Project created","Project Agency",datetime.now().strftime("%Y-%m-%d %H:%M")))
        con.commit(); con.close(); sync_shared({"_endpoint":"project/create","project_id":pid,"name":data["name"],"state":data["state"],"district":data["district"],"villages":data["villages"],"required_land":float(data["land_required"]),"status":"Draft"})
        flash(f"Project {pid} created successfully.","success")
        return redirect(url_for("project_detail",pid=pid))
    return render_template("new_project.html")

@app.route("/project/<pid>")
def project_detail(pid):
    con=db()
    p=con.execute("SELECT * FROM projects WHERE project_id=?",(pid,)).fetchone()
    if not p: return "Project not found",404
    parcels=con.execute("SELECT * FROM parcels WHERE project_id=?",(pid,)).fetchall()
    docs=con.execute("SELECT * FROM documents WHERE project_id=? ORDER BY id DESC",(pid,)).fetchall()
    comp=con.execute("SELECT * FROM compensation WHERE project_id=?",(pid,)).fetchall()
    rr=con.execute("SELECT * FROM rr WHERE project_id=?",(pid,)).fetchall()
    gr=con.execute("SELECT * FROM grievances WHERE project_id=? ORDER BY id DESC",(pid,)).fetchall()
    audit=con.execute("SELECT * FROM audit WHERE project_id=? ORDER BY id DESC",(pid,)).fetchall()
    con.close()
    return render_template("project_detail.html",p=p,parcels=parcels,docs=docs,comp=comp,rr=rr,gr=gr,audit=audit)

@app.post("/project/<pid>/stage")
def update_stage(pid):
    stage=request.form["stage"]
    progress=int(request.form.get("progress",0))
    con=db(); con.execute("UPDATE projects SET stage=?,progress=? WHERE project_id=?",(stage,progress,pid))
    con.execute("INSERT INTO audit(project_id,action,actor,created_at) VALUES(?,?,?,?)",
                (pid,f"Stage updated to {stage} ({progress}%)","Project Agency",datetime.now().strftime("%Y-%m-%d %H:%M")))
    con.commit(); con.close()
    flash("Workflow stage updated.","success")
    return redirect(url_for("project_detail",pid=pid))

@app.route("/land")
def land():
    con=db()
    parcels=con.execute("SELECT * FROM parcels ORDER BY id").fetchall()
    projects=con.execute("SELECT project_id,name FROM projects").fetchall()
    con.close()
    return render_template("land.html",parcels=parcels,projects=projects)

@app.post("/land/add")
def add_parcel():
    d=request.form
    con=db()
    con.execute("""INSERT INTO parcels(project_id,survey_no,village,taluka,district,area,land_type,status,lat,lng,owner,disputed)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (d["project_id"],d["survey_no"],d["village"],d["taluka"],d["district"],float(d["area"]),d["land_type"],"Proposed",
                 float(d["lat"]),float(d["lng"]),d["owner"],0))
    con.execute("UPDATE projects SET land_acquired=land_acquired WHERE project_id=?",(d["project_id"],))
    con.commit(); con.close(); sync_shared({"_endpoint":"parcel/create","project_id":d["project_id"],"parcel_id":d.get("parcel_id") or d["survey_no"],"landowner_id":d.get("landowner_id") or "LO-DEMO-"+d["survey_no"],"survey_no":d["survey_no"],"village":d["village"],"area":float(d["area"]),"lat":float(d["lat"]),"lng":float(d["lng"]),"status":"Proposed"})
    flash("Land parcel added and available on GIS map.","success")
    return redirect(url_for("land"))

@app.route("/documents")
def documents():
    con=db()
    docs=con.execute("SELECT d.*,p.name project_name FROM documents d LEFT JOIN projects p ON d.project_id=p.project_id ORDER BY d.id DESC").fetchall()
    projects=con.execute("SELECT project_id,name FROM projects ORDER BY id").fetchall()
    con.close()
    return render_template("documents.html",docs=docs,projects=projects)

@app.post("/documents/upload")
def upload_doc():
    d=request.form
    uploaded=request.files.get("file")
    original_name = (uploaded.filename or "").strip()
    display_name = d.get("name","").strip() or original_name or "Untitled Document"
    if uploaded and original_name:
        safe = "".join(ch for ch in original_name if ch.isalnum() or ch in "._-")[:120]
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        saved_name = f"{stamp}_{safe}"
        uploaded.save(os.path.join(UPLOAD_DIR, saved_name))
    con=db()
    con.execute("INSERT INTO documents(project_id,parcel_id,name,dtype,status,uploaded_by,version,uploaded_at) VALUES(?,?,?,?,?,?,?,?)",
                (d["project_id"],d.get("parcel_id") or "",display_name,d["dtype"],"Pending Validation","Project Agency",1,datetime.now().strftime("%Y-%m-%d %H:%M")))
    con.commit(); con.close(); sync_shared({"_endpoint":"document","project_id":d["project_id"],"parcel_id":d.get("parcel_id", ""),"category":d["dtype"],"name":display_name,"type":d["dtype"],"uploaded_by":"Project Agency","status":"Pending Validation","source_path":original_name})
    flash("Document uploaded. Validation queued.","success")
    return redirect(url_for("documents"))

@app.post("/documents/<int:doc_id>/verify")
def verify_doc(doc_id):
    con=db(); row=con.execute("SELECT project_id,parcel_id,name FROM documents WHERE id=?",(doc_id,)).fetchone(); con.execute("UPDATE documents SET status='Verified' WHERE id=?",(doc_id,)); con.commit(); con.close()
    if row: sync_shared({'_endpoint':'document/status','project_id':row['project_id'],'parcel_id':row['parcel_id'] or '', 'name':row['name'], 'status':'Verified'})
    flash("Document verified and central registry updated.","success"); return redirect(url_for("documents"))

@app.route("/compensation")
def compensation():
    con=db()
    rows=con.execute("SELECT c.*,p.name project_name FROM compensation c LEFT JOIN projects p ON c.project_id=p.project_id ORDER BY c.id DESC").fetchall()
    totals=con.execute("SELECT COALESCE(SUM(assessed),0),COALESCE(SUM(approved),0),COALESCE(SUM(disbursed),0) FROM compensation").fetchone()
    con.close()
    return render_template("compensation.html",rows=rows,totals=totals)

@app.post("/compensation/<int:cid>/pay")
def pay_comp(cid):
    con=db()
    con.execute("UPDATE compensation SET disbursed=approved,status='Disbursed',payment_ref=? WHERE id=?",
                (f"PFMS-{datetime.now().strftime('%Y%m%d')}-{cid:04d}",cid))
    row=con.execute("SELECT project_id,family_id FROM compensation WHERE id=?",(cid,)).fetchone()
    con.execute("INSERT INTO audit(project_id,action,actor,created_at) VALUES(?,?,?,?)",
                (row["project_id"],f"Compensation disbursed for {row['family_id']}","Project Agency",datetime.now().strftime("%Y-%m-%d %H:%M")))
    con.commit(); con.close()
    flash("Compensation marked as disbursed.","success"); return redirect(url_for("compensation"))

@app.route("/rr")
def rr():
    con=db(); rows=con.execute("SELECT r.*,p.name project_name FROM rr r LEFT JOIN projects p ON r.project_id=p.project_id ORDER BY r.id").fetchall()
    con.close(); return render_template("rr.html",rows=rows)

@app.post("/rr/<int:rid>/update")
def rr_update(rid):
    status=request.form.get("status","Pending")
    try:
        progress=max(0,min(100,int(request.form.get("progress",0))))
    except (TypeError, ValueError):
        progress=0
    # Keep status and progress consistent.
    if status=="Completed":
        progress=100
    elif status=="Pending":
        progress=0
    con=db()
    row=con.execute("SELECT project_id,family_id FROM rr WHERE id=?",(rid,)).fetchone()
    if not row:
        con.close()
        return "R&R case not found",404
    con.execute("UPDATE rr SET status=?,progress=? WHERE id=?",(status,progress,rid))
    con.execute("INSERT INTO audit(project_id,action,actor,created_at) VALUES(?,?,?,?)",
                (row["project_id"],f"R&R status updated for {row['family_id']} → {status} ({progress}%)",
                 "Project Agency",datetime.now().strftime("%Y-%m-%d %H:%M")))
    con.commit(); con.close()
    flash("R&R status updated successfully.","success")
    return redirect(url_for("rr"))

@app.route("/landowner-verification")
def landowner_verification():
    import urllib.request, json as _json
    try:
        with urllib.request.urlopen("http://127.0.0.1:8090/api/landowners", timeout=2) as r: rows=_json.loads(r.read().decode())
    except Exception: rows=[]
    return render_template("landowner_verification.html", rows=rows)

@app.post("/landowner-verification/<landowner_id>/verify")
def verify_landowner(landowner_id):
    import urllib.request, json as _json
    try:
        req=urllib.request.Request(f"http://127.0.0.1:8090/api/landowners/{landowner_id}/verify", data=b"{}", headers={"Content-Type":"application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=3).read()
    except Exception: pass
    flash(f"{landowner_id} verified. Any eligible ON-HOLD complaint is automatically released to the Grievance Officer.","success")
    return redirect(url_for("landowner_verification"))

@app.post("/landowner-verification/<landowner_id>/reject")
def reject_landowner(landowner_id):
    import urllib.request, json as _json
    reason=request.form.get("reason") or "Please correct the submitted registration details and resubmit."
    try:
        req=urllib.request.Request(f"http://127.0.0.1:8090/api/landowners/{landowner_id}/reject", data=_json.dumps({"reason":reason}).encode(), headers={"Content-Type":"application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=3).read()
    except Exception: pass
    flash(f"{landowner_id} rejected. The landowner can correct details and resubmit.","warning")
    return redirect(url_for("landowner_verification"))

@app.route("/grievance")
def grievance():
    con=db()
    rows=con.execute("SELECT g.*,p.name project_name FROM grievances g LEFT JOIN projects p ON g.project_id=p.project_id ORDER BY g.id DESC").fetchall()
    projects=con.execute("SELECT project_id,name FROM projects ORDER BY id").fetchall()
    con.close()
    return render_template("grievance.html",rows=rows,projects=projects)

@app.post("/grievance/add")
def grievance_add():
    d=request.form; now=datetime.now().strftime("%Y-%m-%d %H:%M")
    con=db(); n=con.execute("SELECT COUNT(*) FROM grievances").fetchone()[0]+17
    gid=f"GRV-{datetime.now().year}-{n:03d}"
    con.execute("""INSERT INTO grievances(project_id,parcel_id,landowner_id,grievance_id,citizen,category,description,status,priority,assigned_to,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (d["project_id"],d.get("parcel_id",""),"LO-DEMO-"+d.get("parcel_id","NA"),gid,d["citizen"],d["category"],d["description"],"Open",d["priority"],"Unassigned",now,now))
    con.commit(); con.close(); flash(f"{gid} registered successfully.","success"); return redirect(url_for("grievance"))

@app.post("/grievance/<int:gid>/resolve")
def resolve_grievance(gid):
    con=db(); con.execute("UPDATE grievances SET status='Resolved',updated_at=? WHERE id=?",(datetime.now().strftime("%Y-%m-%d %H:%M"),gid)); con.commit(); con.close()
    flash("Grievance resolved and citizen status updated.","success"); return redirect(url_for("grievance"))

@app.route("/reports")
def reports():
    return render_template("reports.html")

@app.route("/reports/export/<kind>")
def export_report(kind):
    con=db()
    if kind=="projects":
        rows=con.execute("SELECT project_id,name,ptype,state,district,land_required,land_acquired,stage,progress,risk FROM projects").fetchall()
        headers=rows[0].keys() if rows else ["project_id"]
    elif kind=="compensation":
        rows=con.execute("SELECT family_id,owner,parcel,assessed,approved,disbursed,status,payment_ref FROM compensation").fetchall()
        headers=rows[0].keys() if rows else ["family_id"]
    elif kind=="rr":
        rows=con.execute("SELECT family_id,head,village,land_area,status,benefit,progress FROM rr").fetchall()
        headers=rows[0].keys() if rows else ["family_id"]
    else:
        rows=con.execute("SELECT grievance_id,citizen,category,status,priority,assigned_to,created_at FROM grievances").fetchall()
        headers=rows[0].keys() if rows else ["grievance_id"]
    out=io.StringIO(); w=csv.writer(out); w.writerow(headers)
    for r in rows: w.writerow([r[h] for h in headers])
    con.close()
    mem=io.BytesIO(out.getvalue().encode("utf-8")); mem.seek(0)
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=f"nlams_{kind}_report.csv")

@app.route("/ai-risk")
def ai_risk():
    con=db()
    projects=con.execute("SELECT * FROM projects ORDER BY risk DESC").fetchall()
    con.close()
    return render_template("risk.html",projects=projects)

@app.route("/notifications")
def notifications():
    con=db(); rows=con.execute("SELECT * FROM notifications ORDER BY id DESC").fetchall(); con.close()
    return render_template("notifications.html",rows=rows)

@app.post("/notifications/read/<int:nid>")
def notification_read(nid):
    con=db(); con.execute("UPDATE notifications SET read_flag=1 WHERE id=?",(nid,)); con.commit(); con.close()
    return redirect(url_for("notifications"))

@app.route("/api/summary")
def api_summary():
    con=db()
    result={
      "projects": con.execute("SELECT COUNT(*) FROM projects").fetchone()[0],
      "land_required": con.execute("SELECT COALESCE(SUM(land_required),0) FROM projects").fetchone()[0],
      "land_acquired": con.execute("SELECT COALESCE(SUM(land_acquired),0) FROM projects").fetchone()[0],
      "compensation_assessed": con.execute("SELECT COALESCE(SUM(assessed),0) FROM compensation").fetchone()[0],
      "compensation_disbursed": con.execute("SELECT COALESCE(SUM(disbursed),0) FROM compensation").fetchone()[0],
      "open_grievances": con.execute("SELECT COUNT(*) FROM grievances WHERE status!='Resolved'").fetchone()[0]
    }
    con.close(); return jsonify(result)

# -----------------------------------------------------------------------------
# NLAMS Acceptance Automation API
# Central workflow, task, document/evidence registry, validation and AI guide.
# -----------------------------------------------------------------------------
def ensure_automation_schema():
    con=db()
    cols=lambda t: [r[1] for r in con.execute(f'PRAGMA table_info({t})').fetchall()]
    for table, col, ddl in [
        ('parcels','parcel_id','TEXT'), ('parcels','landowner_id','TEXT'),
        ('documents','parcel_id','TEXT'), ('documents','uploaded_by','TEXT'), ('documents','version','INTEGER DEFAULT 1'),
        ('grievances','parcel_id','TEXT'), ('grievances','landowner_id','TEXT')]:
        if col not in cols(table):
            con.execute(f'ALTER TABLE {table} ADD COLUMN {col} {ddl}')
    con.executescript('''
    CREATE TABLE IF NOT EXISTS gis_evidence(
      id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, parcel_id TEXT,
      evidence_type TEXT, name TEXT, lat REAL, lng REAL, measured_area REAL,
      label TEXT, uploaded_by TEXT, uploaded_at TEXT
    );
    CREATE TABLE IF NOT EXISTS workflow_tasks(
      id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT UNIQUE, project_id TEXT, parcel_id TEXT,
      title TEXT, assigned_role TEXT, status TEXT, priority TEXT, created_at TEXT, completed_at TEXT
    );
    ''')
    # Backfill deterministic IDs for the demo and existing records.
    rows=con.execute("SELECT id,project_id,survey_no,owner FROM parcels").fetchall()
    for r in rows:
        pid=f"P-{r['id']:03d}"
        if r['project_id']=='NH44-MH-001':
            mapping={'125':'P-001','126':'P-002','128':'P-003'}
            pid=mapping.get(r['survey_no'],pid)
        lo=f"LO-DEMO-{r['survey_no']}"
        con.execute("UPDATE parcels SET parcel_id=COALESCE(parcel_id,?),landowner_id=COALESCE(landowner_id,?) WHERE id=?",(pid,lo,r['id']))
    con.commit(); con.close()

ensure_automation_schema()

# Seed the hero parcel's synthetic evidence and initial Revenue task once.
_con=db()
if _con.execute("SELECT COUNT(*) FROM gis_evidence WHERE parcel_id='P-001'").fetchone()[0] == 0:
    _now=datetime.now().strftime('%Y-%m-%d %H:%M')
    _con.executemany("INSERT INTO gis_evidence(project_id,parcel_id,evidence_type,name,lat,lng,measured_area,label,uploaded_by,uploaded_at) VALUES(?,?,?,?,?,?,?,?,?,?)", [
      ('NH44-MH-001','P-001','Field Photograph','Field Photo 01',18.5204,73.8567,2.48,'DEMO / SAMPLE FIELD IMAGE','Survey/GIS Officer',_now),
      ('NH44-MH-001','P-001','Field Photograph','Field Photo 02',18.5206,73.8569,2.48,'DEMO / SAMPLE FIELD IMAGE','Survey/GIS Officer',_now),
      ('NH44-MH-001','P-001','Boundary','GIS Boundary – DEMO',18.5204,73.8567,2.48,'DEMO / SAMPLE GIS EVIDENCE','Survey/GIS Officer',_now),
      ('NH44-MH-001','P-001','Survey Report','Survey Report – DEMO',18.5204,73.8567,2.48,'DEMO / SAMPLE DOCUMENT','Survey/GIS Officer',_now)])
if _con.execute("SELECT COUNT(*) FROM workflow_tasks WHERE parcel_id='P-001'").fetchone()[0] == 0:
    create_ref='TASK-REVENUE-P001'
    _con.execute("INSERT INTO workflow_tasks(ref,project_id,parcel_id,title,assigned_role,status,priority,created_at) VALUES(?,?,?,?,?,?,?,?)",(create_ref,'NH44-MH-001','P-001','Revenue verification','Revenue Officer','Pending','High',datetime.now().strftime('%Y-%m-%d %H:%M')))
_con.commit(); _con.close()

REQUIRED_DOCS={
 'Compensation':['Award Copy / Compensation Statement','Bank / Payment Proof (if applicable)'],
 'R&R':['R&R Eligibility / Benefit Record','Identity or entitlement proof (if applicable)'],
 'Land Record':['7/12 Extract','Ownership / Title Record','Mutation Record'],
 'Ownership':['7/12 Extract','Ownership / Title Record','Mutation Record'],
 'Boundary':['Survey / Measurement Report','7/12 Extract','GIS Boundary / Map'],
 'Survey':['Survey / Measurement Report','GIS Boundary / Map','Field Photographs'],
 'Notification':['Acquisition Notification / Notice','Relevant Project / Parcel Record'],
 'Hearing':['Hearing Notice','Objection / Representation','Supporting Evidence'],
 'Grievance':['Grievance application / description','Relevant land record or notice','Supporting evidence (if available)']
}

def ai_document_guide(text, category='Grievance'):
    s=(text or '').lower()
    rules=[
      (['compensation','payment','award','money'], 'Compensation'),
      (['rehabilitation','r&r','resettlement','skill','benefit'], 'R&R'),
      (['owner','ownership','name wrong','land record','7/12','mutation'], 'Land Record'),
      (['boundary','survey number','area mismatch','measurement','map'], 'Boundary'),
      (['photo','gps','field','survey'], 'Survey'),
      (['notice','notification'], 'Notification'),
      (['hearing','objection'], 'Hearing')]
    chosen=category if category in REQUIRED_DOCS else 'Grievance'
    for words,cat in rules:
        if any(w in s for w in words): chosen=cat; break
    docs=REQUIRED_DOCS[chosen]
    return {'category':chosen,'documents':docs,'explanation':'Suggested from the grievance/request wording. This is guidance; an authorized officer must confirm the final legal requirements.'}

def add_audit(con, project_id, action, actor='System', parcel_id=None):
    detail=action if not parcel_id else f"{action} [Parcel {parcel_id}]"
    con.execute("INSERT INTO audit(project_id,action,actor,created_at) VALUES(?,?,?,?)",(project_id,detail,actor,datetime.now().strftime('%Y-%m-%d %H:%M')))

def create_task(con, project_id, parcel_id, title, role, priority='Medium'):
    ref=f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S%f')[-10:]}"
    con.execute("INSERT INTO workflow_tasks(ref,project_id,parcel_id,title,assigned_role,status,priority,created_at) VALUES(?,?,?,?,?,?,?,?)",
                (ref,project_id,parcel_id,title,role,'Pending',priority,datetime.now().strftime('%Y-%m-%d %H:%M')))
    con.execute("INSERT INTO notifications(title,body,ntype,created_at) VALUES(?,?,?,?)",
                ('New workflow task',f'{title} · {project_id} · {parcel_id}','workflow',datetime.now().strftime('%Y-%m-%d %H:%M')))
    return ref

@app.get('/api/automation/summary')
def automation_summary():
    con=db()
    out={
      'parcels':con.execute('SELECT COUNT(*) FROM parcels').fetchone()[0],
      'documents':con.execute('SELECT COUNT(*) FROM documents').fetchone()[0],
      'evidence':con.execute('SELECT COUNT(*) FROM gis_evidence').fetchone()[0],
      'pending_tasks':con.execute("SELECT COUNT(*) FROM workflow_tasks WHERE status='Pending'").fetchone()[0],
      'unread_notifications':con.execute('SELECT COUNT(*) FROM notifications WHERE read_flag=0').fetchone()[0],
      'fully_verified':con.execute("SELECT COUNT(*) FROM parcels WHERE status='GIS Verified'").fetchone()[0]
    }
    con.close(); return jsonify(out)

@app.get('/api/automation/tasks')
def automation_tasks():
    role=request.args.get('role','project_agency')
    role_map={'project_agency':'Project Agency','revenue_officer':'Revenue Officer','survey_gis':'Survey/GIS Officer','land_acquisition':'LAO','grievance_officer':'Grievance Officer','admin':'Admin'}
    wanted=role_map.get(role,role)
    con=db(); rows=con.execute("SELECT * FROM workflow_tasks WHERE status='Pending' AND (assigned_role=? OR ?='Admin') ORDER BY id DESC",(wanted,wanted)).fetchall(); con.close()
    return jsonify([dict(r) for r in rows])

@app.get('/api/case/<parcel_id>')
def case_api(parcel_id):
    con=db(); p=con.execute('SELECT * FROM parcels WHERE parcel_id=?',(parcel_id,)).fetchone()
    if not p: con.close(); return jsonify({'error':'Parcel not found'}),404
    docs=con.execute('SELECT * FROM documents WHERE project_id=? AND (parcel_id=? OR parcel_id IS NULL OR parcel_id=?) ORDER BY id DESC',(p['project_id'],parcel_id,'')).fetchall()
    ev=con.execute('SELECT * FROM gis_evidence WHERE project_id=? AND parcel_id=? ORDER BY id DESC',(p['project_id'],parcel_id)).fetchall()
    audit=con.execute('SELECT * FROM audit WHERE project_id=? AND (action LIKE ? OR action LIKE ?) ORDER BY id DESC',(p['project_id'],f'%{parcel_id}%',f'%{p["survey_no"]}%')).fetchall()
    out={'parcel':dict(p),'documents':[dict(x) for x in docs],'evidence':[dict(x) for x in ev],'audit':[dict(x) for x in audit]}; con.close(); return jsonify(out)

@app.get('/api/case-health')
def case_health():
    parcel_id=request.args.get('parcel_id','P-001'); con=db(); p=con.execute('SELECT * FROM parcels WHERE parcel_id=?',(parcel_id,)).fetchone()
    if not p: con.close(); return jsonify({'error':'Parcel not found'}),404
    docs=con.execute("SELECT COUNT(*) FROM documents WHERE project_id=? AND (parcel_id=? OR parcel_id IS NULL OR parcel_id='')",(p['project_id'],parcel_id)).fetchone()[0]
    ev=con.execute('SELECT * FROM gis_evidence WHERE project_id=? AND parcel_id=?',(p['project_id'],parcel_id)).fetchall()
    types={x['evidence_type'] for x in ev}; checks=[
      {'name':'Project linked','status':'PASS' if p['project_id'] else 'FAIL'},
      {'name':'Parcel identity','status':'PASS' if p['parcel_id'] else 'FAIL'},
      {'name':'Landowner linked','status':'PASS' if p['landowner_id'] else 'FAIL'},
      {'name':'Documents available','status':'PASS' if docs else 'FAIL'},
      {'name':'GPS evidence','status':'PASS' if any(x['lat'] is not None and x['lng'] is not None for x in ev) else 'FAIL'},
      {'name':'Field photograph','status':'PASS' if 'Field Photograph' in types else 'FAIL'},
      {'name':'GIS boundary','status':'PASS' if 'Boundary' in types else 'FAIL'},
      {'name':'Survey report','status':'PASS' if 'Survey Report' in types else 'FAIL'}]
    score=round(sum(c['status']=='PASS' for c in checks)/len(checks)*100); risk='LOW' if score>=85 else ('MEDIUM' if score>=60 else 'HIGH')
    out={'parcel':dict(p),'checks':checks,'score':score,'risk':risk,'document_count':docs,'evidence_count':len(ev)}; con.close(); return jsonify(out)

@app.post('/api/workflow/<ref>/transition')
def workflow_transition(ref):
    data=request.get_json(silent=True) or {}; action=data.get('action','approve'); actor=data.get('actor_role','System')
    con=db(); task=con.execute('SELECT * FROM workflow_tasks WHERE ref=?',(ref,)).fetchone()
    if not task: con.close(); return jsonify({'error':'Task not found'}),404
    if action=='return':
        con.execute("UPDATE workflow_tasks SET status='Returned' WHERE ref=?",(ref,)); add_audit(con,task['project_id'],f'Task returned: {task["title"]}',actor,task['parcel_id']); con.commit(); con.close(); return jsonify({'current_role':task['assigned_role'],'status':'Returned'})
    con.execute("UPDATE workflow_tasks SET status='Completed',completed_at=? WHERE ref=?",(datetime.now().strftime('%Y-%m-%d %H:%M'),ref))
    p=con.execute('SELECT * FROM parcels WHERE parcel_id=?',(task['parcel_id'],)).fetchone(); title=task['title']
    if 'Revenue' in title:
        con.execute("UPDATE parcels SET status='Revenue Verified' WHERE parcel_id=?",(task['parcel_id'],)); next_role='Survey/GIS Officer'; next_title='GIS field verification'; create_task(con,p['project_id'],p['parcel_id'],next_title,next_role,'High')
    elif 'GIS' in title:
        con.execute("UPDATE parcels SET status='GIS Verified' WHERE parcel_id=?",(task['parcel_id'],)); next_role='LAO'; next_title='LAO complete case scrutiny'; create_task(con,p['project_id'],p['parcel_id'],next_title,next_role,'High')
    else:
        next_role='Admin'
    add_audit(con,p['project_id'],f'{title} completed → next task created',actor,p['parcel_id']); con.commit(); con.close(); return jsonify({'current_role':next_role,'status':'Completed'})

@app.get('/api/parcels')
def api_parcels():
    con=db(); rows=con.execute('SELECT parcel_id,survey_no,owner,area FROM parcels WHERE project_id=? ORDER BY id',(request.args.get('project_id'),)).fetchall(); con.close(); return jsonify([dict(r) for r in rows])

@app.post('/api/ai/document-guide')
def ai_guide_api():
    data=request.get_json(silent=True) or {}; return jsonify(ai_document_guide(data.get('text',''),data.get('category','Grievance')))


if __name__=="__main__":
    app.run(debug=True, host="127.0.0.1", port=int(__import__("os").environ.get("NLAMS_PORT", "5008")))
