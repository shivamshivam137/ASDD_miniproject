# NLAMS Data Connectivity - Final Fix

This package keeps the existing portal UI, roles and features. The fix is limited to persistence and cross-portal synchronization.

## Run

1. Extract the ZIP.
2. Double-click `START_ALL_NLAMS.bat`.
3. Open `http://127.0.0.1:8000`.

## Verify the real cross-portal grievance flow

1. Landowner Portal -> My Grievances -> Submit New Grievance.
2. Note the generated ticket, e.g. `GRV-20260908-XXXXX`.
3. Open Grievance Officer Portal and refresh Command Center / All Grievances.
4. The exact ticket, subject and description are pulled from the shared NLAMS Integration Service and appear in the existing Grievance Officer UI.
5. Open the ticket and use the existing Save Officer Action button.
6. The action is written to the local officer database and the shared workflow database.
7. The central workflow changes `current_role` and records a workflow event.
8. Open the next role portal (LAO for the connected grievance route). Its existing Connected NLAMS Workflow panel reads the same central workflow record.
9. Use Forward / Approve / Return from that panel. The next-role assignment changes in the same shared record.

## Shared services

- Integration API: `http://127.0.0.1:8090/api/health`
- Shared SQLite store: `integration/nlams_integration.db` (created automatically on first run)
- Existing portal databases remain local to their portals; the integration service is the authoritative cross-portal workflow layer.

## GIS

Survey/GIS continues to use the existing portal. Browser geolocation is stored in the shared integration service when the existing location capture workflow runs. Other portals can consume the shared location records without changing their existing UI.

## Important

Do not delete or rename existing role portals. Do not change role names or existing screens. This release is specifically for frontend/backend persistence and cross-portal data synchronization.
