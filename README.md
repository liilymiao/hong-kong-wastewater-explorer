# Hong Kong Wastewater Explorer

[Open the website](https://liilymiao.github.io/hong-kong-wastewater-explorer/) · [Download the complete project](https://github.com/liilymiao/hong-kong-wastewater-explorer/releases/latest) · [Watch the proposal](https://liilymiao.github.io/hong-kong-wastewater-explorer/proposal.mp4)

Explore whether wastewater adds predictive value to forecasts based on recent clinical history.

The website provides four views:

- **Monitoring overview:** weekly clinical positivity and wastewater trends, a project introduction, and CSV exports.
- **Historical replay:** historical forecast origins, target dates, model predictions, and observed results.
- **Model comparison:** matched test weeks, forecast horizons, scoring views, and sensitivity results.
- **Patterns & anomalies:** signal combinations, historical neighbours, and unusual observations.

The interface opens in English. One button switches to Chinese while preserving selections. The introduction has English narration and selectable English, Simplified Chinese, Traditional Chinese, Cantonese, Japanese, Korean, Spanish, and French subtitles.

## Data and methods

The frozen Department of Health monitoring snapshot contains 194 weekly records from 2023 to 2026, including two missing wastewater observations. The forecast target is clinical specimen positivity. The primary horizon is two monitoring weeks after the latest observed week.

The website displays saved retrospective results. It includes ridge-regression forecasts, K-means groups, and Local Outlier Factor results from the reproducible Python project. Source definitions and evaluation details are available inside the application and complete project download.

## Files

The website runs directly in the browser using the files in this repository. The release download includes the Python application, frozen data and results, methods, editable slides, video, subtitles, and verification records.

Photo sources are listed in `CREDITS.txt`. `source_manifest.json` maps the website data to the frozen analysis files.

Created by [liilymiao](https://github.com/liilymiao).
