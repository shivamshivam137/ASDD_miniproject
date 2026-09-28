# NLAMS Real Connected Workflow – v5

## Core rule
Do not create a separate copy of a project in every portal. The central NLAMS integration database is the authoritative case record. Each officer portal receives a workflow task that opens the same Project/Parcel/Landowner/Documents/GIS/Evidence/History packet.

## Automated handoff
Project Agency creates and saves a project -> central project record and workflow are created -> LAO receives a task and complete case packet -> LAO decision updates the central workflow -> Revenue receives the same project data and documents -> R&R receives the same record -> Survey/GIS receives the same parcels plus GIS evidence -> Administration receives the final case.

Notifications are only the alert. The task queue now loads the complete case packet before a decision: project identity, parcels, documents, landowners, GIS evidence, workflow history, and role-specific verification checklist.

## Why this is the correct architecture
A government workflow should not depend on an officer clicking Approve from a notification without seeing the underlying case. The notification routes work; the central record supplies the evidence needed to perform the work. Keeping one authoritative record also prevents conflicting project copies between departments.
