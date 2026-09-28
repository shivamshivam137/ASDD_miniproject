# NLAMS Advanced Pro Portal
Built from the supplied 8-panel reference image as a functional original implementation.

## Stack
HTML5 + CSS3 + Vanilla JavaScript + Python Flask + SQLite SQL.

## Included modules
1. Admin Dashboard Overview
2. GIS National Command Map
3. Risk & Delay Radar + SLA/Escalation
4. Smart Workflow Recommendation + Case Timeline
5. Duplicate & Conflict Detection + Document Integrity
6. Officer Workload Balancer + What-if Simulator
7. AI Assistant + Audit Logs + Project Analytics
8. Notifications + System Settings + Live Monitoring
Plus Project Monitoring, Grievance Management, Reports, User Management, Roles, District Management.

## Run in VS Code
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

Demo administrator:
- username: `admin`
- password: `admin123`

Other seeded users:
- `amit.k`, `neha.p`, `rahul.d`, `priya.s`
- password: `password123`

The SQLite database `nlams.db` is generated automatically.

## Notes
The GIS screen is a local interactive visualization with clickable project pins so it works without requiring a mapping API key. For production, replace the map layer with Leaflet/MapLibre and a permitted tile provider if desired.
