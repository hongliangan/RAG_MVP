# PandaWiki 对接蓝图和同步逻辑
import requests
import os
import json
from flask import Blueprint, request, jsonify
from rag_core.knowledge_base import KnowledgeBase

panda_bp = Blueprint('panda', __name__)

PANDAWIKI_API = "http://pandawiki_host:2443/api"
LOCAL_KB_ROOT = "knowledge_base/documents/panda_sync"

@panda_bp.route('/api/ai/answer', methods=['POST'])
def panda_ai_answer():
    """
    兼容 PandaWiki 的 AI 问答接口
    POST: { "question": "...", "kb_id": "..." }
    返回: { "success": True, "answer": "..." }
    """
    data = request.get_json()
    question = data.get("question")
    kb_id = data.get("kb_id")
    answer = your_rag_answer_func(question, kb_id)
    return jsonify({"success": True, "answer": answer})


def sync_pandawiki_kb(log=None):
    """
    PandaWiki 知识库内容同步主流程
    - 支持 log 回调，实时记录同步进度
    - 拉取 PandaWiki 所有知识库及文档，存入本地并自动入库
    :param log: 可选日志回调函数
    """
    os.makedirs(LOCAL_KB_ROOT, exist_ok=True)
    if log: log("开始同步 PandaWiki 知识库...")
    resp = requests.get(f"{PANDAWIKI_API}/kb/list")
    kb_list = resp.json().get("data", [])
    for kb in kb_list:
        if log: log(f"同步知识库 {kb['id']} - {kb.get('name','')}")
        docs = requests.get(f"{PANDAWIKI_API}/kb/{kb['id']}/docs").json()
        save_to_local_kb(kb['id'], docs)
        if log: log(f"知识库 {kb['id']} 同步完成，文档数: {len(docs)}")
    if log: log("全部 PandaWiki 知识库同步完成！")


def save_to_local_kb(kb_id, docs):
    """
    将 PandaWiki 某知识库的所有文档保存到本地并入库
    - 每个知识库一个子目录，文档以 txt 存储
    - 自动调用 KnowledgeBase.add_document 入库
    """
    kb_dir = os.path.join(LOCAL_KB_ROOT, kb_id)
    os.makedirs(kb_dir, exist_ok=True)
    kb = KnowledgeBase(kb_id, base_path=LOCAL_KB_ROOT)
    for i, doc in enumerate(docs):
        content = doc.get("content", "")
        file_path = os.path.join(kb_dir, f"doc_{i+1}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        # 逐个文档入库
        kb.add_document(file_path)
    print(f"同步知识库 {kb_id}，文档数: {len(docs)}")


def your_rag_answer_func(question, kb_id):
    """
    用本地同步的 PandaWiki 知识库做智能检索与生成
    - 检索相关文档片段
    - 可集成 LLM/自定义生成逻辑
    """
    kb = KnowledgeBase(kb_id, base_path=LOCAL_KB_ROOT)
    # 检索相关文档片段
    search_result = kb.search(question, top_k=3)
    context = "\n".join([item.get("content", "") for item in search_result])
    # 生成答案（此处可调用 LLM/自定义生成逻辑）
    answer = f"【知识库检索片段】\n{context}\n【问题】{question}\n【答案】（此处调用你的RAG生成模型）"
    return answer 