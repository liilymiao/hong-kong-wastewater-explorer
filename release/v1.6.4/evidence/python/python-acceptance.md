# Published Python course package acceptance

Executed on 11 November 2026 against the actual downloaded [v1.6.3 course-python.zip](https://github.com/liilymiao/hong-kong-wastewater-explorer/releases/download/v1.6.3/course-python.zip). This record describes a new execution; previous pre-publication logs are identified separately in `python-prior-evidence-index.json`.

## Package and environment

- ZIP size: 9,746,184 bytes; SHA256: `1ee1825bcd3318441b263ed40dbcf869bb6091d1a6ec5e3a1d0cf54166369ef6`.
- ZIP CRC and complete inventory passed: 138 files; all 137 manifest entries verified before and after execution.
- A new isolated virtual environment used Python 3.12.14 on macOS arm64. All 42 applicable exact locked dependency versions matched; `pip check` passed. Pip reused its distribution download cache where available; no existing virtual environment was reused.
- First installation used a network-enabled environment. Browser/network-blocked demonstration results are documented separately.

## Current execution results

The applicable suite passed **157 tests**, with **0 failures, 0 errors and 0 skips**. One collected test was explicitly deselected:

`tests/test_acceptance.py::test_frozen_source_bytes_match_independent_catalogue`

It requires original supporting PDF/HTML archives omitted from public distribution. The included CSV, numerical, temporal and application tests remained active. The console reported 38.46 seconds; JUnit contains per-test execution records. The separately executed AppTest subset passed **38 tests** in the console-reported 16.88 seconds, including the 12 horizon/scoring/block combinations. This does not substitute for a real browser.

The full pipeline ran in a separate reproduction directory. Both comparisons passed: bundled `saved_results/` versus regenerated outputs, and the published package's `outputs/` versus regenerated outputs. Each covered **26 CSVs, 8,173 rows and 108,164 numeric cells**, with **zero numerical changes**. Stable row identities and other text values matched. Six unscored future projections contain the new actual generation timestamp; those timestamp changes are explicitly recorded. Original extracted package files remained unchanged.

| Command record | Exit code | Process seconds | Log |
| --- | ---: | ---: | --- |
| python-create-venv | 0 | 1.857 | python-create-venv.log |
| python-install | 0 | 20.113 | python-install.log |
| python-pip-check | 0 | 0.296 | python-pip-check.log |
| python-environment | 0 | 0.106 | python-environment.log |
| python-collection | 0 | 7.882 | python-collection.log |
| python-pytest | 0 | 39.047 | python-pytest.log |
| python-report-links | 0 | 0.068 | python-report-links.log |
| python-reproduction | 0 | 8.383 | python-reproduction.log |
| python-apptest | 0 | 17.261 | python-apptest.log |

## Reproduce the checks

From the extracted course directory, with the locked dependencies installed:

```bash
python -m pytest -q -k "not test_frozen_source_bytes_match_independent_catalogue" --junitxml=../python-pytest.xml
python scripts/check_report_links.py
python scripts/reproduce_course.py --work-dir ../new-reproduction
python -m pytest tests/test_app.py tests/test_app_review.py tests/test_i18n.py tests/test_course_demo.py -q --junitxml=../python-apptest.xml
python -m pip check
```

The reproduction destination must not already exist. It runs the complete pipeline and row comparison without overwriting the original package. Exact commands, working directories, timestamps, exit codes and logs are in `python-execution.json`; this summary does not treat publication CI as a scientific test run.

## Evidence files

`python-evidence-binding.json` binds the package SHA256 to JUnit, environment and per-file comparison records. `python-file-comparison.csv` is the compact per-file result. The report-link check verifies bundled link structure, not live external source availability. The published English report, method mapping and student confirmation items are delivered separately with the final acceptance package.

`python-readable/` contains portable copies with local directory prefixes replaced by `AUDIT_ROOT` / `PYTHON_RUNTIME` and JUnit hostnames removed. `portable-evidence-manifest.json` records the SHA256 of each raw original and its portable copy. Raw local evidence remains intact. No repository, tag or release asset was changed by this verification.
