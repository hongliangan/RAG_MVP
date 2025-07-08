"""
config.py
多LLM服务配置管理模块。
"""

import os

# 当前使用的LLM服务名（如 'siliconflow', 'openai', 'qwen'）
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "siliconflow")

# 各LLM服务的配置，支持多服务切换
LLM_CONFIGS = {
    "siliconflow": {
        "api_key": os.getenv("SILICONFLOW_API_KEY", "sk-naigtfmindcikjoukvfdiwmbjavabmaxkqoplfmyemalyobg"),
        "model_name": os.getenv("SILICONFLOW_MODEL_NAME", "Tongyi-Zhiwen/QwenLong-L1-32B"),
        "api_url": os.getenv("SILICONFLOW_API_URL", "https://api.siliconflow.cn/v1/chat/completions"),
    },
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY", "your-openai-api-key"),
        "model_name": os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),
        "api_url": os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"),
    },
    # 可继续扩展其它LLM服务
}

def get_llm_config():
    """
    获取当前选定LLM服务的配置。
    :return: dict，包含api_key、model_name、api_url
    """
    config = LLM_CONFIGS.get(LLM_PROVIDER, {})
    print(f"[config] 当前LLM_PROVIDER: {LLM_PROVIDER}, model_name: {config.get('model_name')}")
    return config
