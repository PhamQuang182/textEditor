import tkinter as tk
from tkinter.filedialog import askopenfilename, asksaveasfilename

current_file = None


def open_file(window, text_edit):
    global current_file
    filepath = askopenfilename(
        filetypes=[
            ("Text Files", "*.txt"),
            ("JSON Files", "*.json"),
            ("All Files", "*.*")
        ])
    if not filepath:
        return

    text_edit.delete(1.0, tk.END)
    with open(filepath, "r") as f:
        content = f.read()
        text_edit.insert(tk.END, content)
    current_file = filepath
    window.title(f"Open File: {filepath}")


def get_default_filename(text_edit):
    """Extract first 30 chars from the first line to use as default filename."""
    first_line = text_edit.get("1.0", "1.end").strip()

    if not first_line:
        return "untitled"

    invalid_chars = r'\/:*?"<>|'
    sanitized = "".join(c for c in first_line if c not in invalid_chars)

    return sanitized[:30].strip() or "untitled"


def save_as(window, text_edit):
    global current_file
    default_name = get_default_filename(text_edit)

    filepath = asksaveasfilename(
        initialfile=default_name,
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt"), ("JSON Files", "*.json")]
    )
    if not filepath:
        return

    with open(filepath, "w") as f:
        content = text_edit.get(1.0, tk.END)
        f.write(content)
    current_file = filepath
    window.title(f"Save File: {filepath}")


def save_file(window, text_edit):
    global current_file

    if current_file is None:
        save_as(window, text_edit)
        return
    with open(current_file, "w") as f:
        content = text_edit.get(1.0, tk.END)
        f.write(content)
    window.title(f"Saved: {current_file}")