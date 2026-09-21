# Government of India Copyright Registration Filing Guide (Form XIV)

## Work: JudiQ — Section 138 NI Act Litigation Intelligence Platform

This guide provides field-by-field instructions for filing the copyright application exclusively for the **Section 138 Negotiable Instruments Act (NI Act, 1881) litigation intelligence software** of JudiQ on the official Government of India Copyright Office portal: **[https://copyright.gov.in](https://copyright.gov.in)**.

---

## 1. Statutory Framework & Rule 70(5) Compliance

Under **Rule 70(5) of the Copyright Rules, 2013** and **Section 2(o) of the Indian Copyright Act, 1957**:
> *"In respect of a computer programme, the applicant shall submit the source code and object code. In case the source code is more than 20 pages, the first 10 pages and the last 10 pages of the source code should be deposited."*

### Exclusively Section 138 NI Act Implementation

- **Section A (Pages 1 to 10)**:
  - **`backend/cheque_bounce/cheque_bounce_engine.py`**: Master Section 138 NI Act procedural graph engine, cheque presentation timeline rules (RBI 90 days), statutory notice timelines (30 days), complaint windows (15 days grace + 30 days filing), Section 139 & 118 statutory debt presumptions, and Section 141 company/director vicarious liability.
  - **`backend/cheque_bounce/ni_act_statutory_rules.py`**: Landmark Supreme Court legal precedent evaluation (*Central Bank of India v. Saxons Farms*, *Yogendra Pratap Singh*, *Rangappa*, *Bir Singh*, *Basalingappa*, *Aneeta Hada*, *Rakesh Ranjan Shahi*), territorial jurisdiction under Section 142(2), Section 143A interim compensation, and Section 148 appellate deposits.
  - **`backend/cheque_bounce/defence_catalogue.py`**: Section 138 defense patterns and rebuttal strategies (Security cheque defense, signature dispute, time-barred debt, non-service of notice, lack of financial capacity).
- **Section B (Pages 11 to 20)**:
  - **`backend/banking/statutory_drafter.py`**: Court-admissible Section 138(b) Demand Notice drafting, Section 142(1)(b) delay condonation petitions, Section 143A interim compensation petitions, and Section 65B/Section 63 BSA electronic evidence certificates.
  - **`frontend/draft_templates.js`**: Section 138 timeline verification engine, Legal Notice under Section 138 NI Act, Reply to Notice, and Criminal Complaint under Section 138 & 142 NI Act before the Judicial Magistrate / Metropolitan Magistrate Court.
- **Strict 20 Pages**: Exactly 10 pages for Section A and 10 pages for Section B.
- **Zero Redactions**: Complete, legible monospace code with line numbers and vertical gutter guides.
- **File Size**: 0.07 MB (well under the 10 MB maximum portal threshold).

---

## 2. Prepared Files in `ip code submission/`

| File Name | File Size | Description & Portal Use |
| :--- | :--- | :--- |
| **`JudiQ_Source_Code_Copyright_Submission_20Pages.pdf`** | **0.07 MB** | **PRIMARY UPLOAD FILE** for the portal under "Upload Work / Source Code". Exactly 20 pages of Section 138 NI Act code. |
| **`JudiQ_Source_Code_Repository_Clean.zip`** | **0.92 MB** | Complete clean repository source code archive (0 git, 0 node_modules, 0 cache, 0 `.env`, 0 db dumps). |
| **`generate_submission_pdf.py`** | **~13 KB** | Python generator script to recreate or re-validate the submission PDF and clean ZIP. |
| **`page_1_preview.png`** / **`page_11_preview.png`** | — | High-resolution visual proof of Page 1 (Section A) and Page 11 (Section B). |

---

## 3. Form XIV — Statement of Particulars (SoP) Checklist

| Field No. | Form XIV Field | Value to Enter on copyright.gov.in |
| :---: | :--- | :--- |
| **1.** | **Name, address & nationality of Applicant** | **Atharva** (Nationality: Indian, Address: Permanent residential address) |
| **2.** | **Nature of the Applicant's interest** | **Author & Owner** (Select "Author") |
| **3.** | **Class and description of the work** | **Computer Software Work (Literary Work under Sec 2(o))** |
| **4.** | **Title of the work** | `JudiQ: Section 138 NI Act Litigation Intelligence Platform` |
| **5.** | **Language of the work** | `English / Python, JavaScript` |
| **6.** | **Published or unpublished?** | Select **Unpublished** (or Published, if live) |
| **7.** | **Name, address & nationality of Author** | Name: **Atharva** (Nationality: Indian, Status: Alive) |
| **8.** | **Sole Author?** | **Yes** (Sole Developer & Creator) |
| **9.** | **Description / Remarks** | Computer software comprising automated reasoning engines, statutory limitation calculators, and court document drafters exclusively for Section 138 of the Negotiable Instruments Act, 1881. Deposited under Rule 70(5) (First 10 Pages & Last 10 Pages). |

---

## 4. Online Portal Upload Steps

1. Go to **[copyright.gov.in](https://copyright.gov.in)** and login.
2. Select **"e-Filing of Application"** -> **"Form XIV (Literary/Software Work)"**.
3. Fill in the Statement of Particulars as listed in Section 3 above.
4. In the document upload step, upload:
   - **Work Deposit**: `JudiQ_Source_Code_Copyright_Submission_20Pages.pdf`
   - **Identity Document**: Government ID (Aadhaar / Passport of Atharva).
5. Pay the statutory individual filing fee of **₹500** via Bharatkosh.
6. Note down the **Diary Number** and download the acknowledgment copy.
