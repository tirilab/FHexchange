# FHexchange: Resources for Family Health History Extraction and Normalization From Consumer Dialog Sources
## Introduction to this resource
Thanks for visiting this repository. Here you can access the annotated datasets from the paper: **FHexchange: Resources for Family Health History Extraction and Normalization From Consumer Dialog Sources, BioNLP 2026** (without UMLS identifiers). If you'd like to access the UMLS CUI annotations, please contact the authors using this form: 

## Dataset sources
FHexchange is a resource that consists of annotated data from two existing dialog corpora:
1. 104 Chatbot transcripts from Nguyen et al., 2024, JMIR [^1] referred to as FHexchange-KIT, and
2. 154 FHx-related dialogs from the openly available MTS-Dialog dataset from Ben Abacha et al., 2023, Proceedings of the 17th Conference of the European Chapter of the Association for Computational Linguistics [^2], referred to as FHexchange-MTS. [MTS-Dialog repository](https://github.com/abachaa/MTS-Dialog) 

## Folder structure

The repository is organized according to the two data sources as follows:

```text
FHexchange/
├── FHexchange_KIT/
│   ├── transcripts/
│   │   ├── 0.txt
│   │   ├── 1.txt
│   │   ├── 2.txt
│   │   └── ...
│   └── annotations/
│       └── FHexchange_KIT.json
│
├── FHexchange_MTS/
│   └── annotations/
│       └── FHexchange_MTS.json

```
The FHexchange_MTS transcripts can be downloaded from the MTS-Dialog repository. 

## Annotation file convention

Each annotation file is a single JSON dictionary where:
- ***keys*** correspond to transcript/dialog IDs
- ***values*** are lists of annotated family history mentions for that record

  
Each individual family history mention contains the following fields:

- **family_member**: the relative mentioned in the family history
- **age_of_onset**: age when the condition began, if available
- **observation**: the condition, symptom, or health-related observation
- **side_of_family**: maternal/paternal side, if specified
- **living_status**: whether the family member is living or deceased, if available
- **age**: age of the family member, if mentioned
- **age_of_death**: age at death, if mentioned
- **cause_of_death**: reported cause of death, if available
- **negated**: whether the condition is negated or absent (true/false)

if not mentioned, the value is null. 

### Example
```
{
  "1": [
    {
      "family_member": "Mother",
      "age_of_onset": null,
      "observation": "High blood pressure (hypertension)",
      "side_of_family": null,
      "living_status": null,
      "age": null,
      "age_of_death": null,
      "cause_of_death": null,
      "negated": false
    }
  ]
}
```
[!NOTE]
The set with UMLS CUI annotations includes an additional field labeled **cui**. Please complete the form to verify your UMLS Terminology Services account in order to access the data. 

## Acknowledgments
We'd like to acknowledge the genetic counselors who assisted us in developing the annotation guideline. Additionally, thank you to the MTS-Dialog dataset authors, Drs. Asma Ben Abacha, Wen-wai Yim, Yadan Fan, Thomas Lin for making the resource accessible for the clinical NLP research community!

## References
[^1]: Nguyen M, Sedoc J, Taylor C. Usability, Engagement, and Report Usefulness of Chatbot-Based Family Health History Data Collection: Mixed Methods Analysis. J Med Internet Res 2024;26:e55164. URL: https://www.jmir.org/2024/1/e55164. DOI: 10.2196/55164
[^2]: Asma Ben Abacha, Wen-wai Yim, Yadan Fan, and Thomas Lin. 2023. An Empirical Study of Clinical Note Generation from Doctor-Patient Encounters. In Proceedings of the 17th Conference of the European Chapter of the Association for Computational Linguistics, pages 2291–2302, Dubrovnik, Croatia. Association for Computational Linguistics. 

