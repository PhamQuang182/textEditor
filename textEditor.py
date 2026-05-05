import tkinter as tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import messagebox
import re

current_file = None


class LineNumbers(tk.Canvas):
    """Canvas widget that displays line numbers synced with a Text widget."""
    
    def __init__(self, parent, text_widget, **kwargs):
        super().__init__(parent, **kwargs)
        self.text_widget = text_widget
        self.config(width=50, bg='lightgray', highlightthickness=0)
        
        # Bind to text widget events
        self.text_widget.bind('<<Configure>>', self._on_text_change)
        # Use <<Modified>> to detect content changes and KeyRelease for immediate updates
        self.text_widget.bind('<<Modified>>', lambda e: (self._on_text_change(), self.text_widget.edit_modified(False)))
        self.text_widget.bind('<KeyRelease>', self._on_text_change)
        # Mouse wheel events handled via yscrollcommand in main; keep fallback bindings
        self.text_widget.bind('<MouseWheel>', self._on_scroll)
        self.text_widget.bind('<Button-4>', self._on_scroll)  # Linux scroll up
        self.text_widget.bind('<Button-5>', self._on_scroll)  # Linux scroll down
        
        # Initial draw
        self.after(100, self._update_line_numbers)
    
    def _on_text_change(self, event=None):
        self.after(10, self._update_line_numbers)
    
    def _on_scroll(self, event=None):
        self.after(10, self._update_line_numbers)
    
    def _update_line_numbers(self):
        """Redraw line numbers based on current text content and scroll position."""
        self.delete("all")
        
        # Get the first and last visible line
        first_visible = self.text_widget.index("@0,0")
        last_visible = self.text_widget.index(f"@0,{self.text_widget.winfo_height()}")
        
        # Parse line numbers
        first_line = int(first_visible.split('.')[0])
        last_line = int(last_visible.split('.')[0]) + 1
        
        # Get total lines
        total_lines = int(self.text_widget.index("end").split('.')[0])
        
        # Draw line numbers
        y_offset = 0
        for line_num in range(first_line, min(last_line + 1, total_lines + 1)):
            # Get y coordinate for this line
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


def get_default_filename(text_edit):
    """Extract first 30 chars from the first line to use as default filename."""
    first_line = text_edit.get("1.0", "1.end").strip()  # Get only line 1

    if not first_line:
        return "untitled"

    # Sanitize: remove characters that are invalid in filenames
    invalid_chars = r'\/:*?"<>|'
    sanitized = "".join(c for c in first_line if c not in invalid_chars)

    return sanitized[:30].strip() or "untitled"

# Save file as
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

def _safe_edit_undo(text_edit):
    """Call edit_undo safely (ignore when no undo steps available)."""
    try:
        text_edit.edit_undo()
    except tk.TclError:
        pass


def _safe_edit_redo(text_edit):
    """Call edit_redo safely (ignore when no redo steps available)."""
    try:
        text_edit.edit_redo()
    except tk.TclError:
        pass


class SearchState:
    """Persistent search state for forward-iteration find behavior."""
    
    def __init__(self):
        self.pattern = None
        self.case_sensitive = False
        self.whole_word = False
        self.regex_mode = False
        self.wrap_around = True
        self.in_selection = False
        self.last_match_end = 0
        self.search_region_start = 0
        self.search_region_end = None
    
    def compile_pattern(self, pattern_str):
        """Compile pattern string into regex, respecting flags."""
        if not pattern_str:
            return None
        
        try:
            flags = 0
            if not self.case_sensitive:
                flags |= re.IGNORECASE
            
            if self.regex_mode:
                pattern = pattern_str
            else:
                pattern = re.escape(pattern_str)
            
            if self.whole_word:
                pattern = r'\b' + pattern + r'\b'
            
            return re.compile(pattern, flags | re.MULTILINE)
        except re.error as e:
            return None
    
    def search(self, text, pattern_compiled):
        """
        Search for next match starting from last_match_end.
        
        Returns:
            dict with keys:
            - match_start (int): offset of match start, or -1 if not found
            - match_end (int): offset of match end
            - matched_text (str): the matched text
            - status (str): 'found', 'not_found', or 'wrapped'
            - wrapped (bool): whether search wrapped around
        """
        if not pattern_compiled or not text:
            return {
                'match_start': -1, 'match_end': -1, 'matched_text': '',
                'status': 'not_found', 'wrapped': False
            }
        
        # Determine search bounds
        search_start = self.search_region_start
        search_end = self.search_region_end if self.search_region_end is not None else len(text)
        
        # Search forward from last_match_end
        wrapped = False
        search_from = max(self.last_match_end, search_start)
        
        for m in pattern_compiled.finditer(text[search_from:search_end]):
            match_start = search_from + m.start()
            match_end = search_from + m.end()
            
            # Skip zero-length matches by advancing by 1
            if match_start == match_end:
                continue
            
            # Update state and return
            self.last_match_end = match_end
            return {
                'match_start': match_start,
                'match_end': match_end,
                'matched_text': m.group(),
                'status': 'found',
                'wrapped': wrapped
            }
        
        # No match found in forward direction
        if self.wrap_around and search_from > search_start:
            # Wrap around to beginning of search region
            wrapped = True
            for m in pattern_compiled.finditer(text[search_start:search_from]):
                match_start = search_start + m.start()
                match_end = search_start + m.end()
                
                if match_start == match_end:
                    continue
                
                self.last_match_end = match_end
                return {
                    'match_start': match_start,
                    'match_end': match_end,
                    'matched_text': m.group(),
                    'status': 'wrapped',
                    'wrapped': wrapped
                }
        
        return {
            'match_start': -1, 'match_end': -1, 'matched_text': '',
            'status': 'not_found', 'wrapped': wrapped
        }
    
    def reset(self):
        """Reset search state (called when pattern changes or explicitly)."""
        self.pattern = None
        self.last_match_end = 0
        self.search_region_start = 0
        self.search_region_end = None


def open_find_replace(window, text_edit):
    """Open a Find & Replace dialog with regex support and highlighting."""
    top = tk.Toplevel(window)
    top.title("Find & Replace")
    top.transient(window)
    top.resizable(False, False)

    frm = tk.Frame(top)
    frm.pack(padx=8, pady=8)

    tk.Label(frm, text="Find:").grid(row=0, column=0, sticky="w")
    entry_find = tk.Entry(frm, width=30)
    entry_find.grid(row=0, column=1, padx=4, pady=2)

    tk.Label(frm, text="Replace:").grid(row=1, column=0, sticky="w")
    entry_replace = tk.Entry(frm, width=30)
    entry_replace.grid(row=1, column=1, padx=4, pady=2)

    # Options
    regex_var = tk.IntVar(value=0)
    case_var = tk.IntVar(value=0)
    whole_word_var = tk.IntVar(value=0)
    wrap_var = tk.IntVar(value=1)
    
    tk.Checkbutton(frm, text="Regex", variable=regex_var).grid(row=2, column=0, sticky="w")
    tk.Checkbutton(frm, text="Case Sensitive", variable=case_var).grid(row=2, column=1, sticky="w")
    tk.Checkbutton(frm, text="Whole Word", variable=whole_word_var).grid(row=3, column=0, sticky="w")
    tk.Checkbutton(frm, text="Wrap Around", variable=wrap_var).grid(row=3, column=1, sticky="w")

    # Ensure highlight tag exists
    text_edit.tag_configure("match", background="yellow")
    text_edit.tag_configure("match_current", background="orange")

    # Persistent search state
    search_state = SearchState()
    status_label = tk.Label(frm, text="", fg="blue")
    status_label.grid(row=4, column=0, columnspan=2, pady=(6, 0))

    def update_search_state():
        """Update SearchState from UI controls."""
        search_state.pattern = entry_find.get()
        search_state.regex_mode = regex_var.get()
        search_state.case_sensitive = case_var.get()
        search_state.whole_word = whole_word_var.get()
        search_state.wrap_around = wrap_var.get()
        search_state.in_selection = False  # Can be expanded later

    def on_pattern_change(*args):
        """Reset search when pattern changes."""
        search_state.reset()
        # Update cursor position for new search
        cursor_pos = len(text_edit.get("1.0", "insert"))
        search_state.last_match_end = cursor_pos
        search_state.search_region_start = 0
        search_state.search_region_end = None
        highlight_all()

    entry_find.bind('<KeyRelease>', on_pattern_change)

    def highlight_all():
        """Highlight all matches."""
        text_edit.tag_remove("match", "1.0", "end")
        update_search_state()
        comp = search_state.compile_pattern(search_state.pattern)
        if not comp:
            status_label.config(text="", fg="blue")
            return
        
        text = text_edit.get("1.0", "end-1c")
        count = 0
        for m in comp.finditer(text):
            if m.start() == m.end():
                continue
            start = f"1.0 + {m.start()} chars"
            end = f"1.0 + {m.end()} chars"
            text_edit.tag_add("match", start, end)
            count += 1
        
        if count > 0:
            status_label.config(text=f"Found {count} match(es)", fg="blue")
        else:
            status_label.config(text="No matches", fg="red")

    def find_next():
        """Find next match using stateful search."""
        update_search_state()
        
        if not entry_find.get():
            status_label.config(text="Enter search pattern", fg="red")
            return
        
        # Compile pattern
        comp = search_state.compile_pattern(search_state.pattern)
        if not comp:
            status_label.config(text="Invalid pattern", fg="red")
            return
        
        # Get text
        text = text_edit.get("1.0", "end-1c")
        
        # Set initial search position from cursor if this is first search
        if search_state.last_match_end == 0 or entry_find.get() != search_state.pattern:
            cursor_offset = len(text_edit.get("1.0", "insert"))
            search_state.last_match_end = cursor_offset
        
        # Perform search
        result = search_state.search(text, comp)
        
        # Clear previous selection
        text_edit.tag_remove("sel", "1.0", "end")
        
        if result['match_start'] != -1:
            start_idx = f"1.0 + {result['match_start']} chars"
            end_idx = f"1.0 + {result['match_end']} chars"
            text_edit.tag_add("sel", start_idx, end_idx)
            text_edit.mark_set("insert", end_idx)
            text_edit.see(start_idx)
            
            status = result['status']
            if status == 'wrapped':
                status_label.config(text="Wrapped around - found match", fg="green")
            else:
                status_label.config(text="Match found", fg="green")
        else:
            status_label.config(text="No match found", fg="red")
        
        # Update highlights
        highlight_all()

    def replace_one():
        """Replace the current selection."""
        sel = text_edit.tag_ranges("sel")
        if sel:
            start = sel[0]
            end = sel[1]
            repl = entry_replace.get()
            text_edit.delete(start, end)
            text_edit.insert(start, repl)
            # Reset and rehighlight
            search_state.reset()
            search_state.last_match_end = len(text_edit.get("1.0", start))
            highlight_all()
            status_label.config(text="Replaced 1 match", fg="green")
        else:
            status_label.config(text="No selection to replace", fg="red")

    def replace_all():
        """Replace all matches."""
        patt = entry_find.get()
        if not patt:
            status_label.config(text="Enter search pattern", fg="red")
            return
        
        repl = entry_replace.get()
        full = text_edit.get("1.0", "end-1c")
        
        update_search_state()
        comp = search_state.compile_pattern(patt)
        if not comp:
            status_label.config(text="Invalid pattern", fg="red")
            return
        
        # Count matches before replacement
        count = len([m for m in comp.finditer(full) if m.start() != m.end()])
        
        # Replace
        try:
            if search_state.regex_mode:
                new = re.sub(patt, repl, full, flags=(0 if search_state.case_sensitive else re.IGNORECASE))
            else:
                new = full.replace(patt, repl)
        except re.error as e:
            status_label.config(text=f"Error: {e}", fg="red")
            return
        
        # Update editor
        text_edit.delete("1.0", "end")
        text_edit.insert("1.0", new)
        
        # Reset search state
        search_state.reset()
        highlight_all()
        status_label.config(text=f"Replaced {count} match(es)", fg="green")
    
    def clear_highlight():
        """Clear all highlights."""
        text_edit.tag_remove("match", "1.0", "end")
        text_edit.tag_remove("match_current", "1.0", "end")
        search_state.reset()
        status_label.config(text="", fg="blue")

    # Buttons
    btn_frame = tk.Frame(frm)
    btn_frame.grid(row=5, column=0, columnspan=2, pady=(6, 0))
    tk.Button(btn_frame, text="Find Next", command=find_next).grid(row=0, column=0, padx=2)
    tk.Button(btn_frame, text="Highlight All", command=highlight_all).grid(row=0, column=1, padx=2)
    tk.Button(btn_frame, text="Replace", command=replace_one).grid(row=0, column=2, padx=2)
    tk.Button(btn_frame, text="Replace All", command=replace_all).grid(row=0, column=3, padx=2)
    tk.Button(btn_frame, text="Clear", command=clear_highlight).grid(row=0, column=4, padx=2)
    tk.Button(btn_frame, text="Close", command=top.destroy).grid(row=0, column=5, padx=2)

    entry_find.focus_set()



def main():
    window = tk.Tk()
    window.title("Text Editor")
    window.rowconfigure(0, minsize=400)
    window.columnconfigure(2, minsize=400)

    # Enable built-in multi-level undo/redo support
    text_edit = tk.Text(window, font="Courier 12", undo=True, autoseparators=True, maxundo=-1)
    text_edit.grid(row=0, column=2, sticky="nsew")

    # Create line number gutter
    line_numbers = LineNumbers(window, text_edit, bg='lightgray')
    line_numbers.grid(row=0, column=1, sticky='ns')

    # Vertical scrollbar
    scrollbar = tk.Scrollbar(window, command=text_edit.yview)
    def _yscroll(*args):
        scrollbar.set(*args)
        line_numbers._update_line_numbers()
    text_edit.config(yscrollcommand=_yscroll)
    scrollbar.grid(row=0, column=3, sticky='ns')

    frame = tk.Frame(window, relief=tk.RAISED, bd=2)
    save_button = tk.Button(frame, text="Save", command=lambda: save_file(window, text_edit))
    saveas_button = tk.Button(frame, text="Save As", command=lambda: save_as(window, text_edit))
    open_button = tk.Button(frame, text="Open", command=lambda: open_file(window, text_edit))
    findreplace_button = tk.Button(frame, text="Find/Replace", command=lambda: open_find_replace(window, text_edit))

    save_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
    saveas_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
    open_button.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
    findreplace_button.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
    frame.grid(row=0, column=0, sticky="ns")

    # Key bindings for Undo/Redo
    window.bind_all("<Control-z>", lambda event: _safe_edit_undo(text_edit))
    window.bind_all("<Control-y>", lambda event: _safe_edit_redo(text_edit))
    window.bind_all("<Control-Shift-Z>", lambda event: _safe_edit_redo(text_edit))
    window.bind_all("<Control-f>", lambda event: open_find_replace(window, text_edit))

    window.mainloop()

main()