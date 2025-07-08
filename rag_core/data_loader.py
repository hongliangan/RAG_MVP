"""
data_loader.py
数据加载与预处理模块。
支持txt、docx、pdf三种格式。
"""
import os

def load_documents(file_path):
    """
    从本地txt、docx、pdf文件加载文本，按段落分割。
    :param file_path: 文本文件路径
    :return: List[str]，每个元素为一个段落
    """
    # 获取文件扩展名，判断文件类型
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == '.txt':
        # 加载txt文件
        return _load_txt(file_path)
    elif ext == '.docx':
        # 加载docx文件
        return _load_docx(file_path)
    elif ext == '.pdf':
        # 加载pdf文件
        return _load_pdf(file_path)
    else:
        # 不支持的文件格式抛出异常
        raise ValueError(f"不支持的文件格式: {ext}")

def _load_txt(file_path):
    """
    加载txt文件并按空行分段。
    :param file_path: txt文件路径
    :return: List[str]，每段内容
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 按两个换行分段，去除空段
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    return paragraphs

def _load_docx(file_path):
    """
    加载docx文件并按段落分段。
    :param file_path: docx文件路径
    :return: List[str]，每段内容
    """
    from docx import Document
    doc = Document(file_path)
    # 只保留非空段落
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return paragraphs

def _load_pdf(file_path):
    """
    加载pdf文件并按空行分段。
    :param file_path: pdf文件路径
    :return: List[str]，每段内容
    """
    from PyPDF2 import PdfReader
    reader = PdfReader(file_path)
    paragraphs = []
    for page in reader.pages:
        # 提取每页文本
        text = page.extract_text()
        if text:
            # 按两个换行分段，去除空段
            paragraphs.extend([p.strip() for p in text.split('\n\n') if p.strip()])
    return paragraphs
