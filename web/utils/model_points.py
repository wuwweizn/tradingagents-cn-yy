"""
模型点数配置
定义不同LLM模型分析时消耗的点数
同时支持研究深度级别（1-5级）的点数配置
"""

import json
from pathlib import Path
from typing import Dict, Tuple, List

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
    
    # OpenRouter
    ("openrouter", "default"): 2,  # 默认点数（当模型未配置时使用）
    # 常见OpenRouter模型配置
    ("openrouter", "anthropic/claude-3.7-sonnet"): 5,  # Claude 3.7 Sonnet - 高质量模型
    ("openrouter", "anthropic/claude-opus-4"): 8,  # Claude 4 Opus - 顶级模型
    ("openrouter", "anthropic/claude-3.5-sonnet"): 4,  # Claude 3.5 Sonnet
    ("openrouter", "anthropic/claude-3-opus"): 6,  # Claude 3 Opus
    ("openrouter", "openai/gpt-4o"): 5,  # GPT-4o
    ("openrouter", "openai/gpt-4-turbo"): 4,  # GPT-4 Turbo
    ("openrouter", "openai/gpt-4"): 4,  # GPT-4
    ("openrouter", "openai/gpt-3.5-turbo"): 1,  # GPT-3.5 Turbo - 较便宜
    ("openrouter", "google/gemini-2.0-flash-exp"): 2,  # Gemini 2.0 Flash
    ("openrouter", "google/gemini-pro"): 3,  # Gemini Pro
    ("openrouter", "meta-llama/llama-4-scout"): 3,  # Llama 4 Scout
    ("openrouter", "meta-llama/llama-3.1-405b"): 4,  # Llama 3.1 405B
    ("openrouter", "meta-llama/llama-3.1-70b"): 2,  # Llama 3.1 70B
    
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

# 点数消耗开关默认配置
DEFAULT_POINTS_TOGGLE_CONFIG = {
    "enable_research_depth_points": True,  # 启用研究深度点数消耗
    "enable_model_points": True,  # 启用模型点数消耗
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
    global _POINTS_TOGGLE_CONFIG_CACHE
    _CONFIG_CACHE = _load_config()
    _RESEARCH_DEPTH_CONFIG_CACHE = _load_research_depth_config()
    _POINTS_TOGGLE_CONFIG_CACHE = _load_points_toggle_config()


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
    
    # 对于OpenRouter、custom_openai、qianfan等支持default配置的提供商
    # 如果找不到精确匹配，先检查是否有default配置
    if provider in ["openrouter", "custom_openai", "qianfan"]:
        default_key = (provider, "default")
        if default_key in config:
            return config[default_key]
    
    # 如果找不到精确匹配，尝试模糊匹配（用于处理一些特殊格式）
    # 例如：某些模型名称可能包含额外信息
    # 注意：对于OpenRouter等，如果找不到精确匹配，已经使用了default配置，这里主要是处理其他提供商
    for (config_provider, config_model), points in config.items():
        if config_provider == provider:
            # 跳过default配置（已经处理过了）
            if config_model == "default":
                continue
            
            # 精确匹配（在循环中再次检查，虽然理论上不会到这里，但为了安全）
            if model == config_model:
                return points
            
            # 通用模糊匹配：检查模型名称是否包含配置的模型名称，或配置的模型名称是否包含实际模型名称
            # 例如：某些模型名称可能包含额外信息（版本号、后缀等）
            # 但只对非OpenRouter提供商使用，OpenRouter已经通过default配置处理
            if provider not in ["openrouter", "custom_openai", "qianfan"]:
                if model.startswith(config_model) or config_model.startswith(model):
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


def get_available_providers() -> List[str]:
    """
    获取所有可用的提供商列表（从默认配置中提取）
    
    Returns:
        提供商名称列表，按字母顺序排序
    """
    providers = set()
    # 从默认配置中提取所有提供商
    for provider, _ in DEFAULT_MODEL_POINTS_CONFIG.keys():
        providers.add(provider)
    # 从当前配置中提取所有提供商（可能包含用户自定义的）
    config = _get_config()
    for provider, _ in config.keys():
        providers.add(provider)
    return sorted(list(providers))


def get_available_models(provider: str) -> List[str]:
    """
    获取指定提供商下的所有可用模型列表
    
    Args:
        provider: 提供商名称
    
    Returns:
        模型名称列表，按字母顺序排序
    """
    provider_lower = str(provider).lower().strip()
    models = set()
    
    # 从默认配置中提取该提供商的所有模型
    for (config_provider, model) in DEFAULT_MODEL_POINTS_CONFIG.keys():
        if config_provider.lower() == provider_lower:
            models.add(model)
    
    # 从当前配置中提取该提供商的所有模型（可能包含用户自定义的）
    config = _get_config()
    for (config_provider, model) in config.keys():
        if config_provider.lower() == provider_lower:
            models.add(model)
    
    return sorted(list(models))


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


def _load_points_toggle_config() -> Dict[str, bool]:
    """
    从配置文件加载点数消耗开关配置
    
    Returns:
        格式: {"enable_research_depth_points": bool, "enable_model_points": bool}
    """
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                toggle_config = data.get('points_toggle', {})
                if toggle_config:
                    config = {
                        "enable_research_depth_points": toggle_config.get("enable_research_depth_points", True),
                        "enable_model_points": toggle_config.get("enable_model_points", True),
                    }
                    return config
    except Exception:
        pass
    
    # 如果加载失败，返回默认配置
    return DEFAULT_POINTS_TOGGLE_CONFIG.copy()


# 全局点数开关配置缓存
_POINTS_TOGGLE_CONFIG_CACHE: Dict[str, bool] = None


def _get_points_toggle_config() -> Dict[str, bool]:
    """获取点数开关配置（带缓存）"""
    global _POINTS_TOGGLE_CONFIG_CACHE
    if _POINTS_TOGGLE_CONFIG_CACHE is None:
        _POINTS_TOGGLE_CONFIG_CACHE = _load_points_toggle_config()
    return _POINTS_TOGGLE_CONFIG_CACHE


def get_points_toggle_config() -> Dict[str, bool]:
    """
    获取点数消耗开关配置
    
    Returns:
        格式: {"enable_research_depth_points": bool, "enable_model_points": bool}
    """
    return _get_points_toggle_config().copy()


def set_points_toggle_config(enable_research_depth_points: bool = None, enable_model_points: bool = None) -> bool:
    """
    设置点数消耗开关配置
    
    Args:
        enable_research_depth_points: 是否启用研究深度点数消耗（None表示不修改）
        enable_model_points: 是否启用模型点数消耗（None表示不修改）
    
    Returns:
        是否保存成功
    """
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
                'research_depth_points': {},
                'points_toggle': {}
            }
        
        # 更新开关配置
        if 'points_toggle' not in data:
            data['points_toggle'] = DEFAULT_POINTS_TOGGLE_CONFIG.copy()
        
        current_config = _get_points_toggle_config()
        if enable_research_depth_points is not None:
            data['points_toggle']['enable_research_depth_points'] = bool(enable_research_depth_points)
        if enable_model_points is not None:
            data['points_toggle']['enable_model_points'] = bool(enable_model_points)
        
        # 保存配置
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 重新加载配置缓存
        global _POINTS_TOGGLE_CONFIG_CACHE
        _POINTS_TOGGLE_CONFIG_CACHE = _load_points_toggle_config()
        
        return True
    except Exception:
        return False


def get_analysis_points(research_depth: int, llm_provider: str = None, llm_model: str = None) -> int:
    """
    获取分析消耗的总点数（根据开关状态决定是否包含研究深度点数和模型点数）
    
    Args:
        research_depth: 研究深度级别 (1-5)
        llm_provider: LLM提供商（可选，如果提供则会根据开关状态加上模型点数）
        llm_model: 模型名称（可选，如果提供则会根据开关状态加上模型点数）
    
    Returns:
        消耗的总点数
    """
    # 获取开关配置
    toggle_config = _get_points_toggle_config()
    enable_research_depth_points = toggle_config.get("enable_research_depth_points", True)
    enable_model_points = toggle_config.get("enable_model_points", True)
    
    total_points = 0
    
    # 根据开关状态添加研究深度基础点数
    if enable_research_depth_points:
        depth_points = get_research_depth_points(research_depth)
        total_points += depth_points
    
    # 根据开关状态添加模型点数
    if enable_model_points and llm_provider and llm_model:
        model_points = get_model_points(llm_provider, llm_model)
        total_points += model_points
    
    return total_points


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
    
    def get_points_toggle_config(self) -> Dict[str, bool]:
        """获取点数消耗开关配置"""
        return get_points_toggle_config()
    
    def set_points_toggle_config(self, enable_research_depth_points: bool = None, enable_model_points: bool = None) -> bool:
        """设置点数消耗开关配置"""
        return set_points_toggle_config(enable_research_depth_points, enable_model_points)


# 创建全局实例（兼容旧代码）
model_points_manager = ModelPointsManager()

