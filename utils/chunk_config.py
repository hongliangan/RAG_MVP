"""
chunk_config.py
文档切片参数配置模块，提供所有可配置参数的详细说明和最佳默认值。
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum


class SplitMethod(Enum):
    """切片方式枚举"""
    PARAGRAPH = "paragraph"    # 按段落切片
    CHARACTER = "character"    # 按字符数切片
    SENTENCE = "sentence"      # 按句子切片


@dataclass
class ChunkParameter:
    """切片参数定义"""
    name: str
    value: Any
    description: str
    category: str
    min_value: Any = None
    max_value: Any = None
    step: Any = None
    unit: str = ""
    required: bool = False
    depends_on: str | None = None  # 依赖的其他参数


class DocumentChunkConfig:
    """
    文档切片配置管理器
    
    提供所有可配置参数的详细说明、最佳默认值和验证功能
    """
    
    def __init__(self):
        """初始化配置管理器"""
        self.parameters = self._initialize_parameters()
    
    def _initialize_parameters(self) -> Dict[str, ChunkParameter]:
        """初始化所有可配置参数"""
        params = {}
        
        # 基础切片方式
        params["split_method"] = ChunkParameter(
            name="split_method",
            value="paragraph",
            description="文本切片方式：paragraph(按段落)适合结构化文档，character(按字符数)适合长文本，sentence(按句子)适合对话类文本",
            category="基础配置",
            required=True
        )
        
        # 字符数切片参数
        params["chunk_size"] = ChunkParameter(
            name="chunk_size",
            value=800,
            description="每个文本块的最大字符数，建议范围500-1500，过小可能丢失上下文，过大可能包含无关信息",
            category="字符数切片",
            min_value=100,
            max_value=3000,
            step=50,
            unit="字符",
            depends_on="split_method"
        )
        
        params["chunk_overlap"] = ChunkParameter(
            name="chunk_overlap",
            value=100,
            description="相邻文本块的重叠字符数，建议为chunk_size的10-20%，确保上下文连续性",
            category="字符数切片",
            min_value=0,
            max_value=500,
            step=10,
            unit="字符",
            depends_on="split_method"
        )
        
        # 句子切片参数
        params["max_sentences_per_chunk"] = ChunkParameter(
            name="max_sentences_per_chunk",
            value=3,
            description="每个文本块包含的最大句子数，建议2-5句，平衡上下文完整性和检索精度",
            category="句子切片",
            min_value=1,
            max_value=10,
            step=1,
            unit="句",
            depends_on="split_method"
        )
        
        # 段落切片参数
        params["paragraph_separator"] = ChunkParameter(
            name="paragraph_separator",
            value="\n\n",
            description="段落分隔符，用于识别段落边界，支持正则表达式",
            category="段落切片",
            depends_on="split_method"
        )
        
        params["min_paragraph_length"] = ChunkParameter(
            name="min_paragraph_length",
            value=30,
            description="最小段落长度，过滤过短的段落，避免产生无意义的文本块",
            category="段落切片",
            min_value=10,
            max_value=200,
            step=5,
            unit="字符",
            depends_on="split_method"
        )
        
        params["max_paragraph_length"] = ChunkParameter(
            name="max_paragraph_length",
            value=1500,
            description="最大段落长度，超过此长度的段落会被进一步分割",
            category="段落切片",
            min_value=500,
            max_value=3000,
            step=100,
            unit="字符",
            depends_on="split_method"
        )
        
        # 通用过滤参数
        params["min_chunk_length"] = ChunkParameter(
            name="min_chunk_length",
            value=20,
            description="最小文本块长度，过滤过短的文本块，提高检索质量",
            category="过滤规则",
            min_value=5,
            max_value=100,
            step=5,
            unit="字符"
        )
        
        params["max_chunk_length"] = ChunkParameter(
            name="max_chunk_length",
            value=3000,
            description="最大文本块长度，超过此长度的文本块会被进一步分割",
            category="过滤规则",
            min_value=1000,
            max_value=5000,
            step=100,
            unit="字符"
        )
        
        params["remove_empty_chunks"] = ChunkParameter(
            name="remove_empty_chunks",
            value=True,
            description="是否移除空的文本块，建议启用以提高检索效率",
            category="过滤规则"
        )
        
        params["remove_whitespace_only"] = ChunkParameter(
            name="remove_whitespace_only",
            value=True,
            description="是否移除仅包含空白字符的文本块，建议启用",
            category="过滤规则"
        )
        
        # 高级参数
        params["smart_split"] = ChunkParameter(
            name="smart_split",
            value=True,
            description="智能分割，尝试在合适的位置分割文本（如句号、空格），避免切断单词",
            category="高级配置"
        )
        
        params["preserve_formatting"] = ChunkParameter(
            name="preserve_formatting",
            value=False,
            description="是否保留原始格式（如换行、缩进），可能影响检索效果但保持文档结构",
            category="高级配置"
        )
        
        params["merge_short_chunks"] = ChunkParameter(
            name="merge_short_chunks",
            value=True,
            description="是否合并过短的文本块，提高检索效率",
            category="高级配置"
        )
        
        params["merge_threshold"] = ChunkParameter(
            name="merge_threshold",
            value=0.3,
            description="合并阈值，当文本块长度小于min_chunk_length的此倍数时尝试合并",
            category="高级配置",
            min_value=0.1,
            max_value=0.8,
            step=0.1,
            depends_on="merge_short_chunks"
        )
        
        return params
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {name: param.value for name, param in self.parameters.items()}
    
    def get_parameter_info(self, param_name: str) -> ChunkParameter:
        """获取参数详细信息"""
        if param_name not in self.parameters:
            raise ValueError(f"未知参数: {param_name}")
        return self.parameters[param_name]
    
    def get_parameters_by_category(self) -> Dict[str, List[ChunkParameter]]:
        """按类别获取参数列表"""
        categories = {}
        for param in self.parameters.values():
            if param.category not in categories:
                categories[param.category] = []
            categories[param.category].append(param)
        return categories
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """验证配置参数"""
        errors = {}
        
        for param_name, value in config.items():
            if param_name not in self.parameters:
                if param_name not in errors:
                    errors[param_name] = []
                errors[param_name].append("未知参数")
                continue
            
            param = self.parameters[param_name]
            
            # 检查数值范围
            if param.min_value is not None and value < param.min_value:
                if param_name not in errors:
                    errors[param_name] = []
                errors[param_name].append(f"值不能小于 {param.min_value}")
            
            if param.max_value is not None and value > param.max_value:
                if param_name not in errors:
                    errors[param_name] = []
                errors[param_name].append(f"值不能大于 {param.max_value}")
            
            # 检查依赖关系
            if param.depends_on and param.depends_on in config:
                if config[param.depends_on] != "character" and param.category == "字符数切片":
                    if param_name not in errors:
                        errors[param_name] = []
                    errors[param_name].append(f"仅在 split_method 为 'character' 时有效")
                elif config[param.depends_on] != "sentence" and param.category == "句子切片":
                    if param_name not in errors:
                        errors[param_name] = []
                    errors[param_name].append(f"仅在 split_method 为 'sentence' 时有效")
                elif config[param.depends_on] != "paragraph" and param.category == "段落切片":
                    if param_name not in errors:
                        errors[param_name] = []
                    errors[param_name].append(f"仅在 split_method 为 'paragraph' 时有效")
        
        return errors
    
    def get_recommended_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取推荐配置模板"""
        return {
            "通用文档": {
                "split_method": "paragraph",
                "min_paragraph_length": 30,
                "max_paragraph_length": 1500,
                "min_chunk_length": 20,
                "max_chunk_length": 3000,
                "smart_split": True,
                "merge_short_chunks": True
            },
            "长文本": {
                "split_method": "character",
                "chunk_size": 1000,
                "chunk_overlap": 150,
                "min_chunk_length": 50,
                "max_chunk_length": 2000,
                "smart_split": True
            },
            "对话文本": {
                "split_method": "sentence",
                "max_sentences_per_chunk": 5,
                "min_chunk_length": 30,
                "max_chunk_length": 1500,
                "preserve_formatting": True
            },
            "技术文档": {
                "split_method": "paragraph",
                "min_paragraph_length": 50,
                "max_paragraph_length": 2000,
                "min_chunk_length": 30,
                "max_chunk_length": 4000,
                "preserve_formatting": True
            },
            "新闻文章": {
                "split_method": "paragraph",
                "min_paragraph_length": 40,
                "max_paragraph_length": 1200,
                "min_chunk_length": 25,
                "max_chunk_length": 2500
            }
        }
    
    def merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置，override_config 会覆盖 base_config 中的值"""
        merged = base_config.copy()
        merged.update(override_config)
        return merged


# 全局配置管理器实例
chunk_config_manager = DocumentChunkConfig()


def get_default_chunk_config() -> Dict[str, Any]:
    """获取默认切片配置"""
    return chunk_config_manager.get_default_config()


def get_recommended_configs() -> Dict[str, Dict[str, Any]]:
    """获取推荐配置模板"""
    return chunk_config_manager.get_recommended_configs()


def validate_chunk_config(config: Dict[str, Any]) -> Dict[str, List[str]]:
    """验证切片配置"""
    return chunk_config_manager.validate_config(config)


def get_parameter_info(param_name: str) -> ChunkParameter:
    """获取参数详细信息"""
    return chunk_config_manager.get_parameter_info(param_name)


def get_parameters_by_category() -> Dict[str, List[ChunkParameter]]:
    """按类别获取参数列表"""
    return chunk_config_manager.get_parameters_by_category() 