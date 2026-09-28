from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
import sqlite3, os, csv, io
from datetime import datetime
from functools import wraps
BASE=os.path.dirname(__file__); DB=os.path.join(BASE,'rr.db'); app=Flask(__name__); app.secret_key='NLAMS-RR-FINAL-2026'
def db(): c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def now(): return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
def audit(action,entity,details): c=db(); c.execute('INSERT INTO audit(action,entity,details,at) VALUES(?,?,?,?)',(action,entity,details,now())); c.commit(); c.close()
def init():
 c=db(); c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE,password TEXT,name TEXT,role TEXT);
 CREATE TABLE IF NOT EXISTS families(id INTEGER PRIMARY KEY,code TEXT UNIQUE,head TEXT,village TEXT,district TEXT,members INTEGER,affected_area REAL,displacement TEXT,eligibility TEXT,rr_status TEXT,risk INTEGER,phone TEXT,address TEXT,documents TEXT,notes TEXT);
 CREATE TABLE IF NOT EXISTS benefits(id INTEGER PRIMARY KEY,family_id INTEGER,category TEXT,amount REAL,status TEXT,allocated_date TEXT,remarks TEXT);
 CREATE TABLE IF NOT EXISTS field_visits(id INTEGER PRIMARY KEY,family_id INTEGER,officer TEXT,date TEXT,observation TEXT,status TEXT,gps TEXT);
 CREATE TABLE IF NOT EXISTS issues(id INTEGER PRIMARY KEY,family_id INTEGER,category TEXT,description TEXT,priority TEXT,status TEXT,opened TEXT,resolved TEXT);
 CREATE TABLE IF NOT EXISTS rr_plans(id INTEGER PRIMARY KEY,family_id INTEGER,housing REAL,plot TEXT,employment TEXT,training TEXT,location TEXT,completion TEXT,status TEXT,remarks TEXT);
 CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,action TEXT,entity TEXT,details TEXT,at TEXT);''')
 if not c.execute('SELECT 1 FROM users').fetchone(): c.execute('INSERT INTO users(username,password,name,role) VALUES(?,?,?,?)',('rro','rro123','R&R Officer','R&R'))
 if not c.execute('SELECT 1 FROM families').fetchone():
  # Seed a realistic operational register matching the dashboard KPIs.
  detailed=[('Mahesh Patil','Aundh','Pune',5,2.4,'Yes','Eligible','Completed',72),('Sunita More','Baner','Pune',4,1.8,'Yes','Under Review','Pending',88),('Rahul Jadhav','Wakad','Pune',6,3.1,'Yes','Eligible','Completed',24),('Kiran Shinde','Sinnar','Nashik',3,1.1,'No','Not Eligible','Not Started',35)]
  for i in range(1,1843):
   if i<=4: head,village,district,members,area,disp,elig,status,risk=detailed[i-1]
   else:
    head=f'Family Head {i:04d}'; village=f'Village-{(i%80)+1:02d}'; district=['Pune','Nashik','Satara','Nagpur'][i%4]; members=3+(i%5); area=round(0.6+(i%40)*0.08,2); disp='Yes' if i<=732 else ('Yes' if i%7==0 else 'No'); elig='Under Review' if i<=124 else ('Eligible' if i%10 else 'Not Eligible'); status='Completed' if i<=1253 else ('In Progress' if i<=1600 else 'Pending'); risk=(i*13)%96
   code=f'AF-{2026}-{i:04d}'; phone=f'98{70000000+i%10000000:08d}'; c.execute('INSERT INTO families(code,head,village,district,members,affected_area,displacement,eligibility,rr_status,risk,phone,address,documents,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(code,head,village,district,members,area,disp,elig,status,risk,phone,f'{village}, {district}','Identity; Land Record; Displacement Proof','R&R case record'))
  # Core benefit records for the first operational families.
  for r in [(1,'Housing Assistance',500000,'Allocated','2026-08-01','Housing sanctioned'),(1,'Plot Allocation',0,'Completed','2026-08-15','Plot handed over'),(2,'Housing Assistance',500000,'Pending','2026-09-01','Awaiting verification'),(3,'Housing Assistance',500000,'Paid','2026-07-10','Paid'),(3,'Employment Support',0,'Completed','2026-07-20','Employment linked')]: c.execute('INSERT INTO benefits(family_id,category,amount,status,allocated_date,remarks) VALUES(?,?,?,?,?,?)',r)
  for r in [(1,'Field Officer','2026-09-08','Housing and relocation verified','Verified','18.534,73.824'),(2,'Field Officer','2026-09-10','Benefit delivery pending','Scheduled','18.560,73.780'),(3,'Field Officer','2026-09-05','Resettlement completed','Verified','18.520,73.830')]: c.execute('INSERT INTO field_visits(family_id,officer,date,observation,status,gps) VALUES(?,?,?,?,?,?)',r)
  for i in range(1,57): c.execute('INSERT INTO issues(family_id,category,description,priority,status,opened) VALUES(?,?,?,?,?,?)',(i,'Housing' if i%2 else 'Benefit','Pending family support issue','High' if i%3==0 else 'Medium','Open',datetime.now().strftime('%Y-%m-%d')))
  c.execute('INSERT INTO issues(family_id,category,description,priority,status,opened) VALUES(?,?,?,?,?,?)',(57,'Documentation','Minor record correction','Low','Resolved',datetime.now().strftime('%Y-%m-%d')))
  for r in [(1,500000,'Allocated','Skill training','Agricultural skill','Aundh R&R Site','2026-10-15','In Progress','Pending final field check'),(2,500000,'Pending','Employment counselling','Training pending','Baner R&R Site','2026-11-10','Draft','Eligibility review required'),(3,500000,'Allocated','Job provided','Completed','Wakad R&R Site','2026-08-30','Completed','All required activities completed')]: c.execute('INSERT INTO rr_plans(family_id,housing,plot,employment,training,location,completion,status,remarks) VALUES(?,?,?,?,?,?,?,?,?)',r)
 c.commit(); c.close()
def login_required(f):
 @wraps(f)
 def w(*a,**k):
  if not session.get('user'): return redirect(url_for('login',next=request.path))
  return f(*a,**k)
 return w
@app.context_processor
def ctx(): return {'role':'R&R','user':session.get('user')}

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
  if u: session.clear(); session['user']=u['name']; audit('Login','Authentication',u['username']); return redirect(request.args.get('next') or url_for('dashboard'))
  flash('Invalid username or password.','danger')
 return render_template('login.html')
@app.route('/logout')
def logout(): audit('Logout','Authentication',session.get('user','Unknown')); session.clear(); return redirect(url_for('login'))
@app.route('/')
@login_required
def dashboard():
 c=db(); families=c.execute('SELECT * FROM families ORDER BY id DESC').fetchall(); k={'affected':c.execute('SELECT COUNT(*) n FROM families').fetchone()['n'],'displaced':c.execute("SELECT COUNT(*) n FROM families WHERE displacement='Yes'").fetchone()['n'],'pending':c.execute("SELECT COUNT(*) n FROM families WHERE eligibility='Under Review'").fetchone()['n'],'issues':c.execute("SELECT COUNT(*) n FROM issues WHERE status='Open'").fetchone()['n'],'completed':c.execute("SELECT COUNT(*) n FROM families WHERE rr_status='Completed'").fetchone()['n']}; total=k['affected']; k['progress']=round((k['completed']/total)*100) if total else 0; c.close(); return render_template('dashboard.html',families=families,k=k)
@app.route('/families')
@login_required
def families():
 q=request.args.get('q','').strip(); c=db(); rows=c.execute('SELECT * FROM families WHERE code LIKE ? OR head LIKE ? OR village LIKE ? OR district LIKE ? ORDER BY id DESC',(f'%{q}%',f'%{q}%',f'%{q}%',f'%{q}%')).fetchall(); c.close(); return render_template('families.html',families=rows,q=q)
@app.route('/families/new',methods=['GET','POST'])
@login_required
def family_new():
 if request.method=='POST':
  data=[request.form.get('code','').strip(),request.form.get('head','').strip(),request.form.get('village','').strip(),request.form.get('district','').strip(),int(request.form.get('members') or 0),float(request.form.get('affected_area') or 0),request.form.get('displacement','No'),request.form.get('eligibility','Under Review'),'Not Started',int(request.form.get('risk') or 0),request.form.get('phone','').strip(),request.form.get('address','').strip(),request.form.get('documents','').strip(),request.form.get('notes','').strip()]
  if not data[0] or not data[1] or not data[2] or not data[3]: flash('Family ID, head of family, village and district are required.','danger'); return render_template('family_new.html')
  c=db()
  try: c.execute('INSERT INTO families(code,head,village,district,members,affected_area,displacement,eligibility,rr_status,risk,phone,address,documents,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',data); c.commit(); fid=c.execute('SELECT last_insert_rowid() id').fetchone()['id']; c.close(); audit('Family Created','Family',data[0]); flash('Affected family created successfully.','success'); return redirect(url_for('family',fid=fid))
  except sqlite3.IntegrityError: c.close(); flash('Family ID already exists.','danger')
 return render_template('family_new.html')
@app.route('/family/<int:fid>')
@login_required
def family(fid):
 c=db(); f=c.execute('SELECT * FROM families WHERE id=?',(fid,)).fetchone()
 if not f: c.close(); flash('Family not found.','danger'); return redirect(url_for('families'))
 b=c.execute('SELECT * FROM benefits WHERE family_id=? ORDER BY id DESC',(fid,)).fetchall(); v=c.execute('SELECT * FROM field_visits WHERE family_id=? ORDER BY id DESC',(fid,)).fetchall(); i=c.execute('SELECT * FROM issues WHERE family_id=? ORDER BY id DESC',(fid,)).fetchall(); p=c.execute('SELECT * FROM rr_plans WHERE family_id=? ORDER BY id DESC',(fid,)).fetchone(); c.close(); return render_template('family.html',f=f,benefits=b,visits=v,issues=i,plan=p)
@app.route('/eligibility')
@login_required
def eligibility():
 c=db(); rows=c.execute("SELECT * FROM families WHERE eligibility!='Eligible' ORDER BY risk DESC").fetchall(); c.close(); return render_template('eligibility.html',families=rows)
@app.route('/eligibility/<int:fid>',methods=['POST'])
@login_required
def eligibility_update(fid):
 st=request.form['eligibility']; c=db(); c.execute('UPDATE families SET eligibility=? WHERE id=?',(st,fid)); c.commit(); c.close(); audit('Eligibility Updated','Family',f'{fid}: {st}'); flash('Eligibility updated.','success'); return redirect(url_for('eligibility'))
@app.route('/benefits',methods=['GET','POST'])
@login_required
def benefits():
 c=db()
 if request.method=='POST':
  c.execute('INSERT INTO benefits(family_id,category,amount,status,allocated_date,remarks) VALUES(?,?,?,?,?,?)',(request.form['family_id'],request.form['category'],float(request.form.get('amount') or 0),request.form['status'],datetime.now().strftime('%Y-%m-%d'),request.form.get('remarks',''))); c.commit(); audit('Benefit Created','Benefit',request.form['category']); flash('Benefit allocated successfully.','success')
 rows=c.execute('SELECT b.*,f.code,f.head FROM benefits b JOIN families f ON f.id=b.family_id ORDER BY b.id DESC').fetchall(); families=c.execute('SELECT * FROM families WHERE eligibility="Eligible"').fetchall(); c.close(); return render_template('benefits.html',rows=rows,families=families)
@app.route('/benefits/<int:bid>',methods=['POST'])
@login_required
def benefit_update(bid):
 c=db(); c.execute('UPDATE benefits SET amount=?,status=?,remarks=? WHERE id=?',(float(request.form.get('amount') or 0),request.form['status'],request.form.get('remarks',''),bid)); c.commit(); c.close(); audit('Benefit Updated','Benefit',str(bid)); flash('Benefit record updated.','success'); return redirect(url_for('benefits'))
@app.route('/resettlement',methods=['GET','POST'])
@login_required
def resettlement():
 c=db()
 if request.method=='POST':
  fid=request.form['family_id']; existing=c.execute('SELECT id FROM rr_plans WHERE family_id=?',(fid,)).fetchone(); vals=(float(request.form.get('housing') or 0),request.form.get('plot',''),request.form.get('employment',''),request.form.get('training',''),request.form.get('location',''),request.form.get('completion',''),request.form['status'],request.form.get('remarks',''))
  if existing: c.execute('UPDATE rr_plans SET housing=?,plot=?,employment=?,training=?,location=?,completion=?,status=?,remarks=? WHERE id=?',(*vals,existing['id']))
  else: c.execute('INSERT INTO rr_plans(family_id,housing,plot,employment,training,location,completion,status,remarks) VALUES(?,?,?,?,?,?,?,?,?)',(fid,*vals))
  c.execute('UPDATE families SET rr_status=? WHERE id=?',(request.form['status'],fid)); c.commit(); audit('R&R Plan Saved','Family',fid); flash('R&R plan saved successfully.','success')
 rows=c.execute('SELECT p.*,f.code,f.head FROM rr_plans p JOIN families f ON f.id=p.family_id ORDER BY p.id DESC').fetchall(); families=c.execute('SELECT * FROM families WHERE eligibility="Eligible"').fetchall(); c.close(); return render_template('resettlement.html',rows=rows,families=families)
@app.route('/field',methods=['GET','POST'])
@login_required
def field():
 c=db()
 if request.method=='POST': c.execute('INSERT INTO field_visits(family_id,officer,date,observation,status,gps) VALUES(?,?,?,?,?,?)',(request.form['family_id'],request.form['officer'],request.form['date'],request.form['observation'],request.form['status'],request.form.get('gps',''))); c.commit(); audit('Field Visit Submitted','Family',request.form['family_id']); flash('Field verification saved.','success')
 families=c.execute('SELECT * FROM families').fetchall(); visits=c.execute('SELECT v.*,f.code,f.head FROM field_visits v JOIN families f ON f.id=v.family_id ORDER BY v.id DESC').fetchall(); c.close(); return render_template('field.html',families=families,visits=visits)
@app.route('/field/<int:vid>',methods=['POST'])
@login_required
def field_update(vid):
 c=db(); c.execute('UPDATE field_visits SET status=?,observation=?,gps=? WHERE id=?',(request.form['status'],request.form.get('observation',''),request.form.get('gps',''),vid)); c.commit(); c.close(); audit('Field Visit Updated','Visit',str(vid)); flash('Field verification status updated.','success'); return redirect(url_for('field'))
@app.route('/issues',methods=['GET','POST'])
@login_required
def issues():
 c=db()
 if request.method=='POST': c.execute('INSERT INTO issues(family_id,category,description,priority,status,opened) VALUES(?,?,?,?,?,?)',(request.form['family_id'],request.form['category'],request.form['description'],request.form['priority'],'Open',datetime.now().strftime('%Y-%m-%d'))); c.commit(); audit('Grievance Registered','Family',request.form['family_id']); flash('Issue registered.','success')
 rows=c.execute('SELECT i.*,f.code,f.head FROM issues i JOIN families f ON f.id=i.family_id ORDER BY i.id DESC').fetchall(); families=c.execute('SELECT * FROM families').fetchall(); c.close(); return render_template('issues.html',rows=rows,families=families)
@app.route('/issues/<int:iid>',methods=['POST'])
@login_required
def issue_update(iid):
 status=request.form['status']; c=db(); c.execute('UPDATE issues SET status=?,resolved=? WHERE id=?',(status,datetime.now().strftime('%Y-%m-%d') if status=='Resolved' else None,iid)); c.commit(); c.close(); audit('Issue Updated','Issue',str(iid)); flash('Issue status updated.','success'); return redirect(url_for('issues'))
@app.route('/completion')
@login_required
def completion():
 c=db(); rows=c.execute('SELECT f.*,COALESCE((SELECT COUNT(*) FROM issues i WHERE i.family_id=f.id AND i.status="Open"),0) open_issues,COALESCE((SELECT COUNT(*) FROM field_visits v WHERE v.family_id=f.id AND v.status="Verified"),0) verified_visits FROM families f ORDER BY id DESC').fetchall(); c.close(); return render_template('completion.html',families=rows)
@app.route('/closure/<int:fid>',methods=['POST'])
@login_required
def closure(fid):
 c=db(); open_issue=c.execute('SELECT COUNT(*) n FROM issues WHERE family_id=? AND status="Open"',(fid,)).fetchone()['n']; eligible=c.execute('SELECT eligibility FROM families WHERE id=?',(fid,)).fetchone();
 if open_issue or not eligible or eligible['eligibility']!='Eligible': c.close(); flash('Cannot close R&R: family must be eligible and have no open issues.','danger'); return redirect(url_for('completion'))
 c.execute('UPDATE families SET rr_status=? WHERE id=?',('Completed',fid)); c.commit(); c.close(); audit('R&R Completed','Family',str(fid)); flash('R&R marked completed and ready for project closure.','success'); return redirect(url_for('completion'))
@app.route('/reports')
@login_required
def reports():
 c=db(); elig=c.execute('SELECT eligibility,COUNT(*) n FROM families GROUP BY eligibility').fetchall(); benefit=c.execute('SELECT COALESCE(SUM(amount),0) a FROM benefits WHERE status IN ("Paid","Completed")').fetchone(); issue=c.execute('SELECT status,COUNT(*) n FROM issues GROUP BY status').fetchall(); rr=c.execute('SELECT rr_status,COUNT(*) n FROM families GROUP BY rr_status').fetchall(); c.close(); return render_template('reports.html',elig=elig,benefit=benefit,issue=issue,rr=rr)
@app.route('/reports/export')
@login_required
def export():
 c=db(); rows=c.execute('SELECT code,head,village,district,members,affected_area,displacement,eligibility,rr_status,risk,phone FROM families ORDER BY id').fetchall(); c.close(); out=io.StringIO(); w=csv.writer(out); w.writerow(rows[0].keys() if rows else ['Family']); [w.writerow(list(r)) for r in rows]; audit('Report Exported','MIS','Families CSV'); return Response(out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=nlams_rr_families.csv'})
@app.route('/ai')
@login_required
def ai(): c=db(); rows=c.execute('SELECT * FROM families ORDER BY risk DESC').fetchall(); c.close(); return render_template('ai.html',families=rows)
@app.route('/audit')
@login_required
def audit_page(): c=db(); rows=c.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 100').fetchall(); c.close(); return render_template('audit.html',rows=rows)
init()
if __name__=='__main__': app.run(port=int(__import__("os").environ.get("NLAMS_PORT", "5003")),debug=True)
