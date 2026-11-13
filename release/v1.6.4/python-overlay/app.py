"""Local, offline view of the saved monitoring analysis.

Views read saved outputs. The optional origin reproduction calls the existing
Python analysis functions with frozen parameters and never writes analysis files.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from i18n import st, language, toggle_language, restore_widget_values, display_frame, display_figure
import yaml

from src.artifacts import ArtifactError, verify_artifacts
from src.course_trace import saved_feature_evidence, lag_observations, reproduce_origin
from home_video import render_home_video


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs"
APP_CONFIG: dict = {}
ARTIFACT_METADATA: dict = {}
MODEL_NAMES = {
    "persistence": "持续性基线",
    "clinical_ridge": "临床岭回归",
    "combined_ridge": "临床＋污水岭回归",
}
MODEL_COLORS = {"persistence": "#8C91A1", "clinical_ridge": "#3F6EC7", "combined_ridge": "#00887A"}
SPLIT_NAMES = {"test": "2026 最终测试", "validation": "2025 开发／验证", "future": "快照末端未评分"}
PAGES = ["课程演示", "监测概览", "历史回放", "模型比较", "状态与异常"]
SCORE_NAMES = {"clipped": "限制到 0–100%（主评分）", "raw": "原始预测（未限制）"}
FEATURE_NAMES = {
    "p": "阳性比例（%）",
    "p_change_2w": "两周阳性比例变化（百分点）",
    "log1p_w": "污水 log(1＋w)",
    "log1p_w_change_2w": "两周污水 log(1＋w) 变化",
}


class OutputDataError(ValueError):
    """A saved output cannot safely support the selected view."""


REQUIRED_COLUMNS = {
    "clean.csv": {"Year", "From", "To_corrected", "week_key", "source_version", "SARSCoV2_proportion", "Sewage_viralload"},
    "predictions.csv": {
        "run_id", "backtest_mode", "source_version", "evaluation_vintage", "issue_at",
        "anchor_year", "anchor_week", "anchor_from", "anchor_to", "target_year", "target_week",
        "target_from", "target_to", "horizon", "model_id", "prediction", "raw_prediction",
        "observed", "abs_error_pp", "raw_abs_error_pp", "n_train", "lambda", "status", "split",
    },
    "metrics.csv": {"split", "horizon", "model_id", "n_origins", "mae_pp", "rmse_pp", "delta_mae_pp", "relative_gain_pct", "n_clipped"},
    "patterns.csv": {"week_key", "source_version", "issue_at", "cluster_id", "cluster_label", "cluster_k", "lof_score", "lof_k", "n_reference", "reference_start", "reference_end", "status", "p_change_2w", "log1p_w_change_2w"},
    "pattern_centers.csv": {"query_week_key", "cluster_id", "cluster_label", "n_members", "p_center", "p_change_2w_center", "w_center"},
    "pattern_neighbors.csv": {"query_week_key", "lof_k", "neighbor_rank", "neighbor_week_key", "distance"},
    "pattern_sensitivity.csv": {"week_key", "lof_k", "lof_score"},
    "bootstrap_sensitivity.csv": {"split", "horizon", "low", "high", "block_weeks"},
    "stage_metrics.csv": {"split", "horizon", "stage_label", "n_origins", "clinical_mae_pp", "combined_mae_pp", "delta_mae_pp"},
}


def validate_columns(frame: pd.DataFrame, name: str, *, allow_empty: bool = False) -> pd.DataFrame:
    schema_name = name.removeprefix("raw_")
    missing = REQUIRED_COLUMNS.get(schema_name, set()) - set(frame.columns)
    if missing:
        raise OutputDataError(f"{name} 缺少必需字段：" + "、".join(sorted(missing)))
    if frame.empty and not allow_empty:
        raise OutputDataError(f"{name} 没有可显示的记录")
    return frame


def calendar_chart_frame(frame: pd.DataFrame, date_column: str = "From") -> pd.DataFrame:
    """Keep weekly gaps explicit after filtering; exports retain selected rows only."""
    if frame.empty:
        return frame.copy()
    ordered = frame.sort_values(date_column).copy()
    if ordered[date_column].duplicated().any():
        raise OutputDataError(f"图表日期 {date_column} 出现重复记录")
    calendar = pd.date_range(ordered[date_column].min(), ordered[date_column].max(), freq="7D")
    return ordered.set_index(date_column).reindex(calendar).rename_axis(date_column).reset_index()


def scoring_columns(score_mode: str) -> tuple[str, str]:
    if score_mode not in SCORE_NAMES:
        raise OutputDataError(f"未知评分视角：{score_mode}")
    return ("raw_prediction", "raw_abs_error_pp") if score_mode == "raw" else ("prediction", "abs_error_pp")


def metrics_for_block(metrics: pd.DataFrame, intervals: pd.DataFrame, block: int) -> pd.DataFrame:
    """Attach the selected saved interval to the same paired metric records."""
    result = metrics.copy()
    result["block_weeks"] = block
    for col in ["delta_ci_low_pp", "delta_ci_high_pp"]:
        result[col] = np.nan
    chosen = intervals.loc[intervals.block_weeks == block] if not intervals.empty else intervals
    if chosen.empty:
        result["bootstrap_status"] = "unavailable"
        return result
    if len(chosen) != 1 or result.paired_set_id.nunique() != 1 or chosen.iloc[0].paired_set_id != result.iloc[0].paired_set_id:
        raise OutputDataError("时间块区间与当前比较集合不一致")
    interval = chosen.iloc[0]
    if not result.n_origins.eq(interval.n_origins).all():
        raise OutputDataError("时间块区间与当前比较集合不一致")
    combined = result.model_id == "combined_ridge"
    result.loc[combined, "delta_ci_low_pp"] = interval.low
    result.loc[combined, "delta_ci_high_pp"] = interval.high
    for target, source in [("bootstrap_blocks", "n_blocks"), ("bootstrap_status", "status"),
                           ("bootstrap_n_covered", "n_covered"), ("bootstrap_n_uncovered", "n_uncovered"),
                           ("bootstrap_confidence_level", "confidence_level")]:
        result[target] = interval[source]
    return result


def show_output_error(exc: Exception) -> None:
    st.error(f"本地分析产物无法一致读取：{exc}")
    st.write("请在项目目录重建完整分析产物，再刷新页面：")
    st.code("python -m src.pipeline --config config.yaml --stage all", language="bash")


def percent(value: float, digits: int = 2) -> str:
    """A proportion is multiplied by 100 once, at the display boundary."""
    return "暂无" if pd.isna(value) else f"{100 * float(value):.{digits}f}%"


def pp(value: float, digits: int = 3) -> str:
    """Saved errors already use percentage points; do not multiply again."""
    return "暂无" if pd.isna(value) else f"{float(value):.{digits}f}"


def date_text(value: object) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    return "暂无" if pd.isna(parsed) else parsed.strftime("%Y-%m-%d")


def hkt(value: object) -> pd.Timestamp:
    parsed = pd.Timestamp(value)
    return parsed.tz_localize("Asia/Hong_Kong") if parsed.tzinfo is None else parsed.tz_convert("Asia/Hong_Kong")


def timing_for_row(row: pd.Series, delay_days: int | None) -> dict:
    """Compute actual calendar relationships without relabeling a prediction.

    The configured issue time is 23:59 HKT. +7 days after a Saturday end is
    still Saturday; +8 begins the h2 target and requires h3 for a future week.
    """
    anchor_start = hkt(row["anchor_from"]).normalize()
    issue = hkt(row["issue_at"]) if delay_days is None else hkt(row["anchor_to"]).normalize() + pd.Timedelta(days=delay_days, hours=23, minutes=59)
    target_start = hkt(row["target_from"]).normalize()
    dynamic_h = 1
    while anchor_start + pd.Timedelta(weeks=dynamic_h) <= issue:
        dynamic_h += 1
    dynamic_start = anchor_start + pd.Timedelta(weeks=dynamic_h)
    return {
        "display_issue_at": issue.isoformat(),
        "delay_days": delay_days,
        "timing_source": "saved_run_time" if delay_days is None else "hypothetical_delay",
        "target_started": bool(target_start <= issue),
        "next_future_from": dynamic_start.date().isoformat(),
        "next_future_to": (dynamic_start + pd.Timedelta(days=6)).date().isoformat(),
        "next_future_horizon": dynamic_h,
        "dynamic_prediction_available": dynamic_h in (1, 2),
    }


def filter_predictions(frame: pd.DataFrame, split: str, horizon: int, anchor: str | None = None) -> pd.DataFrame:
    selected = frame.loc[(frame["split"] == split) & (frame["horizon"] == horizon)].copy()
    if anchor is not None:
        selected = selected.loc[selected["anchor_key"] == anchor].copy()
    return selected.sort_values(["anchor_from", "model_id"]).reset_index(drop=True)


def csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8-sig")


@st.cache_data(show_spinner=False)
def read_csv(path: str, modified_ns: int, content_sha256: str = "") -> pd.DataFrame:
    # The verified digest also invalidates a restored file with a preserved mtime.
    del modified_ns, content_sha256
    return pd.read_csv(path)


def read_saved_csv(path: Path) -> pd.DataFrame:
    relative = path.relative_to(ROOT)
    records = ARTIFACT_METADATA.get("files", {})
    entry = records.get(relative.as_posix(), records.get(str(relative), {}))
    return read_csv(str(path), path.stat().st_mtime_ns, entry.get("sha256", ""))


def optional_csv(name: str) -> pd.DataFrame:
    path = OUTPUT_DIR / name
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return validate_columns(read_saved_csv(path), name, allow_empty=True)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def optional_json(name: str) -> dict:
    path = OUTPUT_DIR / name
    result = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if not isinstance(result, dict):
        raise OutputDataError(f"{name} 必须包含一个 JSON 对象")
    return result


def download(frame: pd.DataFrame, label: str, filename: str, key: str) -> None:
    st.download_button(label, csv_bytes(frame), file_name=filename, mime="text/csv", key=key)


def table(frame: pd.DataFrame) -> None:
    frame = display_frame(frame)
    columns = {}
    for column in frame.columns:
        if pd.api.types.is_datetime64_any_dtype(frame[column]):
            columns[column] = st.column_config.DateColumn(format="YYYY-MM-DD")
        elif any(unit in column for unit in ["（%）", "（百分点）", "(%)", "(pp)"]):
            columns[column] = st.column_config.NumberColumn(format="%.4f")
    st.dataframe(frame, hide_index=True, width="stretch", column_config=columns)


def style_chart(fig: go.Figure, height: int = 400) -> go.Figure:
    fig.update_layout(
        template="plotly_white", height=height, margin=dict(l=10, r=20, t=35, b=25),
        font=dict(family="Arial, PingFang SC, Microsoft YaHei, sans-serif", color="#24354B"),
        legend=dict(orientation="h", y=1.12, x=0), hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E8EDF1", zerolinecolor="#DDE5EB")
    return fig


def plot(fig: go.Figure, key: str) -> None:
    # Streamlit embeds its bundled Plotly runtime; no CDN is requested.
    st.plotly_chart(display_figure(fig), use_container_width=True, config={"displaylogo": False}, key=key)


def prepare_frames(clean: pd.DataFrame, predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    validate_columns(clean, "clean.csv")
    validate_columns(predictions, "predictions.csv")
    clean = clean.copy()
    predictions = predictions.copy()
    clean["From"] = pd.to_datetime(clean["From"], format="ISO8601")
    clean["To_corrected"] = pd.to_datetime(clean["To_corrected"], format="ISO8601")
    for col in ["anchor_from", "anchor_to", "target_from", "target_to"]:
        predictions[col] = pd.to_datetime(predictions[col], format="ISO8601")
    predictions["anchor_key"] = predictions.apply(lambda r: f"{int(r.anchor_year)}W{int(r.anchor_week):02d}", axis=1)
    if clean.week_key.duplicated().any() or clean.From.duplicated().any():
        raise OutputDataError("clean.csv 的监测周或起始日期重复")
    if predictions.duplicated(["split", "horizon", "anchor_key", "model_id"]).any():
        raise OutputDataError("predictions.csv 同一起点、时距与模型出现多个结果，无法确定本次回放版本")
    return clean.sort_values("From"), predictions


def source_details(clean: pd.DataFrame) -> None:
    with st.expander("数据定义与版本"):
        st.caption("冻结版本回顾性分析")
        st.write("临床目标为 PHLSB 呼吸道标本的 SARS-CoV-2 阳性比例。图表以百分比显示，预测误差使用百分点。该指标不能解释为全港感染比例。")
        st.write("污水指标：Per capita viral load (7-day geometric mean)，周报单位 copy/L。保留官方口径；归一化公式未随周表提供。")
        snapshot_date = APP_CONFIG.get("project", {}).get("snapshot_date_hkt", "见来源记录")
        st.write(f"来源：香港卫生署 COVID-19 Express；本地冻结日期 {snapshot_date}。缺测保留为空，2026W6 的结束日期按官方周报修正，原值留在派生数据表。")
        st.code("\n".join(clean.source_version.dropna().astype(str).unique()), language=None)
        if ARTIFACT_METADATA.get("generated_at_utc"):
            st.caption("产物生成：" + hkt(ARTIFACT_METADATA["generated_at_utc"]).strftime("%Y-%m-%d %H:%M HKT"))
        st.caption("主任务 h2；h1 为补充。模型与统计结果预先计算，筛选和导出可离线使用。")
        st.caption("本应用使用已保存结果，离线可操作。完整历史档案 as-of 回测尚未实施；已有档案样本用于数据审计。")


def select_course_page(page: str) -> None:
    st.session_state["page"] = page
    shadow = dict(st.session_state.get("_i18n_widget_values", {}))
    shadow["page"] = page
    if page in {"历史回放", "模型比较"}:
        prefix = "replay" if page == "历史回放" else "compare"
        chosen = {f"{prefix}_horizon": st.session_state.get("course_horizon", 2),
                  f"{prefix}_score": st.session_state.get("course_score", "clipped"),
                  f"{prefix}_split": "test"}
        if page == "历史回放" and "course_anchor" in st.session_state:
            chosen["replay_anchor"] = st.session_state["course_anchor"]
            chosen["replay_delay"] = 5
        for key, value in chosen.items():
            st.session_state[key] = value
            shadow[key] = value
    st.session_state["_i18n_widget_values"] = shadow


def course_context(clean: pd.DataFrame) -> None:
    st.caption("冻结回顾性分析")
    st.write("预测目标：PHLSB 呼吸道标本的 SARS-CoV-2 阳性比例（%）。污水指标单位：copy/L。")
    a, b = st.columns(2)
    latest = clean.sort_values("From").iloc[-1]
    a.caption(f"数据截至 {latest.week_key}（{date_text(latest.To_corrected)}）")
    b.caption("快照日期：" + str(APP_CONFIG["project"]["snapshot_date_hkt"]))


def course_home(clean: pd.DataFrame, predictions: pd.DataFrame, metrics: pd.DataFrame) -> None:
    st.title("课程演示")
    st.subheader("加入污水信息后，能否改善仅使用临床历史的预测？")
    course_context(clean)
    st.write("面向公共卫生研究者：追踪一条历史预测，比较三个模型，并解释相似周与异常信号。")
    a, b = st.columns(2)
    horizon = a.selectbox("课程预测时距", [2, 1], format_func=lambda x: f"h{x}", key="course_horizon")
    score = b.radio("课程评分", list(SCORE_NAMES), format_func=SCORE_NAMES.get, horizontal=True, key="course_score")
    result_metrics = optional_csv("raw_metrics.csv") if score == "raw" else metrics
    result = result_metrics.loc[(result_metrics.split == "test") & (result_metrics.horizon == horizon)]
    selected = filter_predictions(predictions, "test", horizon)
    if result.empty or selected.empty:
        st.info("当前选择没有评价记录。")
        return
    joint = result.loc[result.model_id == "combined_ridge"].iloc[0]
    cards = st.columns(3)
    cards[0].metric("共同评价周数", int(joint.n_origins))
    cards[1].metric("联合 MAE（百分点）", pp(joint.mae_pp))
    cards[2].metric("ΔMAE（百分点）", pp(joint.delta_mae_pp))
    latest_origin = selected.iloc[-1]
    st.session_state["course_anchor"] = latest_origin.anchor_key
    st.caption(f"示例起点 {latest_origin.anchor_key}；名义发出时间 {hkt(latest_origin.issue_at).strftime('%Y-%m-%d %H:%M HKT')}；目标 {date_text(latest_origin.target_from)} 至 {date_text(latest_origin.target_to)}。")
    st.write("在当前冻结数据、模型和评价设置下，加入污水信号降低了部分预测误差；改善幅度受输出约束和评价时段影响。")
    links = st.columns(4)
    for col, label, page in zip(links, ["查看数据", "追踪一次预测", "比较模型", "解释模式与异常"], PAGES[1:]):
        col.button(label, key="course_open_" + page, on_click=select_course_page, args=(page,), use_container_width=True)
    st.subheader("演示顺序")
    st.write("问题与数据（2 分钟）→ 历史预测（2 分钟）→ 模型比较（2 分钟）→ 聚类与异常（2 分钟）→ 导出、复现与结论（2 分钟）。")
    st.subheader("导出与复现")
    export = selected.copy()
    export["display_score_mode"] = score
    pred_col, err_col = scoring_columns(score)
    export["display_prediction"] = export[pred_col]
    export["display_abs_error_pp"] = export[err_col]
    download(export, "下载测试期预测（CSV）", f"course_test_h{horizon}_{score}.csv", "course_export")
    st.code("python -m pytest -q -k 'not test_frozen_source_bytes_match_independent_catalogue'\npython -m src.pipeline --config config.yaml --stage all", language="bash")
    st.caption("完整管线应在独立副本运行。历史回放中的“重新计算此起点”只读取冻结输入，不覆盖结果。")
    source_details(clean)


def origin_trace(clean: pd.DataFrame, view: pd.DataFrame, frozen: dict) -> None:
    """Saved evidence is available immediately; recomputation requires one click."""
    if not {"model_state", "query_features"}.issubset(view.columns):
        return
    with st.expander("输入到预测", expanded=bool(st.session_state.get("_course_mode"))):
        st.caption("以下参数来自该起点保存的拟合记录。")
        model = st.selectbox("查看模型过程", ["combined_ridge", "clinical_ridge"], format_func=MODEL_NAMES.get, key="trace_model")
        row = view.loc[view.model_id == model].iloc[0]
        state = json.loads(row.model_state)
        observations = lag_observations(clean, view, APP_CONFIG["forecast"]["lags"])
        observations["clinical_proportion"] *= 100
        table(observations.rename(columns={"lag_weeks": "滞后周数", "week_key": "监测周", "from": "开始日期", "clinical_proportion": "临床阳性比例（%）", "wastewater_copy_per_l": "污水（copy/L）"}))
        cards = st.columns(4)
        cards[0].metric("共同训练行数", int(row.n_train))
        cards[1].metric("最后训练目标周", row.train_last_target)
        cards[2].metric("λ", f"{row['lambda']:g}")
        cards[3].metric("截距（比例）", f"{state['intercept']:.8g}")
        st.caption("训练标签可得截止：" + str(row.train_last_target_available_at))
        evidence = saved_feature_evidence(view, model)
        table(evidence.rename(columns={"feature": "特征", "query_value": "输入值", "training_mean": "训练均值", "training_sd": "训练标准差", "standardized_query": "标准化输入", "coefficient": "系数"}))
        st.caption("p 特征使用 0–1 比例；w_log1p 特征使用 log(1＋copy/L)。标准化只使用当前训练行。")
        st.code("z = (x - training_mean) / training_sd\ny_hat = z @ coef + intercept", language="python")
        st.write("Ridge 最小化平均平方误差＋λ × 系数平方和；截距不受惩罚。")
        st.caption("实际计算：src.models.RidgeRegressor.fit / predict；src.backtest.predict_origin。")
        key = "origin_reproduction_" + str(row.split) + "_" + str(row.anchor_from) + "_" + str(row.horizon)
        if st.button("重新计算此起点", key="reproduce_origin"):
            st.session_state[key] = reproduce_origin(ROOT, APP_CONFIG, view, frozen)
        if key in st.session_state:
            rebuilt = st.session_state[key]
            st.success("当前复算与保存结果一致。") if rebuilt.matches_saved.all() else st.error("当前复算与保存结果存在差异。")
            shown = rebuilt.copy()
            shown["model_id"] = shown.model_id.map(MODEL_NAMES)
            for col in ["saved_raw_prediction", "recomputed_raw_prediction", "saved_prediction", "recomputed_prediction", "observed"]:
                shown[col] *= 100
            table(shown.rename(columns={"model_id": "模型", "saved_raw_prediction": "保存的原始预测（%）", "recomputed_raw_prediction": "复算的原始预测（%）", "saved_prediction": "保存的限定预测（%）", "recomputed_prediction": "复算的限定预测（%）", "observed": "实际（%）", "absolute_difference": "原始比例绝对差", "n_train": "训练行数", "matches_saved": "与保存结果一致"}))
            download(rebuilt, "下载复算记录（CSV）", f"origin_reproduction_{row.anchor_key}_h{int(row.horizon)}.csv", "trace_export")


def overview(clean: pd.DataFrame) -> None:
    st.title("监测概览")
    render_home_video(ROOT, language=language())
    st.subheader("监测数据")
    a, b = st.columns([3, 2])
    years = sorted(clean["Year"].dropna().astype(int).unique())
    chosen = a.multiselect("监测年份", years, default=years, key="overview_years")
    scale = b.radio("污水显示尺度", ["原始值", "log(1＋w)"], horizontal=True, key="overview_scale")
    view = clean.loc[clean.Year.isin(chosen)].copy()
    if view.empty:
        st.info("请选择至少一个监测年份。")
        return
    latest = view.iloc[-1]
    cards = st.columns(4)
    cards[0].metric("筛选范围内监测周数", f"{len(view)} 周")
    cards[1].metric("最新周阳性比例", percent(latest.SARSCoV2_proportion))
    cards[2].metric("最新周污水指标", "暂无" if pd.isna(latest.Sewage_viralload) else f"{latest.Sewage_viralload:,.0f}", help="单位 copy/L；官方七日几何平均指标。")
    cards[3].metric("污水缺测", f"{int(view.Sewage_viralload.isna().sum())} 周")
    st.caption(f"筛选日期 {date_text(view.From.min())} 至 {date_text(view.To_corrected.max())}；最新所选周 {latest.week_key}。")
    chart = calendar_chart_frame(view)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.13)
    fig.add_trace(go.Scatter(x=chart.From, y=chart.SARSCoV2_proportion * 100, name="临床阳性比例", mode="lines", line=dict(color="#3F6EC7", width=2.5), connectgaps=False, customdata=chart.week_key, hovertemplate="%{customdata}<br>%{y:.3f}%<extra></extra>"), row=1, col=1)
    sewage_values = np.log1p(chart.Sewage_viralload) if scale == "log(1＋w)" else chart.Sewage_viralload
    fig.add_trace(go.Scatter(x=chart.From, y=sewage_values, name="污水指标", mode="lines", line=dict(color="#00887A", width=2.5), connectgaps=False, customdata=chart.week_key, hovertemplate="%{customdata}<br>%{y:,.3f}<extra></extra>"), row=2, col=1)
    fig.update_yaxes(title_text="阳性比例（%）", row=1, col=1)
    fig.update_yaxes(title_text="log(1＋w)" if scale != "原始值" else "污水（copy/L）", row=2, col=1)
    fig.update_xaxes(title_text="监测周开始日期", row=2, col=1)
    plot(style_chart(fig, 530), "overview_chart")
    if len(chart) > len(view):
        st.caption("未选年份保留为日历空档，折线在空档处断开。导出仅包含所选记录。")
    if scale != "原始值":
        st.caption("对数视图显示 log(1＋w)，零值仍保留，空缺位置对应缺测。导出保留原始比例与污水数值。")
    shown = view[[c for c in ["week_key", "From", "To_corrected", "SARSCoV2_proportion", "Sewage_viralload", "correction_applied", "source_row_key"] if c in view]].copy()
    shown["SARSCoV2_proportion"] *= 100
    table(shown.rename(columns={"week_key": "官方监测周", "From": "开始日期", "To_corrected": "结束日期", "SARSCoV2_proportion": "阳性比例（%）", "Sewage_viralload": "污水（copy/L）", "correction_applied": "日期已纠错", "source_row_key": "原始记录键"}))
    download(view, "导出所选监测记录（CSV）", "monitoring_filtered.csv", "overview_export")
    source_details(clean)


def playback(clean: pd.DataFrame, predictions: pd.DataFrame, frozen: dict) -> None:
    st.title("历史回放")
    st.write("按预测起点查看观测信息、目标日期及三个系统的已保存预测。")
    a, b, c = st.columns([2, 2, 2])
    splits = [x for x in ["test", "validation", "future"] if x in predictions.split.unique()]
    split = a.selectbox("结果范围", splits, format_func=SPLIT_NAMES.get, key="replay_split")
    horizon = b.selectbox("预测时距", [2, 1], format_func=lambda x: f"h{x} · 相对观测周后 {x} 周", key="replay_horizon")
    delay_options = [0, 5, 6, 7, 8] if split == "future" else [5, 6, 7, 8]
    delay = c.selectbox("运行时间视图", delay_options, format_func=lambda x: "记录中的实际运行时刻" if x == 0 else f"假设周结束后 {x} 天" + ("（额外情境）" if x == 8 else ""), key="replay_delay")
    score_mode = st.radio("预测数值视角", list(SCORE_NAMES), format_func=SCORE_NAMES.get, horizontal=True, key="replay_score")
    prediction_column, error_column = scoring_columns(score_mode)
    selected = filter_predictions(predictions, split, horizon)
    if selected.empty:
        st.info("当前范围没有已保存的预测。")
        return
    anchors = selected.drop_duplicates("anchor_key").sort_values("anchor_from")
    anchor_labels = {r.anchor_key: f"{r.anchor_key} · {date_text(r.anchor_from)}—{date_text(r.anchor_to)}" for r in anchors.itertuples()}
    # Resolve one valid selection before rendering; restored session state and
    # a separate non-default widget index would otherwise compete.
    shadow = dict(st.session_state.get("_i18n_widget_values", {}))
    anchor = st.session_state.get("replay_anchor", shadow.get("replay_anchor"))
    if anchor not in anchor_labels:
        anchor = next(reversed(anchor_labels))
    if st.session_state.get("replay_anchor") != anchor:
        st.session_state["replay_anchor"] = anchor
    shadow["replay_anchor"] = anchor
    st.session_state["_i18n_widget_values"] = shadow
    anchor = st.selectbox("预测起点：最新已知完整监测周", list(anchor_labels), index=None, format_func=anchor_labels.get, key="replay_anchor")
    view = filter_predictions(predictions, split, horizon, anchor)
    row = view.iloc[0]
    timing = timing_for_row(row, None if delay == 0 else delay)
    if split == "validation":
        st.info("2025 开发／验证结果：展示参数由完整验证期选择，参数选择使用了该期后续资料。")
    elif split == "test":
        st.success("2026 最终测试：在回顾性流程中先用验证期选择并固定超参数，再评估测试期；每周仅用该起点已成熟的训练标签重新拟合。")
    else:
        st.info("冻结快照末端未评分预测：尚无目标观测，误差保持空缺。这些结果未获得后续实际值验证。")
    if split == "future":
        st.write(f"预测记录的实际运行时刻：{hkt(row.issue_at).strftime('%Y-%m-%d %H:%M:%S %Z')}。")
        if delay:
            st.caption("当前显示额外假设时间情境；预测记录中的实际运行时刻保留。情境使用同一冻结观测信息集。")
    else:
        st.caption("冻结版本回顾性回测 · 名义运行时刻为周末后指定天数的香港时间 23:59。时间情境保留同一观测信息集，未重建真实逐期发布时间。")
    cards = st.columns(3)
    cards[0].metric("实际运行时刻（香港）" if delay == 0 else "假设运行时刻（香港）", hkt(timing["display_issue_at"]).strftime("%m-%d %H:%M"))
    cards[1].metric("目标监测周", f"{int(row.target_year)}W{int(row.target_week):02d}")
    cards[2].metric("目标日期", f"{pd.Timestamp(row.target_from):%m-%d} — {pd.Timestamp(row.target_to):%m-%d}")
    st.write(f"完整运行日期：{hkt(timing['display_issue_at']).strftime('%Y-%m-%d %H:%M %Z')}。观测截止：{date_text(row.anchor_to)}。目标：{date_text(row.target_from)} 至 {date_text(row.target_to)}。")
    if timing["target_started"]:
        st.warning(f"所选运行时刻，固定 h{horizon} 目标周已经开始。下一完整未来周为 {timing['next_future_from']} 至 {timing['next_future_to']}，对应 h{timing['next_future_horizon']}。")
    else:
        st.caption(f"目标周在所选运行时刻尚未开始；下一完整未来周对应 h{timing['next_future_horizon']}。")
    if not timing["dynamic_prediction_available"]:
        st.warning(f"动态未来目标 h{timing['next_future_horizon']} 预测不可用：当前只保存 h1 与 h2 模型。固定 h{horizon} 的数值和目标日期保持对应。")
    forecast_table = view[["model_id", "prediction", "observed", "abs_error_pp", "n_train", "lambda", "status"]].copy()
    forecast_table["prediction"] = view[prediction_column]
    forecast_table["abs_error_pp"] = view[error_column]
    if score_mode == "raw":
        st.caption("当前显示原始回归输出及对应误差，数值可能低于 0% 或高于 100%。主评分视角使用预先规定的 0–100% 范围。")
    forecast_table["model_id"] = forecast_table.model_id.map(MODEL_NAMES).fillna(forecast_table.model_id)
    forecast_table[["prediction", "observed"]] *= 100
    table(forecast_table.rename(columns={"model_id": "模型", "prediction": "预测（%）", "observed": "实际（%）", "abs_error_pp": "绝对误差（百分点）", "n_train": "共同训练行数", "lambda": "λ", "status": "记录状态"}))
    history = clean.loc[clean.From <= row.anchor_from].tail(24)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=history.From, y=history.SARSCoV2_proportion * 100, name="已知临床观测", mode="lines+markers", line=dict(color="#263B55", width=2)))
    for prediction in view.itertuples():
        fig.add_trace(go.Scatter(x=[prediction.target_from], y=[getattr(prediction, prediction_column) * 100], name=MODEL_NAMES.get(prediction.model_id, prediction.model_id), mode="markers", marker=dict(size=12, symbol="diamond", color=MODEL_COLORS.get(prediction.model_id))))
    if pd.notna(row.observed):
        fig.add_trace(go.Scatter(x=[row.target_from], y=[row.observed * 100], name="后续实际观测", mode="markers", marker=dict(color="#172B44", size=12, symbol="x")))
    fig.update_yaxes(title_text="阳性比例（%）")
    fig.update_xaxes(title_text="监测周开始日期")
    plot(style_chart(fig), "replay_chart")
    export = view.copy()
    export["display_score_mode"] = score_mode
    export["display_prediction"] = view[prediction_column]
    export["display_abs_error_pp"] = view[error_column]
    for key, value in timing.items():
        export[key] = value
    download(export, "导出当前起点与时间情境（CSV）", f"replay_{anchor}_h{horizon}_{score_mode}_delay{delay}.csv", "replay_export")
    origin_trace(clean, view, frozen)
    with st.expander("输入版本、训练截止与固定参数"):
        fields = [x for x in ["run_id", "backtest_mode", "source_version", "evaluation_vintage", "issue_at", "nominal_issue_at", "train_last_target", "train_anchor_keys", "feature_set", "stage_label", "raw_prediction", "was_clipped"] if x in view]
        table(view[["model_id"] + fields])
        if frozen:
            st.json(frozen, expanded=False)
    with st.expander("该起点的原始观测与日期纠错"):
        raw = clean.loc[clean.From == row.anchor_from]
        table(raw)
        download(raw, "导出起点观测（CSV）", f"observation_{anchor}.csv", "replay_raw_export")


def compare(predictions: pd.DataFrame, metrics: pd.DataFrame) -> None:
    st.title("模型比较")
    st.write("在共同起点、目标周与评价版本上比较三个系统。ΔMAE = 临床模型 MAE − 联合模型 MAE；正值表示联合模型误差较低。")
    score_mode = st.radio("误差评分视角", list(SCORE_NAMES), format_func=SCORE_NAMES.get, horizontal=True, key="compare_score")
    prefix = "raw_" if score_mode == "raw" else ""
    if score_mode == "raw":
        metrics = optional_csv("raw_metrics.csv")
        if metrics.empty:
            st.info("原始预测评分尚未生成。请运行完整分析管线后再查看此视角。")
            st.code("python -m src.pipeline --config config.yaml --stage all", language="bash")
            return
    validate_columns(metrics, f"{prefix}metrics.csv")
    prediction_column, error_column = scoring_columns(score_mode)
    a, b, c = st.columns(3)
    splits = [x for x in ["test", "validation"] if x in metrics.split.unique()]
    if not splits:
        raise OutputDataError(f"{prefix}metrics.csv 没有可识别的验证或测试范围")
    split = a.selectbox("评价范围", splits, format_func=SPLIT_NAMES.get, key="compare_split")
    horizon = b.selectbox("比较时距", [2, 1], format_func=lambda x: f"h{x}", key="compare_horizon")
    block = c.selectbox("时间块长度（周）", [4, 2, 8], key="compare_block")
    view = metrics.loc[(metrics.split == split) & (metrics.horizon == horizon)].copy()
    week_predictions = filter_predictions(predictions, split, horizon)
    if view.empty:
        st.info("当前选择没有评价记录。")
        return
    saved_intervals = optional_csv(f"{prefix}bootstrap_sensitivity.csv")
    if not saved_intervals.empty:
        saved_intervals = saved_intervals.loc[(saved_intervals.split == split) & (saved_intervals.horizon == horizon)].copy()
    view = metrics_for_block(view, saved_intervals, block)
    if split == "validation":
        st.info("开发／验证期用于选择参数，此处指标包含参数选择的影响。主要结论请查看 2026 最终测试。")
    joint = view.loc[view.model_id == "combined_ridge"]
    if not joint.empty:
        result = joint.iloc[0]
        cards = st.columns(4)
        cards[0].metric("配对起点", f"{int(result.n_origins)} 周")
        cards[1].metric("联合 MAE（百分点）", pp(result.mae_pp))
        cards[2].metric("ΔMAE（百分点）", pp(result.delta_mae_pp))
        cards[3].metric("相对改善", "未定义" if pd.isna(result.relative_gain_pct) else f"{result.relative_gain_pct:.2f}%")
        if score_mode == "raw":
            st.caption(f"当前误差使用未经范围限制的原始输出；{int(result.n_clipped)}／{int(result.n_origins)} 个预测越过 0–100% 边界。模型、预测起点和参数与主评分相同。")
        elif "raw_mae_pp" in result:
            st.caption(f"联合模型原始预测 MAE 为 {pp(result.raw_mae_pp)} 个百分点；{int(result.n_clipped)}／{int(result.n_origins)} 个预测发生 0–100% 边界截断。")
        low, high = result.get("delta_ci_low_pp", np.nan), result.get("delta_ci_high_pp", np.nan)
        if pd.notna(low) and pd.notna(high):
            evaluation = optional_json("config.json").get("evaluation", {})
            repeats = evaluation.get("bootstrap_repeats", 2000)
            confidence = result.get("bootstrap_confidence_level", 0.95)
            st.write(f"当前评分 ΔMAE 的 {confidence:.0%} 时间块重采样区间：[{pp(low)}, {pp(high)}] 个百分点（{block} 周块、{repeats:,} 次）。")
            if low <= 0 <= high:
                st.caption("该区间包含零，当前结果未显示方向稳定的增量改善。")
        else:
            st.caption("该范围的时间块区间不可用；请查看运行结果中的原因与候选块数量。")
        if not saved_intervals.empty:
            valid_intervals = saved_intervals.dropna(subset=["low", "high"])
            contains_zero = (valid_intervals.low <= 0) & (valid_intervals.high >= 0)
            if contains_zero.any() and not contains_zero.all():
                crossing = "、".join(str(int(v)) for v in valid_intervals.loc[contains_zero, "block_weeks"])
                st.warning(f"区间结论依赖时间块长度：{crossing} 周块的区间包含零。完整 2／4／8 周块结果见下方敏感性表。")
    names = [x for x in MODEL_NAMES if x in view.model_id.unique()]
    models = st.multiselect("表格与误差曲线显示模型", names, default=names, format_func=MODEL_NAMES.get, key="compare_models")
    shown = view.loc[view.model_id.isin(models)].copy()
    cols = [c for c in ["model_id", "n_origins", "mae_pp", "rmse_pp", "raw_mae_pp", "raw_rmse_pp", "delta_mae_pp", "delta_ci_low_pp", "delta_ci_high_pp", "relative_gain_pct", "coverage", "n_clipped"] if c in shown]
    display = shown[cols].copy()
    display["model_id"] = display.model_id.map(MODEL_NAMES)
    table(display.rename(columns={"model_id": "模型", "n_origins": "配对起点数", "mae_pp": "MAE（百分点）", "rmse_pp": "RMSE（百分点）", "raw_mae_pp": "原始预测 MAE（百分点）", "raw_rmse_pp": "原始预测 RMSE（百分点）", "delta_mae_pp": "ΔMAE（百分点）", "delta_ci_low_pp": "ΔMAE 区间下限（百分点）", "delta_ci_high_pp": "ΔMAE 区间上限（百分点）", "relative_gain_pct": "相对改善（%）", "coverage": "可用覆盖率", "n_clipped": "截断预测数"}))
    st.caption("评分视角只改变如何评价已保存的预测，不重新选参或训练。顶部增量指标及下方配对图始终比较临床与联合模型。")
    fig = go.Figure()
    for model in models:
        rows = week_predictions.loc[week_predictions.model_id == model]
        chart = calendar_chart_frame(rows, "anchor_from")
        fig.add_trace(go.Scatter(x=chart.anchor_from, y=chart[error_column], name=MODEL_NAMES[model], mode="lines+markers", marker=dict(size=4), line=dict(color=MODEL_COLORS[model], width=2), connectgaps=False))
    fig.update_yaxes(title_text="绝对误差（百分点）")
    fig.update_xaxes(title_text="预测起点监测周开始日期")
    plot(style_chart(fig), "compare_errors")
    pair_keys = ["anchor_from", "target_from", "horizon", "evaluation_vintage", "source_version", "issue_at", "backtest_mode"]
    paired = week_predictions.pivot(index=pair_keys, columns="model_id", values=error_column).reset_index()
    if {"clinical_ridge", "combined_ridge"}.issubset(paired):
        paired = paired.dropna(subset=["clinical_ridge", "combined_ridge"])
        paired["delta_abs_error_pp"] = paired.clinical_ridge - paired.combined_ridge
        paired["split"] = split
        paired["score_mode"] = score_mode
        gain = go.Figure(go.Bar(x=paired.anchor_from, y=paired.delta_abs_error_pp, name="逐周误差差值", marker_color=np.where(paired.delta_abs_error_pp >= 0, "#00887A", "#C07855")))
        gain.update_yaxes(title_text="临床误差 − 联合误差（百分点）")
        gain.update_xaxes(title_text="共同预测起点监测周开始日期")
        plot(style_chart(gain, 290), "compare_gain")
        download(paired, "导出所选范围配对误差（CSV）", f"paired_{split}_h{horizon}_{score_mode}.csv", "compare_pair_export")
    shown["score_mode"] = score_mode
    download(shown, "导出所选模型汇总（CSV）", f"metrics_{split}_h{horizon}_{score_mode}_block{block}.csv", "compare_metrics_export")
    prediction_export = week_predictions.loc[week_predictions.model_id.isin(models)].copy()
    prediction_export["display_score_mode"] = score_mode
    prediction_export["display_prediction"] = prediction_export[prediction_column]
    prediction_export["display_abs_error_pp"] = prediction_export[error_column]
    download(prediction_export, "导出所选模型逐周预测（CSV）", f"predictions_{split}_h{horizon}_{score_mode}.csv", "compare_predictions_export")
    with st.expander("历史变化阶段与时间块敏感性"):
        stages = optional_csv(f"{prefix}stage_metrics.csv")
        if not stages.empty:
            stages = stages.loc[(stages.split == split) & (stages.horizon == horizon)].copy()
            st.caption("阶段按起点已知的临床变化规则划分；阶段结果保留正负误差差值。")
            table(stages)
            download(stages, "导出当前阶段结果（CSV）", f"stages_{split}_h{horizon}_{score_mode}.csv", "compare_stages_export")
        intervals = optional_csv(f"{prefix}bootstrap_sensitivity.csv")
        if not intervals.empty:
            intervals = intervals.loc[(intervals.split == split) & (intervals.horizon == horizon)].copy()
            table(intervals)
            download(intervals, "导出时间块敏感性（CSV）", f"bootstrap_{split}_h{horizon}_{score_mode}.csv", "compare_bootstrap_export")
    with st.expander("比较集合与来源"):
        table(shown[[c for c in ["model_id", "paired_set_id", "run_id", "backtest_mode", "bootstrap_blocks"] if c in shown]])
        st.caption("所有汇总来自已保存的预计算结果。误差差值保留完整正负方向；配对表以共同起点、目标、时距和评价版本对齐。")


def patterns_page(clean: pd.DataFrame) -> None:
    st.title("状态与异常")
    st.write("查看联合状态、相对历史邻域的少见程度，以及支持判断的原始观测。LOF 分数表示相对密度差异，不对应已核实异常事件的概率。")
    patterns = optional_csv("patterns.csv")
    if patterns.empty:
        st.info("状态与异常输出尚未生成。完成分析管线后，本页将读取本地 patterns.csv。")
        return
    patterns["Year"] = patterns.week_key.astype(str).str[:4].astype(int)
    patterns = patterns.merge(clean[["week_key", "From"]], on="week_key", how="left")
    a, b = st.columns([2, 3])
    years = sorted(patterns.Year.unique())
    selected_years = a.multiselect("查询年份", years, default=[max(years)], key="patterns_years")
    ordering = b.radio("记录排序", ["LOF 从高到低", "监测周从近到远"], horizontal=True, key="patterns_sort")
    view = patterns.loc[patterns.Year.isin(selected_years)].copy()
    view = view.sort_values("lof_score" if ordering.startswith("LOF") else "From", ascending=False, na_position="last")
    if view.empty:
        st.info("请选择至少一个查询年份。")
        return
    window = APP_CONFIG.get("patterns", {}).get("reference_window_weeks", 104)
    primary_k = APP_CONFIG.get("patterns", {}).get("lof_primary_neighbors", 10)
    st.caption(f"每个查询仅使用其之前最多 {window} 个日历周的参考记录；查询周不参与拟合。列表排序是对所选范围已完成查询的事后比较，单周详情中的排名以该查询周为截止。")
    plot_data = calendar_chart_frame(view)
    fig = go.Figure(go.Scatter(x=plot_data.From, y=plot_data.lof_score, mode="lines+markers", name="LOF novelty 分数", line=dict(color="#00887A", width=2), connectgaps=False, customdata=plot_data.week_key, hovertemplate="%{customdata}<br>LOF %{y:.3f}<extra></extra>"))
    fig.update_yaxes(title_text=f"LOF 分数（k={primary_k}）")
    fig.update_xaxes(title_text="查询周开始日期")
    plot(style_chart(fig, 300), "patterns_scores")
    brief_cols = [c for c in ["week_key", "cluster_label", "lof_score", "lof_k", "n_reference", "reference_start", "reference_end", "status"] if c in view]
    table(view[brief_cols].rename(columns={"week_key": "查询周", "cluster_label": "所属簇中心特征", "lof_score": "LOF 分数", "lof_k": "近邻数", "n_reference": "参考记录数", "reference_start": "参考开始", "reference_end": "参考截止", "status": "计算状态"}))
    download(view, "导出筛选状态与异常记录（CSV）", "patterns_filtered.csv", "patterns_export")
    selected_week = st.selectbox("查看某一查询周", view.week_key.tolist(), key="pattern_week")
    row = view.loc[view.week_key == selected_week].iloc[0]
    if row.get("status", "ok") != "ok":
        status_labels = {"missing_query_features": "该查询周的状态特征缺失", "insufficient_reference": "历史合格参考记录不足 52 行", "config_not_yet_available": "此时尚未固定模式参数"}
        st.warning(status_labels.get(row.get("status"), str(row.get("status"))))
    cards = st.columns(3)
    cards[0].metric("查询周", selected_week)
    cards[1].metric("局部聚类编号", "暂无" if pd.isna(row.cluster_id) else f"{int(row.cluster_id)}（k={int(row.cluster_k)}）")
    cards[2].metric("LOF 分数", pp(row.lof_score))
    st.write("所属簇的中心特征：" + ("暂无" if pd.isna(row.cluster_label) else str(row.cluster_label)))
    st.caption("簇描述概括历史参考组的中心。查询周自身的方向和变化量如下，可能与中心描述不同。")
    trend_cards = st.columns(2)
    trend_cards[0].metric("查询周临床两周变化（百分点）", pp(row.p_change_2w * 100))
    trend_cards[1].metric("查询周污水两周变化 · log(1＋w)", pp(row.log1p_w_change_2w))
    st.write(f"参考区间：{row.reference_start} 至 {row.reference_end}；合格参考记录 {row.n_reference}。")
    state_rows = []
    for feature, label in FEATURE_NAMES.items():
        if feature in row:
            multiplier = 100 if feature.startswith("p") else 1
            state_rows.append({"状态特征": label, "查询值": row[feature] * multiplier, "参考均值": row.get(f"{feature}_reference_mean", np.nan) * multiplier, "标准化偏离（z）": row.get(f"{feature}_z", np.nan)})
    if state_rows:
        table(pd.DataFrame(state_rows))
        st.caption("标准化偏离 z =（查询值 − 参考均值）／参考标准差；均值和标准差均仅由查询之前的合格参考记录计算。")
    centers = optional_csv("pattern_centers.csv")
    neighbors = optional_csv("pattern_neighbors.csv")
    sensitivity = optional_csv("pattern_sensitivity.csv")
    tabs = st.tabs(["局部聚类中心", "历史近邻", "参数敏感性", "原始记录"])
    with tabs[0]:
        if not centers.empty and "query_week_key" in centers:
            selected = centers.loc[centers.query_week_key == selected_week].copy()
            display = selected[[col for col in ["cluster_id", "cluster_label", "n_members", "p_center", "p_change_2w_center", "w_center", "log1p_w_change_2w_center"] if col in selected]].copy()
            for col in ["p_center", "p_change_2w_center"]:
                if col in display:
                    display[col] *= 100
            display = display.rename(columns={"cluster_id": "簇编号", "cluster_label": "簇中心特征", "n_members": "成员周数", "p_center": "阳性比例中心（%）", "p_change_2w_center": "两周变化中心（百分点）", "w_center": "污水中心反变换（copy/L）", "log1p_w_change_2w_center": "两周污水 log 变化中心"})
            table(display)
            st.caption("每行对应本次查询参考集的一个聚类中心。成员周及完整中心保留在导出表；不同查询之间的数字簇号不能直接视为同一状态。")
            download(selected, "导出本周聚类中心与成员（CSV）", f"centers_{selected_week}.csv", "centers_export")
            if "member_week_keys" in selected:
                table(selected[["cluster_id", "cluster_label", "member_week_keys"]].rename(columns={"cluster_id": "簇编号", "cluster_label": "簇中心特征", "member_week_keys": "成员周"}))
        else:
            st.info("暂无聚类中心输出。")
    with tabs[1]:
        if not neighbors.empty and "query_week_key" in neighbors:
            selected = neighbors.loc[neighbors.query_week_key == selected_week].copy()
            if "lof_k" in selected and not selected.empty:
                candidates = sorted(selected.lof_k.unique())
                k = st.selectbox("解释近邻数 k", candidates, index=candidates.index(10) if 10 in candidates else 0, key="neighbors_k")
                selected = selected.loc[selected.lof_k == k].copy()
            display = selected[[col for col in ["neighbor_rank", "neighbor_week_key", "distance", "reachability_distance", "SARSCoV2_proportion", "Sewage_viralload", "p_change_2w", "log1p_w_change_2w"] if col in selected]].copy()
            for col in ["SARSCoV2_proportion", "p_change_2w"]:
                if col in display:
                    display[col] *= 100
            table(display.rename(columns={"neighbor_rank": "距离排序", "neighbor_week_key": "参考周", "distance": "标准化距离", "reachability_distance": "可达距离", "SARSCoV2_proportion": "阳性比例（%）", "Sewage_viralload": "污水（copy/L）", "p_change_2w": "两周临床变化（百分点）", "log1p_w_change_2w": "两周污水 log 变化"}))
            download(selected, "导出所选历史近邻（CSV）", f"neighbors_{selected_week}.csv", "neighbors_export")
        else:
            st.info("暂无历史近邻输出。")
    with tabs[2]:
        if not sensitivity.empty:
            selected = sensitivity.loc[sensitivity.week_key == selected_week].copy()
            as_of_columns = [c for c in ["week_key", "query_from", "issue_at", "lof_k", "lof_score", "n_reference", "rank_as_of", "n_scored_as_of"] if c in selected]
            if {"rank_as_of", "n_scored_as_of"}.issubset(selected):
                as_of = selected[as_of_columns].copy()
                st.caption(f"排名只比较截至 {selected_week} 的有效历史查询，并列分数采用相同名次。")
                table(as_of.rename(columns={"week_key": "查询周", "lof_k": "近邻数", "lof_score": "LOF 分数", "rank_as_of": "截至查询周名次", "n_scored_as_of": "截至查询周有效周数"}))
                download(as_of, "导出截至本周的 LOF 敏感性（CSV）", f"lof_sensitivity_{selected_week}_asof.csv", "sensitivity_export")
            else:
                st.info("该输出尚未包含截至查询周的排名，重建完整分析后可查看。")
            with st.expander("全期事后排名与截止周"):
                retrospective_columns = [c for c in ["week_key", "period", "lof_k", "lof_score", "rank_all", "rank_all_cutoff_week", "rank_period", "rank_period_cutoff_week"] if c in selected]
                retrospective = selected[retrospective_columns].copy()
                st.caption("下表含所选查询周之后的记录，用于事后描述；每个排名同时列出实际截止周。")
                table(retrospective)
                download(retrospective, "导出全期事后排名（CSV）", f"lof_sensitivity_{selected_week}_retrospective.csv", "sensitivity_retrospective_export")
        else:
            st.info("暂无参数敏感性输出。")
    with tabs[3]:
        raw = clean.loc[clean.week_key == selected_week]
        table(raw)
        table(view.loc[view.week_key == selected_week, [c for c in ["source_version", "source_row_key", "issue_at", "reference_start", "reference_end", "cluster_k", "lof_k", "period", "backtest_mode"] if c in view]])
        download(raw, "导出本周原始观测（CSV）", f"pattern_observation_{selected_week}.csv", "pattern_raw_export")


def main(course_default: bool = False) -> None:
    global APP_CONFIG, OUTPUT_DIR, ARTIFACT_METADATA
    restore_widget_values()
    if course_default:
        st.session_state["_course_mode"] = True
    if "page" not in st.session_state and "page" not in st.session_state.get("_i18n_widget_values", {}):
        st.session_state["page"] = "课程演示" if course_default else "监测概览"
    st.set_page_config(page_title="香港污水与临床监测", page_icon="🌊", layout="wide", initial_sidebar_state="expanded")
    st.markdown("""<style>
        .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1440px;}
        h1 {font-size: 2rem !important; color: #19344B; letter-spacing: -.03em;}
        [data-testid="stMetric"] {background: #F3F7FA; padding: 1rem 1.15rem; border-radius: 12px;}
        [data-testid="stMetricValue"] {font-size: 1.65rem;}
        [data-testid="stSidebar"] {background: #EDF3F6;}
        [data-testid="stSidebar"] hr {border-color: #D6E2E9;}
        </style>""", unsafe_allow_html=True)
    try:
        APP_CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
        if not isinstance(APP_CONFIG, dict):
            raise OutputDataError("config.yaml 必须包含项目配置")
        output = APP_CONFIG.get("output", {})
        if not isinstance(output, dict) or not isinstance(output.get("directory", "outputs"), str):
            raise OutputDataError("config.yaml 的 output.directory 必须为目录路径")
        OUTPUT_DIR = ROOT / output.get("directory", "outputs")
        metadata = verify_artifacts(ROOT, APP_CONFIG)
        ARTIFACT_METADATA = metadata
    except (ArtifactError, OutputDataError, KeyError, TypeError, OSError, ValueError, yaml.YAMLError) as exc:
        show_output_error(exc)
        st.stop()
    with st.sidebar:
        st.button("中文" if language() == "en" else "English", key="language_toggle", on_click=toggle_language)
        st.markdown("### 香港污水与临床监测")
        page = st.radio("分析页面", PAGES, key="page", label_visibility="collapsed")
    required = {
        "clean": ROOT / "data" / "processed" / "clean.csv",
        "predictions": OUTPUT_DIR / "predictions.csv",
        "metrics": OUTPUT_DIR / "metrics.csv",
    }
    missing = [str(path.relative_to(ROOT)) for path in required.values() if not path.exists()]
    if missing:
        st.title("分析结果尚未生成")
        st.info("缺少本地结果：" + "、".join(missing))
        st.write("请在项目目录运行分析管线，再刷新应用：")
        st.code("python -m src.pipeline --config config.yaml --stage all", language="bash")
        st.stop()
    try:
        clean, predictions = prepare_frames(
            read_saved_csv(required["clean"]),
            read_saved_csv(required["predictions"]),
        )
        metrics = validate_columns(read_saved_csv(required["metrics"]), "metrics.csv")
        frozen = optional_json("frozen_config.json")
        if st.session_state.get("_course_mode") and page != "课程演示":
            course_context(clean)
        if page == "课程演示":
            course_home(clean, predictions, metrics)
        elif page == "监测概览":
            overview(clean)
        elif page == "历史回放":
            playback(clean, predictions, frozen)
        elif page == "模型比较":
            compare(predictions, metrics)
        else:
            patterns_page(clean)
    except (OutputDataError, KeyError, ValueError, OSError, pd.errors.EmptyDataError) as exc:
        show_output_error(exc)
        st.stop()
    st.divider()
    st.caption("香港卫生署开放数据 · PHLSB 标本监测指标 · 本地冻结分析 · 研究用途")


if __name__ == "__main__":
    main()
