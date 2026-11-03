# Third-party notices

## Government surveillance data

Source and ownership: Department of Health, Government of the Hong Kong Special Administrative Region; supplied through DATA.GOV.HK. [Dataset](https://data.gov.hk/en-data/dataset/hk-dh-chpsebcddr-covid-express) · [DATA.GOV.HK terms](https://data.gov.hk/en/terms-and-conditions).

The dataset page explicitly lists `covidx_data.csv` and the data dictionary `covidx_spec_en.pdf`. This relationship was checked on 3 November 2026. The public package uses frozen CSV data and its source metadata with attribution. DATA.GOV.HK terms cover the resources supplied through that portal; a link to another site does not establish that all materials on that site share those terms. Extra CHP weekly reports and copied course materials are excluded from the release packages. Their source links, hashes, and purpose are retained in `release_sources.json`. The dictionary is also linked rather than copied to keep the package small.

## PHLSB outpatient resistance

Source: Department of Health, Hong Kong SAR Government, Public Health Laboratory Services Branch, through [DATA.GOV.HK](https://data.gov.hk/en-data/dataset/hk-dh-dh_phlsb-phlsb-bac-path-isolation-antimicrobial-resistance/resource/cc032b80-99f7-4116-8205-3e019829113b). The [original CSV](https://www.chp.gov.hk/files/misc/bac_path_isolation_and_antimicrobial_resistance_en.csv) is redistributed unchanged with attribution under the [DATA.GOV.HK Terms of Use, version 1.2](https://data.gov.hk/en/terms-and-conditions). Source ownership remains with the Government and relevant organisations.

The application restructures the annual 2020–2025 tables into 234 records, retaining raw cells, official percentages, reported organism totals and missing values. Drug resistance and marker positivity remain separate. Source hashes, coordinates and parsing rules are in [PHLSB metadata](datasets/phlsb-metadata.json); the project-owned parser uses MIT.

## European sewage ResFinder counts

Becsei A, Fuschi A, Otani S, et al. *Nature Communications* 15, 7551 (2024), [doi:10.1038/s41467-024-51957-8](https://doi.org/10.1038/s41467-024-51957-8). The checked article notice states [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/); no separate data licence was found in the workbook or article XML. These source terms are recorded separately from the application's MIT licence.

The application extracts factual counts and sample fields from Supplementary Data 1 and 3, indexed to the gene dictionary in Supplementary Data 5. Numeric parsing, ISO dates and the explicit alias/replica join preserve the source values. The original workbook, article figures and article prose are not bundled; the [official supplementary-file archive](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11364805/supplementaryFiles) remains available at its source. This research presentation is non-commercial. [Provenance](datasets/europe-provenance.json) · [Detailed source notice](datasets/europe-NOTICE.txt).

## Hong Kong community sewage study

Ding J and coauthors (2026). *Advanced Science* 13(20), e08389, [doi:10.1002/advs.202508389](https://doi.org/10.1002/advs.202508389). Copyright 2026 The Authors, published by Wiley-VCH GmbH. The article and its Supporting Information II workbook are provided under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The original workbook is bundled unchanged; Tables S1 and S2 are also parsed into JSON and CSV, retaining raw cell values and identifying normalized missing values.

The 189 QC identifiers are distinct from the paper's 190 collected samples and its Figure 1 analysis of 185 samples. The separate [PRJNA1207805 ENA index](https://www.ebi.ac.uk/ena/browser/view/PRJNA1207805) contains 406 run records and follows the [ENA/INSDC data-record policy](https://ena-browser-docs.readthedocs.io/en/latest/about/policies.html). No verified crosswalk was obtained between the archive aliases and QC identifiers. The [author processing repository](https://github.com/dingjiahui123/Sewage_ARG) has no explicit licence file and is linked only. [Full source and adaptation notice](datasets/hk-community-NOTICE.txt).

## Hospital Authority AMR and antimicrobial supply

The HA blood-culture key-findings tables and antimicrobial wholesale supply statistics come from the Centre for Health Protection / Department of Health, Hong Kong SAR Government. [HA source](https://www.chp.gov.hk/files/pdf/haamr_blood_key_findings2024.pdf) · [Supply source](https://www.chp.gov.hk/en/statistics/data/10/100044/6960.html) · [CHP copyright notice](https://www.chp.gov.hk/en/static/24027.html).

The checked CHP notice describes complete, unmodified copies for personal/internal non-commercial use and does not establish a general open-data licence for these adapted extracts. The application includes factual statistical values with source coordinates and attribution. Original reports, HTML, figures and prose are linked rather than bundled. Source rights remain separate from the project MIT grant. [HA notice](datasets/ha-NOTICE.txt) · [Supply notice](datasets/supply-NOTICE.txt).

## BV-BRC

The public experimental AST and genome metadata retain original identifiers, study references and response hashes. The [BV-BRC public-data policy](https://www.bv-brc.org/docs/system_documentation/data_management_sharing.html) states that public data are freely available without restriction on use. Cite BV-BRC and the original studies when using the records. Sequence files are linked through accession manifests; they are not mirrored in the application. [Dataset notice](datasets/bvbrc-NOTICE.txt).

## HKO rainfall and Flu Express

HKO daily rainfall is provided by the Hong Kong Observatory; Flu Express is provided by the Department of Health, Hong Kong SAR Government. Both resources are listed through DATA.GOV.HK and retain the [DATA.GOV.HK Terms of Use](https://data.gov.hk/en/terms-and-conditions). Attribution, original source links, hashes and field units accompany the parsed records. The original CSVs and Flu dictionary remain linked at their official sources. [Rainfall notice](datasets/rainfall-NOTICE.txt) · [Flu notice](datasets/flu-NOTICE.txt).

## Global Sewage 3

The fixed [Zenodo record 14652833](https://zenodo.org/records/14652833), DOI [10.5281/zenodo.14652833](https://doi.org/10.5281/zenodo.14652833), declares [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Source creators, version, original file checksums and the declared 16-sample extraction scope are retained. ENA sample/run records preserve their accession provenance under the [ENA/INSDC policy](https://ena-browser-docs.readthedocs.io/en/latest/about/policies.html). Large original count and sequence files remain external. [Dataset notice](datasets/global-sewage-NOTICE.txt).

## Plotly.js

Bundled standalone version: **3.1.1**. Distribution header: Copyright 2012–2025, Plotly, Inc. The complete version-specific upstream MIT license is included at `LICENSE-Plotly.txt`, preserving the upstream copyright statement. [Official tagged license](https://raw.githubusercontent.com/plotly/plotly.js/v3.1.1/LICENSE). Embedded dependency notices in the distribution are retained. Python-generated reports may use the Plotly version installed from the recorded Python dependencies; the packaging audit records the embedded report version separately.

## Font

Noto Sans SC is distributed under the SIL Open Font License 1.1; the application includes `assets/fonts/OFL.txt`. No Apple system font files are bundled. Browser/system font names in CSS refer to fonts available on the viewer's system.

## Maps and audiovisual media

Map source and provenance are recorded separately in `map-source.json` for the public website. Legacy Google tile mosaics, extracted outlines, and videos containing those legacy maps are excluded by the release allowlist. A separately regenerated video must be identified by its exact SHA256 before it can be added to a release.

Narration was supplied by the user, who authorized its use and publication in this project. The original generator/provider, creation date, and applicable service terms have not been documented. This notice records the available provenance and does not assign a new license to the recording. Newly rendered media are admitted by exact hash after source and visual checks; course acceptance of the existing narration and personal re-recording remain unconfirmed.

## Package scope

The public application and the Python course source package are separate artifacts. Sources and numerical results remain traceable to their frozen hashes. Historical internal logs and course full-text evidence are retained in the internal copy and excluded from public distribution. No license to third-party materials is implied by this notice.

## Project-owned code

The project-owned source code and documentation use the MIT License in `LICENSE`, as selected by the project owner on 3 November 2026. This grant does not replace the separate terms for third-party data, libraries, fonts, maps or media.
