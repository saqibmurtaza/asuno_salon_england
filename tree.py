import os

EXCLUDE_DIRS = {'.git', 'node_modules', '.venv', '__pycache__', '.next', '.idea', '.vscode'}
INDENT_STR = '│   '

lines = []

def print_tree_to_list(start_path: str, level: int = 0):
    try:
        entries = sorted(os.listdir(start_path))
    except PermissionError:
        return

    entries = [e for e in entries if e not in EXCLUDE_DIRS and not e.startswith('.')]

    for entry in entries:
        full_path = os.path.join(start_path, entry)
        indent = INDENT_STR * level + '├── '

        if os.path.isdir(full_path):
            lines.append(f"{indent}{entry}/")
            print_tree_to_list(full_path, level + 1)
        else:
            lines.append(f"{indent}{entry}")

if __name__ == "__main__":
    root = os.path.basename(os.getcwd())
    lines.append(f"{root}/")
    print_tree_to_list(".")
    
    with open("structure.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print("✅ Folder structure saved to 'structure.txt'")
