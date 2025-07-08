"""
retriever.py
向量检索模块，基于余弦相似度实现。
"""
import numpy as np

def retrieve(query, doc_vectors, docs, model_path=None, top_k=3):
    """
    基于向量相似度检索相关文档片段。
    :param query: str，用户问题
    :param doc_vectors: List[List[float]]，文档向量列表
    :param docs: List[str]，原始文档片段
    :param model_path: str，embedding模型路径（可选）
    :param top_k: int，返回最相关的片段数
    :return: List[str]，检索到的相关片段
    """
    # 向量化用户问题
    from rag_core.embedding import embed_documents
    query_vec = embed_documents([query], model_name=model_path)[0]
    # 计算每个文档片段与问题的余弦相似度
    sims = []
    for vec in doc_vectors:
        # 计算余弦相似度
        sim = np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec) + 1e-8)
        sims.append(sim)
    # 获取相似度最高的top_k索引
    top_indices = np.argsort(sims)[-top_k:][::-1]
    # 返回对应的文档片段
    return [docs[i] for i in top_indices]
