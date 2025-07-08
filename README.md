# RAG MVP 项目

本项目基于"使用Python构建RAG系统"的原理，采用MVP（最小可行性产品）模式实现一个简洁的RAG（检索增强生成）系统。

## 🆕 最新功能

### 多轮对话系统 (v1.5)
- **新增**: 完整的多轮对话管理功能，支持会话持久化和上下文传递
- **功能**: 对话创建、消息管理、历史记录、上下文拼接、对话导出
- **特性**: 支持多知识库对话、智能上下文管理、JSON/TXT格式导出
- **界面**: 独立的对话页面，支持实时对话、历史对话管理、知识库切换

### 本地向量数据库 (v1.4)
- **新增**: 本地向量存储引擎，支持SQLite + FAISS持久化存储
- **功能**: 知识库管理、文档批量处理、向量检索和相似度搜索
- **特性**: 支持多知识库、文档版本管理、增量更新
- **界面**: Web端知识库管理界面，支持文档上传、搜索、删除等操作

## 🐛 最近修复

### 类型转换错误修复 (2025-07-08)
- **问题**: Web界面传递的字符串类型参数导致 `'<' not supported between instances of 'int' and 'str'` 错误
- **原因**: 文本切片器期望整数类型参数，但Web界面传递的是字符串类型
- **解决方案**: 在 `TextSplitter` 类中添加 `_normalize_config()` 方法，自动转换参数类型
- **影响**: 修复了Web界面的文档加载功能，现在可以正常处理所有文件格式

### UI界面优化 (2025-07-08)
- **改进**: 移除了结果页面中难看的进度条
- **优化**: 将"RAG处理进度"改为"处理结果统计"，提供更清晰的信息展示
- **效果**: 界面更加简洁美观，用户体验得到提升

## 📚 文档

- [参数使用指南](PARAMETER_GUIDE.md) - 详细的参数配置说明和调优建议
- [核心模块说明](#核心模块) - 各模块功能和使用方法

## 🚀 快速开始

## 目录结构

```
rag_mvp/
│
├── README.md                # 项目说明（本文件）
├── requirements.txt         # 依赖包列表
├── main.py                  # 命令行入口，串联RAG流程
│
├── data/
│   └── example.txt          # 示例文档（可替换为你自己的文件）
│
├── rag_core/
│   ├── __init__.py
│   ├── data_loader.py       # 文档加载与预处理（支持txt、docx、pdf）
│   ├── embedding.py         # 文本向量化（支持本地模型和云模型）
│   ├── retriever.py         # 检索模块（基于余弦相似度，支持多种可调节参数）
│   ├── generator.py         # 生成模块（拼接prompt并调用LLM）
│   ├── llm_api.py           # LLM API调用模块（支持硅基流动等）
│   ├── text_splitter.py     # 增强版文本切片器
│   ├── vector_store.py      # 本地向量存储引擎（SQLite + FAISS）
│   ├── knowledge_base.py    # 知识库管理器
│   └── conversation_manager.py # 多轮对话管理器
│
├── utils/
│   ├── __init__.py
│   └── config.py            # 多LLM服务配置管理（支持多服务切换与独立参数）
│
├── web/
│   ├── __init__.py
│   ├── app.py               # Flask Web应用
│   ├── templates/
│   │   ├── index.html       # 主页面模板（支持检索参数配置）
│   │   ├── result.html      # 结果页面模板（显示检索配置信息）
│   │   ├── knowledge_base.html # 知识库管理页面
│   │   └── chat.html        # 多轮对话页面
│   └── static/
│       ├── style.css        # 样式文件
│       └── script.js        # 交互脚本
│
├── models/                  # 本地模型存储目录
│   └── sentence-transformers/
│
├── knowledge_base/          # 知识库存储目录
│   ├── documents/           # 文档存储
│   └── vectors/             # 向量存储
├── conversations/           # 对话存储目录
│
└── tests/
    ├── __init__.py
    ├── test_data_loader.py  # 文档加载测试
    ├── test_embedding.py    # 向量化测试
    ├── test_retriever.py    # 检索测试
    ├── test_generator.py    # 生成测试
    ├── test_llm_api.py      # LLM API测试
    ├── test_config.py       # 配置测试
    └── test_web.py          # Web应用测试
```

## 各部分说明

- **main.py**：命令行入口，提供完整的RAG流程演示。
- **rag_core/**：核心功能模块，分为数据加载、向量化、检索、生成、LLM API调用五部分，便于扩展和维护。
    - **data_loader.py**：支持txt、docx、pdf格式文档加载，自动处理中文内容。
    - **embedding.py**：支持本地sentence-transformers模型和云模型，自动fallback机制。
    - **retriever.py**：基于余弦相似度的文档检索，支持多种可调节参数：
        - **相似度阈值**：过滤低于阈值的文档片段
        - **去重策略**：去除重复或高度相似的文档片段
        - **检索策略**：支持余弦相似度、点积相似度、欧氏距离
        - **权重调整**：支持文档长度、位置、关键词权重
        - **上下文窗口**：包含相邻文档片段作为上下文
    - **generator.py**：智能拼接prompt并调用LLM生成答案。
    - **llm_api.py**：封装与大语言模型（LLM）API的交互，支持硅基流动等API。
    - **text_splitter.py**：增强版文本切片器，支持多种切片方式和可配置参数。
    - **vector_store.py**：本地向量存储引擎，支持SQLite + FAISS持久化存储，提供向量检索和相似度搜索功能。
    - **knowledge_base.py**：知识库管理器，整合文档处理、向量化和存储功能，支持多知识库管理。
    - **conversation_manager.py**：多轮对话管理器，支持会话创建、消息管理、上下文拼接、历史记录和对话导出。
- **utils/**：工具类和配置管理。
    - **config.py**：支持多LLM服务配置（如硅基流动、OpenAI等），可通过环境变量`LLM_PROVIDER`选择服务，参数（API Key、模型名、URL）独立配置，便于灵活扩展。新增检索参数配置支持。
- **web/**：Web界面模块。
    - **app.py**：Flask应用，提供文件上传和问答界面，支持检索参数配置。
    - **templates/**：HTML模板，支持中文界面和响应式设计，新增检索参数配置界面和知识库管理界面。
    - **static/**：静态资源，包含样式和交互脚本。
- **data/**：存放本地测试用的文档数据。
- **models/**：本地模型存储目录，自动下载和管理。
- **tests/**：各模块的单元测试文件，每个功能模块都配套一个测试文件，便于开发和调试。
- **requirements.txt**：列出所有依赖，便于环境搭建。
- **README.md**：项目说明和使用方法。

## 安装和运行

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

> **注意**：如需支持Excel（.xlsx/.xls）等表格文件处理，需确保已安装 `pandas`、`openpyxl`、`xlrd`。

### 2. 命令行使用

```bash
# 问答模式
python main.py --mode qa --file data/example.txt --question "请总结文档内容"

# 知识库模式
python main.py --mode kb --action add --kb-name my_kb --document data/example.txt
python main.py --mode kb --action search --kb-name my_kb --query "什么是RAG" --top-k 5
python main.py --mode kb --action list --kb-name my_kb
python main.py --mode kb --action stats --kb-name my_kb
python main.py --mode kb --action delete --kb-name my_kb --doc-id 1
python main.py --mode kb --action clear --kb-name my_kb

# 查看帮助
python main.py --help
```

### 3. Web界面使用

```bash
# 启动Web服务
cd web
python app.py

# 访问 http://localhost:5000
# 知识库管理: http://localhost:5000/knowledge_base
# 智能对话: http://localhost:5000/chat
```

## 多轮对话功能

### 功能特性

- **会话管理**: 支持创建、加载、删除对话会话
- **上下文传递**: 智能管理对话上下文，支持多轮对话连贯性
- **历史记录**: 完整的对话历史记录和持久化存储
- **多知识库支持**: 可以为不同知识库创建独立的对话
- **智能检索**: 结合知识库检索和对话上下文生成回答
- **对话导出**: 支持JSON和TXT格式的对话导出
- **Web界面**: 提供现代化的对话界面，支持实时对话

### 对话操作

```python
from rag_core.conversation_manager import get_conversation_manager

# 获取对话管理器
conv_manager = get_conversation_manager()

# 创建新对话
conversation = conv_manager.create_conversation("my_kb")

# 添加消息
conv_manager.add_message(conversation.session_id, "user", "你好")
conv_manager.add_message(conversation.session_id, "assistant", "你好！有什么可以帮助你的吗？")

# 获取对话上下文
context = conv_manager.get_conversation_context(conversation.session_id)

# 列出对话
conversations = conv_manager.list_conversations("my_kb")

# 导出对话
export_content = conv_manager.export_conversation(conversation.session_id, "txt")

# 删除对话
conv_manager.delete_conversation(conversation.session_id)
```

### Web界面使用

1. 访问 `http://localhost:5000/chat` 进入对话页面
2. 选择知识库或创建新对话
3. 在输入框中输入问题，按Enter或点击发送
4. 系统会结合知识库内容和对话上下文生成回答
5. 可以查看历史对话、导出对话记录

## 知识库功能

### 功能特性

- **多知识库支持**: 可以创建和管理多个独立的知识库
- **文档管理**: 支持添加、删除、查看文档列表
- **向量存储**: 使用SQLite + FAISS进行持久化向量存储
- **智能搜索**: 基于向量相似度的语义搜索
- **Web界面**: 提供友好的Web管理界面
- **命令行工具**: 支持命令行操作知识库

### 知识库操作

```bash
# 创建知识库（自动创建）
kb = create_knowledge_base("my_kb")

# 添加文档
result = kb.add_document("path/to/document.txt")

# 搜索文档
results = kb.search("查询内容", top_k=5)

# 列出所有文档
documents = kb.list_documents()

# 获取统计信息
stats = kb.get_stats()

# 删除文档
kb.delete_document(doc_id)

# 清空知识库
kb.clear()
```

### 存储结构

```
knowledge_base/
├── documents/           # 文档存储
│   └── {kb_name}/      # 按知识库名称分类
└── vectors/            # 向量存储
    └── {kb_name}/      # 按知识库名称分类
        ├── vector_store.db  # SQLite数据库
        ├── embeddings.npy   # 向量数据
        └── faiss_index.pkl  # FAISS索引
```

## 检索参数配置

### 环境变量配置

```bash
# 检索参数配置
export RETRIEVAL_TOP_K=3                    # 返回最相关的片段数
export RETRIEVAL_SIMILARITY_THRESHOLD=0.0   # 相似度阈值
export RETRIEVAL_DEDUPLICATION=true         # 是否去重
export RETRIEVAL_STRATEGY=cosine            # 检索策略：cosine, dot_product, euclidean
export RETRIEVAL_CONTEXT_WINDOW=0           # 上下文窗口大小

# 权重配置
export RETRIEVAL_LENGTH_WEIGHT=             # 长度权重：prefer_long, prefer_short
export RETRIEVAL_POSITION_WEIGHT=           # 位置权重：prefer_early, prefer_late
export RETRIEVAL_KEYWORD_WEIGHT=            # 关键词权重（逗号分隔）
```

### 检索参数说明

1. **top_k**：返回最相关的片段数量，默认3
2. **similarity_threshold**：相似度阈值，过滤低于此值的文档片段，默认0.0
3. **deduplication**：是否去除重复或高度相似的文档片段，默认true
4. **retrieval_strategy**：检索策略
   - `cosine`：余弦相似度（默认）
   - `dot_product`：点积相似度
   - `euclidean`：欧氏距离
5. **context_window**：上下文窗口大小，包含相邻文档片段，默认0
6. **weight_config**：权重配置
   - `length_weight`：文档长度权重
     - `prefer_long`：偏好长文档
     - `prefer_short`：偏好短文档
   - `position_weight`：文档位置权重
     - `prefer_early`：偏好早期文档
     - `prefer_late`：偏好后期文档
   - `keyword_weight`：关键词权重列表，包含这些关键词的文档片段会获得更高权重

## 测试策略

- 每个核心模块都应有独立的测试文件，统一放在`tests/`目录下，命名如`test_xxx.py`。
- 推荐使用pytest进行测试。
- 每次新增/修改模块时，同步完善对应的测试文件。

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定模块测试
pytest tests/test_embedding.py

# 运行测试并显示详细输出
pytest -v tests/
```

## 主流程示例

```python
from rag_core.data_loader import load_documents
from rag_core.embedding import embed_documents
from rag_core.retriever import retrieve
from rag_core.generator import generate_answer
from utils.config import get_retrieval_params

# 1. 加载文档
docs = load_documents("data/example.txt")
# 2. 文档向量化
doc_vectors = embed_documents(docs)
# 3. 获取检索参数
retrieval_params = get_retrieval_params()
# 4. 检索相关文档
query = "你的问题"
relevant_docs = retrieve(query, doc_vectors, docs, **retrieval_params)
# 5. 生成答案
answer = generate_answer(query, relevant_docs)
print(answer)
```

## 特性说明

### 文档支持
- **TXT文件**：支持UTF-8编码，自动段落分割
- **DOCX文件**：支持Word文档，提取段落内容
- **PDF文件**：支持中文PDF，自动字体检测
- **Markdown/HTML/JSON/CSV/Excel**：支持多种结构化和半结构化文档，表格内容自动提取（需安装 pandas、openpyxl、xlrd）

### 向量化支持
- **本地模型**：使用sentence-transformers，自动下载和缓存
- **云模型**：支持在线API调用，断网时自动fallback
- **多语言**：支持中英文混合内容

### 检索功能增强
- **多种相似度计算**：支持余弦相似度、点积相似度、欧氏距离
- **相似度阈值过滤**：可设置阈值过滤低相似度文档
- **去重策略**：自动去除重复或高度相似的文档片段
- **权重调整**：支持文档长度、位置、关键词权重调整
- **上下文窗口**：可包含相邻文档片段作为上下文

### LLM API支持
- **硅基流动**：兼容OpenAI格式的API
- **可扩展**：支持添加其他LLM服务商
- **参数配置**：支持API Key、模型名、URL等参数

### Web界面特性
- **文件上传**：支持拖拽上传和点击选择
- **参数配置**：可自定义LLM API参数和检索参数
- **进度展示**：实时显示处理进度
- **结果展示**：分区域展示各处理步骤结果和配置信息

## 配置说明

### 环境变量配置

```bash
# 选择LLM服务商
export LLM_PROVIDER=siliconflow  # 或 openai

# 配置API参数
export SILICONFLOW_API_KEY=your_api_key
export SILICONFLOW_MODEL_NAME=your_model_name
export SILICONFLOW_API_URL=your_api_url

# 检索参数配置
export RETRIEVAL_TOP_K=3
export RETRIEVAL_SIMILARITY_THRESHOLD=0.0
export RETRIEVAL_DEDUPLICATION=true
export RETRIEVAL_STRATEGY=cosine
export RETRIEVAL_CONTEXT_WINDOW=0
export RETRIEVAL_LENGTH_WEIGHT=prefer_long
export RETRIEVAL_POSITION_WEIGHT=prefer_early
export RETRIEVAL_KEYWORD_WEIGHT=重要,关键,核心
```

### 本地模型配置

```python
# 在embedding.py中配置本地模型路径
MODEL_PATH = "models/sentence-transformers/all-MiniLM-L6-v2"
```

## 开发说明

- 本项目不包含原项目的测试文件，后续可用你自己的本地文件进行测试。
- 新增文件时请先查阅本README，确保与项目架构设计一致，并及时补充相关说明。
- 所有核心模块都有详细的中文注释，便于维护和扩展。
- 遵循统一的代码风格和命名规范。
- 检索模块新增了多种可调节参数，支持更精细的检索控制。

## 分支策略

### 分支说明
- **main**: 主分支，用于发布稳定版本
- **develop**: 开发分支，用于日常开发和功能集成
- **feature/***: 功能分支，用于开发新功能
- **hotfix/***: 热修复分支，用于紧急修复

### 开发流程
1. 从 `develop` 分支创建功能分支：`git checkout -b feature/新功能名`
2. 在功能分支上开发完成后，合并回 `develop` 分支
3. 当 `develop` 分支功能稳定后，合并到 `main` 分支发布新版本
4. 紧急修复时从 `main` 分支创建 `hotfix/*` 分支

### 当前状态
- **稳定版本**: v1.3 (main分支)
- **开发版本**: develop分支 (下一个版本开发中)

## 版本信息

**版本**: 1.3  
**更新内容**: 
- 修复类型转换错误，解决Web界面参数传递问题
- 移除难看的进度条，优化用户界面
- 完善参数配置，添加合理的默认值和范围提示
- 新增详细的参数使用指南文档
- 清理测试数据和缓存文件，提升代码质量
