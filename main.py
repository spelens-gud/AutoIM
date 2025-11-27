"""旺旺RPA系统主入口。

提供命令行接口，启动和管理RPA系统。
"""

import argparse
import os
import sys
from pathlib import Path

from src.rpa import WangWangRPA
from src.utils.exceptions import WangWangRPAException
from src.utils.logger import setup_logging, get_logger


def parse_arguments():
    """解析命令行参数。
    
    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        description="旺旺RPA系统 - 自动化旺旺消息收发工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 使用默认配置启动（显示浏览器窗口）
  python main.py
  
  # 使用无头模式启动（后台运行）
  python main.py --headless
  
  # 指定配置文件
  python main.py --config custom_config.yaml
  
  # 设置日志级别
  python main.py --log-level DEBUG
        """
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="使用无头模式运行浏览器（后台运行，不显示窗口）"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="配置文件路径（默认: config/config.yaml）"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="日志级别（会覆盖配置文件中的设置）"
    )

    parser.add_argument(
        "--cookies",
        type=str,
        help="手动配置Cookie（JSON格式字符串或文件路径）。"
             "示例: --cookies '[{\"name\":\"_tb_token_\",\"value\":\"xxx\",\"domain\":\".1688.com\"}]' "
             "或 --cookies cookies.json"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="旺旺RPA系统 v1.0.0"
    )

    return parser.parse_args()


def print_welcome():
    """打印欢迎信息。"""
    welcome_text = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              旺旺RPA自动化系统 v1.0.0                      ║
║                                                           ║
║         自动监控和回复旺旺消息，提升客服效率               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(welcome_text)


def check_environment():
    """检查运行环境。
    
    检查必要的目录和文件是否存在。
    """
    # 确保必要的目录存在
    directories = ["config", "logs", "browser_data"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    # 检查配置文件
    if not os.path.exists("config/config.yaml"):
        print("   警告: 未找到配置文件 config/config.yaml")
        print("   系统将使用默认配置创建配置文件")


def main():
    """主入口函数。
    
    解析命令行参数，初始化并启动RPA系统。
    """
    # 解析命令行参数
    args = parse_arguments()

    # 打印欢迎信息
    print_welcome()

    # 检查运行环境
    check_environment()

    # 设置日志系统
    log_level = args.log_level if args.log_level else None
    setup_logging(level=log_level)
    logger = get_logger(__name__)

    logger.info("旺旺RPA系统启动中...")
    logger.info(f"配置文件: {args.config}")
    logger.info(f"无头模式: {'是' if args.headless else '否'}")

    # 解析Cookie参数
    cookies = None
    if args.cookies:
        try:
            import json
            import os

            # 检查是否是文件路径
            if os.path.isfile(args.cookies):
                logger.info(f"从文件加载Cookie: {args.cookies}")
                with open(args.cookies, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
            else:
                # 尝试解析为JSON字符串
                logger.info("解析Cookie JSON字符串")
                cookies = json.loads(args.cookies)

            if not isinstance(cookies, list):
                logger.error("Cookie必须是一个列表")
                print("错误: Cookie格式不正确，必须是一个列表")
                sys.exit(1)

            logger.info(f"成功解析 {len(cookies)} 个Cookie")

        except json.JSONDecodeError as e:
            logger.error(f"Cookie JSON解析失败: {e}")
            print(f"错误: Cookie JSON格式不正确: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"加载Cookie失败: {e}")
            print(f"错误: 加载Cookie失败: {e}")
            sys.exit(1)

    rpa = None

    try:
        # 初始化RPA控制器
        rpa = WangWangRPA(config_path=args.config, cookies=cookies)

        # 如果命令行指定了无头模式，覆盖配置文件设置
        if args.headless:
            logger.info("命令行参数指定使用无头模式")
            rpa.config.browser_headless = True
            rpa.browser.headless = True

        # 启动RPA系统
        rpa.start()

        # 运行消息监控循环
        rpa.run()

    except WangWangRPAException as e:
        logger.error(f"RPA系统错误: {str(e)}")
        print(f"\n错误: {str(e)}")
        print("请检查日志文件获取详细信息")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("接收到用户中断信号")
        print("\n\n用户中断，正在退出...")

    except Exception as e:
        logger.error(f"未预期的错误: {str(e)}", exc_info=True)
        print(f"\n发生未预期的错误: {str(e)}")
        print("请检查日志文件获取详细信息")
        sys.exit(1)

    finally:
        # 清理资源
        if rpa:
            try:
                rpa.stop()
            except Exception as e:
                logger.error(f"清理资源时出错: {str(e)}")

        print("\n" + "=" * 60)
        print("感谢使用旺旺RPA系统！")
        print("=" * 60)
        logger.info("系统已完全退出")


if __name__ == "__main__":
    main()
