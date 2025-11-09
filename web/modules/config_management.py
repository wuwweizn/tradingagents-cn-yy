#!/usr/bin/env python3
"""
配置管理页面
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import List

# 添加项目根目录到路径
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入UI工具函数
sys.path.append(str(Path(__file__).parent.parent))
from utils.ui_utils import apply_hide_deploy_button_css

from tradingagents.config.config_manager import (
    config_manager, ModelConfig, PricingConfig
)


def render_config_management():
    """渲染配置管理页面"""
    # 应用隐藏Deploy按钮的CSS样式
    apply_hide_deploy_button_css()
    
    st.title("⚙️ 配置管理")

    # 显示.env配置状态
    render_env_status()

    # 侧边栏选择功能
    st.sidebar.title("配置选项")
    page = st.sidebar.selectbox(
        "选择功能",
        ["环境变量配置", "模型配置", "定价设置", "模型点数设置", "研究深度点数设置", "使用统计", "系统设置"]
    )
    
    if page == "环境变量配置":
        render_env_config()
    elif page == "模型配置":
        render_model_config()
    elif page == "定价设置":
        render_pricing_config()
    elif page == "模型点数设置":
        render_model_points_config()
    elif page == "研究深度点数设置":
        render_research_depth_points_config()
    elif page == "使用统计":
        render_usage_statistics()
    elif page == "系统设置":
        render_system_settings()


def render_model_config():
    """渲染模型配置页面"""
    st.markdown("**🤖 模型配置**")

    # 加载现有配置
    models = config_manager.load_models()

    # 显示当前配置
    st.markdown("**当前模型配置**")
    
    if models:
        # 创建DataFrame显示
        model_data = []
        env_status = config_manager.get_env_config_status()

        for i, model in enumerate(models):
            # 检查API密钥来源
            env_has_key = env_status["api_keys"].get(model.provider.lower(), False)
            api_key_display = "***" + model.api_key[-4:] if model.api_key else "未设置"
            if env_has_key:
                api_key_display += " (.env)"

            model_data.append({
                "序号": i,
                "供应商": model.provider,
                "模型名称": model.model_name,
                "API密钥": api_key_display,
                "最大Token": model.max_tokens,
                "温度": model.temperature,
                "状态": "✅ 启用" if model.enabled else "❌ 禁用"
            })
        
        df = pd.DataFrame(model_data)
        st.dataframe(df, use_container_width=True)
        
        # 编辑模型配置
        st.markdown("**编辑模型配置**")
        
        # 选择要编辑的模型
        model_options = [f"{m.provider} - {m.model_name}" for m in models]
        selected_model_idx = st.selectbox("选择要编辑的模型", range(len(model_options)),
                                         format_func=lambda x: model_options[x],
                                         key="select_model_to_edit")
        
        if selected_model_idx is not None:
            model = models[selected_model_idx]

            # 检查是否来自.env
            env_has_key = env_status["api_keys"].get(model.provider.lower(), False)
            if env_has_key:
                st.info(f"💡 此模型的API密钥来自 .env 文件，修改 .env 文件后需重启应用生效")

            col1, col2 = st.columns(2)

            with col1:
                new_api_key = st.text_input("API密钥", value=model.api_key, type="password", key=f"edit_api_key_{selected_model_idx}")
                if env_has_key:
                    st.caption("⚠️ 此密钥来自 .env 文件，Web修改可能被覆盖")
                new_max_tokens = st.number_input("最大Token数", value=model.max_tokens, min_value=1000, max_value=32000, key=f"edit_max_tokens_{selected_model_idx}")
                new_temperature = st.slider("温度参数", 0.0, 2.0, model.temperature, 0.1, key=f"edit_temperature_{selected_model_idx}")

            with col2:
                new_enabled = st.checkbox("启用模型", value=model.enabled, key=f"edit_enabled_{selected_model_idx}")
                new_base_url = st.text_input("自定义API地址 (可选)", value=model.base_url or "", key=f"edit_base_url_{selected_model_idx}")
            
            if st.button("保存配置", type="primary", key=f"save_model_config_{selected_model_idx}"):
                # 更新模型配置
                models[selected_model_idx] = ModelConfig(
                    provider=model.provider,
                    model_name=model.model_name,
                    api_key=new_api_key,
                    base_url=new_base_url if new_base_url else None,
                    max_tokens=new_max_tokens,
                    temperature=new_temperature,
                    enabled=new_enabled
                )
                
                config_manager.save_models(models)
                st.success("✅ 配置已保存！")
                st.rerun()
    
    else:
        st.warning("没有找到模型配置")
    
    # 添加新模型
    st.markdown("**添加新模型**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_provider = st.selectbox("供应商", ["dashscope", "openai", "google", "anthropic", "other"], key="new_provider")
        new_model_name = st.text_input("模型名称", placeholder="例如: gpt-4, qwen-plus-latest", key="new_model_name")
        new_api_key = st.text_input("API密钥", type="password", key="new_api_key")

    with col2:
        new_max_tokens = st.number_input("最大Token数", value=4000, min_value=1000, max_value=32000, key="new_max_tokens")
        new_temperature = st.slider("温度参数", 0.0, 2.0, 0.7, 0.1, key="new_temperature")
        new_enabled = st.checkbox("启用模型", value=True, key="new_enabled")
    
    if st.button("添加模型", key="add_new_model"):
        if new_provider and new_model_name and new_api_key:
            new_model = ModelConfig(
                provider=new_provider,
                model_name=new_model_name,
                api_key=new_api_key,
                max_tokens=new_max_tokens,
                temperature=new_temperature,
                enabled=new_enabled
            )
            
            models.append(new_model)
            config_manager.save_models(models)
            st.success("✅ 新模型已添加！")
            st.rerun()
        else:
            st.error("请填写所有必需字段")


def render_pricing_config():
    """渲染定价配置页面"""
    st.markdown("**💰 定价设置**")

    # 加载现有定价
    pricing_configs = config_manager.load_pricing()

    # 显示当前定价
    st.markdown("**当前定价配置**")
    
    if pricing_configs:
        pricing_data = []
        for i, pricing in enumerate(pricing_configs):
            pricing_data.append({
                "序号": i,
                "供应商": pricing.provider,
                "模型名称": pricing.model_name,
                "输入价格 (每1K token)": f"{pricing.input_price_per_1k} {pricing.currency}",
                "输出价格 (每1K token)": f"{pricing.output_price_per_1k} {pricing.currency}",
                "货币": pricing.currency
            })
        
        df = pd.DataFrame(pricing_data)
        st.dataframe(df, use_container_width=True)
        
        # 编辑定价
        st.markdown("**编辑定价**")
        
        pricing_options = [f"{p.provider} - {p.model_name}" for p in pricing_configs]
        selected_pricing_idx = st.selectbox("选择要编辑的定价", range(len(pricing_options)),
                                          format_func=lambda x: pricing_options[x],
                                          key="select_pricing_to_edit")
        
        if selected_pricing_idx is not None:
            pricing = pricing_configs[selected_pricing_idx]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                new_input_price = st.number_input("输入价格 (每1K token)",
                                                value=pricing.input_price_per_1k,
                                                min_value=0.0, step=0.001, format="%.6f",
                                                key=f"edit_input_price_{selected_pricing_idx}")

            with col2:
                new_output_price = st.number_input("输出价格 (每1K token)",
                                                 value=pricing.output_price_per_1k,
                                                 min_value=0.0, step=0.001, format="%.6f",
                                                 key=f"edit_output_price_{selected_pricing_idx}")

            with col3:
                new_currency = st.selectbox("货币", ["CNY", "USD", "EUR"],
                                          index=["CNY", "USD", "EUR"].index(pricing.currency),
                                          key=f"edit_currency_{selected_pricing_idx}")
            
            if st.button("保存定价", type="primary", key=f"save_pricing_config_{selected_pricing_idx}"):
                pricing_configs[selected_pricing_idx] = PricingConfig(
                    provider=pricing.provider,
                    model_name=pricing.model_name,
                    input_price_per_1k=new_input_price,
                    output_price_per_1k=new_output_price,
                    currency=new_currency
                )
                
                config_manager.save_pricing(pricing_configs)
                st.success("✅ 定价已保存！")
                st.rerun()
    
    # 添加新定价
    st.markdown("**添加新定价**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_provider = st.text_input("供应商", placeholder="例如: openai, dashscope", key="new_pricing_provider")
        new_model_name = st.text_input("模型名称", placeholder="例如: gpt-4, qwen-plus", key="new_pricing_model")
        new_currency = st.selectbox("货币", ["CNY", "USD", "EUR"], key="new_pricing_currency")

    with col2:
        new_input_price = st.number_input("输入价格 (每1K token)", min_value=0.0, step=0.001, format="%.6f", key="new_pricing_input")
        new_output_price = st.number_input("输出价格 (每1K token)", min_value=0.0, step=0.001, format="%.6f", key="new_pricing_output")
    
    if st.button("添加定价", key="add_new_pricing"):
        if new_provider and new_model_name:
            new_pricing = PricingConfig(
                provider=new_provider,
                model_name=new_model_name,
                input_price_per_1k=new_input_price,
                output_price_per_1k=new_output_price,
                currency=new_currency
            )
            
            pricing_configs.append(new_pricing)
            config_manager.save_pricing(pricing_configs)
            st.success("✅ 新定价已添加！")
            st.rerun()
        else:
            st.error("请填写供应商和模型名称")


def render_model_points_config():
    """渲染模型点数配置页面"""
    st.markdown("**模型点数设置**")
    st.markdown("管理员可以设置不同模型版本使用时的消耗点数")
    
    # 导入模型点数管理器
    try:
        from utils.model_points import (
            get_all_model_points, 
            set_model_points, 
            delete_model_points,
            get_model_points,
            reload_config,
            DEFAULT_POINTS
        )
    except ImportError:
        st.error("无法导入模型点数管理模块")
        return
    
    # 重新加载配置（确保获取最新数据）
    reload_config()
    
    # 获取所有配置
    all_config = get_all_model_points()
    
    # 显示当前配置
    st.markdown("**当前模型点数配置**")
    
    if all_config:
        # 按提供商分组显示
        config_data = []
        for (provider, model), points in sorted(all_config.items()):
            config_data.append({
                "提供商": provider,
                "模型名称": model,
                "消耗点数": points
            })
        
        df = pd.DataFrame(config_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("暂无模型点数配置")
    
    st.markdown("---")
    
    # 编辑现有配置
    st.markdown("**编辑模型点数配置**")
    
    if all_config:
        # 选择要编辑的配置
        config_options = [f"{provider} - {model}" for (provider, model) in sorted(all_config.keys())]
        selected_idx = st.selectbox(
            "选择要编辑的模型",
            range(len(config_options)),
            format_func=lambda x: config_options[x],
            key="select_model_points_to_edit"
        )
        
        if selected_idx is not None:
            selected_key = sorted(all_config.keys())[selected_idx]
            provider, model = selected_key
            current_points = all_config[selected_key]
            
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.text_input("提供商", value=provider, disabled=True, key="edit_provider")
            
            with col2:
                st.text_input("模型名称", value=model, disabled=True, key="edit_model")
            
            with col3:
                new_points = st.number_input(
                    "消耗点数",
                    min_value=1,
                    value=current_points,
                    step=1,
                    key="edit_points"
                )
            
            col_save, col_delete = st.columns([1, 1])
            
            with col_save:
                if st.button("保存", type="primary", key="save_model_points"):
                    if set_model_points(provider, model, new_points):
                        st.success("配置已保存！")
                        st.rerun()
                    else:
                        st.error("保存失败")
            
            with col_delete:
                if st.button("删除配置", type="secondary", key="delete_model_points"):
                    if delete_model_points(provider, model):
                        st.success("配置已删除，将使用默认点数")
                        st.rerun()
                    else:
                        st.error("删除失败")
    
    st.markdown("---")
    
    # 添加新配置
    st.markdown("**添加新模型点数配置**")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        new_provider = st.text_input("提供商", placeholder="例如: dashscope, google, openai", key="new_provider")
    
    with col2:
        new_model = st.text_input("模型名称", placeholder="例如: qwen-turbo, gemini-2.5-pro", key="new_model")
    
    with col3:
        new_points_value = st.number_input("消耗点数", min_value=1, value=1, step=1, key="new_points")
    
    if st.button("添加配置", type="primary", key="add_model_points"):
        if new_provider and new_model:
            provider_lower = new_provider.lower().strip()
            model_strip = new_model.strip()
            
            # 检查是否已存在
            if (provider_lower, model_strip) in all_config:
                st.warning("该模型配置已存在，请使用编辑功能修改")
            else:
                if set_model_points(provider_lower, model_strip, new_points_value):
                    st.success("配置已添加！")
                    st.rerun()
                else:
                    st.error("添加失败")
        else:
            st.error("请填写提供商和模型名称")
    
    st.markdown("---")
    
    # 批量导出和导入功能
    st.markdown("**批量导出/导入配置**")
    st.markdown("可以导出当前所有配置到JSON或Excel文件，或从JSON/Excel文件批量导入配置")
    
    col_export, col_import = st.columns(2)
    
    with col_export:
        st.markdown("**导出配置**")
        
        # 导出格式选择
        export_format = st.radio(
            "导出格式",
            ["JSON格式", "Excel格式"],
            horizontal=True,
            key="export_format_radio"
        )
        
        if export_format == "JSON格式":
            if st.button("📥 导出配置为JSON", type="primary", key="export_model_points_json"):
                try:
                    from utils.model_points import export_config_to_json
                    import tempfile
                    from datetime import datetime
                    
                    # 创建临时文件
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    temp_file = tempfile.NamedTemporaryFile(
                        mode='w',
                        suffix=f'_model_points_{timestamp}.json',
                        delete=False,
                        encoding='utf-8'
                    )
                    temp_file.close()
                    
                    # 导出配置
                    file_path = export_config_to_json(temp_file.name)
                    
                    # 读取文件内容用于下载
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    
                    # 提供下载
                    st.download_button(
                        label="💾 下载JSON配置文件",
                        data=file_content,
                        file_name=f"model_points_config_{timestamp}.json",
                        mime="application/json",
                        key="download_model_points_config_json"
                    )
                    
                    st.success("✅ 配置导出成功！点击上方按钮下载文件")
                    
                    # 显示导出预览
                    with st.expander("📋 查看导出内容预览"):
                        st.json(file_content[:2000] + "..." if len(file_content) > 2000 else file_content)
                        
                except Exception as e:
                    st.error(f"❌ 导出失败: {str(e)}")
        else:  # Excel格式
            if st.button("📥 导出配置为Excel", type="primary", key="export_model_points_excel"):
                try:
                    from utils.model_points import export_config_to_excel
                    from datetime import datetime
                    import tempfile
                    
                    # 创建临时文件
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    temp_file = tempfile.NamedTemporaryFile(
                        suffix=f'_model_points_{timestamp}.xlsx',
                        delete=False
                    )
                    temp_file.close()
                    
                    # 导出配置
                    file_path = export_config_to_excel(temp_file.name)
                    
                    # 读取文件内容用于下载
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    
                    # 提供下载
                    st.download_button(
                        label="💾 下载Excel配置文件",
                        data=file_content,
                        file_name=f"model_points_config_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_model_points_config_excel"
                    )
                    
                    st.success("✅ Excel配置导出成功！点击上方按钮下载文件")
                    st.info("💡 Excel文件包含多个工作表：模型点数配置、研究深度配置、开关配置、配置信息")
                    
                except ImportError as e:
                    st.error("❌ 导出失败: 需要安装openpyxl库")
                    st.code("pip install openpyxl", language="bash")
                except Exception as e:
                    st.error(f"❌ 导出失败: {str(e)}")
    
    with col_import:
        st.markdown("**导入配置**")
        
        # 导入模式选择
        import_mode = st.radio(
            "导入模式",
            ["合并模式", "覆盖模式"],
            help="合并模式：保留现有配置，只更新导入的配置项\n覆盖模式：完全替换现有配置",
            key="import_mode_radio"
        )
        merge_mode = (import_mode == "合并模式")
        
        # 文件上传（支持JSON和Excel）
        uploaded_file = st.file_uploader(
            "选择配置文件（支持JSON或Excel格式）",
            type=['json', 'xlsx', 'xls'],
            key="upload_model_points_config"
        )
        
        if uploaded_file is not None:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            try:
                if file_extension == 'json':
                    # JSON格式导入
                    json_data = uploaded_file.read().decode('utf-8')
                    
                    # 显示文件预览
                    with st.expander("📋 查看导入文件内容"):
                        st.json(json_data[:2000] + "..." if len(json_data) > 2000 else json_data)
                    
                    # 导入按钮
                    if st.button("📤 导入配置", type="primary", key="import_model_points_json"):
                        from utils.model_points import import_config_from_json
                        
                        # 执行导入
                        success, stats = import_config_from_json(json_data, merge_mode=merge_mode)
                        
                        if success:
                            st.success("✅ 配置导入成功！")
                            
                            # 显示导入统计
                            st.info(f"""
                            **导入统计：**
                            - 新增模型配置: {stats['model_points_added']} 个
                            - 更新模型配置: {stats['model_points_updated']} 个
                            - 更新研究深度配置: {stats['research_depth_updated']} 个
                            - 更新开关配置: {'是' if stats['toggle_updated'] else '否'}
                            """)
                            
                            if stats['errors']:
                                st.warning(f"⚠️ 导入过程中有 {len(stats['errors'])} 个警告/错误")
                                with st.expander("查看详细错误信息"):
                                    for error in stats['errors']:
                                        st.text(f"- {error}")
                            
                            st.rerun()
                        else:
                            st.error("❌ 配置导入失败！")
                            if stats.get('errors'):
                                st.error("**错误信息：**")
                                for error in stats['errors']:
                                    st.text(f"- {error}")
                
                elif file_extension in ['xlsx', 'xls']:
                    # Excel格式导入
                    import tempfile
                    import os
                    
                    # 保存上传的文件到临时位置
                    temp_file = tempfile.NamedTemporaryFile(
                        suffix=f'.{file_extension}',
                        delete=False
                    )
                    temp_file.write(uploaded_file.read())
                    temp_file.close()
                    
                    st.info(f"📄 已上传Excel文件: {uploaded_file.name}")
                    st.info("💡 Excel文件应包含以下工作表：模型点数配置、研究深度配置、开关配置")
                    
                    # 导入按钮
                    if st.button("📤 导入配置", type="primary", key="import_model_points_excel"):
                        from utils.model_points import import_config_from_excel
                        
                        # 执行导入
                        success, stats = import_config_from_excel(temp_file.name, merge_mode=merge_mode)
                        
                        # 删除临时文件
                        try:
                            os.unlink(temp_file.name)
                        except:
                            pass
                        
                        if success:
                            st.success("✅ 配置导入成功！")
                            
                            # 显示导入统计
                            st.info(f"""
                            **导入统计：**
                            - 新增模型配置: {stats['model_points_added']} 个
                            - 更新模型配置: {stats['model_points_updated']} 个
                            - 更新研究深度配置: {stats['research_depth_updated']} 个
                            - 更新开关配置: {'是' if stats['toggle_updated'] else '否'}
                            """)
                            
                            if stats['errors']:
                                st.warning(f"⚠️ 导入过程中有 {len(stats['errors'])} 个警告/错误")
                                with st.expander("查看详细错误信息"):
                                    for error in stats['errors']:
                                        st.text(f"- {error}")
                            
                            st.rerun()
                        else:
                            st.error("❌ 配置导入失败！")
                            if stats.get('errors'):
                                st.error("**错误信息：**")
                                for error in stats['errors']:
                                    st.text(f"- {error}")
                else:
                    st.error(f"❌ 不支持的文件格式: {file_extension}")
                        
            except UnicodeDecodeError:
                st.error("❌ 文件编码错误，请确保文件是UTF-8编码（JSON文件）")
            except ImportError as e:
                st.error("❌ 导入失败: 需要安装openpyxl库")
                st.code("pip install openpyxl", language="bash")
            except Exception as e:
                st.error(f"❌ 导入失败: {str(e)}")
    
    st.markdown("---")
    
    # 显示默认点数说明
    st.info(f"**说明**：未配置的模型将使用默认点数 {DEFAULT_POINTS} 点")


def render_research_depth_points_config():
    """渲染研究深度点数配置页面"""
    st.markdown("**研究深度点数设置**")
    st.markdown("管理员可以设置不同研究深度级别使用时的消耗点数（1级最低，5级最高）")
    
    # 导入研究深度点数管理器
    try:
        from utils.model_points import (
            get_all_research_depth_points, 
            set_research_depth_points, 
            get_research_depth_points,
            reload_config,
            DEFAULT_RESEARCH_DEPTH_POINTS_CONFIG
        )
    except ImportError:
        st.error("无法导入研究深度点数管理模块")
        return
    
    # 重新加载配置（确保获取最新数据）
    reload_config()
    
    # 获取所有配置
    all_config = get_all_research_depth_points()
    
    # 显示当前配置
    st.markdown("**当前研究深度点数配置**")
    
    if all_config:
        # 显示配置表格
        config_data = []
        depth_names = {
            1: "1级 - 快速分析",
            2: "2级 - 基础分析",
            3: "3级 - 标准分析",
            4: "4级 - 深度分析",
            5: "5级 - 全面分析"
        }
        
        for depth in sorted(all_config.keys()):
            points = all_config[depth]
            config_data.append({
                "研究深度": f"{depth}级",
                "级别名称": depth_names.get(depth, f"{depth}级"),
                "消耗点数": points
            })
        
        df = pd.DataFrame(config_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("暂无研究深度点数配置")
    
    st.markdown("---")
    
    # 编辑配置
    st.markdown("**编辑研究深度点数配置**")
    
    # 定义研究深度名称（在函数内部定义，确保可用）
    depth_names = {
        1: "1级 - 快速分析",
        2: "2级 - 基础分析",
        3: "3级 - 标准分析",
        4: "4级 - 深度分析",
        5: "5级 - 全面分析"
    }
    
    if all_config:
        # 选择要编辑的研究深度
        selected_depth = st.selectbox(
            "选择研究深度",
            options=sorted(all_config.keys()),
            format_func=lambda x: f"{x}级 - {depth_names.get(x, '未知')}",
            key="edit_research_depth"
        )
        
        if selected_depth:
            current_points = all_config.get(selected_depth, 1)
            
            col_edit, col_save = st.columns([3, 1])
            
            with col_edit:
                new_points = st.number_input(
                    "消耗点数",
                    min_value=1,
                    value=current_points,
                    step=1,
                    key=f"edit_points_{selected_depth}"
                )
            
            with col_save:
                st.write("")  # 占位
                st.write("")  # 占位
                if st.button("保存配置", type="primary", key=f"save_research_depth_{selected_depth}"):
                    if set_research_depth_points(selected_depth, new_points):
                        st.success("配置已保存！")
                        st.rerun()
                    else:
                        st.error("保存失败")
    
    st.markdown("---")
    
    # 点数消耗开关设置
    st.markdown("**点数消耗开关设置**")
    st.markdown("可以控制是否启用研究深度点数和模型点数的消耗")
    
    try:
        from utils.model_points import get_points_toggle_config, set_points_toggle_config, reload_config
        
        # 获取当前开关状态
        toggle_config = get_points_toggle_config()
        enable_research_depth_points = toggle_config.get("enable_research_depth_points", True)
        enable_model_points = toggle_config.get("enable_model_points", True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_enable_research_depth = st.checkbox(
                "启用研究深度点数消耗",
                value=enable_research_depth_points,
                help="如果关闭，研究深度级别将不消耗点数",
                key="toggle_research_depth_points"
            )
        
        with col2:
            new_enable_model = st.checkbox(
                "启用模型点数消耗",
                value=enable_model_points,
                help="如果关闭，模型选择将不消耗点数",
                key="toggle_model_points"
            )
        
        if st.button("保存开关设置", type="primary", key="save_points_toggle"):
            if set_points_toggle_config(
                enable_research_depth_points=new_enable_research_depth,
                enable_model_points=new_enable_model
            ):
                reload_config()
                st.success("✅ 开关设置已保存！")
                st.rerun()
            else:
                st.error("❌ 保存失败")
        
        # 显示当前状态说明
        st.info(f"""
        **当前状态：**
        - 研究深度点数消耗：{'✅ 已启用' if enable_research_depth_points else '❌ 已禁用'}
        - 模型点数消耗：{'✅ 已启用' if enable_model_points else '❌ 已禁用'}
        
        **说明：**
        - 如果两个开关都关闭，分析将不消耗任何点数
        - 如果只启用其中一个，则只计算该部分的点数
        - 如果两个都启用，总点数 = 研究深度基础点数 + 模型点数
        """)
    except Exception as e:
        st.error(f"无法加载开关设置: {e}")
    
    st.markdown("---")
    
    # 显示默认配置说明
    st.info("**说明**：研究深度级别从1级到5级，级别越高分析越详细，消耗的点数也越多。当前默认配置：")
    default_info = []
    for depth in sorted(DEFAULT_RESEARCH_DEPTH_POINTS_CONFIG.keys()):
        points = DEFAULT_RESEARCH_DEPTH_POINTS_CONFIG[depth]
        default_info.append(f"- {depth}级: {points}点")
    st.markdown("\n".join(default_info))


def render_usage_statistics():
    """渲染使用统计页面"""
    st.markdown("**📊 使用统计**")

    # 时间范围选择
    col1, col2 = st.columns(2)
    with col1:
        days = st.selectbox("统计时间范围", [7, 30, 90, 365], index=1, key="stats_time_range")
    with col2:
        st.metric("统计周期", f"最近 {days} 天")

    # 获取统计数据
    stats = config_manager.get_usage_statistics(days)

    if stats["total_requests"] == 0:
        st.info("📝 暂无使用记录")
        return

    # 总体统计
    st.markdown("**📈 总体统计**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总成本", f"¥{stats['total_cost']:.4f}")
    
    with col2:
        st.metric("总请求数", f"{stats['total_requests']:,}")
    
    with col3:
        st.metric("输入Token", f"{stats['total_input_tokens']:,}")
    
    with col4:
        st.metric("输出Token", f"{stats['total_output_tokens']:,}")
    
    # 按供应商统计
    if stats["provider_stats"]:
        st.markdown("**🏢 按供应商统计**")
        
        provider_data = []
        for provider, data in stats["provider_stats"].items():
            provider_data.append({
                "供应商": provider,
                "成本": f"¥{data['cost']:.4f}",
                "请求数": data['requests'],
                "输入Token": f"{data['input_tokens']:,}",
                "输出Token": f"{data['output_tokens']:,}",
                "平均成本/请求": f"¥{data['cost']/data['requests']:.6f}" if data['requests'] > 0 else "¥0"
            })
        
        df = pd.DataFrame(provider_data)
        st.dataframe(df, use_container_width=True)
        
        # 成本分布饼图
        if len(provider_data) > 1:
            fig = px.pie(
                values=[stats["provider_stats"][p]["cost"] for p in stats["provider_stats"]],
                names=list(stats["provider_stats"].keys()),
                title="成本分布"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 使用趋势
    st.markdown("**📈 使用趋势**")
    
    records = config_manager.load_usage_records()
    if records:
        # 按日期聚合
        daily_stats = {}
        for record in records:
            try:
                date = datetime.fromisoformat(record.timestamp).date()
                if date not in daily_stats:
                    daily_stats[date] = {"cost": 0, "requests": 0}
                daily_stats[date]["cost"] += record.cost
                daily_stats[date]["requests"] += 1
            except:
                continue
        
        if daily_stats:
            dates = sorted(daily_stats.keys())
            costs = [daily_stats[date]["cost"] for date in dates]
            requests = [daily_stats[date]["requests"] for date in dates]
            
            # 创建双轴图表
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=dates, y=costs,
                mode='lines+markers',
                name='每日成本 (¥)',
                yaxis='y'
            ))
            
            fig.add_trace(go.Scatter(
                x=dates, y=requests,
                mode='lines+markers',
                name='每日请求数',
                yaxis='y2'
            ))
            
            fig.update_layout(
                title='使用趋势',
                xaxis_title='日期',
                yaxis=dict(title='成本 (¥)', side='left'),
                yaxis2=dict(title='请求数', side='right', overlaying='y'),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)


def render_system_settings():
    """渲染系统设置页面"""
    st.markdown("**🔧 系统设置**")

    # 加载当前设置
    settings = config_manager.load_settings()

    st.markdown("**基本设置**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        default_provider = st.selectbox(
            "默认供应商",
            ["dashscope", "openai", "google", "anthropic"],
            index=["dashscope", "openai", "google", "anthropic"].index(
                settings.get("default_provider", "dashscope")
            ),
            key="settings_default_provider"
        )

        enable_cost_tracking = st.checkbox(
            "启用成本跟踪",
            value=settings.get("enable_cost_tracking", True),
            key="settings_enable_cost_tracking"
        )

        currency_preference = st.selectbox(
            "首选货币",
            ["CNY", "USD", "EUR"],
            index=["CNY", "USD", "EUR"].index(
                settings.get("currency_preference", "CNY")
            ),
            key="settings_currency_preference"
        )
    
    with col2:
        default_model = st.text_input(
            "默认模型",
            value=settings.get("default_model", "qwen-turbo"),
            key="settings_default_model"
        )

        cost_alert_threshold = st.number_input(
            "成本警告阈值",
            value=settings.get("cost_alert_threshold", 100.0),
            min_value=0.0,
            step=10.0,
            key="settings_cost_alert_threshold"
        )

        max_usage_records = st.number_input(
            "最大使用记录数",
            value=settings.get("max_usage_records", 10000),
            min_value=1000,
            max_value=100000,
            step=1000,
            key="settings_max_usage_records"
        )

    auto_save_usage = st.checkbox(
        "自动保存使用记录",
        value=settings.get("auto_save_usage", True),
        key="settings_auto_save_usage"
    )
    
    if st.button("保存设置", type="primary", key="save_system_settings"):
        new_settings = {
            "default_provider": default_provider,
            "default_model": default_model,
            "enable_cost_tracking": enable_cost_tracking,
            "cost_alert_threshold": cost_alert_threshold,
            "currency_preference": currency_preference,
            "auto_save_usage": auto_save_usage,
            "max_usage_records": max_usage_records
        }
        
        config_manager.save_settings(new_settings)
        st.success("✅ 设置已保存！")
        st.rerun()
    
    # 数据管理
    st.markdown("**数据管理**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("导出配置", help="导出所有配置到JSON文件", key="export_config"):
            # 这里可以实现配置导出功能
            st.info("配置导出功能开发中...")
    
    with col2:
        if st.button("清空使用记录", help="清空所有使用记录", key="clear_usage_records"):
            if st.session_state.get("confirm_clear", False):
                config_manager.save_usage_records([])
                st.success("✅ 使用记录已清空！")
                st.session_state.confirm_clear = False
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("⚠️ 再次点击确认清空")
    
    with col3:
        if st.button("重置配置", help="重置所有配置到默认值", key="reset_all_config"):
            if st.session_state.get("confirm_reset", False):
                # 删除配置文件，重新初始化
                import shutil
                if config_manager.config_dir.exists():
                    shutil.rmtree(config_manager.config_dir)
                config_manager._init_default_configs()
                st.success("✅ 配置已重置！")
                st.session_state.confirm_reset = False
                st.rerun()
            else:
                st.session_state.confirm_reset = True
                st.warning("⚠️ 再次点击确认重置")


def render_env_status():
    """显示.env配置状态"""
    st.markdown("**📋 配置状态概览**")

    # 获取.env配置状态
    env_status = config_manager.get_env_config_status()

    # 显示.env文件状态
    col1, col2 = st.columns(2)

    with col1:
        if env_status["env_file_exists"]:
            st.success("✅ .env 文件已存在")
        else:
            st.error("❌ .env 文件不存在")
            st.info("💡 请复制 .env.example 为 .env 并配置API密钥")

    with col2:
        # 统计已配置的API密钥数量
        configured_keys = sum(1 for configured in env_status["api_keys"].values() if configured)
        total_keys = len(env_status["api_keys"])
        st.metric("API密钥配置", f"{configured_keys}/{total_keys}")

    # 详细API密钥状态
    with st.expander("🔑 API密钥详细状态", expanded=False):
        api_col1, api_col2 = st.columns(2)

        with api_col1:
            st.write("**大模型API密钥:**")
            for provider, configured in env_status["api_keys"].items():
                if provider in ["dashscope", "openai", "google", "anthropic"]:
                    status = "✅ 已配置" if configured else "❌ 未配置"
                    provider_name = {
                        "dashscope": "阿里百炼",
                        "openai": "OpenAI",
                        "google": "Google AI",
                        "anthropic": "Anthropic"
                    }.get(provider, provider)
                    st.write(f"- {provider_name}: {status}")

        with api_col2:
            st.write("**其他API密钥:**")
            finnhub_status = "✅ 已配置" if env_status["api_keys"]["finnhub"] else "❌ 未配置"
            st.write(f"- FinnHub (金融数据): {finnhub_status}")

            reddit_status = "✅ 已配置" if env_status["other_configs"]["reddit_configured"] else "❌ 未配置"
            st.write(f"- Reddit API: {reddit_status}")

    # 配置优先级说明
    st.info("""
    📌 **配置优先级说明:**
    - API密钥优先从 `.env` 文件读取
    - Web界面配置作为补充和管理工具
    - 修改 `.env` 文件后需重启应用生效
    - 推荐使用 `.env` 文件管理敏感信息
    """)

    st.divider()


def render_env_config():
    """渲染环境变量配置页面"""
    st.markdown("**🔧 环境变量配置**")
    st.markdown("管理.env文件中的环境变量配置")
    
    try:
        from utils.env_config_manager import get_env_config_manager
        
        env_manager = get_env_config_manager()
        
        # 检查.env文件是否存在
        if not env_manager.env_file_exists():
            st.warning("⚠️ .env文件不存在，将自动创建")
            # 创建空文件
            env_manager.env_file_path.touch()
            st.info("✅ .env文件已创建")
            st.rerun()
        
        # 显示文件路径
        st.info(f"📁 配置文件路径: `{env_manager.env_file_path}`")
        
        # 备份功能
        col_backup, col_reload = st.columns(2)
        with col_backup:
            if st.button("💾 备份.env文件", help="创建.env文件的备份", key="backup_env_file"):
                backup_path = env_manager.backup_env_file()
                if backup_path:
                    st.success(f"✅ 备份已创建: `{backup_path}`")
                else:
                    st.error("❌ 备份失败")
        
        with col_reload:
            if st.button("🔄 重新加载", help="重新加载.env文件", key="reload_env_file"):
                st.rerun()
        
        st.markdown("---")
        
        # 获取分类的环境变量
        categories = env_manager.get_env_variable_categories()
        
        # 使用标签页显示不同分类
        category_names = list(categories.keys())
        if category_names:
            tabs = st.tabs(category_names)
            
            for tab_idx, (category_name, tab) in enumerate(zip(category_names, tabs)):
                with tab:
                    st.markdown(f"**{category_name}**")
                    
                    variables = categories[category_name]
                    
                    if not variables:
                        st.info("该分类下暂无配置项")
                        continue
                    
                    # 按变量分组显示
                    for var_info in variables:
                        with st.expander(f"🔧 {var_info['name']}", expanded=False):
                            key = var_info['key']
                            current_value = var_info.get('value', '')
                            is_sensitive = var_info.get('sensitive', False)
                            description = var_info.get('description', '')
                            default_value = var_info.get('default', '')
                            
                            # 显示说明
                            if description:
                                st.caption(f"💡 {description}")
                            
                            # 显示当前状态
                            if var_info.get('is_set', False):
                                st.success("✅ 已配置")
                            else:
                                st.warning("⚠️ 未配置")
                                if default_value:
                                    st.info(f"默认值: {default_value}")
                            
                            # 编辑表单
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                if is_sensitive:
                                    # 敏感信息使用密码输入框
                                    new_value = st.text_input(
                                        "值",
                                        value=current_value if current_value else "",
                                        type="password",
                                        key=f"env_input_{key}",
                                        help="输入新的值（敏感信息，输入时会被隐藏）"
                                    )
                                else:
                                    # 非敏感信息使用普通输入框
                                    placeholder = default_value if default_value else "请输入值"
                                    new_value = st.text_input(
                                        "值",
                                        value=current_value if current_value else "",
                                        key=f"env_input_{key}",
                                        placeholder=placeholder,
                                        help=description
                                    )
                            
                            with col2:
                                # 显示当前值（如果是敏感信息，只显示部分）
                                if is_sensitive and current_value:
                                    display_value = "***" + current_value[-4:] if len(current_value) > 4 else "***"
                                    st.text(f"当前: {display_value}")
                                elif current_value:
                                    st.text(f"当前: {current_value}")
                                else:
                                    st.text("当前: 未设置")
                            
                            # 操作按钮
                            col_save, col_delete, col_reset = st.columns(3)
                            
                            with col_save:
                                if st.button("💾 保存", key=f"save_{key}", type="primary"):
                                    # 验证值
                                    is_valid, error_msg = env_manager.validate_env_variable(key, new_value)
                                    
                                    if not is_valid:
                                        st.error(f"❌ 验证失败: {error_msg}")
                                    else:
                                        # 保存变量
                                        if env_manager.set_env_variable(key, new_value):
                                            st.success(f"✅ {var_info['name']} 已保存")
                                            st.info("💡 修改.env文件后，需要重启应用才能生效")
                                            st.rerun()
                                        else:
                                            st.error("❌ 保存失败")
                            
                            with col_delete:
                                if st.button("🗑️ 删除", key=f"delete_{key}"):
                                    if env_manager.delete_env_variable(key):
                                        st.success(f"✅ {var_info['name']} 已删除")
                                        st.rerun()
                                    else:
                                        st.error("❌ 删除失败")
                            
                            with col_reset:
                                if default_value and st.button("🔄 重置", key=f"reset_{key}"):
                                    if env_manager.set_env_variable(key, default_value):
                                        st.success(f"✅ {var_info['name']} 已重置为默认值")
                                        st.rerun()
                                    else:
                                        st.error("❌ 重置失败")
        
        st.markdown("---")
        
        # 批量操作
        st.markdown("**批量操作**")
        
        col_export, col_import = st.columns(2)
        
        with col_export:
            st.markdown("**导出配置**")
            if st.button("📥 导出.env文件", key="export_env_file"):
                try:
                    env_vars = env_manager.load_env_variables()
                    env_content = "\n".join([f"{k}={v}" for k, v in env_vars.items() if v])
                    
                    st.download_button(
                        label="💾 下载.env文件",
                        data=env_content,
                        file_name=".env",
                        mime="text/plain",
                        key="download_env_file"
                    )
                    st.success("✅ 配置已准备下载")
                except Exception as e:
                    st.error(f"❌ 导出失败: {str(e)}")
        
        with col_import:
            st.markdown("**导入配置**")
            uploaded_file = st.file_uploader(
                "选择.env文件",
                type=['env', 'txt'],
                key="upload_env_file"
            )
            
            if uploaded_file is not None:
                try:
                    content = uploaded_file.read().decode('utf-8')
                    
                    # 解析.env文件内容
                    env_vars = {}
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip().strip('"').strip("'")
                                if key:
                                    env_vars[key] = value
                    
                    if env_vars:
                        st.info(f"📋 检测到 {len(env_vars)} 个环境变量")
                        
                        if st.button("📤 导入配置", key="import_env_file", type="primary"):
                            # 备份现有配置
                            backup_path = env_manager.backup_env_file()
                            if backup_path:
                                st.info(f"✅ 已备份现有配置到: {backup_path.name}")
                            
                            # 导入新配置
                            if env_manager.save_env_variables(env_vars):
                                st.success("✅ 配置导入成功！")
                                st.warning("⚠️ 需要重启应用才能生效")
                                st.rerun()
                            else:
                                st.error("❌ 导入失败")
                except Exception as e:
                    st.error(f"❌ 导入失败: {str(e)}")
        
        st.markdown("---")
        
        # 重要提示
        st.warning("""
        ⚠️ **重要提示：**
        - 修改.env文件后，需要**重启应用**才能生效
        - 敏感信息（API密钥等）请妥善保管，不要泄露
        - 建议在修改前先备份.env文件
        - 删除变量会将其设置为空值，不会从文件中移除
        """)
        
    except ImportError as e:
        st.error(f"❌ 无法导入环境变量管理模块: {e}")
        st.info("💡 请检查模块是否正确安装")
    except Exception as e:
        st.error(f"❌ 加载环境变量配置失败: {str(e)}")
        # 记录错误（如果logger可用）
        try:
            from tradingagents.utils.logging_manager import get_logger
            logger = get_logger('web')
            logger.error(f"环境变量配置页面错误: {e}", exc_info=True)
        except:
            pass


def main():
    """主函数"""
    st.set_page_config(
        page_title="配置管理 - TradingAgents",
        page_icon="⚙️",
        layout="wide"
    )
    
    render_config_management()

if __name__ == "__main__":
    main()
