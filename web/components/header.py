"""
页面头部组件
"""

import streamlit as st
from pathlib import Path
import json
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def render_header():
    """渲染页面头部"""
    
    # 主标题
    st.markdown("""
    <div class="main-header">
        <h1>TradingAgents-CN 股票分析平台</h1>
        <p>基于多智能体大语言模型的中文金融交易决策框架</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 公告栏
    try:
        from web.modules.announcement_management import get_active_announcements
        announcements = get_active_announcements()
        
        if announcements:
            # 公告栏样式
            st.markdown("""
            <style>
            .announcement-container {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            .announcement-item {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 0.8rem;
                border-left: 4px solid #667eea;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            .announcement-item.high-priority {
                border-left-color: #ff6b6b;
                background: linear-gradient(135deg, #fff5f5 0%, #ffe8e8 100%);
            }
            .announcement-title {
                font-size: 1.1rem;
                font-weight: 600;
                color: #2d3748;
                margin-bottom: 0.5rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            .announcement-content {
                color: #4a5568;
                line-height: 1.6;
                margin-bottom: 0.5rem;
            }
            .announcement-date {
                font-size: 0.85rem;
                color: #718096;
                text-align: right;
            }
            .announcement-priority-badge {
                display: inline-block;
                background: #ff6b6b;
                color: white;
                padding: 0.2rem 0.6rem;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 500;
                margin-left: 0.5rem;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="announcement-container">', unsafe_allow_html=True)
            st.markdown('<h3 style="color: white; margin-bottom: 1rem; text-align: center;">系统公告</h3>', unsafe_allow_html=True)
            
            # 显示公告（最多显示3条，优先显示高优先级）
            display_count = min(3, len(announcements))
            for i, announcement in enumerate(announcements[:display_count]):
                priority_class = "high-priority" if announcement.get("priority") == "high" else ""
                priority_badge = '<span class="announcement-priority-badge">重要</span>' if announcement.get("priority") == "high" else ""
                
                announcement_html = f"""
                <div class="announcement-item {priority_class}">
                    <div class="announcement-title">
                        {announcement.get('title', '公告')} {priority_badge}
                    </div>
                    <div class="announcement-content">
                        {announcement.get('content', '')}
                    </div>
                    <div class="announcement-date">
                        {announcement.get('date', '')}
                    </div>
        </div>
                """
                st.markdown(announcement_html, unsafe_allow_html=True)
            
            if len(announcements) > display_count:
                st.info(f"还有 {len(announcements) - display_count} 条公告，请查看完整公告列表")
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            # 没有公告时显示占位提示（可选）
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                        border-radius: 12px;
                        padding: 2rem;
                        text-align: center;
                        margin: 1rem 0;
                        border: 2px dashed #cbd5e0;">
                <p style="color: #718096; font-size: 1rem; margin: 0;">暂无系统公告</p>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        # 如果加载失败，显示默认内容
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                    border-radius: 12px;
                    padding: 2rem;
                    text-align: center;
                    margin: 1rem 0;
                    border: 2px dashed #cbd5e0;">
            <p style="color: #718096; font-size: 1rem; margin: 0;">公告栏加载中...</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 分隔线
    st.markdown("---")
