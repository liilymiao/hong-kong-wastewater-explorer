Global Sewage 3: bounded, verified count query

Fixed upstream dataset: https://doi.org/10.5281/zenodo.14652833
Licence: Creative Commons Attribution 4.0 (see global-sewage-NOTICE.txt).

Build from preserved original files:
  python3 scripts/adapters/global_sewage_adapter.py

Retrieve/verify the fixed version and rebuild:
  python3 scripts/adapters/global_sewage_adapter.py --refresh

Dependencies are pandas and pyarrow. A local work/adapter-deps directory is
automatically added to the Python path if present. The script accepts an explicit
--sample-limit from 1 to 100; the published snapshot uses 16.

The adapter verifies the original Zenodo file sizes and MD5 for gs3.parquet,
tot_counts.csv and the entire counts_clusters.csv. It reads the actual Parquet
schema and scans every count row. The default subset selects the first 16
distinct complete_name identifiers in fixed source-file order, then retains ALL
of their matching rows across the complete file. This is a reproducible browsing
subset, not a representative global cohort.

Linkage:
  counts_clusters.complete_name = tot_counts.complete_name
  unique tot_counts.sample_name = ENA run_accession
  ENA run sample_accession = ENA sample XML

The repeated bindCol rows in tot_counts are collapsed by exact run, complete_name
and total_fragments tuple. They never increase sequencing depth or sample count.
All selected runs and sample XML collection dates are checked. FASTQ URLs and MD5
values are kept in the sequence manifest; FASTQ files are not downloaded.

gs3.parquet is a geography table without a sample key. Its 524 source records are
read and retained separately. The author notebook's metadata_fixed.csv is not
one of the Zenodo files, and the checked repository-relative path returned 404.
The published subset uses directly linked ENA country/date/accession fields.
City stays missing; no geography record is assigned without a valid sample key.

Displayed values are integer fragmentCountAln, in aligned fragments. PanRes 98%
cluster identifiers are preserved as gene labels. The upstream adjusted fields
are retained as exact text, without a new normalization calculation. Absent
sample/cluster pairs remain absent, not zeros. This release does not infer
copies/L, relative abundance, risk or clinical phenotype from the counts.

Public contract:
  window.EXT_GLOBAL_DATA.meta: source manifest, scope, terms and field definitions
  rows: selected sample/cluster/group count observations with source CSV row
  samples: the selected sample records and exact linkage evidence
  sequence_manifest: ENA FASTQ URLs and MD5 values
  geography: original scalar Parquet geography fields, explicitly unlinked
  excluded: empty; all reported rows for the chosen identifiers are retained

Original data stay in work/data_sources/global-sewage. Large panres_counts.csv
and motus_counts.zip remain external. The 124 MB complete cluster-count file is
used offline and is not copied into the browser site. File hashes and capture
times are in global-sewage-provenance.json. Verification is recorded in
qa/global-sewage-verification.json and qa/global-sewage-runtime-risk-tests.json.
