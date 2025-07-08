"""
text_splitter.py
增强版文本切片器，支持多种切片方式和可配置参数。
"""

import re
from typing import List, Dict, Any
from utils.config import get_text_chunk_config
from utils.chunk_config import get_default_chunk_config, validate_chunk_config


class TextSplitter:
    """
    增强版文本切片器，支持多种切片方式
    """

    def __init__(self, config=None):
        """
        初始化文本切片器

        :param config: 切片配置字典，如果为None则使用默认配置
        """
        # 合并默认配置和用户配置
        default_config = get_default_chunk_config()
        if config:
            # 验证用户配置
            errors = validate_chunk_config(config)
            if errors:
                print(f"[text_splitter] 配置验证警告: {errors}")

            # 合并配置
            self.config = default_config.copy()
            self.config.update(config)
        else:
            self.config = default_config

        self.split_method = self.config.get("split_method", "paragraph")

        # 确保数值类型参数被正确转换
        self._normalize_config()

    def _normalize_config(self):
        """
        标准化配置参数，确保数值类型正确
        """
        # 字符数切片参数
        if "chunk_size" in self.config:
            self.config["chunk_size"] = int(self.config["chunk_size"])
        if "chunk_overlap" in self.config:
            self.config["chunk_overlap"] = int(self.config["chunk_overlap"])

        # 句子切片参数
        if "max_sentences_per_chunk" in self.config:
            self.config["max_sentences_per_chunk"] = int(
                self.config["max_sentences_per_chunk"]
            )

        # 段落切片参数
        if "min_paragraph_length" in self.config:
            self.config["min_paragraph_length"] = int(
                self.config["min_paragraph_length"]
            )
        if "max_paragraph_length" in self.config:
            self.config["max_paragraph_length"] = int(
                self.config["max_paragraph_length"]
            )

        # 通用过滤参数
        if "min_chunk_length" in self.config:
            self.config["min_chunk_length"] = int(self.config["min_chunk_length"])
        if "max_chunk_length" in self.config:
            self.config["max_chunk_length"] = int(self.config["max_chunk_length"])

        # 高级参数
        if "merge_threshold" in self.config:
            self.config["merge_threshold"] = float(self.config["merge_threshold"])

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
        smart_split = self.config.get("smart_split", True)

        if chunk_overlap >= chunk_size:
            chunk_overlap = chunk_size // 4  # 默认重叠为块大小的1/4

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # 智能分割：如果不是最后一块，尝试在合适的位置分割
            if smart_split and end < len(text):
                # 寻找最佳分割点
                split_point = self._find_best_split_point(chunk, chunk_size)

                if split_point > chunk_size * 0.7:  # 如果找到合适的分割点
                    chunk = chunk[: split_point + 1]
                    end = start + split_point + 1

            chunks.append(chunk)
            start = end - chunk_overlap

        return chunks

    def _find_best_split_point(self, chunk: str, chunk_size: int) -> int:
        """
        寻找最佳分割点

        :param chunk: 文本块
        :param chunk_size: 块大小
        :return: 最佳分割点位置
        """
        # 优先级：句号 > 感叹号 > 问号 > 逗号 > 分号 > 空格
        split_chars = ["。", "！", "？", ".", "!", "?", "，", ",", "；", ";", " "]

        for char in split_chars:
            pos = chunk.rfind(char)
            if pos > chunk_size * 0.5:  # 确保分割点不要太靠前
                return pos

        return -1  # 没找到合适的分割点

    def _split_by_sentence(self, text: str) -> List[str]:
        """
        按句子分割文本

        :param text: 要分割的文本
        :return: 分割后的文本块列表
        """
        # 句子结束标记（支持中英文）
        sentence_endings = r"[。！？.!?]"
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
                chunk_text = "。".join(current_chunk) + "。"
                chunks.append(chunk_text)
                current_chunk = []

        # 处理剩余的句子
        if current_chunk:
            chunk_text = "。".join(current_chunk) + "。"
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
        merge_short_chunks = self.config.get("merge_short_chunks", True)
        merge_threshold = self.config.get("merge_threshold", 0.3)
        preserve_formatting = self.config.get("preserve_formatting", False)

        # 第一步：基础过滤
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

        # 第二步：合并短块
        if merge_short_chunks:
            filtered_chunks = self._merge_short_chunks(
                filtered_chunks, min_length, merge_threshold
            )

        # 第三步：格式化处理
        if not preserve_formatting:
            filtered_chunks = self._clean_formatting(filtered_chunks)

        return filtered_chunks

    def _merge_short_chunks(
        self, chunks: List[str], min_length: int, merge_threshold: float
    ) -> List[str]:
        """
        合并过短的文本块

        :param chunks: 文本块列表
        :param min_length: 最小长度
        :param merge_threshold: 合并阈值
        :return: 合并后的文本块列表
        """
        if not chunks:
            return chunks

        merged_chunks = []
        current_chunk = ""
        threshold_length = int(min_length * merge_threshold)

        for chunk in chunks:
            if len(chunk) < threshold_length and current_chunk:
                # 合并短块
                current_chunk += "\n" + chunk
            else:
                # 保存当前块，开始新块
                if current_chunk:
                    merged_chunks.append(current_chunk)
                current_chunk = chunk

        # 添加最后一个块
        if current_chunk:
            merged_chunks.append(current_chunk)

        return merged_chunks

    def _clean_formatting(self, chunks: List[str]) -> List[str]:
        """
        清理文本格式

        :param chunks: 文本块列表
        :return: 清理后的文本块列表
        """
        cleaned_chunks = []

        for chunk in chunks:
            # 移除多余的空白字符
            cleaned = re.sub(r"\n\s*\n", "\n", chunk)  # 移除多余的空行
            cleaned = re.sub(r"[ \t]+", " ", cleaned)  # 合并多个空格
            cleaned = cleaned.strip()

            if cleaned:
                cleaned_chunks.append(cleaned)

        return cleaned_chunks


def split_text(text: str, config: dict | None = None) -> List[str]:
    """
    便捷函数：分割文本

    :param text: 要分割的文本
    :param config: 切片配置字典
    :return: 分割后的文本块列表
    """
    splitter = TextSplitter(config)
    return splitter.split_text(text)
