import tkinter as tk


def safe_edit_undo(text_edit):
    """Call edit_undo safely (ignore when no undo steps available)."""
    try:
        text_edit.edit_undo()
    except tk.TclError:
        pass


def safe_edit_redo(text_edit):
    """Call edit_redo safely (ignore when no redo steps available)."""
    try:
        text_edit.edit_redo()
    except tk.TclError:
        pass