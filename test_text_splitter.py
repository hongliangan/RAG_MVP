#!/usr/bin/env python3
"""
测试文本切片器的不同参数配置
"""
import os
from rag_core.text_splitter import TextSplitter, split_text

def test_text_splitting():
    """测试不同的文本切片方式"""
    
    # 测试文本
    test_text = """
    人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

    该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大，可以设想，未来人工智能带来的科技产品，将会是人类智慧的"容器"。

    人工智能可以对人的意识、思维的信息过程的模拟。人工智能不是人的智能，但能像人那样思考、也可能超过人的智能。人工智能是一门极富挑战性的科学，从事人工智能研究的人员必须懂得计算机知识，心理学和哲学。

    人工智能是包括十分广泛的科学，它由不同的领域组成，如机器学习，计算机视觉等等，总的说来，人工智能研究的一个主要目标是使机器能够胜任一些通常需要人类智能才能完成的复杂工作。

    深度学习是人工智能的一个重要分支，它试图模仿人脑的神经网络结构，通过多层神经网络来学习数据的特征表示。深度学习在图像识别、语音识别、自然语言处理等领域取得了突破性进展。

    机器学习是人工智能的核心技术之一，它使计算机能够在没有明确编程的情况下学习和改进。机器学习算法通过分析大量数据来识别模式，并基于这些模式做出预测或决策。
    """
    
    print("=== 文本切片器测试 ===\n")
    print(f"原始文本长度: {len(test_text)} 字符\n")
    
    # 测试1: 按段落分割（默认）
    print("1. 按段落分割（默认配置）:")
    config1 = {"split_method": "paragraph"}
    splitter1 = TextSplitter(config1)
    chunks1 = splitter1.split_text(test_text)
    print(f"   分割结果: {len(chunks1)} 个块")
    for i, chunk in enumerate(chunks1[:3], 1):  # 只显示前3个块
        print(f"   块 {i}: {len(chunk)} 字符 - {chunk[:50]}...")
    print()
    
    # 测试2: 按字符数分割
    print("2. 按字符数分割（chunk_size=500, overlap=100）:")
    config2 = {
        "split_method": "character",
        "chunk_size": 500,
        "chunk_overlap": 100
    }
    splitter2 = TextSplitter(config2)
    chunks2 = splitter2.split_text(test_text)
    print(f"   分割结果: {len(chunks2)} 个块")
    for i, chunk in enumerate(chunks2[:3], 1):
        print(f"   块 {i}: {len(chunk)} 字符 - {chunk[:50]}...")
    print()
    
    # 测试3: 按句子分割
    print("3. 按句子分割（max_sentences_per_chunk=3）:")
    config3 = {
        "split_method": "sentence",
        "max_sentences_per_chunk": 3
    }
    splitter3 = TextSplitter(config3)
    chunks3 = splitter3.split_text(test_text)
    print(f"   分割结果: {len(chunks3)} 个块")
    for i, chunk in enumerate(chunks3[:3], 1):
        print(f"   块 {i}: {len(chunk)} 字符 - {chunk[:50]}...")
    print()
    
    # 测试4: 自定义过滤条件
    print("4. 自定义过滤条件（min_length=100, max_length=800）:")
    config4 = {
        "split_method": "character",
        "chunk_size": 600,
        "chunk_overlap": 150,
        "min_chunk_length": 100,
        "max_chunk_length": 800
    }
    splitter4 = TextSplitter(config4)
    chunks4 = splitter4.split_text(test_text)
    print(f"   分割结果: {len(chunks4)} 个块")
    for i, chunk in enumerate(chunks4[:3], 1):
        print(f"   块 {i}: {len(chunk)} 字符 - {chunk[:50]}...")
    print()
    
    # 测试5: 便捷函数
    print("5. 使用便捷函数 split_text():")
    chunks5 = split_text(test_text, {"split_method": "character", "chunk_size": 400})
    print(f"   分割结果: {len(chunks5)} 个块")
    for i, chunk in enumerate(chunks5[:2], 1):
        print(f"   块 {i}: {len(chunk)} 字符 - {chunk[:50]}...")
    print()

def test_environment_variables():
    """测试环境变量配置"""
    print("=== 环境变量配置测试 ===\n")
    
    # 设置环境变量
    os.environ["TEXT_SPLIT_METHOD"] = "character"
    os.environ["TEXT_CHUNK_SIZE"] = "300"
    os.environ["TEXT_CHUNK_OVERLAP"] = "50"
    
    from utils.config import get_text_chunk_config
    config = get_text_chunk_config()
    
    print("当前配置:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()
    
    # 使用环境变量配置进行测试
    test_text = "这是一个测试文本，用来验证环境变量配置是否正常工作。我们将使用字符分割方式，每个块300字符，重叠50字符。"
    
    splitter = TextSplitter(config)
    chunks = splitter.split_text(test_text)
    
    print(f"测试结果: {len(chunks)} 个块")
    for i, chunk in enumerate(chunks, 1):
        print(f"  块 {i}: {len(chunk)} 字符 - {chunk}")

if __name__ == "__main__":
    test_text_splitting()
    print("\n" + "="*50 + "\n")
    test_environment_variables() 