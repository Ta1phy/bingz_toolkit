#!/usr/bin/env python3
import os
import sys
import subprocess
import platform

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
            subprocess.run(["rm", "-rf", folder])

# macOS platform packaging - onefile mode
def build_macos():
    print("Starting macOS application packaging...")
    
    # Use onefile mode to generate a single executable file
    cmd = [
        "pyinstaller",
        "--onefile",  # Use onefile mode to generate a single executable file
        "--windowed",
        "--icon=icon/Bingz.png",
        "--name=BingZ Toolkit",
        "--strip",  # Strip debug symbols to reduce size
        "--add-data=ai_tools.json:.",
        "--add-data=icon:icon",
        "--noconfirm",  # Avoid confirmation prompts
        # Only exclude absolutely unnecessary modules to avoid affecting program operation
        "--exclude-module=tkinter",
        "--exclude-module=unittest",
        "ai_tool_manager.py"
    ]
    
    print(f"Executing command: {' '.join(cmd)}")
    subprocess.run(cmd)
    
    print("macOS application packaging completed!")
    print("Executable location: dist/BingZ Toolkit")
    print("\nOptimization notes:")
    print("- Used --strip parameter to strip debug symbols")
    print("- Excluded multiple unnecessary modules")
    print("- Set icon to icon/Bingz.png")
    print("- Used onefile mode to generate a single executable file")

# Windows平台打包
def build_windows():

    
    # Windows打包命令（注意：实际在Windows环境中需要使用分号分隔，这里为了兼容macOS环境使用冒号）
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--icon=icon/Bingz.png",
        "--name=BingZ工具包",
        "--add-data=ai_tools.json:." ,
        "--add-data=icon:icon",
        "ai_tool_manager.py"
    ]
    
    subprocess.run(cmd)
    


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
    else:
        print("   - macOS (Darwin)")
        print("   - Windows")

if __name__ == "__main__":
    main()