from flask import Flask, render_template, request, jsonify, session, redirect, abort
import sqlite3, os, hashlib, uuid, urllib.parse
from datetime import datetime
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
try:
    from client import post as integration_post, get as integration_get
except Exception:
    integration_post=lambda path,payload: {"ok":False,"offline":True}
    integration_get=lambda path: {"ok":False,"offline":True}

app = Flask(__name__)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=False, PERMANENT_SESSION_LIFETIME=1800)
app.secret_key = "NLAMS-SIH-26016-OFFICER-2026"
DB = os.path.join(os.path.dirname(__file__), "officer.db")


def con():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def hp(password):
    return hashlib.sha256(password.encode()).hexdigest()


def now():
    return datetime.now().isoformat(timespec="minutes")


def init():
    c = con()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        name TEXT, email TEXT UNIQUE, password TEXT, role TEXT,
        department TEXT, district TEXT
    );
    CREATE TABLE IF NOT EXISTS landowners(
        id INTEGER PRIMARY KEY,
        owner_code TEXT UNIQUE, name TEXT, mobile TEXT, email TEXT,
        address TEXT, village TEXT, taluka TEXT, district TEXT, state TEXT,
        family_members INTEGER DEFAULT 0, affected_family_members INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS projects(
        id INTEGER PRIMARY KEY,
        project_code TEXT UNIQUE, name TEXT, agency TEXT,
        district TEXT, state TEXT, project_type TEXT, authority TEXT
    );
    CREATE TABLE IF NOT EXISTS parcels(
        id INTEGER PRIMARY KEY,
        parcel_code TEXT UNIQUE, owner_id INTEGER, project_id INTEGER,
        survey_no TEXT, village TEXT, taluka TEXT, district TEXT, state TEXT,
        total_area TEXT, affected_area TEXT, acquired_area TEXT,
        acquisition_stage TEXT, notification_no TEXT, award_no TEXT,
        compensation_assessed REAL, compensation_paid REAL,
        possession_status TEXT, rr_status TEXT, latitude REAL, longitude REAL
    );
    CREATE TABLE IF NOT EXISTS grievances(
        id INTEGER PRIMARY KEY, ticket TEXT UNIQUE, owner_id INTEGER, parcel_id INTEGER,
        category TEXT, priority TEXT, status TEXT, sla_due TEXT, subject TEXT,
        description TEXT, officer_response TEXT DEFAULT '', remarks TEXT DEFAULT '',
        assigned_to TEXT, created TEXT, updated TEXT
    );
    CREATE TABLE IF NOT EXISTS grievance_events(
        id INTEGER PRIMARY KEY, ticket TEXT, status TEXT, actor TEXT,
        note TEXT, created TEXT
    );
    CREATE TABLE IF NOT EXISTS documents(
        id INTEGER PRIMARY KEY, ticket TEXT, name TEXT, doc_type TEXT,
        verification TEXT, uploaded_by TEXT, uploaded TEXT
    );
    CREATE TABLE IF NOT EXISTS reports(
        id INTEGER PRIMARY KEY, report_no TEXT, ticket TEXT,
        findings TEXT, recommendation TEXT, created TEXT
    );
    CREATE TABLE IF NOT EXISTS audit(
        id INTEGER PRIMARY KEY, action TEXT, ticket TEXT, actor TEXT, at TEXT
    );
    """)

    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        c.execute("INSERT INTO users(name,email,password,role,department,district) VALUES(?,?,?,?,?,?)",
                  ("Anita Deshmukh", "officer@nlams.demo", hp("officer123"),
                   "grievance_officer", "District Land Acquisition Cell", "Nagpur"))

    if c.execute("SELECT COUNT(*) FROM landowners").fetchone()[0] == 0:
        owners = [
            ("LO-0001", "Ramesh Patil", "9876543210", "ramesh@example.in", "At Borgaon, Near Gram Panchayat", "Borgaon", "Hingna", "Nagpur", "Maharashtra", 5, 3),
            ("LO-0002", "Sita Wankhede", "9822334455", "sita@example.in", "Ward No. 4, Kamptee", "Kamptee", "Kamptee", "Nagpur", "Maharashtra", 4, 2),
            ("LO-0003", "Mugdha Gharat", "9812345678", "mugdha@example.in", "Village Khed, Main Road", "Khed", "Khed", "Pune", "Maharashtra", 4, 2),
            ("LO-0004", "Vijay Shinde", "9898989898", "vijay@example.in", "At Nandgaon, Taluka Office Road", "Nandgaon", "Nandgaon", "Nashik", "Maharashtra", 6, 4),
            ("LO-0005", "Asha More", "9765432109", "asha@example.in", "At Talegaon, Bus Stand Road", "Talegaon", "Maval", "Pune", "Maharashtra", 3, 1),
        ]
        c.executemany("""INSERT INTO landowners(owner_code,name,mobile,email,address,village,taluka,district,state,family_members,affected_family_members)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?)""", owners)

    if c.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
        projects = [
            ("PRJ-SPH-001", "Solapur–Pune Highway", "National Highways Authority", "Pune", "Maharashtra", "Highway", "District Land Acquisition Authority"),
            ("PRJ-NGP-002", "Nagpur Ring Road", "Maharashtra State Road Development Corporation", "Nagpur", "Maharashtra", "Road", "District Land Acquisition Authority"),
            ("PRJ-NAS-003", "Nashik Industrial Corridor", "Maharashtra Industrial Development Corporation", "Nashik", "Maharashtra", "Industrial Corridor", "Special Land Acquisition Officer"),
        ]
        c.executemany("""INSERT INTO projects(project_code,name,agency,district,state,project_type,authority)
                         VALUES(?,?,?,?,?,?,?)""", projects)

    if c.execute("SELECT COUNT(*) FROM parcels").fetchone()[0] == 0:
        parcels = [
            ("PCL-1001",1,2,"GAT-142/3","Borgaon","Hingna","Nagpur","Maharashtra","4.50 ha","3.20 ha","2.80 ha","Award Declared","N-2025/114","A-2026/72",850000,600000,"Pending","In Progress",21.1458,79.0882),
            ("PCL-1002",2,1,"GAT-77/2","Kamptee","Kamptee","Nagpur","Maharashtra","3.10 ha","1.80 ha","1.20 ha","Notification Issued","N-2026/041","—",520000,0,"Pending","Not Started",21.2712,79.3000),
            ("PCL-1003",3,1,"125/2","Khed","Khed","Pune","Maharashtra","2.00 acres","2.00 acres","1.50 acres","Under Verification","N-2026/089","—",740000,250000,"Pending","In Progress",18.3386,73.8478),
            ("PCL-1004",4,3,"S.No. 44/1","Nandgaon","Nandgaon","Nashik","Maharashtra","5.60 ha","4.10 ha","3.90 ha","Compensation Assessed","N-2025/221","A-2026/103",1120000,900000,"Partially Taken","In Progress",20.3072,74.6550),
            ("PCL-1005",5,1,"GAT-19/7","Talegaon","Maval","Pune","Maharashtra","1.80 ha","1.10 ha","0.90 ha","Possession Pending","N-2025/198","A-2026/91",460000,460000,"Pending","Completed",18.7350,73.6750),
        ]
        c.executemany("""INSERT INTO parcels(parcel_code,owner_id,project_id,survey_no,village,taluka,district,state,total_area,affected_area,acquired_area,
                         acquisition_stage,notification_no,award_no,compensation_assessed,compensation_paid, possession_status,rr_status,latitude,longitude)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", parcels)

    if c.execute("SELECT COUNT(*) FROM grievances").fetchone()[0] == 0:
        grievances = [
            ("GRV-2026-000001",1,1,"Compensation", "High", "Under Review","2026-09-10","Compensation not fully paid","₹2.5 lakh remains unpaid after award.","Payment ledger verification initiated.","Payment record is being matched with award.","District/Field Officer","2026-09-02 17:47","2026-09-02 17:50"),
            ("GRV-2026-000002",2,2,"Possession", "Medium", "Under Verification","2026-09-13","Possession notice received late","Notice was not served in the expected timeline.","","Notice service register requested.","District/Field Officer","2026-09-03 10:15","2026-09-03 10:15"),
            ("GRV-2026-000003",1,1,"Compensation", "Medium", "Open","2026-09-12","Payment pending","Why is my balance compensation still pending?","","Pending payment record review.","Land Acquisition Authority","2026-09-04 09:20","2026-09-04 09:20"),
            ("GRV-2026-000004",3,3,"Wrong land/parcel information", "High", "Under Review","2026-09-09","Survey area shown incorrectly","The affected area shown online is higher than the field measurement.","Field verification scheduled.","Compare GIS boundary and latest field sketch.","District/Field Officer","2026-09-01 11:30","2026-09-05 14:00"),
            ("GRV-2026-000005",4,4,"R&R", "Medium", "Assigned","2026-09-15","R&R benefit not reflected","Eligible family benefit is not visible in the R&R record.","","R&R register verification pending.","R&R Officer","2026-09-04 13:10","2026-09-04 13:10"),
            ("GRV-2026-000006",5,5,"Document issue", "Low", "Resolved","2026-09-05","Award copy not available","Award copy was not available in the landowner document section.","Award copy has been uploaded to the record.","Document uploaded and verified.","District/Field Officer","2026-08-30 16:05","2026-09-03 12:20"),
            ("GRV-2026-000007",2,2,"Wrong land/parcel information", "Medium", "Escalated","2026-09-04","Ownership mismatch","Online record shows an old owner name after mutation.","Escalated to Land Records Authority.","Mutation record requested from Tahsil office.","District Officer","2026-08-28 09:40","2026-09-05 16:00"),
            ("GRV-2026-000008",4,4,"Notification issue", "High", "Open","2026-09-11","Notification copy requested","Landowner has requested the statutory notification copy and hearing details.","","Notification register and dispatch proof required.","Land Acquisition Authority","2026-09-05 10:25","2026-09-05 10:25"),
        ]
        c.executemany("""INSERT INTO grievances(ticket,owner_id,parcel_id,category,priority,status,sla_due,subject,description,officer_response,remarks,assigned_to,created,updated)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", grievances)

        events = [
            ("GRV-2026-000001","Complaint Submitted","Ramesh Patil","Grievance submitted by landowner.","2026-09-02 17:47"),
            ("GRV-2026-000001","Under Review","District Officer","Payment record verification started.","2026-09-02 17:50"),
            ("GRV-2026-000002","Complaint Submitted","Sita Wankhede","Grievance submitted by landowner.","2026-09-03 10:15"),
            ("GRV-2026-000002","Under Verification","District Officer","Notice service record requested.","2026-09-03 11:05"),
            ("GRV-2026-000004","Complaint Submitted","Mugdha Gharat","Wrong parcel information reported.","2026-09-01 11:30"),
            ("GRV-2026-000004","Under Review","District Officer","GIS and field measurement comparison started.","2026-09-05 14:00"),
            ("GRV-2026-000006","Complaint Submitted","Asha More","Award document requested.","2026-08-30 16:05"),
            ("GRV-2026-000006","Action Taken","District/Field Officer","Award copy uploaded and verified.","2026-09-03 12:00"),
            ("GRV-2026-000006","Resolved","District/Field Officer","Landowner document section updated.","2026-09-03 12:20"),
            ("GRV-2026-000007","Complaint Submitted","Sita Wankhede","Ownership mismatch reported.","2026-08-28 09:40"),
            ("GRV-2026-000007","Escalated","District Officer","Escalated to Land Records Authority.","2026-09-05 16:00"),
        ]
        c.executemany("INSERT INTO grievance_events(ticket,status,actor,note,created) VALUES(?,?,?,?,?)", events)

        docs = [
            ("GRV-2026-000001","7_12_Extract.pdf","Land Record","Verified","District/Field Officer","2026-09-02 18:00"),
            ("GRV-2026-000001","Award_Copy.pdf","Award","Verified","District/Field Officer","2026-09-02 18:02"),
            ("GRV-2026-000002","Possession_Notice.pdf","Possession Notice","Pending","District Officer","2026-09-03 11:00"),
            ("GRV-2026-000004","Field_Measurement_Sketch.pdf","Field Evidence","Pending","Field Officer","2026-09-05 14:15"),
            ("GRV-2026-000006","Award_Copy.pdf","Award","Verified","District/Field Officer","2026-09-03 12:00"),
            ("GRV-2026-000007","Mutation_Record.pdf","Land Record","Pending","Land Records Authority","2026-09-05 16:00"),
        ]
        c.executemany("INSERT INTO documents(ticket,name,doc_type,verification,uploaded_by,uploaded) VALUES(?,?,?,?,?,?)", docs)
    c.commit()
    c.close()


def sync_connected_grievances():
    try:
        payload = integration_get('/api/inbox/grievance_officer')
        if not isinstance(payload, list) or not payload:
            return
    except Exception:
        return
    c = con()
    for w in payload:
        ref = w.get('ref')
        if not ref:
            continue
        existing = c.execute('SELECT id FROM grievances WHERE ticket=?', (ref,)).fetchone()
        raw_pid = str(w.get('parcel_id') or '')
        parcel_id = int(raw_pid) if raw_pid.isdigit() else None
        if parcel_id and not c.execute('SELECT 1 FROM parcels WHERE id=?', (parcel_id,)).fetchone():
            parcel_id = None
        if parcel_id is None and raw_pid:
            row = c.execute('SELECT id FROM parcels WHERE parcel_code=? OR survey_no=? LIMIT 1', (raw_pid, raw_pid)).fetchone()
            parcel_id = row['id'] if row else None
        if parcel_id is None:
            row = c.execute('SELECT id FROM parcels ORDER BY id LIMIT 1').fetchone()
            parcel_id = row['id'] if row else None
        if parcel_id is None:
            continue
        owner_id = c.execute('SELECT owner_id FROM parcels WHERE id=?', (parcel_id,)).fetchone()['owner_id']
        low = ((w.get('title') or '') + ' ' + (w.get('description') or '')).lower()
        category = 'Compensation' if any(x in low for x in ('compensation','payment','award')) else ('Possession' if 'possession' in low else ('R&R' if 'r&r' in low or 'rehabilitation' in low else 'Other'))
        status_map = {'Submitted':'Open','Forwarded':'Under Review','Approved - Pending Next Officer':'Under Review','Completed':'Resolved','Rejected':'Rejected','Returned':'Open'}
        status = status_map.get(w.get('status'), w.get('status') or 'Open')
        created = w.get('created_at') or now()
        updated = w.get('updated_at') or created
        try:
            from datetime import timedelta
            sla = (datetime.fromisoformat(created) + timedelta(days=7)).date().isoformat()
        except Exception:
            sla = created[:10]
        if existing:
            c.execute('UPDATE grievances SET status=?,priority=?,subject=?,description=?,updated=? WHERE ticket=?', (status,w.get('priority','Medium'),w.get('title','Connected NLAMS Grievance'),w.get('description',''),updated,ref))
        else:
            c.execute("INSERT OR IGNORE INTO grievances(ticket,owner_id,parcel_id,category,priority,status,sla_due,subject,description,officer_response,remarks,assigned_to,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (ref,owner_id,parcel_id,category,w.get('priority','Medium'),status,sla,w.get('title','Connected NLAMS Grievance'),w.get('description',''),'','','Grievance Officer',created,updated))
        try:
            detail = integration_get('/api/workflow/'+urllib.parse.quote(ref, safe=''))
            for e in (detail.get('events') or []) if isinstance(detail, dict) else []:
                stamp = e.get('at') or now()
                actor = e.get('actor') or 'NLAMS'
                if not c.execute('SELECT 1 FROM grievance_events WHERE ticket=? AND created=? AND actor=?', (ref,stamp,actor)).fetchone():
                    c.execute('INSERT INTO grievance_events(ticket,status,actor,note,created) VALUES(?,?,?,?,?)', (ref,e.get('action') or e.get('status') or 'Workflow Update',actor,e.get('note',''),stamp))
        except Exception:
            pass
    c.commit(); c.close()

def auth_required():
    return "uid" in session


@app.before_request
def protect():
    public = {"login", "static"}
    if request.endpoint not in public and not auth_required():
        return redirect("/login")



@app.after_request
def _nlams_security_headers(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='SAMEORIGIN'
    response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    response.headers['Permissions-Policy']='geolocation=(self), camera=(), microphone=()'
    response.headers['Cache-Control']='no-store'
    return response

@app.route("/")
def home():
    return redirect("/dashboard")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        d = request.form
        c = con()
        u = c.execute("SELECT * FROM users WHERE email=? AND password=? AND role='grievance_officer'",
                      (d.get("email", ""), hp(d.get("password", "")))).fetchone()
        c.close()
        if u:
            session["uid"] = u["id"]
            session["name"] = u["name"]
            session["role"] = u["role"]
            return redirect("/dashboard")
        return render_template("login.html", error="Invalid grievance officer credentials")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/dashboard")
def dashboard():
    if session.get("role") != "grievance_officer": return redirect("/login")
    return render_template("dashboard.html", officer_name=session.get("name", "Grievance Officer"))


@app.route("/grievance/<ticket>")
def grievance_detail(ticket):
    if session.get("role") != "grievance_officer": return redirect("/login")
    c = con()
    g = c.execute("""SELECT g.*, lo.*, p.*, pr.project_code, pr.name AS project_name,
                            pr.agency, pr.project_type, pr.authority, pr.district AS project_district,
                            pr.state AS project_state
                     FROM grievances g
                     JOIN landowners lo ON lo.id=g.owner_id
                     JOIN parcels p ON p.id=g.parcel_id
                     JOIN projects pr ON pr.id=p.project_id
                     WHERE g.ticket=?""", (ticket,)).fetchone()
    c.close()
    if not g:
        abort(404)
    return render_template("grievance_detail.html", g=dict(g), officer_name=session.get("name", "Grievance Officer"))


@app.route("/api/dashboard")
def dashboard_api():
    if session.get("role") != "grievance_officer": return jsonify({"error":"Unauthorized"}), 401
    sync_connected_grievances()
    c = con()
    rows = c.execute("""SELECT g.*, lo.name AS owner_name, lo.mobile, lo.owner_code,
                              p.parcel_code, p.survey_no, p.village, p.district,
                              pr.name AS project_name
                       FROM grievances g
                       JOIN landowners lo ON lo.id=g.owner_id
                       JOIN parcels p ON p.id=g.parcel_id
                       JOIN projects pr ON pr.id=p.project_id
                       ORDER BY CASE g.priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END,
                                g.created DESC""").fetchall()
    projects = c.execute("SELECT name, COUNT(*) AS count FROM grievances g JOIN parcels p ON p.id=g.parcel_id JOIN projects pr ON pr.id=p.project_id GROUP BY pr.id ORDER BY count DESC").fetchall()
    categories = c.execute("SELECT category, COUNT(*) AS count FROM grievances GROUP BY category ORDER BY count DESC").fetchall()
    c.close()
    return jsonify({"rows":[dict(x) for x in rows], "projects":[dict(x) for x in projects], "categories":[dict(x) for x in categories]})


@app.route("/api/grievance/<ticket>")
def one(ticket):
    if session.get("role") != "grievance_officer": return jsonify({"error":"Unauthorized"}), 401
    sync_connected_grievances()
    c = con()
    g = c.execute("""SELECT g.*, lo.*, p.*, pr.project_code, pr.name AS project_name,
                            pr.agency, pr.project_type, pr.authority,
                            pr.district AS project_district, pr.state AS project_state
                     FROM grievances g
                     JOIN landowners lo ON lo.id=g.owner_id
                     JOIN parcels p ON p.id=g.parcel_id
                     JOIN projects pr ON pr.id=p.project_id
                     WHERE g.ticket=?""", (ticket,)).fetchone()
    if not g:
        c.close(); abort(404)
    events = c.execute("SELECT * FROM grievance_events WHERE ticket=? ORDER BY created", (ticket,)).fetchall()
    docs = c.execute("SELECT * FROM documents WHERE ticket=? ORDER BY uploaded DESC", (ticket,)).fetchall()
    c.close()
    data = dict(g)
    data["compensation_pending"] = max(0, (data["compensation_assessed"] or 0) - (data["compensation_paid"] or 0))
    return jsonify({"grievance":data, "events":[dict(x) for x in events], "documents":[dict(x) for x in docs]})


@app.route("/api/triage", methods=["POST"])
def triage():
    t = request.get_json().get("text", "").lower()
    cats = {
        "Compensation": ["compensation", "payment", "award", "money", "unpaid"],
        "Possession": ["possession", "handover"],
        "R&R": ["rehabilitation", "resettlement", "displaced"],
        "Land Record": ["survey", "gat", "7/12", "ownership", "parcel"],
        "Notification": ["notification", "notice"],
    }
    scores = {k: sum(w in t for w in v) for k, v in cats.items()}
    cat = max(scores, key=scores.get) if max(scores.values()) else "Other"
    pri = "High" if any(w in t for w in ["urgent", "court", "stay", "unpaid", "displaced", "wrong land"]) else "Medium"
    return jsonify({"category":cat, "priority":pri, "confidence":min(.98, .55 + .12 * scores[cat]), "scores":scores})


@app.route("/api/duplicates", methods=["POST"])
def duplicates():
    d = request.get_json(); c = con()
    r = c.execute("""SELECT g.ticket, g.subject, g.status, g.category, lo.name AS owner_name,
                            p.survey_no, pr.name AS project_name
                     FROM grievances g JOIN landowners lo ON lo.id=g.owner_id
                     JOIN parcels p ON p.id=g.parcel_id JOIN projects pr ON pr.id=p.project_id
                     WHERE (g.owner_id=(SELECT id FROM landowners WHERE name=? LIMIT 1) OR lo.name LIKE ?)
                       AND p.survey_no=?""", (d.get("owner",""), "%"+d.get("owner","")+"%", d.get("survey_no",""))).fetchall()
    c.close(); return jsonify({"rows":[dict(x) for x in r]})


@app.route("/api/verify", methods=["POST"])
def verify():
    t = request.get_json().get("text", "").lower()
    fields = {"Survey/Gat":"gat" in t or "survey" in t, "Notification":"notification" in t or "notice" in t,
              "Award":"award" in t, "Compensation":"compensation" in t or "₹" in t, "Possession":"possession" in t}
    return jsonify({"confidence":.92 if sum(fields.values()) >= 4 else .70,
                    "checks":[{"field":k,"status":"Verified" if v else "Needs Review"} for k,v in fields.items()]})


@app.route("/api/report", methods=["POST"])
def report():
    d=request.get_json() or {}
    ticket=(d.get("ticket") or "").strip(); findings=(d.get("findings") or "").strip(); recommendation=(d.get("recommendation") or "").strip()
    if not ticket or not findings or not recommendation:
        return jsonify(ok=False,error="Grievance ID, findings and recommendation are required."),400
    report_no=f"VR-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"
    con=db(); con.execute("INSERT INTO reports(report_no,ticket,findings,recommendation,created_at) VALUES(?,?,?,?,?)",(report_no,ticket,findings,recommendation,now())); con.commit(); con.close()
    return jsonify(ok=True,report_no=report_no)

@app.route("/api/grievance/update", methods=["POST"])
def update_grievance():
    if session.get("role") != "grievance_officer": return jsonify({"ok":False,"error":"Unauthorized"}), 401
    d = request.get_json(); ticket = d.get("ticket")
    status = d.get("status", "Under Review")
    priority = d.get("priority", "Medium")
    category = d.get("category", "Other")
    remarks = d.get("remarks", "")
    response = d.get("response", "")
    c = con()
    g = c.execute("SELECT status FROM grievances WHERE ticket=?", (ticket,)).fetchone()
    if not g:
        c.close(); return jsonify({"ok":False,"error":"Grievance not found"}), 404
    c.execute("UPDATE grievances SET status=?,priority=?,category=?,remarks=?,officer_response=?,updated=? WHERE ticket=?",
              (status,priority,category,remarks,response,now(),ticket))
    c.execute("INSERT INTO grievance_events(ticket,status,actor,note,created) VALUES(?,?,?,?,?)",
              (ticket,status,session.get("name","District Officer"),remarks or response or "Status updated by officer.",now()))
    c.execute("INSERT INTO audit(action,ticket,actor,at) VALUES(?,?,?,?)",
              (f"Status changed: {g['status']} → {status}",ticket,session.get("name","Officer"),now()))
    c.commit(); c.close()
    if status in ("Under Review", "Action Taken", "Resolved", "Escalated"):
        integration_post("/api/workflow/%s/transition" % ticket, {"actor_role":"grievance_officer","actor_name":session.get("name","Grievance Officer"),"action":"forward" if status != "Resolved" else "approve","note":remarks or response or "Grievance reviewed in officer portal."})
    return jsonify({"ok":True})


if __name__ == "__main__":
    init()
    app.run(port=int(__import__("os").environ.get("NLAMS_PORT", "5002")), debug=True)
