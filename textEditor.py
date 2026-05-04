import tkinter as tk
from tkinter.filedialog import askopenfilename, asksaveasfilename

current_file = None

# Open file
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

# Save file as
def save_as(window, text_edit):
    global current_file

    filepath = asksaveasfilename(
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

# Save file
def save_file(window, text_edit):
    global current_file

    if current_file is None:
        save_as(window, text_edit)
        return
    with open(current_file, "w") as f:
        content = text_edit.get(1.0, tk.END)
        f.write(content)
    window.title(f"Saved: {current_file}")

def main():
    window = tk.Tk()
    window.title("Text Editor")
    window.rowconfigure(0, minsize=400)
    window.columnconfigure(1, minsize=400)

    text_edit = tk.Text(window, font = "COLRv0 12")
    text_edit.grid(row = 0, column = 1)

    frame = tk.Frame(window, relief=tk.RAISED, bd = 2)
    save_button = tk.Button(frame, text = "Save", command = lambda: save_file(window, text_edit))
    saveas_button = tk.Button(frame, text = "Save As", command = lambda: save_as(window, text_edit))
    open_button = tk.Button(frame, text = "Open", command = lambda: open_file(window, text_edit))
    
    save_button.grid(row = 0, column = 0, padx=5, pady=5, sticky="ew")
    saveas_button.grid(row = 1, column = 0, padx=5, pady=5, sticky="ew")
    open_button.grid(row = 2, column = 0, padx=5, pady=5, sticky="ew")
    frame.grid(row = 0, column = 0, sticky="ns")

    window.mainloop()

main()