# NLAMS Governance-Ready Prototype Upgrade

This release adds a security/privacy layer and automation-first UX across the portals.

## Design principles
- One authoritative Project → Parcel → Landowner → Document → Complaint chain.
- Role-based access at every portal; citizen and officer views are separated.
- Central automation service provides next-action hints, tasks, notifications and audit events.
- Privacy notice is visible in every portal and a central policy endpoint exposes the current policy version.
- Sessions use HttpOnly/SameSite controls, inactivity awareness and security headers.
- Sensitive records should be served only through authenticated APIs in production.

## Production hardening required before government deployment
Use approved government identity/SSO (e.g. the authority's designated identity provider), HTTPS/TLS, managed secrets/HSM/KMS, centralized PostgreSQL, object storage with encryption and malware scanning, WAF/API gateway, centralized SIEM/audit retention, backups/DR, formal RBAC/ABAC, DPIA/privacy review, accessibility/security testing, and approved retention/deletion schedules. The included data and documents remain synthetic demo records.
