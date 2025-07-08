"""
config.py
多LLM服务配置管理模块。
"""

import os
import json

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
        "model_name": os.getenv(
            "SILICONFLOW_MODEL_NAME", "Tongyi-Zhiwen/QwenLong-L1-32B"
        ),
        "api_url": os.getenv(
            "SILICONFLOW_API_URL", "https://api.siliconflow.cn/v1/chat/completions"
        ),
    },
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY", ""),  # 从环境变量读取，不设置默认值
        "model_name": os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),
        "api_url": os.getenv(
            "OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"
        ),
    },
    # 可继续扩展其它LLM服务
}

# 文本切片配置
TEXT_CHUNK_CONFIG = {
    # 切片方式：'paragraph'（按段落）, 'character'（按字符数）, 'sentence'（按句子）
    "split_method": os.getenv("TEXT_SPLIT_METHOD", "paragraph"),
    # 字符数切片参数（当split_method为'character'时使用）
    "chunk_size": int(
        os.getenv("TEXT_CHUNK_SIZE", "800")
    ),  # 每个切片的最大字符数，默认800
    "chunk_overlap": int(
        os.getenv("TEXT_CHUNK_OVERLAP", "100")
    ),  # 相邻切片的重叠字符数，默认100
    # 句子切片参数（当split_method为'sentence'时使用）
    "max_sentences_per_chunk": int(
        os.getenv("MAX_SENTENCES_PER_CHUNK", "3")
    ),  # 每个切片的最大句子数，默认3
    # 段落切片参数（当split_method为'paragraph'时使用）
    "paragraph_separator": os.getenv("PARAGRAPH_SEPARATOR", "\n\n"),  # 段落分隔符
    "min_paragraph_length": int(
        os.getenv("MIN_PARAGRAPH_LENGTH", "30")
    ),  # 最小段落长度（字符数），默认30
    "max_paragraph_length": int(
        os.getenv("MAX_PARAGRAPH_LENGTH", "1500")
    ),  # 最大段落长度（字符数），默认1500
    # 通用过滤参数
    "min_chunk_length": int(os.getenv("MIN_CHUNK_LENGTH", "20")),  # 最小切片长度
    "max_chunk_length": int(os.getenv("MAX_CHUNK_LENGTH", "3000")),  # 最大切片长度
    "remove_empty_chunks": os.getenv("REMOVE_EMPTY_CHUNKS", "true").lower()
    == "true",  # 是否移除空切片
    "remove_whitespace_only": os.getenv("REMOVE_WHITESPACE_ONLY", "true").lower()
    == "true",  # 是否移除仅包含空白字符的切片
}

# 检索配置
RETRIEVAL_CONFIG = {
    # 基本检索参数
    "top_k": int(os.getenv("RETRIEVAL_TOP_K", "5")),  # 返回最相关的片段数，默认5个
    "similarity_threshold": float(
        os.getenv("RETRIEVAL_SIMILARITY_THRESHOLD", "0.1")
    ),  # 相似度阈值，默认0.1
    "deduplication": os.getenv("RETRIEVAL_DEDUPLICATION", "true").lower()
    == "true",  # 是否去重，默认启用
    "retrieval_strategy": os.getenv(
        "RETRIEVAL_STRATEGY", "cosine"
    ),  # 检索策略：cosine, dot_product, euclidean
    "context_window": int(
        os.getenv("RETRIEVAL_CONTEXT_WINDOW", "1")
    ),  # 上下文窗口大小，默认1
    # 权重配置
    "weight_config": {
        "length_weight": os.getenv(
            "RETRIEVAL_LENGTH_WEIGHT", ""
        ),  # 长度权重：prefer_long, prefer_short, ""
        "position_weight": os.getenv(
            "RETRIEVAL_POSITION_WEIGHT", ""
        ),  # 位置权重：prefer_early, prefer_late, ""
        "keyword_weight": (
            os.getenv("RETRIEVAL_KEYWORD_WEIGHT", "").split(",")
            if os.getenv("RETRIEVAL_KEYWORD_WEIGHT")
            else []
        ),  # 关键词权重
    },
}

CONFIG_JSON_PATH = os.path.join(os.path.dirname(__file__), "../config.json")


def load_global_config():
    """
    加载全局配置（如config.json），如不存在则返回默认结构。
    """
    try:
        with open(CONFIG_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # 默认结构
        return {
            "llm_provider": LLM_PROVIDER,
            "llm_configs": LLM_CONFIGS,
            "local_model_dir": os.getenv("LOCAL_MODEL_DIR", "./models"),
            "prefer_local_model": os.getenv("PREFER_LOCAL_MODEL", "false").lower()
            == "true",
        }


def save_global_config(config: dict):
    """
    保存全局配置到config.json。
    """
    with open(CONFIG_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_llm_config():
    """
    获取当前选定LLM服务的配置（始终读取最新config.json）。
    :return: dict，包含api_key、model_name、api_url
    """
    global_config = load_global_config()
    provider = global_config.get("llm_provider", "siliconflow")
    llm_configs = global_config.get("llm_configs", {})
    config = llm_configs.get(provider, {})
    print(
        f"[config] 当前LLM_PROVIDER: {provider}, model_name: {config.get('model_name')}"
    )
    return config


def get_text_chunk_config():
    """
    获取文本切片配置。
    :return: dict，包含所有切片相关参数
    """
    return TEXT_CHUNK_CONFIG


def get_retrieval_config():
    """
    获取检索配置。
    :return: dict，包含所有检索相关参数
    """
    return RETRIEVAL_CONFIG.copy()


def get_retrieval_params():
    """
    获取检索参数（始终读取最新config.json）。
    :return: dict
    """
    global_config = load_global_config()
    # 可扩展：如有检索参数存储在config.json则优先取，否则用默认
    return global_config.get("retrieval_config", RETRIEVAL_CONFIG)
