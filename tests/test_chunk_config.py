"""
test_chunk_config.py
文档切片参数配置模块的测试文件
"""

import pytest
from utils.chunk_config import (
    get_default_chunk_config,
    get_recommended_configs,
    validate_chunk_config,
    get_parameters_by_category,
)


def test_get_default_chunk_config():
    """测试获取默认配置"""
    config = get_default_chunk_config()

    # 检查必要参数是否存在
    assert "split_method" in config
    assert "chunk_size" in config
    assert "chunk_overlap" in config

    # 检查参数类型
    assert isinstance(config["split_method"], str)
    assert isinstance(config["chunk_size"], int)
    assert isinstance(config["chunk_overlap"], int)


def test_get_recommended_configs():
    """测试获取推荐配置"""
    configs = get_recommended_configs()

    # 检查推荐配置模板
    assert "通用文档" in configs
    assert "长文本" in configs
    assert "对话文本" in configs
    assert "技术文档" in configs
    assert "新闻文章" in configs

    # 检查每个配置的完整性
    for name, config in configs.items():
        assert "split_method" in config
        assert isinstance(config["split_method"], str)


def test_validate_chunk_config_valid():
    """测试有效配置的验证"""
    valid_config = {
        "split_method": "character",
        "chunk_size": 800,
        "chunk_overlap": 100,
    }

    errors = validate_chunk_config(valid_config)
    assert not errors


def test_validate_chunk_config_invalid():
    """测试无效配置的验证"""
    invalid_config = {
        "split_method": "character",
        "chunk_size": 50,  # 小于最小值
        "chunk_overlap": 1000,  # 大于最大值
    }

    errors = validate_chunk_config(invalid_config)
    assert "chunk_size" in errors
    assert "chunk_overlap" in errors


def test_validate_chunk_config_unknown_param():
    """测试未知参数的验证"""
    config_with_unknown = {"split_method": "character", "unknown_param": "value"}

    errors = validate_chunk_config(config_with_unknown)
    assert "unknown_param" in errors


def test_get_parameters_by_category():
    """测试按类别获取参数"""
    categories = get_parameters_by_category()

    # 检查主要类别
    assert "基础配置" in categories
    assert "字符数切片" in categories
    assert "句子切片" in categories
    assert "段落切片" in categories
    assert "过滤规则" in categories
    assert "高级配置" in categories

    # 检查每个类别都有参数
    for category, params in categories.items():
        assert len(params) > 0
        for param in params:
            assert hasattr(param, "name")
            assert hasattr(param, "description")
            assert hasattr(param, "category")


def test_character_split_config():
    """测试字符数切片配置"""
    config = {"split_method": "character", "chunk_size": 1000, "chunk_overlap": 150}

    errors = validate_chunk_config(config)
    assert not errors


def test_sentence_split_config():
    """测试句子切片配置"""
    config = {"split_method": "sentence", "max_sentences_per_chunk": 5}

    errors = validate_chunk_config(config)
    assert not errors


def test_paragraph_split_config():
    """测试段落切片配置"""
    config = {
        "split_method": "paragraph",
        "min_paragraph_length": 50,
        "max_paragraph_length": 2000,
    }

    errors = validate_chunk_config(config)
    assert not errors


if __name__ == "__main__":
    pytest.main([__file__])
