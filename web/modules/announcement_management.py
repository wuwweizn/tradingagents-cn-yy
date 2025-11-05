"""
公告管理模块
管理员可以编辑和发布公告
"""

import json
import time
from pathlib import Path
from datetime import datetime
import streamlit as st

# 认证与日志
try:
    from web.utils.auth_manager import auth_manager
except Exception:
    from ..utils.auth_manager import auth_manager  # type: ignore


ANNOUNCEMENT_FILE = Path(__file__).parent.parent / "config" / "announcements.json"


def _load_announcements(show_error: bool = False) -> list:
    """加载公告列表"""
    try:
        if ANNOUNCEMENT_FILE.exists():
            return json.loads(ANNOUNCEMENT_FILE.read_text(encoding="utf-8"))
        return []
    except Exception as e:
        if show_error:
            st.error(f"读取公告数据失败: {e}")
        return []


def _save_announcements(announcements: list) -> bool:
    """保存公告列表"""
    try:
        ANNOUNCEMENT_FILE.parent.mkdir(parents=True, exist_ok=True)
        ANNOUNCEMENT_FILE.write_text(json.dumps(announcements, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception as e:
        st.error(f"保存公告数据失败: {e}")
        return False


def render_announcement_management():
    """渲染公告管理页面"""
    # 权限保护
    if not auth_manager or not auth_manager.check_permission("admin"):
        st.error("您没有权限访问公告管理")
        return

    st.title("公告管理")
    
    announcements = _load_announcements(show_error=True)
    
    # 显示现有公告
    st.subheader("现有公告")
    if announcements:
        for idx, announcement in enumerate(announcements):
            with st.expander(f"{announcement.get('title', '无标题')} - {announcement.get('date', '')}", expanded=False):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**内容：** {announcement.get('content', '')}")
                    st.markdown(f"**发布时间：** {announcement.get('date', '')}")
                    if announcement.get('priority'):
                        st.markdown(f"**优先级：** {'高' if announcement.get('priority') == 'high' else '普通'}")
                
                with col2:
                    if st.button("删除", key=f"delete_{idx}", type="secondary"):
                        announcements.pop(idx)
                        if _save_announcements(announcements):
                            st.success("删除成功")
                            try:
                                st.rerun()
                            except:
                                st.experimental_rerun()
    else:
        st.info("暂无公告")
    
    st.markdown("---")
    
    # 添加/编辑公告
    st.subheader("添加公告")
    with st.form("announcement_form", clear_on_submit=True):
        title = st.text_input("公告标题", placeholder="例如：系统升级通知")
        content = st.text_area("公告内容", placeholder="请输入公告内容...", height=150)
        priority = st.radio("优先级", ["normal", "high"], format_func=lambda x: "普通" if x == "normal" else "高优先级", horizontal=True)
        
        submitted = st.form_submit_button("发布公告", type="primary")
        if submitted:
            if not title or not content:
                st.error("标题和内容不能为空")
            else:
                new_announcement = {
                    "title": title,
                    "content": content,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "priority": priority
                }
                announcements.append(new_announcement)
                if _save_announcements(announcements):
                    st.success("公告发布成功")
                    try:
                        st.rerun()
                    except:
                        st.experimental_rerun()


def get_active_announcements() -> list:
    """获取当前有效的公告列表（按优先级和日期排序）"""
    announcements = _load_announcements(show_error=False)
    # 按优先级和日期排序：高优先级在前，同优先级按日期倒序
    announcements.sort(key=lambda x: (
        x.get("priority") != "high",  # 高优先级优先
        -time.mktime(time.strptime(x.get("date", "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S")) if x.get("date") else 0
    ))
    return announcements

