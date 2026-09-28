# NLAMS Automation Upgrade

This build adds an acceptance-ready automation layer while preserving the existing portal structure.

## Automation Center

Every portal with `data-nlams-role` now gets a shared **NLAMS Automation Center** with working tabs:

1. Overview — central metrics and workflow chain
2. Tasks — role-based automatic task queue
3. Documents — shared document registry for P-001
4. GIS Evidence — shared photos/GPS/boundary registry
5. Notifications — automatic workflow notifications
6. Audit — workflow event timeline
7. Validation — document/GIS validation rules
8. Case Health — completeness score and risk
9. AI Doc Guide — explains which documents are useful for a grievance/request

## AI Document Guide

The AI-style document assistant analyzes the grievance/request text and category and produces an explainable document checklist. It currently uses deterministic keyword/rule classification so the prototype works offline and is reliable during judging. It is deliberately labelled as guidance; final legal/document requirements remain subject to officer verification.

Examples:

- Compensation/payment complaint → Award Copy / Compensation Statement
- Ownership/survey complaint → 7/12, Ownership/Title, Mutation, Survey/Measurement
- Possession complaint → Possession/Handover Notice
- R&R complaint → R&R/Rehabilitation Eligibility Record
- Notification complaint → Acquisition Notification/Notice
- Boundary/area complaint → Survey/Measurement Report

## Reliability rules

The central workflow engine blocks:

- Revenue approval when 7/12 and ownership evidence are missing.
- GIS approval when GPS and at least one field photo are missing.

Approved workflow transitions automatically create the next task and notification and append an audit event.

## Demo case

Use `P-001 / Survey 125` as the hero parcel:

Project: `NH44-MH-001`
Owner: `Demo Owner A`
Area: `2.5 acres`

The same IDs are used by Project Agency, Revenue, GIS, LAO, R&R, Compensation, Grievance and Admin.

## Resetting the demo

Run `RESET_DEMO.bat` before a fresh presentation. Then run `START_ALL_NLAMS.bat`.

The reset only clears the central integration database; the portal-specific local demo databases are not deleted.
