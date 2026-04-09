"""Standardize TE dataset feature columns and persist the scaler."""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler


def detect_target_column(df: pd.DataFrame) -> str | None:
    """Detect target column from common naming conventions."""
    for candidate in ("target", "TARGET", "Target", "status", "STATUS", "Status"):
        if candidate in df.columns:
            return candidate
    return None


def pick_input_csv(data_dir: Path) -> Path:
    """Prefer latest processed dataset if available."""
    candidates = [
        data_dir / "TE_dataset_outlier_clipped.csv",
        data_dir / "TE_dataset_filled.csv",
        data_dir / "TE_dataset.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("No input dataset found in data directory.")


def standardize_features(df: pd.DataFrame, target_col: str | None) -> tuple[pd.DataFrame, StandardScaler, list[str]]:
    """Standardize numeric feature columns while excluding target column."""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    feature_cols = [col for col in numeric_cols if col != target_col]

    scaler = StandardScaler()
    if feature_cols:
        df.loc[:, feature_cols] = scaler.fit_transform(df[feature_cols])

    return df, scaler, feature_cols


def main() -> None:
    project_root = Path(__file__).resolve().parent
    data_dir = project_root / "data"

    input_path = pick_input_csv(data_dir)
    output_path = data_dir / "TE_dataset_standardized.csv"
    scaler_path = data_dir / "scaler.pkl"

    df = pd.read_csv(input_path)
    target_col = detect_target_column(df)

    standardized_df, scaler, feature_cols = standardize_features(df, target_col)

    standardized_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    joblib.dump(scaler, scaler_path)

    print("=" * 80)
    print(f"Input file: {input_path}")
    print(f"Output file: {output_path}")
    print(f"Scaler file: {scaler_path}")
    print(f"Detected target column: {target_col}")
    print(f"Standardized feature columns: {len(feature_cols)}")
    print("=" * 80)
    print("Standardized dataset preview (first 5 rows):")
    print(standardized_df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
