import pandas as pd
import os

def load_te_data(file_path):
    # 加 r 消除转义警告
    return pd.read_csv(file_path, sep=r'\s+', header=None)

data_path = r"D:\TE_Project1\data"

normal_df = load_te_data(os.path.join(data_path, "d00.dat"))
fault1_df = load_te_data(os.path.join(data_path, "d01.dat"))

# 用 assign 消除性能警告
normal_df = normal_df.assign(label=0)
fault1_df = fault1_df.assign(label=1)

df = pd.concat([normal_df, fault1_df], axis=0).reset_index(drop=True)

print(f"数据读取成功！形状：{df.shape}")
df = df.dropna().drop_duplicates()
print(f"清洗后形状：{df.shape}")

df.to_csv(os.path.join(data_path, "te_clean.csv"), index=False)
print("✅ 标准TE数据已保存为te_clean.csv，任务完成！")
