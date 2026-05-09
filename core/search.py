import re
import tkinter as tk


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

            pattern = pattern_str if self.regex_mode else re.escape(pattern_str)

            if self.whole_word:
                pattern = r'\b' + pattern + r'\b'

            return re.compile(pattern, flags | re.MULTILINE)
        except re.error:
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

        search_start = self.search_region_start
        search_end = self.search_region_end if self.search_region_end is not None else len(text)

        wrapped = False
        search_from = max(self.last_match_end, search_start)

        for m in pattern_compiled.finditer(text[search_from:search_end]):
            match_start = search_from + m.start()
            match_end = search_from + m.end()

            if match_start == match_end:
                continue

            self.last_match_end = match_end
            return {
                'match_start': match_start,
                'match_end': match_end,
                'matched_text': m.group(),
                'status': 'found',
                'wrapped': wrapped
            }

        if self.wrap_around and search_from > search_start:
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

    regex_var = tk.IntVar(value=0)
    case_var = tk.IntVar(value=0)
    whole_word_var = tk.IntVar(value=0)
    wrap_var = tk.IntVar(value=1)

    tk.Checkbutton(frm, text="Regex", variable=regex_var).grid(row=2, column=0, sticky="w")
    tk.Checkbutton(frm, text="Case Sensitive", variable=case_var).grid(row=2, column=1, sticky="w")
    tk.Checkbutton(frm, text="Whole Word", variable=whole_word_var).grid(row=3, column=0, sticky="w")
    tk.Checkbutton(frm, text="Wrap Around", variable=wrap_var).grid(row=3, column=1, sticky="w")

    text_edit.tag_configure("match", background="yellow")
    text_edit.tag_configure("match_current", background="orange")

    search_state = SearchState()
    status_label = tk.Label(frm, text="", fg="blue")
    status_label.grid(row=4, column=0, columnspan=2, pady=(6, 0))

    def update_search_state():
        search_state.pattern = entry_find.get()
        search_state.regex_mode = regex_var.get()
        search_state.case_sensitive = case_var.get()
        search_state.whole_word = whole_word_var.get()
        search_state.wrap_around = wrap_var.get()
        search_state.in_selection = False

    def on_pattern_change(*args):
        search_state.reset()
        cursor_pos = len(text_edit.get("1.0", "insert"))
        search_state.last_match_end = cursor_pos
        search_state.search_region_start = 0
        search_state.search_region_end = None
        highlight_all()

    entry_find.bind('<KeyRelease>', on_pattern_change)

    def highlight_all():
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
        update_search_state()

        if not entry_find.get():
            status_label.config(text="Enter search pattern", fg="red")
            return

        comp = search_state.compile_pattern(search_state.pattern)
        if not comp:
            status_label.config(text="Invalid pattern", fg="red")
            return

        text = text_edit.get("1.0", "end-1c")

        if search_state.last_match_end == 0 or entry_find.get() != search_state.pattern:
            cursor_offset = len(text_edit.get("1.0", "insert"))
            search_state.last_match_end = cursor_offset

        result = search_state.search(text, comp)
        text_edit.tag_remove("sel", "1.0", "end")

        if result['match_start'] != -1:
            start_idx = f"1.0 + {result['match_start']} chars"
            end_idx = f"1.0 + {result['match_end']} chars"
            text_edit.tag_add("sel", start_idx, end_idx)
            text_edit.mark_set("insert", end_idx)
            text_edit.see(start_idx)

            if result['status'] == 'wrapped':
                status_label.config(text="Wrapped around - found match", fg="green")
            else:
                status_label.config(text="Match found", fg="green")
        else:
            status_label.config(text="No match found", fg="red")

        highlight_all()

    def replace_one():
        sel = text_edit.tag_ranges("sel")
        if sel:
            start, end = sel[0], sel[1]
            repl = entry_replace.get()
            text_edit.delete(start, end)
            text_edit.insert(start, repl)
            search_state.reset()
            search_state.last_match_end = len(text_edit.get("1.0", start))
            highlight_all()
            status_label.config(text="Replaced 1 match", fg="green")
        else:
            status_label.config(text="No selection to replace", fg="red")

    def replace_all():
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

        count = len([m for m in comp.finditer(full) if m.start() != m.end()])

        try:
            if search_state.regex_mode:
                new = re.sub(patt, repl, full, flags=(0 if search_state.case_sensitive else re.IGNORECASE))
            else:
                new = full.replace(patt, repl)
        except re.error as e:
            status_label.config(text=f"Error: {e}", fg="red")
            return

        text_edit.delete("1.0", "end")
        text_edit.insert("1.0", new)
        search_state.reset()
        highlight_all()
        status_label.config(text=f"Replaced {count} match(es)", fg="green")

    def clear_highlight():
        text_edit.tag_remove("match", "1.0", "end")
        text_edit.tag_remove("match_current", "1.0", "end")
        search_state.reset()
        status_label.config(text="", fg="blue")

    btn_frame = tk.Frame(frm)
    btn_frame.grid(row=5, column=0, columnspan=2, pady=(6, 0))
    tk.Button(btn_frame, text="Find Next",     command=find_next).grid(row=0, column=0, padx=2)
    tk.Button(btn_frame, text="Highlight All", command=highlight_all).grid(row=0, column=1, padx=2)
    tk.Button(btn_frame, text="Replace",       command=replace_one).grid(row=0, column=2, padx=2)
    tk.Button(btn_frame, text="Replace All",   command=replace_all).grid(row=0, column=3, padx=2)
    tk.Button(btn_frame, text="Clear",         command=clear_highlight).grid(row=0, column=4, padx=2)
    tk.Button(btn_frame, text="Close",         command=top.destroy).grid(row=0, column=5, padx=2)

    entry_find.focus_set()