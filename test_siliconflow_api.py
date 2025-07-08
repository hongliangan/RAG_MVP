#!/usr/bin/env python3
"""
测试硅基流动API连接和响应
"""
import requests
import json
import os

def test_siliconflow_api():
    """测试硅基流动API"""
    
    # 从环境变量或配置文件获取API信息
    api_key = os.getenv("SILICONFLOW_API_KEY", "")
    model_name = os.getenv("SILICONFLOW_MODEL_NAME", "Tongyi-Zhiwen/QwenLong-L1-32B")
    api_url = os.getenv("SILICONFLOW_API_URL", "https://api.siliconflow.cn/v1/chat/completions")
    
    if not api_key:
        print("❌ 错误: 未设置 SILICONFLOW_API_KEY 环境变量")
        print("请设置环境变量: export SILICONFLOW_API_KEY='your-api-key'")
        return

    print(f"=== 硅基流动API测试 ===")
    print(f"API URL: {api_url}")
    print(f"模型: {model_name}")
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print("-" * 50)
    
    # 测试连接
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "你好，请简单回复'测试成功'"}
        ],
        "temperature": 0.7,
        "max_tokens": 50,
        "stream": False
    }
    
    try:
        print("正在发送请求...")
        # 增加超时时间到120秒
        response = requests.post(api_url, headers=headers, json=payload, timeout=120)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应内容: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            if "choices" in data and data["choices"]:
                content = data["choices"][0]["message"]["content"]
                print(f"\n✅ API测试成功！回复: {content}")
            else:
                print(f"\n❌ API响应格式异常: {data}")
        else:
            print(f"❌ API请求失败: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时 (120秒)")
        print("建议检查网络连接或API服务状态")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        print(f"错误类型: {type(e).__name__}")

if __name__ == "__main__":
    test_siliconflow_api() 