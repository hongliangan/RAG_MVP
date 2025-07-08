"""
config.py
多LLM服务配置管理模块。
"""

import os

# 尝试加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有安装python-dotenv，跳过
    pass

# 当前使用的LLM服务名（如 'siliconflow', 'openai', 'qwen'）
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "siliconflow")

# 各LLM服务的配置，支持多服务切换
LLM_CONFIGS = {
    "siliconflow": {
        "api_key": os.getenv("SILICONFLOW_API_KEY", ""),  # 从环境变量读取，不设置默认值
        "model_name": os.getenv("SILICONFLOW_MODEL_NAME", "Tongyi-Zhiwen/QwenLong-L1-32B"),
        "api_url": os.getenv("SILICONFLOW_API_URL", "https://api.siliconflow.cn/v1/chat/completions"),
    },
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY", ""),  # 从环境变量读取，不设置默认值
        "model_name": os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),
        "api_url": os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"),
    },
    # 可继续扩展其它LLM服务
}

# 文本切片配置
TEXT_CHUNK_CONFIG = {
    # 切片方式：'paragraph'（按段落）, 'character'（按字符数）, 'sentence'（按句子）
    "split_method": os.getenv("TEXT_SPLIT_METHOD", "paragraph"),
    
    # 字符数切片参数（当split_method为'character'时使用）
    "chunk_size": int(os.getenv("TEXT_CHUNK_SIZE", "1000")),  # 每个切片的最大字符数
    "chunk_overlap": int(os.getenv("TEXT_CHUNK_OVERLAP", "200")),  # 相邻切片的重叠字符数
    
    # 句子切片参数（当split_method为'sentence'时使用）
    "max_sentences_per_chunk": int(os.getenv("MAX_SENTENCES_PER_CHUNK", "5")),  # 每个切片的最大句子数
    
    # 段落切片参数（当split_method为'paragraph'时使用）
    "paragraph_separator": os.getenv("PARAGRAPH_SEPARATOR", "\n\n"),  # 段落分隔符
    "min_paragraph_length": int(os.getenv("MIN_PARAGRAPH_LENGTH", "50")),  # 最小段落长度（字符数）
    "max_paragraph_length": int(os.getenv("MAX_PARAGRAPH_LENGTH", "2000")),  # 最大段落长度（字符数）
    
    # 通用过滤参数
    "min_chunk_length": int(os.getenv("MIN_CHUNK_LENGTH", "20")),  # 最小切片长度
    "max_chunk_length": int(os.getenv("MAX_CHUNK_LENGTH", "3000")),  # 最大切片长度
    "remove_empty_chunks": os.getenv("REMOVE_EMPTY_CHUNKS", "true").lower() == "true",  # 是否移除空切片
    "remove_whitespace_only": os.getenv("REMOVE_WHITESPACE_ONLY", "true").lower() == "true",  # 是否移除仅包含空白字符的切片
}

def get_llm_config():
    """
    获取当前选定LLM服务的配置。
    :return: dict，包含api_key、model_name、api_url
    """
    config = LLM_CONFIGS.get(LLM_PROVIDER, {})
    print(f"[config] 当前LLM_PROVIDER: {LLM_PROVIDER}, model_name: {config.get('model_name')}")
    return config

def get_text_chunk_config():
    """
    获取文本切片配置。
    :return: dict，包含所有切片相关参数
    """
    return TEXT_CHUNK_CONFIG
