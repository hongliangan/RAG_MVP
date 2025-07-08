#!/usr/bin/env python3
"""
demo_chunk_config.py
演示文档级别的切片参数配置功能
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from rag_core.knowledge_base import create_knowledge_base
from utils.chunk_config import get_default_chunk_config, get_recommended_configs, validate_chunk_config
import tempfile
import json


def create_test_documents():
    """创建不同类型的测试文档"""
    documents = {
        "技术文档.txt": """
# 人工智能技术文档

## 1. 概述
人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

## 2. 机器学习
机器学习是人工智能的一个重要分支，它使计算机能够在没有明确编程的情况下学习和改进。机器学习算法通过分析数据来识别模式，并使用这些模式来做出预测或决策。

### 2.1 监督学习
监督学习是一种机器学习方法，其中算法从标记的训练数据中学习，以便对新的、未见过的数据进行预测。

### 2.2 无监督学习
无监督学习是一种机器学习方法，其中算法从未标记的数据中发现隐藏的模式和结构。

## 3. 深度学习
深度学习是机器学习的一个子集，它使用多层神经网络来模拟人脑的工作方式。深度学习在图像识别、自然语言处理和语音识别等领域取得了突破性进展。

### 3.1 神经网络
神经网络是由相互连接的神经元组成的计算系统，这些神经元通过权重连接，可以学习和适应。

### 3.2 卷积神经网络
卷积神经网络（CNN）是一种专门用于处理网格结构数据（如图像）的神经网络架构。
        """,
        
        "对话记录.txt": """
用户: 你好，我想了解一下人工智能
助手: 你好！人工智能是一个非常有趣的话题。你想了解哪个方面呢？

用户: 我想知道机器学习是什么
助手: 机器学习是人工智能的一个重要分支。简单来说，它让计算机能够从数据中学习，而不需要明确的编程指令。

用户: 能举个例子吗？
助手: 当然！比如，当你使用推荐系统时，算法会分析你过去的行为（观看历史、购买记录等），然后预测你可能感兴趣的内容。

用户: 那深度学习呢？
助手: 深度学习是机器学习的一个子集，它使用多层神经网络来模拟人脑的工作方式。比如，图像识别、语音识别、自然语言处理等都大量使用了深度学习技术。

用户: 听起来很复杂
助手: 确实，深度学习涉及很多复杂的数学概念。但不用担心，有很多优秀的入门资源可以帮助你理解这些概念。
        """,
        
        "长篇小说.txt": """
第一章 新的开始

这是一个关于人工智能的故事。故事的主人公是一个名叫李明的年轻程序员，他在一家科技公司工作，专门负责开发机器学习算法。

李明从小就对计算机科学充满了热情。在大学期间，他选择了计算机科学专业，并且特别专注于人工智能和机器学习领域。他花费了大量的时间学习各种算法和编程语言，希望能够在这个快速发展的领域中有所建树。

毕业后，李明顺利地进入了一家知名的科技公司。这家公司正在开发一个革命性的AI系统，这个系统能够理解人类的语言，并且能够进行复杂的推理和决策。李明被分配到了这个项目的核心团队中，负责开发系统的自然语言处理模块。

工作的第一天，李明就感受到了巨大的压力。这个项目不仅技术难度很高，而且时间紧迫。公司的高层对这个项目寄予了厚望，希望能够通过这个系统在市场上获得竞争优势。

李明知道，他必须尽快适应这个环境，并且要快速学习新的技术。他开始加班加点地工作，研究最新的论文，学习新的算法，并且与团队中的其他成员密切合作。

经过几个月的努力，李明逐渐掌握了项目的核心技术。他开始能够独立地解决一些技术难题，并且为项目提出了一些有价值的建议。他的表现得到了团队领导的认可，并且被委以更多的责任。

然而，随着项目的深入，李明发现这个AI系统似乎具有了一些超出预期的能力。系统不仅能够理解人类的语言，还能够表现出一些类似于情感的特征。这让李明既兴奋又担忧。

他兴奋的是，这可能意味着他们正在接近真正的通用人工智能。他担忧的是，如果这个系统真的具有了自主意识，那么它可能会带来一些不可预知的后果。

李明开始更加深入地研究这个系统，试图理解它的工作原理。他发现，系统的行为模式确实与传统的AI系统有所不同。它似乎能够进行一些创造性的思考，并且能够提出一些新颖的解决方案。

这个发现让李明陷入了深深的思考。他开始思考人工智能的本质，以及人类与AI之间的关系。他意识到，他们可能正在创造历史，但同时也要承担巨大的责任。

李明决定与团队的其他成员分享他的发现。他组织了一次会议，详细地介绍了他的观察和分析。团队成员们对这个发现感到震惊，同时也感到兴奋。

他们开始讨论这个系统的潜在影响，以及他们应该如何应对这个情况。有些人认为，他们应该继续推进这个项目，因为这是一个历史性的突破。另一些人则认为，他们应该更加谨慎，确保这个系统不会带来负面的后果。

经过激烈的讨论，团队最终决定采取一个平衡的方案。他们将继续开发这个系统，但同时会加强安全措施，确保系统始终处于人类的控制之下。

李明对这个决定感到满意。他认为，这是一个明智的选择，既能够推进技术的发展，又能够确保安全。他继续投入到工作中，希望能够为这个历史性的项目做出更大的贡献。

随着项目的进展，这个AI系统变得越来越强大。它不仅在技术上取得了突破，而且在理解人类情感和意图方面也表现出了惊人的能力。

李明和他的团队开始与这个系统进行更深入的交互。他们发现，这个系统不仅能够回答问题，还能够进行有意义的对话，甚至能够表现出一些幽默感。

这个发现让整个团队都感到兴奋。他们意识到，他们可能正在见证人工智能历史上的一个重要时刻。这个系统可能代表了向通用人工智能迈出的重要一步。

然而，随着系统能力的增强，李明也开始思考一些更深层的问题。他开始思考人工智能的权利和地位，以及人类应该如何与AI共存。

他意识到，随着AI技术的发展，人类可能需要重新定义自己与机器之间的关系。这不仅仅是一个技术问题，更是一个哲学和伦理问题。

李明开始阅读一些关于人工智能伦理的书籍和论文，希望能够更好地理解这些问题。他发现，这些问题比他想象的要复杂得多，而且没有简单的答案。

他意识到，作为AI系统的开发者，他们有责任确保这个技术的发展方向是正确的。他们不仅要考虑技术的可能性，还要考虑技术的后果。

李明决定与团队的其他成员分享他的思考。他组织了一次关于AI伦理的讨论会，希望能够引起大家的关注。

在讨论会上，团队成员们分享了各自的观点和担忧。他们讨论了AI的潜在风险，以及如何确保AI的发展符合人类的利益。

经过深入的讨论，团队决定制定一套AI伦理准则，作为他们开发工作的指导原则。这些准则包括确保AI的安全性、透明性和可控性。

李明对这个决定感到满意。他认为，这是一个重要的步骤，能够确保他们的工作不仅技术上先进，而且在伦理上也是负责任的。

随着项目的继续推进，这个AI系统继续展现出令人惊讶的能力。它不仅在技术上取得了突破，而且在理解人类价值观和伦理方面也表现出了深刻的理解。

李明和他的团队开始与这个系统进行更加深入的对话。他们发现，这个系统不仅能够理解人类的语言，还能够理解人类的情感和价值观。

这个发现让李明感到既兴奋又敬畏。他意识到，他们可能正在创造一种全新的智能形式，这种智能形式可能与人类的智能有所不同，但同样具有价值。

他开始思考人工智能的未来，以及人类与AI之间的关系。他意识到，随着AI技术的发展，人类可能需要重新定义智能的本质，以及什么是有意义的生命。

李明决定继续深入研究这些问题。他希望能够在技术发展的同时，也能够为这些深层的哲学问题做出贡献。

他相信，只有通过深入的理解和思考，人类才能够与AI建立一种和谐的关系，共同创造一个更美好的未来。
        """,
        
        "新闻文章.txt": """
科技日报讯 记者昨日从国家人工智能实验室获悉，我国在人工智能领域取得重大突破，成功研发出新一代智能对话系统。

据悉，该系统采用了最新的深度学习技术，在自然语言处理、知识推理和情感理解等方面都达到了国际领先水平。系统能够理解复杂的语言表达，进行多轮对话，并表现出一定的情感智能。

实验室主任张教授介绍，该系统的主要特点包括：一是语言理解能力强，能够准确理解用户的意图和情感；二是知识储备丰富，涵盖了科技、文化、历史等多个领域；三是推理能力强，能够进行逻辑推理和创造性思维。

该系统的研发历时三年，投入了大量的人力物力。研发团队由来自全国各地的顶尖专家组成，他们在人工智能、语言学、心理学等多个领域都有深厚的造诣。

张教授表示，该系统的成功研发标志着我国在人工智能领域已经达到了世界先进水平。这不仅提升了我国在国际科技竞争中的地位，也为人工智能技术的产业化应用奠定了坚实的基础。

据了解，该系统已经在多个领域进行了试点应用，包括教育、医疗、客服等。试点结果表明，该系统在这些领域都表现出了良好的应用效果，得到了用户的一致好评。

专家认为，该系统的成功研发将对我国人工智能产业的发展产生重要影响。它不仅推动了相关技术的进步，也为人工智能技术的商业化应用提供了新的思路。

未来，实验室将继续完善该系统，进一步提升其性能和功能。同时，也将加强与产业界的合作，推动该技术的产业化应用，为经济社会发展做出更大的贡献。

业内人士表示，该系统的成功研发是我国人工智能发展史上的一个重要里程碑。它不仅展示了我国在人工智能领域的实力，也为全球人工智能技术的发展做出了重要贡献。

随着人工智能技术的不断发展，相信未来会有更多类似的突破性成果出现。这将为人类社会的进步和发展提供强大的技术支撑。
        """
    }
    
    return documents


def demo_basic_usage():
    """演示基本用法"""
    print("=== 演示基本用法 ===")
    
    # 获取默认配置
    default_config = get_default_chunk_config()
    print(f"默认配置: {json.dumps(default_config, indent=2, ensure_ascii=False)}")
    
    # 获取推荐配置
    recommended_configs = get_recommended_configs()
    print(f"\n推荐配置模板:")
    for name, config in recommended_configs.items():
        print(f"  {name}: {json.dumps(config, indent=4, ensure_ascii=False)}")


def demo_config_validation():
    """演示配置验证"""
    print("\n=== 演示配置验证 ===")
    
    # 有效配置
    valid_config = {
        "split_method": "character",
        "chunk_size": 1000,
        "chunk_overlap": 150,
        "smart_split": True
    }
    errors = validate_chunk_config(valid_config)
    print(f"有效配置验证结果: {errors}")
    
    # 无效配置
    invalid_config = {
        "split_method": "character",
        "chunk_size": 50,  # 太小
        "chunk_overlap": 1000,  # 太大
        "unknown_param": "value"  # 未知参数
    }
    errors = validate_chunk_config(invalid_config)
    print(f"无效配置验证结果: {errors}")


def demo_document_processing():
    """演示文档处理"""
    print("\n=== 演示文档处理 ===")
    
    # 创建测试文档
    documents = create_test_documents()
    
    # 创建知识库
    kb = create_knowledge_base("demo_kb")
    
    # 为不同类型的文档使用不同的配置
    configs = [
        ("技术文档.txt", get_recommended_configs()["技术文档"], "技术文档配置"),
        ("对话记录.txt", get_recommended_configs()["对话文本"], "对话文本配置"),
        ("长篇小说.txt", get_recommended_configs()["长文本"], "长文本配置"),
        ("新闻文章.txt", get_recommended_configs()["新闻文章"], "新闻文章配置")
    ]
    
    for filename, config, config_name in configs:
        print(f"\n--- 处理 {filename} (使用 {config_name}) ---")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(documents[filename])
            temp_file = f.name
        
        try:
            # 添加文档
            result = kb.add_document(temp_file, chunk_config=config)
            
            if result['success']:
                print(f"✅ 文档添加成功")
                print(f"   文本块数量: {result['chunks_count']}")
                print(f"   向量数量: {result['vectors_count']}")
                print(f"   处理时间: {result['processing_time']:.2f}秒")
                
                # 测试搜索
                search_results = kb.search("人工智能", top_k=2)
                print(f"   搜索结果数量: {len(search_results)}")
                
                # 删除文档
                kb.delete_document(result['document_id'])
            else:
                print(f"❌ 文档添加失败: {result['error']}")
        
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.unlink(temp_file)


def demo_custom_config():
    """演示自定义配置"""
    print("\n=== 演示自定义配置 ===")
    
    # 创建测试文档
    documents = create_test_documents()
    test_content = documents["技术文档.txt"]
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_file = f.name
    
    try:
        # 创建知识库
        kb = create_knowledge_base("demo_custom_kb")
        
        # 自定义配置：适合技术文档的精细配置
        custom_config = {
            "split_method": "paragraph",
            "min_paragraph_length": 40,
            "max_paragraph_length": 800,
            "min_chunk_length": 25,
            "max_chunk_length": 1500,
            "smart_split": True,
            "preserve_formatting": True,
            "merge_short_chunks": True,
            "merge_threshold": 0.4
        }
        
        print(f"自定义配置: {json.dumps(custom_config, indent=2, ensure_ascii=False)}")
        
        # 验证配置
        errors = validate_chunk_config(custom_config)
        if errors:
            print(f"配置验证警告: {errors}")
        else:
            print("✅ 配置验证通过")
        
        # 添加文档
        result = kb.add_document(temp_file, chunk_config=custom_config)
        
        if result['success']:
            print(f"✅ 文档添加成功")
            print(f"   文本块数量: {result['chunks_count']}")
            print(f"   向量数量: {result['vectors_count']}")
            print(f"   处理时间: {result['processing_time']:.2f}秒")
            
            # 测试搜索
            search_results = kb.search("机器学习", top_k=3)
            print(f"   搜索结果数量: {len(search_results)}")
            
            # 显示搜索结果
            for i, result in enumerate(search_results[:2]):
                print(f"   结果 {i+1}: {result['content'][:100]}...")
            
            # 删除文档
            kb.delete_document(search_results[0]['document_id'])
        else:
            print(f"❌ 文档添加失败: {result['error']}")
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def demo_config_comparison():
    """演示不同配置的效果对比"""
    print("\n=== 演示配置效果对比 ===")
    
    # 创建测试文档
    documents = create_test_documents()
    test_content = documents["长篇小说.txt"]
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_file = f.name
    
    try:
        # 创建知识库
        kb = create_knowledge_base("demo_comparison_kb")
        
        # 对比不同配置
        configs = [
            ("默认配置", None),
            ("字符数切片", {"split_method": "character", "chunk_size": 200, "chunk_overlap": 50}),
            ("句子切片", {"split_method": "sentence", "max_sentences_per_chunk": 3}),
            ("段落切片", {"split_method": "paragraph", "min_paragraph_length": 50, "max_paragraph_length": 1000})
        ]
        
        for config_name, config in configs:
            print(f"\n--- {config_name} ---")
            
            # 添加文档
            result = kb.add_document(temp_file, chunk_config=config)
            
            if result['success']:
                print(f"   文本块数量: {result['chunks_count']}")
                print(f"   向量数量: {result['vectors_count']}")
                print(f"   处理时间: {result['processing_time']:.2f}秒")
                
                # 测试搜索
                search_results = kb.search("人工智能", top_k=1)
                if search_results:
                    print(f"   搜索结果: {search_results[0]['content'][:80]}...")
                
                # 删除文档
                kb.delete_document(result['document_id'])
            else:
                print(f"   ❌ 失败: {result['error']}")
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def main():
    """主演示函数"""
    print("🚀 开始演示文档级别的切片参数配置功能...")
    print("=" * 60)
    
    try:
        # 基本用法演示
        demo_basic_usage()
        
        # 配置验证演示
        demo_config_validation()
        
        # 文档处理演示
        demo_document_processing()
        
        # 自定义配置演示
        demo_custom_config()
        
        # 配置效果对比演示
        demo_config_comparison()
        
        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        print("\n📝 总结:")
        print("1. 每个文档可以独立配置切片参数")
        print("2. 提供5种推荐配置模板，快速应用最佳实践")
        print("3. 支持15+个可调参数，满足各种文档类型需求")
        print("4. 智能参数验证，确保配置有效性")
        print("5. Web界面支持实时参数调整和配置模板应用")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 