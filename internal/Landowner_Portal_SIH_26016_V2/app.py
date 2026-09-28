from flask import Flask, render_template, request, jsonify, session, redirect, flash
import sqlite3, os, hashlib, uuid, re, secrets
from datetime import datetime
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
try:
    from client import post as integration_post
except Exception:
    integration_post=lambda path,payload: {"ok":False,"offline":True}

app=Flask(__name__); app.secret_key="SIH26016-DEMO-SECRET"
DB=os.path.join(os.path.dirname(__file__),"landowner.db")

def con():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def hashpw(p):
    try:
        import bcrypt
        return "bcrypt$" + bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
    except Exception:
        # Demo fallback when bcrypt is unavailable; production deployments should install bcrypt.
        return "scrypt$" + hashlib.scrypt(p.encode(), salt=b"NLAMS-DEMO-SALT", n=2**14, r=8, p=1).hex()

def checkpw(p, stored):
    try:
        if stored.startswith("bcrypt$"):
            import bcrypt
            return bcrypt.checkpw(p.encode(), stored[7:].encode())
        if stored.startswith("scrypt$"):
            return secrets.compare_digest(stored[7:], hashlib.scrypt(p.encode(), salt=b"NLAMS-DEMO-SALT", n=2**14, r=8, p=1).hex())
        return secrets.compare_digest(stored, hashlib.sha256(p.encode()).hexdigest())
    except Exception:
        return False

def valid_email(v): return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v or ""))
def valid_mobile(v): return bool(re.fullmatch(r"[6-9]\d{9}", re.sub(r"\D", "", v or "")))


def init():
    c=con()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,email TEXT UNIQUE,mobile TEXT,password TEXT,role TEXT,landowner_id TEXT UNIQUE,account_status TEXT DEFAULT 'VERIFIED',rejection_reason TEXT DEFAULT '',created_at TEXT,otp_hash TEXT DEFAULT '',otp_expires TEXT DEFAULT '',otp_attempts INTEGER DEFAULT 0,auth_method TEXT DEFAULT 'password',verified_at TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS landowner_registrations(id INTEGER PRIMARY KEY AUTOINCREMENT,landowner_id TEXT UNIQUE,user_id INTEGER,name TEXT,email TEXT,mobile TEXT,survey_no TEXT,gat_no TEXT,land_type TEXT,village TEXT,taluka TEXT,district TEXT,nearby_identifier TEXT,project_id TEXT,parcel_id TEXT,status TEXT DEFAULT 'PENDING VERIFICATION',rejection_reason TEXT DEFAULT '',created_at TEXT,updated_at TEXT);
    CREATE TABLE IF NOT EXISTS registration_documents(id INTEGER PRIMARY KEY AUTOINCREMENT,landowner_id TEXT,document_id TEXT UNIQUE,name TEXT,sha256 TEXT,status TEXT DEFAULT 'Verified',uploaded_at TEXT);
    CREATE TABLE IF NOT EXISTS parcels(id INTEGER PRIMARY KEY,owner_id INTEGER,survey_no TEXT,village TEXT,district TEXT,state TEXT,total_area REAL,affected_area REAL,acquired_area REAL,lat REAL,lng REAL,stage TEXT,notification_no TEXT,award_no TEXT,comp_assessed REAL,comp_paid REAL,possession TEXT,rr_status TEXT);
    CREATE TABLE IF NOT EXISTS milestones(id INTEGER PRIMARY KEY,parcel_id INTEGER,stage TEXT,status TEXT,date TEXT,authority TEXT,next_action TEXT,sort_order INTEGER);
    CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY,owner_id INTEGER,name TEXT,type TEXT,status TEXT,uploaded TEXT);
    CREATE TABLE IF NOT EXISTS grievances(id INTEGER PRIMARY KEY,ticket TEXT,owner_id INTEGER,parcel_id INTEGER,subject TEXT,description TEXT,status TEXT,created TEXT,landowner_id TEXT,project_id TEXT,hold_reason TEXT);
    CREATE TABLE IF NOT EXISTS alerts(id INTEGER PRIMARY KEY,owner_id INTEGER,title TEXT,message TEXT,due TEXT,severity TEXT,read INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,user_id INTEGER,action TEXT,at TEXT);
    CREATE TABLE IF NOT EXISTS user_documents(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,landowner_id TEXT,parcel_id INTEGER,grievance_ticket TEXT,document_id TEXT UNIQUE,name TEXT,category TEXT,sha256 TEXT UNIQUE,size INTEGER,status TEXT DEFAULT 'Verified',storage_path TEXT,uploaded_at TEXT);
    """)
    for table, cols in [("users", [("landowner_id","TEXT"),("account_status","TEXT DEFAULT 'VERIFIED'"),("rejection_reason","TEXT DEFAULT ''"),("created_at","TEXT")]), ("grievances", [("landowner_id","TEXT"),("project_id","TEXT"),("hold_reason","TEXT")])]:
        existing={r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()}
        for name,typ in cols:
            if name not in existing: c.execute(f"ALTER TABLE {table} ADD COLUMN {name} {typ}")

    c.execute("CREATE INDEX IF NOT EXISTS idx_user_docs_owner ON user_documents(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_user_docs_hash ON user_documents(sha256)")
    # Backward-compatible security columns for existing demo databases.
    for col, definition in [("otp_hash","TEXT DEFAULT ''"),("otp_expires","TEXT DEFAULT ''"),("otp_attempts","INTEGER DEFAULT 0"),("auth_method","TEXT DEFAULT 'password'"),("verified_at","TEXT DEFAULT ''")]:
        try: c.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
        except sqlite3.OperationalError: pass

    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0]==0:
        c.execute("INSERT INTO users(name,email,mobile,password,role,landowner_id,account_status,created_at) VALUES(?,?,?,?,?,?,?,?)",("Ramesh Patil","ramesh@nlams.demo","9876543210",hashpw("land123"),"landowner","LND-DEMO01","VERIFIED",datetime.now().isoformat(timespec="minutes")))
        uid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
        c.execute("""INSERT INTO parcels(owner_id,survey_no,village,district,state,total_area,affected_area,acquired_area,lat,lng,stage,notification_no,award_no,comp_assessed,comp_paid,possession,rr_status)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(uid,"GAT-142/3","Borgaon","Nagpur","Maharashtra",4.5,3.2,2.8,21.1458,79.0882,"Award Declared","N-2025/114","A-2026/72",850000,600000,"Pending","In Progress"))
        pid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
        stages=[("Proposal","completed","2025-02-10","District Authority","Survey"),("Survey","completed","2025-03-18","LAO","Notification"),("Notification","completed","2025-05-02","Collector","Objection"),("Objection","completed","2025-06-14","Hearing Officer","Award"),("Award","current","2026-07-20","LAO","Compensation release"),("Compensation","pending","","Treasury","Payment"),("Possession","pending","","District Administration","Possession notice"),("R&R","pending","","R&R Cell","R&R package")]
        for i,x in enumerate(stages): c.execute("INSERT INTO milestones(parcel_id,stage,status,date,authority,next_action,sort_order) VALUES(?,?,?,?,?,?,?)",(pid,*x,i))
        alerts=[("Notice response deadline","Respond to the latest notice before the deadline.","2026-09-15","high"),("Compensation update","₹2,50,000 remains pending.","2026-09-20","high"),("R&R milestone","R&R verification is scheduled.","2026-09-28","medium")]
        for a in alerts:c.execute("INSERT INTO alerts(owner_id,title,message,due,severity) VALUES(?,?,?,?,?)",(uid,*a))
        c.execute("INSERT INTO documents(owner_id,name,type,status,uploaded) VALUES(?,?,?,?,?)",(uid,"7_12_Extract.pdf","Land Record","Verified","2026-08-10"))
        c.execute("INSERT INTO documents(owner_id,name,type,status,uploaded) VALUES(?,?,?,?,?)",(uid,"Award_Copy.pdf","Award","Verified","2026-08-12"))
        c.commit()
    c.close()


@app.after_request
def _nlams_security_headers(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='SAMEORIGIN'
    response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    response.headers['Permissions-Policy']='geolocation=(self), camera=(), microphone=()'
    response.headers['Cache-Control']='no-store'
    return response

@app.route("/")
def home(): return redirect("/dashboard") if "uid" in session else redirect("/auth")
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        d=request.form;c=con();u=c.execute("SELECT * FROM users WHERE email=? AND role='landowner'",(d.get("email","").strip().lower(),)).fetchone();
        ok = bool(u and checkpw(d.get("password",""), u["password"]))
        if ok:
            session.clear(); session["uid"]=u["id"]; session["landowner_id"]=u["landowner_id"]; session["account_status"]=u["account_status"] or "PENDING VERIFICATION"; return redirect("/dashboard")
        c.close(); return render_template("login.html",error="Invalid landowner credentials")
    return render_template("login.html")
@app.route("/logout")
def logout(): session.clear(); return redirect("/login")
@app.route("/auth")
def auth_landing():
    return render_template("auth.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "GET": return render_template("register.html")
    d=request.form
    name=d.get("name","").strip(); email=d.get("email","").strip().lower(); mobile=re.sub(r"\D","",d.get("mobile",""))
    if not name or not valid_email(email) or not valid_mobile(mobile): return render_template("register.html",error="Enter a valid name, email and 10-digit Indian mobile number.",data=d)
    if len(d.get("password","")) < 8 or d.get("password") != d.get("confirm_password"): return render_template("register.html",error="Password must be at least 8 characters and both passwords must match.",data=d)
    if not d.get("consent"): return render_template("register.html",error="Privacy consent is required to create an NLAMS account.",data=d)
    c=con()
    existing=c.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
    now=datetime.now().isoformat(timespec="minutes")
    if existing and existing["account_status"]=="REJECTED":
        landowner_id=existing["landowner_id"]; user_id=existing["id"]
        c.execute("UPDATE users SET name=?,mobile=?,password=?,account_status='PENDING VERIFICATION',rejection_reason='',created_at=? WHERE id=?",(name,mobile,hashpw(d["password"]),now,user_id))
        c.execute("DELETE FROM landowner_registrations WHERE landowner_id=?",(landowner_id,))
    elif existing:
        c.close(); return render_template("register.html",error="An account already exists for this email. Please sign in.",data=d)
    else:
        landowner_id="LND-"+secrets.token_hex(3).upper()
        c.execute("INSERT INTO users(name,email,mobile,password,role,landowner_id,account_status,created_at) VALUES(?,?,?,?,?,?,?,?)",(name,email,mobile,hashpw(d["password"]),"landowner",landowner_id,"PENDING VERIFICATION",now))
        user_id=c.execute("SELECT last_insert_rowid()").fetchone()[0]
    # Project/parcel is optional at registration. If the survey/village matches a central parcel, link it automatically; otherwise keep the account usable and let the owner raise a project-discovery request.
    project_id=(d.get("project_id") or "").strip(); parcel_id=(d.get("parcel_id") or "").strip()
    if not project_id or not parcel_id:
        try:
            import urllib.parse, urllib.request, json as _json
            qs=urllib.parse.urlencode({'survey_no':d.get('survey_no','').strip(),'village':d.get('village','').strip()})
            lookup=_json.loads(urllib.request.urlopen('http://127.0.0.1:8090/api/landowner/project-lookup?'+qs,timeout=2).read().decode())
            if lookup:
                project_id=lookup[0].get('project_id',''); parcel_id=lookup[0].get('parcel_id','')
        except Exception:
            pass
    c.execute("INSERT INTO landowner_registrations(landowner_id,user_id,name,email,mobile,survey_no,gat_no,land_type,village,taluka,district,nearby_identifier,project_id,parcel_id,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(landowner_id,user_id,name,email,mobile,d.get("survey_no"),d.get("gat_no"),d.get("land_type"),d.get("village"),d.get("taluka"),d.get("district"),d.get("nearby_identifier"),project_id,parcel_id,"PENDING VERIFICATION",now,now))
    # OTP is generated for the registration step. In this local prototype it is logged to the server console; production must connect an approved SMS/OTP provider.
    otp=str(secrets.randbelow(900000)+100000)
    otp_hash=hashlib.sha256(otp.encode()).hexdigest(); exp=(datetime.now()+__import__('datetime').timedelta(minutes=5)).isoformat()
    c.execute("UPDATE users SET otp_hash=?,otp_expires=?,otp_attempts=0,auth_method='mobile_otp' WHERE id=?",(otp_hash,exp,user_id)); c.commit(); c.close()
    print(f"[NLAMS DEMO OTP] {landowner_id} mobile={mobile} OTP={otp} expires={exp}")
    try: integration_post("/api/landowners/register", {"landowner_id":landowner_id,"name":name,"email":email,"mobile":mobile,"survey_no":d.get("survey_no"),"gat_no":d.get("gat_no"),"land_type":d.get("land_type"),"village":d.get("village"),"taluka":d.get("taluka"),"district":d.get("district"),"nearby_identifier":d.get("nearby_identifier"),"project_id":project_id,"parcel_id":parcel_id,"status":"PENDING VERIFICATION","created_at":now})
    except Exception: pass
    session.clear(); session["uid"]=user_id; session["landowner_id"]=landowner_id; session["account_status"]="PENDING OTP"
    return redirect("/verify-otp")

@app.route("/verify-otp", methods=["GET","POST"])
def verify_otp():
    if "uid" not in session: return redirect("/login")
    c=con(); u=c.execute("SELECT * FROM users WHERE id=?",(session["uid"],)).fetchone()
    if request.method=="POST":
        code=re.sub(r"\D","",request.form.get("otp",""))
        if not u or not u["otp_hash"] or u["otp_expires"] < datetime.now().isoformat():
            c.close(); return render_template("verify_otp.html",error="OTP expired. Please register again or request a new OTP.",mobile=(u["mobile"] if u else ""))
        if int(u["otp_attempts"] or 0) >= 5:
            c.close(); return render_template("verify_otp.html",error="Too many OTP attempts. Please register again.",mobile=u["mobile"])
        c.execute("UPDATE users SET otp_attempts=otp_attempts+1 WHERE id=?",(u["id"],))
        if secrets.compare_digest(hashlib.sha256(code.encode()).hexdigest(),u["otp_hash"]):
            now=datetime.now().isoformat(timespec="minutes"); c.execute("UPDATE users SET auth_method='mobile_otp',verified_at=?,otp_hash='',otp_expires='',otp_attempts=0 WHERE id=?",(now,u["id"])); c.commit(); c.close(); session["account_status"]="PENDING VERIFICATION"; return redirect("/registration-success")
        c.commit(); c.close(); return render_template("verify_otp.html",error="Invalid OTP.",mobile=u["mobile"])
    c.close(); return render_template("verify_otp.html",mobile=u["mobile"] if u else "")

@app.route("/registration-success")
def registration_success():
    if "uid" not in session: return redirect("/login")
    return render_template("registration_success.html",landowner_id=session.get("landowner_id"))

@app.route("/api/privacy")
def privacy():
    return jsonify({"title":"NLAMS Data Privacy & Security","principles":["Purpose-limited collection","Consent before identity verification","Passwords stored as strong password hashes","OTP is time-limited and never stored after successful verification","Aadhaar numbers/biometrics must not be stored in this prototype","Role-based access and audit logging","HTTPS/TLS, centralized IAM, encryption, KMS/HSM and approved government hosting are required for production"]})

@app.route("/account-status")
def account_status():
    if "uid" not in session: return redirect("/login")
    c=con(); u=c.execute("SELECT landowner_id,account_status,rejection_reason FROM users WHERE id=?",(session["uid"],)).fetchone(); c.close()
    session["account_status"]=u["account_status"] if u else "PENDING VERIFICATION"
    return jsonify(dict(u) if u else {})

@app.route("/dashboard")
def dashboard(): return render_template("dashboard.html",user=session.get("uid"))
def uid(): return session["uid"]
@app.route("/api/me")
def me():
    c=con();u=c.execute("SELECT id,name,email,mobile,landowner_id,account_status,rejection_reason FROM users WHERE id=?",(uid(),)).fetchone();p=c.execute("SELECT * FROM parcels WHERE owner_id=?",(uid(),)).fetchall();g=c.execute("SELECT ticket,status,subject,created,hold_reason FROM grievances WHERE owner_id=? ORDER BY id DESC",(uid(),)).fetchall(); c.close();return jsonify({"user":dict(u),"parcels":[dict(x) for x in p],"account_status":u["account_status"] if u else "PENDING VERIFICATION","rejection_reason":u["rejection_reason"] if u else "","grievances":[dict(x) for x in g]})
@app.route("/api/parcel/<int:pid>")
def parcel(pid):
    c=con();p=c.execute("SELECT * FROM parcels WHERE id=? AND owner_id=?",(pid,uid())).fetchone();m=c.execute("SELECT * FROM milestones WHERE parcel_id=? ORDER BY sort_order",(pid,)).fetchall();c.close();return jsonify({"parcel":dict(p),"milestones":[dict(x) for x in m]})
@app.route("/api/alerts")
def alerts():
    c=con();x=c.execute("SELECT * FROM alerts WHERE owner_id=? ORDER BY due",(uid(),)).fetchall();c.close();return jsonify([dict(a) for a in x])
@app.route("/api/documents")
def docs():
    c=con();x=c.execute("SELECT * FROM documents WHERE owner_id=? ORDER BY uploaded DESC",(uid(),)).fetchall();c.close();return jsonify([dict(a) for a in x])
@app.route('/api/project-discovery-request',methods=['POST'])
def project_discovery_request():
    if 'uid' not in session: return jsonify({'error':'Authentication required'}),401
    d=request.get_json(silent=True) or {}; u=con().execute('SELECT landowner_id FROM users WHERE id=?',(uid(),)).fetchone()
    payload={'survey_no':d.get('survey_no',''),'gat_no':d.get('gat_no',''),'village':d.get('village',''),'district':d.get('district',''),'landowner_id':u['landowner_id'] if u else ''}
    try:
        result=integration_post('/api/landowner/project-discovery-request',payload)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error':'Central workflow service unavailable'}),503
@app.route("/api/grievance",methods=["POST"])
def grievance():
    d=request.get_json();c=con();p=c.execute("SELECT id FROM parcels WHERE id=? AND owner_id=?",(d["parcel_id"],uid())).fetchone();
    if not p: c.close(); return jsonify({"error":"Parcel not found"}),404
    u=c.execute("SELECT landowner_id,account_status FROM users WHERE id=?",(uid(),)).fetchone(); status="Submitted" if u["account_status"]=="VERIFIED" else "ON HOLD"; hold="" if status=="Submitted" else "Awaiting Project Agency verification of landowner account."
    ticket="GRV-"+datetime.now().strftime("%Y%m%d")+"-"+uuid.uuid4().hex[:5].upper(); now=datetime.now().isoformat(timespec="minutes")
    c.execute("INSERT INTO grievances(ticket,owner_id,parcel_id,subject,description,status,created,landowner_id,project_id,hold_reason) VALUES(?,?,?,?,?,?,?,?,?,?)",(ticket,uid(),p["id"],d["subject"],d["description"],status,now,u["landowner_id"],d.get("project_id","NH44-MH-001"),hold)); c.commit(); c.close()
    if status=="Submitted": integration_post("/api/grievances/submit", {"ticket":ticket,"subject":d["subject"],"description":d["description"],"parcel_id":str(d["parcel_id"]),"landowner_id":u["landowner_id"],"project_id":d.get("project_id","NH44-MH-001"),"created_by":"Landowner","priority":"High"})
    return jsonify({"ticket":ticket,"status":status,"message":"Complaint forwarded to Grievance Officer." if status=="Submitted" else "Complaint registered successfully and placed ON HOLD until account verification."})
@app.route("/api/documents/upload", methods=["POST"])
def upload_document():
    if "uid" not in session: return jsonify({"error":"Authentication required"}),401
    f=request.files.get("document")
    if not f or not f.filename: return jsonify({"error":"Select a document to upload"}),400
    allowed={"pdf","jpg","jpeg","png","doc","docx","txt"}
    ext=f.filename.rsplit(".",1)[-1].lower() if "." in f.filename else ""
    if ext not in allowed: return jsonify({"error":"Allowed formats: PDF, JPG, PNG, DOC, DOCX, TXT"}),400
    raw=f.read()
    if len(raw)>10*1024*1024: return jsonify({"error":"Maximum file size is 10 MB"}),400
    sha=hashlib.sha256(raw).hexdigest()
    c=con(); u=c.execute("SELECT landowner_id FROM users WHERE id=?",(uid(),)).fetchone()
    dup=c.execute("SELECT document_id,name,uploaded_at FROM user_documents WHERE sha256=?",(sha,)).fetchone()
    if dup:
        c.close(); return jsonify({"duplicate":True,"error":"DUPLICATE DOCUMENT DETECTED","existing":dict(dup)}),409
    doc_id="DOC-"+uuid.uuid4().hex[:10].upper()
    storage_dir=os.path.join(os.path.dirname(__file__),"secure_uploads"); os.makedirs(storage_dir,exist_ok=True)
    safe=re.sub(r"[^A-Za-z0-9._-]","_",f.filename); path=os.path.join(storage_dir,doc_id+"_"+safe)
    with open(path,"wb") as out: out.write(raw)
    parcel_id=request.form.get("parcel_id") or None; ticket=request.form.get("grievance_ticket") or None; category=request.form.get("category") or "Supporting Evidence"; now=datetime.now().isoformat(timespec="minutes")
    c.execute("INSERT INTO user_documents(user_id,landowner_id,parcel_id,grievance_ticket,document_id,name,category,sha256,size,status,storage_path,uploaded_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(uid(),u["landowner_id"],parcel_id,ticket,doc_id,f.filename,category,sha,len(raw),"Verified",path,now))
    c.execute("INSERT INTO audit(user_id,action,at) VALUES(?,?,?)",(uid(),"Secure document uploaded: "+doc_id,now)); c.commit(); c.close()
    try: integration_post("/api/shared/document",{"project_id":"NH44-MH-001","parcel_id":parcel_id or "","category":category,"name":f.filename,"type":ext.upper(),"uploaded_by":"Landowner "+u["landowner_id"],"status":"Pending Review","version":1,"source_path":doc_id})
    except Exception: pass
    return jsonify({"ok":True,"document_id":doc_id,"name":f.filename,"sha256":sha,"status":"Verified","message":"Document securely stored and linked to your NLAMS case."})

@app.route("/api/compensation/<int:pid>")
def compensation(pid):
    c=con();p=c.execute("SELECT * FROM parcels WHERE id=? AND owner_id=?",(pid,uid())).fetchone();c.close();ass=p["comp_assessed"];paid=p["comp_paid"];return jsonify({"land_value":ass*.625,"assets":ass*.125,"benefits":ass*.25,"assessed":ass,"paid":paid,"pending":ass-paid})
@app.route("/api/document-ai",methods=["POST"])
def document_ai():
    text=request.get_json().get("text",""); words=text.lower();keys=[x for x in ["survey","gat","7/12","award","notification","compensation","possession","rehabilitation"] if x in words]
    summary=" ".join([s.strip() for s in text.replace("\n"," ").split(".") if s.strip()][:3])
    return jsonify({"summary":summary or "No readable text supplied.","document_type":"Land Acquisition Document" if keys else "Unclassified","fields":keys})
if __name__=="__main__": init();app.run(port=int(__import__("os").environ.get("NLAMS_PORT", "5005")),debug=True)
