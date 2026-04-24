# K3 — Current State
**Date:** 24/04/2026
**Migrations:** 0019, clean
**Repo:** `main` (stable base) + `dev` (all wizard work) — `inab-certh/K3-ticket-management-system`

---

## 1. What Works End-to-End

| Feature | Status |
|---|---|
| Wizard steps 1–5 | ✅ Complete |
| Wizard tab navigation | ✅ Complete |
| Settings page | ✅ Complete |
| Notifications bell | ✅ Complete |
| Search | ✅ Complete |
| Dashboard | ✅ Complete |
| Statistics | ✅ Complete |
| User roles | ✅ Basic (admin/staff + center) |

---

## 2. Pending — Next Session

**Bugs/fixes:**
- `request_id` carried through `prev` on steps 3–4
- Neoplasm delete button label → "Διαγραφή Νεοπλάσματος"
- Sidebar active state for edit vs new entry
- Password change template — needs creating

**Features:**
- Statistics interactive filters (center, date range)
- CSV export
- Action model design — still unresolved (call/email/referral split, `direction`, `contact_type`, `external_org` FK vs freeform, minimum viable log)
- KEPAAssessment model + migration
- VM / deployment setup

---

## Priority for Next Session

`request_id` prev fix → neoplasm label → password change template → sidebar active state → statistics filters → CSV export → Action model decision → KEPA → VM/deployment
