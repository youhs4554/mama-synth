# Crawled Page: 
            
    Data - The MAMA-SYNTH Challenge - Grand Challenge

            
                
            
        
- **Source URL:** [https://mamasynth.grand-challenge.org/data/](https://mamasynth.grand-challenge.org/data/)

---

### **Data**[¶](#data "Permanent link")

#### **Overview**[¶](#overview "Permanent link")

The MAMA-SYNTH challenge adopts a **multi-center data design** to promote algorithmic generalizability across scanners, acquisition settings, and patient populations.

The benchmark combines a large-scale training cohort with two independent external test cohorts. This design supports robust evaluation of virtual contrast-enhancement methods under clinically realistic distribution shifts.

#### **Training cohort**[¶](#training-cohort "Permanent link")

The training cohort is based on the **MAMA-MIA** dataset, which contains pre-treatment breast DCE-MRI from **1,506 patients** collected from **more than 25 centers** across the United States.

This dataset was also used in the first edition of the MAMA challenges for **primary tumor segmentation** and **pathologic complete response prediction**, and serves here as the development cohort for virtual post-contrast MRI synthesis.

#### **External test cohorts**[¶](#external-test-cohorts "Permanent link")

The test data are acquired from two independent external institutions:

* **Radboud University Medical Centre** — The Netherlands
* **Instituto Alexander Fleming** — Argentina

Each test case corresponds to a **2D slice** extracted from a patient’s DCE-MRI examination. For each patient, the selected slice contains the **largest malignant tumor area** in the **peak-enhancement phase**.

All test images are **fat-suppressed** and acquired in the **axial plane**.

This external evaluation design is intended to assess the robustness of submitted methods across different scanners, imaging protocols, and patient populations.

#### **Cohort summary**[¶](#cohort-summary "Permanent link")

| Attribute | Training cohort (MAMA-MIA) | Test cohort A (Radboud University Medical Centre) | Test cohort B (Instituto Alexander Fleming) |
| --- | --- | --- | --- |
| Role | Development / training cohort | External test cohort | External test cohort |
| Country / region | United States | The Netherlands | Argentina |
| Number of cases | 1,506 cases | 200 cases | 100 cases |
| Source | Multi-center dataset | Single external institution | Single external institution |
| Centers | 25+ centers | 1 institution | 1 institution |
| Imaging type | Pre-treatment breast DCE-MRI | 2D slice from breast DCE-MRI | 2D slice from breast DCE-MRI |
| Slice selection | - | Largest malignant tumor area in the peak-enhancement phase | Largest malignant tumor area in the peak-enhancement phase |
| Acquisition plane | Axial (84.4%), Sagittal (15.6%) | Axial | Axial |
| Fat suppression | - | Yes | Yes |
| Image dimension | - | 416 × 416 px | 512 × 512 px |
| Magnetic field strength | 1.5T (72.1%), 3T (27.9%) | 3T | 1.5T |
| Scanner manufacturer | GE (64.1%), Siemens (27.3%), Philips (8.6%) | Siemens | GE |
| Contrast agents | - | DOTAREM (99%), GADOVIST (0.5%) | DOTAREM, GADOVIST |
| Acquisition protocol | - | t1\_fl3d\_tra\_Dixon\_W | - |
| TR | - | 5–10 ms | 4.2 ms |
| TE | - | 2–5 ms | 2 ms |
| Flip angle | - | 8–15° | 12° |
| Slice thickness | - | Approximately 1 mm | 1.1 mm |
| Pixel spacing | - | Range: 0.8654–0.9615 mm; Mean: 0.8689 mm; Median: 0.8654 mm; SD: 0.0157 mm | - |
| Molecular subtypes | - | Luminal: 165 (85.7%); Triple Negative: 23 (9.4%); Other: 12 (4.9%) | Luminal: 37 (37%); Triple Negative: 30 (30%); Other: 20 (20%) |

#### **Data access and usage**[¶](#data-access-and-usage "Permanent link")

The challenge data are provided for the development and evaluation of methods within the scope of MAMA-SYNTH 2026.

Participants may train their methods using:

* the data provided by the challenge, and/or
* additional **publicly available datasets**

The use of **private data** is not allowed.

Any external dataset used in model development should be clearly documented as part of the submission.

#### **Data policy**[¶](#data-policy "Permanent link")

Participants must comply with the challenge governance requirements and with any organizer-defined restrictions regarding data usage, redistribution, and controlled-access repositories.

The use of non-public institutional data, private collections, or privately shared model-development resources is prohibited.

We further note that by participating in this challenge, participants agree to comply with EO 14117, 28 CFR Part 202, and Guide Notice [NOT-OD-25-083](https://grants.nih.gov/grants/guide/notice-files/NOT-OD-25-083.html) and acknowledge that the usage of NIH Controlled-access Data Repositories (CADRs) is prohibited in this challenge.

Further details regarding permitted data usage and submission requirements will be provided in the relevant challenge documentation.