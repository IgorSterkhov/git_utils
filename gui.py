import difflib
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
from git_utils import git_commit_all
from ch_format import format_sql_with_clickhouse_format as format_sql

class MergeToolGUI(tk.Tk):
    def __init__(self, files, branch1_name, branch2_name, branch3_name, get_content_func, get_commit_info_func, on_choose_version):
        super().__init__()
        self.title(f"Merge Tool: {branch1_name} vs {branch2_name} into {branch3_name}")
        self.geometry("1000x700")
        self.files = files
        self.branch1 = branch1_name
        self.branch2 = branch2_name
        self.branch3 = branch3_name
        self.get_content = get_content_func
        self.get_commit_info = get_commit_info_func
        self.on_choose_version = on_choose_version
        self.selected_file = None

        # Left listbox for files
        self.file_listbox = tk.Listbox(self, width=30)
        for f in self.files:
            self.file_listbox.insert(tk.END, f)
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_selected)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.branch1_frame = ttk.Frame(right_frame)
        self.branch1_frame.pack(fill=tk.BOTH, expand=True)
        self.branch2_frame = ttk.Frame(right_frame)
        self.branch2_frame.pack(fill=tk.BOTH, expand=True)

        # Branch1 label and status label for modified/new file
        top_frame1 = ttk.Frame(self.branch1_frame)
        top_frame1.pack(fill=tk.X)
        self.label_branch1 = ttk.Label(top_frame1, text=f"{self.branch1} - файл / дата / автор")
        self.label_branch1.pack(side=tk.LEFT, anchor="w")
        self.label_status = ttk.Label(top_frame1, text="", font=('TkDefaultFont', 10, 'bold'), foreground='red')
        self.label_status.pack(side=tk.LEFT, padx=10)

        self.text_branch1 = scrolledtext.ScrolledText(self.branch1_frame, height=10, wrap='word')
        self.text_branch1.pack(fill=tk.BOTH, expand=True)
        self.btn_branch1 = ttk.Button(self.branch1_frame, text=f"Оставить из {self.branch1}", command=self.leave_branch1)
        self.btn_branch1.pack(pady=5)

        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        self.label_branch2 = ttk.Label(self.branch2_frame, text=f"{self.branch2} - файл / дата / автор")
        self.label_branch2.pack(anchor="w")
        self.text_branch2 = scrolledtext.ScrolledText(self.branch2_frame, height=10, wrap='word')
        self.text_branch2.pack(fill=tk.BOTH, expand=True)
        self.btn_branch2 = ttk.Button(self.branch2_frame, text=f"Оставить из {self.branch2} (отредактированный вариант)", command=self.leave_branch2)
        self.btn_branch2.pack(pady=5)

        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Добавляем кнопку сравнения файлов перед Commit
        self.btn_compare = ttk.Button(self.branch2_frame, text="Сравнить файлы", command=self.compare_files)
        self.btn_compare.pack(pady=5)

        self.btn_commit = ttk.Button(self.branch2_frame, text="Commit all", command=self.gui_commit_all)
        self.btn_commit.pack(pady=5)

        if self.files:
            self.file_listbox.selection_set(0)
            self.load_file_content(self.files[0])

    def on_file_selected(self, event):
        selection = self.file_listbox.curselection()
        if selection:
            file_name = self.file_listbox.get(selection[0])
            self.load_file_content(file_name)

    def load_file_content(self, file_name):
        self.selected_file = file_name
        content1 = self.get_content(self.branch1, file_name)
        content2 = self.get_content(self.branch2, file_name)
        info1 = self.get_commit_info(self.branch1, file_name)
        info2 = self.get_commit_info(self.branch2, file_name)

        label1 = f"{file_name} | {info1['date']} | {info1['author']}" if info1['author'] else file_name
        label2 = f"{file_name} | {info2['date']} | {info2['author']}" if info2['author'] else file_name

        self.label_branch1.config(text=label1)
        self.label_branch2.config(text=label2)

        # Определяем статус файла (новый или модифицированный)
        if info1['author'] is None:  # no commit info - возможно новый файл
            self.label_status.config(text="NEW FILE")
        else:
            # Проверяем, модифицирован ли файл, используя признак из self.files или дополнительный метод
            # Здесь предполагается, что self.files содержит список модифицированных/новых файлов
            # Можно сделать проверку через git_status_modified_files, если передается
            self.label_status.config(text="MODIFIED")

        self.text_branch1.config(state=tk.NORMAL)
        self.text_branch1.delete(1.0, tk.END)
        self.text_branch1.insert(tk.END, content1)
        self.text_branch1.config(state=tk.NORMAL)  # Editable

        self.text_branch2.config(state=tk.NORMAL)
        self.text_branch2.delete(1.0, tk.END)
        self.text_branch2.insert(tk.END, content2)
        self.text_branch2.config(state=tk.NORMAL)  # Editable

    def leave_branch1(self):
        if not self.selected_file:
            messagebox.showerror("Ошибка", "Файл не выбран")
            return
        self.on_choose_version(self.selected_file, self.branch1, None)
        # Удаляем файл из списка и из списка файлов
        if self.selected_file in self.files:
            index = self.files.index(self.selected_file)
            self.files.remove(self.selected_file)
            self.file_listbox.delete(index)
            self.selected_file = None
        messagebox.showinfo("Сохранено", f"Выбрана версия из {self.branch1} для {self.selected_file}")

    def leave_branch2(self):
        if not self.selected_file:
            messagebox.showerror("Ошибка", "Файл не выбран")
            return
        content = self.text_branch2.get(1.0, tk.END)
        self.on_choose_version(self.selected_file, self.branch2, content)
        messagebox.showinfo("Сохранено", f"Выбрана версия из {self.branch2} для {self.selected_file}")

    def gui_commit_all(self):
        commit_message = simpledialog.askstring("Комментарий к коммиту", "Введите комментарий к коммиту для файла:")
        if commit_message is None or commit_message.strip() == "":
            messagebox.showerror("Ошибка", "Комментарий к коммиту обязателен")
            return
        git_commit_all(commit_message)

    def compare_files(self):
        # Получаем тексты из двух полей
        text1 = format_sql(self.text_branch1.get(1.0, tk.END)).splitlines()
        text2 = format_sql(self.text_branch2.get(1.0, tk.END)).splitlines()

        diff = difflib.ndiff(text1, text2)
        diff_window = tk.Toplevel(self)
        diff_window.title(f"Сравнение файлов: {self.selected_file}")

        diff_text = scrolledtext.ScrolledText(diff_window, height=30, width=100, wrap='none')
        diff_text.pack(fill=tk.BOTH, expand=True)

        for line in diff:
            if line.startswith("-"):
                diff_text.insert(tk.END, line + "\n", 'deleted')
            elif line.startswith("+"):
                diff_text.insert(tk.END, line + "\n", 'added')
            elif line.startswith("?"):
                # Отметим символы различий
                continue
            else:
                diff_text.insert(tk.END, line + "\n")

        diff_text.tag_config('deleted', background='red', foreground='white')
        diff_text.tag_config('added', background='green', foreground='white')

        diff_text.config(state=tk.DISABLED)