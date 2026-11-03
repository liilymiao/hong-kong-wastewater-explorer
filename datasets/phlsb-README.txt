PHLSB outpatient antimicrobial resistance · 2020–2025

Source: Department of Health, Hong Kong SAR Government, via DATA.GOV.HK.
https://www.chp.gov.hk/files/misc/bac_path_isolation_and_antimicrobial_resistance_en.csv
https://data.gov.hk/en-data/dataset/hk-dh-dh_phlsb-phlsb-bac-path-isolation-antimicrobial-resistance/resource/cc032b80-99f7-4116-8205-3e019829113b

phlsb-source.csv is the byte-identical official download. phlsb-long.csv and phlsb.json are derived annual long tables. phlsb.js exposes the same object as window.PHLSB_DATA.

One row represents a year, specimen type, organism and drug or resistance marker. Drug R and marker-positive results are separate. The official percentages and No. organism totals are retained; the totals are not independently verified drug-specific AST denominators. Count-only markers have null reported_percent, and dashes remain missing.

The provider updates the resource quarterly; observations in this snapshot are annual. Raw values, symbols, source row/column coordinates and SHA256 accompany each record. Details and transformation rules are in phlsb-metadata.json.

Source terms: https://data.gov.hk/en/terms-and-conditions
Reproduce the long table with: python3 phlsb-parser.py --source phlsb-source.csv --metadata phlsb-metadata.json --out regenerated --report regenerated/verification.json

Project-owned parser and interface: MIT. Source-data ownership remains with the Government and relevant organisations.
