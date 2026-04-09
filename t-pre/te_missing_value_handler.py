"""Handle missing values for TE dataset.

Rules:
1) Fill numeric columns with mean values.
2) Do not process target column.
3) Print missing-value check after filling.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def detect_target_column(df: pd.DataFrame) -> str | None:
    """Detect target column name from common choices in this project."""
    for candidate in ("target", "TARGET", "Target", "status", "STATUS", "Status"):
        if candidate in df.columns:
            return candidate
    return None


def main() -> None:
    project_root = Path(__file__).resolve().parent
    input_csv = project_root / "data" / "TE_dataset.csv"
    output_csv = project_root / "data" / "TE_dataset_filled.csv"

    if not input_csv.exists():
        raise FileNotFoundError(f"Dataset file not found: {input_csv}")

    df = pd.read_csv(input_csv)

    target_col = detect_target_column(df)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    cols_to_fill = [col for col in numeric_cols if col != target_col]
    if cols_to_fill:
        df[cols_to_fill] = df[cols_to_fill].fillna(df[cols_to_fill].mean())

    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    missing_count = df.isna().sum()
    missing_rate = (missing_count / len(df)) * 100
    missing_summary = pd.DataFrame(
        {
            "missing_count": missing_count,
            "missing_rate_percent": missing_rate.round(4),
        }
    )

    print("=" * 80)
    print(f"Input file: {input_csv}")
    print(f"Output file: {output_csv}")
    print(f"Detected target column: {target_col}")
    print(f"Filled numeric columns (exclude target): {len(cols_to_fill)}")

    print("=" * 80)
    print("Missing-value check after filling")
    print(missing_summary)


if __name__ == "__main__":
    main()
