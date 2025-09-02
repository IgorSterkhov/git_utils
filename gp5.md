Для реализации описанного функционала с командной строкой, git-операциями и графическим интерфейсом предлагается следующая структура проекта и примерная реализация основных модулей.

***

## Структура проекта

```
project/
│
├── main.py         # Точка входа, обработка CLI, взаимодействие модулей
├── gui.py          # Графический интерфейс на tkinter
├── git_utils.py    # Обертки для работы с git и файловыми операциями
└── requirements.txt
```

***

## requirements.txt

```txt
# Требуемые библиотеки
# tkinter входит в стандартную библиотеку Python,
# другие библиотеки тоже стандартные, следовательно пусто или можно вписать минимальный Python
```

***

## git_utils.py

```python
import subprocess
import os
import shutil

def run_git_command(args, cwd=None):
    result = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Git command failed: git {' '.join(args)}\n{result.stderr.strip()}")
    return result.stdout.strip()

def is_git_repo(path="."):
    try:
        run_git_command(["rev-parse", "--is-inside-work-tree"], cwd=path)
        return True
    except Exception:
        return False

def git_fetch_origin():
    return run_git_command(["fetch", "origin"])

def git_checkout_branch(branch, create_new=False, force_delete=False):
    if force_delete:
        # Delete branch if exists
        branches = run_git_command(["branch"]).splitlines()
        branches = [b.strip().lstrip("* ") for b in branches]
        if branch in branches:
            run_git_command(["branch", "-D", branch])
    if create_new:
        run_git_command(["checkout", "-b", branch])
    else:
        run_git_command(["checkout", branch])
        
def git_pull(branch):
    run_git_command(["pull", "origin", branch])

def copy_branch_files_to_workdir(branch):
    # Clean current working directory except .git
    for root, dirs, files in os.walk("."):
        # avoid .git directory
        if ".git" in dirs:
            dirs.remove(".git")
        for f in files:
            try:
                os.remove(os.path.join(root, f))
            except Exception:
                pass
        for d in dirs:
            try:
                shutil.rmtree(os.path.join(root, d))
            except Exception:
                pass
    # Checkout the files from branch forcibly without switching branch
    run_git_command(["checkout", branch, "--", "."])

def checkout_different_files_from_branch2(branch2):
    # git checkout branch2 -- . will overwrite all files, we want only changed files compared to current
    # Using "git checkout branch2 -- ." as per instructions
    run_git_command(["checkout", branch2, "--", "."])

def git_status_modified_files():
    status_output = run_git_command(["status", "-s"])
    # Lines starting with M or ?? are modified or untracked
    files = []
    for line in status_output.splitlines():
        status_code, file_path = line[0:2].strip(), line[3:].strip()
        if status_code in {"M", "??"}:
            files.append(file_path)
    return files

def get_file_last_commit_info(branch, file_path):
    # Get last commit hash, author name, date and commit message for a file in branch
    try:
        result = run_git_command(["log", "-1", "--pretty=format:%H%x09%an%x09%ad", branch, "--", file_path])
        commit_hash, author, date = result.split("\t")
        return {"commit_hash": commit_hash, "author": author, "date": date}
    except Exception:
        return {"commit_hash": None, "author": None, "date": None}

def read_file_at_branch(branch, file_path):
    try:
        content = run_git_command(["show", f"{branch}:{file_path}"])
        return content
    except Exception:
        return ""

def git_restore_file_from_branch(file_path, branch):
    # Restore file content from branch (discard changes)
    run_git_command(["restore", "--source", branch, "--", file_path])

def git_commit_file(file_path, message):
    # Stage the file and commit
    run_git_command(["add", file_path])
    run_git_command(["commit", "-m", message])
```

***

## gui.py

```python
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext

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
        
        # Frame for content display and controls on right
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Frames for branch1 and branch2 content views
        self.branch1_frame = ttk.Frame(right_frame)
        self.branch1_frame.pack(fill=tk.BOTH, expand=True)

        self.branch2_frame = ttk.Frame(right_frame)
        self.branch2_frame.pack(fill=tk.BOTH, expand=True)

        # Branch1 widgets
        self.label_branch1 = ttk.Label(self.branch1_frame, text=f"{self.branch1} - файл / дата / автор")
        self.label_branch1.pack(anchor="w")

        self.text_branch1 = scrolledtext.ScrolledText(self.branch1_frame, height=10)
        self.text_branch1.pack(fill=tk.BOTH, expand=True)

        self.btn_branch1 = ttk.Button(self.branch1_frame, text=f"Оставить из {self.branch1}", command=self.leave_branch1)
        self.btn_branch1.pack(pady=5)

        # Separator between the two branch blocks
        self.separator = ttk.Separator(right_frame, orient=tk.HORIZONTAL)
        self.separator.pack(fill=tk.X, pady=10)

        # Branch2 widgets
        self.label_branch2 = ttk.Label(self.branch2_frame, text=f"{self.branch2} - файл / дата / автор")
        self.label_branch2.pack(anchor="w")

        self.text_branch2 = scrolledtext.ScrolledText(self.branch2_frame, height=10)
        self.text_branch2.pack(fill=tk.BOTH, expand=True)

        self.btn_branch2 = ttk.Button(self.branch2_frame, text=f"Оставить из {self.branch2}", command=self.leave_branch2)
        self.btn_branch2.pack(pady=5)

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

        label1 = f"{file_name}  |  {info1['date']}  |  {info1['author']}" if info1['author'] else file_name
        label2 = f"{file_name}  |  {info2['date']}  |  {info2['author']}" if info2['author'] else file_name

        self.label_branch1.config(text=label1)
        self.label_branch2.config(text=label2)

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
        messagebox.showinfo("Сохранено", f"Выбрана версия из {self.branch1} для {self.selected_file}")

    def leave_branch2(self):
        if not self.selected_file:
            messagebox.showerror("Ошибка", "Файл не выбран")
            return
        # Текст из виджета branch2 может быть изменён пользователем
        content = self.text_branch2.get(1.0, tk.END)
        commit_message = simpledialog.askstring("Комментарий к коммиту", "Введите комментарий к коммиту для файла:")
        if commit_message is None or commit_message.strip() == "":
            messagebox.showerror("Ошибка", "Комментарий к коммиту обязателен")
            return
        self.on_choose_version(self.selected_file, self.branch2, {"content": content, "commit_message": commit_message.strip()})
        messagebox.showinfo("Сохранено", f"Выбрана версия из {self.branch2} для {self.selected_file}")
```

***

## main.py

```python
import argparse
import sys
import os
from git_utils import *
from gui import MergeToolGUI

def parse_args():
    parser = argparse.ArgumentParser(description="Git merge helper tool")
    parser.add_argument("--branch1", required=True, help="Name of branch1")
    parser.add_argument("--branch2", required=True, help="Name of branch2")
    parser.add_argument("--branch3", required=True, help="Name of new branch3")
    return parser.parse_args()

def main():
    args = parse_args()

    if not is_git_repo():
        print("Текущая директория не является git-репозиторием")
        sys.exit(1)

    print("Fetching origin...")
    git_fetch_origin()

    print(f"Checkout and pull {args.branch1}...")
    git_checkout_branch(args.branch1)
    git_pull(args.branch1)

    print(f"Checkout and pull {args.branch2}...")
    git_checkout_branch(args.branch2)
    git_pull(args.branch2)

    print(f"Creating branch {args.branch3}...")
    git_checkout_branch(args.branch3, create_new=True, force_delete=True)

    print(f"Copying files from branch {args.branch1}...")
    copy_branch_files_to_workdir(args.branch1)

    print(f"Copying changed files from branch {args.branch2}...")
    checkout_different_files_from_branch2(args.branch2)

    modified_files = git_status_modified_files()
    if not modified_files:
        print("Нет измененных файлов для обработки")
        sys.exit(0)

    def get_content(branch, file_path):
        return read_file_at_branch(branch, file_path)

    def get_commit_info(branch, file_path):
        return get_file_last_commit_info(branch, file_path)

    def on_choose_version(file_path, chosen_branch, extra):
        if chosen_branch == args.branch1:
            # Восстановить файл из ветки1 (discarge changes)
            git_restore_file_from_branch(file_path, args.branch1)
        elif chosen_branch == args.branch2:
            content = extra["content"]
            commit_message = extra["commit_message"]
            # Перезаписать файл содержимым из версии ветки2
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            # Сделать коммит изменения для ветки3
            git_commit_file(file_path, commit_message)

    app = MergeToolGUI(
        files=modified_files,
        branch1_name=args.branch1,
        branch2_name=args.branch2,
        branch3_name=args.branch3,
        get_content_func=get_content,
        get_commit_info_func=get_commit_info,
        on_choose_version=on_choose_version
    )
    app.mainloop()

if __name__ == "__main__":
    main()
```

***

# Объяснение

- `main.py` обрабатывает параметры командной строки, проверяет git-репозиторий, делает нужные git-операции, создает ветку3, копирует файлы, определяет изменённые файлы и запускает GUI.
- В `git_utils.py` представлены функции-обёртки для вызова git, копирования файлов и получения информации о коммитах.
- В `gui.py` реализован класс на tkinter, который отображает файлы, их содержимое из двух веток, позволяет выбирать версии и сохранять решение.
- Коммиты из ветки2 создаются только если выбрана версия этой ветки и при этом пользователь вводит комментарий.

Это примерная подробная реализация с соблюдением всех указанных требований. Можно расширять и улучшать интерфейс или логику по необходимости.