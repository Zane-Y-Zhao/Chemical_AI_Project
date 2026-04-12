# knowledge_base/prompt_engineering.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage

def build_decision_prompt(
    prediction_data: dict, 
    retrieved_knowledge: list, 
    safety_rules: list
) -> str:
    """
    构建双路径决策提示词：
    1. 主路径（confidence≥0.85）：调用千问生成建议
    2. 降级路径（confidence<0.85）：从杨泽彤案例集直接提取处置步骤
    3. 安全熔断规则：若检索结果未包含安全操作规程，返回硬错误
    """
    # 提取关键预测值（适配韩永盛API格式）
    pred_value = prediction_data.get("prediction", "unknown")
    confidence = prediction_data.get("confidence", 0.0)
    
    # 安全熔断规则：检查是否包含安全操作规程
    safety_operation_included = any("安全操作规程" in doc.metadata.get('source', '') for doc in retrieved_knowledge)
    if not safety_operation_included:
        return "[ERROR] 安全条款缺失，请人工介入"
    
    # 构建知识依据摘要（摘要式呈现，避免长文本）
    knowledge_summary = "\n".join([
        f"- 【规则{idx+1}】{doc.page_content[:40]}...（来源：{doc.metadata['source']}）"
        for idx, doc in enumerate(retrieved_knowledge[:2])
    ])
    
    # 安全条款强制引用（来自杨泽彤安全规程）
    safety_clause = safety_rules[0].page_content[:80] + "..." if safety_rules else "无安全条款提供"
    
    # 双路径决策逻辑
    if confidence >= 0.85:
        # 主路径：调用千问生成建议
        system_prompt = "你是化工安全工程师，为余热回收系统生成操作建议，必须基于实时数据和知识库原文，引用安全条款，不编造参数。"

        human_prompt = f"""【实时预测数据】
- 预测类型：{pred_value}
- 置信度：{confidence:.2f}
- 时间戳：{prediction_data.get('timestamp', 'N/A')}

【知识库原文依据】
{knowledge_summary}

【强制引用的安全条款】
{safety_clause}

请生成一条具体、可执行、符合安全规范的操作建议（限100字内）："""
    else:
        # 降级路径：从杨泽彤案例集直接提取处置步骤
        system_prompt = "你是化工安全工程师，为余热回收系统生成操作建议，必须基于实时数据和知识库原文，引用安全条款，标注需人工复核，不编造参数。"

        human_prompt = f"""【实时预测数据】
- 预测类型：{pred_value}
- 置信度：{confidence:.2f}
- 时间戳：{prediction_data.get('timestamp', 'N/A')}

【知识库原文依据】
{knowledge_summary}

【强制引用的安全条款】
{safety_clause}

请生成一条具体、可执行、符合安全规范的操作建议（限200字内）："""

    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ])
    prompt_value = prompt_template.format()
    return prompt_value.to_string() if hasattr(prompt_value, 'to_string') else str(prompt_value)

# 辅助函数：从知识库提取安全条款（专用于safety_rules参数）
def get_safety_rules(vectorstore, top_k=1):
    """从Chroma中精准检索安全类规则"""
    results = vectorstore.similarity_search(
        query="高温管道表面温度限值、泄漏应急处置、安全操作边界",
        k=top_k,
        filter={"source": {"$contains": "安全操作规程"}}
    )
    return results
