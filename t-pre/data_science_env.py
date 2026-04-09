"""One-click imports for a Python data science environment."""

import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import torch
import matplotlib
import matplotlib.pyplot as plt
import sklearn
from sklearn import preprocessing
from sklearn.preprocessing import (
    LabelEncoder,
    MinMaxScaler,
    Normalizer,
    OneHotEncoder,
    PolynomialFeatures,
    RobustScaler,
    StandardScaler,
)


def configure_chinese_display() -> None:
    """Configure Matplotlib to display Chinese text correctly."""
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False


def show_environment_info() -> None:
    """Print basic package version information for quick validation."""
    print("Data science environment loaded successfully.")
    print(f"pandas: {pd.__version__}")
    print(f"numpy: {np.__version__}")
    print(f"matplotlib: {matplotlib.__version__}")
    print(f"scikit-learn: {sklearn.__version__}")
    print(f"torch: {torch.__version__}")


configure_chinese_display()


if __name__ == "__main__":
    show_environment_info()
