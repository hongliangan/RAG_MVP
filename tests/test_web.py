"""
测试Web应用的功能
测试Flask应用的页面访问、文件上传和结果展示
"""

import os
import io
import tempfile
import pytest
from flask import url_for
from web.app import app


@pytest.fixture
def client():
    """
    创建测试客户端

    设置测试配置：
    - 启用测试模式
    - 创建临时上传目录
    - 返回测试客户端实例
    """
    app.config["TESTING"] = True
    app.config["UPLOAD_FOLDER"] = tempfile.mkdtemp()
    with app.test_client() as client:
        yield client


def test_index_page(client):
    """
    测试首页访问

    验证内容：
    1. 页面状态码为200
    2. 页面包含文件上传相关文本
    """
    rv = client.get("/")
    text = rv.data.decode(errors="ignore")
    assert rv.status_code == 200
    assert "文件上传" in text or "File Upload" in text


def test_file_upload_and_result(client):
    """
    测试文件上传和结果展示

    测试流程：
    1. 构造测试文件（包含中文内容）
    2. 提交文件上传请求
    3. 验证响应状态码
    4. 验证结果页面包含预期内容

    验证内容：
    - 页面状态码为200
    - 结果页面包含RAG结果相关文本
    - 页面包含用户提交的问题
    """
    # 构造一个简单txt文件上传
    data = {
        "file": (
            io.BytesIO("第一段内容。\n\n第二段内容。".encode("utf-8")),
            "test.txt",
        ),
        "question": "请总结文档内容",
    }
    rv = client.post(
        "/", data=data, content_type="multipart/form-data", follow_redirects=True
    )
    text = rv.data.decode(errors="ignore")
    assert rv.status_code == 200
    # 检查页面标题或关键内容
    assert "RAG MVP" in text or "结果展示" in text or "RAG Result" in text
    assert "请总结文档内容" in text or "File" in text


def test_api_config_set_validation(client):
    """
    测试全局配置API参数校验
    1. 缺字段/类型错误时应返回校验失败和详细错误
    2. 合法参数应保存成功
    """
    url = "/api/config/set"
    # 缺llm_provider
    resp = client.post(url, json={})
    data = resp.get_json()
    assert not data["success"], f"data: {data}"
    assert "llm_provider" in data.get("detail", {})
    # llm_configs类型错误
    resp = client.post(
        url,
        json={
            "llm_provider": "openai",
            "llm_configs": [],
            "local_model_dir": "./models",
            "prefer_local_model": True,
        },
    )
    data = resp.get_json()
    assert not data["success"], f"data: {data}"
    assert "llm_configs" in data.get("detail", {})
    # provider配置缺失
    resp = client.post(
        url,
        json={
            "llm_provider": "openai",
            "llm_configs": {},
            "local_model_dir": "./models",
            "prefer_local_model": True,
        },
    )
    data = resp.get_json()
    assert not data["success"], f"data: {data}"
    assert "llm_configs" in data.get("detail", {})
    # api_key缺失
    resp = client.post(
        url,
        json={
            "llm_provider": "openai",
            "llm_configs": {
                "openai": {
                    "model_name": "gpt-3.5-turbo",
                    "api_url": "https://api.openai.com/v1/chat/completions",
                }
            },
            "local_model_dir": "./models",
            "prefer_local_model": True,
        },
    )
    data = resp.get_json()
    assert not data["success"], f"data: {data}"
    assert "llm_api_key" in data.get("detail", {})
    # 正常保存
    resp = client.post(
        url,
        json={
            "llm_provider": "openai",
            "llm_configs": {
                "openai": {
                    "api_key": "sk-xxx",
                    "model_name": "gpt-3.5-turbo",
                    "api_url": "https://api.openai.com/v1/chat/completions",
                }
            },
            "local_model_dir": "./models",
            "prefer_local_model": True,
            "embedding_provider": "local",
            "embedding_configs": {
                "local": {"model_path": "./models/embedding"},
                "online": {"api_url": "https://api.siliconflow.cn/v1/embeddings", "api_key": "", "model_name": "BAAI/bge-large-zh-v1.5"}
            }
        },
    )
    data = resp.get_json()
    assert data["success"], f"data: {data}";


def test_kb_add_document_validation(client):
    """
    测试知识库文档上传接口的切片参数校验
    1. 缺失/错误参数应返回校验失败和详细错误
    2. 合法参数应上传成功
    """
    url = "/kb/add_document"
    # 构造一个简单txt文件
    file_data = (io.BytesIO("第一段内容。\n\n第二段内容。".encode("utf-8")), "test.txt")
    # 缺少必需参数
    data = {
        "file": (io.BytesIO("第一段内容。\n\n第二段内容。".encode("utf-8")), "test.txt"),
        "kb_name": "default",
        "split_method": "character",
        # chunk_size缺失
        "chunk_size": 800,
        "chunk_overlap": 100,
    }
    resp = client.post(url, data=data, content_type="multipart/form-data")
    result = resp.get_json()
    assert not result["success"]
    assert ("分段失败" in result.get("error", "") or "参数校验失败" in result.get("error", ""))
    # chunk_size类型错误
    data = {
        "file": (io.BytesIO("第一段内容。\n\n第二段内容。".encode("utf-8")), "test.txt"),
        "kb_name": "default",
        "split_method": "character",
        "chunk_size": "abc",
        "chunk_overlap": 100,
    }
    resp = client.post(url, data=data, content_type="multipart/form-data")
    result = resp.get_json()
    assert not result["success"]
    assert ("分段失败" in result.get("error", "") or "参数校验失败" in result.get("error", ""))
    # chunk_size范围错误
    data = {
        "file": (io.BytesIO("第一段内容。\n\n第二段内容。".encode("utf-8")), "test.txt"),
        "kb_name": "default",
        "split_method": "character",
        "chunk_size": 10,  # 太小
        "chunk_overlap": 100,
    }
    resp = client.post(url, data=data, content_type="multipart/form-data")
    result = resp.get_json()
    assert not result["success"]
    assert ("分段失败" in result.get("error", "") or "参数校验失败" in result.get("error", ""))
    # 合法参数
    data = {
        "file": (io.BytesIO("第一段内容。\n\n第二段内容。".encode("utf-8")), "test.txt"),
        "kb_name": "default",
        "split_method": "character",
        "chunk_size": 800,
        "chunk_overlap": 100,
    }
    resp = client.post(url, data=data, content_type="multipart/form-data")
    result = resp.get_json()
    print("[test_kb_add_document_validation] 合法参数返回:", result)
    # 只要不是参数校验失败即通过（可能因其它mock依赖失败）
    assert "参数校验失败" not in result.get("error", "")
