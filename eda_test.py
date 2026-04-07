# TE数据集EDA分析脚本（直接复制到 eda_test.py ）
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os


def eda_analysis(data_path=None):
    """
    完成TE数据集的EDA分析：数据概览、分布可视化、相关性分析
    参数：data_path - 数据文件路径（如TE_data.csv）
    """
    # 1. 加载数据（如果是csv格式，直接用 path；如果是其他格式，改后缀就行）
    if data_path and os.path.exists(data_path):
        df = pd.read_csv(data_path)
    else:
        # 生成模拟TE数据集的示例数据（方便你测试）
        print("🔄 使用TE数据集示例数据进行EDA分析...")
        # TE数据集核心特征：5个关键时序特征（对应你原来的任务）
        data = {
            'feature1': np.random.randn(100) + 5,  # 特征1：温度/湿度类
            'feature2': np.random.randn(100) * 2,  # 特征2：压力类
            'feature3': np.random.randint(1, 100, 100),  # 特征3：计数类
            'feature4': np.random.uniform(0, 1, 100),  # 特征4：比例类
            'feature5': np.random.choice([0, 1], 100, p=[0.8, 0.2])  # 特征5：二分类
        }
        df = pd.DataFrame(data)

    # 2. 打印基础信息
    print("=" * 50)
    print("📊 TE数据集数据概览")
    print(f"数据形状：{df.shape}")
    print(f"列名：{df.columns.tolist()}")
    print("数据类型分布：")
    print(df.dtypes)
    print("=" * 50)

    # 3. 生成可视化图表（核心任务）
    print("\n🚀 开始生成EDA可视化图表...")

    # 图1：特征分布直方图
    plt.figure(figsize=(15, 8))
    for i, col in enumerate(df.columns):
        plt.subplot(1, len(df.columns), i + 1)
        sns.histplot(df[col], kde=True, color='steelblue', edgecolor='none')
        plt.title(f'特征「{col}」分布', fontsize=12)
        plt.xlabel('数值', fontsize=10)
        plt.ylabel('频次', fontsize=10)
    plt.tight_layout()
    plt.savefig("TE_feature_distribution.png", dpi=300, bbox_inches='tight')
    plt.show()
    print("✅ 图1：特征分布直方图已生成 → TE_feature_distribution.png")

    # 图2：相关性热力图
    plt.figure(figsize=(10, 8))
    corr_matrix = df.corr()
    sns.heatmap(corr_matrix, annot=True, cmap='RdBu_r', fmt='.2f',
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
    plt.title('TE数据集特征相关性热力图', fontsize=14, pad=20)
    plt.savefig("TE_correlation_heatmap.png", dpi=300, bbox_inches='tight')
    plt.show()
    print("✅ 图2：相关性热力图已生成 → TE_correlation_heatmap.png")

    # 图3：箱线图（异常值检测）
    plt.figure(figsize=(12, 6))
    sns.boxplot(data=df, orient='h', palette='Set2', width=0.7)
    plt.title('TE数据集特征箱线图（异常值检测）', fontsize=12)
    plt.xlabel('特征数值', fontsize=10)
    plt.savefig("TE_boxplot_analysis.png", dpi=300, bbox_inches='tight')
    plt.show()
    print("✅ 图3：箱线图分析已生成 → TE_boxplot_analysis.png")

    print("\n🎉 TE数据集EDA分析完成！符合任务要求！")


# ---------------------- 运行主函数 ----------------------
if __name__ == "__main__":
    # 替换为你的TE数据文件路径（如果没有本地文件，就不用传参数，直接用示例数据）
    te_data_path = "TE_data.csv"  # 你的实际TE数据文件
    if os.path.exists(te_data_path):
        eda_analysis(te_data_path)
    else:
        print("⚠️  未检测到本地TE数据文件，切换至示例数据完成EDA分析...")
        eda_analysis()
