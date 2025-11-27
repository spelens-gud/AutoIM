"""消息路由器模块。

负责在多账号之间分发消息和聚合接收到的消息。
"""

import queue
import threading
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.models.message import Message
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MessageTask:
    """消息任务数据结构。
    
    Attributes:
        account_id: 目标账号ID
        contact_id: 联系人ID
        content: 消息内容
        retry_times: 重试次数
        retry_delay: 重试延迟
        task_id: 任务唯一标识
        created_at: 创建时间
    """
    account_id: str
    contact_id: str
    content: str
    retry_times: int = 2
    retry_delay: int = 1
    task_id: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        """初始化任务ID和创建时间。"""
        if self.task_id is None:
            import uuid
            self.task_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()


class MessageRouter:
    """消息路由器类。
    
    管理多账号之间的消息分发和聚合。
    
    Attributes:
        send_queues: 发送消息队列字典，key为账号ID
        receive_queue: 接收消息队列（所有账号共享）
        max_queue_size: 队列最大大小
    """
    
    def __init__(self, max_queue_size: int = 1000):
        """初始化消息路由器。
        
        Args:
            max_queue_size: 队列最大大小
        """
        self.send_queues: Dict[str, queue.Queue] = {}
        self.receive_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self.max_queue_size = max_queue_size
        self._lock = threading.Lock()
        
        logger.info(f"消息路由器初始化完成，队列大小: {max_queue_size}")
    
    def register_account(self, account_id: str) -> None:
        """注册账号，创建对应的发送队列。
        
        Args:
            account_id: 账号ID
        """
        with self._lock:
            if account_id not in self.send_queues:
                self.send_queues[account_id] = queue.Queue(maxsize=self.max_queue_size)
                logger.info(f"为账号 {account_id} 创建发送队列")
            else:
                logger.warning(f"账号 {account_id} 的发送队列已存在")
    
    def unregister_account(self, account_id: str) -> None:
        """注销账号，清理对应的发送队列。
        
        Args:
            account_id: 账号ID
        """
        with self._lock:
            if account_id in self.send_queues:
                # 清空队列
                try:
                    while not self.send_queues[account_id].empty():
                        self.send_queues[account_id].get_nowait()
                except queue.Empty:
                    pass
                
                del self.send_queues[account_id]
                logger.info(f"账号 {account_id} 的发送队列已清理")
            else:
                logger.warning(f"账号 {account_id} 的发送队列不存在")
    
    def send_message(
        self,
        account_id: str,
        contact_id: str,
        content: str,
        retry_times: int = 2,
        retry_delay: int = 1,
        timeout: Optional[float] = None
    ) -> bool:
        """发送消息到指定账号的队列。
        
        Args:
            account_id: 目标账号ID
            contact_id: 联系人ID
            content: 消息内容
            retry_times: 重试次数
            retry_delay: 重试延迟
            timeout: 超时时间（秒），None表示阻塞等待
            
        Returns:
            True表示成功加入队列，False表示失败
        """
        if account_id not in self.send_queues:
            logger.error(f"账号 {account_id} 未注册")
            return False
        
        task = MessageTask(
            account_id=account_id,
            contact_id=contact_id,
            content=content,
            retry_times=retry_times,
            retry_delay=retry_delay
        )
        
        try:
            if timeout is None:
                self.send_queues[account_id].put(task)
            else:
                self.send_queues[account_id].put(task, timeout=timeout)
            
            logger.debug(f"消息任务已加入队列 - 账号: {account_id}, 联系人: {contact_id}")
            return True
        except queue.Full:
            logger.error(f"账号 {account_id} 的发送队列已满")
            return False
    
    def get_send_task(self, account_id: str, timeout: Optional[float] = 1.0) -> Optional[MessageTask]:
        """从指定账号的发送队列获取消息任务。
        
        Args:
            account_id: 账号ID
            timeout: 超时时间（秒），None表示阻塞等待
            
        Returns:
            消息任务对象，如果队列为空则返回None
        """
        if account_id not in self.send_queues:
            logger.error(f"账号 {account_id} 未注册")
            return None
        
        try:
            task = self.send_queues[account_id].get(timeout=timeout)
            return task
        except queue.Empty:
            return None
    
    def receive_message(self, message: Message, account_id: str) -> bool:
        """接收消息并加入接收队列。
        
        Args:
            message: 消息对象
            account_id: 来源账号ID
            
        Returns:
            True表示成功加入队列，False表示失败
        """
        try:
            # 在消息中添加账号信息
            if not hasattr(message, 'account_id'):
                message.account_id = account_id
            
            self.receive_queue.put_nowait(message)
            logger.debug(f"收到消息 - 账号: {account_id}, 联系人: {message.contact_name}")
            return True
        except queue.Full:
            logger.error("接收队列已满，消息被丢弃")
            return False
    
    def get_received_messages(self, max_count: int = 100, timeout: float = 0.1) -> List[Message]:
        """获取接收到的消息列表。
        
        Args:
            max_count: 最多获取的消息数量
            timeout: 每次获取的超时时间（秒）
            
        Returns:
            消息列表
        """
        messages = []
        
        for _ in range(max_count):
            try:
                message = self.receive_queue.get(timeout=timeout)
                messages.append(message)
            except queue.Empty:
                break
        
        if messages:
            logger.debug(f"获取到 {len(messages)} 条接收消息")
        
        return messages
    
    def get_queue_status(self) -> Dict:
        """获取所有队列的状态信息。
        
        Returns:
            队列状态字典
        """
        status = {
            "receive_queue_size": self.receive_queue.qsize(),
            "send_queues": {}
        }
        
        for account_id, send_queue in self.send_queues.items():
            status["send_queues"][account_id] = {
                "size": send_queue.qsize(),
                "max_size": self.max_queue_size
            }
        
        return status
    
    def clear_all_queues(self) -> None:
        """清空所有队列。"""
        logger.info("清空所有消息队列")
        
        # 清空接收队列
        try:
            while not self.receive_queue.empty():
                self.receive_queue.get_nowait()
        except queue.Empty:
            pass
        
        # 清空所有发送队列
        for account_id in list(self.send_queues.keys()):
            try:
                while not self.send_queues[account_id].empty():
                    self.send_queues[account_id].get_nowait()
            except queue.Empty:
                pass
        
        logger.info("所有消息队列已清空")
