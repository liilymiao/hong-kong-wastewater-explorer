# Release acceptance evidence

This compact archive preserves the executed **11 November 2026** acceptance records and the **13 November 2026** release preflight for release 1.6.4. The original package and local candidate are distinguished below. Release packaging on 13 November updates version labels and distribution documentation; current asset identities are recorded in `release/v1.6.4/release.json` and the release's `SHA256SUMS.txt`. The November 11 records remain historical evidence, including their local-candidate status and original tested-file hashes. Fresh release-package records are in `release-preflight/`.

## Results

| Scope | Executed result | Evidence |
| --- | --- | --- |
| Downloaded v1.6.3 course package | Fresh Python 3.12.14 environment; 42 applicable locked dependencies; 157 tests passed, one deselected | `python/python-execution.json`, `python/python-pytest.xml`, installation and environment logs |
| Independent published-package AppTest | 38 passed | `python/python-apptest.xml` |
| Scientific rebuild | 26 CSVs, 8,173 rows and 108,164 numeric cells reproduced exactly against references and published outputs | `python/python-file-comparison.csv`, `python/python-reference-comparison.json`, `python/python-published-output-comparison.json` |
| Replay-selector candidate | 158 tests passed, one deselected; 39 UI tests passed | `python/candidate/python-candidate-full-execution.json` and JUnit files |
| Website content fingerprint | 11,349 assertions passed, 15 same-count mutation cases; 3,952 original exported rows retained their numerical values | `fingerprint/comparison-fingerprint-tests.json` |
| Published Python real-browser route | 51 assertions, 16 actual CSV downloads; 12 horizon/scoring/block combinations | `browser/course-browser-results.json`, `browser/downloads/` |
| Plotted values and hover | 18 assertions; 480 error values and dates checked across h1/h2 and raw/clipped | `browser/plot-browser-results.json` |
| Fresh Python candidate browser | 7 assertions, including week retention and real recomputation | `browser/candidate-course-results.json` |
| Deployed website / final local website | 15 assertions and 5 CSVs / 24 assertions and 7 CSVs | `browser/website-browser-results.json`, `browser/final-candidate-browser-results.json` |
| Final candidate archive | Manifest/hash checks and 4 extracted-package regression tests passed | `packaging/final-package-verification.json` |

The exact original published `course-python.zip` SHA256 is `1ee1825bcd3318441b263ed40dbcf869bb6091d1a6ec5e3a1d0cf54166369ef6`. Its 137 manifest entries remained unchanged. The candidate retained all 78 data, configuration, reference and result files. Reproduction changed six future-projection generation timestamps, with zero changed numeric cells. The English report was rendered and all seven pages inspected; `packaging/report-review.json` records this review.

The single deselected test is `tests/test_acceptance.py::test_frozen_source_bytes_match_independent_catalogue`. It depends on internal original PDF/HTML archives absent from the public package. Tests for the distributed CSVs, temporal rules, algorithms and application remain active. No failure or skip is represented as a passed test.

## Browser and offline scope

Browser checks used background **WebKit 26.5 with Playwright 1.62.1 on macOS**, separate from Node DOM and Streamlit AppTest. The installed Safari application was not operated. Actual chart arrays, hover text and downloaded CSV values were checked; browser screenshots and the full exploratory harness logs remain in the complete local November 11 archive and are omitted from this compact download.

Offline checks blocked external browser requests and Python socket/DNS calls while retaining localhost. Fresh course loading, charts, single-origin recomputation and download succeeded after dependencies were installed. The operating system network remained enabled. `browser/offline-guard-selftest.json` records the guard test. A timed spoken rehearsal, projector choice and installed Safari check are personal demonstration tasks.

A synthetic same-count change was made only in browser memory: the current MAE was recalculated, the old interval became unavailable, and the downloaded predictions' absolute errors, squared errors, clipping flag, empty paired-set ID and content fingerprint matched the modified values. The retained synthetic CSVs are software-test outputs, not new scientific observations.

The attachment's original snippet loader omitted a dependency and failed before reaching the case. `fingerprint/followup-loader-fixed.cjs` adds that dependency. With this loading correction, the original strict check failed on stale intervals and passed on the candidate; the 25 existing boundary assertions remained passing. The application was additionally checked using actual render/export functions and a real browser.

## Reading or rerunning the records

Execution JSON files preserve commands, exit codes, timing, environment and tested hashes. `python/` and its candidate subdirectory retain raw-versus-portable hash maps; `historical-copy-provenance.json` covers the other selected copies. Host directory prefixes and XML hostnames were normalized for distribution. No scientific values or test outcomes were changed.

The browser scripts retain their recorded ports and placeholder installation paths. Configure those paths and start the documented local servers before rerunning; generate `expected.json` with `browser/make_expected.py` from the original published course outputs. Browser downloads are actual files from the recorded runs. Scientific reproduction is available through the course package's `scripts/reproduce_course.py`; website integrity checks use `node tests/comparison-fingerprint.cjs`.
