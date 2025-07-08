#!/usr/bin/env python3
"""
测试完整的RAG流程，包括新的文本切片功能
"""
import os
import sys
from rag_core.data_loader import load_documents
from rag_core.embedding import embed_documents
from rag_core.retriever import retrieve
from rag_core.llm_api import call_llm_api
from utils.config import get_text_chunk_config

def test_rag_with_different_chunk_configs():
    """测试不同切片配置下的RAG效果"""
    
    # 测试文档路径
    test_doc_path = "web/uploads/xRay.docx"
    
    if not os.path.exists(test_doc_path):
        print(f"❌ 测试文档不存在: {test_doc_path}")
        return
    
    print("=== RAG流程测试（不同切片配置） ===\n")
    
    # 测试查询
    test_query = "X射线是什么？它有什么用途？"
    print(f"测试查询: {test_query}\n")
    
    # 配置1: 按段落分割（默认）
    print("1. 按段落分割（默认配置）:")
    config1 = {"split_method": "paragraph"}
    test_rag_flow(test_doc_path, test_query, config1, "段落分割")
    
    # 配置2: 按字符数分割
    print("\n2. 按字符数分割（chunk_size=500）:")
    config2 = {
        "split_method": "character",
        "chunk_size": 500,
        "chunk_overlap": 100
    }
    test_rag_flow(test_doc_path, test_query, config2, "字符分割")
    
    # 配置3: 按句子分割
    print("\n3. 按句子分割（max_sentences=3）:")
    config3 = {
        "split_method": "sentence",
        "max_sentences_per_chunk": 3
    }
    test_rag_flow(test_doc_path, test_query, config3, "句子分割")

def test_rag_flow(doc_path, query, chunk_config, config_name):
    """测试单个RAG流程"""
    
    try:
        print(f"  配置: {config_name}")
        
        # 1. 文档加载和切片
        print("  📄 加载文档并切片...")
        chunks = load_documents(doc_path, chunk_config)
        print(f"    切片结果: {len(chunks)} 个块")
        for i, chunk in enumerate(chunks[:2], 1):
            print(f"    块 {i}: {len(chunk)} 字符 - {chunk[:60]}...")
        if len(chunks) > 2:
            print(f"    ... 还有 {len(chunks)-2} 个块")
        
        # 2. 向量化
        print("  🔢 生成向量...")
        embeddings = embed_documents(chunks)
        print(f"    向量化完成: {len(embeddings)} 个向量")
        
        # 3. 检索
        print("  🔍 检索相关片段...")
        similar_chunks = retrieve(query, embeddings, chunks, top_k=3)
        print(f"    检索到 {len(similar_chunks)} 个相关片段")
        for i, chunk in enumerate(similar_chunks, 1):
            print(f"    相关片段 {i}: {chunk[:80]}...")
        
        # 4. LLM生成
        print("  🤖 生成回答...")
        context = "\n\n".join(similar_chunks)
        prompt = f"""基于以下上下文信息回答问题：

上下文：
{context}

问题：{query}

请提供准确、详细的回答："""
        
        response = call_llm_api(prompt)
        print(f"    LLM回答: {response[:200]}...")
        
        print("  ✅ 流程完成")
        
    except Exception as e:
        print(f"  ❌ 错误: {e}")

def test_chunk_config_comparison():
    """比较不同切片配置的效果"""
    
    print("\n=== 切片配置效果比较 ===\n")
    
    # 测试文本
    test_text = """
    X射线是一种电磁辐射，波长比可见光短，能量比可见光高。X射线具有穿透性，能够穿透人体软组织，但会被骨骼等密度较大的组织吸收。

    X射线在医学诊断中广泛应用，主要用于检查骨折、肺部疾病、牙齿问题等。通过X射线摄影，医生可以观察到人体内部的结构，帮助诊断疾病。

    X射线技术也在工业检测、安全检查、材料分析等领域发挥重要作用。在机场安检中，X射线机可以检测行李中的违禁物品。

    然而，X射线对人体有一定的辐射危害，因此在使用时需要严格控制剂量，并采取必要的防护措施。
    """
    
    # 不同配置
    configs = {
        "段落分割": {"split_method": "paragraph"},
        "字符分割(500)": {"split_method": "character", "chunk_size": 500, "chunk_overlap": 100},
        "字符分割(300)": {"split_method": "character", "chunk_size": 300, "chunk_overlap": 50},
        "句子分割": {"split_method": "sentence", "max_sentences_per_chunk": 2}
    }
    
    from rag_core.text_splitter import TextSplitter
    
    for name, config in configs.items():
        print(f"{name}:")
        splitter = TextSplitter(config)
        chunks = splitter.split_text(test_text)
        print(f"  块数: {len(chunks)}")
        print(f"  平均长度: {sum(len(c) for c in chunks) // len(chunks) if chunks else 0} 字符")
        print(f"  长度范围: {min(len(c) for c in chunks) if chunks else 0} - {max(len(c) for c in chunks) if chunks else 0} 字符")
        print()

if __name__ == "__main__":
    # 测试切片配置比较
    test_chunk_config_comparison()
    
    # 测试完整RAG流程
    test_rag_with_different_chunk_configs() 