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


# ===== 批量导出和导入功能 =====

def export_all_config() -> Dict:
    """
    导出所有模型点数配置（包括模型配置、研究深度配置、开关配置）
    
    Returns:
        包含所有配置的字典，格式：
        {
            'version': str,
            'export_time': str,
            'model_points': [...],
            'research_depth_points': {...},
            'points_toggle': {...},
            'default_points': int
        }
    """
    from datetime import datetime
    
    try:
        # 获取所有配置
        model_config = get_all_model_points()
        research_depth_config = get_all_research_depth_points()
        toggle_config = get_points_toggle_config()
        
        # 构建导出数据
        export_data = {
            'version': '2.0',  # 导出格式版本
            'export_time': datetime.now().isoformat(),
            'export_description': 'TradingAgents-CN 模型点数配置导出',
            'default_points': DEFAULT_POINTS,
            'model_points': [
                {
                    'provider': provider,
                    'model': model,
                    'points': points
                }
                for (provider, model), points in sorted(model_config.items())
            ],
            'research_depth_points': {
                str(depth): points
                for depth, points in sorted(research_depth_config.items())
            },
            'points_toggle': toggle_config.copy()
        }
        
        return export_data
    except Exception as e:
        raise Exception(f"导出配置失败: {str(e)}")


def export_config_to_json(file_path: str = None) -> str:
    """
    导出配置到JSON文件
    
    Args:
        file_path: 文件路径，如果为None则返回JSON字符串
    
    Returns:
        如果file_path为None，返回JSON字符串；否则返回文件路径
    """
    import json
    
    try:
        export_data = export_all_config()
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        if file_path:
            # 保存到文件
            path_obj = Path(file_path)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(path_obj, 'w', encoding='utf-8') as f:
                f.write(json_str)
            return str(path_obj.absolute())
        else:
            # 返回JSON字符串
            return json_str
    except Exception as e:
        raise Exception(f"导出配置到JSON失败: {str(e)}")


def import_config_from_dict(import_data: Dict, merge_mode: bool = False) -> Tuple[bool, Dict[str, int]]:
    """
    从字典导入配置
    
    Args:
        import_data: 导入的配置数据
        merge_mode: True=合并模式（保留现有配置，只更新导入的配置），False=覆盖模式（完全替换）
    
    Returns:
        (是否成功, 统计信息字典)
    """
    stats = {
        'model_points_added': 0,
        'model_points_updated': 0,
        'research_depth_updated': 0,
        'toggle_updated': False,
        'errors': []
    }
    
    try:
        # 验证导入数据格式
        if not isinstance(import_data, dict):
            stats['errors'].append("导入数据格式错误：必须是字典格式")
            return False, stats
        
        # 检查版本兼容性
        version = import_data.get('version', '1.0')
        if version not in ['1.0', '2.0']:
            stats['errors'].append(f"不支持的配置版本: {version}")
            return False, stats
        
        # 导入模型点数配置
        if 'model_points' in import_data:
            model_points_list = import_data['model_points']
            if not isinstance(model_points_list, list):
                stats['errors'].append("model_points 必须是列表格式")
            else:
                current_config = get_all_model_points() if merge_mode else {}
                
                for item in model_points_list:
                    try:
                        provider = str(item.get('provider', '')).lower().strip()
                        model = str(item.get('model', '')).strip()
                        points = int(item.get('points', DEFAULT_POINTS))
                        
                        if not provider or not model:
                            stats['errors'].append(f"无效的配置项: {item}")
                            continue
                        
                        key = (provider, model)
                        if key in current_config:
                            stats['model_points_updated'] += 1
                        else:
                            stats['model_points_added'] += 1
                        
                        current_config[key] = points
                    except (ValueError, TypeError) as e:
                        stats['errors'].append(f"配置项格式错误: {item} - {str(e)}")
                        continue
                
                # 保存模型点数配置
                if _save_config(current_config):
                    reload_config()
                else:
                    stats['errors'].append("保存模型点数配置失败")
        
        # 导入研究深度点数配置
        if 'research_depth_points' in import_data:
            research_depth_data = import_data['research_depth_points']
            if not isinstance(research_depth_data, dict):
                stats['errors'].append("research_depth_points 必须是字典格式")
            else:
                for depth_str, points in research_depth_data.items():
                    try:
                        depth = int(depth_str)
                        points_int = int(points)
                        
                        if depth < 1 or depth > 5:
                            stats['errors'].append(f"研究深度必须在1-5之间: {depth}")
                            continue
                        
                        if set_research_depth_points(depth, points_int):
                            stats['research_depth_updated'] += 1
                        else:
                            stats['errors'].append(f"设置研究深度 {depth} 失败")
                    except (ValueError, TypeError) as e:
                        stats['errors'].append(f"研究深度配置格式错误: {depth_str} - {str(e)}")
                        continue
        
        # 导入点数开关配置
        if 'points_toggle' in import_data:
            toggle_data = import_data['points_toggle']
            if not isinstance(toggle_data, dict):
                stats['errors'].append("points_toggle 必须是字典格式")
            else:
                enable_research_depth = toggle_data.get('enable_research_depth_points')
                enable_model = toggle_data.get('enable_model_points')
                
                if set_points_toggle_config(
                    enable_research_depth_points=enable_research_depth,
                    enable_model_points=enable_model
                ):
                    stats['toggle_updated'] = True
                else:
                    stats['errors'].append("设置点数开关配置失败")
        
        # 检查是否有严重错误
        has_critical_error = any('失败' in error or '格式错误' in error for error in stats['errors'])
        
        return not has_critical_error, stats
        
    except Exception as e:
        stats['errors'].append(f"导入配置时发生异常: {str(e)}")
        return False, stats


def import_config_from_json(json_data: str, merge_mode: bool = False) -> Tuple[bool, Dict[str, int]]:
    """
    从JSON字符串导入配置
    
    Args:
        json_data: JSON格式的配置数据
        merge_mode: True=合并模式，False=覆盖模式
    
    Returns:
        (是否成功, 统计信息字典)
    """
    import json
    
    try:
        import_data = json.loads(json_data)
        return import_config_from_dict(import_data, merge_mode)
    except json.JSONDecodeError as e:
        return False, {
            'errors': [f"JSON解析失败: {str(e)}"],
            'model_points_added': 0,
            'model_points_updated': 0,
            'research_depth_updated': 0,
            'toggle_updated': False
        }
    except Exception as e:
        return False, {
            'errors': [f"导入配置失败: {str(e)}"],
            'model_points_added': 0,
            'model_points_updated': 0,
            'research_depth_updated': 0,
            'toggle_updated': False
        }


def import_config_from_file(file_path: str, merge_mode: bool = False) -> Tuple[bool, Dict[str, int]]:
    """
    从JSON文件导入配置
    
    Args:
        file_path: JSON文件路径
        merge_mode: True=合并模式，False=覆盖模式
    
    Returns:
        (是否成功, 统计信息字典)
    """
    try:
        path_obj = Path(file_path)
        if not path_obj.exists():
            return False, {
                'errors': [f"文件不存在: {file_path}"],
                'model_points_added': 0,
                'model_points_updated': 0,
                'research_depth_updated': 0,
                'toggle_updated': False
            }
        
        with open(path_obj, 'r', encoding='utf-8') as f:
            json_data = f.read()
        
        return import_config_from_json(json_data, merge_mode)
    except Exception as e:
        return False, {
            'errors': [f"读取文件失败: {str(e)}"],
            'model_points_added': 0,
            'model_points_updated': 0,
            'research_depth_updated': 0,
            'toggle_updated': False
        }


# ===== Excel格式导出和导入功能 =====

def export_config_to_excel(file_path: str = None) -> str:
    """
    导出配置到Excel文件
    
    Args:
        file_path: 文件路径，如果为None则返回字节数据
    
    Returns:
        如果file_path为None，返回字节数据；否则返回文件路径
    """
    try:
        import pandas as pd
        from io import BytesIO
        
        # 获取所有配置
        export_data = export_all_config()
        
        # 创建Excel写入器
        if file_path:
            excel_writer = pd.ExcelWriter(file_path, engine='openpyxl')
        else:
            excel_buffer = BytesIO()
            excel_writer = pd.ExcelWriter(excel_buffer, engine='openpyxl')
        
        try:
            # 1. 模型点数配置工作表
            model_points_data = []
            for item in export_data.get('model_points', []):
                model_points_data.append({
                    '提供商 (Provider)': item['provider'],
                    '模型名称 (Model)': item['model'],
                    '消耗点数 (Points)': item['points']
                })
            
            if model_points_data:
                df_model = pd.DataFrame(model_points_data)
                df_model.to_excel(excel_writer, sheet_name='模型点数配置', index=False)
            else:
                # 创建空的工作表
                df_model = pd.DataFrame(columns=['提供商 (Provider)', '模型名称 (Model)', '消耗点数 (Points)'])
                df_model.to_excel(excel_writer, sheet_name='模型点数配置', index=False)
            
            # 2. 研究深度点数配置工作表
            research_depth_data = []
            for depth_str, points in sorted(export_data.get('research_depth_points', {}).items()):
                research_depth_data.append({
                    '研究深度级别 (Depth)': int(depth_str),
                    '消耗点数 (Points)': points,
                    '说明': f'{depth_str}级 - {"快速分析" if depth_str == "1" else "基础分析" if depth_str == "2" else "标准分析" if depth_str == "3" else "深度分析" if depth_str == "4" else "全面分析"}'
                })
            
            if research_depth_data:
                df_depth = pd.DataFrame(research_depth_data)
                df_depth.to_excel(excel_writer, sheet_name='研究深度配置', index=False)
            else:
                df_depth = pd.DataFrame(columns=['研究深度级别 (Depth)', '消耗点数 (Points)', '说明'])
                df_depth.to_excel(excel_writer, sheet_name='研究深度配置', index=False)
            
            # 3. 点数开关配置工作表
            toggle_data = [{
                '配置项': '启用研究深度点数消耗',
                '当前值': export_data.get('points_toggle', {}).get('enable_research_depth_points', True),
                '说明': '是否启用研究深度级别的点数消耗'
            }, {
                '配置项': '启用模型点数消耗',
                '当前值': export_data.get('points_toggle', {}).get('enable_model_points', True),
                '说明': '是否启用模型点数消耗'
            }]
            
            df_toggle = pd.DataFrame(toggle_data)
            df_toggle.to_excel(excel_writer, sheet_name='开关配置', index=False)
            
            # 4. 配置信息工作表
            info_data = [{
                '配置项': '导出时间',
                '值': export_data.get('export_time', '')
            }, {
                '配置项': '配置版本',
                '值': export_data.get('version', '2.0')
            }, {
                '配置项': '默认点数',
                '值': export_data.get('default_points', DEFAULT_POINTS)
            }, {
                '配置项': '说明',
                '值': '此文件包含TradingAgents-CN模型点数配置，可直接编辑后导入'
            }]
            
            df_info = pd.DataFrame(info_data)
            df_info.to_excel(excel_writer, sheet_name='配置信息', index=False)
            
            # 保存Excel文件
            excel_writer.close()
            
            if file_path:
                return str(Path(file_path).absolute())
            else:
                excel_buffer.seek(0)
                return excel_buffer.getvalue()
                
        except Exception as e:
            excel_writer.close()
            raise e
            
    except ImportError:
        raise Exception("需要安装openpyxl库: pip install openpyxl")
    except Exception as e:
        raise Exception(f"导出配置到Excel失败: {str(e)}")


def import_config_from_excel(file_path: str, merge_mode: bool = False) -> Tuple[bool, Dict[str, int]]:
    """
    从Excel文件导入配置
    
    Args:
        file_path: Excel文件路径
        merge_mode: True=合并模式，False=覆盖模式
    
    Returns:
        (是否成功, 统计信息字典)
    """
    stats = {
        'model_points_added': 0,
        'model_points_updated': 0,
        'research_depth_updated': 0,
        'toggle_updated': False,
        'errors': []
    }
    
    try:
        import pandas as pd
        
        path_obj = Path(file_path)
        if not path_obj.exists():
            return False, {
                'errors': [f"文件不存在: {file_path}"],
                **{k: v for k, v in stats.items() if k != 'errors'}
            }
        
        # 读取Excel文件
        excel_file = pd.ExcelFile(file_path, engine='openpyxl')
        
        # 构建导入数据字典
        import_data = {
            'version': '2.0',
            'model_points': [],
            'research_depth_points': {},
            'points_toggle': {}
        }
        
        # 1. 读取模型点数配置
        if '模型点数配置' in excel_file.sheet_names:
            try:
                df_model = pd.read_excel(excel_file, sheet_name='模型点数配置')
                
                # 处理不同的列名格式
                provider_col = None
                model_col = None
                points_col = None
                
                for col in df_model.columns:
                    col_lower = str(col).lower()
                    if 'provider' in col_lower or '提供商' in col:
                        provider_col = col
                    elif 'model' in col_lower or '模型' in col:
                        model_col = col
                    elif 'points' in col_lower or '点数' in col:
                        points_col = col
                
                if provider_col and model_col and points_col:
                    for _, row in df_model.iterrows():
                        try:
                            provider = str(row[provider_col]).strip().lower()
                            model = str(row[model_col]).strip()
                            points = int(float(row[points_col]))  # 处理可能的浮点数
                            
                            if provider and model and not pd.isna(points):
                                import_data['model_points'].append({
                                    'provider': provider,
                                    'model': model,
                                    'points': points
                                })
                        except (ValueError, TypeError) as e:
                            stats['errors'].append(f"模型配置行格式错误: {row.to_dict()} - {str(e)}")
                else:
                    stats['errors'].append("模型点数配置工作表缺少必要的列")
            except Exception as e:
                stats['errors'].append(f"读取模型点数配置失败: {str(e)}")
        
        # 2. 读取研究深度点数配置
        if '研究深度配置' in excel_file.sheet_names:
            try:
                df_depth = pd.read_excel(excel_file, sheet_name='研究深度配置')
                
                depth_col = None
                points_col = None
                
                for col in df_depth.columns:
                    col_lower = str(col).lower()
                    if 'depth' in col_lower or '深度' in col:
                        depth_col = col
                    elif 'points' in col_lower or '点数' in col:
                        points_col = col
                
                if depth_col and points_col:
                    for _, row in df_depth.iterrows():
                        try:
                            depth = int(float(row[depth_col]))
                            points = int(float(row[points_col]))
                            
                            if 1 <= depth <= 5 and not pd.isna(points):
                                import_data['research_depth_points'][str(depth)] = points
                        except (ValueError, TypeError) as e:
                            stats['errors'].append(f"研究深度配置行格式错误: {row.to_dict()} - {str(e)}")
                else:
                    stats['errors'].append("研究深度配置工作表缺少必要的列")
            except Exception as e:
                stats['errors'].append(f"读取研究深度配置失败: {str(e)}")
        
        # 3. 读取开关配置
        if '开关配置' in excel_file.sheet_names:
            try:
                df_toggle = pd.read_excel(excel_file, sheet_name='开关配置')
                
                config_col = None
                value_col = None
                
                for col in df_toggle.columns:
                    col_lower = str(col).lower()
                    if '配置项' in col or 'config' in col_lower:
                        config_col = col
                    elif '值' in col or 'value' in col_lower:
                        value_col = col
                
                if config_col and value_col:
                    for _, row in df_toggle.iterrows():
                        try:
                            config_item = str(row[config_col]).strip()
                            value = row[value_col]
                            
                            # 处理布尔值
                            if isinstance(value, bool):
                                bool_value = value
                            elif isinstance(value, str):
                                bool_value = value.lower() in ['true', '1', 'yes', '是', '启用']
                            else:
                                bool_value = bool(value)
                            
                            if '研究深度' in config_item or 'research' in config_item.lower():
                                import_data['points_toggle']['enable_research_depth_points'] = bool_value
                            elif '模型' in config_item or 'model' in config_item.lower():
                                import_data['points_toggle']['enable_model_points'] = bool_value
                        except Exception as e:
                            stats['errors'].append(f"开关配置行格式错误: {row.to_dict()} - {str(e)}")
                else:
                    stats['errors'].append("开关配置工作表缺少必要的列")
            except Exception as e:
                stats['errors'].append(f"读取开关配置失败: {str(e)}")
        
        # 使用字典导入函数
        success, import_stats = import_config_from_dict(import_data, merge_mode)
        
        # 合并统计信息
        stats['model_points_added'] = import_stats.get('model_points_added', 0)
        stats['model_points_updated'] = import_stats.get('model_points_updated', 0)
        stats['research_depth_updated'] = import_stats.get('research_depth_updated', 0)
        stats['toggle_updated'] = import_stats.get('toggle_updated', False)
        stats['errors'].extend(import_stats.get('errors', []))
        
        return success, stats
        
    except ImportError:
        return False, {
            'errors': ['需要安装openpyxl库: pip install openpyxl'],
            **{k: v for k, v in stats.items() if k != 'errors'}
        }
    except Exception as e:
        return False, {
            'errors': [f"从Excel导入配置失败: {str(e)}"],
            **{k: v for k, v in stats.items() if k != 'errors'}
        }

