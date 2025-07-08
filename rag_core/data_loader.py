"""
data_loader.py
数据加载与预处理模块。
支持多种文档格式，使用增强版文档预处理器。
"""
import os
from .text_splitter import TextSplitter
from .document_processor import DocumentProcessor
from utils.config import get_text_chunk_config

def load_documents(file_path, chunk_config=None, processor_config=None):
    """
    从本地文件加载文本，按配置方式分割。
    支持多种文档格式：txt、docx、pdf、md、html、json、csv、xlsx等。
    
    :param file_path: 文档文件路径
    :param chunk_config: 切片配置字典，如果为None则使用默认配置
    :param processor_config: 预处理器配置字典
    :return: List[str]，每个元素为一个文本块
    """
    # 使用增强版文档预处理器
    processor = DocumentProcessor(processor_config)
    result = processor.process_document(file_path)
    
    if not result['success']:
        raise ValueError(f"文档处理失败: {result.get('error', '未知错误')}")
    
    content = result['content']
    
    # 使用文本切片器分割内容
    splitter = TextSplitter(chunk_config)
    chunks = splitter.split_text(content)
    
    return chunks

def load_documents_with_metadata(file_path, chunk_config=None, processor_config=None):
    """
    加载文档并返回包含元数据的详细信息
    
    :param file_path: 文档文件路径
    :param chunk_config: 切片配置字典
    :param processor_config: 预处理器配置字典
    :return: Dict，包含文本块列表和元数据
    """
    # 使用增强版文档预处理器
    processor = DocumentProcessor(processor_config)
    result = processor.process_document(file_path)
    
    if not result['success']:
        raise ValueError(f"文档处理失败: {result.get('error', '未知错误')}")
    
    content = result['content']
    
    # 使用文本切片器分割内容
    splitter = TextSplitter(chunk_config)
    chunks = splitter.split_text(content)
    
    return {
        'chunks': chunks,
        'metadata': result['metadata'],
        'format': result.get('format', 'unknown'),
        'processing_time': result.get('processing_time', 0),
        'original_data': result.get('original_data', None)
    }

def batch_load_documents(file_paths, chunk_config=None, processor_config=None):
    """
    批量加载多个文档
    
    :param file_paths: 文档路径列表
    :param chunk_config: 切片配置字典
    :param processor_config: 预处理器配置字典
    :return: List[Dict]，每个字典包含文档的文本块和元数据
    """
    results = []
    
    for file_path in file_paths:
        try:
            result = load_documents_with_metadata(file_path, chunk_config, processor_config)
            results.append(result)
        except Exception as e:
            # 记录错误但继续处理其他文件
            print(f"处理文件 {file_path} 时出错: {str(e)}")
            results.append({
                'chunks': [],
                'metadata': {'file_path': file_path, 'error': str(e)},
                'format': 'error',
                'processing_time': 0
            })
    
    return results

def get_supported_formats():
    """
    获取支持的文件格式列表
    
    :return: List[str]，支持的文件扩展名列表
    """
    processor = DocumentProcessor()
    return processor.get_supported_formats()

def get_document_info(file_path):
    """
    获取文档信息
    
    :param file_path: 文档路径
    :return: Dict，文档信息
    """
    processor = DocumentProcessor()
    return processor.get_document_info(file_path)

# 保持向后兼容性的函数
def _load_txt(file_path):
    """
    加载txt文件内容（保持向后兼容）。
    :param file_path: txt文件路径
    :return: str，文件内容
    """
    processor = DocumentProcessor()
    result = processor._process_txt(file_path)
    return result['content']

def _load_docx(file_path):
    """
    加载docx文件内容（保持向后兼容）。
    :param file_path: docx文件路径
    :return: str，文件内容
    """
    processor = DocumentProcessor()
    result = processor._process_docx(file_path)
    return result['content']

def _load_pdf(file_path):
    """
    加载pdf文件内容（保持向后兼容）。
    :param file_path: pdf文件路径
    :return: str，文件内容
    """
    processor = DocumentProcessor()
    result = processor._process_pdf(file_path)
    return result['content']
