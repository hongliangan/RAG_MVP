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
    # 默认本地模型保存路径
    default_local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'all-MiniLM-L6-v2'))
    if model_name is None:
        # 如果未指定模型名，优先使用本地模型路径
        model_name = default_local_path
    use_cloud = False  # 标记是否使用云端模型
    # 如果本地模型目录不存在且不是云模型名，则切换为云模型
    if os.path.isdir(model_name) is False and not model_name.startswith('sentence-transformers/'):
        print(f"[embedding] 本地模型目录不存在，自动切换为云模型: sentence-transformers/all-MiniLM-L6-v2")
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        use_cloud = True
    print(f"[embedding] 实际加载模型路径/名: {model_name}")
    print(f"[embedding] 输入文本数量: {len(docs)}")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_name)
        # 如果首次用云模型，自动保存到本地，便于后续离线加载
        if use_cloud and not os.path.isdir(default_local_path):
            print(f"[embedding] 正在将云端模型保存到本地: {default_local_path}")
            model.save(default_local_path)
        # 进行文本向量化
        embeddings = model.encode(docs, show_progress_bar=False)
        if embeddings is not None and len(embeddings) > 0:
            print(f"[embedding] 输出向量数量: {len(embeddings)}，每个向量长度: {len(embeddings[0])}")
            print(f"[embedding] 向量类型: {type(embeddings)}, 单个向量类型: {type(embeddings[0])}")
        else:
            print("[embedding] 输出为空")
        return embeddings.tolist()
    except ImportError:
        # 未安装sentence-transformers时返回mock向量
        print("[embedding] 未安装sentence-transformers，返回mock向量")
        return [[float(i)]*8 for i in range(len(docs))]
    except Exception as e:
        # 其他异常处理，返回全零向量
        print(f"[embedding] 向量化异常: {e}")
        return [[0.0]*8 for _ in range(len(docs))]
