# Third-party notices

## Government surveillance data

Source and ownership: Department of Health, Government of the Hong Kong Special Administrative Region; supplied through DATA.GOV.HK. [Dataset](https://data.gov.hk/en-data/dataset/hk-dh-chpsebcddr-covid-express) · [DATA.GOV.HK terms](https://data.gov.hk/en/terms-and-conditions).

The dataset page explicitly lists `covidx_data.csv` and the data dictionary `covidx_spec_en.pdf`. This relationship was checked on 3 November 2026. The public package uses frozen CSV data and its source metadata with attribution. DATA.GOV.HK terms cover the resources supplied through that portal; a link to another site does not establish that all materials on that site share those terms. Extra CHP weekly reports and copied course materials are excluded from the release packages. Their source links, hashes, and purpose are retained in `release_sources.json`. The dictionary is also linked rather than copied to keep the package small.

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
