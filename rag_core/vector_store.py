"""
vector_store.py
本地向量存储引擎，支持SQLite + FAISS的持久化向量存储。
"""
import os
import json
import sqlite3
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import pickle
from datetime import datetime

try:
    import faiss  # type: ignore
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("[vector_store] 警告: FAISS未安装，将使用基础向量存储")


class VectorStore:
    """
    本地向量存储引擎
    
    支持功能：
    - 向量持久化存储
    - 文档元数据管理
    - 向量检索和相似度搜索
    - 增量更新支持
    """
    
    def __init__(self, db_path: str = "knowledge_base/vectors/vector_store.db"):
        """
        初始化向量存储引擎
        
        :param db_path: SQLite数据库路径
        """
        self.db_path = db_path
        self.vectors_path = os.path.join(os.path.dirname(db_path), "embeddings.npy")
        self.index_path = os.path.join(os.path.dirname(db_path), "faiss_index.pkl")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        
        # 加载或创建向量索引
        self._load_or_create_index()
        
    def _init_database(self):
        """初始化SQLite数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 文档表：存储文档元数据
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # 文本块表：存储文档分块信息
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    chunk_size INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents (id)
                )
            """)
            
            # 向量表：存储向量元数据
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vectors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chunk_id INTEGER NOT NULL,
                    vector_index INTEGER NOT NULL,
                    vector_dim INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chunk_id) REFERENCES chunks (id)
                )
            """)
            
            conn.commit()
    
    def _load_or_create_index(self):
        """加载或创建FAISS索引"""
        if FAISS_AVAILABLE and os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'rb') as f:
                    self.index = pickle.load(f)
                print(f"[vector_store] 加载FAISS索引: {self.index_path}")
            except Exception as e:
                print(f"[vector_store] 加载索引失败，创建新索引: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """创建新的FAISS索引"""
        if FAISS_AVAILABLE:
            # 创建IVFFlat索引，适合小到中等规模数据集
            dimension = 384  # 默认维度，后续可动态调整
            self.index = faiss.IndexFlatIP(dimension)  # 内积索引，用于余弦相似度
            print(f"[vector_store] 创建新FAISS索引，维度: {dimension}")
        else:
            self.index = None
            print("[vector_store] FAISS不可用，使用基础向量存储")
    
    def add_document(self, file_path: str, chunks: List[str], embeddings: List[List[float]]) -> int:
        """
        添加文档到知识库
        
        :param file_path: 文档路径
        :param chunks: 文档分块列表
        :param embeddings: 对应的向量列表
        :return: 文档ID
        """
        if len(chunks) != len(embeddings):
            raise ValueError("文档块数量与向量数量不匹配")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. 添加文档记录
            filename = os.path.basename(file_path)
            file_type = os.path.splitext(filename)[1].lower()
            file_size = os.path.getsize(file_path)
            
            cursor.execute("""
                INSERT INTO documents (filename, file_path, file_type, file_size)
                VALUES (?, ?, ?, ?)
            """, (filename, file_path, file_type, file_size))
            
            document_id = cursor.lastrowid
            if document_id is None:
                raise ValueError("无法获取文档ID")
            
            # 2. 添加文本块
            for i, chunk in enumerate(chunks):
                cursor.execute("""
                    INSERT INTO chunks (document_id, chunk_index, content, chunk_size)
                    VALUES (?, ?, ?, ?)
                """, (document_id, i, chunk, len(chunk)))
                
                chunk_id = cursor.lastrowid
                
                # 3. 添加向量记录
                embedding = embeddings[i]
                cursor.execute("""
                    INSERT INTO vectors (chunk_id, vector_index, vector_dim)
                    VALUES (?, ?, ?)
                """, (chunk_id, i, len(embedding)))
            
            conn.commit()
        
        # 4. 更新向量索引
        self._update_index(embeddings)
        
        print(f"[vector_store] 成功添加文档: {filename}，包含 {len(chunks)} 个文本块")
        return document_id
    
    def _update_index(self, embeddings: List[List[float]]):
        """更新FAISS索引"""
        if not FAISS_AVAILABLE or self.index is None:
            return
        
        # 转换为numpy数组
        vectors = np.array(embeddings, dtype=np.float32)
        
        # 添加到索引
        self.index.add(vectors)
        
        # 保存索引
        with open(self.index_path, 'wb') as f:
            pickle.dump(self.index, f)
        
        print(f"[vector_store] 更新FAISS索引，新增 {len(embeddings)} 个向量")
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict]:
        """
        向量相似度搜索
        
        :param query_vector: 查询向量
        :param top_k: 返回最相似的结果数量
        :return: 搜索结果列表，包含文档信息和相似度分数
        """
        if not FAISS_AVAILABLE or self.index is None:
            # 回退到基础搜索
            return self._basic_search(query_vector, top_k)
        
        # 使用FAISS搜索
        query_array = np.array([query_vector], dtype=np.float32)
        scores, indices = self.index.search(query_array, top_k)
        
        # 获取详细信息
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx == -1:  # FAISS返回-1表示无效索引
                continue
            
            chunk_info = self._get_chunk_by_index(idx)
            if chunk_info:
                results.append({
                    'chunk_id': chunk_info['chunk_id'],
                    'content': chunk_info['content'],
                    'document_id': chunk_info['document_id'],
                    'filename': chunk_info['filename'],
                    'score': float(score),
                    'rank': i + 1
                })
        
        return results
    
    def _basic_search(self, query_vector: List[float], top_k: int = 5) -> List[Dict]:
        """基础向量搜索（不使用FAISS）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 获取所有向量
            cursor.execute("""
                SELECT v.id, v.chunk_id, v.vector_index, c.content, c.document_id, d.filename
                FROM vectors v
                JOIN chunks c ON v.chunk_id = c.id
                JOIN documents d ON c.document_id = d.id
                ORDER BY v.id
            """)
            
            rows = cursor.fetchall()
            
            if not rows:
                return []
            
            # 计算相似度（这里简化处理，实际应该从文件加载向量）
            results = []
            for row in rows:
                # 简化的相似度计算，实际应该加载真实向量
                score = 0.5  # 占位符
                results.append({
                    'chunk_id': row[1],
                    'content': row[3],
                    'document_id': row[4],
                    'filename': row[5],
                    'score': score,
                    'rank': len(results) + 1
                })
            
            # 按分数排序并返回top_k
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:top_k]
    
    def _get_chunk_by_index(self, index: int) -> Optional[Dict]:
        """根据索引获取文本块信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.content, c.document_id, d.filename
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                ORDER BY c.id
                LIMIT 1 OFFSET ?
            """, (index,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'chunk_id': row[0],
                    'content': row[1],
                    'document_id': row[2],
                    'filename': row[3]
                }
            return None
    
    def get_document_info(self, document_id: int) -> Optional[Dict]:
        """获取文档信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, file_path, file_type, file_size, created_at, updated_at, status
                FROM documents
                WHERE id = ?
            """, (document_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'filename': row[1],
                    'file_path': row[2],
                    'file_type': row[3],
                    'file_size': row[4],
                    'created_at': row[5],
                    'updated_at': row[6],
                    'status': row[7]
                }
            return None
    
    def list_documents(self) -> List[Dict]:
        """列出所有文档"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, file_type, file_size, created_at, status
                FROM documents
                ORDER BY created_at DESC
            """)
            
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'filename': row[1],
                    'file_type': row[2],
                    'file_size': row[3],
                    'created_at': row[4],
                    'status': row[5]
                }
                for row in rows
            ]
    
    def delete_document(self, document_id: int) -> bool:
        """删除文档"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 获取文档的所有chunk_id
            cursor.execute("SELECT id FROM chunks WHERE document_id = ?", (document_id,))
            chunk_ids = [row[0] for row in cursor.fetchall()]
            
            if not chunk_ids:
                return False
            
            # 删除向量记录
            cursor.execute("DELETE FROM vectors WHERE chunk_id IN ({})".format(
                ','.join('?' * len(chunk_ids))), chunk_ids)
            
            # 删除文本块
            cursor.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            
            # 删除文档
            cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            
            conn.commit()
            
            # 重建索引（简化处理，实际应该增量更新）
            self._rebuild_index()
            
            print(f"[vector_store] 成功删除文档 ID: {document_id}")
            return True
    
    def _rebuild_index(self):
        """重建FAISS索引"""
        if not FAISS_AVAILABLE:
            return
        
        # 这里应该重新加载所有向量并重建索引
        # 简化处理，实际实现需要从数据库加载所有向量
        print("[vector_store] 索引重建功能待实现")
    
    def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 文档数量
            cursor.execute("SELECT COUNT(*) FROM documents WHERE status = 'active'")
            doc_count = cursor.fetchone()[0]
            
            # 文本块数量
            cursor.execute("SELECT COUNT(*) FROM chunks")
            chunk_count = cursor.fetchone()[0]
            
            # 向量数量
            cursor.execute("SELECT COUNT(*) FROM vectors")
            vector_count = cursor.fetchone()[0]
            
            # 总文件大小
            cursor.execute("SELECT SUM(file_size) FROM documents WHERE status = 'active'")
            result = cursor.fetchone()[0]
            total_size = result if result is not None else 0
            
            return {
                'document_count': doc_count,
                'chunk_count': chunk_count,
                'vector_count': vector_count,
                'total_size_bytes': total_size,
                'index_type': 'FAISS' if FAISS_AVAILABLE else 'Basic',
                'database_path': self.db_path
            } 