"""自动回复引擎测试。"""

import pytest
import yaml
from pathlib import Path
from src.core.auto_reply_engine import AutoReplyEngine
from src.utils.exceptions import ConfigException


class TestAutoReplyEngine:
    """测试AutoReplyEngine类的所有功能。"""
    
    @pytest.fixture
    def temp_rules_file(self, tmp_path):
        """创建临时规则文件。"""
        rules_file = tmp_path / "test_rules.yaml"
        rules_data = {
            'rules': [
                {
                    'keywords': ['价格', '多少钱'],
                    'reply': '请查看商品详情页'
                },
                {
                    'keywords': ['发货', '什么时候发'],
                    'reply': '48小时内发货'
                },
                {
                    'keywords': ['退货', '退款'],
                    'reply': '请联系售后客服'
                }
            ]
        }
        with open(rules_file, 'w', encoding='utf-8') as f:
            yaml.dump(rules_data, f, allow_unicode=True)
        return rules_file
    
    @pytest.fixture
    def engine(self, temp_rules_file):
        """创建自动回复引擎实例。"""
        return AutoReplyEngine(str(temp_rules_file))
    
    def test_init(self, temp_rules_file):
        """测试初始化。"""
        engine = AutoReplyEngine(str(temp_rules_file))
        assert engine.rules_file == Path(temp_rules_file)
        assert engine.rules == []
    
    def test_load_rules_success(self, engine):
        """测试成功加载规则。"""
        engine.load_rules()
        assert len(engine.rules) == 3
        assert engine.rules[0].keywords == ['价格', '多少钱']
        assert engine.rules[0].reply == '请查看商品详情页'
    
    def test_load_rules_file_not_exist(self, tmp_path):
        """测试规则文件不存在。"""
        engine = AutoReplyEngine(str(tmp_path / "nonexistent.yaml"))
        with pytest.raises(ConfigException, match="规则文件不存在"):
            engine.load_rules()
    
    def test_load_rules_invalid_format(self, tmp_path):
        """测试无效的规则文件格式。"""
        rules_file = tmp_path / "invalid.yaml"
        with open(rules_file, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: content:")
        
        engine = AutoReplyEngine(str(rules_file))
        with pytest.raises(ConfigException, match="解析YAML文件失败"):
            engine.load_rules()
    
    def test_load_rules_missing_rules_field(self, tmp_path):
        """测试缺少rules字段。"""
        rules_file = tmp_path / "no_rules.yaml"
        with open(rules_file, 'w', encoding='utf-8') as f:
            yaml.dump({'other': 'data'}, f)
        
        engine = AutoReplyEngine(str(rules_file))
        with pytest.raises(ConfigException, match="缺少 'rules' 字段"):
            engine.load_rules()
    
    def test_match_rule_success(self, engine):
        """测试成功匹配规则。"""
        engine.load_rules()
        
        # 测试匹配第一个关键词
        reply = engine.match_rule("这个商品价格是多少？")
        assert reply == '请查看商品详情页'
        
        # 测试匹配第二个关键词
        reply = engine.match_rule("请问多少钱？")
        assert reply == '请查看商品详情页'
    
    def test_match_rule_case_insensitive(self, engine):
        """测试关键词匹配不区分大小写。"""
        engine.load_rules()
        
        reply = engine.match_rule("这个商品价格是多少？")
        assert reply == '请查看商品详情页'
        
        reply = engine.match_rule("这个商品价格是多少？")
        assert reply == '请查看商品详情页'
    
    def test_match_rule_no_match(self, engine):
        """测试没有匹配的规则。"""
        engine.load_rules()
        
        reply = engine.match_rule("这是一个随机的问题")
        assert reply is None
    
    def test_match_rule_empty_message(self, engine):
        """测试空消息。"""
        engine.load_rules()
        
        reply = engine.match_rule("")
        assert reply is None
    
    def test_match_rule_first_match_wins(self, engine):
        """测试按顺序匹配，返回第一个匹配的规则。"""
        engine.load_rules()
        
        # 消息同时包含多个关键词，应返回第一个匹配的规则
        reply = engine.match_rule("请问价格和发货时间")
        assert reply == '请查看商品详情页'  # 第一个规则
    
    def test_add_rule(self, engine):
        """测试动态添加规则。"""
        engine.load_rules()
        initial_count = len(engine.rules)
        
        engine.add_rule(['测试', 'test'], '这是测试回复')
        assert len(engine.rules) == initial_count + 1
        
        # 验证新规则可以匹配
        reply = engine.match_rule("这是一个测试消息")
        assert reply == '这是测试回复'
    
    def test_add_rule_invalid(self, engine):
        """测试添加无效规则。"""
        with pytest.raises(ValueError):
            engine.add_rule([], '回复内容')  # 空关键词列表
        
        with pytest.raises(ValueError):
            engine.add_rule(['关键词'], '')  # 空回复内容
    
    def test_get_rules_count(self, engine):
        """测试获取规则数量。"""
        assert engine.get_rules_count() == 0
        
        engine.load_rules()
        assert engine.get_rules_count() == 3
        
        engine.add_rule(['新关键词'], '新回复')
        assert engine.get_rules_count() == 4
    
    def test_clear_rules(self, engine):
        """测试清空规则。"""
        engine.load_rules()
        assert engine.get_rules_count() > 0
        
        engine.clear_rules()
        assert engine.get_rules_count() == 0
        assert engine.rules == []
