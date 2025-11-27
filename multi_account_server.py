"""多账号旺旺RPA Web API 服务。

提供多账号管理的 RESTful API 接口。
"""

import argparse
import sys
import yaml
from pathlib import Path
from typing import Optional, List, Dict

from flask import Flask, request, jsonify
from flask_cors import CORS

from src.core.multi_account_manager import MultiAccountManager
from src.models.account import Account
from src.utils.logger import setup_logging, get_logger

# 初始化日志
setup_logging()
logger = get_logger(__name__)

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局多账号管理器实例
manager: Optional[MultiAccountManager] = None


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口。"""
    return jsonify({
        "status": "ok",
        "service": "多账号旺旺RPA API"
    })


@app.route('/api/accounts', methods=['GET'])
def list_accounts():
    """获取所有账号列表。"""
    try:
        if not manager:
            return jsonify({
                "success": False,
                "message": "管理器未初始化"
            }), 400
        
        accounts = manager.get_all_accounts_status()
        
        return jsonify({
            "success": True,
            "data": {
                "count": len(accounts),
                "accounts": accounts
            }
        })
    except Exception as e:
        logger.error(f"获取账号列表失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取账号列表失败: {str(e)}"
        }), 500


@app.route('/api/accounts/<account_id>', methods=['GET'])
def get_account(account_id):
    """获取指定账号信息。"""
    try:
        if not manager:
            return jsonify({
                "success": False,
                "message": "管理器未初始化"
            }), 400
        
        account = manager.get_account_status(account_id)
        
        if not account:
            return jsonify({
                "success": False,
                "message": f"账号 {account_id} 不存在"
            }), 404
        
        return jsonify({
            "success": True,
            "data": account
        })
    except Exception as e:
        logger.error(f"获取账号信息失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取账号信息失败: {str(e)}"
        }), 500


@app.route('/api/accounts/<account_id>/start', methods=['POST'])
def start_account(account_id):
    """启动指定账号。"""
    try:
        if not manager:
            return jsonify({
                "success": False,
                "message": "管理器未初始化"
            }), 400
        
        success = manager.start_account(account_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"账号 {account_id} 启动成功"
            })
        else:
            return jsonify({
                "success": False,
                "message": f"账号 {account_id} 启动失败"
            }), 500
    except Exception as e:
        logger.error(f"启动账号失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"启动账号失败: {str(e)}"
        }), 500


@app.route('/api/accounts/<account_id>/stop', methods=['POST'])
def stop_account(account_id):
    """停止指定账号。"""
    try:
        if not manager:
            return jsonify({
                "success": False,
                "message": "管理器未初始化"
            }), 400
        
        success = manager.stop_account(account_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"账号 {account_id} 停止成功"
            })
        else:
            return jsonify({
                "success": False,
                "message": f"账号 {account_id} 停止失败"
            }), 500
    except Exception as e:
        logger.error(f"停止账号失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"停止账号失败: {str(e)}"
        }), 500


@app.route('/api/accounts/start-all', methods=['POST'])
def start_all_accounts():
    """启动所有账号。"""
    try:
        if not manager:
            return jsonify({
                "success": False,
                "message": "管理器未初始化"
            }), 400
        
        results = manager.start_all_accounts()
        
        success_count = sum(1 for v in results.values() if v)
        
        return jsonify({
            "success": True,
            "message": f"启动完成，成功: {success_count}/{len(results)}",
            "data": results
        })
    except Exception as e:
        logger.error(f"启动所有账号失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"启动所有账号失败: {str(e)}"
        }), 500


@app.route('/api/accounts/stop-all', methods=['POST'])
def stop_all_accounts():
    """停止所有账号。"""
    try:
        if not manager:
            return jsonify({
                "success": False,
                "message": "管理器未初始化"
            }), 400
        
        results = manager.stop_all_accounts()
        
        success_count = sum(1 for v in results.values() if v)
        
        return jsonify({
            "success": True,
            "message": f"停止完成，成功: {success_count}/{len(results)}",
            "data": results
        })
    except Exception as e:
        logger.error(f"停止所有账号失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"停止所有账号失败: {str(e)}"
        }), 500


@app.route('/api/message/send', methods=['POST'])
def send_message():
    """通过指定账号发送消息。
    
    Request Body:
        {
            "account_id": "账号ID",
            "contact_id": "联系人ID",
            "content": "消息内容",
            "retry_times": 2,
            "retry_delay": 1
        }
    """
    try:
        if not manager:
            return jsonify({
                "success": False,
                "message": "管理器未初始化"
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "缺少请求数据"
            }), 400
        
        account_id = data.get('account_id')
        contact_id = data.get('contact_id')
        content = data.get('content')
        retry_times = data.get('retry_times', 2)
        retry_delay = data.get('retry_delay', 1)
        
        if not account_id or not contact_id or not content:
            return jsonify({
                "success": False,
                "message": "缺少必需参数: account_id, contact_id, content"
            }), 400
        
        success = manager.send_message(
            account_id=account_id,
            contact_id=contact_id,
            content=content,
            retry_times=retry_times,
            retry_delay=retry_delay
        )
        
        if success:
            return jsonify({
                "success": True,
                "message": "消息已加入发送队列"
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
            "message": f"发送消息失败: {str(e)}"
        }), 500


@app.route('/api/message/receive', methods=['GET'])
def receive_messages():
    """获取所有账号接收到的消息。
    
    Query Parameters:
        max_count: 最多获取的消息数量（默认100）
    """
    try:
        if not manager:
            return jsonify({
                "success": False,
                "message": "管理器未初始化"
            }), 400
        
        max_count = request.args.get('max_count', 100, type=int)
        
        messages = manager.get_received_messages(max_count=max_count)
        
        # 转换为字典格式
        messages_data = []
        for msg in messages:
            messages_data.append({
                "message_id": msg.message_id,
                "account_id": getattr(msg, 'account_id', 'unknown'),
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
        logger.error(f"获取消息失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取消息失败: {str(e)}"
        }), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取统计信息。"""
    try:
        if not manager:
            return jsonify({
                "success": False,
                "message": "管理器未初始化"
            }), 400
        
        stats = manager.get_statistics()
        
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取统计信息失败: {str(e)}"
        }), 500


def load_accounts_from_config(config_file: str) -> List[Account]:
    """从配置文件加载账号列表。
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        账号列表
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        accounts = []
        accounts_config = config.get('accounts', [])
        
        for acc_cfg in accounts_config:
            account = Account(
                account_id=acc_cfg['id'],
                account_name=acc_cfg['name'],
                cookie_file=acc_cfg.get('cookie_file', ''),
                user_data_dir=acc_cfg['user_data_dir'],
                cookies=acc_cfg.get('cookies'),
                enabled=acc_cfg.get('enabled', True),
                metadata=acc_cfg.get('metadata', {})
            )
            accounts.append(account)
        
        logger.info(f"从配置文件加载了 {len(accounts)} 个账号")
        return accounts
    except Exception as e:
        logger.error(f"加载账号配置失败: {str(e)}")
        return []


def parse_arguments():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="多账号旺旺RPA Web API 服务",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config/multi_account_config.yaml",
        help="多账号配置文件路径"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=5002,
        help="API服务端口（默认: 5002）"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="API服务监听地址（默认: 0.0.0.0）"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="使用无头模式运行浏览器"
    )
    
    parser.add_argument(
        "--auto-start",
        action="store_true",
        help="自动启动所有账号"
    )
    
    return parser.parse_args()


def main():
    """启动多账号API服务。"""
    global manager
    
    # 解析命令行参数
    args = parse_arguments()
    
    print("\n" + "=" * 60)
    print("多账号旺旺RPA Web API 服务")
    print("=" * 60)
    print(f"API地址: http://localhost:{args.port}")
    print(f"配置文件: {args.config}")
    print(f"无头模式: {'是' if args.headless else '否'}")
    print("=" * 60 + "\n")
    
    try:
        # 初始化多账号管理器
        logger.info("初始化多账号管理器...")
        manager = MultiAccountManager(
            config_path="config/config.yaml",
            headless=args.headless
        )
        
        # 加载账号配置
        if Path(args.config).exists():
            logger.info(f"加载账号配置: {args.config}")
            accounts = load_accounts_from_config(args.config)
            
            for account in accounts:
                manager.add_account(account)
            
            print(f"✓ 已加载 {len(accounts)} 个账号")
        else:
            logger.warning(f"配置文件不存在: {args.config}")
            print(f"⚠️  配置文件不存在: {args.config}")
            print("   将以空账号列表启动，请通过API添加账号")
        
        # 自动启动所有账号
        if args.auto_start:
            print("\n正在启动所有账号...")
            results = manager.start_all_accounts()
            success_count = sum(1 for v in results.values() if v)
            print(f"✓ 启动完成，成功: {success_count}/{len(results)}\n")
        
        print("API服务启动中...\n")
        
        # 启动Flask应用
        app.run(
            host=args.host,
            port=args.port,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在停止...")
        print("\n\n👋 正在停止服务...")
        
        # 停止所有账号
        if manager:
            try:
                manager.stop_all_accounts()
            except Exception as e:
                logger.error(f"停止账号时出错: {str(e)}")
        
        print("服务已停止\n")
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}", exc_info=True)
        print(f"\n❌ 服务启动失败: {str(e)}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
