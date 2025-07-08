"""
测试embedding模块的功能
测试向量化文档的正确性、输出格式和数值合理性
"""
from rag_core.embedding import embed_documents
import numpy as np

def test_embed_documents():
    """
    测试文档向量化功能
    
    测试内容：
    1. 输入中文文档列表
    2. 验证输出格式（list类型）
    3. 验证输出长度与输入一致
    4. 验证每个向量为list或numpy数组
    5. 验证向量维度（384为真实模型，8为mock）
    6. 验证数值合理性（不全为0，且为数值类型）
    """
    docs = ["你好，世界。", "RAG是一种检索增强生成方法。"]
    embeddings = embed_documents(docs)
    
    # 验证输出类型和长度
    assert isinstance(embeddings, list)
    assert len(embeddings) == len(docs)
    
    # 验证每个向量的格式和数值合理性
    for vec in embeddings:
        assert isinstance(vec, (list, np.ndarray))
        assert len(vec) in (384, 8)  # 384为真实模型，8为mock
        
        # 检查数值合理性（不全为0，且为float）
        assert any(abs(float(x)) > 1e-6 for x in vec)
        assert all(isinstance(x, (float, np.floating, int)) for x in vec) 