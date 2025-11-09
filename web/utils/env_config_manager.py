"""
环境变量配置文件管理器
用于在Web界面中管理.env文件
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import dotenv_values, set_key

# 导入日志模块
try:
    from tradingagents.utils.logging_manager import get_logger
    logger = get_logger('web')
except ImportError:
    # 如果无法导入，使用标准logging
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('web')


class EnvConfigManager:
    """环境变量配置文件管理器"""
    
    def __init__(self, env_file_path: Optional[Path] = None):
        """
        初始化环境变量管理器
        
        Args:
            env_file_path: .env文件路径，如果为None则使用项目根目录的.env
        """
        if env_file_path is None:
            # 获取项目根目录
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            env_file_path = project_root / ".env"
        
        self.env_file_path = Path(env_file_path)
        self.env_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def env_file_exists(self) -> bool:
        """检查.env文件是否存在"""
        return self.env_file_path.exists()
    
    def load_env_variables(self) -> Dict[str, str]:
        """
        加载.env文件中的所有变量
        
        Returns:
            环境变量字典
        """
        if not self.env_file_exists():
            return {}
        
        try:
            # 使用dotenv_values读取，不覆盖系统环境变量
            env_vars = dotenv_values(self.env_file_path)
            # 过滤掉None值
            return {k: v for k, v in env_vars.items() if v is not None}
        except Exception as e:
            logger.error(f"加载.env文件失败: {e}")
            return {}
    
    def get_env_variable(self, key: str, default: str = "") -> str:
        """
        获取环境变量值
        
        Args:
            key: 环境变量名
            default: 默认值
        
        Returns:
            环境变量值
        """
        env_vars = self.load_env_variables()
        return env_vars.get(key, default)
    
    def set_env_variable(self, key: str, value: str) -> bool:
        """
        设置环境变量
        
        Args:
            key: 环境变量名
            value: 环境变量值
        
        Returns:
            是否成功
        """
        try:
            # 使用set_key函数更新.env文件
            result = set_key(
                self.env_file_path,
                key,
                value,
                quote_mode='never'  # 不添加引号，保持原样
            )
            
            if result:
                logger.info(f"✅ 环境变量 {key} 已更新")
                return True
            else:
                logger.error(f"❌ 环境变量 {key} 更新失败")
                return False
        except Exception as e:
            logger.error(f"设置环境变量失败: {e}")
            return False
    
    def delete_env_variable(self, key: str) -> bool:
        """
        删除环境变量（通过设置为空值实现）
        
        Args:
            key: 环境变量名
        
        Returns:
            是否成功
        """
        return self.set_env_variable(key, "")
    
    def save_env_variables(self, variables: Dict[str, str]) -> bool:
        """
        批量保存环境变量
        
        Args:
            variables: 环境变量字典
        
        Returns:
            是否成功
        """
        try:
            # 读取现有变量
            existing_vars = self.load_env_variables()
            
            # 合并新变量（包括空值，用于删除）
            existing_vars.update(variables)
            
            # 读取原始文件内容，保留注释和格式
            original_lines = []
            if self.env_file_exists():
                with open(self.env_file_path, 'r', encoding='utf-8') as f:
                    original_lines = f.readlines()
            
            # 构建已处理的键集合
            processed_keys = set()
            
            # 写入文件
            with open(self.env_file_path, 'w', encoding='utf-8') as f:
                # 先写入原始文件中的注释和已存在的变量
                for line in original_lines:
                    line_stripped = line.strip()
                    # 保留注释和空行
                    if not line_stripped or line_stripped.startswith('#'):
                        f.write(line)
                    elif '=' in line_stripped:
                        key = line_stripped.split('=', 1)[0].strip()
                        # 如果这个键在要更新的变量中，跳过（后面会写入新值）
                        if key in variables:
                            processed_keys.add(key)
                            # 写入新值
                            value = existing_vars.get(key, '')
                            if value:
                                # 处理包含空格或特殊字符的值
                                if ' ' in str(value) or '#' in str(value) or '\n' in str(value) or '"' in str(value):
                                    # 使用引号包裹，转义内部引号
                                    escaped_value = str(value).replace('"', '\\"')
                                    f.write(f'{key}="{escaped_value}"\n')
                                else:
                                    f.write(f'{key}={value}\n')
                        else:
                            # 保留原有变量
                            f.write(line)
                            processed_keys.add(key)
                
                # 写入新增的变量（不在原文件中的）
                for key, value in variables.items():
                    if key not in processed_keys:
                        if value:
                            # 处理包含空格或特殊字符的值
                            if ' ' in str(value) or '#' in str(value) or '\n' in str(value) or '"' in str(value):
                                escaped_value = str(value).replace('"', '\\"')
                                f.write(f'{key}="{escaped_value}"\n')
                            else:
                                f.write(f'{key}={value}\n')
            
            logger.info(f"✅ 已保存 {len(variables)} 个环境变量")
            return True
        except Exception as e:
            logger.error(f"保存环境变量失败: {e}")
            return False
    
    def get_env_variable_categories(self) -> Dict[str, List[Dict[str, str]]]:
        """
        获取分类的环境变量配置
        
        Returns:
            分类的环境变量字典
        """
        env_vars = self.load_env_variables()
        
        # 定义环境变量分类和说明
        categories = {
            "LLM API密钥": [
                {
                    "key": "DASHSCOPE_API_KEY",
                    "name": "阿里百炼 (DashScope) API密钥",
                    "description": "用于调用阿里百炼大模型",
                    "sensitive": True,
                    "required": False
                },
                {
                    "key": "OPENAI_API_KEY",
                    "name": "OpenAI API密钥",
                    "description": "用于调用OpenAI模型（GPT系列）",
                    "sensitive": True,
                    "required": False
                },
                {
                    "key": "GOOGLE_API_KEY",
                    "name": "Google AI API密钥",
                    "description": "用于调用Google Gemini模型",
                    "sensitive": True,
                    "required": False
                },
                {
                    "key": "ANTHROPIC_API_KEY",
                    "name": "Anthropic API密钥",
                    "description": "用于调用Claude模型",
                    "sensitive": True,
                    "required": False
                },
                {
                    "key": "DEEPSEEK_API_KEY",
                    "name": "DeepSeek API密钥",
                    "description": "用于调用DeepSeek模型",
                    "sensitive": True,
                    "required": False
                },
                {
                    "key": "SILICONFLOW_API_KEY",
                    "name": "硅基流动 (SiliconFlow) API密钥",
                    "description": "用于调用硅基流动模型",
                    "sensitive": True,
                    "required": False
                },
                {
                    "key": "QIANFAN_API_KEY",
                    "name": "百度千帆 API密钥",
                    "description": "用于调用百度文心一言模型",
                    "sensitive": True,
                    "required": False
                },
            ],
            "数据源API密钥": [
                {
                    "key": "FINNHUB_API_KEY",
                    "name": "Finnhub API密钥",
                    "description": "用于获取美股金融数据",
                    "sensitive": True,
                    "required": False
                },
                {
                    "key": "TUSHARE_TOKEN",
                    "name": "Tushare Token",
                    "description": "用于获取A股和港股数据",
                    "sensitive": True,
                    "required": False
                },
            ],
            "社交媒体API": [
                {
                    "key": "REDDIT_CLIENT_ID",
                    "name": "Reddit Client ID",
                    "description": "Reddit API客户端ID",
                    "sensitive": True,
                    "required": False
                },
                {
                    "key": "REDDIT_CLIENT_SECRET",
                    "name": "Reddit Client Secret",
                    "description": "Reddit API客户端密钥",
                    "sensitive": True,
                    "required": False
                },
            ],
            "数据库配置": [
                {
                    "key": "MONGODB_HOST",
                    "name": "MongoDB主机地址",
                    "description": "MongoDB数据库主机地址",
                    "sensitive": False,
                    "required": False,
                    "default": "localhost"
                },
                {
                    "key": "MONGODB_PORT",
                    "name": "MongoDB端口",
                    "description": "MongoDB数据库端口",
                    "sensitive": False,
                    "required": False,
                    "default": "27017"
                },
                {
                    "key": "MONGODB_USERNAME",
                    "name": "MongoDB用户名",
                    "description": "MongoDB数据库用户名",
                    "sensitive": True,
                    "required": False
                },
                {
                    "key": "MONGODB_PASSWORD",
                    "name": "MongoDB密码",
                    "description": "MongoDB数据库密码",
                    "sensitive": True,
                    "required": False
                },
                {
                    "key": "MONGODB_DATABASE",
                    "name": "MongoDB数据库名",
                    "description": "MongoDB数据库名称",
                    "sensitive": False,
                    "required": False,
                    "default": "tradingagents"
                },
                {
                    "key": "MONGODB_AUTH_SOURCE",
                    "name": "MongoDB认证源",
                    "description": "MongoDB认证数据库",
                    "sensitive": False,
                    "required": False,
                    "default": "admin"
                },
                {
                    "key": "TRADINGAGENTS_REDIS_URL",
                    "name": "Redis连接URL",
                    "description": "Redis数据库连接URL",
                    "sensitive": True,
                    "required": False
                },
            ],
            "系统配置": [
                {
                    "key": "TRADINGAGENTS_LOG_LEVEL",
                    "name": "日志级别",
                    "description": "系统日志级别 (DEBUG, INFO, WARNING, ERROR)",
                    "sensitive": False,
                    "required": False,
                    "default": "INFO"
                },
                {
                    "key": "TRADINGAGENTS_LOG_DIR",
                    "name": "日志目录",
                    "description": "日志文件存储目录",
                    "sensitive": False,
                    "required": False,
                    "default": "./logs"
                },
                {
                    "key": "TRADINGAGENTS_RESULTS_DIR",
                    "name": "结果目录",
                    "description": "分析结果存储目录",
                    "sensitive": False,
                    "required": False,
                    "default": "./results"
                },
                {
                    "key": "OPENAI_ENABLED",
                    "name": "启用OpenAI",
                    "description": "是否启用OpenAI模型 (true/false)",
                    "sensitive": False,
                    "required": False,
                    "default": "false"
                },
                {
                    "key": "DOCKER_CONTAINER",
                    "name": "Docker容器模式",
                    "description": "是否在Docker容器中运行 (true/false)",
                    "sensitive": False,
                    "required": False,
                    "default": "false"
                },
            ],
            "其他配置": []
        }
        
        # 填充实际值
        result = {}
        for category, items in categories.items():
            result[category] = []
            for item in items:
                key = item["key"]
                current_value = env_vars.get(key, "")
                item["value"] = current_value
                item["is_set"] = bool(current_value)
                result[category].append(item)
        
        # 添加未分类的变量到"其他配置"
        defined_keys = set()
        for items in categories.values():
            for item in items:
                defined_keys.add(item["key"])
        
        for key, value in env_vars.items():
            if key not in defined_keys:
                result["其他配置"].append({
                    "key": key,
                    "name": key,
                    "description": "自定义环境变量",
                    "sensitive": "KEY" in key.upper() or "SECRET" in key.upper() or "PASSWORD" in key.upper() or "TOKEN" in key.upper(),
                    "required": False,
                    "value": value,
                    "is_set": bool(value)
                })
        
        return result
    
    def validate_env_variable(self, key: str, value: str) -> Tuple[bool, str]:
        """
        验证环境变量值
        
        Args:
            key: 环境变量名
            value: 环境变量值
        
        Returns:
            (是否有效, 错误信息)
        """
        # 基本验证
        if not key:
            return False, "环境变量名不能为空"
        
        if not re.match(r'^[A-Z_][A-Z0-9_]*$', key):
            return False, "环境变量名格式不正确（应全大写字母、数字和下划线，且不能以数字开头）"
        
        # 特定变量的验证
        if key == "MONGODB_PORT":
            try:
                port = int(value)
                if port < 1 or port > 65535:
                    return False, "端口号必须在1-65535之间"
            except ValueError:
                return False, "端口号必须是整数"
        
        if key == "TRADINGAGENTS_LOG_LEVEL":
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if value.upper() not in valid_levels:
                return False, f"日志级别必须是: {', '.join(valid_levels)}"
        
        if key in ["OPENAI_ENABLED", "DOCKER_CONTAINER"]:
            if value.lower() not in ["true", "false", "1", "0", "yes", "no"]:
                return False, "布尔值必须是: true/false, 1/0, yes/no"
        
        return True, ""
    
    def backup_env_file(self) -> Optional[Path]:
        """
        备份.env文件
        
        Returns:
            备份文件路径，如果失败返回None
        """
        if not self.env_file_exists():
            return None
        
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.env_file_path.parent / f".env.backup_{timestamp}"
            
            import shutil
            shutil.copy2(self.env_file_path, backup_path)
            
            logger.info(f"✅ .env文件已备份到: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"备份.env文件失败: {e}")
            return None


# 创建全局实例
def get_env_config_manager() -> EnvConfigManager:
    """获取环境变量管理器实例"""
    return EnvConfigManager()

