"""
generator.py
生成模块，调用LLM API生成答案。
"""

from rag_core.llm_api import call_llm_api


def generate_answer(query, relevant_docs, llm_model=None, **kwargs):
    """
    基于用户问题和检索片段，调用LLM生成答案。
    :param query: str，用户问题
    :param relevant_docs: List[str]，检索到的相关片段
    :param llm_model: str，LLM模型名（可选）
    :param kwargs: 其它LLM参数
    :return: str，生成的答案
    """
    # 拼接prompt，将检索片段作为上下文
    context = "\n".join(relevant_docs)
    prompt = f"已知信息如下：\n{context}\n\n请根据上述内容回答：{query}"
    # 调用LLM API生成答案
    return call_llm_api(prompt, model=llm_model, **kwargs)
