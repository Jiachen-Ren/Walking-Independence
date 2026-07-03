from __future__ import annotations

import json
import joblib
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="术后行走能力恢复预测计算器",
    page_icon="🚶",
    layout="centered",
)


@st.cache_resource
def load_bundle():
    return joblib.load("final_model_bundle.joblib")


@st.cache_data
def load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


bundle = load_bundle()
selected_info = load_json("selected_variables.json", {})
threshold_info = load_json("model_threshold.json", {"threshold": 0.5})

PREDICTORS = bundle["predictors"]
CATEGORICAL_VARS = set(bundle["categorical_predictors"])
CATEGORY_LEVELS = bundle["category_levels"]
CATEGORY_MAPPINGS = bundle.get("category_mappings", {})
MODELS = bundle["fitted_models"]
PREPROCESSORS = bundle["preprocessors"]
IMPUTERS = bundle["imputers"]
VARIABLE_LABELS = bundle.get("variable_labels", {})
DEFAULTS = bundle.get("defaults", {})
EXCLUDED = bundle.get("excluded_predictors", [])
THRESHOLD = float(threshold_info.get("threshold", 0.5))


def label_of(var: str) -> str:
    return VARIABLE_LABELS.get(var, var)


def level_key(v) -> str:
    if pd.isna(v):
        return "<MISSING>"
    try:
        return f"NUM::{float(v):.12g}"
    except Exception:
        return f"STR::{str(v).strip()}"


def format_category(var: str, value):
    # 将分类变量显示为中文
    try:
        vf = float(value)
        if var == "smoking":
            if vf == 0:
                return "0 / 否"
            if vf == 1:
                return "1 / 是"
        if var == "Fracturetype":
            if vf == 1:
                return "1 / 股骨颈骨折"
            if vf == 2:
                return "2 / 转子间骨折"
            if vf.is_integer():
                return f"骨折类型编码 {int(vf)}"
        if vf.is_integer():
            return f"编码 {int(vf)}"
    except Exception:
        pass
    return str(value)


def build_raw_input() -> pd.DataFrame:
    st.header("患者信息")
    values = {}

    for var in PREDICTORS:
        label = label_of(var)
        default = DEFAULTS.get(var, 0)

        if var in CATEGORICAL_VARS:
            levels = CATEGORY_LEVELS.get(var, [0, 1])
            display_to_raw = {format_category(var, x): x for x in levels}
            options = list(display_to_raw.keys())
            default_display = format_category(var, default)
            index = options.index(default_display) if default_display in options else 0
            chosen = st.selectbox(label, options=options, index=index)
            values[var] = display_to_raw[chosen]
        else:
            values[var] = st.number_input(label, value=float(default), step=1.0)

    return pd.DataFrame([values], columns=PREDICTORS)


def encode_raw_categories(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    for c in PREDICTORS:
        if c not in CATEGORICAL_VARS:
            out[c] = pd.to_numeric(out[c], errors="coerce")

    for c in CATEGORICAL_VARS:
        mapping = CATEGORY_MAPPINGS.get(c, {})
        out[c] = out[c].map(lambda x: mapping.get(level_key(x), np.nan))

    return out[PREDICTORS]


def snap_categories(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    for c in CATEGORICAL_VARS:
        k = len(CATEGORY_LEVELS.get(c, []))
        if k <= 1:
            out[c] = 0
        else:
            out[c] = np.clip(np.rint(out[c]), 0, k - 1).astype(int)

    return out


def predict_probability(raw_df: pd.DataFrame) -> float:
    encoded = encode_raw_categories(raw_df)
    probs = []

    for model, preprocessor, imputer in zip(MODELS, PREPROCESSORS, IMPUTERS):
        arr = imputer.transform(encoded)
        model_df = pd.DataFrame(arr, columns=PREDICTORS)
        model_df = snap_categories(model_df)
        X = preprocessor.transform(model_df[PREDICTORS])
        probs.append(float(model.predict_proba(X)[0, 1]))

    return float(np.mean(probs))


st.title("老年髋部骨折术后独立行走能力恢复预测计算器")
st.caption("模型：LASSO逻辑回归模型。结局编码：1表示丧失行走能力/不能独立行走；0表示恢复行走能力。")
st.warning("本工具为研究型预测模型原型，仅用于科研展示和临床辅助参考，不能替代医生判断。")

with st.expander("模型信息", expanded=False):
    st.write("模型：**LASSO逻辑回归模型**")
    st.write("判定阈值：", THRESHOLD)
    st.write("排除变量：", EXCLUDED if EXCLUDED else "无")
    st.write("输入变量：")
    st.write([label_of(v) for v in PREDICTORS])

    lasso_selected = selected_info.get("lasso_selected_variables", [])
    if lasso_selected:
        st.write("LASSO筛选出的变量：")
        st.write([label_of(v) for v in lasso_selected])

raw_input = build_raw_input()

if st.button("开始计算", type="primary"):
    risk_loss = predict_probability(raw_input)
    prob_recovery = 1.0 - risk_loss

    st.subheader("预测结果")
    st.metric("丧失行走能力风险（结局=1）", f"{risk_loss * 100:.1f}%")
    st.metric("恢复行走能力概率（结局=0）", f"{prob_recovery * 100:.1f}%")

    if risk_loss >= THRESHOLD:
        st.error("预测结果：患者丧失行走能力/不能独立行走风险较高。")
    else:
        st.success("预测结果：患者恢复行走能力概率较高。")

    with st.expander("查看输入值"):
        display_df = raw_input.rename(columns={v: label_of(v) for v in raw_input.columns})
        st.dataframe(display_df)
