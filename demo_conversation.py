#!/usr/bin/env python3
"""
多轮对话功能演示脚本
"""
import os
import sys
import tempfile

# 添加项目路径
sys.path.insert(0, os.path.abspath("."))

from rag_core.conversation_manager import get_conversation_manager
from rag_core.knowledge_base import create_knowledge_base
from rag_core.llm_api import call_llm_api
from utils.config import get_llm_config


def create_demo_document():
    """创建演示文档"""
    content = """
    人工智能（AI）是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的系统。
    
    AI的主要类型：
    1. 弱人工智能（Narrow AI）：专注于特定任务，如语音识别、图像识别
    2. 强人工智能（General AI）：具有与人类相当的通用智能
    3. 超人工智能（Superintelligent AI）：超越人类智能的AI
    
    AI的应用领域：
    - 自然语言处理：机器翻译、文本生成、对话系统
    - 计算机视觉：图像识别、视频分析、自动驾驶
    - 机器学习：预测分析、推荐系统、异常检测
    - 机器人技术：工业机器人、服务机器人、医疗机器人
    
    AI的发展趋势：
    - 深度学习技术的突破
    - 大语言模型的发展
    - 多模态AI的兴起
    - AI伦理和安全的重要性
    """

    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    )
    temp_file.write(content)
    temp_file.close()

    return temp_file.name


def demo_conversation():
    """演示多轮对话功能"""
    print("🤖 多轮对话功能演示")
    print("=" * 50)

    # 创建演示文档
    demo_file = create_demo_document()

    try:
        # 创建知识库
        print("📚 创建知识库...")
        kb = create_knowledge_base("demo_conversation")

        # 添加文档
        print("📄 添加演示文档...")
        result = kb.add_document(demo_file)
        if not result["success"]:
            print(f"❌ 添加文档失败: {result.get('error')}")
            return

        print(f"✅ 文档添加成功: {result['filename']}")

        # 创建对话管理器
        conv_manager = get_conversation_manager()
        conversation = conv_manager.create_conversation("demo_conversation")

        print(f"💬 创建对话会话: {conversation.session_id[:8]}...")

        # 模拟多轮对话
        demo_questions = [
            "什么是人工智能？",
            "AI有哪些主要类型？",
            "AI在哪些领域有应用？",
            "AI的发展趋势是什么？",
            "你能总结一下我们刚才的对话吗？",
        ]

        for i, question in enumerate(demo_questions, 1):
            print(f"\n🔄 第{i}轮对话")
            print(f"👤 用户: {question}")

            # 添加用户消息
            conv_manager.add_message(conversation.session_id, "user", question)

            # 获取对话上下文
            context = conv_manager.get_conversation_context(conversation.session_id)

            # 在知识库中搜索
            search_results = kb.search(question, top_k=2, use_enhanced=True)

            # 构建增强的查询
            enhanced_query = question
            if context:
                enhanced_query = f"对话上下文：\n{context}\n\n当前问题：{question}"

            # 生成回答
            if search_results:
                # 构建检索到的内容
                retrieved_content = "\n\n".join(
                    [
                        f"相关内容 {i+1}：{result['content']}"
                        for i, result in enumerate(search_results)
                    ]
                )

                # 构建完整的prompt
                prompt = f"""基于以下检索到的相关内容，回答用户的问题。

检索到的相关内容：
{retrieved_content}

用户问题：{enhanced_query}

请基于检索到的内容，结合对话上下文，给出准确、详细的回答。如果检索到的内容不足以回答问题，请说明情况。"""
            else:
                prompt = f"""用户问题：{enhanced_query}

很抱歉，在知识库中没有找到与您问题相关的信息。请尝试换个方式提问，或者检查知识库中是否有相关文档。"""

            # 调用LLM生成回答
            llm_config = get_llm_config()
            response = call_llm_api(prompt, stream=False, **llm_config)

            print(f"🤖 AI: {response}")

            # 添加AI回复
            conv_manager.add_message(
                conversation.session_id,
                "assistant",
                response,
                {
                    "search_results": len(search_results),
                    "sources": [r.get("filename", "未知") for r in search_results],
                },
            )

        # 显示对话统计
        print(f"\n📊 对话统计")
        print(f"   会话ID: {conversation.session_id}")
        print(f"   消息数量: {len(conversation.messages)}")
        print(f"   知识库: {conversation.kb_name}")
        print(f"   创建时间: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        # 导出对话
        print(f"\n💾 导出对话...")
        export_txt = conv_manager.export_conversation(conversation.session_id, "txt")
        if export_txt:
            # 保存到文件
            export_file = f"conversation_export_{conversation.session_id[:8]}.txt"
            with open(export_file, "w", encoding="utf-8") as f:
                f.write(export_txt)
            print(f"✅ 对话已导出到: {export_file}")

        # 清理
        conv_manager.delete_conversation(conversation.session_id)
        kb.clear()

        print(f"\n🎉 演示完成！")
        print(f"💡 提示: 启动Web应用 (python web/app.py) 体验完整的对话界面")

    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")

    finally:
        # 清理临时文件
        if os.path.exists(demo_file):
            os.unlink(demo_file)


if __name__ == "__main__":
    demo_conversation()
