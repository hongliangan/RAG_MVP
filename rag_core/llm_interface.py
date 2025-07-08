# -*- coding: utf-8 -*-
"""
本模块负责与大语言模型（LLM）进行交互。

它实现了一个 LLMInterface 类，该类根据配置选择并初始化相应的 LLM 客户端（如 Google Gemini 或 SiliconFlow）。
这种设计使得在不同的 LLM 服务之间切换变得简单，只需更改配置文件即可。
"""

from typing import List
import google.generativeai as genai
from openai import OpenAI
import config

class LLMInterface:
    """
    一个与大语言模型交互的接口类。

    根据配置文件中的 `LLM_PROVIDER` 来决定使用哪个 LLM 服务。
    """
    def __init__(self):
        """
        初始化 LLMInterface。

        根据 config.LLM_PROVIDER 的值，配置并创建相应的 LLM 客户端。
        如果配置了 'gemini'，则初始化 Google Gemini 客户端。
        如果配置了 'siliconflow'，则初始化一个兼容 OpenAI 的客户端，指向硅基流动的 API 端点。
        如果提供了不支持的 provider，则会抛出 ValueError。
        """
        self.provider = config.LLM_PROVIDER
        if self.provider == 'gemini':
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.client = genai.GenerativeModel(config.LLM_MODEL_NAME)
        elif self.provider == 'siliconflow':
            self.client = OpenAI(
                api_key=config.SILICONFLOW_API_KEY,
                base_url=config.SILICONFLOW_API_BASE,
            )
        else:
            raise ValueError(f"不支持的 LLM 提供商: {self.provider}")

    def generate(self, prompt: str) -> str:
        """
        根据构建好的 prompt 生成答案。

        Args:
            prompt (str): 包含上下文和问题的完整 prompt。

        Returns:
            str: 由 LLM 生成的最终答案。
        """
        print(f"--- Prompt 发送至 {self.provider} ---\n{prompt}\n---------------------------------")

        # 根据不同的 provider，调用相应的 API
        if self.provider == 'gemini':
            response = self.client.generate_content(prompt)
            return response.text
        elif self.provider == 'siliconflow':
            # 硅基流动使用与 OpenAI 兼容的聊天接口
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=config.LLM_MODEL_NAME,
            )
            return chat_completion.choices[0].message.content

        return "错误：未能生成回答。"

# 创建一个全局的 LLM 接口实例
llm_interface = LLMInterface()