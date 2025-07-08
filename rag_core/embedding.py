"""
embedding.py
文本向量化模块，支持用sentence-transformers生成文本向量。
"""

import os


def embed_documents(docs, model_name=None):
    """
    对文本列表进行向量化。
    :param docs: List[str]，文本分段
    :param model_name: str，sentence-transformers模型名或本地路径
    :return: List[List[float]]，每段文本的向量
    """
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
        if embeddings is not None and len(embeddings) > 0:
            print(
                f"[embedding] 输出向量数量: {len(embeddings)}，每个向量长度: {len(embeddings[0])}"
            )
            print(
                f"[embedding] 向量类型: {type(embeddings)}, 单个向量类型: {type(embeddings[0])}"
            )
        else:
            print("[embedding] 输出为空")
        return embeddings.tolist()
    except ImportError:
        # 未安装sentence-transformers时返回mock向量
        print("[embedding] 未安装sentence-transformers，返回mock向量")
        return [[float(i)] * 8 for i in range(len(docs))]
    except Exception as e:
        # 其他异常处理，返回全零向量
        print(f"[embedding] 向量化异常: {e}")
        return [[0.0] * 8 for _ in range(len(docs))]
