import json
import os
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple, Optional


def _get_storage_path(username: Optional[str] = None) -> Path:
    """获取授权信息存储路径（按用户隔离）"""
    # 授权信息存放在项目 web 目录下隐藏文件，按用户隔离
    base = Path(__file__).parent.parent
    if username:
        # 按用户存储：.batch_license_{username}.json
        return base / f'.batch_license_{username}.json'
    else:
        # 兼容旧版本：全局存储（如果没有用户名）
        return base / '.batch_license.json'


def _load_license(username: Optional[str] = None) -> dict:
    """加载授权信息（按用户隔离）"""
    p = _get_storage_path(username)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def _save_license(data: dict, username: Optional[str] = None) -> None:
    """保存授权信息（按用户隔离）"""
    p = _get_storage_path(username)
    try:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        # 目录不可写等情况忽略，保持无激活
        pass


def _generate_machine_code(username: Optional[str] = None) -> str:
    """生成机器码（包含用户名以确保每个用户的机器码不同）"""
    # 使用 MAC 地址、主机名和用户名生成稳定可读的机器码（仅数字）
    try:
        mac_int = uuid.getnode()
        host = os.environ.get('COMPUTERNAME') or os.environ.get('HOSTNAME') or 'HOST'
        # 包含用户名，确保不同用户在同一台机器上得到不同的机器码
        username_part = username or 'GLOBAL'
        base_str = f"{mac_int}_{host}_{username_part}"
        base_num = abs(hash(base_str))
        code = str(base_num)
        # 取最后 10 位作为机器码，全部是数字
        return code[-10:] if len(code) >= 10 else code.zfill(10)
    except Exception:
        return '0000000000'


def get_or_create_machine_code(username: Optional[str] = None) -> str:
    """获取或创建机器码（按用户隔离）"""
    data = _load_license(username)
    code = data.get('machine_code')
    if not code:
        code = _generate_machine_code(username)
        data['machine_code'] = code
        data.setdefault('activated', False)
        _save_license(data, username)
    return code


def is_activated(username: Optional[str] = None) -> bool:
    """检查是否已激活（按用户隔离）"""
    data = _load_license(username)
    return bool(data.get('activated'))


def expected_password(now: datetime, machine_code: str) -> int:
    """计算期望的激活码"""
    y, m, d, h = now.year, now.month, now.day, now.hour
    last3 = int(machine_code[-3:]) if machine_code[-3:].isdigit() else 0
    return (y + m + d + h) * 7 + last3


def verify_and_activate(input_password: str, username: Optional[str] = None) -> Tuple[bool, str]:
    """校验密码并激活（按用户隔离）
    
    Args:
        input_password: 用户输入的激活码
        username: 用户名，如果提供则按用户隔离存储激活状态
    
    返回：(是否成功, 提示信息)
    """
    data = _load_license(username)
    # 确保使用正确的机器码（先尝试从数据中获取，如果没有则生成并保存）
    code = data.get('machine_code')
    if not code:
        code = get_or_create_machine_code(username)
        data['machine_code'] = code
        _save_license(data, username)
    
    try:
        now = datetime.now()
        exp = expected_password(now, code)
        input_pwd = str(input_password).strip()
        
        # 允许当前小时和前一个小时的激活码（处理时间边界情况）
        prev_hour_time = now - timedelta(hours=1)
        exp_prev = expected_password(prev_hour_time, code)
        
        if input_pwd == str(exp) or input_pwd == str(exp_prev):
            data['activated'] = True
            data['machine_code'] = code  # 确保保存机器码
            _save_license(data, username)
            return True, '激活成功'
        else:
            return False, '激活码错误'
    except Exception as e:
        return False, f'激活异常: {e}'


