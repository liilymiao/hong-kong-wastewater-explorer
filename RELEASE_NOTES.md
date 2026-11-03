# v1.5.1 — research review and distribution update

The comparison view now places bounded and raw prediction performance together, with clipping counts, MAE/RMSE, block-length sensitivity, and downloadable evidence. New chronological-half and cumulative-gain charts describe the existing saved predictions; model parameters, frozen inputs, and scientific results remain unchanged.

The experience page exports the selected 2-, 4-, or 8-week interval consistently. Moving from the map to forecasts preserves the chosen week; a missing or unscored result remains explicit. Keyboard interactions, mobile navigation, and reduced-motion behavior have been updated.

The project introduction uses a newly drawn Natural Earth overview and the supplied narration, with eight selectable subtitle tracks and a separate English-caption video. Source records identify the map data and the available audio provenance. The original audio provider, creation date, and service terms remain unknown.

The public distribution excludes copied course material, extra CHP report PDFs, old Google mosaics and their videos, and internal logs containing personal-machine paths. It includes the full Plotly.js 3.1.1 MIT license. The separate Python course package contains Python source, frozen CSV inputs, and CSV reference results.

## Verification

The course package was unpacked and its complete Python pipeline ran successfully using the existing matching locked environment. Numeric values in all 26 reference CSVs matched the regenerated outputs exactly. The packaged-scope tests completed with **123 passed and 1 deselected**. The omitted test requires the intentionally excluded supporting PDF/HTML source archive; the unchanged full-suite trial recorded **123 passed and 1 failed** for that missing-archive condition. No fresh dependency installation was performed.

The experience interaction checks passed 25 cases, including all 12 horizon/scoring/block-length combinations. Science presentation checks passed 412 assertions in 16 states, and 2,052 independent arithmetic checks matched the saved CSVs. These automated JavaScript checks use a DOM harness and do not constitute visual browser inspection.

The supplied course requirements still need the student's own narration or an explicit course ruling, confirmation of the animated-screen format, and an honest record of personal contributions. Full historical as-of evaluation, new sampling-regime confirmation, prospective warning validation, and real-user testing remain future work.
