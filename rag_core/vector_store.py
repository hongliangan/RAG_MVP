import chromadb
from chromadb.types import Collection
from typing import List, Dict, Any
import numpy as np
import config

class VectorStore:
    """
    封装了 ChromaDB 客户端，用于管理向量存储和检索。
    """
    def __init__(self, collection_name: str = "default"):
        """
        初始化 VectorStore，连接到 ChromaDB 并获取或创建指定的集合。

        Args:
            collection_name (str, optional): 要使用的集合名称。默认为 "default"。
        """
        self.client = chromadb.EphemeralClient() # 使用内存客户端，程序关闭后数据会丢失
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def save_embeddings(self, texts: List[str], embeddings: np.ndarray) -> None:
        """
        将文本和它们对应的嵌入向量保存到集合中。

        Args:
            texts (List[str]): 原始文本文档列表。
            embeddings (np.ndarray): 文本对应的嵌入向量数组。
        """
        ids = [str(i) for i in range(len(texts))]
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=texts,
            ids=ids
        )

    def retrieve(self, query_embedding: np.ndarray, n_results: int = 5) -> Dict[str, Any]:
        """
        根据查询嵌入从集合中检索最相关的文档。

        Args:
            query_embedding (np.ndarray): 查询的嵌入向量。
            n_results (int, optional): 要检索的文档数量。默认为 5。

        Returns:
            Dict[str, Any]: 包含检索结果的字典。
        """
        return self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results
        )

# 创建一个全局的向量存储实例
vector_store = VectorStore()

def save_to_vector_store(texts: List[str], embeddings: np.ndarray) -> None:
    """
    使用全局向量存储实例保存文本和嵌入。

    Args:
        texts (List[str]): 原始文本文档列表。
        embeddings (np.ndarray): 文本对应的嵌入向量数组。
    """
    vector_store.save_embeddings(texts, embeddings)

def retrieve_from_vector_store(query_embedding: np.ndarray, n_results: int = 5) -> Dict[str, Any]:
    """
    使用全局向量存储实例进行检索。

    Args:
        query_embedding (np.ndarray): 查询的嵌入向量。
        n_results (int, optional): 要检索的文档数量。默认为 5。

    Returns:
        Dict[str, Any]: 包含检索结果的字典。
    """
    return vector_store.retrieve(query_embedding, n_results)