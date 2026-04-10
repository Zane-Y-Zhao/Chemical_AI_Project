# knowledge_base/prompt_engineering.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage

def build_decision_prompt(
    prediction_data: dict, 
    retrieved_knowledge: list, 
    safety_rules: list
) -> str:
    """
    构建三层约束提示词：
    1. 角色约束：必须以化工安全工程师身份发言
    2. 数据约束：所有结论必须基于prediction_data数值与retrieved_knowledge原文
    3. 安全约束：必须引用safety_rules中至少1条条款作为决策依据
    """
    # 提取关键预测值（适配冯申雨API格式）
    pred_value = prediction_data.get("prediction", "unknown")
    confidence = prediction_data.get("confidence", 0.0)
    
    # 构建知识依据摘要（避免长文本淹没关键信息）
    knowledge_summary = "\n".join([
        f"- 【规则{idx+1}】{doc.page_content[:60]}...（来源：{doc.metadata['source']}）"
        for idx, doc in enumerate(retrieved_knowledge[:2])
    ])
    
    # 安全条款强制引用（来自杨泽彤安全规程）
    safety_clause = safety_rules[0].page_content if safety_rules else "无安全条款提供"
    
    system_prompt = f"""你是一名资深化工安全工程师，正在为余热回收系统生成操作建议。
    必须严格遵守以下原则：
    ① 所有建议必须基于以下【实时预测数据】和【知识库原文】；
    ② 每条建议必须明确引用至少1条【安全条款】；
    ③ 若预测置信度<0.85，必须标注"需人工复核"；
    ④ 禁止编造任何未在输入中出现的参数、单位或逻辑关系。"""

    human_prompt = f"""【实时预测数据】
    - 预测类型：{pred_value}
    - 置信度：{confidence:.2f}
    - 时间戳：{prediction_data.get('timestamp', 'N/A')}

    【知识库原文依据】
    {knowledge_summary}

    【强制引用的安全条款】
    {safety_clause}

    请生成一条具体、可执行、符合安全规范的操作建议（限100字内）："""

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
