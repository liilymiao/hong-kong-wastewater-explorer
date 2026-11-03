BV-BRC E. coli / ciprofloxacin experimental AST

Build from the preserved public API responses:
  python3 scripts/adapters/bvbrc_adapter.py

Retrieve a new snapshot, validate pagination and rebuild:
  python3 scripts/adapters/bvbrc_adapter.py --refresh

The adapter uses Python's standard library. The browser loads bvbrc-data.js on
demand. Column encoding is expanded into ordinary flat object arrays at load time.
No remote API request is made by the browser.

Public data contract
  window.EXT_BVBRC_DATA.meta: source manifest, terms, definitions and counts
  rows: all original experimental AST records plus explicit derived quality flags
  samples: one metadata row per linked genome, including stable sample_group_id
  sequence_manifest: public accessions and documented explicit-FTPS FASTA paths
  excluded: original record IDs and conservative-cohort exclusion reasons

The exact query is taxon_id=562, antibiotic=ciprofloxacin and
evidence=Laboratory Method. API paging uses limit(page_size, offset), ordered by
id. Every original measurement, sign, value and unit is preserved. No missing
label is inferred from a numeric concentration and no breakpoint is applied.

MIC requires a numeric mg/L result and MIC or a dilution method. Disk diffusion
with mg/L is a source method/unit conflict. These records remain visible and are
not included by the method-verified MIC filter. Censored signs remain attached to
values; this snapshot does not turn them into exact training targets.

Exact BioSample, SRA and assembly identifiers connect genome versions into
sample groups. Genome-ID fallbacks remain unresolved identities. These groups
support downstream separation of related records; their number is not a claim
that all entries are independent biological isolates. Original repeated
experiments remain in rows. Duplicate AST payloads, conflicting S/I/R groups,
missing sequence accessions and unusable labels have explicit exclusion reasons.

Collection dates retain source precision. If collection_year is absent, a year
is extracted only from YYYY, YYYY-MM or YYYY-MM-DD collection_date. A YYYY-YYYY
range keeps collection_year missing and supplies year_start/year_end. The
raw_collection_year and collection_year_basis fields record the distinction;
samples retains all original metadata.

Source responses remain in work/data_sources/bvbrc, outside the public site.
bvbrc-provenance.json records the SHA256 of each response, URL and capture time.
The primary source_sha256 is the hash of the canonical source manifest. The
source version combines the retrieval date and manifest-hash prefix.

Sequence contents are not mirrored. The manifest provides public accessions and
the BV-BRC documented FTP path, which requires explicit TLS (FTPS). Individual
FASTA file downloads have not been verified.

Verification reports: qa/bvbrc-verification.json and
qa/bvbrc-runtime-risk-tests.json. Public use terms are in bvbrc-NOTICE.txt.
