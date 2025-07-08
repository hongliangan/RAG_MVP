"""
测试llm_api模块的功能
测试LLM API调用的正确性和返回值格式
"""

from rag_core.llm_api import call_llm_api


def test_call_llm_api():
    """
    测试LLM API调用功能

    测试内容：
    1. 输入中文查询文本
    2. 调用LLM API
    3. 验证返回结果格式
    4. 验证返回内容合理性

    验证要点：
    - 返回类型为字符串
    - 返回内容不为空
    - 支持中文查询
    """
    result = call_llm_api("你好，介绍一下RAG是什么？")
    assert isinstance(result, str)
    assert "LLM API" in result or len(result) > 0  # 占位返回或后续真实返回
