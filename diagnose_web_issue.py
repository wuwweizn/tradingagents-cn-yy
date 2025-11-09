#!/usr/bin/env python3
"""
Web界面启动问题诊断工具
帮助快速定位无法访问界面的原因
"""

import os
import sys
import socket
import subprocess
from pathlib import Path
import importlib.util

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_port(port=8501):
    """检查端口是否被占用"""
    print_header("检查端口占用")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    
    if result == 0:
        print(f"❌ 端口 {port} 已被占用")
        print(f"💡 解决方案:")
        print(f"   1. 使用不同端口: streamlit run web/app.py --server.port 8502")
        print(f"   2. 查找并关闭占用端口的进程:")
        if sys.platform == 'win32':
            print(f"      netstat -ano | findstr :{port}")
            print(f"      taskkill /PID <PID> /F")
        else:
            print(f"      lsof -ti:{port} | xargs kill -9")
        return False
    else:
        print(f"✅ 端口 {port} 可用")
        return True

def check_python_version():
    """检查Python版本"""
    print_header("检查Python版本")
    version = sys.version_info
    print(f"当前Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python版本过低，需要 >= 3.10")
        return False
    else:
        print("✅ Python版本符合要求")
        return True

def check_virtual_env():
    """检查虚拟环境"""
    print_header("检查虚拟环境")
    in_venv = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )
    
    if in_venv:
        print(f"✅ 在虚拟环境中")
        print(f"   虚拟环境路径: {sys.prefix}")
    else:
        print(f"⚠️  未检测到虚拟环境（可选，但建议使用）")
        print(f"💡 建议创建虚拟环境:")
        print(f"   python -m venv env")
        print(f"   .\\env\\Scripts\\activate  # Windows")
        print(f"   source env/bin/activate  # Linux/macOS")
    
    return True

def check_dependencies():
    """检查依赖包"""
    print_header("检查依赖包")
    dependencies = {
        'streamlit': 'Streamlit Web框架',
        'tradingagents': 'TradingAgents主模块',
        'dotenv': '环境变量加载',
        'pandas': '数据处理',
        'plotly': '图表绘制'
    }
    
    all_ok = True
    for module, description in dependencies.items():
        try:
            if module == 'tradingagents':
                # 特殊处理tradingagents模块
                project_root = Path(__file__).parent
                sys.path.insert(0, str(project_root))
                import tradingagents
                print(f"✅ {module} ({description}) - 已安装")
            else:
                __import__(module)
                print(f"✅ {module} ({description}) - 已安装")
        except ImportError:
            print(f"❌ {module} ({description}) - 未安装")
            all_ok = False
            if module == 'tradingagents':
                print(f"💡 解决方案: pip install -e .")
            else:
                print(f"💡 解决方案: pip install {module}")
    
    return all_ok

def check_project_structure():
    """检查项目结构"""
    print_header("检查项目结构")
    project_root = Path(__file__).parent
    required_files = [
        'web/app.py',
        'tradingagents/__init__.py',
        'start_web.py',
        '.env'
    ]
    
    all_ok = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path} - 存在")
        else:
            print(f"❌ {file_path} - 不存在")
            all_ok = False
    
    return all_ok

def check_env_file():
    """检查.env文件"""
    print_header("检查环境配置")
    project_root = Path(__file__).parent
    env_file = project_root / '.env'
    
    if not env_file.exists():
        print("⚠️  .env文件不存在")
        print("💡 可以创建.env文件或使用默认配置")
        return True
    
    print("✅ .env文件存在")
    
    # 检查关键配置（不显示敏感信息）
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'DASHSCOPE_API_KEY' in content or 'OPENAI_API_KEY' in content:
                print("✅ 检测到API密钥配置")
            else:
                print("⚠️  未检测到API密钥配置（可选）")
    except Exception as e:
        print(f"⚠️  读取.env文件失败: {e}")
    
    return True

def check_streamlit_config():
    """检查Streamlit配置"""
    print_header("检查Streamlit配置")
    project_root = Path(__file__).parent
    config_dir = project_root / '.streamlit'
    config_file = config_dir / 'config.toml'
    
    if config_file.exists():
        print("✅ Streamlit配置文件存在")
    else:
        print("⚠️  Streamlit配置文件不存在（将使用默认配置）")
    
    return True

def test_import():
    """测试模块导入"""
    print_header("测试模块导入")
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        from web import app
        print("✅ web.app模块可以导入")
        return True
    except Exception as e:
        print(f"❌ web.app模块导入失败: {e}")
        print(f"💡 解决方案:")
        print(f"   1. 确保在项目根目录运行此脚本")
        print(f"   2. 运行: pip install -e .")
        print(f"   3. 检查PYTHONPATH环境变量")
        return False

def check_running_processes():
    """检查是否有Streamlit进程在运行"""
    print_header("检查运行中的进程")
    if sys.platform == 'win32':
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe'],
                capture_output=True,
                text=True
            )
            if 'streamlit' in result.stdout.lower() or 'python' in result.stdout.lower():
                print("⚠️  检测到Python进程在运行")
                print("💡 可能是之前的Streamlit进程未关闭")
                print("💡 可以尝试:")
                print("   taskkill /F /IM python.exe")
            else:
                print("✅ 未检测到冲突的Python进程")
        except Exception:
            print("⚠️  无法检查进程（需要管理员权限）")
    else:
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True
            )
            if 'streamlit' in result.stdout.lower():
                print("⚠️  检测到Streamlit进程在运行")
            else:
                print("✅ 未检测到冲突的Streamlit进程")
        except Exception:
            print("⚠️  无法检查进程")
    
    return True

def suggest_solutions():
    """提供解决方案建议"""
    print_header("解决方案建议")
    print("如果以上检查都通过但仍无法访问界面，请尝试:")
    print()
    print("1. 使用推荐的启动方式:")
    print("   python start_web.py")
    print()
    print("2. 手动启动Streamlit:")
    print("   streamlit run web/app.py --server.port 8501 --server.address localhost")
    print()
    print("3. 检查防火墙设置:")
    print("   确保端口8501未被防火墙阻止")
    print()
    print("4. 查看详细错误日志:")
    print("   python start_web.py > startup.log 2>&1")
    print()
    print("5. 如果使用Docker:")
    print("   docker-compose logs web")
    print("   docker-compose ps")
    print()
    print("6. 重新安装项目:")
    print("   pip install -e .")
    print()

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  TradingAgents-CN Web界面启动问题诊断工具")
    print("=" * 60)
    
    results = {
        '端口检查': check_port(),
        'Python版本': check_python_version(),
        '虚拟环境': check_virtual_env(),
        '依赖包': check_dependencies(),
        '项目结构': check_project_structure(),
        '环境配置': check_env_file(),
        'Streamlit配置': check_streamlit_config(),
        '模块导入': test_import(),
        '运行进程': check_running_processes()
    }
    
    print_header("诊断总结")
    all_passed = all(results.values())
    
    for check, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
    
    if all_passed:
        print("\n✅ 所有检查通过！")
        print("💡 如果仍无法访问界面，请查看上面的解决方案建议")
    else:
        print("\n❌ 发现问题，请根据上述提示修复")
    
    suggest_solutions()

if __name__ == "__main__":
    main()

