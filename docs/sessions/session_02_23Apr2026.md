# K3 — Current State
**Date:** 23/04/2026  
**Migrations:** 0014, clean (`is_intake` applied)  
**Repo:** `main` (stable base) + `dev` (all wizard work) — `inab-certh/K3-ticket-management-system`

---

## 1. What Works End-to-End

- Person CRUD — create, list, detail, edit all working
- Person detail — gradient header, K3 dark/red palette, recent requests with #1/#2 counters, `← Ωφελούμενος` back button visible
- Request CRUD — create, list, detail, edit all working
- Intake requests (`is_intake=True`) filtered out of person detail and request list
- Wizard completion → redirects to `person_detail`
- Actions save correctly (broken `Request.save()` auto-category logic removed)
- Multi-step intake wizard — all 5 steps working (save + repopulate):

| Step | Title | Models | Save | Repopulate |
|---|---|---|---|---|
| 1 | Αρχικά Στοιχεία | Person + Request (intake) | ✅ | ✅ |
| 2 | Επιπλέον Στοιχεία | Person extra + ContactPerson | ✅ | ✅ |
| 3 | Ασφαλιστική-Εργασιακή | Insurance + Employment on Person | ✅ | ✅ |
| 4 | Νεοπλάσματα | Neoplasm + Therapy with ICD10 FK | ✅ | ✅ |
| 5 | Ιστορικό/Συνοδά/BMI | MedicalHistory + Comorbidity + BMI | ✅ | ✅ |

---

## 2. Pending — Next Session

**Bugs/fixes:**
- `request_id` carried through `prev` on steps 3–4
- Neoplasm delete button label → "Διαγραφή Νεοπλάσματος"
- SweetAlert2 — confirm works on all forms
- Statistics view stale field refs (`insurance__insurance_status`, `primary_category`) — will crash if visited

**Features:**
- Action model design — still unresolved (call/email/referral split, `direction`, `contact_type`, `external_org` FK vs freeform, minimum viable log)
- Dashboard — real data widgets
- KEPAAssessment model + migration 0015
- `populate_persons` management command for demo data

---

## 3. Key Files Changed This Session

- `records/models/request.py` — added `is_intake`, fixed broken `save()`
- `records/forms/step5_history.py` — new file
- `records/templates/records/forms/step5_history.html` — fixed HTML
- `records/views.py` — step 5 POST/GET, `is_intake` flag, `PersonDetailView` and `RequestListView` filters
