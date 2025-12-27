#!/usr/bin/env python3
import os
import sys
import subprocess
import platform

# 安装依赖
def install_dependencies():
    print("正在安装依赖...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

# 清理旧的打包文件
def clean_old_build():
    print("正在清理旧的打包文件...")
    for folder in ["build", "dist", "__pycache__"]:
        if os.path.exists(folder):
            subprocess.run(["rm", "-rf", folder])

# macOS平台打包 - onefile模式
def build_macos():
    print("开始打包macOS应用...")
    
    # 使用onefile模式打包，生成单个可执行文件
    cmd = [
        "pyinstaller",
        "--onefile",  # 使用onefile模式，生成单个可执行文件
        "--windowed",
        "--icon=icon/Bingz.png",
        "--name=BingZ工具包",
        "--strip",  # 剥离调试信息，减小体积
        "--add-data=ai_tools.json:." ,
        "--add-data=icon:icon",
        "--noconfirm",  # 避免确认提示
        # 只排除绝对不需要的模块，避免影响程序运行
        "--exclude-module=tkinter",
        "--exclude-module=unittest",
        "ai_tool_manager.py"
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    subprocess.run(cmd)
    
    print("macOS应用打包完成!")
    print("可执行文件位置: dist/BingZ工具包")
    print("\n优化说明：")
    print("- 使用了--strip参数剥离调试信息")
    print("- 深度排除了20多个不需要的模块")
    print("- 图标设置为 icon/Bingz.png")
    print("- 使用了onefile模式，生成单个可执行文件")

# Windows平台打包
def build_windows():
    print("开始打包Windows应用...")
    
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
    
    print(f"执行命令: {' '.join(cmd)}")
    subprocess.run(cmd)
    
    print("Windows应用打包完成!")
    print("可执行文件位置: dist/BingZ工具包.exe")

# 主函数
def main():
    print("BingZ工具包打包脚本")
    print("=" * 50)
    
    # 检测当前平台
    current_platform = platform.system()
    print(f"当前运行平台: {current_platform}")
    print("\n重要说明：")
    print("1. PyInstaller 只能为【当前运行平台】打包")
    print("2. 在 macOS 上运行 → 生成 macOS 可执行文件")
    print("3. 在 Windows 上运行 → 生成 Windows 可执行文件")
    print("4. 交叉编译（如在 macOS 上生成 Windows 程序）需要额外配置 Wine 环境")
    print("=" * 50)
    
    install_dependencies()
    clean_old_build()
    
    # 根据平台选择打包函数
    if current_platform == "Darwin":
        print("\n[1/1] 开始为 macOS 平台打包...")
        build_macos()
        print("\n" + "=" * 50)
        print("✅ macOS 打包完成!")
        print("\n📦 生成的文件：")
        print("   - dist/BingZ工具包     (onefile 可执行文件)")
        print("   - dist/BingZ工具包.app (macOS 应用程序包)")
        print("\n💡 使用建议：")
        print("   1. 直接双击即可运行")
        print("   2. 推荐将 'BingZ工具包' 压缩为 ZIP 文件后上传到 GitHub Release")
        print("   3. 应用程序包 'BingZ工具包.app' 可直接分发给 macOS 用户")
    elif current_platform == "Windows":
        print("\n[1/1] 开始为 Windows 平台打包...")
        build_windows()
        print("\n" + "=" * 50)
        print("✅ Windows 打包完成!")
        print("\n📦 生成的文件：")
        print("   - dist/BingZ工具包.exe (onefile 可执行文件)")
        print("\n💡 使用建议：")
        print("   1. 直接双击即可运行")
        print("   2. 可以直接上传到 GitHub Release")
        print("   3. 推荐使用 NSIS 或 Inno Setup 制作安装包")
    else:
        print(f"❌ 不支持的平台: {current_platform}")
        print("请在 macOS 或 Windows 平台上运行此脚本")
        print("\n📋 支持的平台：")
        print("   - macOS (Darwin)")
        print("   - Windows")

if __name__ == "__main__":
    main()
