rag_project/
├── main.py             # 程序入口，处理命令行参数，协调整个 RAG 流程
├── config.py           # 配置文件，用于管理 API 密钥、模型名称、文件路径等
├── rag_core/
│   ├── __init__.py
│   ├── data_loader.py    # 负责加载和预处理（如分块）文档
│   ├── embedding.py      # 负责将文本转换为向量嵌入
│   ├── vector_store.py   # 负责向量的存储、索引和检索
│   ├── reranker.py       # （可选，但建议保留）负责对检索结果进行重排
│   └── llm_interface.py  # 负责与大语言模型（如 Gemini）交互
├── documents/            # 存放原始知识文档（如 doc.md）
├── .env                  # 存储环境变量（如 API 密钥）
└── pyproject.toml        # 项目依赖管理

### 各模块核心职责 (MVP)
1. data_loader.py :
   
   - 核心功能 : 实现一个 DataLoader 类，其主要方法是 load_and_split(file_path) 。
   - 实现 : 将您在 Notebook 中的 split_into_chunks 函数逻辑封装到这个类中。初期可以只支持 Markdown 或纯文本文件。
2. embedding.py :
   
   - 核心功能 : 实现一个 EmbeddingModel 类，提供 embed_documents(texts) 和 embed_query(text) 方法。
   - 实现 : 封装 sentence-transformers 模型的加载和编码逻辑。这样，如果未来想更换嵌入模型，只需修改这个文件。
3. vector_store.py :
   
   - 核心功能 : 实现一个 VectorStore 类，提供 add_documents(texts, embeddings) 和 search(query_embedding, top_k) 方法。
   - 实现 : 封装 chromadb 的交互逻辑。初期可以使用 EphemeralClient ，未来可以轻松切换到持久化存储的 HttpClient 。
4. reranker.py :
   
   - 核心功能 : 实现一个 Reranker 类，提供 rerank(query, documents, top_k) 方法。
   - 实现 : 封装 CrossEncoder 的加载和预测逻辑。重排可以显著提升检索质量，是 MVP 中非常有价值的一环。
5. llm_interface.py :
   
   - 核心功能 : 实现一个 LLMInterface 类，提供 generate_answer(query, context_documents) 方法。
   - 实现 : 封装构建 prompt 和调用 Google Gemini API 的逻辑。将 prompt 模板放在 config.py 中，方便调整。
6. config.py :
   
   - 核心功能 : 集中管理所有配置项，如模型名称 ( shibing624/text2vec-base-chinese , cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 , gemini-1.5-flash )、文件路径、 top_k 参数等。
7. main.py :
   
   - 核心功能 : 作为程序的总指挥。它会：
     1. 加载配置和环境变量。
     2. 初始化 DataLoader , EmbeddingModel , VectorStore , Reranker , LLMInterface 等所有核心组件。
     3. 执行一次性的文档处理流程：加载文档 -> 嵌入 -> 存入向量数据库。
     4. 进入一个循环，等待用户输入查询。
     5. 对于每个查询，依次调用： embed_query -> search -> rerank -> generate_answer 。
     6. 打印最终答案。