# knowledge_base/document_processor.py
import os
import re
from pathlib import Path
from docx import Document
import PyPDF2
import pandas as pd
from tqdm import tqdm

def clean_text(text: str) -> str:
    """化工文档专用清洗：保留专业术语，剔除无意义符号"""
    # 移除多余空白与换行
    text = re.sub(r'\s+', ' ', text)
    # 移除页眉页脚常见模式（如"第X页 共Y页"、"©2025 化工安全中心"）
    text = re.sub(r'第\s*\d+\s*页\s*共\s*\d+\s*页|©\d{4}.*', '', text)
    # 移除孤立数字编号（如"1. "、"2. "开头但后无实质内容）
    text = re.sub(r'^\d+\.\s*$', '', text, flags=re.MULTILINE)
    # 只保留中文、英文、数字、常用标点和特殊符号（如Δ、=、MPa等）
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\u002E\u002D\u002C\u003B\u0021\u003F\u0028\u0029\u003D\u0394]', '', text)
    # 移除连续的无意义字符
    text = re.sub(r'(.)\1{2,}', r'\1', text)
    return text.strip()

def extract_from_pdf(pdf_path: Path) -> str:
    """提取PDF文本（兼容扫描件OCR后文本）"""
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        full_text = ""
        for page in reader.pages:
            # 尝试使用不同的提取方法
            try:
                text = page.extract_text(extraction_mode="layout") or ""
            except Exception:
                text = page.extract_text() or ""
            full_text += text + "\n"
    # 尝试使用不同的编码处理
    try:
        full_text = full_text.encode('utf-8', errors='ignore').decode('utf-8')
    except Exception:
        pass
    return clean_text(full_text)

def extract_from_docx(docx_path: Path) -> str:
    """提取Word文本（保留标题层级）"""
    doc = Document(docx_path)
    full_text = ""
    for para in doc.paragraphs:
        if para.text.strip() and not para.text.strip().startswith("表") and not para.text.strip().startswith("图"):
            full_text += para.text.strip() + "\n"
    return clean_text(full_text)

def extract_from_excel(excel_path: Path) -> str:
    """提取Excel文本：按"故障现象/原因分析/处置步骤"三列切分语义块"""
    try:
        # 读取Excel文件的所有工作表
        xl_file = pd.ExcelFile(excel_path)
        full_text = ""
        
        for sheet_name in xl_file.sheet_names:
            # 读取工作表
            df = pd.read_excel(xl_file, sheet_name=sheet_name)
            
            # 查找包含"故障现象"、"原因分析"、"处置步骤"的列
            columns = df.columns.tolist()
            fault_col = None
            reason_col = None
            action_col = None
            
            for col in columns:
                col_lower = str(col).lower()
                if "故障现象" in str(col) or "故障" in col_lower:
                    fault_col = col
                elif "原因分析" in str(col) or "原因" in col_lower:
                    reason_col = col
                elif "处理措施" in str(col) or "处置" in col_lower or "步骤" in col_lower or "措施" in col_lower:
                    action_col = col
            
            # 如果找到所需列，按行提取语义块
            if fault_col and reason_col and action_col:
                for idx, row in df.iterrows():
                    fault = str(row.get(fault_col, ""))
                    reason = str(row.get(reason_col, ""))
                    action = str(row.get(action_col, ""))
                    
                    # 只处理非空行
                    if fault.strip() and reason.strip() and action.strip():
                        # 构建语义块
                        chunk = f"故障现象：{fault}\n原因分析：{reason}\n处置步骤：{action}\n"
                        full_text += chunk
            else:
                # 如果没有找到指定列，提取所有文本
                for col in df.columns:
                    for val in df[col].dropna():
                        if str(val).strip():
                            full_text += str(val) + "\n"
        
        return clean_text(full_text)
    except Exception as e:
        print(f"处理Excel文件失败：{str(e)}")
        return ""

def split_into_chunks(text: str, chunk_size: int = 300, overlap: int = 50) -> list:
    """按语义切分：优先在句号/分号/换行处分割，避免切断化工术语和带单位数值"""
    # 定义带单位数值的模式，如 ΔP=0.3MPa, 温度=85°C 等
    unit_pattern = r'[A-Za-zΔ]+\s*=\s*\d+(\.\d+)?[A-Za-z°]+'
    
    # 先标记带单位数值，避免被分割
    text = re.sub(unit_pattern, lambda m: m.group(0).replace(' ', '_SPACE_'), text)
    
    # 按句号/分号/换行处分割
    sentences = re.split(r'(?<=[。；！？])\s+|[\r\n]+', text)
    chunks = []
    current_chunk = ""
    
    for sent in sentences:
        if len(current_chunk) + len(sent) <= chunk_size:
            current_chunk += sent + " "
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sent + " "
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # 恢复带单位数值中的空格
    final_chunks = []
    for i, chunk in enumerate(chunks):
        # 恢复带单位数值中的空格
        chunk = chunk.replace('_SPACE_', ' ')
        
        if i == 0:
            final_chunks.append(chunk)
        else:
            # 确保重叠部分不会切断带单位数值
            prev_chunk = chunks[i-1].replace('_SPACE_', ' ')
            # 找到最后一个带单位数值的位置
            unit_match = re.search(unit_pattern, prev_chunk[::-1])
            if unit_match:
                # 如果重叠部分会切断带单位数值，调整重叠长度
                overlap_adjusted = min(overlap, len(prev_chunk) - unit_match.end())
                prev = prev_chunk[-overlap_adjusted:] if len(prev_chunk) > overlap_adjusted else prev_chunk
            else:
                prev = prev_chunk[-overlap:] if len(prev_chunk) > overlap else prev_chunk
            final_chunks.append(prev + " " + chunk)
    
    return final_chunks

if __name__ == "__main__":
    RAW_DIR = Path(__file__).parent / "doc_raw"
    OUTPUT_DIR = Path(__file__).parent / "docs_cleaned"
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    all_chunks = []
    for file_path in RAW_DIR.iterdir():
        if file_path.suffix.lower() in ['.pdf', '.docx', '.xlsx', '.xls']:
            print(f"处理文档：{file_path.name}")
            try:
                if file_path.suffix.lower() == '.pdf':
                    raw_text = extract_from_pdf(file_path)
                elif file_path.suffix.lower() == '.docx':
                    raw_text = extract_from_docx(file_path)
                elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                    raw_text = extract_from_excel(file_path)
                else:
                    continue
                
                chunks = split_into_chunks(raw_text)
                print(f"提取 {len(chunks)} 个语义片段")
                
                # 保存清洗后片段（供调试查看）
                with open(OUTPUT_DIR / f"{file_path.stem}_chunks.txt", "w", encoding="utf-8") as f:
                    for i, c in enumerate(chunks):
                        f.write(f"[片段{i+1}]\n{c}\n{'='*50}\n")
                
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"处理失败 {file_path.name}：{str(e)}")
    
    print(f"\n总计生成 {len(all_chunks)} 个可向量化的知识片段")
    print(f"清洗结果已存至：{OUTPUT_DIR}")
