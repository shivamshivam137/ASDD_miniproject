# NLAMS Final Submission — Separate LAO + R&R Officer Portals

This package contains two independent Flask + SQLite portals. There is no role-switch button.

## LAO
Folder: `LAO`
URL: http://127.0.0.1:5000
Login: `lao` / `lao123`

Modules: Dashboard, Projects, Scrutiny, Land & Documents, Notifications, Objections/Hearing, Awards, Compensation, Possession, AI Insights, Reports & MIS, Audit Trail.

Project Review includes a visible Document Verification section. Every seeded document has a View Document page and Verify/Reject actions. Land & Documents is fully linked to project review. Reports & MIS has live statistics, CSV export and print.

## R&R
Folder: `RR`
URL: http://127.0.0.1:5001
Login: `rro` / `rro123`

Modules: Dashboard, Affected Families, Create R&R Family, Eligibility, Benefits, Rehabilitation/Resettlement, Field Verification, Grievance/Issues, R&R Completion, Project Closure, AI Insights, Reports & MIS, Audit Trail.

Create R&R Family captures Family ID, head, village, district, members, affected area, displacement, eligibility, risk, contact, address, documents and officer notes. The new family immediately enters the R&R workflow.

## Run

LAO:
```
cd LAO
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

R&R in another terminal:
```
cd RR
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5001

The SQLite databases are created automatically on first run.
