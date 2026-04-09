"""Day-1 deliverables: feature engineering and reports for TE dataset."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


def detect_target_column(df: pd.DataFrame) -> str:
    for candidate in ("target", "TARGET", "Target", "status", "STATUS", "Status"):
        if candidate in df.columns:
            return candidate
    raise ValueError("Target column not found. Expected one of target/STATUS variants.")


def pick_input_csv(data_dir: Path) -> Path:
    candidates = [
        data_dir / "TE_dataset_standardized.csv",
        data_dir / "TE_dataset_outlier_clipped.csv",
        data_dir / "TE_dataset_filled.csv",
        data_dir / "TE_dataset.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("No cleaned or standardized TE dataset file found in data directory.")


def get_top_features_by_correlation(df: pd.DataFrame, target_col: str, top_n: int = 15) -> pd.DataFrame:
    if not pd.api.types.is_numeric_dtype(df[target_col]):
        raise TypeError(f"Target column '{target_col}' must be numeric to compute correlation.")

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    feature_cols = [col for col in numeric_cols if col != target_col]

    corr_series = df[feature_cols + [target_col]].corr(numeric_only=True)[target_col].drop(labels=[target_col])
    result = pd.DataFrame(
        {
            "feature": corr_series.index,
            "correlation_with_target": corr_series.values,
            "abs_correlation": corr_series.abs().values,
        }
    ).sort_values("abs_correlation", ascending=False)

    return result.head(top_n).reset_index(drop=True)


def build_processed_dataset(df: pd.DataFrame, target_col: str, top_features: list[str]) -> pd.DataFrame:
    meta_cols = [col for col in ["source_file", "source_format"] if col in df.columns]
    keep_cols = meta_cols + top_features + [target_col]
    keep_cols = list(dict.fromkeys(keep_cols))
    return df[keep_cols].copy()


def write_quality_report(
    report_path: Path,
    input_path: Path,
    df: pd.DataFrame,
    target_col: str,
    top_corr_df: pd.DataFrame,
    processed_path: Path,
) -> None:
    missing_count = df.isna().sum()
    total_missing = int(missing_count.sum())
    duplicate_count = int(df.duplicated().sum())

    non_zero_missing = missing_count[missing_count > 0].sort_values(ascending=False)
    dtypes_summary = df.dtypes.astype(str).value_counts().to_dict()

    target_stats = df[target_col].describe()
    target_top_values = df[target_col].value_counts().head(10)

    lines = [
        "# 数据质量报告",
        "",
        f"- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 输入数据: {input_path}",
        f"- 行数: {df.shape[0]}",
        f"- 列数: {df.shape[1]}",
        f"- target列: {target_col}",
        "",
        "## 数据类型统计",
        "",
    ]

    for dtype_name, count in dtypes_summary.items():
        lines.append(f"- {dtype_name}: {count}")

    lines.extend(
        [
            "",
            "## 缺失值检查",
            "",
            f"- 总缺失值数量: {total_missing}",
        ]
    )

    if non_zero_missing.empty:
        lines.append("- 所有列缺失值均为0")
    else:
        lines.append("- 缺失值>0的列如下:")
        for col, val in non_zero_missing.items():
            lines.append(f"  - {col}: {int(val)}")

    lines.extend(
        [
            "",
            "## 重复值检查",
            "",
            f"- 重复行数: {duplicate_count}",
            "",
            "## target基本统计",
            "",
            f"- count: {target_stats['count']}",
            f"- mean: {target_stats.get('mean', 'N/A')}",
            f"- std: {target_stats.get('std', 'N/A')}",
            f"- min: {target_stats.get('min', 'N/A')}",
            f"- max: {target_stats.get('max', 'N/A')}",
            "",
            "## target高频值(Top 10)",
            "",
        ]
    )

    for value, count in target_top_values.items():
        lines.append(f"- {value}: {int(count)}")

    lines.extend(["", "## 与target相关性Top15特征", "", "| 特征 | 相关系数 | 绝对相关系数 |", "|---|---:|---:|"])

    for _, row in top_corr_df.iterrows():
        lines.append(
            f"| {row['feature']} | {row['correlation_with_target']:.6f} | {row['abs_correlation']:.6f} |"
        )

    lines.extend(["", "## 产出文件", "", f"- 处理后数据: {processed_path}"])

    report_path.write_text("\n".join(lines), encoding="utf-8")


def write_feature_plan(plan_path: Path, target_col: str, top_corr_df: pd.DataFrame, processed_path: Path) -> None:
    lines = [
        "# 特征工程方案",
        "",
        "## 目标",
        "",
        f"- 面向目标列 `{target_col}` 构建高价值特征子集",
        "- 用相关系数方法筛选首批关键特征，作为第1天交付基础版本",
        "",
        "## 第1天已完成",
        "",
        "- 使用标准化数据进行特征筛选",
        "- 计算数值特征与target的皮尔逊相关系数",
        "- 按绝对相关系数排序，选取Top 15关键特征",
        f"- 生成处理后数据集: {processed_path}",
        "",
        "## Top 15关键特征",
        "",
        "| 排名 | 特征 | 相关系数 | 绝对相关系数 |",
        "|---:|---|---:|---:|",
    ]

    for idx, (_, row) in enumerate(top_corr_df.iterrows(), start=1):
        lines.append(
            f"| {idx} | {row['feature']} | {row['correlation_with_target']:.6f} | {row['abs_correlation']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## 下一步建议(第2天)",
            "",
            "- 使用Top 15特征训练基线分类模型(如RandomForest/XGBoost)",
            "- 增加非线性特征与交互特征",
            "- 进行特征重要性复核(树模型重要度/SHAP)",
            "- 结合时序窗口构造动态特征",
        ]
    )

    plan_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    project_root = Path(__file__).resolve().parent
    data_dir = project_root / "data"

    input_path = pick_input_csv(data_dir)
    processed_path = data_dir / "TE_processed.csv"
    quality_report_path = project_root / "数据质量报告.md"
    feature_plan_path = project_root / "特征工程方案.md"

    df = pd.read_csv(input_path)
    target_col = detect_target_column(df)

    top_corr_df = get_top_features_by_correlation(df, target_col, top_n=15)
    top_features = top_corr_df["feature"].tolist()

    processed_df = build_processed_dataset(df, target_col, top_features)
    processed_df.to_csv(processed_path, index=False, encoding="utf-8-sig")

    write_quality_report(quality_report_path, input_path, df, target_col, top_corr_df, processed_path)
    write_feature_plan(feature_plan_path, target_col, top_corr_df, processed_path)

    print("=" * 80)
    print(f"Input file: {input_path}")
    print(f"Target column: {target_col}")
    print("Top 15 features by absolute correlation:")
    print(top_corr_df.to_string(index=False))
    print("=" * 80)
    print(f"Saved processed dataset: {processed_path}")
    print(f"Saved quality report: {quality_report_path}")
    print(f"Saved feature engineering plan: {feature_plan_path}")


if __name__ == "__main__":
    main()
