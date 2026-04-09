"""Detect and handle outliers in TE dataset using the 3-sigma rule."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def get_input_file(data_dir: Path) -> Path:
    """Prefer filled dataset if available, otherwise fallback to raw dataset."""
    filled_path = data_dir / "TE_dataset_filled.csv"
    raw_path = data_dir / "TE_dataset.csv"

    if filled_path.exists():
        return filled_path
    if raw_path.exists():
        return raw_path

    raise FileNotFoundError("No dataset found. Expected TE_dataset_filled.csv or TE_dataset.csv")


def main() -> None:
    project_root = Path(__file__).resolve().parent
    data_dir = project_root / "data"
    input_path = get_input_file(data_dir)
    output_path = data_dir / "TE_dataset_outlier_clipped.csv"

    df = pd.read_csv(input_path)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    outlier_counts: dict[str, int] = {}

    for col in numeric_cols:
        mean_val = df[col].mean()
        std_val = df[col].std()

        if pd.isna(std_val) or std_val == 0:
            outlier_counts[col] = 0
            continue

        lower = mean_val - 3 * std_val
        upper = mean_val + 3 * std_val

        mask = (df[col] < lower) | (df[col] > upper)
        outlier_counts[col] = int(mask.sum())

        df[col] = df[col].clip(lower=lower, upper=upper)

    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print("=" * 80)
    print(f"Input file: {input_path}")
    print(f"Output file: {output_path}")
    print(f"Numeric columns processed: {len(numeric_cols)}")

    print("=" * 80)
    print("Outlier count per numeric column (3-sigma)")
    count_df = pd.DataFrame(
        {"column": list(outlier_counts.keys()), "outlier_count": list(outlier_counts.values())}
    )
    print(count_df.to_string(index=False))


if __name__ == "__main__":
    main()
