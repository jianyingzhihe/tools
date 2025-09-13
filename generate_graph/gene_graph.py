import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout
import math
import os
import json
from datetime import datetime
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QLineEdit, QPushButton, QLabel, QListWidget,
                             QFileDialog, QMessageBox, QSplitter, QComboBox, QSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib

matplotlib.use('Qt5Agg')


class GraphCanvas(FigureCanvas):
    def __init__(self, parent=None, width=12, height=10, dpi=100):
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)

        # 设置中文字体和负号显示
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False


class GeneGraphUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.G = nx.DiGraph()
        self.config_data = {
            "edges": [],
            "created_time": "",
            "last_modified": "",
            "node_count": 0,
            "version": "1.0"
        }
        self.auto_save_enabled = True  # 添加自动保存控制标志
        self.initUI()

    def initUI(self):
        self.setWindowTitle('基因关系图生成器')
        self.setGeometry(100, 100, 1600, 900)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 左侧控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_panel.setMaximumWidth(400)

        # 图形显示区域
        self.canvas = GraphCanvas(self, width=12, height=10)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(control_panel)
        splitter.addWidget(self.canvas)
        splitter.setSizes([400, 1200])

        main_layout.addWidget(splitter)

        # 控制面板部件
        self.create_control_panel(control_layout)

        # 初始绘制
        self.draw_graph()

    def create_control_panel(self, layout):
        # 标题
        title_label = QLabel('基因关系图生成器')
        title_label.setFont(QFont('Arial', 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 输入区域
        input_group = QWidget()
        input_layout = QVBoxLayout(input_group)

        input_label = QLabel('输入节点关系:')
        input_label.setFont(QFont('Arial', 12))
        input_layout.addWidget(input_label)

        help_text = QLabel('格式: a.b, a.b,c, a.b.c, a.b.c,d')
        help_text.setStyleSheet('color: gray; font-size: 10px;')
        input_layout.addWidget(help_text)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText('输入节点关系，如: a.b.c')
        self.input_field.returnPressed.connect(self.add_edges_from_input)
        input_layout.addWidget(self.input_field)

        add_btn = QPushButton('添加关系')
        add_btn.clicked.connect(self.add_edges_from_input)
        input_layout.addWidget(add_btn)

        layout.addWidget(input_group)

        # 节点和边列表
        lists_group = QWidget()
        lists_layout = QVBoxLayout(lists_group)

        nodes_label = QLabel('节点列表:')
        nodes_label.setFont(QFont('Arial', 12))
        lists_layout.addWidget(nodes_label)

        self.nodes_list = QListWidget()
        lists_layout.addWidget(self.nodes_list)

        edges_label = QLabel('边列表:')
        edges_label.setFont(QFont('Arial', 12))
        lists_layout.addWidget(edges_label)

        self.edges_list = QListWidget()
        lists_layout.addWidget(self.edges_list)

        layout.addWidget(lists_group)

        # 控制按钮
        buttons_group = QWidget()
        buttons_layout = QHBoxLayout(buttons_group)

        clear_btn = QPushButton('清空图形')
        clear_btn.clicked.connect(self.clear_graph)
        buttons_layout.addWidget(clear_btn)

        save_config_btn = QPushButton('保存配置')
        save_config_btn.clicked.connect(lambda: self.save_config_with_dialog())
        buttons_layout.addWidget(save_config_btn)

        load_config_btn = QPushButton('加载配置')
        load_config_btn.clicked.connect(lambda: self.load_config_with_dialog())
        buttons_layout.addWidget(load_config_btn)

        layout.addWidget(buttons_group)

        # 文件操作按钮
        file_buttons_group = QWidget()
        file_buttons_layout = QHBoxLayout(file_buttons_group)

        import_btn = QPushButton('导入文件')
        import_btn.clicked.connect(self.import_from_file)
        file_buttons_layout.addWidget(import_btn)

        export_btn = QPushButton('导出图像')
        export_btn.clicked.connect(self.export_image)
        file_buttons_layout.addWidget(export_btn)

        layout.addWidget(file_buttons_group)

        # 自动保存设置
        auto_save_group = QWidget()
        auto_save_layout = QHBoxLayout(auto_save_group)

        auto_save_label = QLabel('自动保存:')
        auto_save_layout.addWidget(auto_save_label)

        self.auto_save_checkbox = QComboBox()
        self.auto_save_checkbox.addItems(['开启', '关闭'])
        self.auto_save_checkbox.setCurrentText('开启')
        self.auto_save_checkbox.currentTextChanged.connect(self.toggle_auto_save)
        auto_save_layout.addWidget(self.auto_save_checkbox)

        layout.addWidget(auto_save_group)

        # 图形设置
        settings_group = QWidget()
        settings_layout = QVBoxLayout(settings_group)

        settings_label = QLabel('图形设置:')
        settings_label.setFont(QFont('Arial', 12))
        settings_layout.addWidget(settings_label)

        # 节点大小设置
        node_size_layout = QHBoxLayout()
        node_size_label = QLabel('节点大小:')
        node_size_layout.addWidget(node_size_label)

        self.node_size_spin = QSpinBox()
        self.node_size_spin.setRange(100, 2000)
        self.node_size_spin.setValue(800)
        self.node_size_spin.valueChanged.connect(self.draw_graph)
        node_size_layout.addWidget(self.node_size_spin)

        settings_layout.addLayout(node_size_layout)

        layout.addWidget(settings_group)

        # 状态信息
        self.status_label = QLabel('就绪')
        self.status_label.setStyleSheet('color: green; background-color: #f0f0f0; padding: 5px;')
        layout.addWidget(self.status_label)

    def toggle_auto_save(self, state):
        self.auto_save_enabled = (state == '开启')
        self.status_label.setText(f'自动保存: {"开启" if self.auto_save_enabled else "关闭"}')

    def add_edges_from_input(self):
        input_text = self.input_field.text().strip()
        if not input_text:
            return

        try:
            self.parse_and_add_edges(input_text, auto_save=True)
            self.input_field.clear()
            self.draw_graph()
            self.update_lists()
            self.status_label.setText(f'成功添加关系: {input_text}')
        except Exception as e:
            QMessageBox.warning(self, '输入错误', f'错误: {e}\n请使用正确格式，例如：a.b 或 a.b.c 或 a.b,c')

    def parse_and_add_edges(self, input_string, auto_save=False):
        print(input_string)
        nodes_in_chain = [part.strip() for part in input_string.split('.')]

        if len(nodes_in_chain) < 2:
            raise ValueError("输入至少需要两个节点，如 a.b")

        for i in range(len(nodes_in_chain) - 1):
            source = nodes_in_chain[i]
            targets = nodes_in_chain[i + 1].split(',')

            for target in targets:
                target = target.strip()
                if not source or not target:
                    continue
                self.G.add_edge(source, target)

        # 只有在明确要求或自动保存开启时才保存
        if auto_save and self.auto_save_enabled:
            self.save_config("gene_graph_config.txt")  # 使用默认文件名，不弹出对话框

    def draw_graph(self):
        self.canvas.ax.clear()

        if len(self.G.nodes()) == 0:
            self.canvas.ax.text(0.5, 0.5, '暂无数据\n请输入节点关系',
                                ha='center', va='center', fontsize=16,
                                transform=self.canvas.ax.transAxes)
            self.canvas.draw()
            return

        try:
            pos = graphviz_layout(self.G, prog='dot')

            node_size = self.node_size_spin.value()

            nx.draw(
                self.G, pos,
                with_labels=True,
                node_size=node_size,
                node_color='lightblue',
                font_size=10,
                font_weight='bold',
                edge_color='gray',
                arrows=True,
                arrowsize=20,
                alpha=0.9,
                linewidths=1.5,
                ax=self.canvas.ax
            )

            self.canvas.ax.set_title(f'基因关系图 (节点数: {len(self.G.nodes())}, 边数: {len(self.G.edges())})',
                                     fontsize=14)

        except Exception as e:
            self.canvas.ax.text(0.5, 0.5, f'绘制错误: {e}',
                                ha='center', va='center', fontsize=12,
                                transform=self.canvas.ax.transAxes)

        self.canvas.draw()

    def update_lists(self):
        self.nodes_list.clear()
        self.edges_list.clear()

        for node in sorted(self.G.nodes()):
            self.nodes_list.addItem(f'● {node}')

        for edge in sorted(self.G.edges()):
            self.edges_list.addItem(f'{edge[0]} → {edge[1]}')

    def clear_graph(self):
        reply = QMessageBox.question(self, '确认清空', '确定要清空所有数据吗？',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.G.clear()
            self.draw_graph()
            self.update_lists()
            self.save_config("gene_graph_config.txt")
            self.status_label.setText('图形已清空')

    def save_config(self, filename=None):
        """内部保存方法，不弹出对话框"""
        if filename is None:
            filename = "gene_graph_config.txt"

        self.config_data["edges"] = list(self.G.edges())
        self.config_data["node_count"] = len(self.G.nodes())
        self.config_data["last_modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not self.config_data["created_time"]:
            self.config_data["created_time"] = self.config_data["last_modified"]

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            self.status_label.setText(f'配置已保存到 {filename}')
            return True
        except Exception as e:
            print(f'保存配置失败: {e}')
            return False

    def save_config_with_dialog(self):
        """带对话框的保存方法"""
        filename, _ = QFileDialog.getSaveFileName(
            self, '保存配置', 'gene_graph_config.txt', 'Text Files (*.txt)')
        if filename:
            self.save_config(filename)

    def load_config(self, filename=None):
        """内部加载方法"""
        if filename is None:
            filename = "gene_graph_config.txt"

        if not os.path.exists(filename):
            return False

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            self.G.clear()

            for edge in loaded_data.get("edges", []):
                if len(edge) == 2:
                    self.G.add_edge(edge[0], edge[1])

            self.config_data.update(loaded_data)
            self.config_data["last_modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.draw_graph()
            self.update_lists()
            self.status_label.setText(f'配置已从 {filename} 加载')
            return True

        except Exception as e:
            print(f'加载配置失败: {e}')
            return False

    def load_config_with_dialog(self):
        """带对话框的加载方法"""
        filename, _ = QFileDialog.getOpenFileName(
            self, '加载配置', '', 'Text Files (*.txt)')
        if filename:
            self.load_config(filename)

    def import_from_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, '导入数据', '', 'Text Files (*.txt)')
        if not filename:
            return

        try:
            # 临时关闭自动保存，避免多次弹出对话框
            original_auto_save = self.auto_save_enabled
            self.auto_save_enabled = False

            with open(filename, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                success_count = 0
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            self.parse_and_add_edges(line, auto_save=False)
                            success_count += 1
                        except Exception as e:
                            print(f'错误处理第 {line_num} 行: {e}')

            # 导入完成后一次性保存
            if original_auto_save:
                self.save_config("gene_graph_config.txt")

            # 恢复自动保存设置
            self.auto_save_enabled = original_auto_save

            self.draw_graph()
            self.update_lists()
            self.status_label.setText(f'从 {filename} 导入了 {success_count} 条关系')

        except Exception as e:
            QMessageBox.critical(self, '导入失败', f'导入文件失败: {e}')
            self.auto_save_enabled = original_auto_save

    def export_image(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, '导出图像', 'gene_graph.png', 'PNG Files (*.png);;All Files (*)')
        if not filename:
            return

        try:
            self.canvas.fig.savefig(filename, dpi=300, bbox_inches='tight')
            self.status_label.setText(f'图像已导出到 {filename}')
        except Exception as e:
            QMessageBox.critical(self, '导出失败', f'导出图像失败: {e}')


def main():
    app = QApplication(sys.argv)

    # 设置应用程序样式
    app.setStyle('Fusion')

    window = GeneGraphUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()