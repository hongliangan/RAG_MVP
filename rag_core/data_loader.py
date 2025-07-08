import os
from typing import List, Generator

import config

def load_documents(directory: str) -> Generator[str, None, None]:
    """
    从指定目录加载所有文档内容。

    Args:
        directory (str): 文档所在的目录路径。

    Yields:
        Generator[str, None, None]: 每个文档的内容。
    """
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    yield f.read()
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

def split_into_chunks(text: str) -> List[str]:
    """
    将文本内容按双换行符分割成块。

    Args:
        text (str): 要分割的文本。

    Returns:
        List[str]: 分割后的文本块列表。
    """
    return [chunk.strip() for chunk in text.split('\n\n') if chunk.strip()]


def load_and_chunk_documents() -> List[str]:
    """
    加载并分割所有文档。

    Returns:
        List[str]: 所有文档分割后的文本块列表。
    """
    chunks = []
    for content in load_documents(config.DOCUMENTS_DIR):
        chunks.extend(split_into_chunks(content))
    return chunks