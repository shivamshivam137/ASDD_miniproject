
# NLAMS Advanced Project Agency Portal

A functional Flask + SQLite prototype based on the supplied NLAMS Project Agency workflow/screens.

## Included working modules
- Project Agency dashboard
- Create New Project with automatic Project ID
- My Projects search/filter
- Project detail workspace + lifecycle workflow
- Land Requirement + interactive demo GIS parcel map
- Add parcels and parcel register
- Document Management with file upload, validation and verification state
- Compensation assessment/payment workflow
- R&R family management
- Grievance registration + resolution
- Reports & MIS CSV exports
- AI Risk & Delay Analysis (explainable rule-based prototype)
- Notifications and escalation demo
- SQLite database with realistic synthetic demo data
- Audit trail
- Responsive UI

## Run
1. Install Python 3.10+
2. Open terminal in this folder
3. `python -m venv .venv`
4. Windows: `.venv\Scripts\activate`
5. `pip install -r requirements.txt`
6. `python app.py`
7. Open `http://127.0.0.1:5000`

The SQLite database is created automatically on first run.

## Demo data note
The data is synthetic demonstration data. It is structured to resemble the supplied prototype (e.g. NH-44 Expansion, Maharashtra, Pimpalgaon/Khalapur/Nerul, compensation and R&R cases) and is not an authoritative government dataset.

## Production upgrade path
- Replace demo GIS layer with authoritative cadastral/GIS APIs.
- Add real authentication, RBAC, MFA/OTP and session management.
- Store documents in encrypted object storage.
- Integrate state land records, registration, PFMS/payment and notification gateways through approved APIs.
- Add immutable audit logging and formal retention policies.
- Replace rule-based risk scoring with validated, explainable ML after collecting historical project outcomes.


## UI workflow fixes in this updated build

- Documents: uploading only queues the document and shows its current Action Status. Verification/action controls are not shown in the Project Agency portal; Admin handles verification.
- Compensation: each compensation record now has a View option for its full details. Disbursement controls are not shown in this portal; Admin handles payment/disbursement.
- R&R: every row has a working Update Status control. Current status is pre-selected, progress is validated from 0–100%, Pending resets to 0%, and Completed sets progress to 100%. Updates are recorded in the audit trail.
- Grievance: this portal is now display-only. It shows only grievance updates/status received from the separate Grievance Management section. Register/Resolve controls were removed from this page.
