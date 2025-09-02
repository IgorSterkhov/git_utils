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

    print(f"Checkout and pull {args.branch2}...")
    git_checkout_branch(args.branch2)
    git_pull(args.branch2)

    print(f"Checkout and pull {args.branch1}...")
    git_checkout_branch(args.branch1)
    git_pull(args.branch1)

    print(f"Creating branch {args.branch3}...")
    git_checkout_branch(args.branch3, create_new=True, force_delete=True)

    # print(f"Copying files from branch {args.branch1}...")
    # copy_branch_files_to_workdir(args.branch1)

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

    def on_choose_version(file_path, chosen_branch, content=None):
        if chosen_branch == args.branch1:
            print(f'Восстанавливаем версию файла {file_path} из ветки {args.branch1}')
            git_restore_file_from_branch(file_path, args.branch1)
        elif chosen_branch == args.branch2:
            print(f'Записываем в файл {file_path}')
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
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