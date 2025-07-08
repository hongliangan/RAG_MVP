"""
data_loader.py
数据加载与预处理模块。
支持txt、docx、pdf三种格式。
"""
import os
from .text_splitter import TextSplitter
from utils.config import get_text_chunk_config

def load_documents(file_path, chunk_config=None):
    """
    从本地txt、docx、pdf文件加载文本，按配置方式分割。
    :param file_path: 文本文件路径
    :param chunk_config: 切片配置字典，如果为None则使用默认配置
    :return: List[str]，每个元素为一个文本块
    """
    # 获取文件扩展名，判断文件类型
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == '.txt':
        # 加载txt文件
        content = _load_txt(file_path)
    elif ext == '.docx':
        # 加载docx文件
        content = _load_docx(file_path)
    elif ext == '.pdf':
        # 加载pdf文件
        content = _load_pdf(file_path)
    else:
        # 不支持的文件格式抛出异常
        raise ValueError(f"不支持的文件格式: {ext}")
    
    # 使用新的文本切片器
    splitter = TextSplitter(chunk_config)
    chunks = splitter.split_text(content)
    
    return chunks

def _load_txt(file_path):
    """
    加载txt文件内容。
    :param file_path: txt文件路径
    :return: str，文件内容
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def _load_docx(file_path):
    """
    加载docx文件内容。
    :param file_path: docx文件路径
    :return: str，文件内容
    """
    from docx import Document
    doc = Document(file_path)
    # 提取所有段落文本
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    content = '\n\n'.join(paragraphs)
    return content

def _load_pdf(file_path):
    """
    加载pdf文件内容。
    :param file_path: pdf文件路径
    :return: str，文件内容
    """
    from PyPDF2 import PdfReader
    reader = PdfReader(file_path)
    content_parts = []
    for page in reader.pages:
        # 提取每页文本
        text = page.extract_text()
        if text:
            content_parts.append(text)
    content = '\n\n'.join(content_parts)
    return content
