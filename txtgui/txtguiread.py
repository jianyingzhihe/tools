import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import re


class TextFileViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("文本文件查看器 - 支持关键词高亮")
        self.root.geometry("1000x700")

        # 当前文件路径
        self.current_file = None

        # 关键词列表
        self.keywords = []

        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        # 创建主框架 - 使用PanedWindow实现可调节分割
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 控制面板框架（上方固定区域）
        control_container = ttk.Frame(self.main_paned)
        self.main_paned.add(control_container, weight=0)  # weight=0 表示不随窗口拉伸

        # 文件选择区域
        file_frame = ttk.Frame(control_container)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(file_frame, text="选择文件", command=self.open_file).pack(side=tk.LEFT, padx=(0, 10))
        self.file_label = ttk.Label(file_frame, text="未选择文件")
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 设置和控制区域
        settings_frame = ttk.Frame(control_container)
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # 第一行控制
        row1_frame = ttk.Frame(settings_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 5))

        # 字体大小控制
        ttk.Label(row1_frame, text="字体大小:").pack(side=tk.LEFT, padx=(0, 5))
        self.font_size = tk.IntVar(value=12)
        font_spinbox = ttk.Spinbox(row1_frame, from_=8, to=72, width=5,
                                   textvariable=self.font_size, command=self.update_font)
        font_spinbox.pack(side=tk.LEFT, padx=(0, 15))

        # 高亮选项
        self.highlight_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row1_frame, text="高亮显示", variable=self.highlight_var,
                        command=self.update_display).pack(side=tk.LEFT, padx=(0, 10))

        self.bold_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row1_frame, text="加粗显示", variable=self.bold_var,
                        command=self.update_display).pack(side=tk.LEFT, padx=(0, 15))

        # 第二行控制 - 关键词管理
        row2_frame = ttk.Frame(settings_frame)
        row2_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(row2_frame, text="关键词:").pack(side=tk.LEFT, padx=(0, 5))
        self.keyword_var = tk.StringVar()
        keyword_entry = ttk.Entry(row2_frame, textvariable=self.keyword_var, width=20)
        keyword_entry.pack(side=tk.LEFT, padx=(0, 5))
        keyword_entry.bind('<Return>', self.add_keyword)

        ttk.Button(row2_frame, text="添加关键词", command=self.add_keyword).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(row2_frame, text="清除关键词", command=self.clear_keywords).pack(side=tk.LEFT, padx=(0, 10))

        # 关键词列表显示区域
        keywords_frame = ttk.LabelFrame(control_container, text="当前关键词列表")
        keywords_frame.pack(fill=tk.X, pady=(0, 10))

        # 创建关键词列表和滚动条
        listbox_frame = ttk.Frame(keywords_frame)
        listbox_frame.pack(fill=tk.X, padx=5, pady=5)

        self.keywords_listbox = tk.Listbox(listbox_frame, height=3, selectmode=tk.SINGLE)
        self.keywords_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        listbox_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.keywords_listbox.yview)
        listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.keywords_listbox.config(yscrollcommand=listbox_scrollbar.set)

        self.keywords_listbox.bind('<Delete>', self.delete_selected_keyword)
        self.keywords_listbox.bind('<Double-Button-1>', self.delete_selected_keyword)

        # 文本显示区域（下方可伸缩区域）
        text_container = ttk.Frame(self.main_paned)
        self.main_paned.add(text_container, weight=1)  # weight=1 表示随窗口拉伸

        text_container.columnconfigure(0, weight=1)
        text_container.rowconfigure(0, weight=1)

        # 创建文本框
        self.text_area = scrolledtext.ScrolledText(
            text_container,
            wrap=tk.WORD,
            font=("Consolas", self.font_size.get()),
            undo=True
        )
        self.text_area.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置文本标签样式
        self.text_area.tag_configure("highlight", background="yellow")
        self.text_area.tag_configure("bold", font=("Consolas", self.font_size.get(), "bold"))
        self.text_area.tag_configure("highlight_bold",
                                     background="yellow",
                                     font=("Consolas", self.font_size.get(), "bold"))

        # 设置初始分割比例（控制区域占25%，文本区域占75%）
        self.root.update()
        self.main_paned.sashpos(0, int(self.root.winfo_height() * 0.25))

    def open_file(self):
        """打开文件对话框选择txt文件"""
        file_path = filedialog.askopenfilename(
            title="选择文本文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()

                self.current_file = file_path
                self.file_label.config(text=file_path.split('/')[-1])
                self.display_text(content)

            except UnicodeDecodeError:
                # 尝试其他编码
                try:
                    with open(file_path, 'r', encoding='gbk') as file:
                        content = file.read()
                    self.current_file = file_path
                    self.file_label.config(text=file_path.split('/')[-1])
                    self.display_text(content)
                except Exception as e:
                    messagebox.showerror("错误", f"无法读取文件: {str(e)}")
            except Exception as e:
                messagebox.showerror("错误", f"无法读取文件: {str(e)}")

    def display_text(self, text):
        """在文本框中显示文本"""
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, text)
        self.update_display()

    def update_font(self):
        """更新字体大小"""
        try:
            new_size = self.font_size.get()
            self.text_area.config(font=("Consolas", new_size))

            # 更新标签的字体配置
            self.text_area.tag_configure("bold", font=("Consolas", new_size, "bold"))
            self.text_area.tag_configure("highlight_bold",
                                         background="yellow",
                                         font=("Consolas", new_size, "bold"))

            self.update_display()
        except tk.TclError:
            # 如果字体大小无效，恢复默认值
            self.font_size.set(12)

    def add_keyword(self, event=None):
        """添加关键词"""
        keyword = self.keyword_var.get().strip()
        if keyword and keyword not in self.keywords:
            self.keywords.append(keyword)
            self.update_keywords_list()
            self.update_display()
            self.keyword_var.set("")  # 清空输入框

    def delete_selected_keyword(self, event=None):
        """删除选中的关键词"""
        selection = self.keywords_listbox.curselection()
        if selection:
            index = selection[0]
            self.keywords.pop(index)
            self.update_keywords_list()
            self.update_display()

    def clear_keywords(self):
        """清除所有关键词"""
        self.keywords.clear()
        self.update_keywords_list()
        self.update_display()

    def update_keywords_list(self):
        """更新关键词列表显示"""
        self.keywords_listbox.delete(0, tk.END)
        for keyword in self.keywords:
            self.keywords_listbox.insert(tk.END, keyword)

    def update_display(self):
        """更新文本显示，应用高亮和加粗效果"""
        if not self.keywords:
            # 如果没有关键词，清除所有格式
            self.clear_formatting()
            return

        # 获取当前文本
        content = self.text_area.get(1.0, tk.END)

        # 清除所有现有的标签
        self.clear_formatting()

        # 应用新的格式
        for keyword in self.keywords:
            if not keyword:
                continue

            # 查找所有匹配的位置（不区分大小写）
            start_idx = "1.0"
            while True:
                pos = self.text_area.search(keyword, start_idx, stopindex=tk.END, nocase=True)
                if not pos:
                    break

                end_idx = f"{pos}+{len(keyword)}c"

                # 根据选项应用不同的标签
                if self.highlight_var.get() and self.bold_var.get():
                    self.text_area.tag_add("highlight_bold", pos, end_idx)
                elif self.highlight_var.get():
                    self.text_area.tag_add("highlight", pos, end_idx)
                elif self.bold_var.get():
                    self.text_area.tag_add("bold", pos, end_idx)

                start_idx = end_idx

    def clear_formatting(self):
        """清除所有文本格式"""
        for tag in ["highlight", "bold", "highlight_bold"]:
            self.text_area.tag_remove(tag, 1.0, tk.END)


def main():
    root = tk.Tk()
    app = TextFileViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()