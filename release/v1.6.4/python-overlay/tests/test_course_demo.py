"""Course entry and real-origin evidence, using the local frozen analysis."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from streamlit.testing.v1 import AppTest

from app import ROOT, prepare_frames, filter_predictions, metrics_for_block, csv_bytes
from src.course_trace import checked_origin, lag_observations, saved_feature_evidence, reproduce_origin


@pytest.fixture
def analysis():
    config = yaml.safe_load((ROOT / "config.yaml").read_text())
    out = ROOT / config["output"]["directory"]
    clean, predictions = prepare_frames(pd.read_csv(ROOT / "data/processed/clean.csv"), pd.read_csv(out / "predictions.csv"))
    frozen = json.loads((out / "frozen_config.json").read_text())
    return config, clean, predictions, frozen


@pytest.mark.parametrize("horizon", [1, 2])
@pytest.mark.parametrize("split", ["validation", "test", "future"])
def test_actual_origin_reproduction_uses_recorded_time_and_frozen_parameters(analysis, horizon, split):
    config, clean, predictions, frozen = analysis
    selected = filter_predictions(predictions, split, horizon)
    view = selected.loc[selected.anchor_from == selected.anchor_from.max()]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / "outputs").glob("*") if p.is_file()}
    result = reproduce_origin(ROOT, config, view, frozen)
    assert len(result) == 3
    assert result.matches_saved.all()
    assert result.absolute_difference.max() < 1e-12
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before}
    if split == "future":
        assert result.observed.isna().all()


@pytest.mark.parametrize("model", ["clinical_ridge", "combined_ridge"])
def test_trace_vector_matches_recorded_prediction(analysis, model):
    config, clean, predictions, frozen = analysis
    view = filter_predictions(predictions, "test", 2, "2026W20")
    evidence = saved_feature_evidence(view, model)
    row = view.loc[view.model_id == model].iloc[0]
    state = json.loads(row.model_state)
    estimate = evidence.standardized_query.to_numpy() @ evidence.coefficient.to_numpy() + state["intercept"]
    assert np.isclose(estimate, row.raw_prediction, rtol=1e-10, atol=1e-12)
    assert len(evidence) == (3 if model == "clinical_ridge" else 6)
    observations = lag_observations(clean, view, config["forecast"]["lags"])
    assert observations["from"].diff().dropna().eq(pd.Timedelta(weeks=-1)).all()
    assert np.allclose(observations.clinical_proportion, evidence.query_value.iloc[:3])


def test_trace_rejects_ambiguous_or_incomplete_origin(analysis):
    _, _, predictions, _ = analysis
    rows = filter_predictions(predictions, "test", 2, "2026W20")
    for malformed in (rows.iloc[:0], rows.iloc[:2], pd.concat([rows, rows.iloc[:1]])):
        with pytest.raises(ValueError, match="three models"):
            checked_origin(malformed)
    rows = rows.copy()
    rows.loc[rows.index[0], "issue_at"] = "2026-01-01T23:59:00+08:00"
    with pytest.raises(ValueError, match="issue_at"):
        checked_origin(rows)


def test_course_entry_routes_to_actual_analysis_and_reproduces_one_origin(analysis):
    app = AppTest.from_file(str(ROOT / "course_demo.py"), default_timeout=30).run()
    assert not app.exception and not app.error
    assert app.title[0].value == "Course demo"
    assert app.session_state["ui_language"] == "en"
    assert any("PHLSB" in str(x.value) for x in app.markdown)
    assert any("Frozen retrospective" in str(x.value) for x in app.caption)
    app.button(key="course_open_历史回放").click().run()
    assert not app.exception and not app.error
    assert app.radio(key="page").value == "历史回放"
    assert any(x.label == "From inputs to prediction" and x.proto.expanded for x in app.expander)
    app.button(key="reproduce_origin").click().run()
    assert not app.exception and not app.error
    assert any("current calculation matches" in x.value for x in app.success)
    app.button(key="language_toggle").click().run()
    assert not app.exception and not app.error
    assert any("当前复算与保存结果一致" in x.value for x in app.success)
    assert app.selectbox(key="trace_model").value == "combined_ridge"


def test_course_entry_keeps_explicit_page_selection(analysis):
    app = AppTest.from_file(str(ROOT / "course_demo.py"), default_timeout=30).run()
    app.radio(key="page").set_value("模型比较").run()
    assert not app.exception and not app.error
    assert app.title[0].value == "Model comparison"
    app.button(key="language_toggle").click().run()
    assert app.radio(key="page").value == "模型比较"
    assert app.title[0].value == "模型比较"


def test_twelve_comparison_states_match_saved_intervals_and_csv(analysis):
    """Exercise the actual page for every h/score/block combination."""
    import io
    app = AppTest.from_file(str(ROOT / "course_demo.py"), default_timeout=30).run()
    app.radio(key="page").set_value("模型比较").run()
    for score in ("clipped", "raw"):
        prefix = "raw_" if score == "raw" else ""
        metrics = pd.read_csv(ROOT / "outputs" / f"{prefix}metrics.csv")
        intervals = pd.read_csv(ROOT / "outputs" / f"{prefix}bootstrap_sensitivity.csv")
        app.radio(key="compare_score").set_value(score).run()
        for h in (1, 2):
            app.selectbox(key="compare_horizon").set_value(h).run()
            subset = metrics.loc[(metrics.split == "test") & (metrics.horizon == h)]
            cis = intervals.loc[(intervals.split == "test") & (intervals.horizon == h)]
            for block in (2, 4, 8):
                app.selectbox(key="compare_block").set_value(block).run()
                assert not app.exception and not app.error
                expected = metrics_for_block(subset, cis, block)
                exported = pd.read_csv(io.BytesIO(csv_bytes(expected)))
                assert exported.block_weeks.eq(block).all()
                pd.testing.assert_frame_equal(exported, expected.reset_index(drop=True), check_dtype=False)
                joint = expected.loc[expected.model_id == "combined_ridge"].iloc[0]
                shown = app.dataframe[0].value
                row = shown.loc[shown["Model"] == "Clinical + wastewater Ridge"].iloc[0]
                assert np.isclose(row["MAE (pp)"], joint.mae_pp)
                assert np.isclose(row["ΔMAE interval lower (pp)"], joint.delta_ci_low_pp)
                assert np.isclose(row["ΔMAE interval upper (pp)"], joint.delta_ci_high_pp)
                assert any(f"{block}-week blocks" in str(x.value) for x in app.markdown)


def test_course_horizon_and_score_follow_task_button(analysis):
    app = AppTest.from_file(str(ROOT / "course_demo.py"), default_timeout=30).run()
    app.selectbox(key="course_horizon").set_value(1).run()
    app.radio(key="course_score").set_value("raw").run()
    app.button(key="course_open_历史回放").click().run()
    assert not app.exception and not app.error
    assert app.selectbox(key="replay_horizon").value == 1
    assert app.radio(key="replay_score").value == "raw"
    assert app.selectbox(key="replay_anchor").value == "2026W40"


def test_replay_anchor_state_has_one_default_and_survives_navigation(monkeypatch):
    """The course link and restored selections must not compete with a widget default."""
    from streamlit.elements.lib import policies

    app = AppTest.from_file(str(ROOT / "course_demo.py"), default_timeout=30)

    def checked_run(action=None):
        # Streamlit normally displays this warning only once per process. Reset
        # its test-visible flag so each navigation step is checked independently.
        monkeypatch.setattr(policies, "_shown_default_value_warning", False)
        (action if action is not None else app).run()
        assert not app.exception and not app.error
        assert not [w.value for w in app.warning if "Session State API" in w.value]

    checked_run()
    checked_run(app.selectbox(key="course_horizon").set_value(1))
    checked_run(app.radio(key="course_score").set_value("raw"))
    checked_run(app.button(key="course_open_历史回放").click())
    assert app.selectbox(key="replay_horizon").value == 1
    assert app.radio(key="replay_score").value == "raw"
    assert app.selectbox(key="replay_anchor").value == "2026W40"

    checked_run(app.selectbox(key="replay_anchor").set_value("2026W20"))
    checked_run(app.radio(key="page").set_value("监测概览"))
    checked_run(app.radio(key="page").set_value("历史回放"))
    assert app.selectbox(key="replay_anchor").value == "2026W20"
    for language in ("zh", "en"):
        checked_run(app.button(key="language_toggle").click())
        assert app.session_state["ui_language"] == language
        assert app.selectbox(key="replay_anchor").value == "2026W20"
        assert app.selectbox(key="replay_horizon").value == 1
        assert app.radio(key="replay_score").value == "raw"

    checked_run(app.selectbox(key="replay_split").set_value("validation"))
    assert app.selectbox(key="replay_anchor").value == "2025W50"
    checked_run(app.selectbox(key="replay_anchor").set_value("2025W20"))
    checked_run(app.button(key="language_toggle").click())
    assert app.selectbox(key="replay_anchor").value == "2025W20"
    checked_run(app.selectbox(key="replay_split").set_value("future"))
    assert app.selectbox(key="replay_anchor").value == "2026W42"
    checked_run(app.selectbox(key="replay_split").set_value("test"))
    assert app.selectbox(key="replay_anchor").value == "2026W40"
