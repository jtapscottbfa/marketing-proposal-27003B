# Subconsultant Intake

This folder is generated and populated by `scripts/rfp_shred.sh`. Do not create subfolders manually — the script scaffolds them from roles identified in the RFP.

---

## Workflow

### 1. Run the shred (one command)

```bash
# Drop your RFP into 00_admin/rfp_intake/original_rfp/, then:
bash scripts/rfp_shred.sh

# Or with the title pre-supplied to skip the prompt:
bash scripts/rfp_shred.sh --title "Agency IFB-2025-001"
```

This produces:

- `00_admin/rfp_shred_YYYYMMDD.md` — full requirements decomposition
- `subconsultant_digest.md` — pre-populated with roles Claude identified from the RFP
- One subfolder per role (see structure below)

### 2. Fill in the digest

Open `subconsultant_digest.md` and fill in `Firm Name`, `POC Name`, `POC Email`, and `MBE Status` as you lock in your team. `Role`, `Documents Received`, and `Status` are pre-populated.

### 3. Drop received docs

As subconsultants send materials, drop files into the relevant role subfolder:

```text
subconsultant_intake/
  mep-engineering/
    received/        ← drop everything here first
    resumes/
    project_sheets/
    letters/
  civil-engineering/
    received/
    ...
```

### 4. Sort docs (coming soon)

`sort_docs.sh` will organize files from `received/` into `resumes/`, `project_sheets/`, and `letters/` based on filename patterns.

---

## Digest Fields

| Field | Description |
| --- | --- |
| **Firm Name** | Legal name of the subconsultant firm — fill in manually |
| **Role** | Functional role in the contract — pre-populated from RFP shred |
| **POC Name** | Main point of contact — fill in manually |
| **POC Email** | POC email address — fill in manually |
| **MBE Status** | SBE/SWaM/DBE/MBE certification and certifying agency — fill in manually |
| **Documents Received** | ☐ unchecked until all required docs are in hand |
| **Status** | `Pending` → `Confirmed` → `Compliant` |

---

## Notes

- Role folder names are slugified from the role title (e.g. `MEP Engineering` → `mep-engineering`). Do not rename folders after creation — `sort_docs.sh` will rely on them.
- If a role is added after the initial shred, create the folder manually using the same slug convention and add a row to `subconsultant_digest.md`.
- If a firm drops out, update their row in the digest. The folder stays — documents already received remain in place.
