import pandas as pd
from pathlib import Path

# 读取Excel文件
excel_path = Path(__file__).parent / "doc_raw" / "化工故障案例集_v1.xlsx.xlsx"

print(f"检查文件: {excel_path}")
print(f"文件是否存在: {excel_path.exists()}")

if excel_path.exists():
    try:
        # 读取Excel文件
        xl_file = pd.ExcelFile(excel_path)
        print(f"\n工作表数量: {len(xl_file.sheet_names)}")
        print(f"工作表名称: {xl_file.sheet_names}")
        
        # 检查每个工作表的结构
        for sheet_name in xl_file.sheet_names:
            print(f"\n=== 工作表: {sheet_name} ===")
            df = pd.read_excel(xl_file, sheet_name=sheet_name)
            print(f"行数: {len(df)}")
            print(f"列数: {len(df.columns)}")
            print(f"列名: {list(df.columns)}")
            
            # 显示前几行数据
            print("\n前5行数据:")
            print(df.head())
            
            # 检查是否包含所需列
            has_fault = any("故障" in str(col) for col in df.columns)
            has_reason = any("原因" in str(col) for col in df.columns)
            has_action = any("处置" in str(col) or "步骤" in str(col) or "措施" in str(col) for col in df.columns)
            
            print(f"\n包含故障列: {has_fault}")
            print(f"包含原因列: {has_reason}")
            print(f"包含处置列: {has_action}")
            
    except Exception as e:
        print(f"读取Excel文件失败: {str(e)}")
else:
    print("文件不存在")
