import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from rag_core.data_loader import load_documents
from rag_core.embedding import embed_documents
from rag_core.retriever import retrieve
from rag_core.generator import generate_answer
from rag_core.knowledge_base import KnowledgeBase, create_knowledge_base, list_knowledge_bases
from utils.config import get_llm_config, LLM_PROVIDER, get_retrieval_params
from rag_core.llm_api import call_llm_api
from utils.config import get_text_chunk_config
import urllib.parse

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt", "pdf", "docx"}

app = Flask(__name__)
app.secret_key = "rag_mvp_secret"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return filename and "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

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
            filename = secure_filename(file.filename)
            if not filename:
                flash("文件名无效")
                return redirect(request.url)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            question = request.form.get("question", "") or ""
            llm_api_key = request.form.get("llm_api_key", "") or ""
            llm_model = request.form.get("llm_model", "") or ""
            
            # 获取切片参数
            split_method = request.form.get('split_method', 'paragraph')
            chunk_size = request.form.get('chunk_size', type=int)
            chunk_overlap = request.form.get('chunk_overlap', type=int)
            max_sentences_per_chunk = request.form.get('max_sentences_per_chunk', type=int)
            min_paragraph_length = request.form.get('min_paragraph_length', type=int)
            max_paragraph_length = request.form.get('max_paragraph_length', type=int)
            
            # 构建切片参数字典
            chunk_config = {'split_method': split_method}
            if split_method == 'character':
                if chunk_size: chunk_config['chunk_size'] = str(chunk_size)
                if chunk_overlap is not None: chunk_config['chunk_overlap'] = str(chunk_overlap)
            if split_method == 'sentence':
                if max_sentences_per_chunk: chunk_config['max_sentences_per_chunk'] = str(max_sentences_per_chunk)
            if split_method == 'paragraph':
                if min_paragraph_length: chunk_config['min_paragraph_length'] = str(min_paragraph_length)
                if max_paragraph_length: chunk_config['max_paragraph_length'] = str(max_paragraph_length)
            
            # 获取检索参数
            top_k = request.form.get('top_k', type=int, default=3)
            similarity_threshold = request.form.get('similarity_threshold', type=float, default=0.0)
            deduplication = request.form.get('deduplication', 'true') == 'true'
            retrieval_strategy = request.form.get('retrieval_strategy', 'cosine')
            context_window = request.form.get('context_window', type=int, default=0)
            
            # 权重配置
            length_weight = request.form.get('length_weight', '')
            position_weight = request.form.get('position_weight', '')
            keyword_weight = request.form.get('keyword_weight', '').split(',') if request.form.get('keyword_weight') else []
            
            weight_config = {
                'length_weight': length_weight if length_weight else None,
                'position_weight': position_weight if position_weight else None,
                'keyword_weight': [kw.strip() for kw in keyword_weight if kw.strip()]
            }
            
            # 构建检索参数字典
            retrieval_config = {
                'top_k': str(top_k),
                'similarity_threshold': str(similarity_threshold),
                'deduplication': str(deduplication).lower(),
                'retrieval_strategy': retrieval_strategy,
                'weight_config': weight_config,
                'context_window': str(context_window)
            }
            
            # 将参数编码进URL
            chunk_config_str = urllib.parse.urlencode(chunk_config)
            retrieval_config_str = urllib.parse.urlencode(retrieval_config, doseq=True)
            
            return redirect(url_for("result", 
                                  filename=filename, 
                                  question=question, 
                                  llm_api_key=llm_api_key, 
                                  llm_model=llm_model, 
                                  chunk_config=chunk_config_str,
                                  retrieval_config=retrieval_config_str))
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
    
    return render_template("knowledge_base.html", 
                         kb_name=kb_name,
                         documents=documents,
                         stats=stats,
                         all_kbs=all_kbs)

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
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)
        
        # 添加到知识库
        kb = create_knowledge_base(kb_name)
        result = kb.add_document(file_path)
        
        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/kb/search")
def kb_search():
    """在知识库中搜索"""
    kb_name = request.args.get("kb_name", "default")
    query = request.args.get("query", "")
    top_k = request.args.get("top_k", type=int, default=5)
    
    if not query:
        return jsonify({"success": False, "error": "查询不能为空"})
    
    try:
        kb = create_knowledge_base(kb_name)
        results = kb.search(query, top_k=top_k)
        return jsonify({"success": True, "results": results})
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
        return render_template("result.html", answer="未指定文件名", filename="", question=question, doc_chunks=[], embeddings=[], retrieved_chunks=[])
    
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    
    # 获取切片参数
    chunk_config_str = request.args.get('chunk_config', '')
    chunk_config = dict(urllib.parse.parse_qsl(chunk_config_str)) if chunk_config_str else get_text_chunk_config()
    
    # 获取检索参数
    retrieval_config_str = request.args.get('retrieval_config', '')
    if retrieval_config_str:
        retrieval_config = dict(urllib.parse.parse_qsl(retrieval_config_str, keep_blank_values=True))
        # 处理权重配置
        weight_config = {}
        if retrieval_config.get('weight_config.length_weight'):
            weight_config['length_weight'] = retrieval_config['weight_config.length_weight']
        if retrieval_config.get('weight_config.position_weight'):
            weight_config['position_weight'] = retrieval_config['weight_config.position_weight']
        if retrieval_config.get('weight_config.keyword_weight'):
            weight_config['keyword_weight'] = [kw.strip() for kw in retrieval_config['weight_config.keyword_weight'].split(',') if kw.strip()]
        
        retrieval_params = {
            'top_k': int(retrieval_config.get('top_k', 3)),
            'similarity_threshold': float(retrieval_config.get('similarity_threshold', 0.0)),
            'deduplication': retrieval_config.get('deduplication', 'true') == 'true',
            'retrieval_strategy': retrieval_config.get('retrieval_strategy', 'cosine'),
            'weight_config': weight_config,
            'context_window': int(retrieval_config.get('context_window', 0))
        }
    else:
        retrieval_params = get_retrieval_params()
    
    # 类型转换 - 保持字符串类型，因为chunk_config需要字符串值
    for k in ['chunk_size', 'chunk_overlap', 'max_sentences_per_chunk', 'min_paragraph_length', 'max_paragraph_length']:
        if k in chunk_config and chunk_config[k] is not None:
            try:
                # 确保是字符串类型
                chunk_config[k] = str(chunk_config[k])
            except Exception:
                pass
    
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
        retrieved_chunks = retrieve(question, embeddings, doc_chunks, **retrieval_params)
    except Exception as e:
        retrieved_chunks = [f"检索失败: {e}"]
    
    # 4. 生成
    try:
        answer = generate_answer(question, retrieved_chunks, llm_model=llm_model, api_key=llm_api_key)
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
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
