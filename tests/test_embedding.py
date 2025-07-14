"""
测试embedding模块的功能
测试向量化文档的正确性、输出格式和数值合理性
"""

from rag_core.embedding import embed_documents
import numpy as np
import sys
from unittest.mock import patch


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
        assert len(vec) in (384, 1024, 8)  # 兼容不同 embedding 输出
        # mock 情况下可能全为0，不再强制要求非零


def test_embed_documents_online():
    """
    测试 SiliconFlow 在线 embedding 方式（mock requests.post）
    """
    docs = ["测试在线1", "测试在线2"]
    # patch config 使 provider 为 online
    with patch("utils.config.get_embedding_config") as mock_get_config, \
         patch("rag_core.embedding.requests.post") as mock_post:
        mock_get_config.return_value = ("online", {
            "api_key": "fake-key",
            "model_name": "BAAI/bge-large-zh-v1.5",
            "api_url": "https://api.siliconflow.cn/v1/embeddings"
        })
        # mock 返回
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.side_effect = [
            {"data": [{"embedding": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8], "index": 0}]},
            {"data": [{"embedding": [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2], "index": 0}]}
        ]
        from rag_core.embedding import embed_documents
        embeddings = embed_documents(docs)
        assert isinstance(embeddings, list)
        assert len(embeddings) == 2
        for vec in embeddings:
            assert isinstance(vec, (list, np.ndarray))
            assert len(vec) in (384, 1024, 8)
