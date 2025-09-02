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

def git_commit_all(message):
    # Stage the file and commit
    run_git_command(["add ."])
    run_git_command(["commit", "-m", message])