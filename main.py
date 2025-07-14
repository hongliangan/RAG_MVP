#!/usr/bin/env python3
"""
RAG MVP系统主入口

提供命令行界面，支持文档处理、知识库管理和问答功能
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from rag_core.data_loader import load_documents
from rag_core.embedding import embed_documents
from rag_core.retriever import retrieve
from rag_core.generator import generate_answer
from rag_core.knowledge_base import (
    KnowledgeBase,
    create_knowledge_base,
    list_knowledge_bases,
)
from utils.config import get_llm_config, get_retrieval_params


def main():
    """
    主函数：提供命令行RAG问答和知识库管理功能
    """
    parser = argparse.ArgumentParser(description="RAG MVP系统 - 文档问答和知识库管理")
    parser.add_argument(
        "--mode",
        choices=["qa", "kb"],
        default="qa",
        help="运行模式: qa(问答模式) 或 kb(知识库模式)",
    )

    # 问答模式参数
    parser.add_argument("--file", help="文档文件路径")
    parser.add_argument("--question", help="问题")

    # 知识库模式参数
    parser.add_argument("--kb-name", default="default", help="知识库名称")
    parser.add_argument(
        "--action",
        choices=["add", "search", "list", "delete", "stats", "clear"],
        help="知识库操作",
    )
    parser.add_argument("--document", help="要添加的文档路径")
    parser.add_argument("--query", help="搜索查询")
    parser.add_argument("--doc-id", type=int, help="文档ID")
    parser.add_argument("--top-k", type=int, default=5, help="返回结果数量")

    args = parser.parse_args()

    if args.mode == "qa":
        run_qa_mode(args)
    elif args.mode == "kb":
        run_kb_mode(args)


def run_qa_mode(args):
    """运行问答模式"""
    if not args.file or not args.question:
        print("问答模式需要指定 --file 和 --question 参数")
        print(
            "示例: python main.py --mode qa --file data/example.txt --question '请总结文档内容'"
        )
        sys.exit(1)

    file_path = args.file
    question = args.question

    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误：文件 {file_path} 不存在")
        sys.exit(1)

    try:
        print("=== RAG MVP 问答模式 ===")
        print(f"文档路径: {file_path}")
        print(f"问题: {question}")
        print("-" * 50)

        # 1. 加载文档
        print("1. 加载文档...")
        documents = load_documents(file_path)
        print(f"   加载了 {len(documents)} 个段落")

        # 2. 向量化文档
        print("2. 向量化文档...")
        doc_vectors = embed_documents(documents)
        print(f"   生成了 {len(doc_vectors)} 个向量")

        # 3. 获取检索参数
        retrieval_params = get_retrieval_params()
        print(f"3. 检索参数: {retrieval_params}")

        # 4. 检索相关文档
        print("4. 检索相关文档...")
        relevant_docs = retrieve(question, doc_vectors, documents, **retrieval_params)
        print(f"   检索到 {len(relevant_docs)} 个相关段落")

        # 5. 生成答案
        print("5. 生成答案...")
        answer = generate_answer(question, relevant_docs)

        print("-" * 50)
        print("答案:")
        print(answer)

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


def run_kb_mode(args):
    """运行知识库模式"""
    if not args.action:
        print("知识库模式需要指定 --action 参数")
        print("可用操作: add, search, list, delete, stats, clear")
        print("示例: python main.py --mode kb --action list --kb-name default")
        sys.exit(1)

    try:
        print("=== RAG MVP 知识库模式 ===")
        print(f"知识库: {args.kb_name}")
        print(f"操作: {args.action}")
        print("-" * 50)

        # 创建或获取知识库
        kb = create_knowledge_base(args.kb_name)

        if args.action == "add":
            if not args.document:
                print("添加文档需要指定 --document 参数")
                sys.exit(1)

            print(f"添加文档: {args.document}")
            result = kb.add_document(args.document)
            if result["success"]:
                print("✅ 文档添加成功")
                print(f"   文档ID: {result['document_id']}")
                print(f"   文本块数: {result['chunks_count']}")
                print(f"   向量数: {result['vectors_count']}")
            else:
                print(f"❌ 文档添加失败: {result['error']}")

        elif args.action == "search":
            if not args.query:
                print("搜索需要指定 --query 参数")
                sys.exit(1)

            print(f"搜索查询: {args.query}")
            results = kb.search(args.query, top_k=args.top_k)

            if results:
                print(f"找到 {len(results)} 个相关结果:")
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. 文档: {result['filename']}")
                    print(f"   相似度: {result['score']:.4f}")
                    print(f"   内容: {result['content'][:200]}...")
            else:
                print("未找到相关结果")

        elif args.action == "list":
            documents = kb.list_documents()
            if documents:
                print(f"知识库包含 {len(documents)} 个文档:")
                for doc in documents:
                    print(
                        f"  ID: {doc['id']}, 文件: {doc['filename']}, 大小: {doc['file_size']} bytes"
                    )
            else:
                print("知识库为空")

        elif args.action == "delete":
            if not args.doc_id:
                print("删除文档需要指定 --doc-id 参数")
                sys.exit(1)

            print(f"删除文档 ID: {args.doc_id}")
            if kb.delete_document(args.doc_id):
                print("✅ 文档删除成功")
            else:
                print("❌ 文档删除失败")

        elif args.action == "stats":
            stats = kb.get_stats()
            print("知识库统计信息:")
            print(f"  知识库名称: {stats['knowledge_base_name']}")
            print(f"  文档数量: {stats['document_count']}")
            print(f"  文本块数量: {stats['chunk_count']}")
            print(f"  向量数量: {stats['vector_count']}")
            print(f"  总大小: {stats['total_size_bytes']} bytes")
            print(f"  索引类型: {stats['index_type']}")
            print(f"  数据库路径: {stats['database_path']}")

        elif args.action == "clear":
            print("清空知识库...")
            if kb.clear():
                print("✅ 知识库已清空")
            else:
                print("❌ 清空知识库失败")

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


def list_all_knowledge_bases():
    """列出所有知识库"""
    kbs = list_knowledge_bases()
    if kbs:
        print("可用的知识库:")
        for kb_name in kbs:
            print(f"  - {kb_name}")
    else:
        print("没有找到知识库")


if __name__ == "__main__":
    main()
