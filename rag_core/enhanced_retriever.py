"""
enhanced_retriever.py
增强版检索模块，支持混合检索、检索历史、结果排序优化等功能。
"""
import re
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime
import numpy as np
from pathlib import Path

from .embedding import embed_documents
from .retriever import retrieve as vector_retrieve


class EnhancedRetriever:
    """
    增强版检索器
    
    功能特性：
    - 混合检索：结合向量搜索和关键词搜索
    - 检索历史：保存和复用搜索历史
    - 结果排序：多种排序方式
    - 搜索建议：智能搜索建议
    - 结果导出：支持多种格式
    """
    
    def __init__(self, history_file: str = "search_history.json"):
        """
        初始化增强检索器
        
        :param history_file: 检索历史文件路径
        """
        self.history_file = Path(history_file)
        self.search_history = self._load_history()
        self.keyword_cache = {}  # 关键词缓存
        
    def _load_history(self) -> List[Dict]:
        """加载检索历史"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[enhanced_retriever] 加载历史记录失败: {e}")
        return []
    
    def _save_history(self):
        """保存检索历史"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.search_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[enhanced_retriever] 保存历史记录失败: {e}")
    
    def hybrid_search(self, query: str, doc_vectors: List[List[float]], docs: List[str],
                     model_path: Optional[str] = None, top_k: int = 5, 
                     vector_weight: float = 0.7, keyword_weight: float = 0.3,
                     **kwargs) -> List[Dict]:
        """
        混合检索：结合向量搜索和关键词搜索
        
        :param query: 查询文本
        :param doc_vectors: 文档向量列表
        :param docs: 原始文档片段
        :param model_path: embedding模型路径
        :param top_k: 返回结果数量
        :param vector_weight: 向量搜索权重
        :param keyword_weight: 关键词搜索权重
        :param kwargs: 其他检索参数
        :return: 混合检索结果
        """
        print(f"[enhanced_retriever] 开始混合检索: {query}")
        
        # 1. 向量搜索
        vector_results = self._vector_search(query, doc_vectors, docs, model_path, top_k * 2, **kwargs)
        
        # 2. 关键词搜索
        keyword_results = self._keyword_search(query, docs, top_k * 2, **kwargs)
        
        # 3. 结果融合
        hybrid_results = self._fuse_results(vector_results, keyword_results, 
                                          vector_weight, keyword_weight, top_k)
        
        # 4. 记录检索历史
        self._record_search(query, hybrid_results)
        
        print(f"[enhanced_retriever] 混合检索完成，返回 {len(hybrid_results)} 个结果")
        return hybrid_results
    
    def _vector_search(self, query: str, doc_vectors: List[List[float]], docs: List[str],
                      model_path: Optional[str] = None, top_k: int = 5, **kwargs) -> List[Dict]:
        """向量搜索"""
        try:
            # 使用原有的向量检索
            retrieved_docs = vector_retrieve(query, doc_vectors, docs, model_path, top_k, **kwargs)
            
            # 转换为统一格式
            results = []
            for i, doc in enumerate(retrieved_docs):
                results.append({
                    'content': doc,
                    'score': 1.0 - (i / len(retrieved_docs)),  # 简化分数计算
                    'source': 'vector',
                    'rank': i + 1
                })
            
            return results
        except Exception as e:
            print(f"[enhanced_retriever] 向量搜索失败: {e}")
            return []
    
    def _keyword_search(self, query: str, docs: List[str], top_k: int = 5, **kwargs) -> List[Dict]:
        """关键词搜索"""
        try:
            # 提取查询关键词
            keywords = self._extract_keywords(query)
            
            # 计算TF-IDF分数
            doc_scores = []
            for i, doc in enumerate(docs):
                score = self._calculate_tfidf_score(doc, keywords)
                if score > 0:
                    doc_scores.append({
                        'content': doc,
                        'score': score,
                        'source': 'keyword',
                        'rank': len(doc_scores) + 1,
                        'matched_keywords': [kw for kw in keywords if kw.lower() in doc.lower()]
                    })
            
            # 按分数排序并返回top_k
            doc_scores.sort(key=lambda x: x['score'], reverse=True)
            return doc_scores[:top_k]
            
        except Exception as e:
            print(f"[enhanced_retriever] 关键词搜索失败: {e}")
            return []
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取查询关键词"""
        # 简单的关键词提取：移除停用词，保留重要词汇
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        
        # 分词（简化版本，按空格和标点分割）
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', query)
        
        # 过滤停用词和短词
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        return keywords
    
    def _calculate_tfidf_score(self, doc: str, keywords: List[str]) -> float:
        """计算TF-IDF分数（简化版本）"""
        if not keywords:
            return 0.0
        
        doc_lower = doc.lower()
        total_score = 0.0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # 计算关键词在文档中的出现次数
            count = doc_lower.count(keyword_lower)
            if count > 0:
                # 简化的TF-IDF计算
                tf = count / len(doc_lower.split())
                total_score += tf * len(keyword)  # 关键词长度作为权重
        
        return total_score
    
    def _fuse_results(self, vector_results: List[Dict], keyword_results: List[Dict],
                     vector_weight: float, keyword_weight: float, top_k: int) -> List[Dict]:
        """融合向量搜索和关键词搜索结果"""
        # 创建文档到结果的映射
        doc_to_results = {}
        
        # 处理向量搜索结果
        for result in vector_results:
            content = result['content']
            if content not in doc_to_results:
                doc_to_results[content] = {
                    'content': content,
                    'vector_score': result['score'],
                    'keyword_score': 0.0,
                    'vector_rank': result['rank'],
                    'keyword_rank': float('inf'),
                    'matched_keywords': [],
                    'source': 'vector'
                }
        
        # 处理关键词搜索结果
        for result in keyword_results:
            content = result['content']
            if content in doc_to_results:
                doc_to_results[content]['keyword_score'] = result['score']
                doc_to_results[content]['keyword_rank'] = result['rank']
                doc_to_results[content]['matched_keywords'] = result.get('matched_keywords', [])
                doc_to_results[content]['source'] = 'hybrid'
            else:
                doc_to_results[content] = {
                    'content': content,
                    'vector_score': 0.0,
                    'keyword_score': result['score'],
                    'vector_rank': float('inf'),
                    'keyword_rank': result['rank'],
                    'matched_keywords': result.get('matched_keywords', []),
                    'source': 'keyword'
                }
        
        # 计算融合分数
        fused_results = []
        for content, result in doc_to_results.items():
            fused_score = (vector_weight * result['vector_score'] + 
                          keyword_weight * result['keyword_score'])
            # 分数归一化到0~1
            fused_score = min(max(fused_score, 0.0), 1.0)
            
            fused_results.append({
                'content': content,
                'fused_score': fused_score,
                'vector_score': result['vector_score'],
                'keyword_score': result['keyword_score'],
                'vector_rank': result['vector_rank'],
                'keyword_rank': result['keyword_rank'],
                'matched_keywords': result['matched_keywords'],
                'source': result['source']
            })
        
        # 按融合分数排序
        fused_results.sort(key=lambda x: x['fused_score'], reverse=True)
        
        # 添加最终排名
        for i, result in enumerate(fused_results):
            result['final_rank'] = i + 1
        
        return fused_results[:top_k]
    
    def _record_search(self, query: str, results: List[Dict]):
        """记录检索历史"""
        search_record = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'result_count': len(results),
            'query_hash': hashlib.md5(query.encode()).hexdigest()
        }
        
        # 添加到历史记录
        self.search_history.append(search_record)
        
        # 保持历史记录数量限制（最多1000条）
        if len(self.search_history) > 1000:
            self.search_history = self.search_history[-1000:]
        
        # 保存历史记录
        self._save_history()
    
    def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """获取搜索建议"""
        if not partial_query or len(partial_query) < 2:
            return []
        
        suggestions = []
        partial_lower = partial_query.lower()
        
        # 从历史记录中查找相似查询
        for record in reversed(self.search_history):
            query = record['query']
            if partial_lower in query.lower() and query not in suggestions:
                suggestions.append(query)
                if len(suggestions) >= limit:
                    break
        
        return suggestions
    
    def get_search_history(self, limit: int = 20) -> List[Dict]:
        """获取检索历史"""
        return self.search_history[-limit:]
    
    def clear_search_history(self):
        """清空检索历史"""
        self.search_history = []
        self._save_history()
    
    def export_results(self, results: List[Dict], format: str = 'json', 
                      file_path: Optional[str] = None) -> Optional[str]:
        """
        导出检索结果
        
        :param results: 检索结果
        :param format: 导出格式 ('json', 'txt', 'csv')
        :param file_path: 导出文件路径
        :return: 导出文件路径
        """
        if not file_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = f"search_results_{timestamp}.{format}"
        
        try:
            if format == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            
            elif format == 'txt':
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"检索结果导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"结果数量: {len(results)}\n\n")
                    
                    for i, result in enumerate(results, 1):
                        f.write(f"=== 结果 {i} ===\n")
                        f.write(f"分数: {result.get('fused_score', 0):.4f}\n")
                        f.write(f"来源: {result.get('source', 'unknown')}\n")
                        f.write(f"匹配关键词: {', '.join(result.get('matched_keywords', []))}\n")
                        f.write(f"内容: {result['content'][:200]}...\n\n")
            
            elif format == 'csv':
                import csv
                with open(file_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['排名', '分数', '来源', '匹配关键词', '内容'])
                    
                    for i, result in enumerate(results, 1):
                        writer.writerow([
                            i,
                            f"{result.get('fused_score', 0):.4f}",
                            result.get('source', 'unknown'),
                            ', '.join(result.get('matched_keywords', [])),
                            result['content'][:100] + '...' if len(result['content']) > 100 else result['content']
                        ])
            
            print(f"[enhanced_retriever] 结果已导出到: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"[enhanced_retriever] 导出失败: {e}")
            return None


def create_enhanced_retriever(history_file: str = "search_history.json") -> EnhancedRetriever:
    """
    创建增强检索器实例
    
    :param history_file: 检索历史文件路径
    :return: 增强检索器实例
    """
    return EnhancedRetriever(history_file) 