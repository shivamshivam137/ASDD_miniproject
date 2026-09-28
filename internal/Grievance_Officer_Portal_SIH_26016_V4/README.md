# NLAMS SIH 26016 — Grievance Officer Portal V4

## Purpose
Officer-only grievance management module for the National Land Acquisition & Management System.

## Login
- URL: http://127.0.0.1:5002
- Email: officer@nlams.demo
- Password: officer123

## Run on Windows
```bat
pip install -r requirements.txt
python app.py
```
Or double-click `start.bat`.

## V4 View Details flow
1. Login as Grievance Officer.
2. Open **All Grievances** from the sidebar.
3. Click the blue **View** button for any grievance.
4. The case view shows Complaint Details, Landowner Profile, Project & Affected Land, Compensation, Documents, Status Timeline, SLA and Officer Action.
5. Saving an officer action updates the grievance, timeline and audit record.

The View Details layout is intentionally based on the supplied screenshot: complaint information on the left and status timeline / Take Action on the right, with the complete landowner and project record below.

## Demo records
The database is seeded automatically with multiple landowners, projects, parcels and grievances on first run.
