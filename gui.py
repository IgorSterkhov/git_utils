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

        self.original_files = files  # исходный список, без фильтрации
        self.filtered_files = files.copy()
        self.branch1 = branch1_name
        self.branch2 = branch2_name
        self.branch3 = branch3_name
        self.get_content = get_content_func
        self.get_commit_info = get_commit_info_func
        self.on_choose_version = on_choose_version
        self.selected_file = None

        # Слева Frame для списка файлов и чекбоксов
        left_frame = ttk.Frame(self)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        self.file_listbox = tk.Listbox(left_frame, width=30)
        self.file_listbox.pack(fill=tk.Y, expand=True)
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_selected)

        # Чекбоксы под списком
        self.var_hide_same = tk.BooleanVar(value=True)
        self.var_hide_drop = tk.BooleanVar(value=False)

        self.checkbox_hide_same = ttk.Checkbutton(left_frame, text="не показывать совпадающие",
                                                  variable=self.var_hide_same,
                                                  command=self.on_checkbox_hide_same_toggle)
        self.checkbox_hide_same.pack(anchor='w', pady=2)

        self.checkbox_hide_drop = ttk.Checkbutton(left_frame, text="не показывать DROP'ы",
                                                 variable=self.var_hide_drop,
                                                 command=self.on_files_filter_change)
        self.checkbox_hide_drop.pack(anchor='w', pady=2)

        # Правый Frame
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Ветка 1
        self.branch1_frame = ttk.Frame(right_frame)
        self.branch1_frame.pack(fill=tk.BOTH, expand=True)

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

        # Ветка 2
        self.branch2_frame = ttk.Frame(right_frame)
        self.branch2_frame.pack(fill=tk.BOTH, expand=True)

        self.label_branch2 = ttk.Label(self.branch2_frame, text=f"{self.branch2} - файл / дата / автор")
        self.label_branch2.pack(anchor="w")

        self.text_branch2 = scrolledtext.ScrolledText(self.branch2_frame, height=10, wrap='word')
        self.text_branch2.pack(fill=tk.BOTH, expand=True)

        self.btn_branch2 = ttk.Button(self.branch2_frame, text=f"Оставить из {self.branch2} (отредактированный вариант)",
                                      command=self.leave_branch2)
        self.btn_branch2.pack(pady=5)

        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Добавляем сепаратор и заголовок для блока сравнения
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        self.label_compare = ttk.Label(right_frame, text="Сравнение файлов", font=('TkDefaultFont', 10, 'bold'))
        self.label_compare.pack(anchor="w", padx=5)

        # Новый текстовый блок для сравнения сразу
        self.text_compare = scrolledtext.ScrolledText(right_frame, height=15, wrap='none')
        self.text_compare.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 10))

        # Коммит кнопка
        self.btn_commit = ttk.Button(right_frame, text="Commit all", command=self.gui_commit_all)
        self.btn_commit.pack(pady=5)

        # Изначально активируем/деактивируем чекбоксы правильно
        self.update_drop_checkbox_state()

        # Заполнить список с фильтрацией
        self.apply_files_filter()

        # Если есть файлы после фильтрации выбираем первый
        if self.filtered_files:
            self.file_listbox.selection_set(0)
            self.load_file_content(self.filtered_files[0])

    def on_checkbox_hide_same_toggle(self):
        self.update_drop_checkbox_state()
        self.apply_files_filter()

    def update_drop_checkbox_state(self):
        if self.var_hide_same.get():
            self.checkbox_hide_drop.state(['!disabled'])
        else:
            self.var_hide_drop.set(False)
            self.checkbox_hide_drop.state(['disabled'])

    def on_files_filter_change(self):
        self.apply_files_filter()

    def apply_files_filter(self):
        # Фильтрация списка файлов в зависимости от чекбоксов
        filtered = []
        for f in self.original_files:
            # Получаем содержимое файлов для сравнения
            content1 = self.get_content(self.branch1, f)
            content2 = self.get_content(self.branch2, f)

            # Форматируем тексты и разбиваем
            text1 = format_sql(content1).splitlines()
            text2 = format_sql(content2).splitlines()

            diff = list(difflib.ndiff(text1, text2))

            # Проверяем отличие
            has_diff = any(line.startswith('+') or line.startswith('-') for line in diff)

            # Если "не показывать совпадающие" включен, пропускаем если нет отличий
            if self.var_hide_same.get() and not has_diff:
                continue

            # Если "не показывать DROP'ы" включен, пропускаем если в отличиях есть DROP или пустые строки
            if self.var_hide_drop.get():
                diff_lines = [line for line in diff if line.startswith('+') or line.startswith('-')]
                # Проверяем наличие "DROP" или пустых различий
                if any((('DROP' in line.upper()) or (line.strip() in {'+', '-', '+ ', '- ', ''})) for line in diff_lines):
                    continue

            filtered.append(f)

        # Обновляем список файлов на экране
        self.filtered_files = filtered
        self.file_listbox.delete(0, tk.END)
        for f in self.filtered_files:
            self.file_listbox.insert(tk.END, f)

        # Если список пуст, очистить текстовые поля
        if not self.filtered_files:
            self.selected_file = None
            self.text_branch1.delete(1.0, tk.END)
            self.text_branch2.delete(1.0, tk.END)
            self.label_branch1.config(text="")
            self.label_branch2.config(text="")
            self.label_status.config(text="")
            self.text_compare.delete(1.0, tk.END)
        else:
            # Автоматически выбрать первый файл
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(0)
            self.load_file_content(self.filtered_files[0])

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

        if info1['author'] is None:
            self.label_status.config(text="NEW FILE")
        else:
            self.label_status.config(text="MODIFIED")

        self.text_branch1.config(state=tk.NORMAL)
        self.text_branch1.delete(1.0, tk.END)
        self.text_branch1.insert(tk.END, content1)
        self.text_branch1.config(state=tk.NORMAL)

        self.text_branch2.config(state=tk.NORMAL)
        self.text_branch2.delete(1.0, tk.END)
        self.text_branch2.insert(tk.END, content2)
        self.text_branch2.config(state=tk.NORMAL)

        # Вывести сравнение сразу при загрузке файла в text_compare
        self.update_file_comparison(content1, content2)

    def update_file_comparison(self, text1_raw, text2_raw):
        # Форматирование
        text1 = format_sql(text1_raw).splitlines()
        text2 = format_sql(text2_raw).splitlines()

        diff = difflib.ndiff(text1, text2)

        # Очищаем предыдущее содержимое
        self.text_compare.config(state=tk.NORMAL)
        self.text_compare.delete(1.0, tk.END)

        for line in diff:
            if line.startswith("-"):
                self.text_compare.insert(tk.END, line + "\n", 'deleted')
            elif line.startswith("+"):
                self.text_compare.insert(tk.END, line + "\n", 'added')
            elif line.startswith("?"):
                # Пропускаем линии подсветки символов различий
                continue
            else:
                self.text_compare.insert(tk.END, line + "\n")

        self.text_compare.tag_config('deleted', background='red', foreground='white')
        self.text_compare.tag_config('added', background='green', foreground='white')

        self.text_compare.config(state=tk.DISABLED)

    def leave_branch1(self):
        if not self.selected_file:
            messagebox.showerror("Ошибка", "Файл не выбран")
            return
        self.on_choose_version(self.selected_file, self.branch1, None)
        # Удаляем файл из списка
        if self.selected_file in self.filtered_files:
            index = self.filtered_files.index(self.selected_file)
            self.filtered_files.remove(self.selected_file)
            self.file_listbox.delete(index)
            self.selected_file = None
            messagebox.showinfo("Сохранено", f"Выбрана версия из {self.branch1}")

    def leave_branch2(self):
        if not self.selected_file:
            messagebox.showerror("Ошибка", "Файл не выбран")
            return
        content = self.text_branch2.get(1.0, tk.END)
        self.on_choose_version(self.selected_file, self.branch2, content)
        messagebox.showinfo("Сохранено", f"Выбрана версия из {self.branch2}")

    def gui_commit_all(self):
        commit_message = simpledialog.askstring("Комментарий к коммиту", "Введите комментарий к коммиту для файла:")
        if commit_message is None or commit_message.strip() == "":
            messagebox.showerror("Ошибка", "Комментарий к коммиту обязателен")
            return
        git_commit_all(commit_message)