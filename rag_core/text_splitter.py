"""
text_splitter.py
增强版文本切片器，支持多种切片方式和可配置参数。
"""
import re
from typing import List
from utils.config import get_text_chunk_config


class TextSplitter:
    """
    增强版文本切片器，支持多种切片方式
    """
    
    def __init__(self, config=None):
        """
        初始化文本切片器
        
        :param config: 切片配置字典，如果为None则使用默认配置
        """
        self.config = config or get_text_chunk_config()
        self.split_method = self.config.get("split_method", "paragraph")
        
    def split_text(self, text: str) -> List[str]:
        """
        根据配置的切片方式分割文本
        
        :param text: 要分割的文本
        :return: 分割后的文本块列表
        """
        if not text or not text.strip():
            return []
            
        # 根据切片方式选择对应的分割方法
        if self.split_method == "character":
            chunks = self._split_by_character(text)
        elif self.split_method == "sentence":
            chunks = self._split_by_sentence(text)
        elif self.split_method == "paragraph":
            chunks = self._split_by_paragraph(text)
        else:
            # 默认使用段落分割
            chunks = self._split_by_paragraph(text)
            
        # 应用通用过滤规则
        chunks = self._apply_filters(chunks)
        
        return chunks
    
    def _split_by_character(self, text: str) -> List[str]:
        """
        按字符数分割文本
        
        :param text: 要分割的文本
        :return: 分割后的文本块列表
        """
        chunk_size = self.config.get("chunk_size", 1000)
        chunk_overlap = self.config.get("chunk_overlap", 200)
        
        if chunk_overlap >= chunk_size:
            chunk_overlap = chunk_size // 4  # 默认重叠为块大小的1/4
            
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # 如果不是最后一块，尝试在合适的位置分割（避免切断单词）
            if end < len(text):
                # 寻找最后一个空格或标点符号
                last_space = chunk.rfind(' ')
                last_punct = max(chunk.rfind('。'), chunk.rfind('！'), chunk.rfind('？'), 
                               chunk.rfind('.'), chunk.rfind('!'), chunk.rfind('?'))
                split_point = max(last_space, last_punct)
                
                if split_point > chunk_size * 0.7:  # 如果找到合适的分割点
                    chunk = chunk[:split_point + 1]
                    end = start + split_point + 1
            
            chunks.append(chunk)
            start = end - chunk_overlap
            
        return chunks
    
    def _split_by_sentence(self, text: str) -> List[str]:
        """
        按句子分割文本
        
        :param text: 要分割的文本
        :return: 分割后的文本块列表
        """
        # 句子结束标记（支持中英文）
        sentence_endings = r'[。！？.!?]'
        sentences = re.split(sentence_endings, text)
        
        max_sentences = self.config.get("max_sentences_per_chunk", 5)
        chunks = []
        current_chunk = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            current_chunk.append(sentence)
            
            # 当达到最大句子数时，创建新块
            if len(current_chunk) >= max_sentences:
                chunk_text = '。'.join(current_chunk) + '。'
                chunks.append(chunk_text)
                current_chunk = []
        
        # 处理剩余的句子
        if current_chunk:
            chunk_text = '。'.join(current_chunk) + '。'
            chunks.append(chunk_text)
            
        return chunks
    
    def _split_by_paragraph(self, text: str) -> List[str]:
        """
        按段落分割文本
        
        :param text: 要分割的文本
        :return: 分割后的文本块列表
        """
        separator = self.config.get("paragraph_separator", "\n\n")
        min_length = self.config.get("min_paragraph_length", 50)
        max_length = self.config.get("max_paragraph_length", 2000)
        
        # 按分隔符分割
        paragraphs = text.split(separator)
        chunks = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # 检查段落长度
            if len(paragraph) < min_length:
                continue
                
            # 如果段落太长，进一步分割
            if len(paragraph) > max_length:
                # 递归调用字符分割
                sub_chunks = self._split_by_character(paragraph)
                chunks.extend(sub_chunks)
            else:
                chunks.append(paragraph)
                
        return chunks
    
    def _apply_filters(self, chunks: List[str]) -> List[str]:
        """
        应用通用过滤规则
        
        :param chunks: 原始文本块列表
        :return: 过滤后的文本块列表
        """
        min_length = self.config.get("min_chunk_length", 20)
        max_length = self.config.get("max_chunk_length", 3000)
        remove_empty = self.config.get("remove_empty_chunks", True)
        remove_whitespace = self.config.get("remove_whitespace_only", True)
        
        filtered_chunks = []
        
        for chunk in chunks:
            # 移除空块
            if remove_empty and not chunk.strip():
                continue
                
            # 移除仅包含空白字符的块
            if remove_whitespace and chunk.strip() == "":
                continue
                
            # 检查长度限制
            if len(chunk) < min_length:
                continue
                
            if len(chunk) > max_length:
                # 如果块太长，进一步分割
                sub_chunks = self._split_by_character(chunk)
                filtered_chunks.extend(sub_chunks)
            else:
                filtered_chunks.append(chunk)
                
        return filtered_chunks


def split_text(text: str, config: dict | None = None) -> List[str]:
    """
    便捷函数：分割文本
    
    :param text: 要分割的文本
    :param config: 切片配置字典
    :return: 分割后的文本块列表
    """
    splitter = TextSplitter(config)
    return splitter.split_text(text) 