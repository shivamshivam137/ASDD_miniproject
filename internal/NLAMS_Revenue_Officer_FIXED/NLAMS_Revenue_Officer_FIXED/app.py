from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "nlams.db")
app = Flask(__name__)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=False, PERMANENT_SESSION_LIFETIME=1800)
app.secret_key = "nlams-demo-secret"


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS cases(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      case_id TEXT UNIQUE, project TEXT, district TEXT, taluka TEXT, village TEXT,
      survey_no TEXT, area REAL, agency_owner TEXT, revenue_owner TEXT,
      land_type TEXT, status TEXT DEFAULT 'Pending Verification',
      encumbrance TEXT DEFAULT 'Clear', lat REAL, lng REAL, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS documents(
      id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT, name TEXT, status TEXT
    );
    CREATE TABLE IF NOT EXISTS audit(
      id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT, action TEXT, actor TEXT, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS issues(
      id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT, issue_type TEXT, description TEXT,
      status TEXT DEFAULT 'Open', created_at TEXT
    );
    """)
    # Upgrade older demo databases without deleting user data.
    cols = {r[1] for r in con.execute("PRAGMA table_info(cases)").fetchall()}
    if 'lat' not in cols: con.execute("ALTER TABLE cases ADD COLUMN lat REAL")
    if 'lng' not in cols: con.execute("ALTER TABLE cases ADD COLUMN lng REAL")
    if con.execute("SELECT COUNT(*) FROM cases").fetchone()[0] == 0:
        cases = [
          ("NH44-MH-001-P-001","NH-44 Highway Expansion","Pune","Pune","Pimpalgaon","125",2.50,"Demo Owner A","Demo Owner A","Agricultural","Pending Verification","Clear"),
          ("NH44-MH-001-P-002","NH-44 Highway Expansion","Pune","Pune","Pimpalgaon","126",3.00,"Demo Owner B","Demo Owner B","Agricultural","Pending Verification","Clear"),
          ("NH44-MH-001-P-003","NH-44 Highway Expansion","Pune","Pune","Wagholi","128",1.80,"Demo Owner C","Demo Owner C","Agricultural","Pending Verification","Clear")
        ]
        for c in cases:
            con.execute("""INSERT INTO cases
            (case_id,project,district,taluka,village,survey_no,area,agency_owner,revenue_owner,land_type,status,encumbrance,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (*c, now()))
        docs = [
          ("NH44-MH-001-P-001","7/12 Extract","Verified"),("NH44-MH-001-P-001","Mutation Certificate","Verified"),
          ("NH44-MH-001-P-001","Ownership Document","Pending"),("NH44-MH-001-P-001","Village Map","Verified"),
          ("NH44-MH-001-P-001","Encumbrance Certificate","Verified"),
          ("NH44-MH-001-P-002","7/12 Extract","Verified"),("NH44-MH-001-P-002","Mutation Certificate","Verified"),
          ("NH44-MH-001-P-002","Ownership Document","Verified"),
          ("NH44-MH-001-P-003","7/12 Extract","Verified"),("NH44-MH-001-P-003","Mutation Certificate","Issue")
        ]
        con.executemany("INSERT INTO documents(case_id,name,status) VALUES(?,?,?)", docs)
        seed_audit = [
          ("NH44-MH-001-P-001","Case assigned for revenue verification","LAO",now()),
          ("NH44-MH-001-P-001","7/12 Extract verified","Revenue Officer",now()),
          ("NH44-MH-001-P-002","Revenue verification approved","Revenue Officer",now()),
          ("NH44-MH-001-P-003","Record mismatch detected","Revenue Officer",now())
        ]
        con.executemany("INSERT INTO audit(case_id,action,actor,created_at) VALUES(?,?,?,?)", seed_audit)
        con.execute("INSERT INTO issues(case_id,issue_type,description,status,created_at) VALUES(?,?,?,?,?)",
                     ("NH44-MH-001-P-003","Encumbrance","Active mortgage found in revenue record. Further review required.","Open",now()))
    # Make the prototype useful even when an older demo database already exists.
    con.executemany("UPDATE cases SET lat=?, lng=? WHERE case_id=?", [
      (18.5204,73.8567,'NH44-MH-001-P-001'),
      (18.5230,73.8590,'NH44-MH-001-P-002'),
      (18.5750,73.9850,'NH44-MH-001-P-003')
    ])
    if con.execute("SELECT COUNT(*) FROM audit").fetchone()[0] == 0:
        seed_audit = [
          ("NH44-MH-001-P-001","Case assigned for revenue verification","LAO",now()),
          ("NH44-MH-001-P-001","7/12 Extract verified","Revenue Officer",now()),
          ("NH44-MH-001-P-002","Revenue verification approved","Revenue Officer",now()),
          ("NH44-MH-001-P-003","Record mismatch detected","Revenue Officer",now())
        ]
        con.executemany("INSERT INTO audit(case_id,action,actor,created_at) VALUES(?,?,?,?)", seed_audit)
    if con.execute("SELECT COUNT(*) FROM issues").fetchone()[0] == 0:
        con.execute("INSERT INTO issues(case_id,issue_type,description,status,created_at) VALUES(?,?,?,?,?)",
                     ("NH44-MH-001-P-003","Encumbrance","Active mortgage found in revenue record. Further review required.","Open",now()))
    con.commit(); con.close()



def sync_shared(parcel_id, **data):
    import urllib.request, json as _json
    try:
        payload=_json.dumps({"project_id":"NH44-MH-001","parcel_id":parcel_id,"role":"revenue_officer",**data}).encode()
        req=urllib.request.Request("http://127.0.0.1:8090/api/shared/parcel/update",data=payload,headers={"Content-Type":"application/json"})
        urllib.request.urlopen(req,timeout=1).read()
    except Exception:
        pass


def log(con, case_id, action, actor="Revenue Officer"):
    con.execute("INSERT INTO audit(case_id,action,actor,created_at) VALUES(?,?,?,?)", (case_id, action, actor, now()))



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
    stats = {
      "total": con.execute("SELECT COUNT(*) FROM cases").fetchone()[0],
      "pending": con.execute("SELECT COUNT(*) FROM cases WHERE status='Pending Verification'").fetchone()[0],
      "verified": con.execute("SELECT COUNT(*) FROM cases WHERE status='Verified'").fetchone()[0],
      "issues": con.execute("SELECT COUNT(*) FROM cases WHERE status IN ('Record Mismatch','Rejected')").fetchone()[0]
    }
    cases=con.execute("SELECT * FROM cases ORDER BY id DESC").fetchall()
    con.close()
    return render_template("dashboard.html", stats=stats, cases=cases, active="dashboard")


@app.route("/cases")
def cases():
    con=db(); rows=con.execute("SELECT * FROM cases ORDER BY id DESC").fetchall(); con.close()
    return render_template("cases.html", cases=rows, active="cases")


@app.route("/gis")
def gis():
    selected_id = request.args.get("case_id", "NH44-MH-001-P-001")
    con=db()
    rows=con.execute("SELECT * FROM cases ORDER BY id DESC").fetchall()
    case=con.execute("SELECT * FROM cases WHERE case_id=?", (selected_id,)).fetchone()
    if not case:
        case=rows[0] if rows else None
    con.close()
    return render_template("gis.html", cases=rows, case=case, active="gis")


@app.route("/documents")
def documents():
    selected_id=request.args.get("case_id")
    con=db()
    cases_rows=con.execute("SELECT * FROM cases ORDER BY id DESC").fetchall()
    if not selected_id and cases_rows:
        selected_id=cases_rows[0]["case_id"]
    case=con.execute("SELECT * FROM cases WHERE case_id=?", (selected_id,)).fetchone() if selected_id else None
    docs=con.execute("SELECT * FROM documents WHERE case_id=? ORDER BY id", (selected_id,)).fetchall() if selected_id else []
    con.close()
    return render_template("documents.html", cases=cases_rows, case=case, docs=docs, active="documents")


@app.route("/case/<case_id>")
def case_detail(case_id):
    con=db()
    case=con.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
    docs=con.execute("SELECT * FROM documents WHERE case_id=?", (case_id,)).fetchall()
    audit=con.execute("SELECT * FROM audit WHERE case_id=? ORDER BY id DESC", (case_id,)).fetchall()
    issues=con.execute("SELECT * FROM issues WHERE case_id=? ORDER BY id DESC", (case_id,)).fetchall()
    con.close()
    if not case: return "Case not found", 404
    return render_template("case.html", case=case, docs=docs, audit=audit, issues=issues, active="cases")


@app.post("/case/<case_id>/verify")
def verify(case_id):
    con=db()
    con.execute("UPDATE cases SET status='Verified' WHERE case_id=?", (case_id,))
    log(con, case_id, "Revenue verification approved and case sent to LAO")
    con.commit(); con.close(); sync_shared(case_id.replace('NH44-MH-001-',''), status='Revenue Verified', revenue_status='Verified', workflow_status='Revenue Verified')
    flash("Case marked as Revenue Verified and sent to LAO.", "success")
    return redirect(url_for("case_detail", case_id=case_id))


@app.post("/case/<case_id>/flag")
def flag(case_id):
    issue_type=request.form.get("issue_type","Record Mismatch")
    desc=request.form.get("description","Verification issue flagged by Revenue Officer.")
    con=db()
    con.execute("UPDATE cases SET status='Record Mismatch' WHERE case_id=?", (case_id,))
    con.execute("INSERT INTO issues(case_id,issue_type,description,created_at) VALUES(?,?,?,?)", (case_id,issue_type,desc,now()))
    log(con, case_id, "Issue flagged and LAO notification created")
    con.commit(); con.close(); sync_shared(case_id.replace('NH44-MH-001-',''), status='Flagged', revenue_status='Flagged', workflow_status='Revenue Flagged')
    flash("Issue flagged. LAO has been notified.", "warning")
    return redirect(url_for("case_detail", case_id=case_id))


@app.post("/case/<case_id>/reject")
def reject(case_id):
    reason=request.form.get("description","Revenue verification failed.")
    con=db()
    con.execute("UPDATE cases SET status='Rejected' WHERE case_id=?", (case_id,))
    con.execute("INSERT INTO issues(case_id,issue_type,description,status,created_at) VALUES(?,?,?,?,?)", (case_id,"Verification Failed",reason,"Open",now()))
    log(con, case_id, "Case rejected during revenue verification")
    con.commit(); con.close(); sync_shared(case_id.replace('NH44-MH-001-',''), status='Rejected', revenue_status='Rejected', workflow_status='Revenue Rejected')
    flash("Case rejected and returned to workflow.", "danger")
    return redirect(url_for("case_detail", case_id=case_id))


@app.post("/case/<case_id>/document/<int:doc_id>")
def document(case_id, doc_id):
    status=request.form.get("status","Verified")
    con=db()
    con.execute("UPDATE documents SET status=? WHERE id=? AND case_id=?", (status,doc_id,case_id))
    log(con, case_id, f"Document updated: {status}")
    con.commit(); con.close()
    flash("Document status updated.", "success")
    return redirect(request.referrer or url_for("documents", case_id=case_id))


@app.post("/documents/<case_id>/bulk-verify")
def bulk_verify(case_id):
    con=db()
    con.execute("UPDATE documents SET status='Verified' WHERE case_id=?", (case_id,))
    log(con, case_id, "All case documents marked Verified")
    con.commit(); con.close()
    flash("All documents for this case are now verified.", "success")
    return redirect(url_for("documents", case_id=case_id))


@app.route("/notifications")
def notifications():
    con=db()
    issues=con.execute("""SELECT i.*, c.project, c.village FROM issues i
                          LEFT JOIN cases c ON c.case_id=i.case_id ORDER BY i.id DESC""").fetchall()
    recent=con.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 12").fetchall()
    con.close()
    return render_template("notifications.html", issues=issues, recent=recent, active="notifications")


@app.route("/audit")
def audit():
    con=db()
    rows=con.execute("""SELECT a.*, c.project FROM audit a
                       LEFT JOIN cases c ON c.case_id=a.case_id ORDER BY a.id DESC""").fetchall()
    con.close()
    return render_template("audit.html", rows=rows, active="audit")


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=int(__import__("os").environ.get("NLAMS_PORT", "5006")))
