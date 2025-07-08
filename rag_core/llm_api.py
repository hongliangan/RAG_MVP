"""
llm_api.py
LLM API调用模块。用于封装与大语言模型（LLM）API的交互。
后续可在此实现如OpenAI、Qwen、GLM等API的调用。
"""
import requests
from utils.config import get_llm_config

def call_llm_api(prompt, model=None, api_key=None, api_url=None, stream=False, **kwargs):
    """
    调用LLM API，返回生成结果。
    :param prompt: 输入提示词
    :param model: 使用的LLM模型名称
    :param api_key: LLM服务API Key
    :param api_url: LLM服务API地址
    :param stream: 是否流式输出
    :param kwargs: 其他API参数
    :return: LLM生成的文本或生成器
    """
    # 获取当前LLM服务配置
    config = get_llm_config()
    api_key = api_key or config.get("api_key")
    model = model or config.get("model_name")  # 使用配置中的模型名，不设置默认值
    api_url = api_url or config.get("api_url")
    temperature = kwargs.get("temperature", 0.7)
    max_tokens = kwargs.get("max_tokens", 512)
    try:
        try:
            # 优先使用openai官方库，兼容OpenAI/Siliconflow等API
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=api_url)
            messages = [
                {"role": "user", "content": prompt}
            ]
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            if stream:
                # 流式输出，返回生成器
                def stream_gen():
                    for chunk in response:
                        if not chunk.choices:
                            continue
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "content") and delta.content:
                            yield delta.content
                        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                            yield delta.reasoning_content
                return stream_gen()
            else:
                # 非流式直接返回内容
                if response.choices and hasattr(response.choices[0].message, "content"):
                    return response.choices[0].message.content
                return str(response)
        except ImportError:
            # fallback: 未安装openai库时，直接用requests请求API
            if not api_url:
                return "[LLM API 调用异常]: api_url未设置，无法请求API。"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                # fallback分支强制非流式
                "stream": False
            }
            # 打印调试信息，便于排查API调用问题
            print("[llm_api] 请求URL:", api_url)
            print("[llm_api] 请求headers:", headers)
            print("[llm_api] 请求payload:", payload)
            resp = requests.post(api_url, headers=headers, json=payload, timeout=120)
            print("[llm_api] 响应状态码:", resp.status_code)
            print("[llm_api] 响应内容:", resp.text)
            resp.raise_for_status()
            data = resp.json()
            # 兼容OpenAI和硅基流动等API格式
            if "choices" in data and data["choices"]:
                return data["choices"][0]["message"]["content"]
            elif "output" in data:
                return data["output"]
            else:
                return str(data)
    except Exception as e:
        # 捕获所有异常，返回异常信息
        return f"[LLM API 调用异常]: {e}" 