"""多账号管理器模块。

管理多个账号的生命周期，协调消息路由和状态监控。
"""

import time
import multiprocessing as mp
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from src.models.account import Account, AccountStatus
from src.core.account_worker import account_worker_process
from src.core.message_router import MessageRouter, MessageTask
from src.models.message import Message
from src.utils.logger import get_logger
from src.utils.exceptions import WangWangRPAException

logger = get_logger(__name__)


class MultiAccountManager:
    """多账号管理器类。
    
    使用多进程模式管理多个旺旺账号，每个账号运行在独立进程中。
    
    Attributes:
        accounts: 账号字典，key为账号ID
        processes: 进程字典，key为账号ID
        message_router: 消息路由器
        config_path: 配置文件路径
        headless: 是否使用无头模式
    """
    
    def __init__(self, config_path: str = "config/config.yaml", headless: bool = False):
        """初始化多账号管理器。
        
        Args:
            config_path: 配置文件路径
            headless: 是否使用无头模式
        """
        self.accounts: Dict[str, Account] = {}
        self.processes: Dict[str, mp.Process] = {}
        self.send_queues: Dict[str, mp.Queue] = {}
        self.control_queues: Dict[str, mp.Queue] = {}
        self.receive_queue: mp.Queue = mp.Queue(maxsize=10000)
        self.status_queue: mp.Queue = mp.Queue(maxsize=1000)
        
        self.message_router = MessageRouter(max_queue_size=1000)
        self.config_path = config_path
        self.headless = headless
        self.is_running = False
        
        logger.info("多账号管理器初始化完成")
    
    def add_account(self, account: Account) -> bool:
        """添加账号到管理器。
        
        Args:
            account: 账号对象
            
        Returns:
            True表示添加成功，False表示失败
        """
        if account.account_id in self.accounts:
            logger.warning(f"账号 {account.account_id} 已存在")
            return False
        
        # 确保用户数据目录存在
        Path(account.user_data_dir).mkdir(parents=True, exist_ok=True)
        
        self.accounts[account.account_id] = account
        self.message_router.register_account(account.account_id)
        
        logger.info(f"添加账号: {account.account_name} ({account.account_id})")
        return True
    
    def remove_account(self, account_id: str) -> bool:
        """从管理器中移除账号。
        
        Args:
            account_id: 账号ID
            
        Returns:
            True表示移除成功，False表示失败
        """
        if account_id not in self.accounts:
            logger.warning(f"账号 {account_id} 不存在")
            return False
        
        # 如果账号正在运行，先停止
        if account_id in self.processes:
            self.stop_account(account_id)
        
        # 移除账号
        account = self.accounts.pop(account_id)
        self.message_router.unregister_account(account_id)
        
        logger.info(f"移除账号: {account.account_name} ({account_id})")
        return True
    
    def start_account(self, account_id: str) -> bool:
        """启动指定账号。
        
        Args:
            account_id: 账号ID
            
        Returns:
            True表示启动成功，False表示失败
        """
        if account_id not in self.accounts:
            logger.error(f"账号 {account_id} 不存在")
            return False
        
        account = self.accounts[account_id]
        
        if not account.enabled:
            logger.warning(f"账号 {account.account_name} 未启用")
            return False
        
        if account_id in self.processes and self.processes[account_id].is_alive():
            logger.warning(f"账号 {account.account_name} 已在运行中")
            return False
        
        try:
            logger.info(f"启动账号: {account.account_name} ({account_id})")
            
            # 更新状态
            account.status = AccountStatus.STARTING
            account.last_active_time = datetime.now()
            
            # 创建队列
            send_queue = mp.Queue(maxsize=1000)
            control_queue = mp.Queue()
            
            self.send_queues[account_id] = send_queue
            self.control_queues[account_id] = control_queue
            
            # 创建并启动进程
            process = mp.Process(
                target=account_worker_process,
                args=(
                    account.account_id,
                    account.account_name,
                    self.config_path,
                    account.cookies,
                    account.user_data_dir,
                    self.headless,
                    send_queue,
                    self.receive_queue,
                    control_queue,
                    self.status_queue
                ),
                name=f"worker-{account_id}"
            )
            
            process.start()
            self.processes[account_id] = process
            account.process_id = process.pid
            
            logger.info(f"账号 {account.account_name} 启动成功，进程ID: {process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"启动账号 {account.account_name} 失败: {str(e)}")
            account.status = AccountStatus.ERROR
            account.last_error = str(e)
            account.error_count += 1
            return False
    
    def stop_account(self, account_id: str, timeout: int = 30) -> bool:
        """停止指定账号。
        
        Args:
            account_id: 账号ID
            timeout: 等待超时时间（秒）
            
        Returns:
            True表示停止成功，False表示失败
        """
        if account_id not in self.accounts:
            logger.error(f"账号 {account_id} 不存在")
            return False
        
        account = self.accounts[account_id]
        
        if account_id not in self.processes:
            logger.warning(f"账号 {account.account_name} 未运行")
            account.status = AccountStatus.STOPPED
            return True
        
        try:
            logger.info(f"停止账号: {account.account_name} ({account_id})")
            
            # 更新状态
            account.status = AccountStatus.STOPPING
            
            # 发送停止命令
            process = self.processes[account_id]
            if process.is_alive():
                self.control_queues[account_id].put("stop")
                
                # 等待进程结束
                process.join(timeout=timeout)
                
                # 如果进程仍在运行，强制终止
                if process.is_alive():
                    logger.warning(f"账号 {account.account_name} 未在超时时间内停止，强制终止")
                    process.terminate()
                    process.join(timeout=5)
                    
                    if process.is_alive():
                        logger.error(f"账号 {account.account_name} 无法终止，强制杀死")
                        process.kill()
                        process.join()
            
            # 清理资源
            del self.processes[account_id]
            del self.send_queues[account_id]
            del self.control_queues[account_id]
            
            account.status = AccountStatus.STOPPED
            account.process_id = None
            
            logger.info(f"账号 {account.account_name} 已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止账号 {account.account_name} 失败: {str(e)}")
            account.status = AccountStatus.ERROR
            account.last_error = str(e)
            return False
    
    def start_all_accounts(self) -> Dict[str, bool]:
        """启动所有已启用的账号。
        
        Returns:
            账号ID到启动结果的映射字典
        """
        logger.info("启动所有账号...")
        results = {}
        
        for account_id, account in self.accounts.items():
            if account.enabled:
                results[account_id] = self.start_account(account_id)
                # 错开启动时间，避免资源竞争
                time.sleep(2)
            else:
                logger.info(f"跳过未启用的账号: {account.account_name}")
                results[account_id] = False
        
        return results
    
    def stop_all_accounts(self) -> Dict[str, bool]:
        """停止所有运行中的账号。
        
        Returns:
            账号ID到停止结果的映射字典
        """
        logger.info("停止所有账号...")
        results = {}
        
        for account_id in list(self.processes.keys()):
            results[account_id] = self.stop_account(account_id)
        
        return results
    
    def send_message(
        self,
        account_id: str,
        contact_id: str,
        content: str,
        retry_times: int = 2,
        retry_delay: int = 1
    ) -> bool:
        """通过指定账号发送消息。
        
        Args:
            account_id: 账号ID
            contact_id: 联系人ID
            content: 消息内容
            retry_times: 重试次数
            retry_delay: 重试延迟
            
        Returns:
            True表示消息已加入发送队列，False表示失败
        """
        if account_id not in self.accounts:
            logger.error(f"账号 {account_id} 不存在")
            return False
        
        if account_id not in self.send_queues:
            logger.error(f"账号 {account_id} 未运行")
            return False
        
        try:
            from src.core.message_router import MessageTask
            task = MessageTask(
                account_id=account_id,
                contact_id=contact_id,
                content=content,
                retry_times=retry_times,
                retry_delay=retry_delay
            )
            
            self.send_queues[account_id].put(task, timeout=5)
            logger.info(f"消息已加入发送队列 - 账号: {account_id}, 联系人: {contact_id}")
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {str(e)}")
            return False
    
    def get_received_messages(self, max_count: int = 100) -> List[Message]:
        """获取所有账号接收到的消息。
        
        Args:
            max_count: 最多获取的消息数量
            
        Returns:
            消息列表
        """
        messages = []
        
        try:
            for _ in range(max_count):
                try:
                    message = self.receive_queue.get_nowait()
                    messages.append(message)
                except:
                    break
        except Exception as e:
            logger.error(f"获取接收消息失败: {str(e)}")
        
        return messages
    
    def update_status(self) -> None:
        """更新所有账号的状态信息。"""
        try:
            while not self.status_queue.empty():
                try:
                    status_info = self.status_queue.get_nowait()
                    account_id = status_info.get("account_id")
                    
                    if account_id in self.accounts:
                        account = self.accounts[account_id]
                        
                        # 更新状态
                        status_str = status_info.get("status")
                        if status_str:
                            account.status = AccountStatus(status_str)
                        
                        # 更新消息计数
                        if "message_count" in status_info:
                            account.message_count = status_info["message_count"]
                        
                        # 更新错误计数
                        if "error_count" in status_info:
                            account.error_count = status_info["error_count"]
                        
                        # 更新错误信息
                        if status_str == "error" and "message" in status_info:
                            account.last_error = status_info["message"]
                        
                        # 更新活跃时间
                        account.last_active_time = datetime.now()
                        
                except:
                    break
        except Exception as e:
            logger.error(f"更新状态失败: {str(e)}")
    
    def get_account_status(self, account_id: str) -> Optional[Dict]:
        """获取指定账号的状态信息。
        
        Args:
            account_id: 账号ID
            
        Returns:
            账号状态字典，如果账号不存在则返回None
        """
        if account_id not in self.accounts:
            return None
        
        account = self.accounts[account_id]
        return account.to_dict()
    
    def get_all_accounts_status(self) -> List[Dict]:
        """获取所有账号的状态信息。
        
        Returns:
            账号状态列表
        """
        # 先更新状态
        self.update_status()
        
        return [account.to_dict() for account in self.accounts.values()]
    
    def get_statistics(self) -> Dict:
        """获取统计信息。
        
        Returns:
            统计信息字典
        """
        total_accounts = len(self.accounts)
        running_accounts = sum(1 for a in self.accounts.values() if a.status == AccountStatus.RUNNING)
        total_messages = sum(a.message_count for a in self.accounts.values())
        total_errors = sum(a.error_count for a in self.accounts.values())
        
        return {
            "total_accounts": total_accounts,
            "running_accounts": running_accounts,
            "stopped_accounts": total_accounts - running_accounts,
            "total_messages": total_messages,
            "total_errors": total_errors,
            "receive_queue_size": self.receive_queue.qsize(),
            "timestamp": datetime.now().isoformat()
        }
