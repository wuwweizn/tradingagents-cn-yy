#!/usr/bin/env python3
"""
密码管理模块
提供Web UI界面修改密码功能
"""

import streamlit as st
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# 导入认证管理器
try:
    from web.utils.auth_manager import auth_manager
except ImportError:
    try:
        from ..utils.auth_manager import auth_manager  # type: ignore
    except ImportError:
        try:
            from utils.auth_manager import auth_manager
        except ImportError:
            st.error("❌ 无法导入认证管理器")
            st.stop()


def render_password_management():
    """渲染密码管理界面"""
    
    # 检查是否已登录
    if not auth_manager.is_authenticated():
        st.error("❌ 请先登录")
        return
    
    current_user = auth_manager.get_current_user()
    if not current_user:
        st.error("❌ 无法获取当前用户信息")
        return
    
    current_username = current_user.get("username")
    current_role = current_user.get("role", "user")
    is_admin = current_role == "admin"
    
    st.title("🔐 密码管理")
    st.markdown("---")
    
    # 创建两个标签页：修改自己的密码 和 管理员修改他人密码
    if is_admin:
        tab1, tab2 = st.tabs(["📝 修改我的密码", "👥 管理员修改密码"])
    else:
        tab1 = None
        tab2 = None
        # 非管理员只显示修改自己的密码
        st.subheader("📝 修改我的密码")
    
    # 标签页1：修改自己的密码
    if tab1 is not None:
        with tab1:
            render_change_own_password(current_username)
    else:
        render_change_own_password(current_username)
    
    # 标签页2：管理员修改他人密码（仅管理员可见）
    if is_admin and tab2 is not None:
        with tab2:
            render_admin_change_password()


def render_change_own_password(username: str):
    """渲染修改自己密码的表单"""
    
    st.markdown("""
    ### 🔒 修改我的密码
    
    请输入您的当前密码和新密码来修改账户密码。
    
    **密码要求：**
    - 密码长度至少6个字符
    - 建议使用包含字母、数字和特殊字符的强密码
    """)
    
    with st.form("change_own_password_form", clear_on_submit=False):
        current_password = st.text_input(
            "当前密码",
            type="password",
            help="请输入您当前的登录密码",
            autocomplete="current-password"
        )
        
        new_password = st.text_input(
            "新密码",
            type="password",
            help="请输入新密码（至少6个字符）",
            autocomplete="new-password"
        )
        
        confirm_password = st.text_input(
            "确认新密码",
            type="password",
            help="请再次输入新密码以确认",
            autocomplete="new-password"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submitted = st.form_submit_button("🔐 修改密码", type="primary")
    
    if submitted:
        # 验证输入
        if not current_password:
            st.error("❌ 请输入当前密码")
            return
        
        if not new_password:
            st.error("❌ 请输入新密码")
            return
        
        if len(new_password) < 6:
            st.error("❌ 新密码长度至少需要6个字符")
            return
        
        if new_password != confirm_password:
            st.error("❌ 两次输入的新密码不一致")
            return
        
        if new_password == current_password:
            st.warning("⚠️ 新密码不能与当前密码相同")
            return
        
        # 执行密码修改
        with st.spinner("正在修改密码..."):
            success, message = auth_manager.change_password(
                username=username,
                old_password=current_password,
                new_password=new_password,
                require_old_password=True
            )
        
        if success:
            st.success(f"✅ {message}")
            st.info("""
            **重要提示：**
            - 密码已成功修改
            - 建议您重新登录以确保安全
            - 如需要，您可以点击侧边栏的"退出"按钮，然后使用新密码重新登录
            """)
            # 可选：自动登出
            if st.button("🚪 退出登录并重新登录"):
                auth_manager.logout()
                st.rerun()
        else:
            st.error(f"❌ {message}")


def render_admin_change_password():
    """渲染管理员修改他人密码的表单"""
    
    # 检查管理员权限
    if not auth_manager.check_permission("admin"):
        st.error("❌ 您没有管理员权限")
        return
    
    st.markdown("""
    ### 👥 管理员修改密码
    
    作为管理员，您可以直接修改任意用户的密码，无需验证旧密码。
    
    **注意事项：**
    - 请确保目标用户存在
    - 密码长度至少6个字符
    - 修改密码后，用户需要使用新密码登录
    """)
    
    # 加载用户列表（使用auth_manager的方法）
    try:
        # 使用auth_manager的内部方法加载用户列表
        users = auth_manager._load_users()
        usernames = list(users.keys())
    except Exception as e:
        st.error(f"❌ 加载用户列表失败: {e}")
        usernames = []
    
    # 获取当前用户名（在表单外获取，避免作用域问题）
    current_user = auth_manager.get_current_user()
    current_username = current_user.get("username") if current_user else None
    
    with st.form("admin_change_password_form", clear_on_submit=False):
        target_username = st.selectbox(
            "选择要修改密码的用户",
            usernames,
            help="选择要修改密码的用户账户"
        )
        
        new_password = st.text_input(
            "新密码",
            type="password",
            help="请输入新密码（至少6个字符）",
            autocomplete="new-password"
        )
        
        confirm_password = st.text_input(
            "确认新密码",
            type="password",
            help="请再次输入新密码以确认",
            autocomplete="new-password"
        )
        
        # 安全提示
        is_modifying_self = target_username == current_username
        if is_modifying_self:
            st.warning("""
            ⚠️ **您正在修改自己的密码**
            
            **重要提示：**
            - 通过此方式修改密码**不需要验证旧密码**
            - **强烈建议**使用上方"📝 修改我的密码"标签页，该功能需要验证旧密码，更加安全
            - 如果您忘记了当前密码，可以使用此功能重置
            
            **风险提示：** 如果您的账户被盗用，攻击者也可能通过此功能修改您的密码。请谨慎使用。
            """)
            # 要求额外确认
            require_confirmation = st.checkbox(
                "我已了解风险，确认要继续修改我的密码",
                value=False,
                help="修改自己的密码是一个高风险操作，请确保您是本人操作"
            )
        else:
            require_confirmation = True  # 修改他人密码不需要额外确认
            st.info(f"💡 将修改用户 **{target_username}** 的密码。修改后该用户需要使用新密码重新登录。")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submitted = st.form_submit_button("🔐 修改密码", type="primary")
    
    if submitted:
        # 验证输入
        if not target_username:
            st.error("❌ 请选择要修改密码的用户")
            return
        
        if not new_password:
            st.error("❌ 请输入新密码")
            return
        
        if len(new_password) < 6:
            st.error("❌ 新密码长度至少需要6个字符")
            return
        
        if new_password != confirm_password:
            st.error("❌ 两次输入的新密码不一致")
            return
        
        # 如果修改的是自己的密码，需要额外确认
        if is_modifying_self and not require_confirmation:
            st.error("❌ 修改自己的密码需要勾选确认框以确认您了解风险")
            return
        
        # 执行密码修改
        with st.spinner(f"正在修改用户 {target_username} 的密码..."):
            success, message = auth_manager.change_password_by_admin(
                target_username=target_username,
                new_password=new_password
            )
        
        if success:
            st.success(f"✅ {message}")
            st.info(f"""
            **操作完成：**
            - 用户 {target_username} 的密码已成功修改
            - 该用户需要使用新密码重新登录
            - 当前会话不会受到影响
            """)
            
            # 如果修改的是自己的密码，提供退出选项
            if is_modifying_self:
                st.warning("⚠️ 您已修改了自己的密码，建议退出登录并使用新密码重新登录以确保安全。")
                if st.button("🚪 退出登录并重新登录", key="logout_after_self_password_change"):
                    auth_manager.logout()
                    st.rerun()
        else:
            st.error(f"❌ {message}")


def main():
    """主函数（用于独立运行）"""
    render_password_management()


if __name__ == "__main__":
    main()

