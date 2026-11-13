# Hong Kong Wastewater Explorer

Python **1.5.4** for release **v1.6.4**, scientific configuration **1.1**, frozen snapshot **23 October 2026**. This update removes the replay-week default warning and preserves the chosen week across navigation and language changes. The course workflow asks whether wastewater adds predictive information after recent clinical specimen positivity is known.

## Install once

Use Python 3.12 in a new directory:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
```

Installation needs the network. The included frozen inputs, results, course demonstration and origin recomputation run locally after installation. No data source is silently refreshed.

## Open the course application

```bash
.venv/bin/python launch.py --port 8501
```

Open `http://127.0.0.1:8501`. Course demo leads through the question, data, a real prediction trace, model comparison, patterns and export. The original analytical pages remain available. Stop the service with Ctrl+C; use another `--port` if needed.

The package includes sealed `outputs/` from the current source and unchanged numerical references in `saved_results/`. Start directly from the supplied results, or reproduce them in an independent directory:

```bash
.venv/bin/python scripts/reproduce_course.py --work-dir ../course-reproduction
.venv/bin/python -m pytest -q -k "not test_frozen_source_bytes_match_independent_catalogue"
.venv/bin/python scripts/check_report_links.py
```

The excluded test depends on internal source PDF/HTML archives that are intentionally absent from the distributable package. Tests for the included CSV bytes, calendar, numerical methods and temporal rules remain active. `scripts/reproduce_course.py` provides the isolated rebuild and row comparison; the destination must not already exist. To rebuild within an expendable copy, run `python -m src.pipeline --config config.yaml --stage all`. Current execution counts and differences are in STATUS.md. Historical test counts are not substituted for current runs.

On Windows, create the environment with `py -3.12 -m venv .venv` and replace `.venv/bin/python` with `.venv\Scripts\python.exe -X utf8`. This revision is tested on macOS; Windows is not execution-verified.

## Read and present

- [English report PDF](outputs/项目报告.pdf), [interactive HTML](outputs/项目报告.html) and [report text](outputs/项目报告.md)
- [Course workflow and closed-book practice](Course.md)
- [Detailed analysis contract](Methods.md)
- [AI assistance declaration](AI使用声明.md)
- [Current execution record](STATUS.md)
- [Data sources](Sources.md) and [third-party terms](THIRD_PARTY_NOTICES.md)

The report is generated from the actual result CSVs and includes the exact function/test mapping. Its target is PHLSB respiratory-specimen positivity, with error in percentage points. h2 means a monitoring-week offset. Raw predictions, output constraints, block-length intervals and post-hoc time-segment results are presented together.

The optional PDF can be regenerated after installing requirements-report.txt with `python scripts/build_report_pdf.py`. The generated HTML embeds its Plotly dependency for offline viewing. Custom submitted source is Python; the JavaScript public website is maintained separately.

Changing numerical/report-generator code requires rebuilding the full pipeline in an independent copy. Do not edit stage receipts or hashes to accept mixed artifacts. Do not overwrite the original frozen release. Moodle submission remains a separate student action.

Project-owned code and documentation use the [MIT License](LICENSE). Third-party materials retain their recorded terms.
