# K3 System — Model & Data Architecture Review
**Date:** March 2026  
**Status:** Pre-development alignment document

---

## 1. What This System Is

K3 is a Django 4.2 case management application for a cancer patient support organization. It manages beneficiaries (ωφελούμενοι), their medical and socioeconomic profile, the requests they bring to K3, and the actions K3 takes on their behalf.

The system was built by digitalizing an existing operational Excel master file (`K3-DB_023_ΑΣΘΕΝΕΙΣ_MASTER_FILE`). The KEPA assessment form (`ΑΠΟΦΑΣΗ_ΚΕΠΑ`) was subsequently provided as an additional data source requirement — it was not the original basis for the models.

---

## 2. Source Documents

| Document | Role |
|---|---|
| `K3-DB_023_ΑΣΘΕΝΕΙΣ_MASTER_FILE.xlsx` | Primary source. K3 operational data, 9 sheets, ~350 beneficiary records |
| `ΑΠΟΦΑΣΗ_ΚΕΠΑ.docx` | Secondary source. Official KEPA committee decision form |

---

## 3. Stack & Project Structure

- Django 4.2, Python 3.x, MySQL (mysqlclient + python-dotenv)
- Volt Dashboard (Bootstrap 5), vendored in `static/`
- `django_extensions` installed
k3-clean/
├── K3/          # project config (settings, urls, wsgi, asgi, .env)
├── records/     # main app (models, views, forms, templates, migrations)
├── static/      # Volt Bootstrap 5 theme + custom JS
└── venv/        # not in repo

Migrations: `0001_initial` → `0013`

---

## 4. Model Assessment

### person.py — Person
| Field | Status |
|---|---|
| last_name, first_name, father_name, mother_name | ✅ |
| birth_year (IntegerField) | ⚠️ Should be full DateField |
| gender, marital_status, children_count, minors | ✅ |
| vat, amka | ✅ with validators |
| id_card (ΑΔΤ) | ❌ Missing |
| nationality | ✅ |
| citizenship (distinct from nationality) | ❌ Missing |
| address, city, postal_code, municipality, region | ✅ |
| phone, mobile, email | ✅ |
| is_student | ❌ Missing |
| military_exemption | ❌ Missing |
| center (FK) | ✅ |

### person.py — ContactPerson
Complete for its scope.

### medhistory.py — MedicalHistory
| Field | Status |
|---|---|
| disability, certified_disability, disability_percentage | ✅ |
| kepa_check, kepa_expiry | ✅ |
| KEPA admin refs (ΑΜ.ΚΕΠΑ, Αρ.Γνωστοποίησης, etc.) | ❌ Missing |
| Breakdown percentages (κινητική, όραση, κώφωση, etc.) | ❌ Missing |
| Per-diagnosis flags (αναστρέψιμη, προϋπάρχουσα, etc.) | ❌ Missing |
| Legal entitlement outcomes | ❌ Missing |

### medhistory.py — Neoplasm
| Field | Status |
|---|---|
| icd10_code, icd10_category, icd10_subcategory | ✅ cascading FK |
| localization, metastasis, surgery, surgery_hospital | ✅ |
| Therapy links | ✅ via Therapy model |
| Scheduled treatment flag | ❌ Missing |

### medhistory.py — Comorbidity
| Field | Status |
|---|---|
| Categorical comorbidities | ✅ via ComorbidityType lookup |
| Weight, height, BMI | ❌ Missing |

### lookups.py — Insurance/Employment
| Field | Status |
|---|---|
| InsuranceProvider, EmploymentStatus | ✅ |
| Specialty funds (ειδικά ταμεία) | ❌ Missing |
| Widowhood pension flag | ❌ Missing |
| Unemployment card + registration date | ❌ Missing |

### Other models
`Request`, `Action`, `Document`, `ICD10`, `Geography`, `Organization` — all solid for current scope.

---

## 5. Required Changes

### person.py
- `birth_year` (IntegerField) → `birth_date` (DateField) — data migration needed if records exist
- Add: `id_card`, `citizenship`, `is_student`, `military_exemption`

### medhistory.py
- Keep `MedicalHistory` as quick-reference summary (disability flags, kepa_check, kepa_expiry)
- Add `KEPAAssessment` model (FK to Person, multiple over time):
  - Admin: `am_kepa`, `notification_number`, `committee_number`, `ype_type`, `valid_from`, `valid_until`, `insurance_carrier`
  - Percentages: `pct_mobility`, `pct_vision`, `pct_hearing`, `pct_psychiatric`, `pct_accident`, `pct_occupational`, `pct_deterioration`, `pct_psychiatric_accident`, `total_disability_pct`
  - Entitlements: `entitlement_old_age_pension`, `entitlement_institutional_allowance`, `entitlement_mobility_allowance`, `requires_assistance`, `law_2643_1998`, `law_1798_1988`
- Add `KEPADiagnosis` model (FK to KEPAAssessment, up to 3):
  - `order`, `icd10_code`, `is_irreversible`, `is_pre_existing`, `from_accident`, `from_occupational_disease`, `deteriorated`
- Add `is_scheduled_treatment` to Neoplasm
- Add `weight`, `height` to Comorbidity or MedicalHistory; `bmi` as `@property`

### lookups.py
- Add `SpecialFund`, `widowhood_pension`, `has_unemployment_card`, `unemployment_registration_date`

---

## 6. Migration Impact

| Change | Type | Risk |
|---|---|---|
| birth_year → birth_date | Data migration + schema | Low if DB near-empty |
| Add fields to Person | Schema only, nullable | None |
| Add fields to MedicalHistory | Schema only, nullable | None |
| New KEPAAssessment, KEPADiagnosis | New tables | None |
| Add fields to Neoplasm, Comorbidity | Schema only, nullable | None |

---

## 7. What Is NOT Being Changed

- `Request`, `Action`, `Document`, `ICD10`, `Geography`, `Organization` models
- Volt theme integration
- URL structure

---

## 8. Recommended Execution Order

1. Approve this document
2. Apply model changes + migration 0014
3. Fix `views.py` form breakage (`PersonForm = None` nullification)
4. Wire up 5-step form completely
5. Add KEPA assessment sub-form in person detail
6. Complete dashboard and statistics views
7. End-to-end test → redeploy