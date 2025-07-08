from typing import List, Any
from sentence_transformers import SentenceTransformer
import numpy as np
import config

class EmbeddingModel:
    """
    封装了 SentenceTransformer 模型，用于生成文本嵌入。
    """
    def __init__(self) -> None:
        """
        初始化 EmbeddingModel，加载配置文件中指定的模型。
        """
        self.model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)

    def embed(self, texts: List[str], show_progress_bar: bool = False) -> np.ndarray:
        """
        为一批文本生成嵌入向量。

        Args:
            texts (List[str]): 需要生成嵌入的文本列表。
            show_progress_bar (bool, optional): 是否显示进度条。默认为 False。

        Returns:
            np.ndarray: 文本的嵌入向量数组。
        """
        return self.model.encode(texts, show_progress_bar=show_progress_bar)

# 创建一个全局的嵌入模型实例，以便在应用中复用
embedding_model = EmbeddingModel()

def embed_texts(texts: List[str], show_progress_bar: bool = False) -> np.ndarray:
    """
    使用全局嵌入模型实例为文本列表生成嵌入。

    Args:
        texts (List[str]): 需要生成嵌入的文本列表。
        show_progress_bar (bool, optional): 是否显示进度条。默认为 False。

    Returns:
        np.ndarray: 文本的嵌入向量数组。
    """
    return embedding_model.embed(texts, show_progress_bar=show_progress_bar)