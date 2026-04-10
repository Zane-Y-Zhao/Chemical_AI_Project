# knowledge_base/document_processor.py
import os
import re
from pathlib import Path
from docx import Document
import PyPDF2
from tqdm import tqdm

def clean_text(text: str) -> str:
    """化工文档专用清洗：保留专业术语，剔除无意义符号"""
    # 移除多余空白与换行
    text = re.sub(r'\s+', ' ', text)
    # 移除页眉页脚常见模式（如"第X页 共Y页"、"©2025 化工安全中心"）
    text = re.sub(r'第\s*\d+\s*页\s*共\s*\d+\s*页|©\d{4}.*', '', text)
    # 移除孤立数字编号（如"1. "、"2. "开头但后无实质内容）
    text = re.sub(r'^\d+\.\s*$', '', text, flags=re.MULTILINE)
    # 只保留中文、英文、数字和常用标点
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\u002E\u002D\u002C\u003B\u0021\u003F\u0028\u0029]', '', text)
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

def split_into_chunks(text: str, chunk_size: int = 300, overlap: int = 50) -> list:
    """按语义切分：优先在句号/分号/换行处分割，避免切断化工术语"""
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
    
    # 添加重叠以保持上下文连贯性
    final_chunks = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            final_chunks.append(chunk)
        else:
            prev = chunks[i-1][-overlap:] if len(chunks[i-1]) > overlap else chunks[i-1]
            final_chunks.append(prev + " " + chunk)
    
    return final_chunks

if __name__ == "__main__":
    RAW_DIR = Path(__file__).parent / "doc_raw"
    OUTPUT_DIR = Path(__file__).parent / "docs_cleaned"
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    all_chunks = []
    for file_path in RAW_DIR.iterdir():
        if file_path.suffix.lower() in ['.pdf', '.docx']:
            print(f"处理文档：{file_path.name}")
            try:
                if file_path.suffix.lower() == '.pdf':
                    raw_text = extract_from_pdf(file_path)
                else:
                    raw_text = extract_from_docx(file_path)
                
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
