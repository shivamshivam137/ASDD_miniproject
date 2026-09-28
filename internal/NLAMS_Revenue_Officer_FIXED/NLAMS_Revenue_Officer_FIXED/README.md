# NLAMS — Revenue Officer Dashboard (Fixed)

Working Flask + SQLite prototype for the Revenue Officer module.

## Fixed in this version
- **GIS Verification** now has its own working `/gis` page, case selector, parcel map, parcel details, zoom/reset controls and link back to the full case.
- **Documents** now has its own working `/documents` page, case selector, document status controls, Verify All action and preview panel.
- **Notifications** now has seeded workflow alerts and dynamically shows issues created by Flag/Reject actions.
- **Audit Trail** now has seeded activity and dynamically records verification, issue, rejection and document actions.
- Sidebar items now route to their actual modules instead of opening the Land Cases page.
- Existing older demo databases are automatically back-filled with initial audit/notification data.

## Run
```bash
pip install -r requirements.txt
python app.py
```
Open: `http://127.0.0.1:5000`

## Recommended SIH demo
1. Open **Land Cases**.
2. Open `NLAMS-PUN-001`.
3. Use **GIS Verification** from the sidebar and select the case.
4. Use **Documents** and change a document status or click **Verify All**.
5. Return to the case and click **Flag Issue** or **Approve Verification**.
6. Open **Notifications** to see the generated workflow alert.
7. Open **Audit Trail** to see the action recorded.
