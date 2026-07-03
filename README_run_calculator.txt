# Walking web calculator

## 文件说明

本文件夹由建模脚本自动生成，包含：

```text
app.py
requirements.txt
final_model_bundle.joblib
final_model.pkl
final_preprocessor.pkl
selected_variables.json
model_threshold.json
README_run_calculator.txt
```

## 结局编码

```text
UnableWalking = 1：丧失行走能力 / 不能独立行走
UnableWalking = 0：恢复行走能力
```

## 骨折类型编码

```text
Fracturetype = 1：股骨颈骨折
Fracturetype = 2：转子间骨折
```

网页计算器输出：

```text
丧失行走能力风险 P(UnableWalking=1)
恢复行走能力概率 P(UnableWalking=0) = 1 - P(UnableWalking=1)
```

## 运行方式

在本文件夹中运行：

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

如果在 GitHub Codespaces 中运行，打开 Ports / 端口 面板中的 8501 链接即可访问。

## 注意

`final_model_bundle.joblib` 是网页计算器实际使用的完整模型包，包含多重插补模型、预处理器、变量水平和默认值。

`final_model.pkl` 和 `final_preprocessor.pkl` 是为了兼容和检查而额外保存的单个代表模型组件；正式网页预测使用 `final_model_bundle.joblib`。
