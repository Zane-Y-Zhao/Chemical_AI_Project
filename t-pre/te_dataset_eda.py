"""Load TE_dataset.csv and run basic exploratory data analysis."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def main() -> None:
    project_root = Path(__file__).resolve().parent
    csv_path = project_root / "data" / "TE_dataset.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    print("=" * 80)
    print("1) Data shape")
    print(df.shape)

    print("=" * 80)
    print("2) Column names")
    print(df.columns.tolist())

    print("=" * 80)
    print("3) First 5 rows")
    print(df.head(5).to_string(index=False))

    print("=" * 80)
    print("4) Last 5 rows")
    print(df.tail(5).to_string(index=False))

    print("=" * 80)
    print("5) Data types")
    print(df.dtypes)

    print("=" * 80)
    print("6) Missing value statistics")
    missing_count = df.isna().sum()
    missing_rate = (missing_count / len(df)) * 100
    missing_summary = pd.DataFrame(
        {
            "missing_count": missing_count,
            "missing_rate_percent": missing_rate.round(4),
        }
    )
    print(missing_summary)

    print("=" * 80)
    print("7) Number of duplicated rows")
    print(int(df.duplicated().sum()))

    print("=" * 80)
    print("8) Descriptive statistics for numeric fields")
    numeric_description = df.describe(include=["number"]).transpose()
    print(numeric_description)


if __name__ == "__main__":
    main()
