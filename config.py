# ... existing code ...
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# --- 文件路径配置 ---
# 获取当前文件所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 设置文档目录
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")

# --- Gemini API 配置 ---
# 从环境变量中获取 Gemini API 密钥
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- 硅基流动 API 配置 ---
# 从环境变量中获取硅基流动 API 密钥
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
# 硅基流动服务的 API 端点
SILICONFLOW_API_BASE = "https://api.siliconflow.cn/v1"

# --- LLM 服务选择 ---
# 指定当前使用的 LLM 服务 ('gemini' 或 'siliconflow')
LLM_PROVIDER = "gemini"

# --- 模型名称配置 ---
# 1. 嵌入模型（Embedding Model）：用于将文本转换为向量
EMBEDDING_MODEL_NAME = "shibing624/text2vec-base-chinese"

# 2. 重排序器模型（Reranker Model）：用于对检索结果进行优化排序
RERANKER_MODEL_NAME = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

# 3. ���语言模型（LLM）：用于根据上下文生成最终答案
# 根据选择的服务提供商，使用不同的模型名称
if LLM_PROVIDER == 'gemini':
    LLM_MODEL_NAME = "gemini-1.5-flash"
elif LLM_PROVIDER == 'siliconflow':
    # 注意：这里需要替换为硅基流动提供的兼容模型名称，例如 "deepseek-ai/deepseek-v2-chat"
    LLM_MODEL_NAME = "deepseek-ai/deepseek-v2-chat"

# --- RAG 流程参数 ---
# 1. 向量数据库检索时返回的文档数量
RETRIEVAL_N_RESULTS = 10

# 2. 重排序后选出的最相关文档数量
RERANKER_TOP_N = 3

# --- Prompt 模板 ---
# 用于指导大语言模型（LLM）生成答案的模板
PROMPT_TEMPLATE = """
你是一个知识渊博的问答机器人。
请根据下面提供的“上下文信息”，用中文简洁、准确地回答用户提出的“问题”。

[上下文信息]
{context}

[问题]
{query}

请开始回答：
"""
