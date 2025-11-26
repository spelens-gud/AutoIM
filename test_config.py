"""测试配置文件是否正确加载。"""

from src.utils.config_manager import ConfigManager
from src.core.auto_reply_engine import AutoReplyEngine


def test_config():
    """测试配置加载。"""
    print("=" * 60)
    print("测试配置文件加载")
    print("=" * 60)
    
    try:
        # 加载配置
        config_manager = ConfigManager("config/config.yaml")
        config = config_manager.load_config()
        
        print(f"✓ 配置加载成功")
        print(f"  - 旺旺URL: {config.wangwang_url}")
        print(f"  - 检查间隔: {config.check_interval}秒")
        print(f"  - 无头模式: {config.browser_headless}")
        print(f"  - 自动回复: {'启用' if config.auto_reply_enabled else '禁用'}")
        print()
        
        # 测试自动回复引擎
        if config.auto_reply_enabled:
            print("=" * 60)
            print("测试自动回复规则")
            print("=" * 60)
            
            engine = AutoReplyEngine(config.auto_reply_rules_file)
            engine.load_rules()
            
            print(f"✓ 成功加载 {engine.get_rules_count()} 条规则")
            print()
            
            # 测试几个关键词匹配
            test_messages = [
                "你好，在吗？",
                "这个产品多少钱？",
                "起订量是多少？",
                "可以寄样品吗？",
                "支持定制吗？",
                "什么时候发货？",
            ]
            
            print("测试关键词匹配：")
            for msg in test_messages:
                reply = engine.match_rule(msg)
                if reply:
                    print(f"  消息: {msg}")
                    print(f"  回复: {reply[:50]}...")
                    print()
                else:
                    print(f"  消息: {msg}")
                    print(f"  回复: 无匹配规则")
                    print()
        
        print("=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_config()
