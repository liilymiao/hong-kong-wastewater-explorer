# Data sources

Nine research datasets are loaded alongside the unchanged COVID-19 analysis. [The dataset manifest](research-datasets.json) records source identities, JavaScript hashes, units, observation counts and terms. [The COVID-19 manifest](source_manifest.json) retains its original 20 frozen source records.

| Source | Loaded scope | Measurement |
| --- | --- | --- |
| PHLSB outpatient | 234 annual records, 2020–2025 | Reported drug-resistant percentages and separate marker-positive counts. Organism totals retain their source meaning. |
| European sewage, PRJEB68319 | 235 biological samples × 554 genes, 2019–2021 | 130,190 raw ResFinder count cells. The sample matrix directly links to 235 runs; 274 runs are associated with those biological samples. |
| Hong Kong community sewage, PRJNA1207805 | 189 QC identifiers, two supplementary tables | Sequencing/assembly QC. The paper reports 190 collections; Figure 1 uses 185 samples. The 406-run ENA index remains separate. |
| HA blood-culture AMR | 175 annual records, 2020–2024 | Non-susceptibility percentages, Wilson confidence intervals, rounded/suppressed counts and coverage flags. E. coli hospital-onset and K. pneumoniae community/hospital-onset are available. |
| Antimicrobial supply | 444 sector/group/year records, 2014–2025 | DID: defined daily doses per 1,000 inhabitants per day. Human and veterinary scope remain distinct; 2025 is provisional. |
| BV-BRC | 15,777 experimental E. coli/ciprofloxacin AST records; 10,904 linked genomes | Source phenotypes and measurements. The conservative cohort includes 12,305 records in 10,495 identifier groups. Groups are not all proven independent isolates. |
| HKO rainfall | 2,830 daily HKO station records, 2019-01-01–2026-09-30 | mm. Trace remains an interval below 0.05 mm. The full source has 49,522 date-labelled rows from 1884; invalid 1900-02-29 is explicitly excluded. |
| Flu Express | 669 weeks, 2014W1–2026W43; 31 source columns | 27 clinical indicators with distinct count, proportion, per-1,000 and per-10,000 units. Blank values remain missing. |
| Global Sewage 3 v1 | First 16 distinct source identifiers; 17,402 reported count rows, 2,638 clusters | Raw aligned fragments. All rows for the selected identifiers were extracted from the checksum-verified complete source. ENA sample/run metadata provide dates and countries. |

The Global Sewage subset is a declared technical subset. Its Parquet geography table has no sample key and remains unlinked. Unlisted gene/sample combinations remain absent. The European and global raw counts use different methods and are not combined into a common abundance scale. No loaded source supplies a wastewater–clinical susceptibility pairing matrix.

Source-specific notices and metadata are in `datasets/`. Government and study materials retain their own terms; [MIT](LICENSE) covers project-owned code. [Third-party notices](THIRD_PARTY_NOTICES.md) record the separate conditions.

## Update or reproduce

Run from the downloaded `website` folder or the website repository root. The browser app needs no Python installation. Source updates require Python 3 and Node.js; HA, European and Global Sewage parsing additionally use `pdfplumber`, `openpyxl`, and `pandas`/`pyarrow`, respectively.

```sh
python3 -m pip install pdfplumber openpyxl pandas pyarrow
python3 scripts/adapters/run_all.py --dataset rainfall --refresh
python3 scripts/adapters/run_all.py --dataset all --refresh
```

Dataset keys: `phlsb`, `europe`, `hong-kong`, `ha`, `supply`, `bvbrc`, `rainfall`, `flu`, `global`. Omit `--refresh` to rebuild from cached original inputs. PHLSB's exact source is also bundled. Research originals downloaded by the runner remain under `work/data_sources/`; the source collection includes large Global Sewage files.

Each adapter runs in a staging folder. A parser failure retains that source's current website files; the runner reports the error and continues other requested sources. Successful updates rebuild the lightweight catalogue and dataset manifest. The result log is `work/last-update-status.json`. Updating local data does not publish a release.

The PHLSB, European and Hong Kong study adapters enforce the checked snapshot structure and known reconciliation counts. Changed schemas or scientific definitions require adapter review. The Flu adapter also checks the dictionary identity. Original units, missing codes and source metadata accompany every generated snapshot.

The COVID-19 models, Python component, media and existing scientific configuration are outside these updates. Rainfall alignment and annual AMR/supply comparisons provide contextual summaries; historical publication-availability validation remains separate.
