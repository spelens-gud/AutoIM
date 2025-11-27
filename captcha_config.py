"""验证码处理配置。

可以通过修改这个文件来调整滑动速度和行为。
"""

# 滑动速度配置
CAPTCHA_CONFIG = {
    # 轨迹生成参数
    "track": {
        "time_interval": 0.1,  # 时间间隔，越小速度越快（0.05-0.2）
        "acceleration_min": 5,  # 加速阶段最小加速度（2-10）
        "acceleration_max": 8,  # 加速阶段最大加速度（5-15）
        "deceleration_min": 3,  # 减速阶段最小加速度（2-8）
        "deceleration_max": 6,  # 减速阶段最大加速度（4-10）
        "min_move": 2,  # 每次最小移动距离（1-5）
        "acceleration_ratio": 0.8,  # 加速阶段占比（0.7-0.9）
    },
    
    # 滑动执行参数
    "slide": {
        "move_to_delay_min": 0.05,  # 移动到滑块的延迟最小值（0.01-0.2）
        "move_to_delay_max": 0.1,   # 移动到滑块的延迟最大值（0.05-0.3）
        "hold_delay_min": 0.1,      # 按住滑块的延迟最小值（0.05-0.3）
        "hold_delay_max": 0.15,     # 按住滑块的延迟最大值（0.1-0.5）
        "move_delay_min": 0.001,    # 每次移动的延迟最小值（0.001-0.01）
        "move_delay_max": 0.002,    # 每次移动的延迟最大值（0.002-0.02）
        "shake_count_min": 1,       # 抖动次数最小值（0-3）
        "shake_count_max": 2,       # 抖动次数最大值（1-5）
        "shake_range": 2,           # 抖动范围（1-5）
        "shake_delay_min": 0.005,   # 抖动延迟最小值（0.001-0.02）
        "shake_delay_max": 0.01,    # 抖动延迟最大值（0.005-0.05）
        "release_delay_min": 0.1,   # 释放前延迟最小值（0.05-0.5）
        "release_delay_max": 0.2,   # 释放前延迟最大值（0.1-0.8）
    },
    
    # 重试配置
    "retry": {
        "max_attempts": 3,  # 最大尝试次数（1-5）
        "retry_delay": 1,   # 重试间隔秒数（0.5-3）
    },
}


# 预设配置
PRESETS = {
    # 极速模式（可能被识别为机器人）
    "fast": {
        "track": {
            "time_interval": 0.05,
            "acceleration_min": 8,
            "acceleration_max": 12,
            "deceleration_min": 5,
            "deceleration_max": 8,
            "min_move": 3,
            "acceleration_ratio": 0.85,
        },
        "slide": {
            "move_to_delay_min": 0.01,
            "move_to_delay_max": 0.05,
            "hold_delay_min": 0.05,
            "hold_delay_max": 0.1,
            "move_delay_min": 0.0005,
            "move_delay_max": 0.001,
            "shake_count_min": 0,
            "shake_count_max": 1,
            "shake_range": 1,
            "shake_delay_min": 0.001,
            "shake_delay_max": 0.005,
            "release_delay_min": 0.05,
            "release_delay_max": 0.1,
        },
    },
    
    # 平衡模式（推荐）
    "balanced": {
        "track": {
            "time_interval": 0.1,
            "acceleration_min": 5,
            "acceleration_max": 8,
            "deceleration_min": 3,
            "deceleration_max": 6,
            "min_move": 2,
            "acceleration_ratio": 0.8,
        },
        "slide": {
            "move_to_delay_min": 0.05,
            "move_to_delay_max": 0.1,
            "hold_delay_min": 0.1,
            "hold_delay_max": 0.15,
            "move_delay_min": 0.001,
            "move_delay_max": 0.002,
            "shake_count_min": 1,
            "shake_count_max": 2,
            "shake_range": 2,
            "shake_delay_min": 0.005,
            "shake_delay_max": 0.01,
            "release_delay_min": 0.1,
            "release_delay_max": 0.2,
        },
    },
    
    # 安全模式（更像人类，但速度较慢）
    "safe": {
        "track": {
            "time_interval": 0.2,
            "acceleration_min": 2,
            "acceleration_max": 5,
            "deceleration_min": 2,
            "deceleration_max": 4,
            "min_move": 1,
            "acceleration_ratio": 0.75,
        },
        "slide": {
            "move_to_delay_min": 0.1,
            "move_to_delay_max": 0.2,
            "hold_delay_min": 0.2,
            "hold_delay_max": 0.3,
            "move_delay_min": 0.002,
            "move_delay_max": 0.005,
            "shake_count_min": 2,
            "shake_count_max": 4,
            "shake_range": 3,
            "shake_delay_min": 0.01,
            "shake_delay_max": 0.03,
            "release_delay_min": 0.2,
            "release_delay_max": 0.4,
        },
    },
}


def get_config(preset="balanced"):
    """获取配置。
    
    Args:
        preset: 预设名称，可选 "fast", "balanced", "safe"
        
    Returns:
        配置字典
    """
    if preset in PRESETS:
        config = CAPTCHA_CONFIG.copy()
        config.update(PRESETS[preset])
        return config
    return CAPTCHA_CONFIG


def print_config(preset="balanced"):
    """打印配置信息。"""
    config = get_config(preset)
    
    print(f"\n配置模式: {preset}")
    print("=" * 60)
    
    print("\n轨迹生成参数:")
    for key, value in config["track"].items():
        print(f"  {key}: {value}")
    
    print("\n滑动执行参数:")
    for key, value in config["slide"].items():
        print(f"  {key}: {value}")
    
    print("\n重试配置:")
    for key, value in config["retry"].items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n可用的预设配置:")
    print("1. fast - 极速模式（可能被识别为机器人）")
    print("2. balanced - 平衡模式（推荐）")
    print("3. safe - 安全模式（更像人类，但速度较慢）")
    
    for preset in ["fast", "balanced", "safe"]:
        print_config(preset)
