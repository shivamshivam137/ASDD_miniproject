from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, send_file
import sqlite3, os, csv, io
from datetime import datetime
from functools import wraps

BASE=os.path.dirname(__file__); DB=os.path.join(BASE,'lao.db'); UP=os.path.join(BASE,'uploads'); os.makedirs(UP,exist_ok=True)
app=Flask(__name__); app.secret_key='NLAMS-LAO-FINAL-2026'

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def now(): return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def audit(action, entity, details):
    c=db(); c.execute('INSERT INTO audit(action,entity,details,at) VALUES(?,?,?,?)',(action,entity,details,now())); c.commit(); c.close()

def make_document(path, project_code, project_name, doc_name, description):
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        os.makedirs(os.path.dirname(path), exist_ok=True)
        pdf=canvas.Canvas(path,pagesize=A4); pdf.setTitle(doc_name)
        pdf.setFont('Helvetica-Bold',18); pdf.drawString(50,800,'NLAMS — Official Project Document')
        pdf.setFont('Helvetica',11); y=765
        for label,value in [('Project Code',project_code),('Project Name',project_name),('Document',doc_name),('Description',description),('Prepared For','Land Acquisition Officer'),('System','National Land Acquisition & Management System')]:
            pdf.drawString(50,y,f'{label}: {value}'); y-=28
        pdf.drawString(50,y,'This locally generated sample document is included for final-system workflow testing.')
        pdf.save()
    except Exception:
        open(path,'w',encoding='utf-8').write(f'{project_code}\n{project_name}\n{doc_name}\n{description}\n')

def init():
    c=db(); c.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE,password TEXT,name TEXT,role TEXT);
    CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY,code TEXT UNIQUE,name TEXT,agency TEXT,district TEXT,taluka TEXT,villages TEXT,area REAL,owners INTEGER,status TEXT,risk INTEGER,updated TEXT);
    CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY,project_id INTEGER,name TEXT,type TEXT,status TEXT,uploaded_by TEXT,uploaded TEXT,file_path TEXT,description TEXT);
    CREATE TABLE IF NOT EXISTS objections(id INTEGER PRIMARY KEY,project_id INTEGER,objector TEXT,survey TEXT,issue TEXT,hearing TEXT,status TEXT,decision TEXT);
    CREATE TABLE IF NOT EXISTS awards(id INTEGER PRIMARY KEY,project_id INTEGER,award_no TEXT,amount REAL,status TEXT,date TEXT);
    CREATE TABLE IF NOT EXISTS compensation(id INTEGER PRIMARY KEY,project_id INTEGER,assessed REAL,approved REAL,disbursed REAL,status TEXT);
    CREATE TABLE IF NOT EXISTS possession(id INTEGER PRIMARY KEY,project_id INTEGER,required REAL,taken REAL,status TEXT);
    CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY,project_id INTEGER,number TEXT,date TEXT,status TEXT,remarks TEXT);
    CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,action TEXT,entity TEXT,details TEXT,at TEXT);
    ''')
    if not c.execute('SELECT 1 FROM users').fetchone(): c.execute('INSERT INTO users(username,password,name,role) VALUES(?,?,?,?)',('lao','lao123','Land Acquisition Officer','LAO'))
    if not c.execute('SELECT 1 FROM projects').fetchone():
        statuses=['Pending Scrutiny']*4 + ['Land Verification']*4 + ['Approved']*5 + ['Notification Issued']*2 + ['Award Declared']*3 + ['Possession Pending']*4 + ['Acquisition Closed']*2
        detailed=[('NH-44 Expansion','NHAI','Pune','Haveli','Aundh, Baner',450,184,82),('Rail Corridor Phase II','Railways','Nashik','Nashik','Deolali, Sinnar',280,126,61),('Irrigation Modernisation','Water Resources','Satara','Karad','Umbraj, Masur',190,98,38),('Industrial Link Road','MIDC','Nagpur','Hingna','Hingna, Wanadongri',120,54,74)]
        for i,status in enumerate(statuses,1):
            if i<=4: name,agency,district,taluka,villages,area,owners,risk=detailed[i-1]
            else: name=f'NLAMS Infrastructure Project {i:02d}'; agency=['NHAI','Railways','Water Resources','MIDC'][i%4]; district=['Pune','Nashik','Satara','Nagpur'][i%4]; taluka=f'Taluka-{i}'; villages=f'Village-{i}A, Village-{i}B'; area=75+i*8; owners=35+i*3; risk=(i*17)%91
            code=f'NLAMS-2026-{i:03d}'; c.execute('INSERT INTO projects(code,name,agency,district,taluka,villages,area,owners,status,risk,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(code,name,agency,district,taluka,villages,area,owners,status,risk,now()))
        docs=[('DPR','PDF','Verified','Detailed project report / DPR'),('Land Requirement','PDF','Verified','Land requirement statement'),('Project Map','MAP','Verified','Project alignment map'),('Survey Record','PDF','Pending','Survey and measurement record'),('Administrative Approval','PDF','Verified','Administrative approval order')]
        for pid in range(1,25):
            project=c.execute('SELECT code,name FROM projects WHERE id=?',(pid,)).fetchone()
            for name,typ,st,desc in docs:
                if pid>4 and name=='Survey Record': st='Verified' if pid%3 else 'Pending'
                fname=f'{project[0]}_{name.replace(" ","_")}.pdf'; fpath=os.path.join(UP,fname); make_document(fpath,project[0],project[1],name,desc)
                c.execute('INSERT INTO documents(project_id,name,type,status,uploaded_by,uploaded,description,file_path) VALUES(?,?,?,?,?,?,?,?)',(pid,name,typ,st,'Project Agency',now(),desc,fpath))
        for i in range(1,12):
            pid=i if i<=11 else 1; c.execute('INSERT INTO awards(project_id,award_no,amount,status,date) VALUES(?,?,?,?,?)',(pid,f'AWD-2026-{i:03d}',50000000+i*750000,'Declared',f'2026-08-{10+(i%18):02d}'))
        for pid in range(1,25):
            required=c.execute('SELECT area FROM projects WHERE id=?',(pid,)).fetchone()['area']; taken=required if pid in [3,5,6,7,8,9,10] else round(required*(0.35+(pid%5)*0.08),2); status='Completed' if taken>=required else ('In Progress' if taken>0 else 'Pending'); c.execute('INSERT INTO possession(project_id,required,taken,status) VALUES(?,?,?,?)',(pid,required,taken,status))
        for pid in range(1,25):
            assessed=100000000+pid*5000000; approved=assessed if pid%3 else assessed*0.8; disbursed=approved if pid%5==0 else approved*0.82; status='Fully Disbursed' if disbursed>=approved else ('Partially Disbursed' if disbursed>0 else 'Pending'); c.execute('INSERT INTO compensation(project_id,assessed,approved,disbursed,status) VALUES(?,?,?,?,?)',(pid,assessed,approved,disbursed,status))
        for i in range(1,6): c.execute('INSERT INTO objections(project_id,objector,survey,issue,hearing,status) VALUES(?,?,?,?,?,?)',(i,f'Landowner {i}',f'{100+i}/4','Compensation / boundary objection',f'2026-09-{20+i:02d}', 'Pending' if i<3 else ('Hearing' if i<5 else 'Resolved')))
        for r in [(1,'NTF-2026-021','2026-06-12','Issued','Statutory notification issued'),(3,'NTF-2026-022','2026-07-18','Published','Published for affected villages')]: c.execute('INSERT INTO notifications(project_id,number,date,status,remarks) VALUES(?,?,?,?,?)',r)
    c.commit(); c.close()

def login_required(f):
    @wraps(f)
    def w(*a,**k):
        if not session.get('user'): return redirect(url_for('login', next=request.path))
        return f(*a,**k)
    return w

@app.context_processor
def ctx(): return {'role':'LAO','user':session.get('user')}


@app.after_request
def _nlams_security_headers(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='SAMEORIGIN'
    response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    response.headers['Permissions-Policy']='geolocation=(self), camera=(), microphone=()'
    response.headers['Cache-Control']='no-store'
    return response

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        c=db(); u=c.execute('SELECT * FROM users WHERE username=? AND password=?',(request.form.get('username'),request.form.get('password'))).fetchone(); c.close()
        if u:
            session.clear(); session['user']=u['name']; audit('Login','Authentication',u['username']); return redirect(request.args.get('next') or url_for('dashboard'))
        flash('Invalid username or password.','danger')
    return render_template('login.html')

@app.route('/logout')
def logout(): audit('Logout','Authentication',session.get('user','Unknown')); session.clear(); return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    c=db(); projects=c.execute('SELECT * FROM projects ORDER BY id DESC').fetchall(); k={
        'total':c.execute('SELECT COUNT(*) n FROM projects').fetchone()['n'],
        'pending':c.execute("SELECT COUNT(*) n FROM projects WHERE status IN ('Pending Scrutiny','Land Verification','Returned for Correction')").fetchone()['n'],
        'awards':c.execute("SELECT COUNT(*) n FROM awards WHERE status='Declared'").fetchone()['n'],
        'possession':c.execute("SELECT COUNT(*) n FROM possession WHERE status!='Completed'").fetchone()['n'],
        'comp_pending':c.execute('SELECT COUNT(*) n FROM compensation WHERE approved>disbursed').fetchone()['n']}; c.close()
    return render_template('dashboard.html',projects=projects,k=k)

@app.route('/projects')
@login_required
def projects():
    q=request.args.get('q','').strip(); c=db(); rows=c.execute('SELECT * FROM projects WHERE code LIKE ? OR name LIKE ? OR district LIKE ? ORDER BY id DESC',(f'%{q}%',f'%{q}%',f'%{q}%')).fetchall(); c.close(); return render_template('projects.html',projects=rows,q=q)

@app.route('/project/<int:pid>')
@login_required
def project(pid):
    c=db(); p=c.execute('SELECT * FROM projects WHERE id=?',(pid,)).fetchone()
    if not p: c.close(); flash('Project not found.','danger'); return redirect(url_for('projects'))
    docs=c.execute('SELECT * FROM documents WHERE project_id=? ORDER BY id',(pid,)).fetchall(); ob=c.execute('SELECT * FROM objections WHERE project_id=?',(pid,)).fetchall(); awards=c.execute('SELECT * FROM awards WHERE project_id=?',(pid,)).fetchall(); comp=c.execute('SELECT * FROM compensation WHERE project_id=?',(pid,)).fetchone(); poss=c.execute('SELECT * FROM possession WHERE project_id=?',(pid,)).fetchone(); notes=c.execute('SELECT * FROM notifications WHERE project_id=?',(pid,)).fetchall(); c.close()
    return render_template('project.html',p=p,docs=docs,ob=ob,awards=awards,comp=comp,poss=poss,notes=notes)

@app.route('/decision/<int:pid>/<action>',methods=['POST'])
@login_required
def decision(pid,action):
    status={'approve':'Approved','return':'Returned for Correction','reject':'Rejected'}.get(action)
    if not status: return redirect(url_for('project',pid=pid))
    reason=request.form.get('reason','').strip()
    if action in ('return','reject') and not reason: flash('A reason is required for Return or Reject.','danger'); return redirect(url_for('project',pid=pid))
    c=db(); c.execute('UPDATE projects SET status=?,updated=? WHERE id=?',(status,now(),pid)); c.commit(); c.close(); audit(action.upper(),'Project',f'Project {pid}; {reason or "Approved after scrutiny"}'); flash(f'Project marked {status}.','success'); return redirect(url_for('project',pid=pid))

@app.route('/scrutiny')
@login_required
def scrutiny():
    c=db(); rows=c.execute("SELECT * FROM projects WHERE status IN ('Pending Scrutiny','Returned for Correction') ORDER BY risk DESC").fetchall(); c.close(); return render_template('list.html',title='Project Scrutiny',subtitle='Review proposals and record statutory decisions.',projects=rows,action='scrutiny')

@app.route('/land')
@login_required
def land():
    c=db(); rows=c.execute('SELECT p.*, COUNT(d.id) document_count, SUM(CASE WHEN d.status="Pending" THEN 1 ELSE 0 END) pending_docs FROM projects p LEFT JOIN documents d ON p.id=d.project_id GROUP BY p.id ORDER BY p.id DESC').fetchall(); c.close(); return render_template('land.html',rows=rows)

@app.route('/land/<int:pid>')
@login_required
def land_project(pid): return redirect(url_for('project',pid=pid)+'#documents')

@app.route('/doc/<int:did>/<action>',methods=['POST'])
@login_required
def doc(did,action):
    st={'verify':'Verified','reject':'Rejected'}.get(action)
    if st:
        c=db(); d=c.execute('SELECT * FROM documents WHERE id=?',(did,)).fetchone();
        if d: c.execute('UPDATE documents SET status=? WHERE id=?',(st,did)); c.commit(); audit(action.upper(),'Document',f'{d["name"]} for project {d["project_id"]}')
        c.close(); flash(f'Document {st}.','success')
    return redirect(request.referrer or url_for('land'))

@app.route('/doc/<int:did>/view')
@login_required
def doc_view(did):
    c=db(); d=c.execute('SELECT d.*,p.code,p.name FROM documents d JOIN projects p ON p.id=d.project_id WHERE d.id=?',(did,)).fetchone(); c.close()
    if not d: flash('Document not found.','danger'); return redirect(url_for('land'))
    return render_template('document_view.html',d=d)

@app.route('/doc/<int:did>/file')
@login_required
def doc_file(did):
    c=db(); d=c.execute('SELECT file_path,name FROM documents WHERE id=?',(did,)).fetchone(); c.close()
    if not d or not d['file_path'] or not os.path.exists(d['file_path']): flash('Original file is not available.','danger'); return redirect(url_for('doc_view',did=did))
    audit('Document Viewed','Document',str(did)); return send_file(d['file_path'],mimetype='application/pdf',as_attachment=False,download_name=d['name'].replace(' ','_')+'.pdf')

@app.route('/notifications',methods=['GET','POST'])
@login_required
def notifications():
    c=db()
    if request.method=='POST':
        pid=request.form['project_id']; number=request.form['number']; date=request.form['date']; status=request.form['status']; remarks=request.form.get('remarks',''); c.execute('INSERT INTO notifications(project_id,number,date,status,remarks) VALUES(?,?,?,?,?)',(pid,number,date,status,remarks)); c.commit(); audit('Notification Created','Notification',number); flash('Notification saved successfully.','success')
    rows=c.execute('SELECT n.*,p.code,p.name FROM notifications n JOIN projects p ON p.id=n.project_id ORDER BY n.id DESC').fetchall(); projects=c.execute('SELECT * FROM projects ORDER BY code').fetchall(); c.close(); return render_template('notifications.html',rows=rows,projects=projects)

@app.route('/objections',methods=['GET','POST'])
@login_required
def objections():
    c=db()
    if request.method=='POST':
        c.execute('UPDATE objections SET hearing=?,decision=?,status=? WHERE id=?',(request.form['hearing'],request.form.get('decision',''),request.form['status'],request.form['id'])); c.commit(); audit('Hearing Updated','Objection',request.form['id']); flash('Hearing/decision saved.','success')
    rows=c.execute('SELECT o.*,p.code FROM objections o JOIN projects p ON p.id=o.project_id ORDER BY o.id DESC').fetchall(); c.close(); return render_template('objections.html',rows=rows)

@app.route('/awards')
@login_required
def awards():
    c=db(); rows=c.execute('SELECT a.*,p.code,p.name FROM awards a JOIN projects p ON p.id=a.project_id ORDER BY a.id DESC').fetchall(); c.close(); return render_template('awards.html',rows=rows)

@app.route('/compensation')
@login_required
def compensation():
    c=db(); rows=c.execute('SELECT c.*,p.code,p.name FROM compensation c JOIN projects p ON p.id=c.project_id ORDER BY c.id DESC').fetchall(); c.close(); return render_template('compensation.html',rows=rows)

@app.route('/compensation/<int:cid>',methods=['POST'])
@login_required
def comp_update(cid):
    try: approved=float(request.form['approved']); disbursed=float(request.form['disbursed'])
    except ValueError: flash('Enter valid compensation amounts.','danger'); return redirect(url_for('compensation'))
    c=db(); r=c.execute('SELECT assessed FROM compensation WHERE id=?',(cid,)).fetchone();
    if not r: c.close(); flash('Compensation record not found.','danger'); return redirect(url_for('compensation'))
    if approved<0 or disbursed<0 or approved>r['assessed'] or disbursed>approved: c.close(); flash('Invalid amounts: Disbursed ≤ Approved ≤ Assessed.','danger'); return redirect(url_for('compensation'))
    c.execute('UPDATE compensation SET approved=?,disbursed=?,status=? WHERE id=?',(approved,disbursed,request.form['status'],cid)); c.commit(); c.close(); audit('Compensation Updated','Compensation',str(cid)); flash('Compensation status updated.','success'); return redirect(url_for('compensation'))

@app.route('/possession')
@login_required
def possession():
    c=db(); rows=c.execute('SELECT ps.*,p.code,p.name FROM possession ps JOIN projects p ON p.id=ps.project_id ORDER BY ps.id DESC').fetchall(); c.close(); return render_template('possession.html',rows=rows)

@app.route('/possession/<int:pid>',methods=['POST'])
@login_required
def possession_update(pid):
    try: taken=float(request.form['taken'])
    except ValueError: flash('Enter a valid area.','danger'); return redirect(url_for('possession'))
    c=db(); r=c.execute('SELECT required FROM possession WHERE id=?',(pid,)).fetchone();
    if not r or taken<0 or taken>r['required']: c.close(); flash('Possession area must be between 0 and required area.','danger'); return redirect(url_for('possession'))
    status=request.form['status']; c.execute('UPDATE possession SET taken=?,status=? WHERE id=?',(taken,status,pid)); c.commit(); c.close(); audit('Possession Updated','Possession',str(pid)); flash('Possession record updated.','success'); return redirect(url_for('possession'))

@app.route('/reports')
@login_required
def reports():
    c=db(); stats=c.execute('SELECT status,COUNT(*) n FROM projects GROUP BY status ORDER BY n DESC').fetchall(); comp=c.execute('SELECT COALESCE(SUM(assessed),0) a,COALESCE(SUM(approved),0) ap,COALESCE(SUM(disbursed),0) d FROM compensation').fetchone(); doc=c.execute('SELECT COUNT(*) total,SUM(CASE WHEN status="Verified" THEN 1 ELSE 0 END) verified,SUM(CASE WHEN status="Pending" THEN 1 ELSE 0 END) pending FROM documents').fetchone(); obj=c.execute('SELECT status,COUNT(*) n FROM objections GROUP BY status').fetchall(); c.close(); return render_template('reports.html',stats=stats,comp=comp,doc=doc,obj=obj)

@app.route('/reports/export')
@login_required
def export():
    c=db(); rows=c.execute('SELECT code,name,agency,district,area,owners,status,risk,updated FROM projects ORDER BY id').fetchall(); c.close(); out=io.StringIO(); w=csv.writer(out); w.writerow(rows[0].keys() if rows else ['Project']); [w.writerow(list(r)) for r in rows]; audit('Report Exported','MIS','Projects CSV'); return Response(out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=nlams_lao_projects.csv'})

@app.route('/ai')
@login_required
def ai():
    c=db(); rows=c.execute('SELECT * FROM projects ORDER BY risk DESC').fetchall(); c.close(); return render_template('ai.html',projects=rows)
@app.route('/audit')
@login_required
def audit_page():
    c=db(); rows=c.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 100').fetchall(); c.close(); return render_template('audit.html',rows=rows)

init()
if __name__=='__main__': app.run(port=int(__import__("os").environ.get("NLAMS_PORT", "5004")),debug=True)
