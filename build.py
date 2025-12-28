#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import shutil
import re

# 获取当前版本号
def get_current_version():
    """从ai_tool_manager.py中读取当前版本号"""
    try:
        with open("ai_tool_manager.py", "r", encoding="utf-8") as f:
            content = f.read()
        # 优先匹配AIToolManager类中的self.current_version
        pattern = r'class AIToolManager\(.*?\).*?self\.current_version\s*=\s*"([\d.]+)"'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1)
        # 尝试匹配普通self.current_version = "x.x.x"格式（类属性）
        pattern = r'self\.current_version\s*=\s*"([\d.]+)"'
        match = re.search(pattern, content)
        if match:
            return match.group(1)
        print("警告: 未找到版本号，使用默认值")
        return "1.0"  # 默认版本号
    except Exception as e:
        print(f"获取版本号失败: {e}")
        return "1.0"

# Install dependencies
def install_dependencies():
    print("Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

# Clean old build files
def clean_old_build():
    print("Cleaning old build files...")
    
    for folder in ["build", "dist", "__pycache__"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)

# macOS platform packaging - onefile mode
def build_macos():
    print("Starting macOS application packaging...")
    
    # 获取当前版本号
    version = get_current_version()
    
    # Use onefile mode to generate a single executable file
    cmd = [
        "pyinstaller",
        "--onefile",  # Use onefile mode to generate a single executable file
        "--windowed",
        f"--name=BingZmac_{version}",
        "--icon=icon/Bingz.png",
        "--strip",  # Strip debug symbols to reduce size
        "--add-data=ai_tools.json:.",
        "--add-data=icon:icon",
        "--noconfirm",  # Avoid confirmation prompts
        "ai_tool_manager.py"
    ]
    
    print(f"Executing command: {' '.join(cmd)}")
    subprocess.run(cmd)
    
    print("macOS application packaging completed!")
    print(f"Executable location: dist/BingZmac_{version}")
    print("\nOptimization notes:")
    print("- Used --strip parameter to strip debug symbols")
    print("- Set icon to icon/Bingz.png")
    print("- Used onefile mode to generate a single executable file")

# Windows平台打包
def build_windows():

    # 获取当前版本号
    version = get_current_version()
    
    # Windows打包命令（Windows环境中必须使用分号作为分隔符）
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--icon=icon/Bingz.png",
        f"--name=BingZwin_{version}",
        "--add-data=ai_tools.json;." ,
        "--add-data=icon;icon",
        "--noupx",
        "--noconfirm",
        "ai_tool_manager.py"
    ]
    
    subprocess.run(cmd)
    
    print("Windows application packaging completed!")
    print(f"Executable location: dist/BingZwin_{version}.exe")

# Linux平台打包
def build_linux():
    print("Starting Linux application packaging...")
    
    # 获取当前版本号
    version = get_current_version()
    
    # Linux打包命令
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        f"--name=BingZlinux_{version}",
        "--icon=icon/Bingz.png",
        "--add-data=ai_tools.json:.",
        "--add-data=icon:icon",
        "--noconfirm",
        "ai_tool_manager.py"
    ]
    
    print(f"Executing command: {' '.join(cmd)}")
    subprocess.run(cmd)
    
    print("Linux application packaging completed!")
    print(f"Executable location: dist/BingZlinux_{version}")

# 主函数
def main():
    print("=" * 50)
    
    # 检测当前平台
    current_platform = platform.system()
    
    install_dependencies()
    clean_old_build()
    
    # 根据平台选择打包函数
    if current_platform == "Darwin":
        build_macos()
    elif current_platform == "Windows":
        build_windows()
    elif current_platform == "Linux":
        build_linux()
    else:
        print("支持的平台:")
        print("   - macOS (Darwin)")
        print("   - Windows")
        print("   - Linux")

if __name__ == "__main__":
    main()