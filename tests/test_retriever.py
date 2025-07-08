"""
测试retriever模块的功能
测试文档检索和相似度计算的正确性
"""
from rag_core.retriever import retrieve
import numpy as np

def test_retrieve():
    """
    测试文档检索功能
    
    测试内容：
    1. 输入文档列表和对应的向量表示
    2. 输入查询文本
    3. Mock查询向量化（返回与第三个文档最相似的向量）
    4. 验证检索结果包含相关文档
    5. 验证返回的文档数量正确
    """
    docs = ["北京是中国的首都。", "苹果是一种水果。", "RAG是一种检索增强生成方法。"]
    # 使用384维向量（与真实模型一致）
    doc_vectors = [[1.0] + [0.0] * 383, [0.0] + [1.0] + [0.0] * 382, [0.0] * 383 + [1.0]]
    query = "什么是RAG？"
    
    # Mock查询向量化，返回与第三个文档最相似的向量
    def mock_embed_documents(texts, model_name=None):
        return [[0.0] * 383 + [1.0] for _ in texts]  # 384维向量
    
    # 正确mock embedding模块
    import rag_core.embedding as embedding
    original_embed_documents = embedding.embed_documents
    embedding.embed_documents = mock_embed_documents
    
    try:
        result = retrieve(query, doc_vectors, docs, model_path=None, top_k=1)
        assert len(result) == 1
        assert "RAG" in result[0]
    finally:
        # 恢复原始函数
        embedding.embed_documents = original_embed_documents 