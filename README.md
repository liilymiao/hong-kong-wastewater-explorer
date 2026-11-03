# Hong Kong Wastewater Explorer

[**Open app**](https://liilymiao.github.io/hong-kong-wastewater-explorer/) · [**Download**](https://github.com/liilymiao/hong-kong-wastewater-explorer/releases/latest/download/project.zip) · [**Video**](https://liilymiao.github.io/hong-kong-wastewater-explorer/video.html)

A research workspace for Hong Kong COVID-19 monitoring and wastewater–clinical antimicrobial resistance research. Query observations, inspect their sources, compare saved forecasts and export an analysis with its conditions.

The app includes nine public research datasets alongside the frozen COVID-19 analysis:

| Dataset | Available records |
| --- | --- |
| Hong Kong PHLSB outpatient resistance | 234 annual records, 2020–2025, across 5 specimen types and 12 organisms. Official resistance percentages and marker-positive counts remain separate. |
| European sewage ARG study | 235 biological samples, 554 ResFinder gene columns and 130,190 raw count cells, 2019–2021. |
| Hong Kong community sewage study | 189 sample identifiers with sequencing and assembly QC; a separate ENA index contains 406 run records. |
| Hospital Authority blood-culture AMR | 175 annual non-susceptibility records, 2020–2024, with confidence intervals and count-quality flags. |
| Hong Kong antimicrobial supply | 444 annual sector/group records, 2014–2025, in DID; 2025 is provisional. |
| BV-BRC experimental AST | 15,777 E. coli/ciprofloxacin experimental records linked to 10,904 genomes; 12,305 records meet the documented cohort rules. |
| HKO rainfall | 2,830 daily station records, 2019–September 2026; Trace and completeness flags retained. |
| Flu Express | 669 weeks and 27 clinical indicators, 2014W1–2026W43, with the official field units. |
| Global Sewage 3 | Fixed v1 subset: 16 samples, 17,402 reported cluster-count rows and 2,638 clusters. |

Dataset queries retain source units, missing values and original identifiers. Local wastewater measurements, exact clinical AST counts and explicit area mappings can also be imported to construct ecological research tables. The loaded datasets do not include a wastewater–clinical pairing matrix.

The complete download includes website **1.6.0**, Python application **1.5.2**, scientific configuration **1.1**, frozen results, video and eight subtitle tracks. The Python package and media are unchanged from v1.5.2.

[Data sources and updates](DATA_SOURCES.md) · [Release notes](RELEASE_NOTES.md) · [Dataset manifest](research-datasets.json) · [Frozen COVID-19 sources](source_manifest.json) · [Credits](CREDITS.txt)

Project-owned code and documentation use the [MIT License](LICENSE). Other materials retain their recorded terms in [Third-party notices](THIRD_PARTY_NOTICES.md).
