# K3 — Session 03 Summary
**Date:** 24/04/2026
**Migrations:** 0019, clean
**Repo:** `main` (stable base) + `dev` (all wizard work) — `inab-certh/K3-ticket-management-system`

---

## What Was Done This Session

**User Roles & Permissions:**
- Created `UserProfile` model with `center` FK + `role` field (admin/staff) — migration 0019
- Signal auto-creates profile on new user creation
- `can_edit_person()` helper checks center match + superuser/admin bypass
- `PersonUpdateView` now checks permission before allowing edit
- Registered `UserProfileAdmin` in Django admin
- Created profiles for existing users via shell command

**Settings Page:**
- Built `records/templates/records/settings.html`
- `settings_view` handles POST (save name, email, center)
- Password change wired via Django's built-in `PasswordChangeView`
- Navigation fixed: Προφίλ μου and Ρυθμίσεις both point to `settings_view`
- Removed duplicate Ρυθμίσεις from dropdown
- Υποστήριξη → `mailto:` link

**Notifications Bell:**
- Created `records/context_processors.py`, registered in `K3/settings.py`
- Bell dropdown shows all alert types with counts and links
- Badge shows `total_alerts` on bell icon
- Added `alert_incomplete_profiles` to bell dropdown

**Search:**
- Built `search_view` with combined Person + Request results
- Navbar search form submits to search page
- Results page shows persons (with `open_requests` annotation) and requests in separate tables

**Dashboard:**
- Added 4th summary card: "Νέοι αυτόν τον μήνα"
- Added KEPA calendar using FullCalendar 6 (color coded)
- Added KEPA expiration list (expired + upcoming)
- Added registrations line chart (Chart.js, last 12 months)
- Fixed timezone-naive datetime warning in chart query
- Fixed `total_requests` to exclude intake requests

**Statistics Page — full rebuild:**
- Fields: gender, marital, insurance, employment, nationality, center, request status, communication, priority, neoplasm categories, comorbidities, BMI
- Doughnut charts (gender, insurance), bar charts (neoplasms, comorbidities), tables for everything else
- Fixed `models.F` import issue

**Wizard Tab Navigation:**
- Tabs clickable when editing existing person
- New entry: tabs are spans (non-clickable, sequential)
- Tab click saves current step data then jumps to target step (`action=jump`)
- Fixed: JS targeting wrong form — fixed with `id="wizard-form"`
- Fixed: button value overriding hidden action — fixed by disabling buttons before submit
- Breadcrumb shows "Επεξεργασία Ωφελούμενου #ID" when editing

**Bug Fixes:**
- `Request.save()` broken auto-set category logic removed
- KEPA expiry date not repopulating in step 5 — fixed

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
- Action model design — still unresolved
- KEPAAssessment model + migration
- VM / deployment setup

---

## 3. Key Files Changed This Session

- `records/models/userprofile.py` — new `UserProfile` model
- `records/context_processors.py` — new file, notifications bell logic
- `records/templates/records/settings.html` — new file
- `records/templates/records/dashboard.html` — cards, KEPA calendar, chart
- `records/templates/records/statistics.html` — full rebuild
- `records/views.py` — `settings_view`, `search_view`, `PersonUpdateView` permission check, statistics rebuild
- `K3/settings.py` — context processor registered
