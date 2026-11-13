# Comparison result identity

The comparison page uses one validated result object for its metrics, charts, diagnostic tables and CSV downloads. `comparison_fingerprint` identifies the comparison split, horizon and score mode, fixed model names, source rows, source metadata, full analysis and frozen configuration, and the sorted normalized input and accepted prediction records. Prediction records retain their source/evaluation versions, origin and target dates, observed values, raw predictions and bounded predictions. Row order does not affect identity.

`comparison-manifest.js` records the reviewed fingerprints and a separate SHA-256 of each saved metrics, paired-error, stage and bootstrap payload. All eight test/validation × h1/h2 × raw/clipped scopes are sealed. The manifest also records the SHA-256 of the unchanged `data.js`. It is generated deliberately at build time; rendering does not create or refresh a seal.

Before using saved results, `reviewDiagnostics()` verifies both content identities. Successful rows carry `saved_match: true`. A mismatch recomputes descriptive MAE/RMSE and paired errors from the current eligible records, sets `saved_match: false`, retains an empty `paired_set_id`, and leaves confidence limits unavailable. No replacement bootstrap interval is calculated in the browser. Empty, duplicate and inconsistent-observation rules continue to apply.

The frozen scientific data and saved numerical arrays are unchanged. The new sidecar contains deterministic integrity metadata. It binds the reviewed payloads; it does not represent new model fitting, data retrieval or independent source authentication.

## Checks

```sh
node tests/comparison-fingerprint.cjs
```

The test compares the actual page/render/export functions with the preserved MIT-licensed v1.6.3 app fixture. It covers unchanged result scopes, all 12 final-test interval settings, same-count input mutations, saved-result tampering, source/configuration changes, row reordering, missing proof, post-load mutation and the existing exclusion rules. SHA-256 is checked against Node's independent crypto implementation, including Unicode and multi-block inputs. Node DOM checks and real-browser checks are reported separately.

For a deliberately reviewed new snapshot, regenerate the manifest with:

```sh
node scripts/build-comparison-manifest.cjs
```

The builder accepts only the reviewed `data.js` SHA-256 and fails before writing when it differs. A new scientific snapshot requires an explicit update to that reviewed-source contract. Do not run this command to make an unexpected mismatch disappear. Review the input/configuration and saved-result changes first. The fixture `tests/fixtures/app-v1.6.3.js` is the exact `app.js` from commit `880ce2e8e9e9c558cd1d857e348c5d06f50612e8`.
