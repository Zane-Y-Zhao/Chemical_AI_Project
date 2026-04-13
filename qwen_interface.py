import json
import sys
import os
from knowledge_base.llm_config import call_qwen

def call_qwen_api(prompt: str) -> list:
    """
    调用千问API，返回JSON格式的假设列表
    
    Args:
        prompt: 提示词
        
    Returns:
        list: 假设列表，每个假设包含参数调整建议
    """
    # 确保日志目录存在
    log_dir = "./logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 日志文件
    log_file = os.path.join(log_dir, "auto_research_test.log")
    
    # 自定义日志函数
    def log(message):
        print(message, file=sys.stdout)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    
    log("[QWen] 开始调用千问API...")
    log(f"[QWen] 提示词长度：{len(prompt)}")
    
    try:
        # 调用千问API
        import time
        start_time = time.time()
        log(f"[QWen] 调用开始时间：{start_time}")
        
        response = call_qwen(prompt)
        
        end_time = time.time()
        log(f"[QWen] 调用结束时间：{end_time}")
        log(f"[QWen] 调用耗时：{end_time - start_time:.2f}秒")
        log(f"[QWen] 响应长度：{len(response)}")
        log(f"[QWen] 响应内容：{response[:100]}...")
        
        # 检查是否调用失败
        if response.startswith("[ERROR]"):
            log(f"[QWen] 调用失败：{response}")
            # 返回默认假设
            default_hypotheses = [
                {"temp_change": 5, "description": "提高温度5度"},
                {"temp_change": -3, "description": "降低温度3度"},
                {"temp_change": 0, "description": "保持温度不变"}
            ]
            log(f"[QWen] 返回默认假设：{default_hypotheses}")
            return default_hypotheses
        
        # 解析响应，提取假设
        log("[QWen] 开始解析响应...")
        try:
            hypotheses = json.loads(response)
            if isinstance(hypotheses, list):
                log(f"[QWen] 解析成功，获取到 {len(hypotheses)} 个假设")
                return hypotheses
            else:
                log("[QWen] 响应不是列表格式")
                # 返回默认假设
                default_hypotheses = [
                    {"temp_change": 5, "description": "提高温度5度"},
                    {"temp_change": -3, "description": "降低温度3度"},
                    {"temp_change": 0, "description": "保持温度不变"}
                ]
                log(f"[QWen] 返回默认假设：{default_hypotheses}")
                return default_hypotheses
        except json.JSONDecodeError as e:
            log(f"[QWen] JSON解析失败：{str(e)}")
            # 如果响应不是JSON格式，尝试提取假设
            import re
            temp_changes = re.findall(r'温度(?:提高|降低|调整)\s*(\d+)度', response)
            if temp_changes:
                log(f"[QWen] 提取到温度变化：{temp_changes}")
                extracted_hypotheses = [
                    {"temp_change": int(change), "description": f"调整温度{change}度"} 
                    for change in temp_changes[:3]
                ]
                log(f"[QWen] 返回提取的假设：{extracted_hypotheses}")
                return extracted_hypotheses
            else:
                log("[QWen] 未能提取温度变化")
                # 返回默认假设
                default_hypotheses = [
                    {"temp_change": 5, "description": "提高温度5度"},
                    {"temp_change": -3, "description": "降低温度3度"},
                    {"temp_change": 0, "description": "保持温度不变"}
                ]
                log(f"[QWen] 返回默认假设：{default_hypotheses}")
                return default_hypotheses
    except Exception as e:
        log(f"[QWen] 调用千问API失败：{str(e)}")
        import traceback
        traceback_str = traceback.format_exc()
        log(f"[QWen] 详细错误信息：{traceback_str}")
        # 返回默认假设
        default_hypotheses = [
            {"temp_change": 5, "description": "提高温度5度"},
            {"temp_change": -3, "description": "降低温度3度"},
            {"temp_change": 0, "description": "保持温度不变"}
        ]
        log(f"[QWen] 返回默认假设：{default_hypotheses}")
        return default_hypotheses
