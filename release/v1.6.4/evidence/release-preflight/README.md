# Release preflight, 13 November 2026

The reconstructed Python 1.5.4 course archive was extracted and tested again. Its 137 manifest files verified, **158 tests passed**, and the same one internal-archive test was deselected. The command, exact package SHA256, exit code, JUnit and post-test package identity are in `course-release-execution.json`. This run reused the Python 3.12.14 environment installed on 11 November; it does not claim another clean installation. All 35 Python source files and 78 scientific/configuration/result/reference assets remain identical to the accepted candidate, recorded in `course-release-protected.json`.

After the website version labels and distribution metadata were updated to 1.6.4, the actual render/export Node suite passed again: **11,349 assertions**, 15 same-count mutation cases, 8 original scopes and 12 interval states. `website-release-execution.json` binds the resulting log and current source files. Exit code 0 was observed by the executing agent. No unrecorded start time or duration is supplied.

Fresh tests here are separate from the dated full scientific rebuild and real WebKit checks in the parent folders. No model fitting, scientific parameter change or new data import occurred in release preparation. Final public asset SHA256 values are also listed in the release's `SHA256SUMS.txt`.

## Export metadata follow-up

Live release QA found an export software-version label still set to 1.6.3. The two export/query constants and their script cache keys were updated to 1.6.4; the Node suite then passed all 11,349 assertions again. `website-export-version-execution.json` binds the final files and follow-up log. The earlier preflight record remains unchanged as historical evidence.
