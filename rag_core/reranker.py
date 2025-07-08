from sentence_transformers.cross_encoder import CrossEncoder
from typing import List, Dict, Any
import numpy as np
import config

class Reranker:
    """
    封装了 CrossEncoder 模型，用于对检索到的文档进行重排序。
    """
    def __init__(self) -> None:
        """
        初始化 Reranker，加载配置文件中指定的 CrossEncoder 模型。
        """
        self.model = CrossEncoder(config.RERANKER_MODEL_NAME)

    def rerank(self, query: str, documents: List[str]) -> List[Dict[str, Any]]:
        """
        对给定的文档列表根据与查询的相关性进行重排序。

        Args:
            query (str): 用户的查询字符串。
            documents (List[str]): 从向量存储中检索到的文档列表。

        Returns:
            List[Dict[str, Any]]: 按相关性得分降序排列的文档列表，每个元素包含 'document' 和 'score'。
        """
        # 创建查询和文档的配对
        pairs = [(query, doc) for doc in documents]
        
        # 预测得分
        scores = self.model.predict(pairs)
        
        # 组合文档、得分并排序
        reranked_results = [{'document': doc, 'score': score} for doc, score in zip(documents, scores)]
        reranked_results.sort(key=lambda x: x['score'], reverse=True)
        
        return reranked_results

# 创建一个全局的重排序器实例
reranker = Reranker()

def rerank_documents(query: str, documents: List[str]) -> List[Dict[str, Any]]:
    """
    使用全局重排序器实例对文档进行重排序。

    Args:
        query (str): 用户的查询字符串。
        documents (List[str]): 检索到的文档列表。

    Returns:
        List[Dict[str, Any]]: 重排序后的文档列表。
    """
    return reranker.rerank(query, documents)