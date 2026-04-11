import pandas as pd
from pathlib import Path

# 读取Excel文件
excel_path = Path(__file__).parent / "doc_raw" / "化工故障案例集_v1.xlsx.xlsx"

# 读取所有工作表
xl_file = pd.ExcelFile(excel_path)
print(f"工作表数量: {len(xl_file.sheet_names)}")
print(f"工作表名称: {xl_file.sheet_names}")

# 检查每个工作表的结构
for sheet_name in xl_file.sheet_names:
    print(f"\n=== 工作表: {sheet_name} ===")
    df = pd.read_excel(xl_file, sheet_name=sheet_name)
    print(f"列名: {df.columns.tolist()}")
    print(f"行数: {len(df)}")
    print("前5行数据:")
    print(df.head())
    print("\n数据类型:")
    print(df.dtypes)
