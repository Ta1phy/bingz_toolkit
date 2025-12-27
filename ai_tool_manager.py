import sys
import json
import os
import webbrowser
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QLineEdit, QTextEdit,
    QFileDialog, QMessageBox, QScrollArea, QFrame, QDialog,
    QMenu, QProgressBar, QDialogButtonBox
)
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QBrush
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QThread, pyqtSignal

##
# 功能：BingZ工具包主窗口
# 作者：BingZ
# 日期：2025-12-15
# 版本：1.1
# 更新：2025-12-26
# 新增功能：
# 1. 新增搜索工具栏
# 2. 新增工具文件夹
# 3. 新增自定义图标
#
##

# 获取用户数据目录
def get_user_data_dir():
    """获取用户数据目录，用于保存配置和数据文件"""
    if os.name == 'nt':  # Windows
        app_data = os.getenv('APPDATA')
        return os.path.join(app_data, 'BingZ工具包')
    elif os.name == 'posix':  # macOS或Linux
        home = os.path.expanduser('~')
        if sys.platform == 'darwin':  # macOS
            return os.path.join(home, 'Library', 'Application Support', 'BingZ工具包')
        else:  # Linux
            return os.path.join(home, '.config', 'BingZ工具包')
    # 默认返回当前目录
    return os.path.abspath('.')

# 处理PyInstaller打包后路径
def resource_path(relative_path):
    """获取资源文件的绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller打包后
        return os.path.join(sys._MEIPASS, relative_path)
    # 开发环境
    return os.path.join(os.path.abspath('.'), relative_path)

class UpdateChecker(QThread):
    """更新检查线程"""
    update_available = pyqtSignal(dict)
    no_update = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)
    download_progress = pyqtSignal(int, str)
    download_complete = pyqtSignal(str)
    
    def __init__(self, current_version, repo_owner, repo_name):
        super().__init__()
        self.current_version = current_version
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    
    def run(self):
        try:
            # 检查更新
            self.progress.emit(20, "正在检查更新...")
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            self.progress.emit(50, "正在解析更新信息...")
            release_info = response.json()
            
            latest_version = release_info["tag_name"]
            
            # 比较版本号
            if self.is_newer_version(latest_version, self.current_version):
                # 发现新版本
                self.progress.emit(80, "发现新版本...")
                
                # 获取适合当前平台的资产
                asset_info = self.get_platform_asset(release_info["assets"])
                if asset_info:
                    update_data = {
                        "version": latest_version,
                        "release_notes": release_info["body"],
                        "asset": asset_info
                    }
                    self.progress.emit(100, "准备下载更新...")
                    self.update_available.emit(update_data)
                else:
                    self.error.emit("未找到适合当前平台的更新包")
            else:
                self.progress.emit(100, "已是最新版本")
                self.no_update.emit()
        except Exception as e:
            self.error.emit(f"检查更新失败: {str(e)}")
    
    def is_newer_version(self, latest, current):
        """比较版本号，判断是否为新版本"""
        try:
            # 移除版本号前缀（如v1.0.0 -> 1.0.0）
            latest = latest.lstrip('vV')
            current = current.lstrip('vV')
            
            # 分割版本号为数字列表
            latest_parts = list(map(int, latest.split('.')))
            current_parts = list(map(int, current.split('.')))
            
            # 确保版本号位数相同
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            # 比较版本号
            for l, c in zip(latest_parts, current_parts):
                if l > c:
                    return True
                elif l < c:
                    return False
            return False
        except Exception:
            return False
    
    def get_platform_asset(self, assets):
        """获取适合当前平台的资产"""
        current_platform = sys.platform
        
        for asset in assets:
            asset_name = asset["name"].lower()
            
            if current_platform == "darwin":  # macOS
                if "mac" in asset_name or "darwin" in asset_name:
                    return asset
            elif current_platform == "win32":  # Windows
                if "win" in asset_name or "windows" in asset_name:
                    return asset
            elif current_platform == "linux":  # Linux
                if "linux" in asset_name:
                    return asset
        
        return None
    
    def download_update(self, asset_url, save_path):
        """下载更新文件"""
        try:
            self.download_progress.emit(0, "准备下载...")
            response = requests.get(asset_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = int((downloaded / total_size) * 100)
                        self.download_progress.emit(progress, f"下载中: {progress}%")
            
            self.download_complete.emit(save_path)
        except Exception as e:
            self.error.emit(f"下载失败: {str(e)}")

class UpdateDialog(QDialog):
    """更新对话框"""
    def __init__(self, parent=None, current_version="1.0.0", repo_owner="Ta1phy", repo_name="bingz_toolkit"):
        super().__init__(parent)
        self.current_version = current_version
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.update_checker = None
        self.downloading = False
        self.init_ui()
        self.check_for_updates()
    
    def init_ui(self):
        """初始化更新对话框"""
        self.setWindowTitle("检查更新")
        self.setFixedSize(400, 200)
        self.setWindowModality(Qt.ApplicationModal)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("BingZ工具包 - 更新检查")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 当前版本
        version_label = QLabel(f"当前版本: {self.current_version}")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        # 状态标签
        self.status_label = QLabel("正在检查更新...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_button)
        
        # 更新按钮（初始隐藏）
        self.update_button = QPushButton("立即更新")
        self.update_button.clicked.connect(self.download_update)
        self.update_button.hide()
        button_layout.addWidget(self.update_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def check_for_updates(self):
        """开始检查更新"""
        self.update_checker = UpdateChecker(self.current_version, self.repo_owner, self.repo_name)
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.no_update.connect(self.on_no_update)
        self.update_checker.error.connect(self.on_error)
        self.update_checker.progress.connect(self.update_progress)
        self.update_checker.start()
    
    def update_progress(self, progress, status):
        """更新进度"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
    
    def on_update_available(self, update_data):
        """发现更新"""
        self.update_data = update_data
        self.status_label.setText(f"发现新版本: {update_data['version']}")
        self.cancel_button.setText("关闭")
        self.update_button.show()
    
    def on_no_update(self):
        """没有更新"""
        self.status_label.setText("已是最新版本")
        self.cancel_button.setText("关闭")
    
    def on_error(self, error_msg):
        """错误处理"""
        self.status_label.setText(error_msg)
        self.cancel_button.setText("关闭")
    
    def download_update(self):
        """下载更新"""
        self.downloading = True
        self.update_button.hide()
        self.cancel_button.setText("取消")
        
        # 创建下载目录
        download_dir = os.path.join(get_user_data_dir(), "downloads")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        
        # 设置保存路径
        asset_name = self.update_data["asset"]["name"]
        save_path = os.path.join(download_dir, asset_name)
        
        # 更新进度信号连接
        self.update_checker.download_progress.connect(self.update_progress)
        self.update_checker.download_complete.connect(self.on_download_complete)
        self.update_checker.error.connect(self.on_error)
        
        # 开始下载
        self.update_checker.download_update(self.update_data["asset"]["browser_download_url"], save_path)
    
    def on_download_complete(self, save_path):
        """下载完成"""
        self.status_label.setText("更新下载完成！")
        self.cancel_button.setText("关闭")
        QMessageBox.information(self, "下载完成", f"更新已下载到: {save_path}\n请手动安装。")
        self.close()

class AIToolManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tools = []
        
        # 版本信息
        self.current_version = "1.1"
        self.repo_owner = "Ta1phy"
        self.repo_name = "bingz_toolkit"
        
        # 创建用户数据目录
        self.data_dir = get_user_data_dir()
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # 设置数据文件路径
        self.data_file = os.path.join(self.data_dir, "ai_tools.json")
        
        # 如果数据文件不存在，从程序目录复制初始数据
        initial_data_file = resource_path("ai_tools.json")
        if not os.path.exists(self.data_file) and os.path.exists(initial_data_file):
            import shutil
            shutil.copy(initial_data_file, self.data_file)
        
        self.init_ui()
        self.load_tools()
        
    def init_ui(self):
        self.setWindowTitle("BingZv1.0")
        
        # 设置窗口图标
        icon_path = resource_path("icon/Bingz.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setFixedSize(425, 500)  # 设置固定大小，不允许鼠标拖动修改
        
        # 主布局
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: white;")  # 固定白色背景
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部控制栏
        top_layout = QHBoxLayout()
        
        # 标题
        title_label = QLabel("BingZ工具包")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: black; padding: 2px 8px; border-radius: 8px;")
        top_layout.addWidget(title_label)
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索工具...")
        self.search_input.setStyleSheet(
            "font-size: 12px; padding: 6px 12px; "
            "border: 1px solid #ddd; border-radius: 15px; "
            "width: 150px;"
        )
        self.search_input.textChanged.connect(self.filter_tools)
        top_layout.addWidget(self.search_input)
        
        # 添加工具按钮（圆角矩形样式）
        add_button = QPushButton("添加")
        add_button.setStyleSheet(
            "QPushButton { "
            "font-size: 12px; padding: 6px 12px; "
            "background-color: #4CAF50; color: white; "
            "border: 2px solid black; border-radius: 15px; "
            " } "
            "QPushButton:hover { "
            "background-color: #388E3C; "
            "border: 2px solid black; "
            " } "
        )
        add_button.clicked.connect(self.add_tool_dialog)

        # 检查更新按钮（圆角矩形样式）
        update_button = QPushButton("检查更新")
        update_button.setStyleSheet(
            "QPushButton { "
            "font-size: 12px; padding: 6px 12px; "
            "background-color: #2196F3; color: white; "
            "border: 2px solid black; border-radius: 15px; "
            " } "
            "QPushButton:hover { "
            "background-color: #1976D2; "
            "border: 2px solid black; "
            " } "
        )
        update_button.clicked.connect(self.check_for_updates)

        
        top_layout.addStretch()
        top_layout.addWidget(add_button)
        top_layout.addWidget(update_button)
        
        main_layout.addLayout(top_layout)
        
        # 工具展示区域（网格布局）
        self.tools_container = QWidget()
        self.tools_container.setFixedSize(400, 400)  # 设置固定尺寸，确保图标位置不变
        self.tools_layout = QGridLayout(self.tools_container)
        self.tools_layout.setSpacing(20)  # 减小间距，实现紧凑布局
        self.tools_layout.setContentsMargins(10, 10, 10, 10)  # 左右各10px边距，确保留白均匀
        self.tools_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)  # 设置顶部水平居中对齐
        
        # 设置每列宽度相等，确保均匀分布
        for col in range(4):
            self.tools_layout.setColumnStretch(col, 1)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(False)  # 关闭自动调整大小，确保图标位置固定
        scroll_area.setWidget(self.tools_container)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_layout.addWidget(scroll_area)
        
        self.setCentralWidget(central_widget)
    
    
    
    def load_tools(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.tools = json.load(f)
            self.display_tools()
    
    def save_tools(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.tools, f, ensure_ascii=False, indent=2)
    
    def display_tools(self, tools=None):
        # 使用传入的工具列表，如果没有则使用所有工具
        display_tools = tools if tools is not None else self.tools
        
        # 对工具进行排序，文件夹类型置顶
        sorted_tools = sorted(display_tools, key=lambda x: (x.get('type', 'tool') != 'folder', x['name']))
        
        # 清空现有工具
        for i in reversed(range(self.tools_layout.count())):
            widget = self.tools_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        # 显示工具（网格排列，一行4个，紧凑布局）
        rows = 0
        cols = 4  # 4列布局，紧凑排列
        for i, tool in enumerate(sorted_tools):
            tool_widget = self.create_tool_widget(tool)
            row = i // cols
            col = i % cols
            self.tools_layout.addWidget(tool_widget, row, col)
            rows = row + 1
    
    def filter_tools(self):
        """根据搜索文本过滤工具"""
        search_text = self.search_input.text().lower().strip()
        
        if not search_text:
            # 搜索文本为空，显示所有工具
            self.display_tools()
            return
        
        # 过滤工具，匹配名称、描述、功能等
        filtered_tools = []
        for tool in self.tools:
            # 检查工具的各个字段是否包含搜索文本
            if (search_text in tool["name"].lower() or
                search_text in tool["description"].lower() or
                search_text in tool["features"].lower() or
                search_text in tool["url"].lower()):
                filtered_tools.append(tool)
        
        # 显示过滤后的工具
        self.display_tools(filtered_tools)
    
    def create_tool_widget(self, tool):
        widget = QWidget()
        widget.setFixedSize(80, 100)  # 适合网格布局的工具项大小
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)  # 内部边距
        layout.setSpacing(5)  # 内部间距
        layout.setAlignment(Qt.AlignCenter)  # 内部元素居中对齐
        
        # 确定工具类型，默认为普通工具
        tool_type = tool.get("type", "tool")
        
        # 图标按钮（网格风格）
        icon_button = QPushButton()
        icon_button.setFixedSize(60, 60)  # 图标按钮大小
        
        if tool_type == "folder":
            # 文件夹类型样式
            icon_button.setStyleSheet(
                "QPushButton {border: 2px solid #2196F3; background-color: #E3F2FD; border-radius: 12px;}"
                "QPushButton:hover {background-color: #BBDEFB;}"
            )
            # 文件夹点击事件
            icon_button.clicked.connect(lambda: self.open_toolkit(tool))
        else:
            # 普通工具样式
            icon_button.setStyleSheet(
                "QPushButton {border: none; background: transparent; border-radius: 12px;}"
                "QPushButton:hover {background-color: rgba(0, 0, 0, 0.1);}"
            )
            # 普通工具点击事件
            icon_button.clicked.connect(lambda: self.show_tool_detail(tool))
        
        # 设置右键菜单
        icon_button.setContextMenuPolicy(Qt.CustomContextMenu)
        icon_button.customContextMenuRequested.connect(lambda pos, btn=icon_button, t=tool: self.show_context_menu(pos, btn, t))
        
        # 绘制图标
        icon_label = QLabel(icon_button)
        icon_label.setGeometry(5, 5, 50, 50)
        icon_label.setAlignment(Qt.AlignCenter)
        
        if tool_type == "folder":
            # 文件夹图标
            icon_path = tool.get("icon_path", "")
            
            # 处理相对路径
            if icon_path.startswith("./"):
                icon_path = resource_path(icon_path[2:])
            
            if icon_path and os.path.exists(icon_path):
                # 检查文件扩展名，支持SVG和其他图片格式
                file_ext = os.path.splitext(icon_path)[1].lower()
                
                if file_ext == ".svg":
                    # SVG图标处理
                    svg_widget = QSvgWidget(icon_path, icon_button)
                    svg_widget.setGeometry(5, 5, 50, 50)
                    icon_label.hide()  # 隐藏文字标签
                else:
                    # 其他图片格式处理
                    pixmap = QPixmap(icon_path)
                    scaled_pixmap = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    # 创建圆角矩形遮罩
                    rounded_pixmap = QPixmap(scaled_pixmap.size())
                    rounded_pixmap.fill(Qt.transparent)
                    painter = QPainter(rounded_pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.setBrush(QBrush(scaled_pixmap))
                    painter.setPen(Qt.NoPen)
                    painter.drawRoundedRect(0, 0, scaled_pixmap.width(), scaled_pixmap.height(), 10, 10)
                    painter.end()
                    
                    icon_label.setPixmap(rounded_pixmap)
            else:
                # 默认文件夹图标
                icon_label.setStyleSheet(
                    "QLabel {"
                    "    font-size: 32px; font-weight: bold; color: #2196F3;"
                    "    background-color: transparent;"
                    "}"
                )
                icon_label.setText("📁")
        else:
            # 普通工具图标
            icon_path = tool.get("icon_path", "")
            
            # 处理相对路径
            if icon_path.startswith("./"):
                icon_path = resource_path(icon_path[2:])
            
            if icon_path and os.path.exists(icon_path):
                # 检查文件扩展名，支持SVG和其他图片格式
                file_ext = os.path.splitext(icon_path)[1].lower()
                
                if file_ext == ".svg":
                    # SVG图标处理
                    svg_widget = QSvgWidget(icon_path, icon_button)
                    svg_widget.setGeometry(5, 5, 50, 50)
                    icon_label.hide()  # 隐藏文字标签
                else:
                    # 其他图片格式处理
                    pixmap = QPixmap(icon_path)
                    scaled_pixmap = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    # 创建圆角矩形遮罩
                    rounded_pixmap = QPixmap(scaled_pixmap.size())
                    rounded_pixmap.fill(Qt.transparent)
                    painter = QPainter(rounded_pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.setBrush(QBrush(scaled_pixmap))
                    painter.setPen(Qt.NoPen)
                    painter.drawRoundedRect(0, 0, scaled_pixmap.width(), scaled_pixmap.height(), 10, 10)
                    painter.end()
                    
                    icon_label.setPixmap(rounded_pixmap)
            else:
                # 默认图标（使用文字，网格布局大小）
                icon_label.setText(tool["name"][0])
                icon_label.setStyleSheet("font-size: 20px; font-weight: bold; background-color: #4CAF50; color: white; border-radius: 10px; width: 50px; height: 50px;")
        
        layout.addWidget(icon_button)
        
        # 名称（小字体，固定在图标正下方）
        name_label = QLabel(tool["name"])
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-size: 10px; color: #333333;")  # 适合网格布局的字体大小
        name_label.setWordWrap(True)
        name_label.setFixedWidth(60)  # 固定宽度，与图标同宽
        name_label.setFixedHeight(25)  # 固定高度，确保文字完整显示
        layout.addWidget(name_label, alignment=Qt.AlignCenter)  # 确保居中对齐
        
        return widget
    
    def open_toolkit(self, tool):
        """打开嵌套工具包"""
        # 创建新的工具包页面
        toolkit_window = QDialog()
        toolkit_window.setWindowTitle(f"{tool['name']}")
        
        # 设置窗口图标
        icon_path = resource_path("icon/Bingz.png")
        if os.path.exists(icon_path):
            toolkit_window.setWindowIcon(QIcon(icon_path))
        
        toolkit_window.setFixedSize(425, 500)
        toolkit_window.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(toolkit_window)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部控制栏
        top_layout = QHBoxLayout()
        
        # 返回按钮
        back_button = QPushButton("返回")
        back_button.setStyleSheet(
            "QPushButton { "
            "font-size: 12px; padding: 6px 12px; "
            "background-color: #2196F3; color: white; "
            "border: 2px solid black; border-radius: 15px; "
            " } "
            "QPushButton:hover { "
            "background-color: #1976D2; "
            "border: 2px solid black; "
            " } "
        )
        back_button.clicked.connect(toolkit_window.close)
        top_layout.addWidget(back_button)
        
        # 标题
        title_label = QLabel(tool["name"])
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: black; padding: 2px 8px; border-radius: 8px;")
        top_layout.addWidget(title_label)
        
        # 添加工具按钮
        add_button = QPushButton("添加")
        add_button.setStyleSheet(
            "QPushButton { "
            "font-size: 12px; padding: 6px 12px; "
            "background-color: #4CAF50; color: white; "
            "border: 2px solid black; border-radius: 15px; "
            " } "
            "QPushButton:hover { "
            "background-color: #388E3C; "
            "border: 2px solid black; "
            " } "
        )
        top_layout.addWidget(add_button)
        
        # 搜索框
        search_input = QLineEdit()
        search_input.setPlaceholderText("搜索工具...")
        search_input.setStyleSheet(
            "font-size: 12px; padding: 6px 12px; "
            "border: 1px solid #ddd; border-radius: 15px; "
            "width: 150px;"
        )
        top_layout.addWidget(search_input)
        
        top_layout.addStretch()
        
        # 工具展示区域
        tools_container = QWidget()
        tools_container.setFixedSize(400, 400)
        tools_layout = QGridLayout(tools_container)
        tools_layout.setSpacing(20)
        tools_layout.setContentsMargins(10, 10, 10, 10)
        tools_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        
        # 设置每列宽度相等
        for col in range(4):
            tools_layout.setColumnStretch(col, 1)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(False)
        scroll_area.setWidget(tools_container)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 获取嵌套工具
        nested_tools = tool.get("children", [])
        
        # 显示嵌套工具（初始排序）
        def show_tools(tools_list):
            # 对工具进行排序，文件夹类型置顶
            sorted_tools = sorted(tools_list, key=lambda x: (x.get('type', 'tool') != 'folder', x['name']))
            
            # 清空现有工具
            for j in reversed(range(tools_layout.count())):
                widget = tools_layout.itemAt(j).widget()
                if widget is not None:
                    widget.deleteLater()
            
            # 显示过滤后的工具
            for j, nested_tool in enumerate(sorted_tools):
                tool_widget = self.create_tool_widget(nested_tool)
                row = j // cols
                col = j % cols
                tools_layout.addWidget(tool_widget, row, col)
        
        # 初始显示嵌套工具
        show_tools(nested_tools)
        
        # 定义搜索过滤函数
        def filter_nested_tools():
            search_text = search_input.text().lower().strip()
            
            if not search_text:
                display_tools = nested_tools
            else:
                display_tools = []
                for nested_tool in nested_tools:
                    if (search_text in nested_tool["name"].lower() or
                        search_text in nested_tool.get("description", "").lower() or
                        search_text in nested_tool.get("features", "").lower() or
                        search_text in nested_tool.get("url", "").lower()):
                        display_tools.append(nested_tool)
            
            # 显示过滤后的工具（排序后）
            show_tools(display_tools)
        
        # 连接搜索信号
        search_input.textChanged.connect(filter_nested_tools)
        
        # 定义添加工具到文件夹的函数
        def add_tool_to_folder():
            # 创建添加工具对话框
            add_dialog = QDialog(toolkit_window)
            add_dialog.setWindowTitle(f"添加工具到 {tool['name']}")
            
            # 设置窗口图标
            icon_path = resource_path("icon/Bingz.png")
            if os.path.exists(icon_path):
                add_dialog.setWindowIcon(QIcon(icon_path))
            
            add_dialog.setGeometry(300, 300, 400, 450)
            add_layout = QVBoxLayout(add_dialog)
            
            # 工具类型选择
            add_layout.addWidget(QLabel("工具类型:"))
            type_layout = QHBoxLayout()
            
            # 普通工具单选按钮
            import PyQt5.QtWidgets as QtWidgets
            tool_type = QtWidgets.QButtonGroup()
            tool_radio = QtWidgets.QRadioButton("普通工具")
            folder_radio = QtWidgets.QRadioButton("文件夹")
            tool_radio.setChecked(True)  # 默认选择普通工具
            
            tool_type.addButton(tool_radio)
            tool_type.addButton(folder_radio)
            
            type_layout.addWidget(tool_radio)
            type_layout.addWidget(folder_radio)
            add_layout.addLayout(type_layout)
            
            # 名称
            add_layout.addWidget(QLabel("工具名称:"))
            name_input = QLineEdit()
            name_input.setStyleSheet(
                "border: 1px solid #ddd; border-radius: 15px; padding: 4px 8px;"
            )
            add_layout.addWidget(name_input)
            
            # 简介
            add_layout.addWidget(QLabel("简介:"))
            desc_input = QLineEdit()
            desc_input.setStyleSheet(
                "border: 1px solid #ddd; border-radius: 15px; padding: 4px 8px;"
            )
            add_layout.addWidget(desc_input)
            
            # 主要功能
            add_layout.addWidget(QLabel("主要功能:"))
            features_input = QTextEdit()
            features_input.setStyleSheet(
                "border: 1px solid #ddd; border-radius: 15px; padding: 4px 8px;"
            )
            add_layout.addWidget(features_input)
            
            # 网站URL
            url_label = QLabel("网站URL:")
            add_layout.addWidget(url_label)
            url_input = QLineEdit()
            url_input.setStyleSheet(
                "border: 1px solid #ddd; border-radius: 15px; padding: 4px 8px;"
            )
            add_layout.addWidget(url_input)
            
            # 图标路径
            icon_label = QLabel("图标路径:")
            add_layout.addWidget(icon_label)
            icon_layout = QHBoxLayout()
            icon_input = QLineEdit()
            icon_input.setStyleSheet(
                "border: 1px solid #ddd; border-radius: 15px; padding: 4px 8px;"
            )
            icon_layout.addWidget(icon_input)
            
            def browse_icon():
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "选择图标", "", "Image Files (*.png *.jpg *.jpeg *.ico *.svg)"
                )
                if file_path:
                    icon_input.setText(file_path)
            
            browse_button = QPushButton("浏览")
            browse_button.setStyleSheet(
                "font-size: 12px; padding: 4px 8px; "
                "background-color: #9E9E9E; color: white; "
                "border: none; border-radius: 15px;"
            )
            browse_button.clicked.connect(browse_icon)
            icon_layout.addWidget(browse_button)
            add_layout.addLayout(icon_layout)
            
            # 保存按钮
            save_button = QPushButton("保存")
            save_button.setStyleSheet(
                "font-size: 14px; padding: 8px 16px; "
                "background-color: #4CAF50; color: white; "
                "border: none; border-radius: 15px;"
            )
            
            def save_new_tool():
                name = name_input.text().strip()
                desc = desc_input.text().strip()
                features = features_input.toPlainText().strip()
                is_tool = tool_radio.isChecked()
                
                if is_tool:
                    # 普通工具验证
                    url = url_input.text().strip()
                    icon_path = icon_input.text().strip()
                    
                    if not name or not url:
                        QMessageBox.warning(self, "错误", "名称和URL不能为空")
                        return
                    
                    new_tool = {
                        "type": "tool",
                        "name": name,
                        "description": desc,
                        "features": features,
                        "url": url,
                        "icon_path": icon_path
                    }
                else:
                    # 文件夹类型
                    if not name:
                        QMessageBox.warning(self, "错误", "名称不能为空")
                        return
                    
                    new_tool = {
                        "type": "folder",
                        "name": name,
                        "description": desc,
                        "features": features,
                        "children": []
                    }
                
                # 添加到文件夹的children列表
                if "children" not in tool:
                    tool["children"] = []
                tool["children"].append(new_tool)
                
                # 保存到数据文件
                self.save_tools()
                
                # 更新嵌套工具列表
                nested_tools.append(new_tool)
                
                # 刷新显示
                filter_nested_tools()
                
                add_dialog.close()
                QMessageBox.information(self, "成功", f"工具已添加到 {tool['name']}")
            
            save_button.clicked.connect(save_new_tool)
            add_layout.addWidget(save_button)
            
            # 根据选择的类型显示/隐藏某些字段
            def update_fields():
                is_tool = tool_radio.isChecked()
                url_label.setVisible(is_tool)
                url_input.setVisible(is_tool)
                icon_label.setVisible(is_tool)
                icon_input.setVisible(is_tool)
                browse_button.setVisible(is_tool)
            
            tool_radio.toggled.connect(update_fields)
            folder_radio.toggled.connect(update_fields)
            
            add_dialog.exec_()
        
        # 连接添加按钮信号
        add_button.clicked.connect(add_tool_to_folder)
        
        layout.addLayout(top_layout)
        layout.addWidget(scroll_area)
        
        toolkit_window.exec_()
    
    def show_tool_detail(self, tool):
        detail_window = QDialog()
        detail_window.setWindowTitle(f"{tool['name']} - 详情")
        
        # 设置窗口图标
        icon_path = resource_path("icon/Bingz.png")
        if os.path.exists(icon_path):
            detail_window.setWindowIcon(QIcon(icon_path))
        
        detail_window.setFixedSize(375, 350)  # 设置固定大小，缩小一倍，不允许鼠标拖动修改
        detail_window.setStyleSheet("background-color: white;")  # 设置背景颜色为白色
        layout = QVBoxLayout(detail_window)
        layout.setContentsMargins(20, 20, 20, 20)  # 设置适当的边距
        
        # 内容区域
        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignTop)  # 内容向顶端靠
        
        # 图标显示区域
        icon_container = QWidget()
        icon_container.setFixedSize(80, 80)  # 固定图标容器大小
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignCenter)
        
        icon_path = tool.get("icon_path", "")
        
        # 处理相对路径
        if icon_path.startswith("./"):
            icon_path = resource_path(icon_path[2:])
        
        if icon_path and os.path.exists(icon_path):
            # 检查文件扩展名，支持SVG和其他图片格式
            file_ext = os.path.splitext(icon_path)[1].lower()
            
            if file_ext == ".svg":
                # SVG图标处理
                svg_widget = QSvgWidget(icon_path)
                svg_widget.setFixedSize(80, 80)
                icon_layout.addWidget(svg_widget)
            else:
                # 其他图片格式处理
                icon_label = QLabel()
                pixmap = QPixmap(icon_path)
                icon_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                icon_label.setAlignment(Qt.AlignCenter)
                icon_layout.addWidget(icon_label)
        else:
            # 默认图标（使用文字）
            icon_label = QLabel(tool["name"][0])
            icon_label.setStyleSheet("font-size: 32px; font-weight: bold; background-color: #4CAF50; color: white; border-radius: 10px; width: 80px; height: 80px;")
            icon_label.setAlignment(Qt.AlignCenter)
            icon_layout.addWidget(icon_label)
        
        content_layout.addWidget(icon_container, alignment=Qt.AlignCenter)  # 确保图标容器居中显示
        
        # 名称
        name_label = QLabel(tool["name"])
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-size: 11px; font-weight: bold;")  # 进一步减小字体大小
        content_layout.addWidget(name_label)
        
        # 简介
        intro_label = QLabel("简介:")
        intro_label.setStyleSheet("font-size: 10px; font-weight: bold;")  # 减小标签文字大小
        content_layout.addWidget(intro_label)
        
        desc_label = QLabel(tool["description"])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 10px;")  # 减小内容文字大小
        content_layout.addWidget(desc_label)
        
        # 主要功能（改为QLabel，与简介显示一致）
        features_title_label = QLabel("主要功能:")
        features_title_label.setStyleSheet("font-size: 11px; font-weight: bold;")  # 减小标签文字大小
        content_layout.addWidget(features_title_label)
        
        features_label = QLabel(tool["features"])
        features_label.setWordWrap(True)
        features_label.setAlignment(Qt.AlignTop)
        features_label.setStyleSheet("font-size: 11px;")  # 减小内容文字大小
        content_layout.addWidget(features_label)
        
        # 将内容区域添加到主布局
        layout.addLayout(content_layout)
        
        # 添加拉伸，将按钮推到底部
        layout.addStretch(1)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)  # 按钮居中对齐
        
        # 只保留打开网站按钮
        open_button = QPushButton("打开网站")
        open_button.setStyleSheet(
            "QPushButton { "
            "font-size: 12px; padding: 4px 8px; "
            "background-color: #2196F3; color: white; "
            "border: 1px solid black; border-radius: 10px; "
            " } "
            "QPushButton:hover { "
            "background-color: #1976D2; "
            "border: 1px solid black; "
            " } "
        )
        open_button.clicked.connect(lambda checked, url=tool["url"]: webbrowser.open(url))
        button_layout.addWidget(open_button)
        
        layout.addLayout(button_layout)
        
        detail_window.exec_()
    
    def show_context_menu(self, pos, widget, tool):
        """显示右键菜单"""
        menu = QMenu(self)
        
        # 确定工具类型
        tool_type = tool.get("type", "tool")
        
        # 修改内容选项
        edit_action = menu.addAction("修改内容")
        edit_action.triggered.connect(lambda: self.edit_tool_dialog(tool))
        
        # 更改图标选项（所有类型都支持）
        change_icon_action = menu.addAction("更改图标")
        change_icon_action.triggered.connect(lambda: self.change_tool_icon(tool))
        
        # 删除选项
        delete_action = menu.addAction("删除")
        delete_action.triggered.connect(lambda: self.delete_tool(tool))
        
        # 在鼠标位置显示菜单
        menu.exec_(widget.mapToGlobal(pos))
    
    def delete_tool(self, tool):
        """删除AI工具"""
        reply = QMessageBox.question(self, '确认删除', f'确定要删除{tool["name"]}吗？', 
                                    QMessageBox.No | QMessageBox.Yes, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self.tools.remove(tool)
            self.save_tools()
            self.display_tools()
            QMessageBox.information(self, '删除成功', f'{tool["name"]}已成功删除')
    
    def change_tool_icon(self, tool):
        """更改工具图标"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图标", "", "Image Files (*.png *.jpg *.jpeg *.ico *.svg)"
        )
        if file_path:
            # 更新工具图标路径
            tool["icon_path"] = file_path
            self.save_tools()
            self.display_tools()
            QMessageBox.information(self, '成功', f'{tool["name"]}的图标已更新')
    
    def add_tool_dialog(self):
        dialog = QDialog()
        dialog.setWindowTitle("添加AI工具")
        
        # 设置窗口图标
        icon_path = resource_path("icon/Bingz.png")
        if os.path.exists(icon_path):
            dialog.setWindowIcon(QIcon(icon_path))
        
        dialog.setGeometry(300, 300, 400, 450)
        layout = QVBoxLayout(dialog)
        
        # 工具类型选择
        layout.addWidget(QLabel("工具类型:"))
        type_layout = QHBoxLayout()
        
        # 普通工具单选按钮
        import PyQt5.QtWidgets as QtWidgets
        tool_type = QtWidgets.QButtonGroup()
        tool_radio = QtWidgets.QRadioButton("普通工具")
        folder_radio = QtWidgets.QRadioButton("文件夹")
        tool_radio.setChecked(True)  # 默认选择普通工具
        
        tool_type.addButton(tool_radio)
        tool_type.addButton(folder_radio)
        
        type_layout.addWidget(tool_radio)
        type_layout.addWidget(folder_radio)
        layout.addLayout(type_layout)
        
        # 名称
        layout.addWidget(QLabel("工具名称:"))
        name_input = QLineEdit()
        name_input.setStyleSheet(
            "border: 1px solid #ddd; border-radius: 15px; padding: 4px 8px;"
        )
        layout.addWidget(name_input)
        
        # 简介
        layout.addWidget(QLabel("简介:"))
        desc_input = QLineEdit()
        desc_input.setStyleSheet(
            "border: 1px solid #ddd; border-radius: 15px; padding: 4px 8px;"
        )
        layout.addWidget(desc_input)
        
        # 主要功能
        layout.addWidget(QLabel("主要功能:"))
        features_input = QTextEdit()
        features_input.setStyleSheet(
            "border: 1px solid #ddd; border-radius: 15px; padding: 4px 8px;"
        )
        layout.addWidget(features_input)
        
        # 网站URL
        url_label = QLabel("网站URL:")
        layout.addWidget(url_label)
        url_input = QLineEdit()
        url_input.setStyleSheet(
            "border: 1px solid #ddd; border-radius: 15px; padding: 4px 8px;"
        )
        layout.addWidget(url_input)
        
        # 图标路径
        icon_label = QLabel("图标路径:")
        layout.addWidget(icon_label)
        icon_layout = QHBoxLayout()
        icon_input = QLineEdit()
        icon_input.setStyleSheet(
            "border: 1px solid #ddd; border-radius: 15px; padding: 4px 8px;"
        )
        icon_layout.addWidget(icon_input)
        
        def browse_icon():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择图标", "", "Image Files (*.png *.jpg *.jpeg *.ico *.svg)"
            )
            if file_path:
                icon_input.setText(file_path)
        
        browse_button = QPushButton("浏览")
        browse_button.setStyleSheet(
            "font-size: 12px; padding: 4px 8px; "
            "background-color: #9E9E9E; color: white; "
            "border: none; border-radius: 15px;"
        )
        browse_button.clicked.connect(browse_icon)
        icon_layout.addWidget(browse_button)
        layout.addLayout(icon_layout)
        
        # 保存按钮（圆角矩形样式）
        save_button = QPushButton("保存")
        save_button.setStyleSheet(
            "font-size: 14px; padding: 8px 16px; "
            "background-color: #4CAF50; color: white; "
            "border: none; border-radius: 15px;"
        )
        save_button.clicked.connect(lambda: self.save_new_tool(
            dialog, name_input, desc_input, features_input, url_input, icon_input, tool_radio.isChecked()
        ))
        layout.addWidget(save_button)
        
        # 根据选择的类型显示/隐藏某些字段
        def update_fields():
            is_tool = tool_radio.isChecked()
            url_label.setVisible(is_tool)
            url_input.setVisible(is_tool)
            icon_label.setVisible(is_tool)
            icon_input.setVisible(is_tool)
            browse_button.setVisible(is_tool)
        
        tool_radio.toggled.connect(update_fields)
        folder_radio.toggled.connect(update_fields)
        
        dialog.exec_()
    
    def save_new_tool(self, dialog, name_input, desc_input, features_input, url_input, icon_input, is_tool):
        """保存新工具"""
        name = name_input.text().strip()
        desc = desc_input.text().strip()
        features = features_input.toPlainText().strip()
        
        if is_tool:
            # 普通工具验证
            url = url_input.text().strip()
            icon_path = icon_input.text().strip()
            
            if not name or not url:
                QMessageBox.warning(self, "错误", "名称和URL不能为空")
                return
            
            new_tool = {
                "type": "tool",
                "name": name,
                "description": desc,
                "features": features,
                "url": url,
                "icon_path": icon_path
            }
        else:
            # 文件夹类型验证
            if not name:
                QMessageBox.warning(self, "错误", "名称不能为空")
                return
            
            new_tool = {
                "type": "folder",
                "name": name,
                "description": desc,
                "features": features,
                "children": []
            }
        
        # 添加到工具列表
        self.tools.append(new_tool)
        self.save_tools()
        self.display_tools()
        
        dialog.close()
        QMessageBox.information(self, "成功", f"{name}已成功添加")
    
    def edit_tool_dialog(self, tool):
        """修改工具内容的对话框"""
        dialog = QDialog()
        dialog.setWindowTitle("修改AI工具")
        
        # 设置窗口图标
        icon_path = resource_path("icon/Bingz.png")
        if os.path.exists(icon_path):
            dialog.setWindowIcon(QIcon(icon_path))
        
        dialog.setGeometry(300, 300, 400, 450)
        layout = QVBoxLayout(dialog)
        
        # 工具类型选择
        layout.addWidget(QLabel("工具类型:"))
        type_layout = QHBoxLayout()
        
        # 普通工具单选按钮
        import PyQt5.QtWidgets as QtWidgets
        tool_type = QtWidgets.QButtonGroup()
        tool_radio = QtWidgets.QRadioButton("普通工具")
        folder_radio = QtWidgets.QRadioButton("文件夹")
        
        # 根据当前工具类型设置默认选择
        current_type = tool.get("type", "tool")
        if current_type == "folder":
            folder_radio.setChecked(True)
        else:
            tool_radio.setChecked(True)
        
        tool_type.addButton(tool_radio)
        tool_type.addButton(folder_radio)
        
        type_layout.addWidget(tool_radio)
        type_layout.addWidget(folder_radio)
        layout.addLayout(type_layout)
        
        # 名称
        layout.addWidget(QLabel("工具名称:"))
        name_input = QLineEdit()
        name_input.setText(tool["name"])
        name_input.setStyleSheet(
            "border: 1px solid #ddd; border-radius: 15px; padding: 4px 8px;"
        )
        layout.addWidget(name_input)
        
        # 简介
        layout.addWidget(QLabel("简介:"))
        desc_input = QLineEdit()
        desc_input.setText(tool["description"])
        desc_input.setStyleSheet(
            "border: 1px solid #ddd; border-radius: 15px; padding: 4px 8px;"
        )
        layout.addWidget(desc_input)
        
        # 主要功能
        layout.addWidget(QLabel("主要功能:"))
        features_input = QTextEdit()
        features_input.setPlainText(tool["features"])
        features_input.setStyleSheet(
            "border: 1px solid #ddd; border-radius: 15px; padding: 4px 8px;"
        )
        layout.addWidget(features_input)
        
        # 网站URL
        url_label = QLabel("网站URL:")
        layout.addWidget(url_label)
        url_input = QLineEdit()
        url_input.setText(tool.get("url", ""))
        url_input.setStyleSheet(
            "border: 1px solid #ddd; border-radius: 15px; padding: 4px 8px;"
        )
        layout.addWidget(url_input)
        
        # 图标路径
        icon_label = QLabel("图标路径:")
        layout.addWidget(icon_label)
        icon_layout = QHBoxLayout()
        icon_input = QLineEdit()
        icon_input.setText(tool.get("icon_path", ""))
        icon_input.setStyleSheet(
            "border: 1px solid #ddd; border-radius: 15px; padding: 4px 8px;"
        )
        icon_layout.addWidget(icon_input)
        browse_button = QPushButton("浏览")
        browse_button.setStyleSheet(
            "font-size: 12px; padding: 4px 8px; "
            "background-color: #9E9E9E; color: white; "
            "border: none; border-radius: 15px;"
        )
        browse_button.clicked.connect(lambda: self.browse_icon(icon_input))
        icon_layout.addWidget(browse_button)
        layout.addLayout(icon_layout)
        
        # 保存按钮（圆角矩形样式）
        save_button = QPushButton("保存")
        save_button.setStyleSheet(
            "font-size: 14px; padding: 8px 16px; "
            "background-color: #4CAF50; color: white; "
            "border: none; border-radius: 15px;"
        )
        save_button.clicked.connect(lambda: self.save_edited_tool(
            dialog, tool, name_input, desc_input, features_input, url_input, icon_input, tool_radio.isChecked()
        ))
        layout.addWidget(save_button)
        
        # 根据选择的类型显示/隐藏某些字段
        def update_fields():
            is_tool = tool_radio.isChecked()
            url_label.setVisible(is_tool)
            url_input.setVisible(is_tool)
            icon_label.setVisible(is_tool)
            icon_input.setVisible(is_tool)
            browse_button.setVisible(is_tool)
        
        tool_radio.toggled.connect(update_fields)
        folder_radio.toggled.connect(update_fields)
        
        # 初始更新字段显示
        update_fields()
        
        dialog.exec_()
    
    def browse_icon(self, icon_input):
        """浏览图标文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图标", "", "Image Files (*.png *.jpg *.jpeg *.ico *.svg)"
        )
        if file_path:
            icon_input.setText(file_path)
    
    def save_edited_tool(self, dialog, tool, name_input, desc_input, features_input, url_input, icon_input, is_tool):
        """保存修改后的工具"""
        name = name_input.text().strip()
        desc = desc_input.text().strip()
        features = features_input.toPlainText().strip()
        
        if is_tool:
            # 普通工具验证
            url = url_input.text().strip()
            icon_path = icon_input.text().strip()
            
            if not name or not url:
                QMessageBox.warning(self, "错误", "名称和URL不能为空")
                return
            
            # 更新普通工具信息
            tool["type"] = "tool"
            tool["name"] = name
            tool["description"] = desc
            tool["features"] = features
            tool["url"] = url
            tool["icon_path"] = icon_path
            
            # 如果之前是文件夹，删除children字段
            if "children" in tool:
                del tool["children"]
        else:
            # 文件夹类型验证
            if not name:
                QMessageBox.warning(self, "错误", "名称不能为空")
                return
            
            # 更新文件夹信息
            tool["type"] = "folder"
            tool["name"] = name
            tool["description"] = desc
            tool["features"] = features
            
            # 如果之前是普通工具，删除不需要的字段
            if "url" in tool:
                del tool["url"]
            if "icon_path" in tool:
                del tool["icon_path"]
            
            # 确保children字段存在
            if "children" not in tool:
                tool["children"] = []
        
        self.save_tools()
        self.display_tools()
        
        dialog.close()
        QMessageBox.information(self, "成功", f"{name}已成功修改")
    
    def check_for_updates(self):
        """检查更新"""
        update_dialog = UpdateDialog(self, self.current_version, self.repo_owner, self.repo_name)
        update_dialog.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AIToolManager()
    window.show()
    sys.exit(app.exec_())