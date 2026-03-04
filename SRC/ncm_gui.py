import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ncmdump import dump


class NCMConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("网易云音乐 NCM 解密工具")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        self.files = []  # 存储文件信息: [{path, size, status, item_id}, ...]
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.default_output_dir = os.path.join(os.path.dirname(self.script_dir), "输出")
        
        self.setup_ui()
        self.update_stats()
        self.log("工具就绪，请添加 NCM 文件")
    
    def setup_ui(self):
        # ========== 顶部按钮区 ==========
        btn_frame = tk.Frame(self.root, padx=10, pady=10)
        btn_frame.pack(fill=tk.X)
        
        self.btn_add_file = tk.Button(btn_frame, text="添加文件", command=self.add_files, width=12)
        self.btn_add_file.pack(side=tk.LEFT, padx=(0, 8))
        
        self.btn_add_folder = tk.Button(btn_frame, text="添加文件夹", command=self.add_folder, width=12)
        self.btn_add_folder.pack(side=tk.LEFT, padx=(0, 8))
        
        self.btn_delete = tk.Button(btn_frame, text="删除", command=self.delete_selected, width=12)
        self.btn_delete.pack(side=tk.LEFT, padx=(0, 8))
        
        self.btn_clear = tk.Button(btn_frame, text="清空", command=self.clear_all, width=12)
        self.btn_clear.pack(side=tk.LEFT)
        
        # ========== 文件列表区 ==========
        list_frame = tk.Frame(self.root, padx=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Treeview 表格
        columns = ("filename", "size", "status", "action")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="extended")
        
        self.tree.heading("filename", text="文件名")
        self.tree.heading("size", text="大小")
        self.tree.heading("status", text="状态")
        self.tree.heading("action", text="操作")
        
        self.tree.column("filename", width=300, anchor=tk.W)
        self.tree.column("size", width=80, anchor=tk.CENTER)
        self.tree.column("status", width=100, anchor=tk.CENTER)
        self.tree.column("action", width=80, anchor=tk.CENTER)
        
        # 滚动条
        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # 统计信息
        self.lbl_stats = tk.Label(self.root, text="文件总数: 0  总大小: 0 MB", anchor=tk.W, padx=10)
        self.lbl_stats.pack(fill=tk.X, pady=2)
        
        # ========== 输出设置区 ==========
        settings_frame = tk.LabelFrame(self.root, text="输出设置", padx=10, pady=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 保存到
        path_frame = tk.Frame(settings_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(path_frame, text="保存到:").pack(side=tk.LEFT)
        self.entry_output = tk.Entry(path_frame)
        self.entry_output.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry_output.insert(0, self.default_output_dir)
        
        tk.Button(path_frame, text="浏览...", command=self.browse_output, width=8).pack(side=tk.LEFT)
        
        # 音质选择 + 开始按钮
        bottom_frame = tk.Frame(settings_frame)
        bottom_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(bottom_frame, text="音质选择:").pack(side=tk.LEFT)
        
        self.quality_var = tk.StringVar(value="VBR")
        tk.Radiobutton(bottom_frame, text="VBR 高质量", variable=self.quality_var, value="VBR").pack(side=tk.LEFT, padx=(5, 10))
        tk.Radiobutton(bottom_frame, text="CBR 320k", variable=self.quality_var, value="320k").pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(bottom_frame, text="CBR 192k", variable=self.quality_var, value="192k").pack(side=tk.LEFT)
        
        self.btn_convert = tk.Button(bottom_frame, text="开始转换 (0 个文件)", command=self.start_convert, 
                                      width=18, bg="#4CAF50", fg="white", state=tk.DISABLED)
        self.btn_convert.pack(side=tk.RIGHT)
        
        # ========== 日志状态栏 ==========
        log_frame = tk.LabelFrame(self.root, text="日志", padx=10, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
    
    def update_stats(self):
        """更新统计信息"""
        total = len(self.files)
        total_size = sum(f['size'] for f in self.files)
        
        self.lbl_stats.config(text=f"文件总数: {total}  总大小: {self.format_size(total_size)}")
        
        if total > 0:
            self.btn_convert.config(text=f"开始转换 ({total} 个文件)", state=tk.NORMAL)
        else:
            self.btn_convert.config(text="开始转换 (0 个文件)", state=tk.DISABLED)
    
    def log(self, message):
        """添加日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def add_files(self):
        """添加文件"""
        file_paths = filedialog.askopenfilenames(
            title="选择 NCM 文件",
            filetypes=[("NCM 文件", "*.ncm"), ("所有文件", "*.*")],
            initialdir=self.script_dir
        )
        
        for path in file_paths:
            if not any(f['path'] == path for f in self.files):
                size = os.path.getsize(path)
                item_id = self.tree.insert("", tk.END, values=(
                    os.path.basename(path),
                    self.format_size(size),
                    "等待中",
                    "-"
                ))
                self.files.append({
                    'path': path,
                    'size': size,
                    'status': '等待中',
                    'item_id': item_id
                })
        
        self.update_stats()
        self.log(f"已添加 {len(file_paths)} 个文件")
    
    def add_folder(self):
        """添加文件夹"""
        folder_path = filedialog.askdirectory(title="选择包含 NCM 文件的文件夹", initialdir=self.script_dir)
        if not folder_path:
            return
        
        added = 0
        for root, _, files in os.walk(folder_path):
            for filename in files:
                if filename.lower().endswith('.ncm'):
                    path = os.path.join(root, filename)
                    if not any(f['path'] == path for f in self.files):
                        size = os.path.getsize(path)
                        item_id = self.tree.insert("", tk.END, values=(
                            filename,
                            self.format_size(size),
                            "等待中",
                            "-"
                        ))
                        self.files.append({
                            'path': path,
                            'size': size,
                            'status': '等待中',
                            'item_id': item_id
                        })
                        added += 1
        
        self.update_stats()
        self.log(f"从文件夹添加了 {added} 个文件")
    
    def delete_selected(self):
        """删除选中项"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要删除的文件")
            return
        
        # 从后往前删除，避免索引混乱
        items_to_remove = []
        for item_id in selected:
            for i, f in enumerate(self.files):
                if f['item_id'] == item_id:
                    items_to_remove.append(i)
                    self.tree.delete(item_id)
                    break
        
        # 从列表中删除
        for i in sorted(items_to_remove, reverse=True):
            self.files.pop(i)
        
        self.update_stats()
        self.log(f"删除了 {len(selected)} 个文件")
    
    def clear_all(self):
        """清空全部"""
        if not self.files:
            return
        
        if messagebox.askyesno("确认", f"确定要清空全部 {len(self.files)} 个文件吗？"):
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.files.clear()
            self.update_stats()
            self.log("已清空所有文件")
    
    def browse_output(self):
        """浏览输出目录"""
        dir_path = filedialog.askdirectory(
            title="选择输出目录",
            initialdir=self.entry_output.get() or self.script_dir
        )
        if dir_path:
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, dir_path)
            self.log(f"设置输出目录: {dir_path}")
    
    def update_file_status(self, item_id, status, action="-"):
        """更新文件状态（线程安全）"""
        self.root.after(0, lambda: self._do_update_status(item_id, status, action))
    
    def _do_update_status(self, item_id, status, action):
        """实际更新状态"""
        values = self.tree.item(item_id, "values")
        self.tree.item(item_id, values=(values[0], values[1], status, action))
    
    def convert_worker(self):
        """转换工作线程"""
        output_dir = self.entry_output.get().strip() or self.default_output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        success_count = fail_count = 0
        total = len(self.files)
        
        for i, file_info in enumerate(self.files, 1):
            if file_info['status'] == '已完成':
                continue
            
            self.update_file_status(file_info['item_id'], "转换中...", "-")
            self.log(f"[{i}/{total}] 正在转换: {os.path.basename(file_info['path'])}")
            
            try:
                result = dump(file_info['path'], output_dir)
                file_info['status'] = '已完成'
                self.update_file_status(file_info['item_id'], "✓ 成功", result)
                self.log(f"  ✓ 成功: {result}")
                success_count += 1
            except Exception as e:
                file_info['status'] = '失败'
                self.update_file_status(file_info['item_id'], "✗ 失败", str(e)[:20])
                self.log(f"  ✗ 失败: {e}")
                fail_count += 1
        
        self.root.after(0, lambda: self._conversion_done(success_count, fail_count))
    
    def _conversion_done(self, success, fail):
        """转换完成回调"""
        self.set_buttons_state(tk.NORMAL)
        self.log("-" * 40)
        self.log(f"转换完成: 成功 {success} 个, 失败 {fail} 个")
        messagebox.showinfo("完成", f"批量解密完成！\n成功: {success} 个\n失败: {fail} 个")
    
    def set_buttons_state(self, state):
        """设置按钮状态"""
        self.btn_add_file.config(state=state)
        self.btn_add_folder.config(state=state)
        self.btn_delete.config(state=state)
        self.btn_clear.config(state=state)
        self.btn_convert.config(state=state)
    
    def start_convert(self):
        """开始转换"""
        if not self.files:
            messagebox.showwarning("提示", "请先添加文件")
            return
        
        output_dir = self.entry_output.get().strip() or self.default_output_dir
        self.log(f"开始转换 {len(self.files)} 个文件...")
        self.log(f"输出目录: {output_dir}")
        self.log("-" * 40)
        
        self.set_buttons_state(tk.DISABLED)
        
        # 启动工作线程
        thread = threading.Thread(target=self.convert_worker, daemon=True)
        thread.start()


def main():
    root = tk.Tk()
    app = NCMConverterGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
