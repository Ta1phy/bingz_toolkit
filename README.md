# BingZ工具包 - AI工具管理器

一个基于PyQt5开发的AI工具管理软件，支持添加、删除、修改AI工具，以及查看工具详情和直接打开对应网站。

## 功能特点

- ✅ 添加AI工具图标和描述
- ✅ 点击图标查看详细信息
- ✅ 一键打开AI网站
- ✅ 右键菜单管理工具
- ✅ 支持多种图标格式（包括SVG）
- ✅ 简洁美观的网格布局

## 技术栈

- Python 3.6+
- PyQt5 5.15.0+

## 安装依赖

```bash
pip install -r requirements.txt
```

## 直接运行

```bash
python ai_tool_manager.py
```

## 跨平台打包指南

我们使用PyInstaller进行跨平台打包，支持Mac、Windows和Ubuntu系统。

### 1. 安装PyInstaller

```bash
pip install pyinstaller
```

### 2. Mac平台打包

#### 打包命令

```bash
pyinstaller --onefile --windowed --icon=icon/ChatGPT.jpg --name="BingZ工具包" --add-data="ai_tools.json:.", --add-data="icon:icon" ai_tool_manager.py
```

#### 打包说明

- `--onefile`：生成单个可执行文件
- `--windowed`：不显示控制台窗口
- `--icon`：指定应用图标
- `--name`：指定应用名称
- `--add-data`：添加数据文件和文件夹

#### 打包后文件位置

```
dist/BingZ工具包.app
```

### 3. Windows平台打包

#### 打包命令

```cmd
pyinstaller --onefile --windowed --icon=icon/ChatGPT.jpg --name="BingZ工具包" --add-data="ai_tools.json;." --add-data="icon;icon" ai_tool_manager.py
```

#### 注意事项

- Windows系统下使用分号`;`分隔文件路径
- 需要在Windows环境下打包，或使用Wine在Linux/Mac上模拟打包

#### 打包后文件位置

```
dist/BingZ工具包.exe
```

### 4. Ubuntu平台打包

#### 打包命令

```bash
pyinstaller --onefile --windowed --icon=icon/ChatGPT.jpg --name="BingZ工具包" --add-data="ai_tools.json:.", --add-data="icon:icon" ai_tool_manager.py
```

#### 打包说明

- 需要安装必要的系统依赖

```bash
sudo apt-get install -y libxext6 libxrender1 libfontconfig1 libxkbcommon-x11-0 libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xkb1
```

#### 打包后文件位置

```
dist/BingZ工具包
```

## 打包注意事项

1. **跨平台打包限制**：
   - 每个平台最好在各自的环境下打包，以获得最佳兼容性
   - 或使用Docker容器进行跨平台打包

2. **数据文件处理**：
   - 确保`ai_tools.json`和`icon`文件夹正确添加到打包中
   - 程序运行时会自动读取这些文件

3. **图标格式**：
   - 建议使用`.ico`格式在Windows上获得最佳效果
   - Mac建议使用`.icns`格式
   - Linux支持多种格式

4. **版本兼容性**：
   - 确保使用的Python版本与目标平台兼容
   - 建议使用Python 3.8或3.9，获得更好的兼容性

## 项目结构

```
bingz_sci_ai_tools/
├── ai_tool_manager.py    # 主程序文件
├── ai_tools.json         # 工具数据文件
├── icon/                 # 图标文件夹
│   ├── ChatGPT.jpg       # 示例图标
│   ├── GeoGPT.svg        # SVG图标示例
│   └── doubao.png        # 示例图标
├── requirements.txt      # 依赖文件
└── README.md             # 项目说明
```

## 更新日志

### v1.0.0
- 初始版本
- 支持基本的AI工具管理功能
- 支持多种图标格式
- 实现跨平台打包支持

## 许可证

MIT License
