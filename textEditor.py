import tkinter as tk

from core.file_ops import open_file, save_file, save_as
from core.edit_ops import safe_edit_undo, safe_edit_redo
from core.search import open_find_replace
from ui import line_numbers
from ui.line_numbers import LineNumbers
from ui.toolbar import build_toolbar, bind_keys
from ui.zoom import setup_zoom

def main():
    window = tk.Tk()
    window.title("Text Editor")
    window.rowconfigure(1, weight=1)
    window.columnconfigure(1, weight=1)

    # Toolbar
    frame = tk.Frame(window, relief=tk.RAISED, bd=2)
    frame.grid(row=0, column=0, columnspan=3, sticky="ew")

    # Text widget
    text_edit = tk.Text(window, font="Courier 12", undo=True, autoseparators=True, maxundo=-1)
    text_edit.grid(row=1, column=1, sticky="nsew")

    # Line number gutter
    line_numbers = LineNumbers(window, text_edit, bg='lightgray')
    line_numbers.grid(row=1, column=0, sticky='nsew')

    # Scrollbar
    scrollbar = tk.Scrollbar(window, command=text_edit.yview)
    def _yscroll(*args):
        scrollbar.set(*args)
        line_numbers._update_line_numbers()
    text_edit.config(yscrollcommand=_yscroll)
    scrollbar.grid(row=1, column=2, sticky='ns')

    setup_zoom(text_edit, line_numbers)

    callbacks = {
        "save":         lambda: save_file(window, text_edit),
        "save_as":      lambda: save_as(window, text_edit),
        "open":         lambda: open_file(window, text_edit),
        "find_replace": lambda: open_find_replace(window, text_edit),
        "undo":         lambda: safe_edit_undo(text_edit),
        "redo":         lambda: safe_edit_redo(text_edit),
    }

    build_toolbar(window, frame, text_edit, callbacks)
    bind_keys(window, text_edit, callbacks)

    window.mainloop()


main()