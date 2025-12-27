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
    progress = pyqtSignal(int, str)  # 添加进度信号
    
    def __init__(self, current_version, update_url):
        super().__init__()
        self.current_version = current_version
        self.update_url = update_url
    
    def run(self):
        try:
            # 发送请求获取最新版本信息
            self.progress.emit(20, "正在连接更新服务器...")
            response = requests.get(self.update_url, timeout=5)
            self.progress.emit(50, "正在下载版本信息...")
            response.raise_for_status()
            self.progress.emit(70, "正在解析版本信息...")
            update_info = response.json()
            self.progress.emit(80, "正在比较版本...")
            
            # 比较版本号
            if self.compare_version(update_info["version"], self.current_version):
                self.progress.emit(100, "发现新版本!")
                self.update_available.emit(update_info)
            else:
                self.progress.emit(100, "当前已是最新版本")
                self.no_update.emit()
        except requests.exceptions.RequestException as e:
            self.progress.emit(100, f"检查更新失败: {str(e)}")
            self.error.emit(f"检查更新失败: {str(e)}")
    
    def compare_version(self, new_version, old_version):
        """比较版本号，新版本大于旧版本返回True"""
        new_parts = list(map(int, new_version.split(".")))
        old_parts = list(map(int, old_version.split(".")))
        
        # 确保版本号位数相同
        max_length = max(len(new_parts), len(old_parts))
        new_parts.extend([0] * (max_length - len(new_parts)))
        old_parts.extend([0] * (max_length - len(old_parts)))
        
        for new, old in zip(new_parts, old_parts):
            if new > old:
                return True
            elif new < old:
                return False
        return False

class UpdateCheckDialog(QDialog):
    """更新检查对话框"""
    update_canceled = pyqtSignal()
    update_checked = pyqtSignal()
    
    def __init__(self, parent=None, current_version="1.0.0", update_url="https://example.com/update_info.json"):
        super().__init__(parent)
        self.current_version = current_version
        self.update_url = update_url
        self.init_ui()
        
    def init_ui(self):
        """初始化更新检查对话框"""
        self.setWindowTitle("检查更新")
        self.setFixedSize(300, 150)
        self.setWindowModality(Qt.ApplicationModal)  # 模态对话框，阻止用户操作其他窗口
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 状态标签
        self.status_label = QLabel("正在检查更新...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.on_cancel)
        button_layout.addWidget(self.cancel_button)
        
        # 关闭按钮（初始隐藏）
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.accept)
        self.close_button.hide()
        button_layout.addWidget(self.close_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 开始检查更新
        self.start_check()
    
    def start_check(self):
        """开始检查更新"""
        # 创建更新检查线程
        self.update_checker = UpdateChecker(self.current_version, self.update_url)
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.no_update.connect(self.on_no_update)
        self.update_checker.error.connect(self.on_update_error)
        self.update_checker.progress.connect(self.update_progress)
        self.update_checker.finished.connect(self.on_check_finished)
        self.update_checker.start()
    
    def update_progress(self, progress, status):
        """更新进度条和状态"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
    
    def on_update_available(self, update_info):
        """发现更新时的处理"""
        self.update_info = update_info
        self.status_label.setText(f"发现新版本 {update_info['version']}！")
        # 显示更新按钮
        self.cancel_button.setText("立即更新")
        self.cancel_button.disconnect()
        self.cancel_button.clicked.connect(self.on_update)
        self.close_button.show()
    
    def on_no_update(self):
        """没有更新时的处理"""
        self.status_label.setText("当前已是最新版本")
        self.cancel_button.hide()
        self.close_button.show()
    
    def on_update_error(self, error_msg):
        """更新检查错误时的处理"""
        self.status_label.setText(error_msg)
        self.cancel_button.hide()
        self.close_button.show()
    
    def on_cancel(self):
        """取消更新检查"""
        self.update_checker.terminate()
        self.update_canceled.emit()
        self.reject()
    
    def on_update(self):
        """立即更新"""
        self.accept()
        # 这里可以添加下载更新的逻辑
        QMessageBox.information(self, "下载更新", f"开始下载新版本 {self.update_info['version']}...")
    
    def on_check_finished(self):
        """检查完成时的处理"""
        pass

class AIToolManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tools = []
        self.data_file = resource_path("ai_tools.json")
        # 版本信息
        self.current_version = "1.0.0"
        self.init_ui()
        self.load_tools()
        
    def init_ui(self):
        self.setWindowTitle("BingZ")
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

        
        top_layout.addStretch()
        top_layout.addWidget(add_button)
        
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
    

    
    def check_for_updates(self):
        """检查更新"""
        print(f"当前版本: {self.current_version}")
        print("正在检查更新...")
        
        # 创建更新检查线程
        self.update_checker = UpdateChecker(self.current_version, self.update_url)
        self.update_checker.update_available.connect(self.show_update_dialog)
        self.update_checker.no_update.connect(self.on_no_update)
        self.update_checker.error.connect(self.on_update_error)
        self.update_checker.start()
    
    def show_update_dialog(self, update_info):
        """显示更新对话框"""
        self.update_info = update_info
        
        dialog = QMessageBox(self)
        dialog.setWindowTitle("发现新版本")
        dialog.setText(f"发现新版本 {update_info['version']}！\n\n更新内容：\n{update_info['changelog']}")
        dialog.setIcon(QMessageBox.Information)
        
        # 添加更新和取消按钮
        dialog.setStandardButtons(QMessageBox.Update | QMessageBox.Cancel)
        dialog.button(QMessageBox.Update).setText("立即更新")
        dialog.button(QMessageBox.Cancel).setText("稍后再说")
        
        # 显示对话框
        result = dialog.exec_()
        if result == QMessageBox.Update:
            self.download_update(update_info)
    
    def on_no_update(self):
        """没有更新时的处理"""
        print("当前已是最新版本")
    
    def on_update_error(self, error_msg):
        """更新检查错误时的处理"""
        print(error_msg)
    
    def download_update(self, update_info):
        """下载更新"""
        # 这里只是示例，实际需要实现下载逻辑
        QMessageBox.information(self, "下载更新", f"开始下载新版本 {update_info['version']}...")
        # 实际应用中，这里应该创建一个下载线程，显示下载进度
        # 下载完成后提示用户安装
        QMessageBox.information(self, "下载完成", "更新已下载完成，请手动安装")
    
    def load_tools(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.tools = json.load(f)
            self.display_tools()
    
    def save_tools(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.tools, f, ensure_ascii=False, indent=2)
    
    def display_tools(self):
        # 清空现有工具
        for i in reversed(range(self.tools_layout.count())):
            widget = self.tools_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        # 显示工具（网格排列，一行4个，紧凑布局）
        rows = 0
        cols = 4  # 4列布局，紧凑排列
        for i, tool in enumerate(self.tools):
            tool_widget = self.create_tool_widget(tool)
            row = i // cols
            col = i % cols
            self.tools_layout.addWidget(tool_widget, row, col)
            rows = row + 1
    
    def create_tool_widget(self, tool):
        widget = QWidget()
        widget.setFixedSize(80, 100)  # 适合网格布局的工具项大小
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)  # 内部边距
        layout.setSpacing(5)  # 内部间距
        layout.setAlignment(Qt.AlignCenter)  # 内部元素居中对齐
        
        # 图标按钮（网格风格）
        icon_button = QPushButton()
        icon_button.setFixedSize(60, 60)  # 图标按钮大小
        icon_button.setStyleSheet(
            "QPushButton {border: none; background: transparent; border-radius: 12px;}"
            "QPushButton:hover {background-color: rgba(0, 0, 0, 0.1);}"
        )
        icon_button.clicked.connect(lambda: self.show_tool_detail(tool))
        
        # 设置右键菜单
        icon_button.setContextMenuPolicy(Qt.CustomContextMenu)
        icon_button.customContextMenuRequested.connect(lambda pos, btn=icon_button, t=tool: self.show_context_menu(pos, btn, t))
        
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
            else:
                # 其他图片格式处理
                icon_label = QLabel(icon_button)
                icon_label.setGeometry(5, 5, 50, 50)  # 图标尺寸
                icon_label.setAlignment(Qt.AlignCenter)
                
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
            icon_label = QLabel(icon_button)
            icon_label.setGeometry(5, 5, 50, 50)
            icon_label.setAlignment(Qt.AlignCenter)
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
    
    def show_tool_detail(self, tool):
        detail_window = QDialog()
        detail_window.setWindowTitle(f"{tool['name']} - 详情")
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
        
        # 删除选项
        delete_action = menu.addAction("删除")
        delete_action.triggered.connect(lambda: self.delete_tool(tool))
        
        # 更改图标选项
        change_icon_action = menu.addAction("更改图标")
        change_icon_action.triggered.connect(lambda: self.change_tool_icon(tool))
        
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
        dialog.setGeometry(300, 300, 400, 400)
        layout = QVBoxLayout(dialog)
        
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
        layout.addWidget(QLabel("网站URL:"))
        url_input = QLineEdit()
        url_input.setStyleSheet(
            "border: 1px solid #ddd; border-radius: 15px; padding: 4px 8px;"
        )
        layout.addWidget(url_input)
        
        # 图标路径
        layout.addWidget(QLabel("图标路径:"))
        icon_layout = QHBoxLayout()
        icon_input = QLineEdit()
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
        save_button.clicked.connect(lambda: self.save_new_tool(
            dialog, name_input, desc_input, features_input, url_input, icon_input
        ))
        layout.addWidget(save_button)
        
        dialog.exec_()
    
    def browse_icon(self, line_edit):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图标", "", "Image Files (*.png *.jpg *.jpeg *.ico *.svg)"
        )
        if file_path:
            line_edit.setText(file_path)
    
    def save_new_tool(self, dialog, name_input, desc_input, features_input, url_input, icon_input):
        name = name_input.text().strip()
        desc = desc_input.text().strip()
        features = features_input.toPlainText().strip()
        url = url_input.text().strip()
        icon_path = icon_input.text().strip()
        
        if not name or not url:
            QMessageBox.warning(self, "错误", "名称和URL不能为空")
            return
        
        new_tool = {
            "name": name,
            "description": desc,
            "features": features,
            "url": url,
            "icon_path": icon_path
        }
        
        self.tools.append(new_tool)
        self.save_tools()
        self.display_tools()
        dialog.close()
        QMessageBox.information(self, "成功", "AI工具添加成功")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 直接启动主程序，不进行更新检查
    window = AIToolManager()
    window.show()
    sys.exit(app.exec_())