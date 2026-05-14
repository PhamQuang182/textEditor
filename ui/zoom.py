import tkinter.font as tkfont


def setup_zoom(text_edit, line_numbers):
    """Bind Ctrl+Scroll to zoom the text widget in and out."""

    def _on_zoom(event):
        font_obj = tkfont.Font(font=text_edit.cget("font"))
        size = font_obj.cget("size")

        if event.delta > 0 or event.num == 4:
            size += 1
        elif event.delta < 0 or event.num == 5:
            size = max(6, size - 1)

        text_edit.config(font=(font_obj.cget("family"), size))
        line_numbers._update_line_numbers()

        # Lock window size after font change
        window = text_edit.winfo_toplevel()
        window.geometry(f"{window.winfo_width()}x{window.winfo_height()}")

    text_edit.bind("<Control-MouseWheel>", _on_zoom)
    text_edit.bind("<Control-Button-4>", _on_zoom)
    text_edit.bind("<Control-Button-5>", _on_zoom)