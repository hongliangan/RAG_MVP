#!/usr/bin/env python3
"""
测试增强检索功能
验证混合检索、搜索建议、历史记录等功能
"""
import os
import tempfile
from rag_core.knowledge_base import create_knowledge_base
from rag_core.enhanced_retriever import create_enhanced_retriever


def test_enhanced_retrieval():
    """测试增强检索功能"""
    print("=== 测试增强检索功能 ===")

    # 创建临时知识库
    kb = create_knowledge_base("test_enhanced")

    # 创建测试文档（使用更长的内容确保能正确切片）
    test_docs = [
        """人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。人工智能技术包括机器学习、深度学习、自然语言处理等多个领域。这些技术正在快速发展，并在各个行业中得到了广泛应用。""",
        """机器学习是人工智能的一个子集，它使计算机能够在没有明确编程的情况下学习和改进。机器学习算法通过分析大量数据来识别模式，并基于这些模式做出预测或决策。常见的机器学习方法包括监督学习、无监督学习和强化学习。""",
        """深度学习是机器学习的一个分支，使用神经网络来模拟人脑的学习过程。深度学习模型通常包含多个隐藏层，能够自动学习数据的复杂特征。在图像识别、语音识别、自然语言处理等领域，深度学习都取得了突破性的进展。""",
        """自然语言处理是人工智能的一个重要领域，专注于计算机理解和生成人类语言。NLP技术包括文本分析、机器翻译、情感分析、问答系统等。随着大语言模型的发展，自然语言处理的能力得到了显著提升。""",
        """计算机视觉是人工智能的一个分支，使计算机能够从图像和视频中获取信息。计算机视觉技术包括图像识别、目标检测、人脸识别、场景理解等。这些技术在自动驾驶、医疗诊断、安防监控等领域有重要应用。""",
    ]

    # 创建临时文件并添加到知识库
    temp_files = []
    try:
        for i, content in enumerate(test_docs):
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as f:
                f.write(content)
                temp_files.append(f.name)

            # 添加到知识库
            result = kb.add_document(temp_files[-1])
            if result["success"]:
                print(
                    f"✅ 文档 {i+1} 添加成功: {result['filename']} (切片数: {result['chunks_count']})"
                )
            else:
                print(f"❌ 文档 {i+1} 添加失败: {result.get('error', '未知错误')}")

        print(f"\n📊 知识库统计: {kb.get_stats()}")

        # 测试增强搜索
        print("\n=== 测试增强搜索 ===")
        test_queries = [
            "什么是人工智能",
            "机器学习技术",
            "深度学习神经网络",
            "自然语言处理",
            "计算机视觉应用",
        ]

        for query in test_queries:
            print(f"\n🔍 查询: {query}")

            # 增强搜索
            enhanced_results = kb.search(query, top_k=3, use_enhanced=True)
            print(f"增强搜索结果数量: {len(enhanced_results)}")
            for i, result in enumerate(enhanced_results[:2]):  # 只显示前2个结果
                print(
                    f"  {i+1}. 分数: {result.get('score', 0):.4f}, 来源: {result.get('source', 'unknown')}"
                )

            # 基础搜索
            basic_results = kb.search(query, top_k=3, use_enhanced=False)
            print(f"基础搜索结果数量: {len(basic_results)}")
            for i, result in enumerate(basic_results[:2]):  # 只显示前2个结果
                print(f"  {i+1}. 分数: {result.get('score', 0):.4f}")

        # 测试搜索建议
        print("\n=== 测试搜索建议 ===")
        suggestions = kb.get_search_suggestions("人工", limit=3)
        print(f"搜索建议: {suggestions}")

        # 测试搜索历史
        print("\n=== 测试搜索历史 ===")
        history = kb.get_search_history(limit=5)
        print(f"搜索历史数量: {len(history)}")
        for record in history:
            print(f"  - {record['query']} ({record['timestamp']})")

        # 测试结果导出
        print("\n=== 测试结果导出 ===")
        test_results = kb.search("人工智能", top_k=3, use_enhanced=True)
        if test_results:
            # 导出JSON
            json_file = kb.export_search_results(test_results, "json")
            print(f"JSON导出: {json_file}")

            # 导出TXT
            txt_file = kb.export_search_results(test_results, "txt")
            print(f"TXT导出: {txt_file}")

            # 导出CSV
            csv_file = kb.export_search_results(test_results, "csv")
            print(f"CSV导出: {csv_file}")

        print("\n✅ 增强检索功能测试完成！")

    finally:
        # 清理临时文件
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        # 清理知识库
        kb.clear()


def test_enhanced_retriever_directly():
    """直接测试增强检索器"""
    print("\n=== 直接测试增强检索器 ===")

    # 创建增强检索器
    retriever = create_enhanced_retriever("test_retriever_history.json")

    # 测试文档和向量（模拟数据）
    docs = [
        "人工智能技术正在快速发展，在各个领域都有重要应用。",
        "机器学习是AI的核心技术，通过数据学习来改进性能。",
        "深度学习在图像识别方面表现出色，准确率很高。",
        "自然语言处理让计算机理解人类语言，实现智能对话。",
    ]

    # 使用真实的embedding向量
    from rag_core.embedding import embed_documents

    doc_vectors = embed_documents(docs)

    # 测试混合搜索
    results = retriever.hybrid_search("人工智能", doc_vectors, docs, top_k=3)
    print(f"混合搜索结果: {len(results)}")
    for result in results:
        print(f"  - 分数: {result['fused_score']:.4f}, 来源: {result['source']}")

    # 测试搜索建议
    suggestions = retriever.get_search_suggestions("人工")
    print(f"搜索建议: {suggestions}")

    # 测试历史记录
    history = retriever.get_search_history()
    print(f"历史记录: {len(history)}")

    # 清理
    if os.path.exists("test_retriever_history.json"):
        os.remove("test_retriever_history.json")


if __name__ == "__main__":
    test_enhanced_retrieval()
    test_enhanced_retriever_directly()
