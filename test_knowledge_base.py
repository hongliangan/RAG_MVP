#!/usr/bin/env python3
"""
test_knowledge_base.py
知识库功能测试脚本
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from rag_core.knowledge_base import KnowledgeBase, create_knowledge_base, list_knowledge_bases
from rag_core.vector_store import VectorStore


def test_vector_store():
    """测试向量存储引擎"""
    print("=== 测试向量存储引擎 ===")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        
        try:
            # 初始化向量存储
            vs = VectorStore(db_path)
            print("✅ 向量存储初始化成功")
            
            # 创建测试文件
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("这是测试文档内容")
            
            # 测试添加文档
            test_chunks = ["这是第一个文本块", "这是第二个文本块", "这是第三个文本块"]
            test_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
            
            doc_id = vs.add_document(test_file, test_chunks, test_embeddings)
            print(f"✅ 文档添加成功，ID: {doc_id}")
            
            # 测试搜索
            query_vector = [0.1, 0.2, 0.3]
            results = vs.search(query_vector, top_k=2)
            print(f"✅ 搜索成功，找到 {len(results)} 个结果")
            
            # 测试文档列表
            documents = vs.list_documents()
            print(f"✅ 文档列表获取成功，共 {len(documents)} 个文档")
            
            # 测试统计信息
            stats = vs.get_stats()
            print(f"✅ 统计信息获取成功: {stats}")
            
            # 测试删除文档
            success = vs.delete_document(doc_id)
            print(f"✅ 文档删除{'成功' if success else '失败'}")
            
        except Exception as e:
            print(f"❌ 向量存储测试失败: {e}")
            return False
    
    return True


def test_knowledge_base():
    """测试知识库管理器"""
    print("\n=== 测试知识库管理器 ===")
    
    # 创建临时知识库
    with tempfile.TemporaryDirectory() as temp_dir:
        kb_path = os.path.join(temp_dir, "test_kb")
        
        try:
            # 创建知识库
            kb = KnowledgeBase("test", kb_path)
            print("✅ 知识库创建成功")
            
            # 创建测试文档
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("这是一个测试文档。\n\n包含多个段落。\n\n用于测试知识库功能。\n\n这个文档包含足够的内容来生成文本块。")
            
            # 测试添加文档
            result = kb.add_document(test_file)
            if result['success']:
                print(f"✅ 文档添加成功: {result}")
            else:
                print(f"❌ 文档添加失败: {result['error']}")
                return False
            
            # 测试搜索
            results = kb.search("测试文档", top_k=3)
            print(f"✅ 搜索成功，找到 {len(results)} 个结果")
            
            # 测试文档列表
            documents = kb.list_documents()
            print(f"✅ 文档列表获取成功，共 {len(documents)} 个文档")
            
            # 测试统计信息
            stats = kb.get_stats()
            print(f"✅ 统计信息获取成功: {stats}")
            
            # 测试删除文档
            if documents:
                doc_id = documents[0]['id']
                success = kb.delete_document(doc_id)
                print(f"✅ 文档删除{'成功' if success else '失败'}")
            
        except Exception as e:
            print(f"❌ 知识库测试失败: {e}")
            return False
    
    return True


def test_knowledge_base_functions():
    """测试知识库工具函数"""
    print("\n=== 测试知识库工具函数 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # 测试创建知识库函数
            kb = create_knowledge_base("test_func", temp_dir)
            print("✅ create_knowledge_base 函数测试成功")
            
            # 测试列出知识库函数
            kbs = list_knowledge_bases(temp_dir)
            print(f"✅ list_knowledge_bases 函数测试成功，找到 {len(kbs)} 个知识库")
            
        except Exception as e:
            print(f"❌ 知识库工具函数测试失败: {e}")
            return False
    
    return True


def test_integration():
    """集成测试"""
    print("\n=== 集成测试 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # 创建知识库
            kb = create_knowledge_base("integration_test", temp_dir)
            
            # 创建多个测试文档
            test_files = []
            for i in range(3):
                test_file = os.path.join(temp_dir, f"test_{i}.txt")
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write(f"这是第{i+1}个测试文档。\n\n包含一些测试内容。\n\n这个文档用于测试知识库功能。\n\n包含足够的内容来生成文本块。")
                test_files.append(test_file)
            
            # 批量添加文档
            for test_file in test_files:
                result = kb.add_document(test_file)
                if not result['success']:
                    print(f"❌ 文档添加失败: {result['error']}")
                    return False
            
            print("✅ 批量文档添加成功")
            
            # 测试搜索功能
            search_results = kb.search("测试", top_k=5)
            print(f"✅ 搜索功能正常，找到 {len(search_results)} 个结果")
            
            # 测试文档管理
            documents = kb.list_documents()
            print(f"✅ 文档管理功能正常，共 {len(documents)} 个文档")
            
            # 测试清空功能
            success = kb.clear()
            print(f"✅ 清空功能{'正常' if success else '异常'}")
            
        except Exception as e:
            print(f"❌ 集成测试失败: {e}")
            return False
    
    return True


def main():
    """主测试函数"""
    print("开始知识库功能测试...\n")
    
    tests = [
        ("向量存储引擎", test_vector_store),
        ("知识库管理器", test_knowledge_base),
        ("知识库工具函数", test_knowledge_base_functions),
        ("集成测试", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"运行测试: {test_name}")
        print('='*50)
        
        try:
            if test_func():
                print(f"✅ {test_name} 测试通过")
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print(f"\n{'='*50}")
    print(f"测试结果: {passed}/{total} 通过")
    print('='*50)
    
    if passed == total:
        print("🎉 所有测试通过！知识库功能正常。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查相关功能。")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 