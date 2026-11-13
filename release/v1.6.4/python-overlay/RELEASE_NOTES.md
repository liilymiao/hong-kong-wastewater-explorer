# Python 1.5.4

Prepared for release v1.6.4 on 13 November 2026.

The historical-week selector now initializes a single valid value, removing Streamlit's competing default/session-state warning. A selected valid week remains selected after page navigation and language switching. A new regression covers the course entry, week selection, navigation, language switching and analysis-range changes.

The executable source is identical to the candidate accepted on 11 November: 158 applicable tests passed, with the one undistributed-source-archive test explicitly deselected. The independent reproduction of the actual v1.6.3 base package matched all 26 CSVs and 108,164 numeric cells; this UI patch preserves the scientific configuration, source and results byte for byte. Real WebKit checks covered the warning fix and selected-week preservation.

Python 1.5.3 added the Course demo, real historical-origin computation, English report and portable reproduction workflow. Those functions remain included. STATUS.md distinguishes base-package evidence from candidate acceptance.
