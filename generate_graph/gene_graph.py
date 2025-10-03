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
import re

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
        self.root_quantity = 1  # 根节点数量，默认为1
        self.initUI()

    def initUI(self):
        self.setWindowTitle('基因关系图生成器 - 带数量计算')
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
        title_label = QLabel('基因关系图生成器 - 带数量计算')
        title_label.setFont(QFont('Arial', 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 根节点数量设置
        root_quantity_group = QWidget()
        root_quantity_layout = QHBoxLayout(root_quantity_group)

        root_quantity_label = QLabel('根节点数量:')
        root_quantity_label.setFont(QFont('Arial', 12))
        root_quantity_layout.addWidget(root_quantity_label)

        self.root_quantity_spin = QSpinBox()
        self.root_quantity_spin.setRange(1, 10000)
        self.root_quantity_spin.setValue(1)
        self.root_quantity_spin.valueChanged.connect(self.on_root_quantity_changed)
        root_quantity_layout.addWidget(self.root_quantity_spin)

        layout.addWidget(root_quantity_group)

        # 输入区域
        input_group = QWidget()
        input_layout = QVBoxLayout(input_group)

        input_label = QLabel('输入节点关系:')
        input_label.setFont(QFont('Arial', 12))
        input_layout.addWidget(input_label)

        help_text = QLabel('格式: a.b, a。b, 2a。3b, a.b.c, 2a.3b.4c\n支持中文句号和直接数量表示')
        help_text.setStyleSheet('color: gray; font-size: 10px;')
        input_layout.addWidget(help_text)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText('输入节点关系，如: 2a。3b 或 a.b.c')
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

    def on_root_quantity_changed(self, value):
        """根节点数量改变时的处理"""
        self.root_quantity = value
        self.calculate_quantities()
        self.draw_graph()
        self.update_lists()

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
            self.calculate_quantities()  # 重新计算数量
            self.draw_graph()
            self.update_lists()
            self.status_label.setText(f'成功添加关系: {input_text}')
        except Exception as e:
            QMessageBox.warning(self, '输入错误', f'错误: {e}\n请使用正确格式，例如：a.b 或 2a。3b 或 a.b.c')

    def parse_and_add_edges(self, input_string, auto_save=False):
        """解析输入字符串并添加边，支持中文句号和直接数量表示"""
        # 统一替换中文句号为英文句点
        input_string = input_string.replace('。', '.')

        # 使用正则表达式解析节点和数量关系
        # 匹配模式：可选的数字+节点名称
        pattern = r'(\d*)([a-zA-Z\u4e00-\u9fff_][a-zA-Z0-9\u4e00-\u9fff_]*)'

        # 分割节点链
        parts = input_string.split('.')
        nodes_with_quantities = []

        for part in parts:
            matches = re.findall(pattern, part.strip())
            for match in matches:
                quantity_str = match[0]
                node_name = match[1]

                if not node_name:
                    continue

                # 解析数量
                if quantity_str:
                    quantity = int(quantity_str)
                else:
                    quantity = 1  # 默认数量为1

                nodes_with_quantities.append((node_name, quantity))

        if len(nodes_with_quantities) < 2:
            raise ValueError("输入至少需要两个节点，如 a.b 或 2a。3b")

        # 添加边和设置数量关系
        for i in range(len(nodes_with_quantities) - 1):
            source, source_qty = nodes_with_quantities[i]
            target, target_qty = nodes_with_quantities[i + 1]

            # 添加边
            self.G.add_edge(source, target)

            # 设置边的数量关系属性
            self.G[source][target]['source_quantity'] = source_qty
            self.G[source][target]['target_quantity'] = target_qty

        # 只有在明确要求或自动保存开启时才保存
        if auto_save and self.auto_save_enabled:
            self.save_config("gene_graph_config.txt")

    def calculate_quantities(self):
        """计算所有节点的数量"""
        # 清除所有节点的数量属性
        for node in self.G.nodes():
            if 'quantity' in self.G.nodes[node]:
                del self.G.nodes[node]['quantity']

        # 找到根节点（没有入边的节点）
        root_nodes = [node for node in self.G.nodes() if self.G.in_degree(node) == 0]

        # 设置根节点数量
        for root in root_nodes:
            self.G.nodes[root]['quantity'] = self.root_quantity

        # 使用拓扑排序确保按层次计算
        try:
            topological_order = list(nx.topological_sort(self.G))

            for node in topological_order:
                if node not in root_nodes:  # 跳过根节点，已经设置过数量
                    # 计算该节点的数量（所有入边的贡献之和）
                    total_quantity = 0

                    for predecessor in self.G.predecessors(node):
                        if 'quantity' in self.G.nodes[predecessor]:
                            edge_data = self.G[predecessor][node]
                            source_qty = edge_data.get('source_quantity', 1)
                            target_qty = edge_data.get('target_quantity', 1)

                            # 计算该前驱节点贡献的数量
                            predecessor_quantity = self.G.nodes[predecessor]['quantity']
                            contribution = predecessor_quantity * target_qty / source_qty
                            total_quantity += contribution

                    if total_quantity > 0:
                        self.G.nodes[node]['quantity'] = total_quantity

        except nx.NetworkXError:
            # 如果有环，使用简单的方法计算
            self.calculate_quantities_with_cycles()

    def calculate_quantities_with_cycles(self):
        """处理有环图的数量计算（简化版本）"""
        # 找到根节点
        root_nodes = [node for node in self.G.nodes() if self.G.in_degree(node) == 0]

        # 设置根节点数量
        for root in root_nodes:
            self.G.nodes[root]['quantity'] = self.root_quantity

        # 使用BFS遍历图
        visited = set(root_nodes)
        queue = list(root_nodes)

        while queue:
            current = queue.pop(0)

            for successor in self.G.successors(current):
                if 'quantity' not in self.G.nodes[successor]:
                    edge_data = self.G[current][successor]
                    source_qty = edge_data.get('source_quantity', 1)
                    target_qty = edge_data.get('target_quantity', 1)

                    current_quantity = self.G.nodes[current]['quantity']
                    successor_quantity = current_quantity * target_qty / source_qty

                    self.G.nodes[successor]['quantity'] = successor_quantity

                if successor not in visited:
                    visited.add(successor)
                    queue.append(successor)

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

            # 绘制节点和边
            nx.draw_networkx_edges(
                self.G, pos,
                edge_color='gray',
                arrows=True,
                arrowsize=20,
                alpha=0.9,
                ax=self.canvas.ax
            )

            # 绘制节点，根据是否有数量信息使用不同颜色
            node_colors = []
            for node in self.G.nodes():
                if 'quantity' in self.G.nodes[node]:
                    node_colors.append('lightgreen')  # 有数量信息的节点
                else:
                    node_colors.append('lightblue')  # 无数量信息的节点

            nx.draw_networkx_nodes(
                self.G, pos,
                node_size=node_size,
                node_color=node_colors,
                alpha=0.9,
                linewidths=1.5,
                ax=self.canvas.ax
            )

            # 绘制节点标签，包含数量信息
            labels = {}
            for node in self.G.nodes():
                if 'quantity' in self.G.nodes[node]:
                    quantity = self.G.nodes[node]['quantity']
                    # 格式化数量显示
                    if quantity.is_integer():
                        labels[node] = f"{node}\n({int(quantity)})"
                    else:
                        labels[node] = f"{node}\n({quantity:.2f})"
                else:
                    labels[node] = node

            nx.draw_networkx_labels(
                self.G, pos,
                labels=labels,
                font_size=10,
                font_weight='bold',
                ax=self.canvas.ax
            )

            # 绘制边标签，显示数量关系
            edge_labels = {}
            for u, v in self.G.edges():
                edge_data = self.G[u][v]
                source_qty = edge_data.get('source_quantity', 1)
                target_qty = edge_data.get('target_quantity', 1)
                edge_labels[(u, v)] = f"{source_qty}:{target_qty}"

            nx.draw_networkx_edge_labels(
                self.G, pos,
                edge_labels=edge_labels,
                font_size=8,
                ax=self.canvas.ax
            )

            self.canvas.ax.set_title(
                f'基因关系图 (节点数: {len(self.G.nodes())}, 边数: {len(self.G.edges())}, 根节点数量: {self.root_quantity})',
                fontsize=14
            )

            self.canvas.ax.axis('off')

        except Exception as e:
            self.canvas.ax.text(0.5, 0.5, f'绘制错误: {e}',
                                ha='center', va='center', fontsize=12,
                                transform=self.canvas.ax.transAxes)

        self.canvas.draw()

    def update_lists(self):
        self.nodes_list.clear()
        self.edges_list.clear()

        for node in sorted(self.G.nodes()):
            if 'quantity' in self.G.nodes[node]:
                quantity = self.G.nodes[node]['quantity']
                if quantity.is_integer():
                    self.nodes_list.addItem(f'● {node} (数量: {int(quantity)})')
                else:
                    self.nodes_list.addItem(f'● {node} (数量: {quantity:.2f})')
            else:
                self.nodes_list.addItem(f'● {node} (数量: 未计算)')

        for edge in sorted(self.G.edges()):
            edge_data = self.G[edge[0]][edge[1]]
            source_qty = edge_data.get('source_quantity', 1)
            target_qty = edge_data.get('target_quantity', 1)
            self.edges_list.addItem(f'{edge[0]} [{source_qty}] → {edge[1]} [{target_qty}]')

    def clear_graph(self):
        reply = QMessageBox.question(self, '确认清空', '确定要清空所有数据吗？',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.G.clear()
            self.root_quantity = 1
            self.root_quantity_spin.setValue(1)
            self.draw_graph()
            self.update_lists()
            self.save_config("gene_graph_config.txt")
            self.status_label.setText('图形已清空')

    def save_config(self, filename=None):
        """内部保存方法，不弹出对话框"""
        if filename is None:
            filename = "gene_graph_config.txt"

        # 保存边信息，包括数量关系
        edges_data = []
        for u, v in self.G.edges():
            edge_data = {
                'source': u,
                'target': v,
                'source_quantity': self.G[u][v].get('source_quantity', 1),
                'target_quantity': self.G[u][v].get('target_quantity', 1)
            }
            edges_data.append(edge_data)

        self.config_data["edges"] = edges_data
        self.config_data["node_count"] = len(self.G.nodes())
        self.config_data["root_quantity"] = self.root_quantity
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

            edges_data = loaded_data.get("edges", [])
            for edge_data in edges_data:
                u = edge_data['source']
                v = edge_data['target']
                self.G.add_edge(u, v)
                self.G[u][v]['source_quantity'] = edge_data.get('source_quantity', 1)
                self.G[u][v]['target_quantity'] = edge_data.get('target_quantity', 1)

            self.root_quantity = loaded_data.get("root_quantity", 1)
            self.root_quantity_spin.setValue(self.root_quantity)

            self.config_data.update(loaded_data)
            self.config_data["last_modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 重新计算数量
            self.calculate_quantities()
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

            # 导入完成后重新计算数量并保存
            self.calculate_quantities()
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