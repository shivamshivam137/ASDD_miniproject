NLAMS GIS / LIVE TRACKING FIXES

1. Survey & GIS Officer: fixed the Vite/JS syntax error in src/main.jsx. GPS timestamps loaded from the integration service are normalized back to Date objects. Existing browser geolocation watch, geo-tagged evidence and Leaflet maps remain enabled.
2. Revenue Officer: replaced the prototype CSS parcel map with a real Leaflet/OpenStreetMap parcel map. The selected case has a reference coordinate, live browser GPS tracking, accuracy circle, and shared location persistence.
3. R&R Officer: replaced the prototype field map with a real Leaflet/OpenStreetMap map, shows R&R sites and shared officer locations, and has live GPS tracking that updates the form coordinate.
4. Administrator GIS Command Map: replaced the fake national map with a real Leaflet/OpenStreetMap map using project lat/lng from the portal database, shared NLAMS field locations, and live administrator tracking.
5. Grievance Officer: fixed tab/action function-name collisions caused by HTML element IDs (triage, verify, duplicates, report). Verification Report generation now validates inputs, saves through /api/report, displays the report number, and provides Print / Save PDF.

Browser GPS requires location permission. Map tiles require internet access to OpenStreetMap. The localhost/127.0.0.1 development server is suitable for browser geolocation in modern browsers; production should use HTTPS and an authorized GIS/tile service.
