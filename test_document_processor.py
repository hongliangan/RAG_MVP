#!/usr/bin/env python3
"""
测试文档预处理器功能
"""
import os
import json
import tempfile
from pathlib import Path

# 添加项目路径
import sys

sys.path.insert(0, os.path.abspath("."))

from rag_core.document_processor import DocumentProcessor
from rag_core.data_loader import load_documents_with_metadata, get_supported_formats
from rag_core.knowledge_base import create_knowledge_base


def create_test_files():
    """创建测试文件"""
    test_files = {}

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()

    # 1. TXT文件
    txt_content = """
    这是一个测试文档。
    包含中文和English混合内容。
    
    第二段内容：
    - 列表项1
    - 列表项2
    - 列表项3
    
    第三段包含一些特殊字符：@#$%^&*()
    """
    txt_path = os.path.join(temp_dir, "test.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(txt_content)
    test_files["txt"] = txt_path

    # 2. Markdown文件
    md_content = """
    # 测试Markdown文档
    
    ## 章节1
    这是第一个章节的内容。
    
    ### 子章节
    - **粗体文本**
    - *斜体文本*
    - `代码片段`
    
    ## 章节2
    这是第二个章节的内容。
    
    ```python
    def hello_world():
        print("Hello, World!")
    ```
    """
    md_path = os.path.join(temp_dir, "test.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    test_files["md"] = md_path

    # 3. JSON文件
    json_data = {
        "title": "测试JSON文档",
        "author": "测试作者",
        "content": {
            "sections": [
                {"title": "第一部分", "text": "这是第一部分的内容"},
                {"title": "第二部分", "text": "这是第二部分的内容"},
            ]
        },
        "metadata": {"created": "2024-01-01", "tags": ["测试", "文档", "JSON"]},
    }
    json_path = os.path.join(temp_dir, "test.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    test_files["json"] = json_path

    # 4. CSV文件
    csv_content = """姓名,年龄,职业,城市
张三,25,工程师,北京
李四,30,设计师,上海
王五,28,产品经理,深圳
赵六,32,数据分析师,广州"""
    csv_path = os.path.join(temp_dir, "test.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(csv_content)
    test_files["csv"] = csv_path

    # 5. HTML文件
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>测试HTML文档</title>
        <style>
            body { font-family: Arial, sans-serif; }
        </style>
    </head>
    <body>
        <h1>测试HTML文档</h1>
        <p>这是一个测试段落。</p>
        <ul>
            <li>列表项1</li>
            <li>列表项2</li>
            <li>列表项3</li>
        </ul>
        <table>
            <tr><th>列1</th><th>列2</th></tr>
            <tr><td>数据1</td><td>数据2</td></tr>
        </table>
    </body>
    </html>
    """
    html_path = os.path.join(temp_dir, "test.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    test_files["html"] = html_path

    return test_files, temp_dir


def test_document_processor():
    """测试文档预处理器"""
    print("=== 测试文档预处理器 ===")

    # 创建测试文件
    test_files, temp_dir = create_test_files()

    # 初始化预处理器
    processor = DocumentProcessor()

    print(f"支持的文件格式: {processor.get_supported_formats()}")
    print()

    # 测试每种格式
    for format_name, file_path in test_files.items():
        print(f"--- 测试 {format_name.upper()} 格式 ---")

        try:
            # 获取文档信息
            info = processor.get_document_info(file_path)
            print(f"文档信息: {info}")

            # 处理文档
            result = processor.process_document(file_path)

            if result["success"]:
                print(f"处理成功！")
                print(f"格式: {result.get('format', 'unknown')}")
                print(f"处理时间: {result.get('processing_time', 0):.3f}秒")
                print(f"内容长度: {len(result['content'])} 字符")
                print(f"内容预览: {result['content'][:200]}...")

                # 显示元数据
                metadata = result.get("metadata", {})
                print(f"文件大小: {metadata.get('file_size', 0)} bytes")
                print(f"文件名: {metadata.get('file_name', 'unknown')}")
            else:
                print(f"处理失败: {result.get('error', '未知错误')}")

        except Exception as e:
            print(f"测试失败: {e}")

        print()


def test_data_loader():
    """测试数据加载器"""
    print("=== 测试数据加载器 ===")

    # 创建测试文件
    test_files, temp_dir = create_test_files()

    print(f"支持的文件格式: {get_supported_formats()}")
    print()

    # 测试每种格式
    for format_name, file_path in test_files.items():
        print(f"--- 测试 {format_name.upper()} 格式 ---")

        try:
            # 使用数据加载器
            result = load_documents_with_metadata(file_path)

            print(f"加载成功！")
            print(f"格式: {result.get('format', 'unknown')}")
            print(f"处理时间: {result.get('processing_time', 0):.3f}秒")
            print(f"文本块数量: {len(result['chunks'])}")

            # 显示前几个文本块
            for i, chunk in enumerate(result["chunks"][:3]):
                print(f"文本块 {i+1}: {chunk[:100]}...")

            # 显示元数据
            metadata = result.get("metadata", {})
            print(f"文件大小: {metadata.get('file_size', 0)} bytes")
            print(f"文件名: {metadata.get('file_name', 'unknown')}")

        except Exception as e:
            print(f"测试失败: {e}")

        print()


def test_knowledge_base():
    """测试知识库集成"""
    print("=== 测试知识库集成 ===")

    # 创建测试文件
    test_files, temp_dir = create_test_files()

    try:
        # 创建测试知识库
        kb = create_knowledge_base("test_processor")

        # 测试添加文档
        for format_name, file_path in test_files.items():
            print(f"--- 添加 {format_name.upper()} 文档到知识库 ---")

            try:
                result = kb.add_document(file_path)

                if result["success"]:
                    print(f"添加成功！")
                    print(f"文档ID: {result['document_id']}")
                    print(f"文件名: {result['filename']}")
                    print(f"文本块数量: {result['chunks_count']}")
                    print(f"向量数量: {result['vectors_count']}")
                    print(f"格式: {result.get('format', 'unknown')}")
                    print(f"处理时间: {result.get('processing_time', 0):.3f}秒")
                else:
                    print(f"添加失败: {result.get('error', '未知错误')}")

            except Exception as e:
                print(f"添加失败: {e}")

            print()

        # 测试搜索
        print("--- 测试搜索功能 ---")
        search_results = kb.search("测试", top_k=3)
        print(f"搜索到 {len(search_results)} 个结果")

        for i, result in enumerate(search_results):
            print(f"结果 {i+1}:")
            print(f"  内容: {result['content'][:100]}...")
            print(f"  分数: {result['score']:.3f}")
            print(f"  来源: {result['source']}")
            print(f"  文件名: {result.get('filename', '未知')}")

        # 清理测试知识库
        kb.clear()
        print("测试知识库已清理")

    except Exception as e:
        print(f"知识库测试失败: {e}")

    finally:
        # 清理临时文件
        import shutil

        shutil.rmtree(temp_dir)
        print(f"临时文件已清理: {temp_dir}")


def main():
    """主函数"""
    print("开始测试文档预处理器功能...")
    print("=" * 50)

    # 测试文档预处理器
    test_document_processor()

    print("=" * 50)

    # 测试数据加载器
    test_data_loader()

    print("=" * 50)

    # 测试知识库集成
    test_knowledge_base()

    print("=" * 50)
    print("所有测试完成！")


if __name__ == "__main__":
    main()
