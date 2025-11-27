"""账号工作进程模块。

每个账号在独立进程中运行，负责该账号的消息收发。
"""

import time
import multiprocessing as mp
from datetime import datetime
from typing import Optional, Dict, List

from src.utils.logger import setup_logging, get_logger
from src.utils.exceptions import WangWangRPAException


def account_worker_process(
    account_id: str,
    account_name: str,
    config_path: str,
    cookies: Optional[List[Dict]],
    user_data_dir: str,
    headless: bool,
    send_queue: mp.Queue,
    receive_queue: mp.Queue,
    control_queue: mp.Queue,
    status_queue: mp.Queue
):
    """账号工作进程函数。
    
    在独立进程中运行，管理单个账号的RPA实例。
    
    Args:
        account_id: 账号ID
        account_name: 账号名称
        config_path: 配置文件路径
        cookies: Cookie列表
        user_data_dir: 浏览器用户数据目录
        headless: 是否使用无头模式
        send_queue: 发送消息队列
        receive_queue: 接收消息队列
        control_queue: 控制命令队列
        status_queue: 状态报告队列
    """
    # 设置进程日志
    setup_logging()
    logger = get_logger(f"worker.{account_id}")
    
    logger.info(f"=" * 60)
    logger.info(f"账号工作进程启动: {account_name} ({account_id})")
    logger.info(f"=" * 60)
    
    rpa_instance = None
    is_running = True
    message_count = 0
    error_count = 0
    
    try:
        # 延迟导入，避免循环导入
        from src.rpa import WangWangRPA
        
        # 初始化RPA实例
        logger.info("初始化RPA实例...")
        rpa_instance = WangWangRPA(config_path=config_path, cookies=cookies)
        
        # 覆盖配置
        rpa_instance.config.browser_headless = headless
        rpa_instance.config.browser_user_data_dir = user_data_dir
        rpa_instance.browser.headless = headless
        rpa_instance.browser.user_data_dir = user_data_dir
        
        # 启动RPA
        logger.info("启动RPA系统...")
        rpa_instance.start()
        
        # 报告启动成功
        status_queue.put({
            "account_id": account_id,
            "status": "running",
            "message": "RPA系统启动成功",
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info("进入消息处理循环...")
        
        # 主循环
        while is_running:
            try:
                # 检查控制命令
                try:
                    command = control_queue.get_nowait()
                    if command == "stop":
                        logger.info("收到停止命令")
                        is_running = False
                        break
                except:
                    pass
                
                # 处理发送消息任务
                try:
                    task = send_queue.get(timeout=0.5)
                    if task:
                        logger.info(f"处理发送任务 - 联系人: {task.contact_id}, 内容: {task.content[:30]}...")
                        
                        try:
                            success = rpa_instance.message_handler.send_message(
                                contact_id=task.contact_id,
                                content=task.content,
                                retry_times=task.retry_times,
                                retry_delay=task.retry_delay
                            )
                            
                            if success:
                                message_count += 1
                                logger.info(f"✓ 消息发送成功")
                            else:
                                error_count += 1
                                logger.error(f"✗ 消息发送失败")
                        except Exception as e:
                            error_count += 1
                            logger.error(f"发送消息异常: {str(e)}")
                except:
                    pass
                
                # 检查新消息
                try:
                    new_messages = rpa_instance.message_handler.check_new_messages()
                    
                    if new_messages:
                        logger.info(f"收到 {len(new_messages)} 条新消息")
                        
                        for msg in new_messages:
                            # 添加账号信息
                            msg.account_id = account_id
                            
                            # 放入接收队列
                            try:
                                receive_queue.put_nowait(msg)
                                message_count += 1
                            except:
                                logger.error("接收队列已满，消息被丢弃")
                except Exception as e:
                    logger.error(f"检查消息异常: {str(e)}")
                
                # 定期报告状态（每30秒）
                if int(time.time()) % 30 == 0:
                    status_queue.put({
                        "account_id": account_id,
                        "status": "running",
                        "message_count": message_count,
                        "error_count": error_count,
                        "timestamp": datetime.now().isoformat()
                    })
                
                # 短暂休眠
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"主循环异常: {str(e)}")
                error_count += 1
                time.sleep(5)
        
        logger.info("退出消息处理循环")
        
    except WangWangRPAException as e:
        logger.error(f"RPA系统错误: {str(e)}")
        status_queue.put({
            "account_id": account_id,
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"工作进程异常: {str(e)}", exc_info=True)
        status_queue.put({
            "account_id": account_id,
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        })
    finally:
        # 清理资源
        if rpa_instance:
            try:
                logger.info("停止RPA实例...")
                rpa_instance.stop()
            except Exception as e:
                logger.error(f"停止RPA实例失败: {str(e)}")
        
        # 报告停止状态
        status_queue.put({
            "account_id": account_id,
            "status": "stopped",
            "message_count": message_count,
            "error_count": error_count,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"=" * 60)
        logger.info(f"账号工作进程退出: {account_name} ({account_id})")
        logger.info(f"消息总数: {message_count}, 错误次数: {error_count}")
        logger.info(f"=" * 60)
