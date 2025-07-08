import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from rag_core.data_loader import load_documents
from rag_core.embedding import embed_documents
from rag_core.retriever import retrieve
from rag_core.generator import generate_answer
from utils.config import get_llm_config, LLM_PROVIDER

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
            return redirect(url_for("result", filename=filename, question=question, llm_api_key=llm_api_key, llm_model=llm_model))
        else:
            flash("文件类型不支持")
            return redirect(request.url)
    return render_template("index.html")

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
    # 1. 文档加载
    try:
        doc_chunks = load_documents(file_path)
    except Exception as e:
        doc_chunks = [f"文档加载失败: {e}"]
    # 2. 向量化
    try:
        embeddings = embed_documents(doc_chunks)
    except Exception as e:
        embeddings = [[0.0] * 8 for _ in doc_chunks]
    # 3. 检索
    try:
        retrieved_chunks = retrieve(question, embeddings, doc_chunks, model_path='rag_mvp/models/all-MiniLM-L6-v2', top_k=2)
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
        retrieved_chunks=retrieved_chunks
    )

if __name__ == "__main__":
    app.run(debug=True)
