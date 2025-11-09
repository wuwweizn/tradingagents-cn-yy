"""
阿里百炼大模型 (DashScope) 适配器
为 TradingAgents 提供阿里百炼大模型的 LangChain 兼容接口
"""

import os
import json
from typing import Any, Dict, List, Optional, Union, Iterator, AsyncIterator, Sequence
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks.manager import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import Field, SecretStr
import dashscope
from dashscope import Generation
from ..config.config_manager import token_tracker

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')



class ChatDashScope(BaseChatModel):
    """阿里百炼大模型的 LangChain 适配器"""
    
    # 模型配置
    model: str = Field(default="qwen-turbo", description="DashScope 模型名称")
    api_key: Optional[SecretStr] = Field(default=None, description="DashScope API 密钥")
    temperature: float = Field(default=0.1, description="生成温度")
    max_tokens: int = Field(default=2000, description="最大生成token数")
    top_p: float = Field(default=0.9, description="核采样参数")
    
    # 内部属性
    _client: Any = None
    
    def __init__(self, **kwargs):
        """初始化 DashScope 客户端"""
        super().__init__(**kwargs)
        
        # 设置API密钥
        api_key = self.api_key
        if api_key is None:
            api_key = os.getenv("DASHSCOPE_API_KEY")
        
        if api_key is None:
            raise ValueError(
                "DashScope API key not found. Please set DASHSCOPE_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # 配置 DashScope
        if isinstance(api_key, SecretStr):
            dashscope.api_key = api_key.get_secret_value()
        else:
            dashscope.api_key = api_key
    
    @property
    def _llm_type(self) -> str:
        """返回LLM类型"""
        return "dashscope"
    
    def _convert_messages_to_dashscope_format(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """将 LangChain 消息格式转换为 DashScope 格式"""
        dashscope_messages = []
        
        for message in messages:
            if isinstance(message, SystemMessage):
                role = "system"
            elif isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            else:
                # 默认作为用户消息处理
                role = "user"
            
            content = message.content
            if isinstance(content, list):
                # 处理多模态内容，目前只提取文本
                text_content = ""
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_content += item.get("text", "")
                content = text_content
            
            dashscope_messages.append({
                "role": role,
                "content": str(content)
            })
        
        return dashscope_messages
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """生成聊天回复"""
        
        # 转换消息格式
        dashscope_messages = self._convert_messages_to_dashscope_format(messages)
        
        # 准备请求参数
        request_params = {
            "model": self.model,
            "messages": dashscope_messages,
            "result_format": "message",
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }
        
        # 添加停止词
        if stop:
            request_params["stop"] = stop
        
        # 合并额外参数
        request_params.update(kwargs)
        
        try:
            # 调用 DashScope API
            response = Generation.call(**request_params)
            
            if response.status_code == 200:
                # 解析响应
                output = response.output
                message_content = output.choices[0].message.content
                
                # 提取token使用量信息
                input_tokens = 0
                output_tokens = 0
                
                # DashScope API响应中包含usage信息
                if hasattr(response, 'usage') and response.usage:
                    usage = response.usage
                    # 根据API文档，usage可能包含input_tokens和output_tokens
                    if hasattr(usage, 'input_tokens'):
                        input_tokens = usage.input_tokens
                    if hasattr(usage, 'output_tokens'):
                        output_tokens = usage.output_tokens
                    # 有些情况下可能是total_tokens
                    elif hasattr(usage, 'total_tokens'):
                        # 估算输入和输出token（如果没有分别提供）
                        total_tokens = usage.total_tokens
                        # 简单估算：假设输入占30%，输出占70%
                        input_tokens = int(total_tokens * 0.3)
                        output_tokens = int(total_tokens * 0.7)
                
                # 记录token使用量
                if input_tokens > 0 or output_tokens > 0:
                    try:
                        # 生成会话ID（如果没有提供）
                        session_id = kwargs.get('session_id', f"dashscope_{hash(str(messages))%10000}")
                        analysis_type = kwargs.get('analysis_type', 'stock_analysis')
                        
                        # 使用TokenTracker记录使用量
                        token_tracker.track_usage(
                            provider="dashscope",
                            model_name=self.model,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            session_id=session_id,
                            analysis_type=analysis_type
                        )
                    except Exception as track_error:
                        # 记录失败不应该影响主要功能
                        logger.info(f"Token tracking failed: {track_error}")
                
                # 创建 AI 消息
                ai_message = AIMessage(content=message_content)
                
                # 创建生成结果
                generation = ChatGeneration(message=ai_message)
                
                return ChatResult(generations=[generation])
            else:
                raise Exception(f"DashScope API error: {response.code} - {response.message}")
                
        except Exception as e:
            raise Exception(f"Error calling DashScope API: {str(e)}")
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """异步生成聊天回复"""
        # 目前使用同步方法，后续可以实现真正的异步
        return self._generate(messages, stop, run_manager, **kwargs)
    
    def bind_tools(
        self,
        tools: Sequence[Union[Dict[str, Any], type, BaseTool]],
        **kwargs: Any,
    ) -> "ChatDashScope":
        """绑定工具到模型"""
        # 注意：DashScope 目前不直接支持工具调用
        # 这里我们返回一个新的实例，但实际上工具调用需要在应用层处理
        formatted_tools = []
        for tool in tools:
            if hasattr(tool, "name") and hasattr(tool, "description"):
                # 这是一个 BaseTool 实例
                formatted_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": getattr(tool, "args_schema", {})
                })
            elif isinstance(tool, dict):
                formatted_tools.append(tool)
            else:
                # 尝试转换为 OpenAI 工具格式
                try:
                    openai_tool = convert_to_openai_tool(tool)
                    formatted_tools.append(openai_tool)
                    logger.debug(f"✅ 工具转换成功: {getattr(tool, 'name', 'unknown')}")
                except Exception as e:
                    # 记录错误并提供回退机制
                    tool_name = getattr(tool, 'name', 'unknown')
                    logger.warning(f"⚠️ 工具转换失败: {tool_name} - {e}")
                    
                    # 尝试手动创建基本工具格式作为回退
                    try:
                        fallback_tool = {
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "description": getattr(tool, 'description', f'工具: {tool_name}'),
                                "parameters": {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            }
                        }
                        formatted_tools.append(fallback_tool)
                        logger.info(f"🔄 使用回退工具格式: {tool_name}")
                    except Exception as fallback_error:
                        logger.error(f"❌ 回退工具格式创建失败: {tool_name} - {fallback_error}")
                        # 如果回退也失败，至少记录警告，不静默失败

        # 创建新实例，保存工具信息
        new_instance = self.__class__(
            model=self.model,
            api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            **kwargs
        )
        new_instance._tools = formatted_tools
        return new_instance

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """返回标识参数"""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }


# 支持的模型列表
DASHSCOPE_MODELS = {
    # 通义千问系列
    "qwen-turbo": {
        "description": "通义千问 Turbo - 快速响应，适合日常对话",
        "context_length": 8192,
        "recommended_for": ["快速任务", "日常对话", "简单分析"]
    },
    "qwen-plus": {
        "description": "通义千问 Plus - 平衡性能和成本",
        "context_length": 32768,
        "recommended_for": ["复杂分析", "专业任务", "深度思考"]
    },
    "qwen-max": {
        "description": "通义千问 Max - 最强性能",
        "context_length": 32768,
        "recommended_for": ["最复杂任务", "专业分析", "高质量输出"]
    },
    "qwen-max-longcontext": {
        "description": "通义千问 Max 长文本版 - 支持超长上下文",
        "context_length": 1000000,
        "recommended_for": ["长文档分析", "大量数据处理", "复杂推理"]
    },
}


def get_available_models() -> Dict[str, Dict[str, Any]]:
    """获取可用的 DashScope 模型列表"""
    return DASHSCOPE_MODELS


def create_dashscope_llm(
    model: str = "qwen-plus",
    api_key: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 2000,
    **kwargs
) -> ChatDashScope:
    """创建 DashScope LLM 实例的便捷函数"""
    
    return ChatDashScope(
        model=model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )
