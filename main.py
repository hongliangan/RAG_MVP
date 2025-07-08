import config
from rag_core.data_loader import load_and_chunk_documents
from rag_core.embedding import embed_texts
from rag_core.vector_store import save_to_vector_store, retrieve_from_vector_store
from rag_core.reranker import rerank_documents
from rag_core.llm_interface import llm_interface


def setup_rag():
    """
    设置 RAG 系统，包括加载数据、生成嵌入并存入向量数据库。
    这个函数在程序启动时运行一次，用于初始化知识库。
    """
    print("--- 正在设置 RAG 系统 ---")
    
    # 1. 加载和分块文档
    chunks = load_and_chunk_documents()
    print(f"成功加载并分割成 {len(chunks)} 个文本块。")

    # 如果没有文档块，则跳过嵌入和存储步骤
    if not chunks:
        print("文档目录为空，跳过嵌入和存储步骤。")
        print("--- RAG 系统设置完毕 ---")
        return
    
    # 2. 生成嵌入
    print("正在为文本块生成嵌入...")
    embeddings = embed_texts(chunks, show_progress_bar=True)
    print("嵌入生成完毕。")
    
    # 3. ��储到向量数据库
    save_to_vector_store(chunks, embeddings)
    print("文本和嵌入已存入向量数据库。")
    print("--- RAG 系统设置完毕 ---")

def query_rag(query: str):
    """
    接收用户查询，通过 RAG 流程生成并返回答案。

    Args:
        query (str): 用户的查询问题。
    """
    print(f"\n--- 收到查询: {query} ---")
    
    # 1. 为查询生成嵌入
    print("为查询生成嵌入...")
    query_embedding = embed_texts([query])[0]
    
    # 2. 从向量数据库检索相关文档
    print("正在从向量数据库检索...")
    retrieved_results = retrieve_from_vector_store(query_embedding, n_results=config.RETRIEVAL_N_RESULTS)
    
    # 如果没有检索到文档，则直接返回提示信息
    if not retrieved_results or not retrieved_results.get('documents') or not retrieved_results['documents'][0]:
        print("知识库中没有相关信息，无法回答问题。")
        print("请先在 'documents' 目录中添加相关文档。")
        print("------------------")
        return

    retrieved_docs = retrieved_results['documents'][0]
    print(f"检索到 {len(retrieved_docs)} 个文档。")
    
    # 3. 重排序检索到的文档
    print("正在重排序检索结果...")
    reranked_docs = rerank_documents(query, retrieved_docs)
    top_docs = reranked_docs[:config.RERANKER_TOP_N]
    print(f"重排序后选出 Top {len(top_docs)} 个文档。")
    
    # 4. 构建上下文并生成 Prompt
    context = "\n\n".join([doc['document'] for doc in top_docs])
    prompt = config.PROMPT_TEMPLATE.format(context=context, query=query)
    
    # 5. 调用大语言模型生成答案
    print("正在调用大语言模型生成答案...")
    answer = llm_interface.generate(prompt)
    
    print("\n--- 生成的答案 ---")
    print(answer)
    print("------------------")

if __name__ == "__main__":
    # 初始化 RAG 系统
    setup_rag()
    
    # 运行一个示例查询
    sample_query = "哆啦A梦使用的3个秘密道具分别是什么？"
    query_rag(sample_query)
    
    # 进入交互式查询循环
    print("\n--- 进入交互式查询模式 (输入 'exit' 退出) ---")
    while True:
        user_query = input("请输入您的问题: ")
        if user_query.lower() == 'exit':
            break
        query_rag(user_query)