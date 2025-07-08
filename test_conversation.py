#!/usr/bin/env python3
"""
测试多轮对话功能
"""
import os
import sys
import tempfile
import json

# 添加项目路径
sys.path.insert(0, os.path.abspath('.'))

from rag_core.conversation_manager import get_conversation_manager, Conversation
from rag_core.knowledge_base import create_knowledge_base


def create_test_document():
    """创建测试文档"""
    content = """
    RAG系统（检索增强生成）是一种结合了信息检索和文本生成的技术。
    
    主要组成部分：
    1. 文档加载器：支持多种格式的文档加载
    2. 文本分割器：将长文档分割成适合检索的小块
    3. 向量化模块：将文本转换为向量表示
    4. 检索模块：基于相似度搜索相关内容
    5. 生成模块：基于检索结果生成回答
    
    优势：
    - 可以处理大量文档
    - 回答基于实际文档内容
    - 支持实时更新知识库
    - 可追溯信息来源
    
    应用场景：
    - 智能客服
    - 文档问答
    - 知识管理
    - 研究助手
    """
    
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    temp_file.write(content)
    temp_file.close()
    
    return temp_file.name


def test_conversation_manager():
    """测试对话管理器"""
    print("=== 测试对话管理器 ===")
    
    # 获取对话管理器
    conv_manager = get_conversation_manager()
    
    # 创建新对话
    conversation = conv_manager.create_conversation("test_kb")
    print(f"创建对话: {conversation.session_id}")
    print(f"知识库: {conversation.kb_name}")
    
    # 添加消息
    conv_manager.add_message(conversation.session_id, "user", "什么是RAG系统？")
    conv_manager.add_message(conversation.session_id, "assistant", "RAG系统是检索增强生成的缩写，它结合了信息检索和文本生成技术。")
    
    # 获取上下文
    context = conv_manager.get_conversation_context(conversation.session_id)
    print(f"对话上下文: {context}")
    
    # 列出对话
    conversations = conv_manager.list_conversations("test_kb")
    print(f"对话列表: {len(conversations)} 个对话")
    
    # 导出对话
    export_content = conv_manager.export_conversation(conversation.session_id, "txt")
    if export_content:
        print(f"导出内容长度: {len(export_content)} 字符")
    else:
        print("导出失败")
    
    # 清理
    conv_manager.delete_conversation(conversation.session_id)
    print("对话已删除")
    
    print()


def test_conversation_with_knowledge_base():
    """测试与知识库结合的对话"""
    print("=== 测试与知识库结合的对话 ===")
    
    # 创建测试文档
    test_file = create_test_document()
    
    try:
        # 创建知识库并添加文档
        kb = create_knowledge_base("test_conversation")
        result = kb.add_document(test_file)
        
        if not result['success']:
            print(f"添加文档失败: {result.get('error')}")
            return
        
        print(f"文档添加成功: {result['filename']}")
        
        # 创建对话管理器
        conv_manager = get_conversation_manager()
        conversation = conv_manager.create_conversation("test_conversation")
        
        # 模拟多轮对话
        test_questions = [
            "什么是RAG系统？",
            "RAG系统有哪些组成部分？",
            "RAG系统有什么优势？",
            "RAG系统可以应用在哪些场景？"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- 第{i}轮对话 ---")
            print(f"用户: {question}")
            
            # 添加用户消息
            conv_manager.add_message(conversation.session_id, "user", question)
            
            # 在知识库中搜索
            search_results = kb.search(question, top_k=2, use_enhanced=True)
            print(f"搜索结果: {len(search_results)} 个")
            
            # 模拟AI回答（这里简化处理）
            if search_results:
                answer = f"根据检索到的内容，{search_results[0]['content'][:100]}..."
            else:
                answer = "抱歉，在知识库中没有找到相关信息。"
            
            print(f"AI: {answer}")
            
            # 添加AI回复
            conv_manager.add_message(conversation.session_id, "assistant", answer, {
                'search_results': len(search_results),
                'sources': [r.get('filename', '未知') for r in search_results]
            })
        
        # 获取完整对话上下文
        context = conv_manager.get_conversation_context(conversation.session_id)
        print(f"\n完整对话上下文长度: {len(context)} 字符")
        
        # 导出对话
        export_json = conv_manager.export_conversation(conversation.session_id, "json")
        export_txt = conv_manager.export_conversation(conversation.session_id, "txt")
        
        if export_json:
            print(f"JSON导出长度: {len(export_json)} 字符")
        else:
            print("JSON导出失败")
            
        if export_txt:
            print(f"TXT导出长度: {len(export_txt)} 字符")
        else:
            print("TXT导出失败")
        
        # 清理
        conv_manager.delete_conversation(conversation.session_id)
        kb.clear()
        
    finally:
        # 清理临时文件
        if os.path.exists(test_file):
            os.unlink(test_file)
    
    print()


def test_conversation_persistence():
    """测试对话持久化"""
    print("=== 测试对话持久化 ===")
    
    conv_manager = get_conversation_manager()
    
    # 创建对话
    conversation = conv_manager.create_conversation("test_persistence")
    
    # 添加一些消息
    messages = [
        ("user", "你好"),
        ("assistant", "你好！有什么可以帮助你的吗？"),
        ("user", "请介绍一下自己"),
        ("assistant", "我是一个AI助手，可以帮你回答问题。")
    ]
    
    for role, content in messages:
        conv_manager.add_message(conversation.session_id, role, content)
    
    session_id = conversation.session_id
    
    # 重新获取对话管理器（模拟重启）
    new_conv_manager = get_conversation_manager()
    
    # 尝试获取对话
    retrieved_conv = new_conv_manager.get_conversation(session_id)
    
    if retrieved_conv:
        print(f"对话恢复成功: {retrieved_conv.session_id}")
        print(f"消息数量: {len(retrieved_conv.messages)}")
        print(f"最后一条消息: {retrieved_conv.messages[-1]['content']}")
    else:
        print("对话恢复失败")
    
    # 清理
    conv_manager.delete_conversation(session_id)
    
    print()


def main():
    """主函数"""
    print("开始测试多轮对话功能...")
    print("=" * 50)
    
    # 测试对话管理器
    test_conversation_manager()
    
    # 测试与知识库结合的对话
    test_conversation_with_knowledge_base()
    
    # 测试对话持久化
    test_conversation_persistence()
    
    print("=" * 50)
    print("所有测试完成！")


if __name__ == "__main__":
    main() 