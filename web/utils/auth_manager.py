"""
用户认证管理器
处理用户登录、权限验证等功能
支持前端缓存登录状态，10分钟无操作自动失效
"""

import streamlit as st
import hashlib
import os
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
import time

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('auth')

# 导入用户活动记录器
try:
    from .user_activity_logger import user_activity_logger
except ImportError:
    user_activity_logger = None
    logger.warning("⚠️ 用户活动记录器导入失败")

class AuthManager:
    """用户认证管理器"""
    
    def __init__(self):
        self.users_file = Path(__file__).parent.parent / "config" / "users.json"
        self.session_timeout = 600  # 10分钟超时
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        """确保用户配置文件存在"""
        self.users_file.parent.mkdir(exist_ok=True)
        
        if not self.users_file.exists():
            # 创建默认用户配置
            default_users = {
                "admin": {
                    "password_hash": self._hash_password("admin123"),
                    "role": "admin",
                    "permissions": ["analysis", "batch_analysis", "config", "admin"],
                    "points": 0,
                    "created_at": time.time()
                },
                "user": {
                    "password_hash": self._hash_password("user123"),
                    "role": "user", 
                    "permissions": ["analysis"],
                    "points": 10,
                    "created_at": time.time()
                }
            }
            
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(default_users, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ 用户认证系统初始化完成")
            logger.info(f"📁 用户配置文件: {self.users_file}")
    
    def _inject_auth_cache_js(self):
        """注入前端认证缓存JavaScript代码"""
        js_code = """
        <script>
        // 认证缓存管理
        window.AuthCache = {
            // 保存登录状态到localStorage
            saveAuth: function(userInfo) {
                const authData = {
                    userInfo: userInfo,
                    loginTime: Date.now(),
                    lastActivity: Date.now()
                };
                localStorage.setItem('tradingagents_auth', JSON.stringify(authData));
                console.log('✅ 登录状态已保存到前端缓存');
            },
            
            // 从localStorage获取登录状态
            getAuth: function() {
                try {
                    const authData = localStorage.getItem('tradingagents_auth');
                    if (!authData) return null;
                    
                    const data = JSON.parse(authData);
                    const now = Date.now();
                    const timeout = 10 * 60 * 1000; // 10分钟
                    
                    // 检查是否超时
                    if (now - data.lastActivity > timeout) {
                        this.clearAuth();
                        console.log('⏰ 登录状态已过期，自动清除');
                        return null;
                    }
                    
                    // 更新最后活动时间
                    data.lastActivity = now;
                    localStorage.setItem('tradingagents_auth', JSON.stringify(data));
                    
                    return data.userInfo;
                } catch (e) {
                    console.error('❌ 读取登录状态失败:', e);
                    this.clearAuth();
                    return null;
                }
            },
            
            // 清除登录状态
            clearAuth: function() {
                localStorage.removeItem('tradingagents_auth');
                console.log('🧹 登录状态已清除');
            },
            
            // 更新活动时间
            updateActivity: function() {
                const authData = localStorage.getItem('tradingagents_auth');
                if (authData) {
                    try {
                        const data = JSON.parse(authData);
                        data.lastActivity = Date.now();
                        localStorage.setItem('tradingagents_auth', JSON.stringify(data));
                    } catch (e) {
                        console.error('❌ 更新活动时间失败:', e);
                    }
                }
            }
        };
        
        // 监听用户活动，更新最后活动时间
        ['click', 'keypress', 'scroll', 'mousemove'].forEach(event => {
            document.addEventListener(event, function() {
                window.AuthCache.updateActivity();
            }, { passive: true });
        });
        
        // 页面加载时检查登录状态
        document.addEventListener('DOMContentLoaded', function() {
            const authInfo = window.AuthCache.getAuth();
            if (authInfo) {
                console.log('🔄 从前端缓存恢复登录状态:', authInfo.username);
                // 通知Streamlit恢复登录状态
                window.parent.postMessage({
                    type: 'restore_auth',
                    userInfo: authInfo
                }, '*');
            }
        });
        </script>
        """
        st.components.v1.html(js_code, height=0)
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _load_users(self) -> Dict:
        """加载用户配置"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ 加载用户配置失败: {e}")
            return {}

    def _save_users(self, users: Dict) -> bool:
        """保存用户配置"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"❌ 保存用户配置失败: {e}")
            return False
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """
        用户认证
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            (认证成功, 用户信息)
        """
        users = self._load_users()
        
        if username not in users:
            logger.warning(f"⚠️ 用户不存在: {username}")
            # 记录登录失败
            if user_activity_logger:
                user_activity_logger.log_login(username, False, "用户不存在")
            return False, None
        
        user_info = users[username]
        password_hash = self._hash_password(password)
        
        if password_hash == user_info["password_hash"]:
            logger.info(f"✅ 用户登录成功: {username}")
            # 记录登录成功
            if user_activity_logger:
                user_activity_logger.log_login(username, True)
            return True, {
                "username": username,
                "role": user_info["role"],
                "permissions": user_info["permissions"],
                "points": int(user_info.get("points", 0))
            }
        else:
            logger.warning(f"⚠️ 密码错误: {username}")
            # 记录登录失败
            if user_activity_logger:
                user_activity_logger.log_login(username, False, "密码错误")
            return False, None
    
    def check_permission(self, permission: str) -> bool:
        """
        检查当前用户权限
        
        Args:
            permission: 权限名称
            
        Returns:
            是否有权限
        """
        if not self.is_authenticated():
            return False
        
        user_info = st.session_state.get('user_info', {})
        permissions = user_info.get('permissions', [])
        
        return permission in permissions
    
    def is_authenticated(self) -> bool:
        """检查用户是否已认证"""
        # 首先检查session_state中的认证状态
        authenticated = st.session_state.get('authenticated', False)
        login_time = st.session_state.get('login_time', 0)
        current_time = time.time()
        
        logger.debug(f"🔍 [认证检查] authenticated: {authenticated}, login_time: {login_time}, current_time: {current_time}")
        
        if authenticated:
            # 检查会话超时
            time_elapsed = current_time - login_time
            logger.debug(f"🔍 [认证检查] 会话时长: {time_elapsed:.1f}秒, 超时限制: {self.session_timeout}秒")
            
            if time_elapsed > self.session_timeout:
                logger.info(f"⏰ 会话超时，自动登出 (已过时间: {time_elapsed:.1f}秒)")
                self.logout()
                return False
            
            logger.debug(f"✅ [认证检查] 用户已认证且未超时")
            return True
        
        logger.debug(f"❌ [认证检查] 用户未认证")
        return False
    
    def login(self, username: str, password: str) -> bool:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            登录是否成功
        """
        success, user_info = self.authenticate(username, password)
        
        if success:
            st.session_state.authenticated = True
            st.session_state.user_info = user_info
            st.session_state.login_time = time.time()
            
            # 保存到前端缓存 - 使用与前端JavaScript兼容的格式
            current_time_ms = int(time.time() * 1000)  # 转换为毫秒
            auth_data = {
                "userInfo": user_info,  # 使用userInfo而不是user_info
                "loginTime": time.time(),
                "lastActivity": current_time_ms,  # 添加lastActivity字段
                "authenticated": True
            }
            
            save_to_cache_js = f"""
            <script>
            console.log('🔐 保存认证数据到localStorage');
            try {{
                const authData = {json.dumps(auth_data)};
                localStorage.setItem('tradingagents_auth', JSON.stringify(authData));
                console.log('✅ 认证数据已保存到localStorage:', authData);
            }} catch (e) {{
                console.error('❌ 保存认证数据失败:', e);
            }}
            </script>
            """
            st.components.v1.html(save_to_cache_js, height=0)
            
            logger.info(f"✅ 用户 {username} 登录成功，已保存到前端缓存")
            return True
        else:
            st.session_state.authenticated = False
            st.session_state.user_info = None
            return False
    
    def logout(self):
        """用户登出"""
        username = st.session_state.get('user_info', {}).get('username', 'unknown')
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.login_time = None
        
        # 清除前端缓存
        clear_cache_js = """
        <script>
        console.log('🚪 清除认证数据');
        try {
            localStorage.removeItem('tradingagents_auth');
            localStorage.removeItem('tradingagents_last_activity');
            console.log('✅ 认证数据已清除');
        } catch (e) {
            console.error('❌ 清除认证数据失败:', e);
        }
        </script>
        """
        st.components.v1.html(clear_cache_js, height=0)
        
        logger.info(f"✅ 用户 {username} 登出，已清除前端缓存")
        
        # 记录登出活动
        if user_activity_logger:
            user_activity_logger.log_logout(username)
    
    def restore_from_cache(self, user_info: Dict, login_time: float = None) -> bool:
        """
        从前端缓存恢复登录状态
        
        Args:
            user_info: 用户信息
            login_time: 原始登录时间，如果为None则使用当前时间
            
        Returns:
            恢复是否成功
        """
        try:
            # 验证用户信息的有效性
            username = user_info.get('username')
            if not username:
                logger.warning(f"⚠️ 恢复失败: 用户信息中没有用户名")
                return False
            
            # 检查用户是否仍然存在
            users = self._load_users()
            if username not in users:
                logger.warning(f"⚠️ 尝试恢复不存在的用户: {username}")
                return False
            
            # 恢复登录状态，使用原始登录时间或当前时间
            restore_time = login_time if login_time is not None else time.time()
            
            st.session_state.authenticated = True
            st.session_state.user_info = user_info
            st.session_state.login_time = restore_time
            
            logger.info(f"✅ 从前端缓存恢复用户 {username} 的登录状态")
            logger.debug(f"🔍 [恢复状态] login_time: {restore_time}, current_time: {time.time()}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 从前端缓存恢复登录状态失败: {e}")
            return False
    
    def get_current_user(self) -> Optional[Dict]:
        """获取当前用户信息"""
        if self.is_authenticated():
            return st.session_state.get('user_info')
        return None

    # ===== 会员点数相关API =====
    def get_user_points(self, username: str) -> int:
        users = self._load_users()
        return int(users.get(username, {}).get("points", 0))

    def set_user_points(self, username: str, points: int) -> bool:
        users = self._load_users()
        if username not in users:
            return False
        users[username]["points"] = int(max(0, points))
        ok = self._save_users(users)
        # 同步到当前会话
        if ok and self.get_current_user() and self.get_current_user().get("username") == username:
            st.session_state.user_info["points"] = int(max(0, points))
        return ok

    def add_user_points(self, username: str, delta: int) -> bool:
        users = self._load_users()
        if username not in users:
            return False
        users[username]["points"] = int(max(0, int(users[username].get("points", 0)) + int(delta)))
        ok = self._save_users(users)
        if ok and self.get_current_user() and self.get_current_user().get("username") == username:
            st.session_state.user_info["points"] = int(users[username]["points"])
        return ok

    def try_deduct_points(self, username: str, amount: int) -> bool:
        """尝试扣减点数，成功返回True；管理员账户不扣减直接True"""
        users = self._load_users()
        info = users.get(username)
        if not info:
            return False
        if info.get("role") == "admin":
            return True
        current = int(info.get("points", 0))
        if amount <= 0:
            return True
        if current < amount:
            return False
        info["points"] = current - amount
        ok = self._save_users(users)
        if ok and self.get_current_user() and self.get_current_user().get("username") == username:
            # 更新session state中的用户信息
            st.session_state.user_info["points"] = int(info["points"])
            # 强制刷新用户信息显示
            st.session_state.user_info_updated = True
        return ok
    
    def require_permission(self, permission: str) -> bool:
        """
        要求特定权限，如果没有权限则显示错误信息
        
        Args:
            permission: 权限名称
            
        Returns:
            是否有权限
        """
        if not self.check_permission(permission):
            st.error(f"❌ 您没有 '{permission}' 权限，请联系管理员")
            return False
        return True
    
    def change_password(self, username: str, old_password: str, new_password: str, require_old_password: bool = True) -> Tuple[bool, str]:
        """
        修改用户密码
        
        Args:
            username: 用户名
            old_password: 旧密码（修改自己的密码时需要验证）
            new_password: 新密码
            require_old_password: 是否需要验证旧密码（管理员修改他人密码时可设为False）
            
        Returns:
            (是否成功, 消息)
        """
        users = self._load_users()
        
        if username not in users:
            logger.warning(f"⚠️ 用户不存在: {username}")
            return False, "用户不存在"
        
        user_info = users[username]
        
        # 如果需要验证旧密码
        if require_old_password:
            old_password_hash = self._hash_password(old_password)
            if old_password_hash != user_info["password_hash"]:
                logger.warning(f"⚠️ 旧密码错误: {username}")
                return False, "旧密码错误"
        
        # 验证新密码强度
        if not new_password or len(new_password) < 6:
            return False, "新密码长度至少需要6个字符"
        
        # 更新密码
        user_info["password_hash"] = self._hash_password(new_password)
        
        # 如果修改的是当前登录用户，更新session state
        current_user = self.get_current_user()
        if current_user and current_user.get("username") == username:
            # 密码已更新，但需要重新登录
            logger.info(f"✅ 用户 {username} 密码已修改")
        
        if self._save_users(users):
            logger.info(f"✅ 用户 {username} 密码修改成功")
            return True, "密码修改成功"
        else:
            logger.error(f"❌ 用户 {username} 密码修改失败")
            return False, "保存密码失败"
    
    def change_password_by_admin(self, target_username: str, new_password: str) -> Tuple[bool, str]:
        """
        管理员修改其他用户密码（不需要旧密码验证）
        
        Args:
            target_username: 目标用户名
            new_password: 新密码
            
        Returns:
            (是否成功, 消息)
        """
        return self.change_password(target_username, "", new_password, require_old_password=False)

# 全局认证管理器实例
auth_manager = AuthManager()