# RAG MVP 参数使用指南

本文档详细说明RAG系统中各个参数的作用、推荐值和注意事项，帮助用户更好地配置系统。

## 📄 文本切片参数

### 切片方式 (split_method)
- **选项**: `paragraph`（推荐）、`character`、`sentence`
- **说明**: 选择文档切片的策略
- **推荐**: 使用 `paragraph`，保持语义完整性

### 字符数切片参数
当选择 `character` 切片方式时使用：

#### 每块最大字符数 (chunk_size)
- **推荐范围**: 500-1000
- **默认值**: 800
- **说明**: 控制每个文本块的大小
- **注意事项**: 
  - 太小（<500）：可能丢失上下文信息
  - 太大（>1000）：可能包含无关信息，影响检索精度

#### 相邻块重叠字符数 (chunk_overlap)
- **推荐范围**: 50-200
- **默认值**: 100
- **说明**: 相邻文本块的重叠部分
- **注意事项**:
  - 太小（<50）：可能丢失跨块的重要信息
  - 太大（>200）：增加冗余，影响处理效率

### 句子切片参数
当选择 `sentence` 切片方式时使用：

#### 每块最大句子数 (max_sentences_per_chunk)
- **推荐范围**: 2-5
- **默认值**: 3
- **说明**: 每个文本块包含的最大句子数量
- **注意事项**:
  - 太少（<2）：信息可能不足
  - 太多（>5）：可能包含无关内容

### 段落切片参数
当选择 `paragraph` 切片方式时使用：

#### 最小段落长度 (min_paragraph_length)
- **推荐范围**: 20-100
- **默认值**: 30
- **说明**: 段落的最小字符数，低于此值的段落会被过滤
- **注意事项**: 太短可能信息不足

#### 最大段落长度 (max_paragraph_length)
- **推荐范围**: 1000-2000
- **默认值**: 1500
- **说明**: 段落的最大字符数，超过此值的段落会被进一步分割
- **注意事项**: 太长可能包含过多无关信息

## 🔍 检索参数

### 返回最相关片段数 (top_k)
- **推荐范围**: 1-10
- **默认值**: 5
- **说明**: 检索返回的最相关文档片段数量
- **注意事项**:
  - 数值越大返回结果越多，但可能包含不相关内容
  - 建议根据文档长度和问题复杂度调整

### 相似度阈值 (similarity_threshold)
- **推荐范围**: 0.0-0.8
- **默认值**: 0.1
- **说明**: 过滤低于此相似度值的文档片段
- **注意事项**:
  - 数值越高要求越严格，可能过滤掉相关内容
  - 0.0：不过滤，返回所有结果
  - 0.8：非常严格，只返回高度相关的内容

### 检索策略 (retrieval_strategy)
- **选项**: `cosine`（推荐）、`dot_product`、`euclidean`
- **默认值**: `cosine`
- **说明**: 计算文档相似度的方法
- **推荐**: 使用 `cosine`，通常效果最好

### 上下文窗口大小 (context_window)
- **推荐范围**: 0-3
- **默认值**: 1
- **说明**: 包含相邻文档片段作为上下文
- **注意事项**:
  - 0：不包含上下文
  - 1-3：包含相邻片段，增加上下文信息
  - 太大可能引入无关信息

### 去重策略 (deduplication)
- **选项**: `true`（推荐）、`false`
- **默认值**: `true`
- **说明**: 是否去除重复或高度相似的文档片段
- **推荐**: 启用，提高结果多样性

## ⚖️ 权重配置

### 文档长度权重 (length_weight)
- **选项**: 无偏好（推荐）、`prefer_long`、`prefer_short`
- **说明**: 对文档长度的偏好设置
- **使用场景**:
  - 无偏好：适用于大多数场景
  - `prefer_long`：需要详细信息时
  - `prefer_short`：需要简洁答案时

### 文档位置权重 (position_weight)
- **选项**: 无偏好（推荐）、`prefer_early`、`prefer_late`
- **说明**: 对文档位置的偏好设置
- **使用场景**:
  - 无偏好：适用于大多数场景
  - `prefer_early`：需要概述信息时
  - `prefer_late`：需要详细说明时

### 关键词权重 (keyword_weight)
- **格式**: 逗号分隔的关键词列表
- **示例**: `重要,关键,核心,总结`
- **说明**: 包含这些关键词的文档片段会获得更高权重
- **注意事项**: 留空则不使用关键词权重

## 🎯 参数调优建议

### 根据文档类型调整

#### 长文档（>10万字）
- `chunk_size`: 800-1000
- `top_k`: 5-8
- `similarity_threshold`: 0.1-0.2
- `context_window`: 1-2

#### 短文档（<1万字）
- `chunk_size`: 500-800
- `top_k`: 3-5
- `similarity_threshold`: 0.05-0.15
- `context_window`: 0-1

#### 技术文档
- `split_method`: `paragraph`
- `length_weight`: `prefer_long`
- `keyword_weight`: 添加技术术语

#### 新闻/文章
- `split_method`: `sentence`
- `position_weight`: `prefer_early`
- `deduplication`: `true`

### 根据问题类型调整

#### 事实性问题
- `similarity_threshold`: 0.2-0.3
- `top_k`: 3-5
- `retrieval_strategy`: `cosine`

#### 分析性问题
- `similarity_threshold`: 0.1-0.2
- `top_k`: 5-8
- `context_window`: 1-2

#### 总结性问题
- `similarity_threshold`: 0.05-0.15
- `top_k`: 8-10
- `position_weight`: `prefer_early`

## ⚠️ 常见问题

### 检索结果太少
- 降低 `similarity_threshold`
- 增加 `top_k`
- 检查 `deduplication` 设置

### 检索结果不相关
- 提高 `similarity_threshold`
- 减少 `top_k`
- 调整 `chunk_size`

### 处理速度慢
- 减少 `chunk_overlap`
- 降低 `context_window`
- 使用更小的 `chunk_size`

### 答案质量差
- 调整 `split_method`
- 优化 `weight_config`
- 检查文档预处理质量

## 📝 配置示例

### 快速开始配置
```bash
# 使用默认配置，适合大多数场景
export TEXT_SPLIT_METHOD=paragraph
export RETRIEVAL_TOP_K=5
export RETRIEVAL_SIMILARITY_THRESHOLD=0.1
export RETRIEVAL_CONTEXT_WINDOW=1
```

### 高精度配置
```bash
# 适合需要高精度答案的场景
export TEXT_SPLIT_METHOD=paragraph
export TEXT_CHUNK_SIZE=600
export RETRIEVAL_TOP_K=3
export RETRIEVAL_SIMILARITY_THRESHOLD=0.2
export RETRIEVAL_CONTEXT_WINDOW=0
```

### 高召回配置
```bash
# 适合需要全面信息的场景
export TEXT_SPLIT_METHOD=paragraph
export TEXT_CHUNK_SIZE=1000
export RETRIEVAL_TOP_K=8
export RETRIEVAL_SIMILARITY_THRESHOLD=0.05
export RETRIEVAL_CONTEXT_WINDOW=2
``` 