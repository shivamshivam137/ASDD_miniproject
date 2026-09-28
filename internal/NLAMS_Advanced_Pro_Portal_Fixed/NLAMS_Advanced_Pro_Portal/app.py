from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, Response
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import sqlite3, os, csv, io, secrets, json

BASE=os.path.dirname(os.path.abspath(__file__)); DB=os.path.join(BASE,"nlams.db")
app=Flask(__name__); app.secret_key=os.environ.get("NLAMS_SECRET_KEY","nlams-dev-secret-change-me")

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
def stamp(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def audit(action,module,details=""):
    c=db(); c.execute("INSERT INTO audit_logs(created_at,user,action,module,details) VALUES(?,?,?,?,?)",
                      (stamp(),session.get("username","system"),action,module,details)); c.commit(); c.close()
def auth(f):
    @wraps(f)
    def w(*a,**k):
        if "user_id" not in session:
            return (jsonify(error="Authentication required"),401) if request.path.startswith("/api/") else redirect("/login")
        return f(*a,**k)
    return w

def init():
    c=db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,username TEXT UNIQUE,email TEXT,role TEXT,district TEXT,status TEXT,password_hash TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS roles(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE,description TEXT,permissions TEXT);
    CREATE TABLE IF NOT EXISTS districts(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE,code TEXT UNIQUE,state TEXT,officer TEXT,status TEXT);
    CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT UNIQUE,name TEXT,district TEXT,agency TEXT,land_required REAL,unit TEXT,status TEXT,progress INTEGER,risk TEXT,description TEXT,lat REAL,lng REAL,created_at TEXT,updated_at TEXT);
    CREATE TABLE IF NOT EXISTS workflow(id INTEGER PRIMARY KEY AUTOINCREMENT,step_order INTEGER,name TEXT,owner_role TEXT,sla_days INTEGER,status TEXT);
    CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,message TEXT,level TEXT,is_read INTEGER,created_at TEXT);
    CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,user TEXT,action TEXT,module TEXT,details TEXT);
    CREATE TABLE IF NOT EXISTS grievances(id INTEGER PRIMARY KEY AUTOINCREMENT,grievance_id TEXT UNIQUE,project_id TEXT,category TEXT,description TEXT,status TEXT,priority TEXT,assigned_to TEXT,created_at TEXT,updated_at TEXT);
    CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT,name TEXT,version TEXT,uploaded_by TEXT,status TEXT,integrity TEXT,uploaded_at TEXT);
    CREATE TABLE IF NOT EXISTS conflicts(id INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT,survey_no TEXT,village TEXT,issue TEXT,conflict_type TEXT,severity TEXT,status TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS workload(id INTEGER PRIMARY KEY AUTOINCREMENT,officer TEXT UNIQUE,role TEXT,pending INTEGER,overdue INTEGER,load_level TEXT);
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
    """)
    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0]==0:
        users=[("System Administrator","admin","admin@nlams.gov.in","Administrator","All Districts","Active"),
        ("Amit Kulkarni","amit.k","amit.k@nlams.gov.in","District Officer","Pune","Active"),
        ("Neha Patil","neha.p","neha.p@nlams.gov.in","LAO","Mumbai","Active"),
        ("Rahul Deshmukh","rahul.d","rahul.d@nlams.gov.in","Survey Officer","Nagpur","Active"),
        ("Priya Shah","priya.s","priya.s@nlams.gov.in","Agency Officer","Thane","Active")]
        for u in users:c.execute("INSERT INTO users(name,username,email,role,district,status,password_hash,created_at) VALUES(?,?,?,?,?,?,?,?)",(*u,generate_password_hash("admin123" if u[1]=="admin" else "password123"),stamp()))
    if c.execute("SELECT COUNT(*) FROM roles").fetchone()[0]==0:
        roles=[("Administrator","Full system access","Dashboard,GIS,Risk,Workflow,Integrity,Workload,AI,Projects,Users,Roles,Districts,Grievances,Reports,Monitoring,Audit,Settings"),
        ("District Officer","District acquisition operations","Dashboard,GIS,Risk,Workflow,Projects,Grievances,Reports"),
        ("LAO","Land acquisition officer","Dashboard,Risk,Workflow,Integrity,Projects,Grievances"),
        ("Survey Officer","Field survey officer","Dashboard,GIS,Workflow,Projects,Integrity"),
        ("Agency Officer","Project submission officer","Dashboard,Projects,Documents,Reports")]
        c.executemany("INSERT INTO roles(name,description,permissions) VALUES(?,?,?)",roles)
    if c.execute("SELECT COUNT(*) FROM districts").fetchone()[0]==0:
        ds=[("Pune","PN","Maharashtra","Amit Kulkarni"),("Mumbai","MU","Maharashtra","Neha Patil"),("Nagpur","NG","Maharashtra","Rahul Deshmukh"),("Thane","TH","Maharashtra","Priya Shah"),("Aurangabad","AU","Maharashtra","Vivek More"),("Nashik","NS","Maharashtra","Sneha Jadhav"),("Solapur","SO","Maharashtra","Rohit Pawar"),("Kolhapur","KO","Maharashtra","Kiran Patil"),("Satara","ST","Maharashtra","Mahesh Shinde"),("Amravati","AM","Maharashtra","Pooja Kale"),("Nanded","ND","Maharashtra","Akash Wagh"),("Ratnagiri","RT","Maharashtra","Minal Joshi")]
        c.executemany("INSERT INTO districts(name,code,state,officer,status) VALUES(?,?,?,?,?)",[(*d,"Active") for d in ds])
    if c.execute("SELECT COUNT(*) FROM projects").fetchone()[0]==0:
        ps=[("NLAMS-PUN-001","Pune Highway","Pune","Maharashtra State Agency",100,"acres","In Progress",72,"Medium","Solapur–Pune highway acquisition",18.5204,73.8567),
        ("NLAMS-MUM-002","Mumbai Metro","Mumbai","Urban Transport Agency",68,"acres","Submitted",38,"High","Metro corridor acquisition",19.0760,72.8777),
        ("NLAMS-NAG-003","Nagpur Expressway","Nagpur","Maharashtra State Agency",145,"acres","In Progress",61,"Low","Expressway corridor",21.1458,79.0882),
        ("NLAMS-THN-004","Thane Ring Road","Thane","Road Development Agency",54,"acres","Approved",92,"Low","Ring road expansion",19.2183,72.9781),
        ("NLAMS-AUR-005","Aurangabad Highway","Aurangabad","Maharashtra State Agency",88,"acres","Draft",15,"Medium","Highway widening",19.8762,75.3433),
        ("NLAMS-SOL-006","Solapur Bypass","Solapur","Road Development Agency",76,"acres","Pending",29,"High","Bypass land acquisition",17.6599,75.9064)]
        for p in ps:c.execute("""INSERT INTO projects(project_id,name,district,agency,land_required,unit,status,progress,risk,description,lat,lng,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(*p,stamp(),stamp()))
    if c.execute("SELECT COUNT(*) FROM workflow").fetchone()[0]==0:
        c.executemany("INSERT INTO workflow(step_order,name,owner_role,sla_days,status) VALUES(?,?,?,?,?)",[(1,"Project Created","Agency Officer",2,"Active"),(2,"Land Proposed","Agency Officer",3,"Active"),(3,"Revenue Verification","District Officer",5,"Active"),(4,"GIS Verification","Survey Officer",7,"Active"),(5,"Notification","LAO",10,"Active"),(6,"Hearing","LAO",15,"Active"),(7,"Award","LAO",7,"Active"),(8,"Compensation","LAO",10,"Active"),(9,"R&R","District Officer",12,"Active"),(10,"Possession","District Officer",7,"Active")])
    if c.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]==0:
        notes=[("New project submitted","Maharashtra State Agency submitted a new project.","success"),("Case NLAMS-PUN-021 moved to LAO","Revenue verification assigned.","info"),("Grievance GRV-2025-0067 resolved","Citizen grievance closed by LAO.","success"),("New user registered","Survey Officer account created.","warning"),("Audit generated for District Pune","Daily audit snapshot completed.","info")]
        c.executemany("INSERT INTO notifications(title,message,level,is_read,created_at) VALUES(?,?,?,?,?)",[(a,b,d,0,stamp()) for a,b,d in notes])
    if c.execute("SELECT COUNT(*) FROM grievances").fetchone()[0]==0:
        gs=[("GRV-2025-0067","NLAMS-PUN-001","Compensation","Compensation clarification requested","Resolved","Medium","Neha Patil"),("GRV-2025-0081","NLAMS-MUM-002","Ownership","Ownership record mismatch","Open","High","Neha Patil"),("GRV-2025-0094","NLAMS-NAG-003","Survey","Survey boundary query","In Progress","Medium","Rahul Deshmukh"),("GRV-2025-0102","NLAMS-THN-004","Hearing","Hearing schedule request","Open","Low","Amit Kulkarni")]
        c.executemany("INSERT INTO grievances(grievance_id,project_id,category,description,status,priority,assigned_to,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",[(*g,stamp(),stamp()) for g in gs])
    if c.execute("SELECT COUNT(*) FROM documents").fetchone()[0]==0:
        docs=[("NLAMS-PUN-001","DPR.pdf","v1","Agency","Verified","Verified"),("NLAMS-PUN-001","LandSchedule.xlsx","v2","Agency","Approved","Verified"),("NLAMS-MUM-002","Metro_DPR.pdf","v3","LAO","Pending","Verified"),("NLAMS-NAG-003","Survey_Report.pdf","v1","Survey Officer","Approved","Verified")]
        c.executemany("INSERT INTO documents(project_id,name,version,uploaded_by,status,integrity,uploaded_at) VALUES(?,?,?,?,?,?,?)",[(*d,stamp()) for d in docs])
    if c.execute("SELECT COUNT(*) FROM conflicts").fetchone()[0]==0:
        cs=[("NLAMS-PUN-001","125","Wakad","Duplicate Parcel","Duplicate Parcel","High","Open"),("NLAMS-MUM-002","87","Kanjurmarg","Multiple ownership entries","Ownership Conflict","High","Open"),("NLAMS-NAG-003","210","Nandgaon","Area mismatch","Area Mismatch","Medium","Review"),("NLAMS-PUN-001","128","Wakad","Repeated document changes","Document Anomaly","Low","Resolved")]
        c.executemany("INSERT INTO conflicts(project_id,survey_no,village,issue,conflict_type,severity,status,created_at) VALUES(?,?,?,?,?,?,?,?)",[(*x,stamp()) for x in cs])
    if c.execute("SELECT COUNT(*) FROM workload").fetchone()[0]==0:
        c.executemany("INSERT INTO workload(officer,role,pending,overdue,load_level) VALUES(?,?,?,?,?)",[("RO - A","Revenue Officer",42,8,"High"),("RO - B","Revenue Officer",15,1,"Low"),("RO - C","Revenue Officer",28,3,"Medium"),("RO - D","Revenue Officer",18,2,"Medium")])
    for k,v in {"portal_name":"NLAMS","organization":"Ministry of Rural Development","email_notifications":"1","maintenance_mode":"0","session_timeout":"60"}.items():
        c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",(k,v))
    c.commit();c.close()
init()


@app.after_request
def _nlams_security_headers(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='SAMEORIGIN'
    response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    response.headers['Permissions-Policy']='geolocation=(self), camera=(), microphone=()'
    response.headers['Cache-Control']='no-store'
    return response

@app.route("/")
def home(): return redirect("/dashboard" if "user_id" in session else "/login")
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form.get("username","").strip();p=request.form.get("password","")
        c=db();x=c.execute("SELECT * FROM users WHERE username=? AND status='Active'",(u,)).fetchone();c.close()
        if x and check_password_hash(x["password_hash"],p):
            session.update(user_id=x["id"],username=x["username"],name=x["name"],role=x["role"]);audit("System Login","System",u);return redirect("/dashboard")
        flash("Invalid username or password","error")
    return render_template("login.html")
@app.route("/logout")
def logout(): 
    if session.get("user_id"): audit("System Logout","System",session.get("username"))
    session.clear();return redirect("/login")

PAGES={"dashboard":"dashboard.html","gis":"gis.html","risk":"risk.html","workflow":"workflow.html","integrity":"integrity.html","workload":"workload.html","assistant":"assistant.html","projects":"projects.html","users":"users.html","roles":"roles.html","districts":"districts.html","grievances":"grievances.html","reports":"reports.html","monitoring":"monitoring.html","audit":"audit.html","settings":"settings.html"}
@app.route("/<page>")
@auth
def page(page):
    if page not in PAGES:return redirect("/dashboard")
    return render_template(PAGES[page],active=page)

def rows(sql,args=()):
    c=db();r=[dict(x) for x in c.execute(sql,args).fetchall()];c.close();return r

@app.route("/api/dashboard")
@auth
def dashboard_api():
    c=db()
    stats={"projects":c.execute("SELECT COUNT(*) FROM projects").fetchone()[0],"active":c.execute("SELECT COUNT(*) FROM projects WHERE status IN ('In Progress','Approved')").fetchone()[0],"pending":c.execute("SELECT COUNT(*) FROM workflow WHERE status='Active'").fetchone()[0]*24+3,"officers":c.execute("SELECT COUNT(*) FROM users WHERE status='Active'").fetchone()[0],"districts":c.execute("SELECT COUNT(*) FROM districts WHERE status='Active'").fetchone()[0],"grievances":c.execute("SELECT COUNT(*) FROM grievances WHERE status!='Resolved'").fetchone()[0],"land":c.execute("SELECT COALESCE(SUM(land_required),0) FROM projects").fetchone()[0]}
    projects=[dict(x) for x in c.execute("SELECT * FROM projects ORDER BY id DESC LIMIT 8")]; notes=[dict(x) for x in c.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 6")];logs=[dict(x) for x in c.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 6")]; statuses=[dict(x) for x in c.execute("SELECT status,COUNT(*) c FROM projects GROUP BY status")]; risks=[dict(x) for x in c.execute("SELECT risk,COUNT(*) c FROM projects GROUP BY risk")];c.close()
    return jsonify(stats=stats,projects=projects,notifications=notes,audit=logs,statuses=statuses,risks=risks)

@app.route("/api/projects",methods=["GET","POST"])
@auth
def projects_api():
    c=db()
    if request.method=="GET":
        q=request.args.get("q","");status=request.args.get("status","")
        sql="SELECT * FROM projects WHERE (project_id LIKE ? OR name LIKE ? OR district LIKE ? OR agency LIKE ?)";a=[f"%{q}%"]*4
        if status:sql+=" AND status=?";a.append(status)
        r=[dict(x) for x in c.execute(sql+" ORDER BY id DESC",a)];c.close();return jsonify(r)
    d=request.get_json() or {};pid=d.get("project_id") or f"NLAMS-{d.get('district','GEN')[:3].upper()}-{secrets.randbelow(900)+100}"
    try:
        c.execute("""INSERT INTO projects(project_id,name,district,agency,land_required,unit,status,progress,risk,description,lat,lng,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (pid,d.get("name"),d.get("district"),d.get("agency","State Agency"),float(d.get("land_required",0)),d.get("unit","acres"),d.get("status","Draft"),int(d.get("progress",0)),d.get("risk","Low"),d.get("description",""),float(d.get("lat",19.5)),float(d.get("lng",75)),stamp(),stamp()));c.commit();c.close();audit("Created Project","Projects",pid);return jsonify(ok=True,project_id=pid)
    except Exception as e:c.close();return jsonify(error=str(e)),400

@app.route("/api/projects/<int:i>",methods=["PUT","DELETE"])
@auth
def project_item(i):
    c=db()
    if request.method=="DELETE":c.execute("DELETE FROM projects WHERE id=?",(i,))
    else:
        d=request.get_json() or {};fields=["name","district","agency","land_required","unit","status","progress","risk","description","lat","lng"];sets=[];a=[]
        for f in fields:
            if f in d:sets.append(f"{f}=?");a.append(d[f])
        sets.append("updated_at=?");a.append(stamp());a.append(i);c.execute("UPDATE projects SET "+",".join(sets)+" WHERE id=?",a)
    c.commit();c.close();audit(("Deleted" if request.method=="DELETE" else "Updated")+" Project","Projects",str(i));return jsonify(ok=True)

@app.route("/api/users",methods=["GET","POST"])
@auth
def users_api():
    c=db()
    if request.method=="GET":
        q=request.args.get("q","");r=[dict(x) for x in c.execute("SELECT id,name,username,email,role,district,status,created_at FROM users WHERE name LIKE ? OR username LIKE ? OR email LIKE ? ORDER BY id DESC",(f"%{q}%",)*3)];c.close();return jsonify(r)
    d=request.get_json() or {}
    try:c.execute("INSERT INTO users(name,username,email,role,district,status,password_hash,created_at) VALUES(?,?,?,?,?,?,?,?)",(d["name"],d["username"],d["email"],d.get("role","Administrator"),d.get("district",""),d.get("status","Active"),generate_password_hash(d.get("password","password123")),stamp()));c.commit();c.close();audit("Created User","User Management",d["username"]);return jsonify(ok=True)
    except Exception as e:c.close();return jsonify(error=str(e)),409
@app.route("/api/users/<int:i>",methods=["PUT","DELETE"])
@auth
def user_item(i):
    c=db()
    if request.method=="DELETE":c.execute("DELETE FROM users WHERE id=?",(i,))
    else:
        d=request.get_json() or {};fs=["name","email","role","district","status"];ss=[];a=[]
        for f in fs:
            if f in d:ss.append(f+"=?");a.append(d[f])
        if d.get("password"):ss.append("password_hash=?");a.append(generate_password_hash(d["password"]))
        a.append(i);c.execute("UPDATE users SET "+",".join(ss)+" WHERE id=?",a)
    c.commit();c.close();audit("User Changed","User Management",str(i));return jsonify(ok=True)

@app.route("/api/roles",methods=["GET","POST"])
@auth
def roles_api():
    if request.method=="GET":return jsonify(rows("SELECT * FROM roles ORDER BY id"))
    d=request.get_json() or {};c=db()
    try:c.execute("INSERT INTO roles(name,description,permissions) VALUES(?,?,?)",(d["name"],d.get("description",""),",".join(d.get("permissions",[]))));c.commit();c.close();audit("Created Role","Roles",d["name"]);return jsonify(ok=True)
    except Exception as e:c.close();return jsonify(error=str(e)),409
@app.route("/api/roles/<int:i>",methods=["PUT","DELETE"])
@auth
def role_item(i):
    c=db()
    if request.method=="DELETE":c.execute("DELETE FROM roles WHERE id=?",(i,))
    else:
        d=request.get_json();c.execute("UPDATE roles SET name=?,description=?,permissions=? WHERE id=?",(d["name"],d.get("description",""),",".join(d.get("permissions",[])),i))
    c.commit();c.close();audit("Role Changed","Roles",str(i));return jsonify(ok=True)

@app.route("/api/districts",methods=["GET","POST"])
@auth
def districts_api():
    if request.method=="GET":return jsonify(rows("SELECT * FROM districts ORDER BY name"))
    d=request.get_json();c=db()
    try:c.execute("INSERT INTO districts(name,code,state,officer,status) VALUES(?,?,?,?,?)",(d["name"],d["code"],d.get("state","Maharashtra"),d.get("officer",""),d.get("status","Active")));c.commit();c.close();audit("Added District","Districts",d["name"]);return jsonify(ok=True)
    except Exception as e:c.close();return jsonify(error=str(e)),409
@app.route("/api/districts/<int:i>",methods=["PUT","DELETE"])
@auth
def district_item(i):
    c=db()
    if request.method=="DELETE":c.execute("DELETE FROM districts WHERE id=?",(i,))
    else:
        d=request.get_json();c.execute("UPDATE districts SET name=?,code=?,officer=?,status=? WHERE id=?",(d["name"],d["code"],d.get("officer",""),d.get("status","Active"),i))
    c.commit();c.close();audit("District Changed","Districts",str(i));return jsonify(ok=True)

@app.route("/api/workflow",methods=["GET","POST"])
@auth
def workflow_api():
    if request.method=="GET":return jsonify(rows("SELECT * FROM workflow ORDER BY step_order"))
    d=request.get_json();c=db();c.execute("INSERT INTO workflow(step_order,name,owner_role,sla_days,status) VALUES(?,?,?,?,?)",(int(d["step_order"]),d["name"],d["owner_role"],int(d["sla_days"]),d.get("status","Active")));c.commit();c.close();audit("Added Workflow Step","Workflow",d["name"]);return jsonify(ok=True)
@app.route("/api/workflow/<int:i>",methods=["PUT","DELETE"])
@auth
def workflow_item(i):
    c=db()
    if request.method=="DELETE":c.execute("DELETE FROM workflow WHERE id=?",(i,))
    else:
        d=request.get_json();c.execute("UPDATE workflow SET step_order=?,name=?,owner_role=?,sla_days=?,status=? WHERE id=?",(int(d["step_order"]),d["name"],d["owner_role"],int(d["sla_days"]),d.get("status","Active"),i))
    c.commit();c.close();audit("Workflow Changed","Workflow",str(i));return jsonify(ok=True)

@app.route("/api/grievances",methods=["GET","POST"])
@auth
def grievances_api():
    c=db()
    if request.method=="GET":r=[dict(x) for x in c.execute("SELECT * FROM grievances ORDER BY id DESC")];c.close();return jsonify(r)
    d=request.get_json();gid=d.get("grievance_id") or f"GRV-{datetime.now().year}-{secrets.randbelow(9000)+1000}"
    c.execute("INSERT INTO grievances(grievance_id,project_id,category,description,status,priority,assigned_to,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",(gid,d.get("project_id",""),d.get("category","Other"),d.get("description",""),d.get("status","Open"),d.get("priority","Medium"),d.get("assigned_to","Unassigned"),stamp(),stamp()));c.commit();c.close();audit("Created Grievance","Grievances",gid);return jsonify(ok=True)
@app.route("/api/grievances/<int:i>",methods=["PUT","DELETE"])
@auth
def grievance_item(i):
    c=db()
    if request.method=="DELETE":c.execute("DELETE FROM grievances WHERE id=?",(i,))
    else:
        d=request.get_json();c.execute("UPDATE grievances SET category=?,description=?,status=?,priority=?,assigned_to=?,updated_at=? WHERE id=?",(d.get("category"),d.get("description"),d.get("status"),d.get("priority"),d.get("assigned_to"),stamp(),i))
    c.commit();c.close();audit("Grievance Changed","Grievances",str(i));return jsonify(ok=True)

@app.route("/api/notifications",methods=["GET","PUT"])
@auth
def notifications_api():
    c=db()
    if request.method=="PUT":c.execute("UPDATE notifications SET is_read=1 WHERE id=?",(request.get_json().get("id"),));c.commit()
    r=[dict(x) for x in c.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 30")];c.close();return jsonify(r)
@app.route("/api/audit")
@auth
def audit_api():
    q=request.args.get("q","");return jsonify(rows("SELECT * FROM audit_logs WHERE user LIKE ? OR action LIKE ? OR module LIKE ? OR details LIKE ? ORDER BY id DESC LIMIT 300",(f"%{q}%",)*4))
@app.route("/api/documents")
@auth
def documents_api():return jsonify(rows("SELECT * FROM documents ORDER BY id DESC"))
@app.route("/api/conflicts")
@auth
def conflicts_api():return jsonify(rows("SELECT * FROM conflicts ORDER BY id DESC"))
@app.route("/api/workload")
@auth
def workload_api():return jsonify(rows("SELECT * FROM workload ORDER BY pending DESC"))
@app.route("/api/workload/<int:i>",methods=["PUT"])
@auth
def workload_item(i):
    d=request.get_json() or {}
    count=max(1,int(d.get("count",1)))
    target=(d.get("target") or "").strip()
    c=db()
    source=c.execute("SELECT * FROM workload WHERE id=?",(i,)).fetchone()
    destination=c.execute("SELECT * FROM workload WHERE officer=?",(target,)).fetchone() if target else None
    if not source or not destination:
        c.close();return jsonify(error="Source or target officer not found"),404
    count=min(count,int(source["pending"]))
    c.execute("UPDATE workload SET pending=?,load_level=? WHERE id=?",(max(0,source["pending"]-count),"High" if max(0,source["pending"]-count)>30 else "Medium" if max(0,source["pending"]-count)>20 else "Low",source["id"]))
    c.execute("UPDATE workload SET pending=?,load_level=? WHERE id=?",(destination["pending"]+count,"High" if destination["pending"]+count>30 else "Medium" if destination["pending"]+count>20 else "Low",destination["id"]))
    c.commit();c.close();audit("Reassigned Cases","Officer Workload",f"{count} cases from {source['officer']} to {destination['officer']}")
    return jsonify(ok=True,moved=count,source=source["officer"],target=destination["officer"])

@app.route("/api/settings",methods=["GET","PUT"])
@auth
def settings_api():
    c=db()
    if request.method=="PUT":
        for k,v in (request.get_json() or {}).items():c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(k,str(v)))
        c.commit();c.close();audit("Settings Updated","Settings","Saved");return jsonify(ok=True)
    r={x["key"]:x["value"] for x in c.execute("SELECT key,value FROM settings")};c.close();return jsonify(r)

@app.route("/api/ai",methods=["POST"])
@auth
def ai_api():
    d=request.get_json() or {};q=(d.get("message") or "").lower()
    if "risk" in q:return jsonify(answer="Current high-risk focus: Mumbai Metro and Solapur Bypass. Review ownership conflicts, overdue verification and compensation dependencies first.")
    if "next" in q or "step" in q:return jsonify(answer="Recommended next action: Revenue Verification → GIS Verification. Prioritize cases with high risk and overdue SLA.")
    if "project" in q:return jsonify(answer="NLAMS can create, monitor and report acquisition projects. Use Projects for CRUD operations and GIS for location overview.")
    return jsonify(answer="I can help with project status, risk, next workflow steps, workload balancing, grievances, documents and system monitoring. Try: 'What are the high-risk projects?'")

@app.route("/api/simulate",methods=["POST"])
@auth
def simulate():
    d=request.get_json() or {};add=int(d.get("add_revenue",0))+int(d.get("add_lao",0));pending=max(0,51-add*3);delay=max(0,39-add*2);return jsonify(current_pending=51,simulated_pending=pending,delay_reduction=delay)

@app.route("/api/report.csv")
@auth
def report_csv():
    data=rows("SELECT project_id,name,district,agency,land_required,unit,status,progress,risk,created_at FROM projects ORDER BY id DESC")
    out=io.StringIO();w=csv.writer(out);w.writerow(data[0].keys() if data else ["project_id"]);[w.writerow(x.values()) for x in data]
    audit("Exported Report","Reports","Project CSV");return Response(out.getvalue(),mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=nlams_project_report.csv"})

@app.context_processor
def ctx():return dict(current_user=session.get("name","Admin"),current_role=session.get("role","Administrator"))
if __name__=="__main__":app.run(host="127.0.0.1",port=int(__import__("os").environ.get("NLAMS_PORT", "5007")),debug=True)
