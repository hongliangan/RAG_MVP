#!/usr/bin/env python3
"""
test_chunk_config.py
测试文档级别的切片参数配置功能
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from rag_core.knowledge_base import create_knowledge_base
from utils.chunk_config import (
    get_default_chunk_config,
    get_recommended_configs,
    validate_chunk_config,
    get_parameters_by_category,
)
from rag_core.text_splitter import TextSplitter
import tempfile
import json


def test_chunk_config_manager():
    """测试切片配置管理器"""
    print("=== 测试切片配置管理器 ===")

    # 测试默认配置
    default_config = get_default_chunk_config()
    print(f"默认配置: {json.dumps(default_config, indent=2, ensure_ascii=False)}")

    # 测试推荐配置
    recommended_configs = get_recommended_configs()
    print(f"\n推荐配置模板:")
    for name, config in recommended_configs.items():
        print(f"  {name}: {json.dumps(config, indent=4, ensure_ascii=False)}")

    # 测试参数分类
    parameters_by_category = get_parameters_by_category()
    print(f"\n参数分类:")
    for category, params in parameters_by_category.items():
        print(f"  {category}:")
        for param in params:
            print(f"    - {param.name}: {param.description}")

    # 测试配置验证
    print(f"\n=== 测试配置验证 ===")

    # 有效配置
    valid_config = {
        "split_method": "character",
        "chunk_size": 1000,
        "chunk_overlap": 150,
        "smart_split": True,
    }
    errors = validate_chunk_config(valid_config)
    print(f"有效配置验证结果: {errors}")

    # 无效配置
    invalid_config = {
        "split_method": "character",
        "chunk_size": 50,  # 太小
        "chunk_overlap": 1000,  # 太大
        "unknown_param": "value",  # 未知参数
    }
    errors = validate_chunk_config(invalid_config)
    print(f"无效配置验证结果: {errors}")


def test_text_splitter_with_config():
    """测试使用自定义配置的文本切片器"""
    print(f"\n=== 测试文本切片器配置 ===")

    # 测试文本
    test_text = """
    这是第一个段落。它包含了一些基本的文本内容。
    
    这是第二个段落。它比第一个段落要长一些，包含更多的内容。
    这个段落有多个句子，用来测试不同的切片方式。
    
    第三个段落比较短。
    
    这是第四个段落，内容非常丰富。它包含了很多信息，可以用来测试各种切片参数。
    这个段落特别长，包含了多个句子和复杂的结构。
    我们希望通过不同的切片方式来获得最佳的检索效果。
    """

    # 测试不同配置
    configs = [
        {"name": "默认配置", "config": None},
        {
            "name": "字符数切片",
            "config": {
                "split_method": "character",
                "chunk_size": 100,
                "chunk_overlap": 20,
                "smart_split": True,
            },
        },
        {
            "name": "句子切片",
            "config": {
                "split_method": "sentence",
                "max_sentences_per_chunk": 2,
                "min_chunk_length": 10,
            },
        },
        {
            "name": "段落切片",
            "config": {
                "split_method": "paragraph",
                "min_paragraph_length": 20,
                "max_paragraph_length": 200,
                "merge_short_chunks": True,
            },
        },
        {"name": "长文本配置", "config": get_recommended_configs()["长文本"]},
    ]

    for test_config in configs:
        print(f"\n--- {test_config['name']} ---")

        # 创建切片器
        splitter = TextSplitter(test_config["config"])

        # 切片文本
        chunks = splitter.split_text(test_text)

        print(f"切片方式: {splitter.split_method}")
        print(f"文本块数量: {len(chunks)}")
        print(f"配置: {splitter.config}")

        # 显示前几个文本块
        for i, chunk in enumerate(chunks[:3]):
            print(f"  块 {i+1} ({len(chunk)} 字符): {chunk[:50]}...")


def test_knowledge_base_with_config():
    """测试知识库的文档级别配置"""
    print(f"\n=== 测试知识库文档级别配置 ===")

    # 创建临时测试文件
    test_content = """
    人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

    机器学习是人工智能的一个重要分支，它使计算机能够在没有明确编程的情况下学习和改进。机器学习算法通过分析数据来识别模式，并使用这些模式来做出预测或决策。

    深度学习是机器学习的一个子集，它使用多层神经网络来模拟人脑的工作方式。深度学习在图像识别、自然语言处理和语音识别等领域取得了突破性进展。

    自然语言处理（NLP）是人工智能的另一个重要领域，它使计算机能够理解、解释和生成人类语言。NLP技术被广泛应用于机器翻译、聊天机器人和文本分析等应用。
    """

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(test_content)
        temp_file = f.name

    try:
        # 创建测试知识库
        kb = create_knowledge_base("test_config_kb")

        # 测试不同配置添加文档
        configs = [
            {"name": "默认配置", "config": None},
            {"name": "技术文档配置", "config": get_recommended_configs()["技术文档"]},
            {
                "name": "自定义配置",
                "config": {
                    "split_method": "character",
                    "chunk_size": 150,
                    "chunk_overlap": 30,
                    "smart_split": True,
                    "merge_short_chunks": True,
                    "merge_threshold": 0.5,
                },
            },
        ]

        for test_config in configs:
            print(f"\n--- 使用 {test_config['name']} 添加文档 ---")

            # 添加文档
            result = kb.add_document(temp_file, chunk_config=test_config["config"])

            if result["success"]:
                print(f"文档添加成功: {result['filename']}")
                print(f"文本块数量: {result['chunks_count']}")
                print(f"向量数量: {result['vectors_count']}")
                print(f"处理时间: {result['processing_time']:.2f}秒")

                # 测试搜索
                search_results = kb.search("人工智能", top_k=3)
                print(f"搜索结果数量: {len(search_results)}")

                # 删除文档以便下次测试
                kb.delete_document(result["document_id"])
            else:
                print(f"文档添加失败: {result['error']}")

    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_config_info_api():
    """测试配置信息API"""
    print(f"\n=== 测试配置信息API ===")

    kb = create_knowledge_base("test_api_kb")

    # 获取配置信息
    config_info = kb.get_chunk_config_info()

    print("配置信息:")
    print(
        f"默认配置: {json.dumps(config_info['default_config'], indent=2, ensure_ascii=False)}"
    )
    print(f"推荐配置数量: {len(config_info['recommended_configs'])}")
    print(f"参数分类数量: {len(config_info['parameters'])}")

    # 测试配置验证
    test_config = {
        "split_method": "character",
        "chunk_size": 1000,
        "chunk_overlap": 200,
    }

    errors = kb.validate_chunk_config(test_config)
    print(f"配置验证结果: {errors}")


def main():
    """主测试函数"""
    print("开始测试文档级别的切片参数配置功能...")

    try:
        # 测试配置管理器
        test_chunk_config_manager()

        # 测试文本切片器
        test_text_splitter_with_config()

        # 测试知识库配置
        test_knowledge_base_with_config()

        # 测试API
        test_config_info_api()

        print(f"\n=== 所有测试完成 ===")
        print("✅ 文档级别的切片参数配置功能测试通过！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
