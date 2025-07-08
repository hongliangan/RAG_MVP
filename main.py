#!/usr/bin/env python3
"""
RAG MVP系统主入口

提供命令行界面，支持文档处理和问答功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from rag_core.data_loader import load_documents
from rag_core.embedding import embed_documents
from rag_core.retriever import retrieve
from rag_core.generator import generate_answer
from utils.config import get_llm_config


def main():
    """
    主函数：提供命令行RAG问答功能
    
    使用方式：
    python main.py <文档路径> <问题>
    
    示例：
    python main.py data/example.txt "请总结文档内容"
    """
    if len(sys.argv) != 3:
        print("使用方式: python main.py <文档路径> <问题>")
        print("示例: python main.py data/example.txt '请总结文档内容'")
        sys.exit(1)
    
    file_path = sys.argv[1]
    question = sys.argv[2]
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误：文件 {file_path} 不存在")
        sys.exit(1)
    
    try:
        print("=== RAG MVP 系统 ===")
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
        
        # 3. 检索相关文档
        print("3. 检索相关文档...")
        relevant_docs = retrieve(question, doc_vectors, documents, top_k=3)
        print(f"   检索到 {len(relevant_docs)} 个相关段落")
        
        # 4. 生成答案
        print("4. 生成答案...")
        answer = generate_answer(question, relevant_docs)
        
        print("-" * 50)
        print("答案:")
        print(answer)
        
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
