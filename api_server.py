"""旺旺RPA Web API 服务。

提供 RESTful API 接口,用于控制旺旺RPA系统。
支持两种模式：
1. 仅API模式：只启动API服务,通过API接口控制RPA
2. 集成模式：同时启动API服务和RPA系统
"""

import argparse
import sys
import threading
import time
from datetime import datetime
from typing import Optional

from flask import Flask, request, jsonify
from flask_cors import CORS

from src.rpa import WangWangRPA
from src.utils.cookie_parser import parse_cookie_string, validate_cookies
from src.utils.logger import setup_logging, get_logger

# 初始化日志
setup_logging()
logger = get_logger(__name__)

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局 RPA 实例
rpa_instance: Optional[WangWangRPA] = None
rpa_thread: Optional[threading.Thread] = None
is_running = False


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口。
    
    Returns:
        JSON响应，包含服务状态
    """
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "旺旺RPA API"
    })


@app.route('/api/rpa/start', methods=['POST'])
def start_rpa():
    """启动RPA系统。
    
    Request Body:
        {
            "config_path": "config/config.yaml",  # 可选，配置文件路径
            "headless": false,  # 可选，是否使用无头模式
            "cookies": [  # 可选，手动配置的Cookie列表（字典格式）
                {
                    "name": "_tb_token_",
                    "value": "xxx",
                    "domain": ".1688.com"
                }
            ],
            "cookie_string": "cookie2=xxx; t=yyy; _tb_token_=zzz"  # 可选，Cookie字符串格式
        }
    
    Request Headers:
        Cookie: cookie2=xxx; t=yyy; _tb_token_=zzz  # 可选，从请求头中读取Cookie
    
    Returns:
        JSON响应,包含启动结果
    """
    global rpa_instance, rpa_thread, is_running

    try:
        if is_running:
            return jsonify({
                "success": False,
                "message": "RPA系统已经在运行中"
            }), 400

        # 获取请求参数
        data = request.get_json() or {}
        config_path = data.get('config_path', 'config/config.yaml')
        headless = data.get('headless', False)
        cookies = data.get('cookies', None)
        cookie_string = data.get('cookie_string', None)

        logger.info(f"启动RPA系统 - 配置: {config_path}, 无头模式: {headless}")

        # 优先级：cookies > cookie_string > 请求头Cookie
        if cookies is None:
            # 尝试从cookie_string解析
            if cookie_string:
                try:
                    logger.info("从cookie_string参数解析Cookie")
                    cookies = parse_cookie_string(cookie_string.__str__())
                except Exception as e:
                    return jsonify({
                        "success": False,
                        "message": f"解析cookie_string失败: {str(e)}",
                        "error_type": "invalid_cookie_string"
                    }), 400
            # 尝试从请求头解析
            elif 'Cookie' in request.headers:
                try:
                    cookie_header = request.headers.get('Cookie')
                    logger.info("从请求头Cookie解析")
                    cookies = parse_cookie_string(cookie_header)
                except Exception as e:
                    return jsonify({
                        "success": False,
                        "message": f"解析请求头Cookie失败: {str(e)}",
                        "error_type": "invalid_cookie_header"
                    }), 400

        # 验证Cookie格式
        if cookies is not None:
            if not isinstance(cookies, list):
                return jsonify({
                    "success": False,
                    "message": "cookies参数必须是一个列表",
                    "error_type": "invalid_parameter"
                }), 400

            logger.info(f"使用手动配置的Cookie（共 {len(cookies)} 个）")

            # 验证Cookie有效性
            if not validate_cookies(cookies):
                logger.warning("Cookie验证失败，但仍会尝试使用")

        # 初始化RPA实例
        rpa_instance = WangWangRPA(config_path=config_path, cookies=cookies)

        if headless:
            rpa_instance.config.browser_headless = True
            rpa_instance.browser.headless = True

        # 启动RPA系统(包括登录检查)
        try:
            rpa_instance.start()
        except Exception as start_error:
            if rpa_instance and rpa_instance.browser:
                rpa_instance.browser.stop()
            rpa_instance = None

            # 检查是否是登录相关错误
            error_msg = str(start_error)
            if "登录" in error_msg or "cookie" in error_msg.lower():
                return jsonify({
                    "success": False,
                    "message": f"登录失败: {error_msg}",
                    "error_type": "login_failed"
                }), 401
            else:
                return jsonify({
                    "success": False,
                    "message": f"启动失败: {error_msg}",
                    "error_type": "startup_failed"
                }), 500

        # 在后台线程中运行消息监控
        def run_rpa():
            global is_running
            is_running = True
            try:
                rpa_instance.run()
            except Exception as e:
                logger.error(f"RPA运行错误: {str(e)}")
            finally:
                is_running = False

        rpa_thread = threading.Thread(target=run_rpa, daemon=True)
        rpa_thread.start()

        logger.info("RPA系统启动成功")

        return jsonify({
            "success": True,
            "message": "RPA系统启动成功",
            "config": {
                "config_path": config_path,
                "headless": headless
            }
        })

    except Exception as e:
        logger.error(f"启动RPA系统失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"启动失败: {str(e)}",
            "error_type": "unknown_error"
        }), 500


@app.route('/api/rpa/stop', methods=['POST'])
def stop_rpa():
    """停止RPA系统。
    
    Returns:
        JSON响应，包含停止结果
    """
    global rpa_instance, is_running

    try:
        if not is_running or not rpa_instance:
            return jsonify({
                "success": False,
                "message": "RPA系统未运行"
            }), 400

        logger.info("停止RPA系统")

        # 停止RPA
        rpa_instance.stop()
        is_running = False

        logger.info("RPA系统已停止")

        return jsonify({
            "success": True,
            "message": "RPA系统已停止"
        })

    except Exception as e:
        logger.error(f"停止RPA系统失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"停止失败: {str(e)}"
        }), 500


@app.route('/api/rpa/status', methods=['GET'])
def get_status():
    """获取RPA系统状态。
    
    Returns:
        JSON响应，包含系统状态信息
    """
    global rpa_instance, is_running

    try:
        if not rpa_instance:
            return jsonify({
                "success": True,
                "data": {
                    "is_running": False,
                    "message": "RPA系统未初始化"
                }
            })

        status = rpa_instance.get_status()
        status['is_running'] = is_running

        return jsonify({
            "success": True,
            "data": status
        })

    except Exception as e:
        logger.error(f"获取状态失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取状态失败: {str(e)}"
        }), 500


@app.route('/api/message/send', methods=['POST'])
def send_message():
    """发送消息到指定联系人。
    
    Request Body:
        {
            "contact_id": "店铺名称或联系人ID",
            "content": "消息内容",
            "retry_times": 2,  # 可选，重试次数
            "retry_delay": 1   # 可选，重试延迟（秒）
        }
    
    Returns:
        JSON响应，包含发送结果
    """
    global rpa_instance

    try:
        if not rpa_instance:
            return jsonify({
                "success": False,
                "message": "RPA系统未启动"
            }), 400

        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "缺少请求数据"
            }), 400

        contact_id = data.get('contact_id')
        content = data.get('content')
        retry_times = data.get('retry_times', 2)
        retry_delay = data.get('retry_delay', 1)

        if not contact_id or not content:
            return jsonify({
                "success": False,
                "message": "缺少必需参数: contact_id 和 content"
            }), 400

        logger.info(f"发送消息到 {contact_id}: {content[:50]}...")

        # 发送消息
        success = rpa_instance.message_handler.send_message(
            contact_id=contact_id,
            content=content,
            retry_times=retry_times,
            retry_delay=retry_delay
        )

        if success:
            return jsonify({
                "success": True,
                "message": "消息发送成功",
                "data": {
                    "contact_id": contact_id,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                }
            })
        else:
            return jsonify({
                "success": False,
                "message": "消息发送失败"
            }), 500

    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"发送失败: {str(e)}"
        }), 500


@app.route('/api/message/check', methods=['GET'])
def check_messages():
    """检查新消息。
    
    Returns:
        JSON响应，包含新消息列表
    """
    global rpa_instance

    try:
        if not rpa_instance:
            return jsonify({
                "success": False,
                "message": "RPA系统未启动"
            }), 400

        logger.debug("检查新消息")

        # 检查新消息
        new_messages = rpa_instance.message_handler.check_new_messages()

        # 转换为字典格式
        messages_data = []
        for msg in new_messages:
            messages_data.append({
                "message_id": msg.message_id,
                "contact_id": msg.contact_id,
                "contact_name": msg.contact_name,
                "content": msg.content,
                "message_type": msg.message_type,
                "timestamp": msg.timestamp.isoformat(),
                "is_sent": msg.is_sent
            })

        return jsonify({
            "success": True,
            "data": {
                "count": len(messages_data),
                "messages": messages_data
            }
        })

    except Exception as e:
        logger.error(f"检查消息失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"检查消息失败: {str(e)}"
        }), 500


@app.route('/api/message/history/<contact_id>', methods=['GET'])
def get_chat_history(contact_id):
    """获取与指定联系人的聊天记录。
    
    Path Parameters:
        contact_id: 联系人ID或联系人名称
    
    Query Parameters:
        max_messages: 最多获取的消息数量（默认100）
    
    Returns:
        JSON响应，包含聊天消息列表
    """
    global rpa_instance

    try:
        if not rpa_instance:
            return jsonify({
                "success": False,
                "message": "RPA系统未启动"
            }), 400

        # 获取查询参数
        max_messages = request.args.get('max_messages', 100, type=int)

        # 验证参数
        if max_messages < 1 or max_messages > 500:
            return jsonify({
                "success": False,
                "message": "max_messages 参数必须在 1-500 之间"
            }), 400

        logger.info(f"获取联系人 {contact_id} 的聊天记录（最多 {max_messages} 条）")

        # 获取聊天消息
        messages = rpa_instance.message_handler.get_chat_messages(
            contact_id=contact_id,
            max_messages=max_messages
        )

        # 转换为字典格式
        messages_data = []
        for msg in messages:
            messages_data.append({
                "message_id": msg.message_id,
                "contact_id": msg.contact_id,
                "contact_name": msg.contact_name,
                "content": msg.content,
                "message_type": msg.message_type,
                "timestamp": msg.timestamp.isoformat(),
                "is_sent": msg.is_sent
            })

        return jsonify({
            "success": True,
            "data": {
                "contact_id": contact_id,
                "count": len(messages_data),
                "messages": messages_data
            }
        })

    except Exception as e:
        logger.error(f"获取聊天记录失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取聊天记录失败: {str(e)}"
        }), 500


@app.route('/api/session/list', methods=['GET'])
def list_sessions():
    """获取会话列表。
    
    Query Parameters:
        active_only: 是否只返回活跃会话（true/false）
    
    Returns:
        JSON响应，包含会话列表
    """
    global rpa_instance

    try:
        if not rpa_instance:
            return jsonify({
                "success": False,
                "message": "RPA系统未启动"
            }), 400

        active_only = request.args.get('active_only', 'false').lower() == 'true'

        logger.debug(f"获取会话列表 - 仅活跃: {active_only}")

        # 获取会话列表
        if active_only:
            sessions = rpa_instance.session_manager.get_active_sessions()
        else:
            sessions = rpa_instance.session_manager.get_all_sessions()

        # 转换为字典格式
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                "contact_id": session.contact_id,
                "contact_name": session.contact_name,
                "last_message_time": session.last_message_time.isoformat() if session.last_message_time else None,
                "last_activity_time": session.last_activity_time.isoformat(),
                "message_count": session.message_count,
                "is_active": session.is_active
            })

        return jsonify({
            "success": True,
            "data": {
                "count": len(sessions_data),
                "sessions": sessions_data
            }
        })

    except Exception as e:
        logger.error(f"获取会话列表失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取会话列表失败: {str(e)}"
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404错误处理。"""
    return jsonify({
        "success": False,
        "message": "接口不存在"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理。"""
    return jsonify({
        "success": False,
        "message": "服务器内部错误"
    }), 500


def parse_arguments():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="旺旺RPA Web API 服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 仅启动API服务（通过API接口控制RPA）
  python api_server.py
  
  # 启动API服务并自动启动RPA系统
  python api_server.py --auto-start
  
  # 启动API服务并自动启动RPA（无头模式）
  python api_server.py --auto-start --headless
  
  # 指定配置文件和端口
  python api_server.py --auto-start --config custom_config.yaml --port 8080
        """
    )

    parser.add_argument(
        "--auto-start",
        action="store_true",
        help="自动启动RPA系统（默认只启动API服务）"
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="使用无头模式运行浏览器（配合 --auto-start 使用）"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="配置文件路径（默认: config/config.yaml）"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=5001,
        help="API服务端口（默认: 5001）"
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="API服务监听地址（默认: 0.0.0.0）"
    )

    parser.add_argument(
        "--cookies",
        type=str,
        help="手动配置Cookie（JSON格式字符串或文件路径，配合 --auto-start 使用）"
    )

    return parser.parse_args()


def auto_start_rpa_system(config_path: str, headless: bool, cookies: Optional[list] = None):
    """自动启动RPA系统。
    
    Args:
        config_path: 配置文件路径
        headless: 是否使用无头模式
        cookies: 可选的Cookie列表
    """
    global rpa_instance, rpa_thread, is_running

    try:
        logger.info("自动启动RPA系统...")
        print("\n" + "=" * 60)
        print("正在自动启动RPA系统...")
        print("=" * 60)

        # 初始化RPA实例
        rpa_instance = WangWangRPA(config_path=config_path, cookies=cookies)

        if headless:
            rpa_instance.config.browser_headless = True
            rpa_instance.browser.headless = True

        # 启动RPA系统
        rpa_instance.start()

        # 在后台线程中运行消息监控
        def run_rpa():
            global is_running
            is_running = True
            try:
                rpa_instance.run()
            except Exception as e:
                logger.error(f"RPA运行错误: {str(e)}")
            finally:
                is_running = False

        rpa_thread = threading.Thread(target=run_rpa, daemon=True)
        rpa_thread.start()

        logger.info("RPA系统自动启动成功")
        print("RPA系统已启动")
        print("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"自动启动RPA系统失败: {str(e)}")
        print(f"RPA系统启动失败: {str(e)}")
        print("API服务将继续运行，您可以稍后通过API手动启动RPA\n")


def main():
    """启动API服务。"""
    # 解析命令行参数
    args = parse_arguments()

    print("\n" + "=" * 60)
    print("旺旺RPA Web API 服务")
    print("=" * 60)
    print(f"API地址: http://localhost:{args.port}")
    print(f"健康检查: http://localhost:{args.port}/api/health")
    print(f"API文档: 查看 API.md")
    print("=" * 60)

    if args.auto_start:
        print(f"模式: 集成模式(API + RPA)")
        print(f"配置文件: {args.config}")
        print(f"无头模式: {'是' if args.headless else '否'}")

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
                    print("错误: Cookie格式不正确，必须是一个列表")
                    sys.exit(1)

                print(f"使用手动配置的Cookie（共 {len(cookies)} 个）")

            except json.JSONDecodeError as e:
                print(f"错误: Cookie JSON格式不正确: {e}")
                sys.exit(1)
            except Exception as e:
                print(f"错误: 加载Cookie失败: {e}")
                sys.exit(1)

        print("=" * 60)

        # 延迟启动RPA，让Flask先初始化
        def delayed_start():
            time.sleep(2)  # 等待Flask启动
            auto_start_rpa_system(args.config, args.headless, cookies)

        threading.Thread(target=delayed_start, daemon=True).start()
    else:
        print(f"模式: 仅API模式")
        print("提示: 使用 --auto-start 参数可以同时启动RPA系统")
        print("=" * 60)

    print("\n")

    # 启动Flask应用
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在停止...")
        print("\n\n正在停止服务...")

        # 停止RPA系统
        if rpa_instance and is_running:
            try:
                rpa_instance.stop()
            except Exception as e:
                logger.error(f"停止RPA时出错: {str(e)}")

        print("服务已停止\n")


if __name__ == '__main__':
    main()
