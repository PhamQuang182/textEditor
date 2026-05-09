import tkinter as tk


def build_toolbar(window, frame, text_edit, callbacks):
    """
    Build and grid all toolbar buttons.

    Args:
        window:    The root Tk window.
        frame:     The Frame widget to place buttons in.
        text_edit: The main Text widget.
        callbacks: Dict of action name -> callable.
    """
    buttons = [
        ("Save",         callbacks["save"]),
        ("Save As",      callbacks["save_as"]),
        ("Open",         callbacks["open"]),
        ("Find/Replace", callbacks["find_replace"]),
    ]

    for row, (label, cmd) in enumerate(buttons):
        tk.Button(frame, text=label, command=cmd).grid(
            row=row, column=0, padx=5, pady=5, sticky="ew"
        )


def bind_keys(window, text_edit, callbacks):
    """
    Register all application-wide keybindings.

    Args:
        window:    The root Tk window.
        text_edit: The main Text widget.
        callbacks: Dict of action name -> callable.
    """
    window.bind_all("<Control-z>", lambda e: callbacks["undo"]())
    window.bind_all("<Control-y>", lambda e: callbacks["redo"]())
    window.bind_all("<Control-Shift-Z>", lambda e: callbacks["redo"]())
    window.bind_all("<Control-f>", lambda e: callbacks["find_replace"]())