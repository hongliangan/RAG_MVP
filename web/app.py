import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from rag_core.data_loader import load_documents
from rag_core.embedding import embed_documents
from rag_core.retriever import retrieve
from rag_core.generator import generate_answer
from rag_core.knowledge_base import (
    KnowledgeBase,
    create_knowledge_base,
    list_knowledge_bases,
)
from rag_core.conversation_manager import get_conversation_manager
from utils.config import get_llm_config, LLM_PROVIDER, get_retrieval_params
from rag_core.llm_api import call_llm_api
from utils.config import get_text_chunk_config
import urllib.parse
import re
from utils.config import load_global_config, save_global_config
from utils.chunk_config import validate_chunk_config

UPLOAD_FOLDER = "uploads"
# 支持更多文档格式
ALLOWED_EXTENSIONS = {"txt", "pdf", "docx", "md", "html", "json", "csv", "xlsx", "xls"}

app = Flask(__name__)
app.secret_key = "rag_mvp_secret"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return (
        filename
        and "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def safe_filename(filename):
    """
    自定义安全的文件名处理函数
    保留中文字符，但移除危险字符
    """
    if not filename:
        return ""

    # 移除路径分隔符和危险字符，但保留中文字符
    # 移除: / \ : * ? " < > |
    filename = re.sub(r'[\/\\:*?"<>|]', "", filename)

    # 移除控制字符
    filename = "".join(char for char in filename if ord(char) >= 32)

    # 移除前后空格
    filename = filename.strip()

    # 如果文件名为空，返回默认名
    if not filename:
        return "unnamed_file"

    return filename


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # 文件上传
        if "file" not in request.files:
            flash("未选择文件")
            return redirect(request.url)
        file = request.files["file"]
        if not file or not file.filename:
            flash("未选择文件")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = safe_filename(file.filename)
            if not filename:
                flash("文件名无效")
                return redirect(request.url)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            question = request.form.get("question", "") or ""
            llm_api_key = request.form.get("llm_api_key", "") or ""
            llm_model = request.form.get("llm_model", "") or ""

            # 获取切片参数
            split_method = request.form.get("split_method", "paragraph")
            chunk_size = request.form.get("chunk_size", type=int)
            chunk_overlap = request.form.get("chunk_overlap", type=int)
            max_sentences_per_chunk = request.form.get(
                "max_sentences_per_chunk", type=int
            )
            min_paragraph_length = request.form.get("min_paragraph_length", type=int)
            max_paragraph_length = request.form.get("max_paragraph_length", type=int)

            # 构建切片参数字典
            chunk_config = {"split_method": split_method}
            if split_method == "character":
                if chunk_size:
                    chunk_config["chunk_size"] = str(chunk_size)
                if chunk_overlap is not None:
                    chunk_config["chunk_overlap"] = str(chunk_overlap)
            if split_method == "sentence":
                if max_sentences_per_chunk:
                    chunk_config["max_sentences_per_chunk"] = str(
                        max_sentences_per_chunk
                    )
            if split_method == "paragraph":
                if min_paragraph_length:
                    chunk_config["min_paragraph_length"] = str(min_paragraph_length)
                if max_paragraph_length:
                    chunk_config["max_paragraph_length"] = str(max_paragraph_length)

            # 获取检索参数
            top_k = request.form.get("top_k", type=int, default=3)
            similarity_threshold = request.form.get(
                "similarity_threshold", type=float, default=0.0
            )
            deduplication = request.form.get("deduplication", "true") == "true"
            retrieval_strategy = request.form.get("retrieval_strategy", "cosine")
            context_window = request.form.get("context_window", type=int, default=0)

            # 权重配置
            length_weight = request.form.get("length_weight", "")
            position_weight = request.form.get("position_weight", "")
            keyword_weight = (
                request.form.get("keyword_weight", "").split(",")
                if request.form.get("keyword_weight")
                else []
            )

            weight_config = {
                "length_weight": length_weight if length_weight else None,
                "position_weight": position_weight if position_weight else None,
                "keyword_weight": [kw.strip() for kw in keyword_weight if kw.strip()],
            }

            # 构建检索参数字典
            retrieval_config = {
                "top_k": str(top_k),
                "similarity_threshold": str(similarity_threshold),
                "deduplication": str(deduplication).lower(),
                "retrieval_strategy": retrieval_strategy,
                "weight_config": weight_config,
                "context_window": str(context_window),
            }

            # 将参数编码进URL
            chunk_config_str = urllib.parse.urlencode(chunk_config)
            retrieval_config_str = urllib.parse.urlencode(retrieval_config, doseq=True)

            return redirect(
                url_for(
                    "result",
                    filename=filename,
                    question=question,
                    llm_api_key=llm_api_key,
                    llm_model=llm_model,
                    chunk_config=chunk_config_str,
                    retrieval_config=retrieval_config_str,
                )
            )
        else:
            flash("文件类型不支持")
            return redirect(request.url)
    return render_template("index.html")


@app.route("/knowledge_base")
def knowledge_base():
    """知识库管理页面"""
    kb_name = request.args.get("kb_name", "default")
    try:
        kb = create_knowledge_base(kb_name)
        documents = kb.list_documents()
        stats = kb.get_stats()
        all_kbs = list_knowledge_bases()
    except Exception as e:
        documents = []
        stats = {}
        all_kbs = []
        flash(f"加载知识库失败: {e}")

    return render_template(
        "knowledge_base.html",
        kb_name=kb_name,
        documents=documents,
        stats=stats,
        all_kbs=all_kbs,
    )


@app.route("/kb/add_document", methods=["POST"])
def kb_add_document():
    """添加文档到知识库"""
    kb_name = request.form.get("kb_name", "default")
    if "file" not in request.files:
        return jsonify({"success": False, "error": "未选择文件"})

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"success": False, "error": "未选择文件"})

    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "文件类型不支持"})

    try:
        # 保存上传的文件
        filename = safe_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        # 读取 embedding_provider 参数
        embedding_provider = request.form.get("embedding_provider", "")
        if not embedding_provider:
            embedding_provider = None  # 跟随全局

        # 解析切片配置参数
        chunk_config = {}
        split_method = request.form.get("split_method", "paragraph")
        chunk_config["split_method"] = split_method

        # 根据切片方式获取对应参数
        if split_method == "character":
            chunk_size = request.form.get("chunk_size", type=int)
            chunk_overlap = request.form.get("chunk_overlap", type=int)
            if chunk_size:
                chunk_config["chunk_size"] = chunk_size
            if chunk_overlap is not None:
                chunk_config["chunk_overlap"] = chunk_overlap

        elif split_method == "sentence":
            max_sentences = request.form.get("max_sentences_per_chunk", type=int)
            if max_sentences:
                chunk_config["max_sentences_per_chunk"] = max_sentences

        elif split_method == "paragraph":
            min_length = request.form.get("min_paragraph_length", type=int)
            max_length = request.form.get("max_paragraph_length", type=int)
            separator = request.form.get("paragraph_separator", "\n\n")
            if min_length:
                chunk_config["min_paragraph_length"] = min_length
            if max_length:
                chunk_config["max_paragraph_length"] = max_length
            if separator:
                chunk_config["paragraph_separator"] = separator

        # 通用过滤参数
        min_chunk_length = request.form.get("min_chunk_length", type=int)
        max_chunk_length = request.form.get("max_chunk_length", type=int)
        remove_empty = request.form.get("remove_empty_chunks", "true") == "true"
        remove_whitespace = request.form.get("remove_whitespace_only", "true") == "true"

        if min_chunk_length:
            chunk_config["min_chunk_length"] = min_chunk_length
        if max_chunk_length:
            chunk_config["max_chunk_length"] = max_chunk_length
        chunk_config["remove_empty_chunks"] = remove_empty
        chunk_config["remove_whitespace_only"] = remove_whitespace

        # 高级参数
        smart_split = request.form.get("smart_split", "true") == "true"
        preserve_formatting = request.form.get("preserve_formatting", "false") == "true"
        merge_short_chunks = request.form.get("merge_short_chunks", "true") == "true"
        merge_threshold = request.form.get("merge_threshold", type=float)

        chunk_config["smart_split"] = smart_split
        chunk_config["preserve_formatting"] = preserve_formatting
        chunk_config["merge_short_chunks"] = merge_short_chunks
        if merge_threshold:
            chunk_config["merge_threshold"] = merge_threshold

        # 后端参数校验
        errors = validate_chunk_config(chunk_config)
        if errors:
            return jsonify(
                {"success": False, "error": "参数校验失败", "detail": errors}
            )

        # 添加到知识库
        kb = create_knowledge_base(kb_name)
        result = kb.add_document(file_path, chunk_config=chunk_config, embedding_provider=embedding_provider)

        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/kb/search", methods=["POST"])
def kb_search():
    """在知识库中搜索"""
    kb_name = request.form.get("kb_name", "default")
    query = request.form.get("query", "")
    top_k = request.form.get("top_k", type=int, default=5)
    use_enhanced = request.form.get("use_enhanced", "true").lower() == "true"

    if not query:
        return jsonify({"success": False, "error": "查询内容不能为空"})

    try:
        kb = create_knowledge_base(kb_name)
        results = kb.search(query, top_k=top_k, use_enhanced=use_enhanced)

        return jsonify({"success": True, "results": results, "count": len(results)})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/kb/suggestions", methods=["GET"])
def kb_suggestions():
    """获取搜索建议"""
    kb_name = request.args.get("kb_name", "default")
    query = request.args.get("query", "")
    limit = request.args.get("limit", type=int, default=5)

    if not query or len(query) < 2:
        return jsonify({"success": True, "suggestions": []})

    try:
        kb = create_knowledge_base(kb_name)
        suggestions = kb.get_search_suggestions(query, limit)

        return jsonify({"success": True, "suggestions": suggestions})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/kb/history", methods=["GET"])
def kb_history():
    """获取检索历史"""
    kb_name = request.args.get("kb_name", "default")
    limit = request.args.get("limit", type=int, default=20)

    try:
        kb = create_knowledge_base(kb_name)
        history = kb.get_search_history(limit)

        return jsonify({"success": True, "history": history})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/kb/clear_history", methods=["POST"])
def kb_clear_history():
    """清空检索历史"""
    kb_name = request.form.get("kb_name", "default")

    try:
        kb = create_knowledge_base(kb_name)
        kb.clear_search_history()

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/kb/export_results", methods=["POST"])
def kb_export_results():
    """导出检索结果"""
    kb_name = request.form.get("kb_name", "default")
    results_json = request.form.get("results", "[]")
    format = request.form.get("format", "json")

    try:
        import json

        results = json.loads(results_json)

        kb = create_knowledge_base(kb_name)
        file_path = kb.export_search_results(results, format)

        if file_path:
            return jsonify({"success": True, "file_path": file_path})
        else:
            return jsonify({"success": False, "error": "导出失败"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/kb/delete_document", methods=["POST"])
def kb_delete_document():
    """删除知识库中的文档"""
    kb_name = request.form.get("kb_name", "default")
    doc_id = request.form.get("doc_id", type=int)

    if not doc_id:
        return jsonify({"success": False, "error": "文档ID不能为空"})

    try:
        kb = create_knowledge_base(kb_name)
        success = kb.delete_document(doc_id)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/kb/stats")
def kb_stats():
    """获取知识库统计信息"""
    kb_name = request.args.get("kb_name", "default")
    try:
        kb = create_knowledge_base(kb_name)
        stats = kb.get_stats()
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/kb/clear", methods=["POST"])
def kb_clear():
    """清空知识库"""
    kb_name = request.form.get("kb_name", "default")
    try:
        kb = create_knowledge_base(kb_name)
        success = kb.clear()
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/kb/config_info")
def kb_config_info():
    """获取切片配置信息"""
    try:
        kb = create_knowledge_base("default")
        config_info = kb.get_chunk_config_info()
        return jsonify(config_info)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/kb/validate_config", methods=["POST"])
def kb_validate_config():
    """验证切片配置"""
    try:
        config = request.get_json()
        kb = create_knowledge_base("default")
        errors = kb.validate_chunk_config(config)
        return jsonify({"errors": errors, "valid": len(errors) == 0})
    except Exception as e:
        return jsonify({"error": str(e)})


# ==================== 对话相关路由 ====================


@app.route("/chat")
def chat():
    """对话页面"""
    kb_name = request.args.get("kb_name", "default")
    session_id = request.args.get("session_id")

    # 获取知识库列表
    all_kbs = list_knowledge_bases()

    # 获取对话管理器
    conv_manager = get_conversation_manager()

    # 获取对话列表
    conversations = conv_manager.list_conversations(kb_name)

    return render_template(
        "chat.html",
        kb_name=kb_name,
        session_id=session_id,
        conversations=conversations,
        all_kbs=all_kbs,
    )


@app.route("/chat/create", methods=["POST"])
def chat_create():
    """创建新对话"""
    kb_name = request.form.get("kb_name", "default")

    try:
        conv_manager = get_conversation_manager()
        conversation = conv_manager.create_conversation(kb_name)

        return jsonify(
            {
                "success": True,
                "session_id": conversation.session_id,
                "kb_name": conversation.kb_name,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/chat/send", methods=["POST"])
def chat_send():
    """发送消息"""
    session_id = request.form.get("session_id")
    message = request.form.get("message", "").strip()
    kb_name = request.form.get("kb_name", "default")

    # 修正：session_id为None、空字符串或'None'时直接返回错误
    if not session_id or session_id == "None" or not message:
        return jsonify({"success": False, "error": "缺少必要参数"})

    try:
        conv_manager = get_conversation_manager()

        # 获取或创建对话
        conversation = conv_manager.get_conversation(session_id)
        if not conversation:
            return jsonify({"success": False, "error": "对话不存在"})

        # 添加用户消息
        conv_manager.add_message(session_id, "user", message)

        # 获取对话上下文
        context = conv_manager.get_conversation_context(session_id)

        # 在知识库中搜索相关内容
        kb = create_knowledge_base(kb_name)
        search_results = kb.search(message, top_k=3, use_enhanced=True)

        # 构建增强的查询（包含上下文）
        enhanced_query = message
        if context:
            enhanced_query = f"对话上下文：\n{context}\n\n当前问题：{message}"

        # 生成回答
        if search_results:
            # 构建检索到的内容
            retrieved_content = "\n\n".join(
                [
                    f"相关内容 {i+1}：{result['content']}"
                    for i, result in enumerate(search_results)
                ]
            )

            # 构建完整的prompt
            prompt = f"""基于以下检索到的相关内容，回答用户的问题。

检索到的相关内容：
{retrieved_content}

用户问题：{enhanced_query}

请基于检索到的内容，结合对话上下文，给出准确、详细的回答。如果检索到的内容不足以回答问题，请说明情况。"""
        else:
            prompt = f"""用户问题：{enhanced_query}

很抱歉，在知识库中没有找到与您问题相关的信息。请尝试换个方式提问，或者检查知识库中是否有相关文档。"""

        # 调用LLM生成回答
        llm_config = get_llm_config()
        # 直接传递参数，避免类型错误
        response = call_llm_api(prompt, stream=False, **llm_config)

        # 添加助手回复
        conv_manager.add_message(
            session_id,
            "assistant",
            response,
            {
                "search_results": len(search_results),
                "sources": [r.get("filename", "未知") for r in search_results],
            },
        )

        return jsonify(
            {
                "success": True,
                "response": response,
                "search_results": search_results,
                "context": context,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/chat/list", methods=["GET"])
def chat_list():
    """获取对话列表"""
    kb_name = request.args.get("kb_name")

    try:
        conv_manager = get_conversation_manager()
        conversations = conv_manager.list_conversations(kb_name)
        return jsonify({"success": True, "conversations": conversations})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/chat/delete", methods=["POST"])
def chat_delete():
    """删除对话"""
    session_id = request.form.get("session_id")

    if not session_id or session_id == "None":
        return jsonify({"success": False, "error": "缺少会话ID"})

    try:
        conv_manager = get_conversation_manager()
        success = conv_manager.delete_conversation(session_id)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/chat/export", methods=["POST"])
def chat_export():
    """导出对话"""
    session_id = request.form.get("session_id")
    format = request.form.get("format", "json")

    if not session_id or session_id == "None":
        return jsonify({"success": False, "error": "缺少会话ID"})

    try:
        conv_manager = get_conversation_manager()
        content = conv_manager.export_conversation(session_id, format)

        if content:
            return jsonify({"success": True, "content": content, "format": format})
        else:
            return jsonify({"success": False, "error": "导出失败"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/chat/clear", methods=["POST"])
def chat_clear():
    """清空对话"""
    kb_name = request.form.get("kb_name")

    try:
        conv_manager = get_conversation_manager()
        deleted_count = conv_manager.clear_conversations(kb_name)
        return jsonify({"success": True, "deleted_count": deleted_count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/result")
def result():
    filename = request.args.get("filename") or ""
    question = request.args.get("question") or ""
    llm_api_key = request.args.get("llm_api_key") or ""
    llm_model = request.args.get("llm_model") or ""
    config = get_llm_config()

    # 自动填充模型名和API Key
    if not llm_model:
        llm_model = config.get("model_name", "Qwen/Qwen2.5-72B-Instruct")
    if not llm_api_key:
        llm_api_key = config.get("api_key", "")
    # 若用硅基流动且模型名为gpt-3.5-turbo，强制替换为平台支持模型
    if LLM_PROVIDER == "siliconflow" and llm_model == "gpt-3.5-turbo":
        llm_model = config.get("model_name", "Qwen/Qwen2.5-72B-Instruct")

    if not filename:
        return render_template(
            "result.html",
            answer="未指定文件名",
            filename="",
            question=question,
            doc_chunks=[],
            embeddings=[],
            retrieved_chunks=[],
        )

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    # 获取切片参数
    chunk_config_str = request.args.get("chunk_config", "")
    if chunk_config_str:
        raw_config = dict(urllib.parse.parse_qsl(chunk_config_str))
        chunk_config = {}
        int_keys = [
            "chunk_size",
            "chunk_overlap",
            "max_sentences_per_chunk",
            "min_paragraph_length",
            "max_paragraph_length",
            "min_chunk_length",
            "max_chunk_length",
        ]
        float_keys = ["merge_threshold"]
        bool_keys = [
            "remove_empty_chunks",
            "remove_whitespace_only",
            "smart_split",
            "preserve_formatting",
            "merge_short_chunks",
        ]
        for k, v in raw_config.items():
            if k in int_keys:
                try:
                    chunk_config[k] = int(v)
                except Exception:
                    chunk_config[k] = v
            elif k in float_keys:
                try:
                    chunk_config[k] = float(v)
                except Exception:
                    chunk_config[k] = v
            elif k in bool_keys:
                chunk_config[k] = str(v).lower() == "true"
            else:
                chunk_config[k] = v
    else:
        chunk_config = get_text_chunk_config()

    # 获取检索参数
    retrieval_config_str = request.args.get("retrieval_config", "")
    if retrieval_config_str:
        retrieval_config = dict(
            urllib.parse.parse_qsl(retrieval_config_str, keep_blank_values=True)
        )
        # 处理权重配置
        weight_config = {}
        if retrieval_config.get("weight_config.length_weight"):
            weight_config["length_weight"] = retrieval_config[
                "weight_config.length_weight"
            ]
        if retrieval_config.get("weight_config.position_weight"):
            weight_config["position_weight"] = retrieval_config[
                "weight_config.position_weight"
            ]
        if retrieval_config.get("weight_config.keyword_weight"):
            weight_config["keyword_weight"] = [
                kw.strip()
                for kw in retrieval_config["weight_config.keyword_weight"].split(",")
                if kw.strip()
            ]

        retrieval_params = {
            "top_k": int(retrieval_config.get("top_k", 3)),
            "similarity_threshold": float(
                retrieval_config.get("similarity_threshold", 0.0)
            ),
            "deduplication": retrieval_config.get("deduplication", "true") == "true",
            "retrieval_strategy": retrieval_config.get("retrieval_strategy", "cosine"),
            "weight_config": weight_config,
            "context_window": int(retrieval_config.get("context_window", 0)),
        }
    else:
        retrieval_params = get_retrieval_params()

    # 类型转换 - 保持数值类型，不要转为字符串
    # 不再强制转为字符串，保持原始类型，TextSplitter 内部会做类型转换

    # 1. 文档加载
    try:
        doc_chunks = load_documents(file_path, chunk_config)
    except Exception as e:
        doc_chunks = [f"文档加载失败: {e}"]

    # 2. 向量化
    try:
        embeddings = embed_documents(doc_chunks)
    except Exception as e:
        embeddings = [[0.0] * 8 for _ in doc_chunks]

    # 3. 检索
    try:
        retrieved_chunks = retrieve(
            question, embeddings, doc_chunks, **retrieval_params
        )
    except Exception as e:
        retrieved_chunks = [f"检索失败: {e}"]

    # 4. 生成
    try:
        answer = generate_answer(
            question, retrieved_chunks, llm_model=llm_model, api_key=llm_api_key
        )
    except Exception as e:
        answer = f"生成失败: {e}"

    return render_template(
        "result.html",
        answer=answer,
        filename=filename,
        question=question,
        doc_chunks=doc_chunks,
        embeddings=embeddings,
        retrieved_chunks=retrieved_chunks,
        chunk_config=chunk_config,
        retrieval_params=retrieval_params,
    )


@app.route("/config")
def config_page():
    """系统设置页面"""
    return render_template("config.html")


@app.route("/api/config/get", methods=["GET"])
def api_get_config():
    """获取全局配置"""
    config = load_global_config()
    # 确保 embedding_provider 和 embedding_configs 字段存在
    if "embedding_provider" not in config:
        config["embedding_provider"] = "local"
    if "embedding_configs" not in config:
        config["embedding_configs"] = {
            "local": {"model_path": "./models/embedding"},
            "online": {
                "api_url": "https://api.siliconflow.cn/v1/embeddings",
                "api_key": "",
                "model_name": "BAAI/bge-large-zh-v1.5"
            }
        }
    return jsonify({"success": True, "config": config})


@app.route("/api/config/set", methods=["POST"])
def api_set_config():
    """保存全局配置"""
    try:
        data = request.get_json()
        print("[api_set_config] received data:", data)
        # 简单校验字段
        if not isinstance(data, dict):
            print("[api_set_config] error: 参数格式错误")
            return jsonify({"success": False, "error": "参数格式错误"})
        errors = {}
        # 校验llm_provider
        if not data.get("llm_provider") or not isinstance(data["llm_provider"], str):
            errors["llm_provider"] = ["LLM服务提供商不能为空，且必须为字符串"]
        # 校验llm_configs
        if "llm_configs" not in data or not isinstance(data["llm_configs"], dict):
            errors["llm_configs"] = ["llm_configs必须为字典"]
        else:
            provider = data.get("llm_provider")
            llm_cfg = data["llm_configs"].get(provider)
            if not llm_cfg or not isinstance(llm_cfg, dict):
                errors["llm_configs"] = [f"缺少{provider}的配置"]
            else:
                if not llm_cfg.get("api_key"):
                    errors["llm_api_key"] = ["API Key不能为空"]
                if not llm_cfg.get("model_name"):
                    errors["llm_model"] = ["模型名不能为空"]
                if not llm_cfg.get("api_url"):
                    errors["api_url"] = ["API地址不能为空"]
        # 校验本地模型目录
        if not data.get("local_model_dir") or not isinstance(
            data["local_model_dir"], str
        ):
            errors["local_model_dir"] = ["本地模型目录不能为空，且必须为字符串"]
        # 校验prefer_local_model
        if "prefer_local_model" not in data or not isinstance(
            data["prefer_local_model"], bool
        ):
            errors["prefer_local_model"] = ["prefer_local_model必须为布尔值"]
        # 校验 embedding_provider
        if not data.get("embedding_provider") or not isinstance(data["embedding_provider"], str):
            errors["embedding_provider"] = ["Embedding方式不能为空，且必须为字符串"]
        # 校验 embedding_configs
        if "embedding_configs" not in data or not isinstance(data["embedding_configs"], dict):
            errors["embedding_configs"] = ["embedding_configs必须为字典"]
        else:
            emb_cfgs = data["embedding_configs"]
            # 本地 embedding 校验
            if "local" not in emb_cfgs or not isinstance(emb_cfgs["local"], dict):
                errors["embedding_local_model_path"] = ["本地embedding配置缺失"]
            else:
                if not emb_cfgs["local"].get("model_path"):
                    errors["embedding_local_model_path"] = ["本地模型路径不能为空"]
            # 在线 embedding 校验
            if "online" not in emb_cfgs or not isinstance(emb_cfgs["online"], dict):
                errors["embedding_api_url"] = ["在线embedding配置缺失"]
            else:
                online_cfg = emb_cfgs["online"]
                if not online_cfg.get("api_url"):
                    errors["embedding_api_url"] = ["API地址不能为空"]
                if not online_cfg.get("model_name"):
                    errors["embedding_model_name"] = ["模型名不能为空"]
                # api_key 可为空
        print("[api_set_config] errors:", errors)
        if errors:
            return jsonify(
                {"success": False, "error": "参数校验失败", "detail": errors}
            )
        save_global_config(data)
        print("[api_set_config] config saved successfully.")
        return jsonify({"success": True})
    except Exception as e:
        print("[api_set_config] exception:", e)
        return jsonify({"success": False, "error": str(e)})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
