import tkinter as tk


class LineNumbers(tk.Canvas):
    """Canvas widget that displays line numbers synced with a Text widget."""

    def __init__(self, parent, text_widget, **kwargs):
        super().__init__(parent, **kwargs)
        self.text_widget = text_widget
        self.config(width=50, bg='lightgray', highlightthickness=0)

        self.text_widget.bind('<<Configure>>', self._on_text_change)
        self.text_widget.bind('<<Modified>>', lambda e: (self._on_text_change(), self.text_widget.edit_modified(False)))
        self.text_widget.bind('<KeyRelease>', self._on_text_change)
        self.text_widget.bind('<MouseWheel>', self._on_scroll)
        self.text_widget.bind('<Button-4>', self._on_scroll)  # Linux scroll up
        self.text_widget.bind('<Button-5>', self._on_scroll)  # Linux scroll down

        self.after(100, self._update_line_numbers)

    def _on_text_change(self, event=None):
        self.after(10, self._update_line_numbers)

    def _on_scroll(self, event=None):
        self.after(10, self._update_line_numbers)

    def _update_line_numbers(self):
        """Redraw line numbers based on current text content and scroll position."""
        self.delete("all")

        first_visible = self.text_widget.index("@0,0")
        last_visible = self.text_widget.index(f"@0,{self.text_widget.winfo_height()}")

        first_line = int(first_visible.split('.')[0])
        last_line = int(last_visible.split('.')[0]) + 1
        total_lines = int(self.text_widget.index("end").split('.')[0])

        for line_num in range(first_line, min(last_line + 1, total_lines + 1)):
            bbox = self.text_widget.bbox(f"{line_num}.0")
            if bbox:
                y = bbox[1]
                self.create_text(
                    45, y,
                    text=str(line_num),
                    font=("Courier", 10),
                    fill="black",
                    anchor="ne"
                )