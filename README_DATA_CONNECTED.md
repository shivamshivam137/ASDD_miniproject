# NLAMS — Data Connectivity Fix

This build keeps the existing role portals, features and UI intact. The change is limited to the data/integration layer.

## What is fixed

- A persistent NLAMS Integration Service at `127.0.0.1:8090`.
- Central SQLite transaction/event store: `integration/nlams_integration.db`.
- Every portal's POST/PUT/PATCH/DELETE browser request is mirrored to the central store without replacing the original portal backend.
- Existing Landowner grievance submission and Survey/GIS GPS calls are connected to the same store.
- Survey/GIS field-survey data (GPS, measured area, land details, boundary, remarks, evidence metadata and document metadata) is persisted in the integration backend and reloaded by parcel.
- Workflow inboxes use the same central record so the receiving role can see the submitted transaction and forward/approve/return it.
- Workflow history records actor, from-role, to-role, action, note and timestamp.
- GIS locations are stored centrally with latitude, longitude, accuracy, timestamp, project and parcel IDs.

## Important design constraint

No existing role has been renamed or removed. No existing portal screen is intentionally redesigned. The integration service acts as a data/transaction bus around the existing applications.

## Run

Double-click `START_ALL_NLAMS.bat`.

Gateway: `http://127.0.0.1:8000`
Integration API: `http://127.0.0.1:8090/api/health`
Survey/GIS: `http://127.0.0.1:5173`

## Example

Landowner submits a grievance -> the local Landowner backend saves it -> the browser integration layer mirrors the payload -> the central workflow assigns it to `grievance_officer` -> Grievance Officer sees it in Connected NLAMS Workflow -> forwarding creates the next workflow event -> the same reference remains the transaction key.

## GIS

Survey/GIS uses real browser geolocation when permission is granted. On desktop browsers, accuracy depends on the computer/browser location source. On a GPS-enabled phone/tablet, use HTTPS or a trusted local deployment and allow location permission for best accuracy.
