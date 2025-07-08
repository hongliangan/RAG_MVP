"""
knowledge_base.py
知识库管理器，整合文档处理、向量化和存储功能。
"""
import os
import shutil
import sqlite3
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

from .data_loader import load_documents, load_documents_with_metadata, get_supported_formats
from .embedding import embed_documents
from .text_splitter import TextSplitter
from .vector_store import VectorStore
from .enhanced_retriever import create_enhanced_retriever
from utils.config import get_text_chunk_config
from utils.chunk_config import get_default_chunk_config, get_recommended_configs, validate_chunk_config


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
        self.enhanced_retriever = create_enhanced_retriever(str(self.base_path / f"{kb_name}_search_history.json"))
        
        print(f"[knowledge_base] 初始化知识库: {kb_name}")
        print(f"[knowledge_base] 文档路径: {self.documents_path}")
        print(f"[knowledge_base] 向量路径: {self.vectors_path}")
    
    def add_document(self, file_path: str, chunk_config: Optional[Dict] = None, processor_config: Optional[Dict] = None) -> Dict:
        """
        添加文档到知识库
        
        :param file_path: 文档路径
        :param chunk_config: 文本切片配置，支持文档级别的参数调整
        :param processor_config: 预处理器配置
        :return: 添加结果信息
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文档不存在: {file_path}")
        
        original_filename = os.path.basename(file_path)
        filename = original_filename
        dest_path = self.documents_path / filename
        # 如有重名，自动加后缀
        count = 1
        while dest_path.exists():
            stem, suffix = os.path.splitext(original_filename)
            filename = f"{stem}_{count}{suffix}"
            dest_path = self.documents_path / filename
            count += 1
        print(f"[knowledge_base] 开始处理文档: {original_filename}")
        
        try:
            # 1. 复制文档到知识库
            shutil.copy2(file_path, dest_path)
            print(f"[knowledge_base] 文档已复制到: {dest_path}")
            
            # 2. 验证和合并切片配置
            if chunk_config:
                # 验证用户配置
                errors = validate_chunk_config(chunk_config)
                if errors:
                    print(f"[knowledge_base] 切片配置验证警告: {errors}")
                
                # 创建文档专用的切片器
                doc_splitter = TextSplitter(chunk_config)
            else:
                doc_splitter = self.text_splitter
            
            # 使用新的文档加载函数，获取详细元数据
            doc_result = load_documents_with_metadata(str(dest_path), doc_splitter.config, processor_config)
            chunks = doc_result['chunks']
            
            print(f"[knowledge_base] 文档预处理完成，格式: {doc_result.get('format', 'unknown')}")
            print(f"[knowledge_base] 文档切片完成，共 {len(chunks)} 个文本块")
            print(f"[knowledge_base] 处理时间: {doc_result.get('processing_time', 0):.2f}秒")
            
            # 3. 向量化文档
            embeddings = embed_documents(chunks)
            print(f"[knowledge_base] 向量化完成，共 {len(embeddings)} 个向量")
            
            # 4. 存储到向量数据库（数据库filename字段始终用原始名）
            document_id = self.vector_store.add_document(str(dest_path), chunks, embeddings, filename=original_filename)
            
            # 5. 获取文档信息
            doc_info = self.vector_store.get_document_info(document_id)
            if doc_info:
                doc_info['filename'] = original_filename
                # 添加预处理元数据
                doc_info['format'] = doc_result.get('format', 'unknown')
                doc_info['processing_time'] = doc_result.get('processing_time', 0)
                doc_info['original_metadata'] = doc_result.get('metadata', {})
            
            result = {
                'success': True,
                'document_id': document_id,
                'filename': original_filename,
                'chunks_count': len(chunks),
                'vectors_count': len(embeddings),
                'file_size': os.path.getsize(dest_path),
                'created_at': datetime.now().isoformat(),
                'document_info': doc_info,
                'format': doc_result.get('format', 'unknown'),
                'processing_time': doc_result.get('processing_time', 0)
            }
            
            print(f"[knowledge_base] 文档添加成功: {original_filename} (ID: {document_id})")
            return result
            
        except Exception as e:
            print(f"[knowledge_base] 文档添加失败: {e}")
            # 清理已复制的文件
            if dest_path.exists():
                dest_path.unlink()
            
            return {
                'success': False,
                'error': str(e),
                'filename': original_filename
            }
    
    def search(self, query: str, top_k: int = 5, use_enhanced: bool = True, **kwargs) -> List[Dict]:
        """
        在知识库中搜索相关内容
        
        :param query: 查询文本
        :param top_k: 返回结果数量
        :param use_enhanced: 是否使用增强检索
        :param kwargs: 其他检索参数
        :return: 搜索结果列表
        """
        print(f"[knowledge_base] 开始搜索: {query}")
        
        if use_enhanced:
            return self._enhanced_search(query, top_k, **kwargs)
        else:
            return self._basic_search(query, top_k, **kwargs)
    
    def _enhanced_search(self, query: str, top_k: int = 5, **kwargs) -> List[Dict]:
        """增强搜索：使用混合检索"""
        try:
            # 获取所有文档的向量和内容
            all_chunks = []
            all_vectors = []
            
            # 从向量存储中获取所有数据
            with sqlite3.connect(self.vector_store.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.content, c.id
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE d.status = 'active'
                    ORDER BY c.id
                """)
                
                for row in cursor.fetchall():
                    all_chunks.append(row[0])
            
            # 重新向量化所有文档（简化处理，实际应该从存储中加载）
            if all_chunks:
                all_vectors = embed_documents(all_chunks)
            
            # 使用增强检索器进行混合搜索
            results = self.enhanced_retriever.hybrid_search(
                query, all_vectors, all_chunks, top_k=top_k, **kwargs
            )
            
            # 转换为标准格式
            standard_results = []
            for result in results:
                # 查找文档名
                filename = None
                try:
                    with sqlite3.connect(self.vector_store.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT d.filename FROM chunks c JOIN documents d ON c.document_id = d.id WHERE c.content = ? LIMIT 1
                        """, (result['content'],))
                        row = cursor.fetchone()
                        if row:
                            filename = row[0]
                except Exception:
                    filename = None
                standard_results.append({
                    'content': result['content'],
                    'score': result['fused_score'],
                    'source': result['source'],
                    'matched_keywords': result.get('matched_keywords', []),
                    'filename': filename or '未知文档'
                })
            
            print(f"[knowledge_base] 增强搜索完成，找到 {len(standard_results)} 个相关结果")
            return standard_results
            
        except Exception as e:
            print(f"[knowledge_base] 增强搜索失败: {e}")
            return self._basic_search(query, top_k, **kwargs)
    
    def _basic_search(self, query: str, top_k: int = 5, **kwargs) -> List[Dict]:
        """基础搜索：使用原有向量搜索"""
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
            
            print(f"[knowledge_base] 基础搜索完成，找到 {len(filtered_results)} 个相关结果")
            return filtered_results
            
        except Exception as e:
            print(f"[knowledge_base] 基础搜索失败: {e}")
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
    
    def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """获取搜索建议"""
        return self.enhanced_retriever.get_search_suggestions(partial_query, limit)
    
    def get_search_history(self, limit: int = 20) -> List[Dict]:
        """获取检索历史"""
        return self.enhanced_retriever.get_search_history(limit)
    
    def clear_search_history(self):
        """清空检索历史"""
        self.enhanced_retriever.clear_search_history()
    
    def export_search_results(self, results: List[Dict], format: str = 'json', 
                             file_path: Optional[str] = None) -> Optional[str]:
        """导出检索结果"""
        return self.enhanced_retriever.export_results(results, format, file_path)
    
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
    
    def get_supported_formats(self) -> List[str]:
        """
        获取支持的文件格式列表
        
        :return: 支持的文件扩展名列表
        """
        return get_supported_formats()
    
    def get_chunk_config_info(self) -> Dict:
        """
        获取切片配置信息
        
        :return: 包含默认配置、推荐配置和参数说明的字典
        """
        from utils.chunk_config import get_parameters_by_category
        
        return {
            "default_config": get_default_chunk_config(),
            "recommended_configs": get_recommended_configs(),
            "parameters": get_parameters_by_category()
        }
    
    def validate_chunk_config(self, config: Dict) -> Dict[str, List[str]]:
        """
        验证切片配置
        
        :param config: 要验证的配置
        :return: 验证错误信息
        """
        return validate_chunk_config(config)


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