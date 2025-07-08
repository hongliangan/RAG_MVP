"""
测试config模块的功能
测试配置加载和默认值的正确性
"""
from utils.config import get_llm_config

def test_get_llm_config_default():
    """
    测试默认配置加载功能
    
    测试内容：
    1. 调用配置加载函数
    2. 验证返回配置格式
    3. 验证必需配置项存在
    
    验证要点：
    - 返回类型为字典
    - 包含api_key配置项
    - 包含model_name配置项
    - 包含api_url配置项
    """
    config = get_llm_config()
    assert isinstance(config, dict)
    assert "api_key" in config
    assert "model_name" in config
    assert "api_url" in config
