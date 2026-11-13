# Course replay selection patch

A real-browser check of the published package revealed Streamlit's duplicate-default warning when Course demo opened a historical forecast. The course action had already set `replay_anchor`, while the selectbox supplied a separate non-default index.

The local `course-candidate` initializes a valid current or restored anchor, selects the latest available week when a changed split invalidates that anchor, then renders the selectbox with `index=None`. The bilingual wrapper is unchanged.

The new regression fails on the published implementation with the same warning and passes after the patch. It covers course h1/raw to replay, week selection, leaving and returning to the page, both language directions, and validation/future/test split transitions. The full UI subset now passes 39 tests (17.82 seconds). A subsequent complete applicable suite passes 158 tests with one internal-archive test explicitly deselected; see python-candidate-full-execution.json and JUnit for command, timings and exact tested source hashes. Streamlit's process-wide one-warning flag is reset only in the regression test so earlier tests cannot hide this defect.

Only `app.py` and `tests/test_course_demo.py` changed. All 78 data, output, saved-reference and configuration files are byte-identical. The original downloaded course's 137 manifest entries remain unchanged. Candidate release metadata has not been resealed or published; integration will update its distribution manifest. Scientific result receipts remain valid.

Before/after logs, JUnit and exact commands are in `python-candidate-tests.json`. Actual-browser acceptance is recorded separately.
