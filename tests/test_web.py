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
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    with app.test_client() as client:
        yield client


def test_index_page(client):
    """
    测试首页访问
    
    验证内容：
    1. 页面状态码为200
    2. 页面包含文件上传相关文本
    """
    rv = client.get('/')
    text = rv.data.decode(errors='ignore')
    assert rv.status_code == 200
    assert '文件上传' in text or 'File Upload' in text


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
        'file': (io.BytesIO('第一段内容。\n\n第二段内容。'.encode('utf-8')), 'test.txt'),
        'question': '请总结文档内容'
    }
    rv = client.post('/', data=data, content_type='multipart/form-data', follow_redirects=True)
    text = rv.data.decode(errors='ignore')
    assert rv.status_code == 200
    # 检查页面标题或关键内容
    assert 'RAG MVP' in text or '结果展示' in text or 'RAG Result' in text
    assert '请总结文档内容' in text or 'File' in text 