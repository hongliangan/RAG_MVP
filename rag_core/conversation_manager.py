"""
conversation_manager.py
多轮对话管理模块，支持会话管理、历史记录、上下文拼接等功能。
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Conversation:
    """
    对话会话类
    """

    def __init__(self, session_id: str, kb_name: str = "default"):
        """
        初始化对话会话

        :param session_id: 会话ID
        :param kb_name: 知识库名称
        """
        self.session_id = session_id
        self.kb_name = kb_name
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.messages: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {
            "title": f"对话 {session_id[:8]}",
            "total_messages": 0,
            "total_tokens": 0,
        }

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        添加消息到对话

        :param role: 角色 (user/assistant)
        :param content: 消息内容
        :param metadata: 额外元数据
        """
        message = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        self.messages.append(message)
        self.updated_at = datetime.now()
        self.metadata["total_messages"] = len(self.messages)

        # 更新标题（使用第一条用户消息）
        if role == "user" and self.metadata["title"].startswith("对话"):
            title = content[:50] + "..." if len(content) > 50 else content
            self.metadata["title"] = title

    def get_context(self, max_messages: int = 10, max_tokens: int = 2000) -> str:
        """
        获取对话上下文

        :param max_messages: 最大消息数量
        :param max_tokens: 最大token数量（估算）
        :return: 上下文字符串
        """
        if not self.messages:
            return ""

        # 获取最近的消息
        recent_messages = self.messages[-max_messages:]

        context_parts = []
        current_tokens = 0

        for message in recent_messages:
            content = message["content"]
            estimated_tokens = len(content) // 4  # 粗略估算

            if current_tokens + estimated_tokens > max_tokens:
                break

            role = "用户" if message["role"] == "user" else "助手"
            context_parts.append(f"{role}: {content}")
            current_tokens += estimated_tokens

        return "\n\n".join(context_parts)

    def get_last_user_message(self) -> Optional[str]:
        """获取最后一条用户消息"""
        for message in reversed(self.messages):
            if message["role"] == "user":
                return message["content"]
        return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "session_id": self.session_id,
            "kb_name": self.kb_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": self.messages,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """从字典创建对话对象"""
        conv = cls(data["session_id"], data["kb_name"])
        conv.created_at = datetime.fromisoformat(data["created_at"])
        conv.updated_at = datetime.fromisoformat(data["updated_at"])
        conv.messages = data["messages"]
        conv.metadata = data["metadata"]
        return conv


class ConversationManager:
    """
    对话管理器
    """

    def __init__(self, storage_path: str = "conversations"):
        """
        初始化对话管理器

        :param storage_path: 存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.active_conversations: Dict[str, Conversation] = {}

        logger.info(f"对话管理器初始化完成，存储路径: {self.storage_path}")

    def create_conversation(self, kb_name: str = "default") -> Conversation:
        """
        创建新对话

        :param kb_name: 知识库名称
        :return: 对话对象
        """
        session_id = str(uuid.uuid4())
        conversation = Conversation(session_id, kb_name)

        self.active_conversations[session_id] = conversation
        logger.info(f"创建新对话: {session_id} (知识库: {kb_name})")

        return conversation

    def get_conversation(self, session_id: str) -> Optional[Conversation]:
        """
        获取对话

        :param session_id: 会话ID
        :return: 对话对象或None
        """
        # 先从内存中查找
        if session_id in self.active_conversations:
            return self.active_conversations[session_id]

        # 从文件加载
        conversation = self._load_conversation(session_id)
        if conversation:
            self.active_conversations[session_id] = conversation

        return conversation

    def add_message(
        self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None
    ) -> bool:
        """
        添加消息到对话

        :param session_id: 会话ID
        :param role: 角色
        :param content: 内容
        :param metadata: 元数据
        :return: 是否成功
        """
        conversation = self.get_conversation(session_id)
        if not conversation:
            return False

        conversation.add_message(role, content, metadata)
        self._save_conversation(conversation)

        return True

    def get_conversation_context(
        self, session_id: str, max_messages: int = 10, max_tokens: int = 2000
    ) -> str:
        """
        获取对话上下文

        :param session_id: 会话ID
        :param max_messages: 最大消息数量
        :param max_tokens: 最大token数量
        :return: 上下文字符串
        """
        conversation = self.get_conversation(session_id)
        if not conversation:
            return ""

        return conversation.get_context(max_messages, max_tokens)

    def list_conversations(self, kb_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出对话列表

        :param kb_name: 知识库名称过滤
        :return: 对话列表
        """
        conversations = []

        # 扫描存储目录
        for file_path in self.storage_path.glob("*.json"):
            try:
                conversation = self._load_conversation_from_file(file_path)
                if conversation and (
                    kb_name is None or conversation.kb_name == kb_name
                ):
                    conversations.append(
                        {
                            "session_id": conversation.session_id,
                            "kb_name": conversation.kb_name,
                            "title": conversation.metadata.get("title", "未命名对话"),
                            "created_at": conversation.created_at.isoformat(),
                            "updated_at": conversation.updated_at.isoformat(),
                            "total_messages": conversation.metadata.get(
                                "total_messages", 0
                            ),
                        }
                    )
            except Exception as e:
                logger.error(f"加载对话文件失败 {file_path}: {e}")

        # 按更新时间排序
        conversations.sort(key=lambda x: x["updated_at"], reverse=True)

        return conversations

    def delete_conversation(self, session_id: str) -> bool:
        """
        删除对话

        :param session_id: 会话ID
        :return: 是否成功
        """
        try:
            # 从内存中移除
            if session_id in self.active_conversations:
                del self.active_conversations[session_id]

            # 删除文件
            file_path = self.storage_path / f"{session_id}.json"
            if file_path.exists():
                file_path.unlink()
                logger.info(f"删除对话: {session_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"删除对话失败 {session_id}: {e}")
            return False

    def clear_conversations(self, kb_name: Optional[str] = None) -> int:
        """
        清空对话

        :param kb_name: 知识库名称过滤
        :return: 删除的对话数量
        """
        deleted_count = 0

        for file_path in self.storage_path.glob("*.json"):
            try:
                conversation = self._load_conversation_from_file(file_path)
                if conversation and (
                    kb_name is None or conversation.kb_name == kb_name
                ):
                    file_path.unlink()
                    deleted_count += 1
            except Exception as e:
                logger.error(f"删除对话文件失败 {file_path}: {e}")

        # 清空内存中的对话
        if kb_name is None:
            self.active_conversations.clear()
        else:
            to_delete = [
                sid
                for sid, conv in self.active_conversations.items()
                if conv.kb_name == kb_name
            ]
            for sid in to_delete:
                del self.active_conversations[sid]

        logger.info(f"清空对话完成，删除 {deleted_count} 个对话")
        return deleted_count

    def export_conversation(
        self, session_id: str, format: str = "json"
    ) -> Optional[str]:
        """
        导出对话

        :param session_id: 会话ID
        :param format: 导出格式 (json/txt)
        :return: 导出内容或None
        """
        conversation = self.get_conversation(session_id)
        if not conversation:
            return None

        if format == "json":
            return json.dumps(conversation.to_dict(), ensure_ascii=False, indent=2)

        elif format == "txt":
            lines = [
                f"对话标题: {conversation.metadata.get('title', '未命名对话')}",
                f"知识库: {conversation.kb_name}",
                f"创建时间: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"更新时间: {conversation.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"消息数量: {len(conversation.messages)}",
                "",
                "=" * 50,
                "",
            ]

            for message in conversation.messages:
                role = "用户" if message["role"] == "user" else "助手"
                timestamp = datetime.fromisoformat(message["timestamp"]).strftime(
                    "%H:%M:%S"
                )
                lines.extend([f"[{timestamp}] {role}:", message["content"], ""])

            return "\n".join(lines)

        return None

    def _save_conversation(self, conversation: Conversation):
        """保存对话到文件"""
        try:
            file_path = self.storage_path / f"{conversation.session_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(conversation.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存对话失败 {conversation.session_id}: {e}")

    def _load_conversation(self, session_id: str) -> Optional[Conversation]:
        """从文件加载对话"""
        file_path = self.storage_path / f"{session_id}.json"
        return self._load_conversation_from_file(file_path)

    def _load_conversation_from_file(self, file_path: Path) -> Optional[Conversation]:
        """从文件加载对话"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Conversation.from_dict(data)
        except Exception as e:
            logger.error(f"加载对话文件失败 {file_path}: {e}")
            return None


# 全局对话管理器实例
conversation_manager = ConversationManager()


def get_conversation_manager() -> ConversationManager:
    """获取全局对话管理器实例"""
    return conversation_manager
