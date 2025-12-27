#!/usr/bin/env python3
import os
import sys
import subprocess
import platform

# 安装依赖
def install_dependencies():
    print("正在安装依赖...")
    # 只安装requirements.txt中的依赖，跳过pyinstaller（网络问题）
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

# 清理旧的打包文件
def clean_old_build():
    print("正在清理旧的打包文件...")
    for folder in ["build", "dist", "__pycache__"]:
        if os.path.exists(folder):
            # 使用Windows兼容的命令清理文件
            if platform.system() == "Windows":
                subprocess.run(["rd", "/s", "/q", folder], shell=True)
            else:
                subprocess.run(["rm", "-rf", folder])

# 检查pyinstaller是否已安装
def check_pyinstaller():
    try:
        subprocess.run(["pyinstaller", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# Windows平台打包
def build_windows():
    print("开始打包Windows应用...")
    
    # 检查pyinstaller是否已安装
    if not check_pyinstaller():
        print("错误: pyinstaller未安装，请手动安装后重试")
        print("安装命令: pip install pyinstaller")
        return
    
    # Windows打包命令（使用分号分隔add-data参数）
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--icon=icon/Bingz.png",
        "--name=BingZ工具包",
        "--add-data=ai_tools.json;." ,
        "--add-data=icon;icon",
        "ai_tool_manager.py"
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("Windows应用打包完成!")
        print("可执行文件位置: dist/BingZ工具包.exe")
    else:
        print("打包失败，请检查错误信息")

# 主函数
def main():
    print("BingZ工具包打包脚本")
    print("=" * 30)
    
    install_dependencies()
    clean_old_build()
    build_windows()
    
    print("\n" + "=" * 30)
    print("脚本执行完成!")
    print("\n安装包制作说明:")
    print("1. 如果打包成功，将dist/BingZ工具包.exe复制到Windows电脑")
    print("2. 推荐使用NSIS或Inno Setup创建安装包")
    print("3. 安装包制作完成后，用户可以在Windows电脑上双击运行安装包")
    print("4. 安装完成后，用户可以在开始菜单或桌面创建快捷方式")

if __name__ == "__main__":
    main()
