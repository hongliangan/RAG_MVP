"""
knowledge_base.py
知识库管理器，整合文档处理、向量化和存储功能。
"""
import os
import shutil
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

from .data_loader import load_documents
from .embedding import embed_documents
from .text_splitter import TextSplitter
from .vector_store import VectorStore
from utils.config import get_text_chunk_config


class KnowledgeBase:
    """
    知识库管理器
    
    功能：
    - 文档管理和存储
    - 自动向量化和索引
    - 知识库查询和检索
    - 文档版本管理
    """
    
    def __init__(self, kb_name: str = "default", base_path: str = "knowledge_base"):
        """
        初始化知识库
        
        :param kb_name: 知识库名称
        :param base_path: 知识库基础路径
        """
        self.kb_name = kb_name
        self.base_path = Path(base_path)
        self.documents_path = self.base_path / "documents" / kb_name
        self.vectors_path = self.base_path / "vectors" / kb_name
        
        # 确保目录存在
        self.documents_path.mkdir(parents=True, exist_ok=True)
        self.vectors_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self.vector_store = VectorStore(str(self.vectors_path / "vector_store.db"))
        self.text_splitter = TextSplitter()
        
        print(f"[knowledge_base] 初始化知识库: {kb_name}")
        print(f"[knowledge_base] 文档路径: {self.documents_path}")
        print(f"[knowledge_base] 向量路径: {self.vectors_path}")
    
    def add_document(self, file_path: str, chunk_config: Optional[Dict] = None) -> Dict:
        """
        添加文档到知识库
        
        :param file_path: 文档路径
        :param chunk_config: 文本切片配置
        :return: 添加结果信息
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文档不存在: {file_path}")
        
        filename = os.path.basename(file_path)
        print(f"[knowledge_base] 开始处理文档: {filename}")
        
        try:
            # 1. 复制文档到知识库
            dest_path = self.documents_path / filename
            shutil.copy2(file_path, dest_path)
            print(f"[knowledge_base] 文档已复制到: {dest_path}")
            
            # 2. 加载和切片文档
            if chunk_config:
                self.text_splitter.config.update(chunk_config)
            
            chunks = load_documents(str(dest_path), self.text_splitter.config)
            print(f"[knowledge_base] 文档切片完成，共 {len(chunks)} 个文本块")
            
            # 3. 向量化文档
            embeddings = embed_documents(chunks)
            print(f"[knowledge_base] 向量化完成，共 {len(embeddings)} 个向量")
            
            # 4. 存储到向量数据库
            document_id = self.vector_store.add_document(str(dest_path), chunks, embeddings)
            
            # 5. 获取文档信息
            doc_info = self.vector_store.get_document_info(document_id)
            
            result = {
                'success': True,
                'document_id': document_id,
                'filename': filename,
                'chunks_count': len(chunks),
                'vectors_count': len(embeddings),
                'file_size': os.path.getsize(dest_path),
                'created_at': datetime.now().isoformat(),
                'document_info': doc_info
            }
            
            print(f"[knowledge_base] 文档添加成功: {filename} (ID: {document_id})")
            return result
            
        except Exception as e:
            print(f"[knowledge_base] 文档添加失败: {e}")
            # 清理已复制的文件
            dest_path = self.documents_path / filename
            if dest_path.exists():
                dest_path.unlink()
            
            return {
                'success': False,
                'error': str(e),
                'filename': filename
            }
    
    def search(self, query: str, top_k: int = 5, **kwargs) -> List[Dict]:
        """
        在知识库中搜索相关内容
        
        :param query: 查询文本
        :param top_k: 返回结果数量
        :param kwargs: 其他检索参数
        :return: 搜索结果列表
        """
        print(f"[knowledge_base] 开始搜索: {query}")
        
        try:
            # 1. 向量化查询
            query_embeddings = embed_documents([query])
            if not query_embeddings:
                return []
            
            query_vector = query_embeddings[0]
            
            # 2. 向量搜索
            results = self.vector_store.search(query_vector, top_k)
            
            # 3. 应用检索参数过滤
            filtered_results = self._apply_retrieval_filters(results, **kwargs)
            
            print(f"[knowledge_base] 搜索完成，找到 {len(filtered_results)} 个相关结果")
            return filtered_results
            
        except Exception as e:
            print(f"[knowledge_base] 搜索失败: {e}")
            return []
    
    def _apply_retrieval_filters(self, results: List[Dict], **kwargs) -> List[Dict]:
        """应用检索参数过滤"""
        filtered_results = results
        
        # 相似度阈值过滤
        similarity_threshold = kwargs.get('similarity_threshold', 0.0)
        if similarity_threshold > 0:
            filtered_results = [
                r for r in filtered_results 
                if r.get('score', 0) >= similarity_threshold
            ]
        
        # 去重过滤
        if kwargs.get('deduplication', True):
            seen_contents = set()
            unique_results = []
            for r in filtered_results:
                content_hash = hash(r.get('content', ''))
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    unique_results.append(r)
            filtered_results = unique_results
        
        return filtered_results
    
    def list_documents(self) -> List[Dict]:
        """列出知识库中的所有文档"""
        return self.vector_store.list_documents()
    
    def get_document_info(self, document_id: int) -> Optional[Dict]:
        """获取文档详细信息"""
        return self.vector_store.get_document_info(document_id)
    
    def delete_document(self, document_id: int) -> bool:
        """删除文档"""
        try:
            # 获取文档信息
            doc_info = self.vector_store.get_document_info(document_id)
            if not doc_info:
                return False
            
            # 删除向量数据库中的记录
            success = self.vector_store.delete_document(document_id)
            
            if success:
                # 删除物理文件
                file_path = Path(doc_info['file_path'])
                if file_path.exists():
                    file_path.unlink()
                    print(f"[knowledge_base] 物理文件已删除: {file_path}")
            
            return success
            
        except Exception as e:
            print(f"[knowledge_base] 删除文档失败: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        stats = self.vector_store.get_stats()
        stats.update({
            'knowledge_base_name': self.kb_name,
            'documents_path': str(self.documents_path),
            'vectors_path': str(self.vectors_path),
            'created_at': datetime.now().isoformat()
        })
        return stats
    
    def clear(self) -> bool:
        """清空知识库"""
        try:
            # 删除所有文档
            documents = self.list_documents()
            for doc in documents:
                self.delete_document(doc['id'])
            
            # 清理目录
            if self.documents_path.exists():
                shutil.rmtree(self.documents_path)
                self.documents_path.mkdir(parents=True, exist_ok=True)
            
            print(f"[knowledge_base] 知识库已清空: {self.kb_name}")
            return True
            
        except Exception as e:
            print(f"[knowledge_base] 清空知识库失败: {e}")
            return False
    
    def export_documents(self, export_path: str) -> bool:
        """导出知识库文档"""
        try:
            export_dir = Path(export_path)
            export_dir.mkdir(parents=True, exist_ok=True)
            
            documents = self.list_documents()
            for doc in documents:
                doc_info = self.get_document_info(doc['id'])
                if doc_info:
                    src_path = Path(doc_info['file_path'])
                    dst_path = export_dir / doc_info['filename']
                    if src_path.exists():
                        shutil.copy2(src_path, dst_path)
            
            print(f"[knowledge_base] 文档已导出到: {export_path}")
            return True
            
        except Exception as e:
            print(f"[knowledge_base] 导出文档失败: {e}")
            return False


def create_knowledge_base(kb_name: str, base_path: str = "knowledge_base") -> KnowledgeBase:
    """
    创建新的知识库
    
    :param kb_name: 知识库名称
    :param base_path: 基础路径
    :return: 知识库实例
    """
    return KnowledgeBase(kb_name, base_path)


def list_knowledge_bases(base_path: str = "knowledge_base") -> List[str]:
    """
    列出所有知识库
    
    :param base_path: 基础路径
    :return: 知识库名称列表
    """
    base_dir = Path(base_path) / "documents"
    if not base_dir.exists():
        return []
    
    return [d.name for d in base_dir.iterdir() if d.is_dir()] 