"""
模型点数配置
定义不同LLM模型分析时消耗的点数
同时支持研究深度级别（1-5级）的点数配置
"""

import json
from pathlib import Path
from typing import Dict, Tuple

# 配置文件路径
CONFIG_FILE = Path(__file__).parent.parent / "config" / "model_points.json"

# 默认模型点数配置表（当配置文件不存在时使用）
# 格式: (provider, model): points
DEFAULT_MODEL_POINTS_CONFIG = {
    # 阿里百炼 (DashScope)
    ("dashscope", "qwen-turbo"): 1,
    ("dashscope", "qwen-plus-latest"): 2,
    ("dashscope", "qwen-max"): 3,
    
    # DeepSeek
    ("deepseek", "deepseek-chat"): 1,
    
    # Google Gemini
    ("google", "gemini-2.5-pro"): 4,
    ("google", "gemini-2.5-flash"): 2,
    ("google", "gemini-2.5-flash-lite"): 1,
    ("google", "gemini-2.5-flash-lite-preview-06-17"): 1,
    ("google", "gemini-2.5-pro-002"): 4,
    ("google", "gemini-2.5-flash-002"): 2,
    ("google", "gemini-2.0-flash"): 2,
    ("google", "gemini-1.5-pro"): 3,
    ("google", "gemini-1.5-flash"): 1,
    
    # OpenAI
    ("openai", "gpt-4o"): 5,
    ("openai", "gpt-4o-mini"): 1,
    ("openai", "gpt-4-turbo"): 4,
    ("openai", "gpt-4"): 4,
    ("openai", "gpt-3.5-turbo"): 1,
    
    # OpenRouter (使用默认值，可在需要时扩展)
    ("openrouter", "default"): 2,
    
    # 硅基流动 (SiliconFlow)
    ("siliconflow", "Qwen/Qwen3-30B-A3B-Thinking-2507"): 3,
    ("siliconflow", "Qwen/Qwen3-30B-A3B-Instruct-2507"): 2,
    ("siliconflow", "Qwen/Qwen3-235B-A22B-Thinking-2507"): 5,
    ("siliconflow", "Qwen/Qwen3-235B-A22B-Instruct-2507"): 4,
    ("siliconflow", "deepseek-ai/DeepSeek-R1"): 3,
    ("siliconflow", "zai-org/GLM-4.5"): 3,
    ("siliconflow", "moonshotai/Kimi-K2-Instruct"): 2,
    
    # 自定义OpenAI端点
    ("custom_openai", "default"): 2,
    
    # 文心一言（千帆）
    ("qianfan", "default"): 2,
}

# 默认点数（当模型未配置时使用）
DEFAULT_POINTS = 1

# 研究深度点数配置表
# 格式: research_depth: points
# 1级最低，5级最高
DEFAULT_RESEARCH_DEPTH_POINTS_CONFIG = {
    1: 1,  # 1级 - 快速分析：最低成本
    2: 2,  # 2级 - 基础分析：较低成本
    3: 3,  # 3级 - 标准分析：中等成本
    4: 5,  # 4级 - 深度分析：较高成本
    5: 8,  # 5级 - 全面分析：最高成本
}


def _load_config() -> Dict[Tuple[str, str], int]:
    """
    从配置文件加载模型点数配置
    
    Returns:
        格式: {(provider, model): points}
    """
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 将JSON格式转换为字典格式
                config = {}
                for item in data.get('config', []):
                    provider = item.get('provider', '').lower().strip()
                    model = item.get('model', '').strip()
                    points = int(item.get('points', DEFAULT_POINTS))
                    config[(provider, model)] = points
                return config
    except Exception:
        pass
    
    # 如果加载失败，返回默认配置
    return DEFAULT_MODEL_POINTS_CONFIG.copy()


def _save_config(config: Dict[Tuple[str, str], int]) -> bool:
    """
    保存模型点数配置到文件
    
    Args:
        config: 格式: {(provider, model): points}
    
    Returns:
        是否保存成功
    """
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换为JSON格式
        data = {
            'version': '1.0',
            'default_points': DEFAULT_POINTS,
            'config': [
                {
                    'provider': provider,
                    'model': model,
                    'points': points
                }
                for (provider, model), points in sorted(config.items())
            ]
        }
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception:
        return False


# 全局配置缓存
_CONFIG_CACHE: Dict[Tuple[str, str], int] = None


def _get_config() -> Dict[Tuple[str, str], int]:
    """获取配置（带缓存）"""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        _CONFIG_CACHE = _load_config()
    return _CONFIG_CACHE


def reload_config():
    """重新加载配置（用于管理员修改配置后）"""
    global _CONFIG_CACHE
    global _RESEARCH_DEPTH_CONFIG_CACHE
    _CONFIG_CACHE = _load_config()
    _RESEARCH_DEPTH_CONFIG_CACHE = _load_research_depth_config()


def get_model_points(llm_provider: str, llm_model: str) -> int:
    """
    获取指定模型分析时消耗的点数
    
    Args:
        llm_provider: LLM提供商 (如: dashscope, google, openai等)
        llm_model: 模型名称 (如: qwen-plus-latest, gemini-2.5-pro等)
    
    Returns:
        消耗的点数
    """
    # 标准化输入
    provider = str(llm_provider).lower().strip()
    model = str(llm_model).strip()
    
    # 获取配置
    config = _get_config()
    
    # 查找精确匹配
    key = (provider, model)
    if key in config:
        return config[key]
    
    # 如果找不到精确匹配，尝试模糊匹配（用于处理一些特殊格式）
    # 例如：某些模型名称可能包含额外信息
    for (config_provider, config_model), points in config.items():
        if config_provider == provider:
            # 检查模型名称是否包含配置的模型名称，或配置的模型名称是否包含实际模型名称
            if model == config_model or model.startswith(config_model) or config_model.startswith(model):
                return points
    
    # 如果仍然找不到，返回默认点数
    return DEFAULT_POINTS


def get_all_model_points() -> Dict[Tuple[str, str], int]:
    """
    获取所有模型的点数配置
    
    Returns:
        格式: {(provider, model): points}
    """
    return _get_config().copy()


def set_model_points(llm_provider: str, llm_model: str, points: int) -> bool:
    """
    设置指定模型的点数
    
    Args:
        llm_provider: LLM提供商
        llm_model: 模型名称
        points: 消耗的点数
    
    Returns:
        是否保存成功
    """
    provider = str(llm_provider).lower().strip()
    model = str(llm_model).strip()
    
    config = _get_config()
    config[(provider, model)] = points
    
    if _save_config(config):
        reload_config()
        return True
    return False


def delete_model_points(llm_provider: str, llm_model: str) -> bool:
    """
    删除指定模型的点数配置（恢复为默认值）
    
    Args:
        llm_provider: LLM提供商
        llm_model: 模型名称
    
    Returns:
        是否保存成功
    """
    provider = str(llm_provider).lower().strip()
    model = str(llm_model).strip()
    
    config = _get_config()
    key = (provider, model)
    
    if key in config:
        del config[key]
        if _save_config(config):
            reload_config()
            return True
    return False


def format_points_display(points: int) -> str:
    """
    格式化点数显示（如果是整数显示整数，如果是小数保留小数）
    
    Args:
        points: 点数
    
    Returns:
        格式化的点数字符串
    """
    if points == int(points):
        return str(int(points))
    else:
        return str(points)


def _load_research_depth_config() -> Dict[int, int]:
    """
    从配置文件加载研究深度点数配置
    
    Returns:
        格式: {research_depth: points}
    """
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 检查是否有研究深度配置
                research_depth_config = data.get('research_depth_points', {})
                if research_depth_config:
                    config = {}
                    for depth_str, points in research_depth_config.items():
                        try:
                            depth = int(depth_str)
                            config[depth] = int(points)
                        except (ValueError, TypeError):
                            continue
                    # 确保所有1-5级都有配置
                    for depth in range(1, 6):
                        if depth not in config:
                            config[depth] = DEFAULT_RESEARCH_DEPTH_POINTS_CONFIG.get(depth, 1)
                    return config
    except Exception:
        pass
    
    # 如果加载失败，返回默认配置
    return DEFAULT_RESEARCH_DEPTH_POINTS_CONFIG.copy()


# 全局研究深度配置缓存
_RESEARCH_DEPTH_CONFIG_CACHE: Dict[int, int] = None


def _get_research_depth_config() -> Dict[int, int]:
    """获取研究深度配置（带缓存）"""
    global _RESEARCH_DEPTH_CONFIG_CACHE
    if _RESEARCH_DEPTH_CONFIG_CACHE is None:
        _RESEARCH_DEPTH_CONFIG_CACHE = _load_research_depth_config()
    return _RESEARCH_DEPTH_CONFIG_CACHE


def get_research_depth_points(research_depth: int) -> int:
    """
    根据研究深度获取消耗的点数
    
    Args:
        research_depth: 研究深度级别 (1-5)
    
    Returns:
        消耗的点数
    
    Raises:
        ValueError: 如果研究深度不在1-5范围内
    """
    if not isinstance(research_depth, int) or research_depth < 1 or research_depth > 5:
        raise ValueError(f"研究深度必须在1-5之间，当前值: {research_depth}")
    
    # 获取配置
    config = _get_research_depth_config()
    
    # 返回对应级别的点数，如果未配置则返回默认值
    return config.get(research_depth, DEFAULT_RESEARCH_DEPTH_POINTS_CONFIG.get(research_depth, 1))


def get_all_research_depth_points() -> Dict[int, int]:
    """
    获取所有研究深度的点数配置
    
    Returns:
        格式: {research_depth: points}
    """
    return _get_research_depth_config().copy()


def set_research_depth_points(research_depth: int, points: int) -> bool:
    """
    设置指定研究深度的点数
    
    Args:
        research_depth: 研究深度级别 (1-5)
        points: 消耗的点数
    
    Returns:
        是否保存成功
    """
    if not isinstance(research_depth, int) or research_depth < 1 or research_depth > 5:
        return False
    
    try:
        # 加载现有配置
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {
                'version': '1.0',
                'default_points': DEFAULT_POINTS,
                'config': [],
                'research_depth_points': {}
            }
        
        # 更新研究深度配置
        if 'research_depth_points' not in data:
            data['research_depth_points'] = {}
        data['research_depth_points'][str(research_depth)] = int(points)
        
        # 保存配置
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 重新加载配置缓存
        global _RESEARCH_DEPTH_CONFIG_CACHE
        _RESEARCH_DEPTH_CONFIG_CACHE = _load_research_depth_config()
        
        return True
    except Exception:
        return False


# 创建模型点数管理器对象（兼容旧代码）
class ModelPointsManager:
    """模型点数管理器类"""
    
    def get_model_points(self, llm_provider: str, llm_model: str) -> int:
        """获取指定模型分析时消耗的点数"""
        return get_model_points(llm_provider, llm_model)
    
    def get_all_model_points(self) -> Dict[Tuple[str, str], int]:
        """获取所有模型的点数配置"""
        return get_all_model_points()
    
    def set_model_points(self, llm_provider: str, llm_model: str, points: int) -> bool:
        """设置指定模型的点数"""
        return set_model_points(llm_provider, llm_model, points)
    
    def delete_model_points(self, llm_provider: str, llm_model: str) -> bool:
        """删除指定模型的点数配置"""
        return delete_model_points(llm_provider, llm_model)
    
    def get_research_depth_points(self, research_depth: int) -> int:
        """获取指定研究深度消耗的点数"""
        return get_research_depth_points(research_depth)
    
    def get_all_research_depth_points(self) -> Dict[int, int]:
        """获取所有研究深度的点数配置"""
        return get_all_research_depth_points()
    
    def set_research_depth_points(self, research_depth: int, points: int) -> bool:
        """设置指定研究深度的点数"""
        return set_research_depth_points(research_depth, points)


# 创建全局实例（兼容旧代码）
model_points_manager = ModelPointsManager()

