"""向指定店铺发送消息并监测回复的示例脚本。

使用方法:
    python send_to_shop.py --shop "店铺名称" --message "你好，请问有货吗？"
"""

import argparse
import sys
import time

from src.core.browser_controller import BrowserController
from src.core.message_handler import MessageHandler
from src.utils.config_manager import ConfigManager
from src.utils.logger import setup_logging, get_logger


def parse_arguments():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="向指定店铺发送消息并监测回复",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 向店铺发送消息并等待回复
  python send_to_shop.py --shop "某某旗舰店" --message "你好，请问有货吗？"
  
  # 只发送消息，不等待回复
  python send_to_shop.py --shop "某某旗舰店" --message "你好" --no-wait
  
  # 设置等待回复的超时时间
  python send_to_shop.py --shop "某某旗舰店" --message "你好" --timeout 120
        """
    )

    parser.add_argument(
        "--shop",
        type=str,
        required=True,
        help="店铺名称"
    )

    parser.add_argument(
        "--message",
        type=str,
        required=True,
        help="要发送的消息内容"
    )

    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="不等待回复，发送后立即退出"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="等待回复的超时时间（秒），默认60秒"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="配置文件路径（默认: config/config.yaml）"
    )

    return parser.parse_args()


def main():
    """主函数。"""
    # 解析命令行参数
    args = parse_arguments()

    # 设置日志
    setup_logging()
    logger = get_logger(__name__)

    print("\n" + "=" * 60)
    print("旺旺主动发送消息工具")
    print("=" * 60)
    print(f"目标店铺: {args.shop}")
    print(f"消息内容: {args.message}")
    print(f"等待回复: {'否' if args.no_wait else '是'}")
    if not args.no_wait:
        print(f"超时时间: {args.timeout}秒")
    print("=" * 60 + "\n")

    browser = None
    
    try:
        # 加载配置
        logger.info("加载配置...")
        config_manager = ConfigManager(args.config)
        config = config_manager.load_config()

        # 初始化浏览器控制器
        logger.info("启动浏览器...")
        browser = BrowserController(
            headless=config.browser_headless,
            user_data_dir=config.browser_user_data_dir
        )
        browser.start()

        # 导航到旺旺页面
        logger.info(f"导航到旺旺页面: {config.wangwang_url}")
        browser.navigate_to(config.wangwang_url)

        # 等待页面加载
        time.sleep(3)

        # 检查登录状态
        logger.info("检查登录状态...")
        if not browser.is_logged_in():
            print("\n⚠️  检测到未登录状态")
            print("请在浏览器中手动完成登录操作")
            print("登录完成后按回车继续...")
            input()

        # 初始化消息处理器
        logger.info("初始化消息处理器...")
        message_handler = MessageHandler(browser)

        # 发送消息
        logger.info(f"向店铺 {args.shop} 发送消息...")
        print(f"\n📤 正在发送消息到店铺: {args.shop}")
        
        # 使用店铺名称作为 contact_id
        contact_id = args.shop
        
        success = message_handler.send_message(
            contact_id=contact_id,
            content=args.message,
            retry_times=2,
            retry_delay=1
        )
        
        if not success:
            logger.error("发送消息失败")
            print("\n❌ 发送消息失败")
            return
        
        print(f"✅ 消息已发送: {args.message}")
        
        # 等待回复
        replies = []
        if not args.no_wait:
            logger.info(f"等待回复（超时: {args.timeout}秒）...")
            print(f"\n⏳ 等待店铺回复（超时: {args.timeout}秒）...\n")
            
            start_time = time.time()
            
            while time.time() - start_time < args.timeout:
                # 检查新消息
                new_messages = message_handler.check_new_messages()
                
                if new_messages:
                    for message in new_messages:
                        # 只处理接收到的消息（不是自己发送的）
                        if not message.is_sent:
                            logger.info(f"收到回复: {message.content[:50]}...")
                            replies.append(message)
                            
                            # 打印回复
                            print("=" * 60)
                            print(f"📨 收到回复:")
                            print(f"   来自: {message.contact_name}")
                            print(f"   时间: {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                            print(f"   内容: {message.content}")
                            print("=" * 60 + "\n")
                
                # 等待一段时间再检查
                time.sleep(2)
            
            if not replies:
                logger.warning("等待超时，未收到回复")
                print(f"⚠️  在 {args.timeout} 秒内未收到回复")

        # 输出结果摘要
        print("\n" + "=" * 60)
        print("执行结果:")
        print("=" * 60)
        print(f"✅ 消息已发送到店铺: {args.shop}")
        
        if not args.no_wait:
            if replies:
                print(f"✅ 收到 {len(replies)} 条回复")
            else:
                print(f"⚠️  未收到回复")
        
        print("=" * 60 + "\n")

    except KeyboardInterrupt:
        logger.info("用户中断")
        print("\n\n👋 用户中断，正在退出...")

    except Exception as e:
        logger.error(f"发生错误: {str(e)}", exc_info=True)
        print(f"\n❌ 错误: {str(e)}")
        sys.exit(1)

    finally:
        # 清理资源
        if browser:
            try:
                print("\n正在关闭浏览器...")
                browser.stop()
            except Exception as e:
                logger.error(f"关闭浏览器时出错: {str(e)}")

        print("感谢使用！\n")


if __name__ == "__main__":
    main()
