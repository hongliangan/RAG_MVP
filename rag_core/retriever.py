"""
retriever.py
向量检索模块，基于余弦相似度实现。
支持多种可调节参数：相似度阈值、去重策略、检索策略、权重调整、上下文窗口等。
"""

import numpy as np
from typing import List, Dict, Any, Optional
from collections import defaultdict


def retrieve(
    query,
    doc_vectors,
    docs,
    model_path=None,
    top_k=3,
    similarity_threshold=0.0,
    deduplication=True,
    retrieval_strategy="cosine",
    weight_config=None,
    context_window=0,
):
    """
    基于向量相似度检索相关文档片段。

    :param query: str，用户问题
    :param doc_vectors: List[List[float]]，文档向量列表
    :param docs: List[str]，原始文档片段
    :param model_path: str，embedding模型路径（可选）
    :param top_k: int，返回最相关的片段数
    :param similarity_threshold: float，相似度阈值，过滤低于此值的文档片段
    :param deduplication: bool，是否去除重复或高度相似的文档片段
    :param retrieval_strategy: str，检索策略，支持'cosine'、'dot_product'、'euclidean'
    :param weight_config: dict，权重配置，可对不同类型文档设置权重
    :param context_window: int，上下文窗口大小，包含相邻文档片段
    :return: List[str]，检索到的相关片段
    """
    if not docs or not doc_vectors:
        return []

    # 向量化用户问题
    from rag_core.embedding import embed_documents

    query_vec = embed_documents([query], model_name=model_path)[0]

    # 计算相似度
    sims = _calculate_similarities(query_vec, doc_vectors, retrieval_strategy)

    # 应用权重调整
    if weight_config and isinstance(weight_config, dict):
        sims = _apply_weights(sims, docs, weight_config)

    # 应用相似度阈值过滤
    if similarity_threshold > 0:
        sims, docs, doc_vectors = _apply_threshold_filter(
            sims, docs, doc_vectors, similarity_threshold
        )

    # 获取top_k索引
    top_indices = np.argsort(sims)[-top_k:][::-1]

    # 应用去重策略
    if deduplication:
        top_indices = _apply_deduplication(
            top_indices, sims, docs, similarity_threshold
        )

    # 应用上下文窗口
    if context_window > 0:
        top_indices = _apply_context_window(top_indices, context_window, len(docs))

    # 返回对应的文档片段
    return [docs[i] for i in top_indices if i < len(docs)]


def _calculate_similarities(query_vec, doc_vectors, strategy="cosine"):
    """
    根据指定策略计算相似度。

    :param query_vec: List[float]，查询向量
    :param doc_vectors: List[List[float]]，文档向量列表
    :param strategy: str，相似度计算策略
    :return: List[float]，相似度列表
    """
    query_vec = np.array(query_vec)
    doc_vectors = np.array(doc_vectors)

    if strategy == "cosine":
        # 余弦相似度
        query_norm = np.linalg.norm(query_vec)
        doc_norms = np.linalg.norm(doc_vectors, axis=1)
        sims = np.dot(doc_vectors, query_vec) / (doc_norms * query_norm + 1e-8)

    elif strategy == "dot_product":
        # 点积相似度
        sims = np.dot(doc_vectors, query_vec)

    elif strategy == "euclidean":
        # 欧氏距离（转换为相似度）
        distances = np.linalg.norm(doc_vectors - query_vec, axis=1)
        max_distance = np.max(distances) if np.max(distances) > 0 else 1
        sims = 1 - (distances / max_distance)

    else:
        # 默认使用余弦相似度
        query_norm = np.linalg.norm(query_vec)
        doc_norms = np.linalg.norm(doc_vectors, axis=1)
        sims = np.dot(doc_vectors, query_vec) / (doc_norms * query_norm + 1e-8)

    return sims.tolist()


def _apply_weights(sims, docs, weight_config):
    """
    应用权重调整。

    :param sims: List[float]，相似度列表
    :param docs: List[str]，文档片段列表
    :param weight_config: dict，权重配置
    :return: List[float]，调整后的相似度列表
    """
    weighted_sims = sims.copy()

    # 根据文档长度调整权重
    if (
        "length_weight" in weight_config
        and weight_config["length_weight"]
        and weight_config["length_weight"] != ""
    ):
        length_weight = weight_config["length_weight"]
        for i, doc in enumerate(docs):
            doc_length = len(doc)
            if length_weight == "prefer_long":
                # 偏好长文档
                weighted_sims[i] *= 1 + doc_length / 1000
            elif length_weight == "prefer_short":
                # 偏好短文档
                weighted_sims[i] *= 1 + 1000 / (doc_length + 1)

    # 根据文档位置调整权重
    if (
        "position_weight" in weight_config
        and weight_config["position_weight"]
        and weight_config["position_weight"] != ""
    ):
        position_weight = weight_config["position_weight"]
        total_docs = len(docs)
        for i in range(total_docs):
            if position_weight == "prefer_early":
                # 偏好早期文档
                weighted_sims[i] *= 1 + (total_docs - i) / total_docs
            elif position_weight == "prefer_late":
                # 偏好后期文档
                weighted_sims[i] *= 1 + i / total_docs

    # 根据关键词匹配调整权重
    if (
        "keyword_weight" in weight_config
        and weight_config["keyword_weight"]
        and len(weight_config["keyword_weight"]) > 0
    ):
        keywords = weight_config["keyword_weight"]
        for i, doc in enumerate(docs):
            keyword_count = sum(
                1 for keyword in keywords if keyword.lower() in doc.lower()
            )
            if keyword_count > 0:
                weighted_sims[i] *= 1 + keyword_count * 0.1

    return weighted_sims


def _apply_threshold_filter(sims, docs, doc_vectors, threshold):
    """
    应用相似度阈值过滤。

    :param sims: List[float]，相似度列表
    :param docs: List[str]，文档片段列表
    :param doc_vectors: List[List[float]]，文档向量列表
    :param threshold: float，相似度阈值
    :return: tuple，过滤后的相似度、文档、向量
    """
    filtered_indices = [i for i, sim in enumerate(sims) if sim >= threshold]

    filtered_sims = [sims[i] for i in filtered_indices]
    filtered_docs = [docs[i] for i in filtered_indices]
    filtered_vectors = [doc_vectors[i] for i in filtered_indices]

    return filtered_sims, filtered_docs, filtered_vectors


def _apply_deduplication(indices, sims, docs, threshold=0.95):
    """
    应用去重策略。

    :param indices: List[int]，文档索引列表
    :param sims: List[float]，相似度列表
    :param docs: List[str]，文档片段列表
    :param threshold: float，去重阈值
    :return: List[int]，去重后的索引列表
    """
    if len(indices) == 0:
        return indices

    deduplicated_indices = [indices[0]]

    for idx in indices[1:]:
        # 检查与已选文档的相似度
        is_duplicate = False
        for selected_idx in deduplicated_indices:
            # 计算文档间的相似度（简化版本，使用向量相似度）
            if selected_idx < len(sims) and idx < len(sims):
                # 这里可以进一步优化，使用实际的文档向量计算相似度
                doc_similarity = min(sims[selected_idx], sims[idx]) / max(
                    sims[selected_idx], sims[idx]
                )
                if doc_similarity > threshold:
                    is_duplicate = True
                    break

        if not is_duplicate:
            deduplicated_indices.append(idx)

    return deduplicated_indices


def _apply_context_window(indices, window_size, total_docs):
    """
    应用上下文窗口。

    :param indices: List[int]，文档索引列表
    :param window_size: int，上下文窗口大小
    :param total_docs: int，总文档数
    :return: List[int]，包含上下文的索引列表
    """
    if window_size <= 0:
        return indices

    expanded_indices = set()

    for idx in indices:
        # 添加当前索引
        expanded_indices.add(idx)

        # 添加上下文窗口
        for offset in range(-window_size, window_size + 1):
            context_idx = idx + offset
            if 0 <= context_idx < total_docs:
                expanded_indices.add(context_idx)

    # 保持原有顺序，但包含上下文
    result = []
    for idx in sorted(expanded_indices):
        if idx in indices or any(
            abs(idx - original_idx) <= window_size for original_idx in indices
        ):
            result.append(idx)

    return result


def get_retrieval_config():
    """
    获取默认的检索配置。

    :return: dict，默认检索配置
    """
    return {
        "top_k": 5,
        "similarity_threshold": 0.1,
        "deduplication": True,
        "retrieval_strategy": "cosine",
        "weight_config": {
            "length_weight": None,  # "prefer_long", "prefer_short", None
            "position_weight": None,  # "prefer_early", "prefer_late", None
            "keyword_weight": [],  # 关键词列表
        },
        "context_window": 1,
    }
