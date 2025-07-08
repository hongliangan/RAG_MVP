"""
测试generator模块的功能
测试答案生成和LLM API调用的正确性
"""

from rag_core.generator import generate_answer


def test_generate_answer():
    """
    测试答案生成功能

    测试内容：
    1. 输入查询和文档列表
    2. Mock LLM API调用返回
    3. 验证生成的答案格式正确
    4. 验证答案包含预期的mock前缀
    """
    query = "什么是RAG？"
    docs = ["RAG是一种检索增强生成方法。", "它结合了检索和生成能力。"]

    # Mock LLM API调用，返回带前缀的答案
    import rag_core.generator as generator

    generator.call_llm_api = (
        lambda prompt, model=None, **kwargs: f"MOCK_ANSWER: {prompt[:10]}..."
    )

    answer = generate_answer(query, docs)
    assert answer.startswith("MOCK_ANSWER")
