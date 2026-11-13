# Python 1.5.4 release acceptance

This Python 1.5.4 component is prepared for release v1.6.4 on 13 November 2026 from the UI candidate accepted on 11 November. It is based on the actual v1.6.3 release course-python.zip (Python component 1.5.3). The downloaded original archive and its extracted files remain unchanged. Original package SHA256: 1ee1825bcd3318441b263ed40dbcf869bb6091d1a6ec5e3a1d0cf54166369ef6.

The actual published package was installed in a new Python 3.12.14 environment with all 42 applicable locked dependencies. Its full applicable suite passed 157 tests; one archive-dependent test was explicitly deselected. A separate AppTest run passed 38 tests. Rebuilding in another directory reproduced 26 CSVs, 8,173 rows and 108,164 numeric cells exactly against both bundled references and published outputs. Only six future-projection generation times changed in the rebuilt copy.

A real WebKit browser found Streamlit's replay_anchor default/session-state warning on the course-to-replay route. The 1.5.4 implementation initializes one valid week and renders the selector without a competing default. Its new regression fails on the published implementation and passes here. Candidate UI checks passed 39 tests; the full applicable candidate suite passed 158 tests, with one deselected, in 39.97 seconds. The two changed Python files are app.py and tests/test_course_demo.py. All 78 data, configuration, reference and result files remain byte-identical.

Exact excluded test: tests/test_acceptance.py::test_frozen_source_bytes_match_independent_catalogue. It requires internal original PDF/HTML archives absent from distribution. All included CSV integrity and scientific tests remain active.

The accompanying acceptance bundle records actual commands, exit codes, environment, JUnit XML, per-file comparisons, package hashes, browser screenshots and downloaded CSV checks. Node DOM, Streamlit AppTest and real WebKit results are recorded separately. WebKit runs headlessly on the demonstration Mac and is not a claim of manual testing in the Safari application. Offline verification blocks external requests while keeping localhost available; it does not change the computer's network settings.

The English report and scientific source are unchanged. Seven report pages were rendered and inspected again. The student still needs a timed personal rehearsal, closed-book practice and confirmation of personal AI disclosure and course submission arrangements. The release packaging adds version and distribution metadata only. Moodle submission remains a separate student action.
