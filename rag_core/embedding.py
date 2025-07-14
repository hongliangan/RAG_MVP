"""
embedding.py
文本向量化模块，支持用sentence-transformers生成文本向量。
"""

import os
import requests
from utils.config import get_embedding_config


def embed_with_siliconflow(docs, api_key, model_name, api_url):
    """
    使用 SiliconFlow 在线 API 进行文本向量化。
    :param docs: List[str]
    :param api_key: str
    :param model_name: str
    :param api_url: str
    :return: List[List[float]]
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    embeddings = []
    for idx, doc in enumerate(docs):
        payload = {
            "model": model_name,
            "input": doc
        }
        try:
            resp = requests.post(api_url, headers=headers, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            emb = data["data"][0]["embedding"]
            embeddings.append(emb)
        except Exception as e:
            print(f"[embedding] SiliconFlow API 调用失败: {e}")
            embeddings.append([0.0] * 8)  # fallback
    return embeddings


def embed_documents(docs, model_name=None):
    """
    对文本列表进行向量化。根据 config 自动选择本地或在线 embedding。
    :param docs: List[str]，文本分段
    :param model_name: str，手动指定本地模型路径（如不指定则用 config）
    :return: List[List[float]]
    """
    provider, config = get_embedding_config()
    if provider == "online":
        print("[embedding] 使用 SiliconFlow 在线 embedding 服务")
        api_key = config.get("api_key", "")
        model_name = config.get("model_name", "BAAI/bge-large-zh-v1.5")
        api_url = config.get("api_url", "https://api.siliconflow.cn/v1/embeddings")
        return embed_with_siliconflow(docs, api_key, model_name, api_url)
    else:
        # 本地 embedding 逻辑
        if model_name is None:
            model_name = config.get("model_path")
        # 统一用项目根目录的绝对路径
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        default_local_path = os.path.join(project_root, "models", "all-MiniLM-L6-v2")
        if model_name is None:
            model_name = default_local_path
        use_cloud = False  # 标记是否使用云端模型

        if not os.path.isdir(model_name) and not (
            model_name.startswith("sentence-transformers/")
        ):
            print(
                f"[embedding] 本地模型目录不存在，自动切换为云模型: sentence-transformers/all-MiniLM-L6-v2"
            )
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            use_cloud = True
        print(f"[embedding] 实际加载模型路径/名: {model_name}")
        print(f"[embedding] 输入文本数量: {len(docs)}")
        try:
            from sentence_transformers import SentenceTransformer
            import torch

            # 检查是否有可用的GPU，如果没有则使用CPU
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"[embedding] 使用设备: {device}")

            model = SentenceTransformer(model_name, device=device)

            # 如果首次用云模型，自动保存到本地，便于后续离线加载
            if use_cloud and not os.path.isdir(default_local_path):
                print(f"[embedding] 正在将云端模型保存到本地: {default_local_path}")
                model.save(default_local_path)

            # 进行文本向量化
            embeddings = model.encode(docs, show_progress_bar=False)
            # 兼容 numpy/tensor 类型
            if hasattr(embeddings, 'tolist'):
                embeddings = embeddings.tolist()
            elif isinstance(embeddings, list) and hasattr(embeddings[0], 'tolist'):
                embeddings = [e.tolist() for e in embeddings]
            if embeddings is not None and len(embeddings) > 0:
                print(
                    f"[embedding] 输出向量数量: {len(embeddings)}，每个向量长度: {len(embeddings[0])}"
                )
                print(
                    f"[embedding] 向量类型: {type(embeddings)}, 单个向量类型: {type(embeddings[0])}"
                )
            else:
                print("[embedding] 输出为空")
            return embeddings
        except ImportError:
            # 未安装sentence-transformers时返回mock向量
            print("[embedding] 未安装sentence-transformers，返回mock向量")
            return [[float(i)] * 8 for i in range(len(docs))]
        except Exception as e:
            # 其他异常处理，返回全零向量
            print(f"[embedding] 向量化异常: {e}")
            return [[0.0] * 8 for _ in range(len(docs))]
