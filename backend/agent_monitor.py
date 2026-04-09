import time
import os
import sys

# --- 1. 确保能正确导入 database ---
# 将 backend 目录添加到系统路径，防止导入错误
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from database import SessionLocal, HeatData

def smart_agent_check():
    print("🤖 智能体监控程序已启动... 正在监测温度...")

    # 记录上一次已经报警的那条数据的 ID
    last_alerted_id = 0

    while True:
        try:
            # 创建数据库会话
            db = SessionLocal()

            # --- 2. 极速查询：按时间倒序取最新的一条 ---
            # 使用 desc() 确保拿到的是最新插入的数据
            latest_data = db.query(HeatData).order_by(HeatData.timestamp.desc()).first()

            if latest_data:
                # 检查温度是否超标 (例如 > 90度)
                if latest_data.temperature > 90:

                    # --- 3. 关键逻辑：只有当 ID 不同时才报警 ---
                    # 如果这条数据的 ID 和上次报警的 ID 不一样，说明是新产生的高温数据
                    if latest_data.id != last_alerted_id:
                        print(f"⚠️ 警告：检测到高温！当前温度 {latest_data.temperature}℃ "
                              f"(时间: {latest_data.timestamp}) [数据ID: {latest_data.id}]")

                        # 更新记录，标记这条数据已经报过警了
                        last_alerted_id = latest_data.id

                    # 如果是同一条数据（ID相同），什么都不做，直接跳过，避免刷屏

                # 如果温度正常 (< 90)，可以选择不打印，或者打印一行绿色日志
                # else:
                #     print(f"✅ 温度正常: {latest_data.temperature}℃")

            db.close()

            # --- 4. 极短的休眠 ---
            # 只休眠 0.1 秒，保证反应速度极快，不会漏掉模拟器发来的数据
            time.sleep(0.1)

        except Exception as e:
            print(f"❌ 发生错误: {e}")
            time.sleep(1)

if __name__ == "__main__":
    smart_agent_check()